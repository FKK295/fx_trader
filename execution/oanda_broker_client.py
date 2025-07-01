from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import pandas as pd
from oandapyV20 import API, V20Error
from oandapyV20.contrib.requests import MarketOrderRequest, StopLossOrderRequest, TakeProfitOrderRequest, TrailingStopLossOrderRequest
from oandapyV20.endpoints import accounts, orders, positions, trades
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from config import settings
from execution.abstract_broker_client import (
    AbstractBrokerClient,
    OrderType,
    Position,
    TradeOrder,
    OrderStatus
)
from utils.logging import get_logger

logger = get_logger(__name__)

# Map OANDA order states to internal OrderStatus
OANDA_ORDER_STATE_MAP = {
    "PENDING": OrderStatus.PENDING,
    "FILLED": OrderStatus.FILLED,
    "TRIGGERED": OrderStatus.FILLED,  # For SL/TP orders that become market orders
    "CANCELLED": OrderStatus.CANCELLED,
    "REJECTED": OrderStatus.REJECTED,
    "EXPIRED": OrderStatus.EXPIRED,
}


class OandaTradeOrder(TradeOrder):
    def __init__(self, oanda_response_data: Dict[str, Any], order_type_override: Optional[OrderType] = None):
        # This is a simplified mapping. A full implementation would parse more fields.
        # 'orderFillTransaction' or 'orderCancelTransaction' or 'orderCreateTransaction'
        transaction_key = None
        if 'orderFillTransaction' in oanda_response_data:
            transaction_key = 'orderFillTransaction'
            data = oanda_response_data[transaction_key]
            self.status = OANDA_ORDER_STATE_MAP.get(
                data.get('type'), OrderStatus.FILLED)  # Assuming fill means filled
        elif 'orderCancelTransaction' in oanda_response_data:
            transaction_key = 'orderCancelTransaction'
            data = oanda_response_data[transaction_key]
            self.status = OrderStatus.CANCELLED
        elif 'orderCreateTransaction' in oanda_response_data:  # For pending orders
            transaction_key = 'orderCreateTransaction'
            data = oanda_response_data[transaction_key]
            self.status = OANDA_ORDER_STATE_MAP.get(
                data.get('state', 'PENDING'), OrderStatus.PENDING)
        elif 'lastTransactionID' in oanda_response_data:  # For order details from /orders endpoint
            data = oanda_response_data
            self.status = OANDA_ORDER_STATE_MAP.get(
                data.get('state'), OrderStatus.PENDING)
        # Fallback if no specific transaction type found (e.g. direct order object)
        else:
            data = oanda_response_data
            self.status = OANDA_ORDER_STATE_MAP.get(
                data.get('state'), OrderStatus.PENDING)

        self.order_id = str(data.get('id'))
        self.client_order_id = data.get('clientOrderID')
        self.instrument = data.get('instrument')
        self.units = float(data.get('units', 0.0))
        self.order_type = order_type_override or OrderType[data.get(
            'type', 'MARKET').upper()]
        self.price = float(data.get('price')) if data.get('price') else None
        # SL/TP details would be in 'stopLossOnFill' / 'takeProfitOnFill' sub-dicts
        self.stop_loss_on_fill = data.get('stopLossOnFill')
        self.take_profit_on_fill = data.get('takeProfitOnFill')


class OandaPosition(Position):
    def __init__(self, oanda_position_data: Dict[str, Any]):
        self.instrument = oanda_position_data['instrument']
        self.long_units = float(oanda_position_data['long']['units'])
        self.short_units = float(oanda_position_data['short']['units'])
        self.unrealized_pnl = float(
            oanda_position_data.get('unrealizedPL', 0.0))
        # Add more fields as needed


class OandaBrokerClient(AbstractBrokerClient):
    def __init__(
        self,
        access_token: str = settings.OANDA_ACCESS_TOKEN,
        account_id: str = settings.OANDA_ACCOUNT_ID,
        environment: str = settings.OANDA_ENVIRONMENT,
    ):
        self.access_token = access_token
        self.account_id = account_id
        self.environment = environment
        self.api = API(access_token=self.access_token,
                       environment=self.environment)
        logger.info(
            f"OANDA Broker Client initialized for account {self.account_id} in {self.environment} environment.")

    async def connect(self) -> None:
        # oandapyV20 doesn't maintain a persistent connection in the same way a websocket client might.
        # API calls are stateless. We can check connectivity with an account summary call.
        logger.info(
            "Attempting to connect to OANDA (checking account summary)...")
        await self.get_account_summary()  # This will raise if auth fails
        logger.info(
            "Successfully connected to OANDA (verified via account summary).")

    async def disconnect(self) -> None:
        logger.info(
            "OANDA client disconnected (stateless, no specific action).")
        pass  # Stateless

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), retry=retry_if_exception_type(V20Error))
    async def get_account_summary(self) -> Dict[str, Any]:
        r = accounts.AccountSummary(accountID=self.account_id)
        try:
            self.api.request(r)
            logger.debug(f"OANDA Account Summary Response: {r.response}")
            return r.response.get("account", {})
        except V20Error as e:
            logger.error(
                f"OANDA API error getting account summary: {e} - {r.response}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), retry=retry_if_exception_type(V20Error))
    async def place_order(self, order_details: Dict[str, Any]) -> OandaTradeOrder:
        """
        Places an order.
        order_details example:
        {
            "instrument": "EUR_USD",
            "units": 100, # Positive for buy, negative for sell
            "type": "MARKET", # or "LIMIT", "STOP"
            "price": 1.12345, # For LIMIT/STOP
            "stopLossOnFill": {"price": "1.12000"},
            "takeProfitOnFill": {"price": "1.12800"}
        }
        """
        oanda_order_request = {
            "order": {
                "instrument": order_details["instrument"],
                "units": str(order_details["units"]),
                "type": order_details.get("type", "MARKET").upper(),
                # FillOrKill for Market, GoodTilCancelled for Limit/Stop
                "timeInForce": order_details.get("timeInForce", "FOK" if order_details.get("type", "MARKET").upper() == "MARKET" else "GTC"),
                "positionFill": order_details.get("positionFill", "DEFAULT")
            }
        }
        if order_details.get("type", "MARKET").upper() in ["LIMIT", "STOP"]:
            if "price" not in order_details:
                raise ValueError("Price is required for LIMIT/STOP orders.")
            oanda_order_request["order"]["price"] = str(order_details["price"])

        if "stopLossOnFill" in order_details:
            oanda_order_request["order"]["stopLossOnFill"] = {
                "price": str(order_details["stopLossOnFill"]["price"])}
        if "takeProfitOnFill" in order_details:
            oanda_order_request["order"]["takeProfitOnFill"] = {
                "price": str(order_details["takeProfitOnFill"]["price"])}
        if "clientOrderID" in order_details:
            oanda_order_request["order"]["clientExtensions"] = {
                "id": str(order_details["clientOrderID"])}

        r = orders.OrderCreate(accountID=self.account_id,
                               data=oanda_order_request)
        try:
            self.api.request(r)
            logger.info(
                f"OANDA OrderCreate Response for {order_details['instrument']}: {r.response}")
            # The response contains info about the transaction that created/filled the order
            return OandaTradeOrder(r.response, order_type_override=OrderType[order_details.get("type", "MARKET").upper()])
        except V20Error as e:
            logger.error(
                f"OANDA API error placing order for {order_details['instrument']}: {e} - {r.response}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), retry=retry_if_exception_type(V20Error))
    async def get_open_positions(self) -> List[OandaPosition]:
        r = positions.OpenPositions(accountID=self.account_id)
        try:
            self.api.request(r)
            return [OandaPosition(pos_data) for pos_data in r.response.get("positions", [])]
        except V20Error as e:
            logger.error(
                f"OANDA API error getting open positions: {e} - {r.response}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), retry=retry_if_exception_type(V20Error))
    async def get_order_status(self, order_id: str) -> OandaTradeOrder:
        r = orders.OrderDetails(accountID=self.account_id, orderID=order_id)
        try:
            self.api.request(r)
            return OandaTradeOrder(r.response.get("order", {}))
        except V20Error as e:
            logger.error(
                f"OANDA API error getting order status for {order_id}: {e} - {r.response}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), retry=retry_if_exception_type(V20Error))
    async def modify_order_sltp(self, order_id: str, sl_price: Optional[float], tp_price: Optional[float]) -> OandaTradeOrder:
        # Modifying SL/TP for an open TRADE (not pending order) is done via TradeCRCDO (trades.TradeCRCDO)
        # Modifying SL/TP for a PENDING order is done via orders.OrderReplace
        # This example assumes modifying SL/TP for an open trade (identified by its trade ID, not order ID)
        # For simplicity, let's assume order_id here refers to a trade_id for an open trade.
        # A more robust implementation would differentiate.

        # This is for a PENDING order:
        # data = {}
        # if sl_price: data["stopLossOnFill"] = {"price": str(sl_price), "timeInForce": "GTC"}
        # if tp_price: data["takeProfitOnFill"] = {"price": str(tp_price), "timeInForce": "GTC"}
        # if not data: raise ValueError("Either sl_price or tp_price must be provided.")
        # r = orders.OrderReplace(accountID=self.account_id, orderID=order_id, data={"order": data})

        # This is for an OPEN TRADE (using tradeID which might be different from original orderID)
        # This requires knowing the tradeID.
        # For now, this function is a placeholder for the complexity.
        logger.warning(
            "modify_order_sltp for OANDA needs to distinguish between pending orders and open trades. This is a placeholder.")
        # Example for modifying an open trade's SL/TP:
        # trade_id = order_id # Assuming order_id is actually the trade_id
        # crcdo_data = {}
        # if sl_price: crcdo_data["stopLoss"] = {"price": str(sl_price), "timeInForce": "GTC"}
        # if tp_price: crcdo_data["takeProfit"] = {"price": str(tp_price), "timeInForce": "GTC"}
        # r = trades.TradeCRCDO(accountID=self.account_id, tradeID=trade_id, data=crcdo_data)
        # try:
        #     self.api.request(r)
        #     # The response here is complex, might be orderFillTransaction for SL/TP if hit immediately,
        #     # or a transaction showing the SL/TP orders being created/modified.
        #     return OandaTradeOrder(r.response.get("orderCreateTransaction") or r.response.get("orderFillTransaction") or {})
        # except V20Error as e:
        #     logger.error(f"OANDA API error modifying SL/TP for trade {trade_id}: {e} - {r.response}")
        #     raise
        raise NotImplementedError(
            "OANDA modify_order_sltp needs robust handling for trades vs orders.")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), retry=retry_if_exception_type(V20Error))
    async def cancel_order(self, order_id: str) -> OandaTradeOrder:
        r = orders.OrderCancel(accountID=self.account_id, orderID=order_id)
        try:
            self.api.request(r)
            # Response contains 'orderCancelTransaction'
            return OandaTradeOrder(r.response)
        except V20Error as e:
            logger.error(
                f"OANDA API error cancelling order {order_id}: {e} - {r.response}")
            # If order is already filled or cancelled, OANDA might return specific error codes.
            # e.g., if V20Error code is 404 and "Order not found" or "Order already cancelled"
            if e.code == 404 and r.response and ("Order not found" in r.response.get("errorMessage", "") or "already been cancelled" in r.response.get("errorMessage", "")):
                logger.warning(
                    f"Order {order_id} not found or already cancelled/filled. Assuming cancellation successful or irrelevant.")
                # Construct a mock response indicating cancellation or use a specific status
                # Mock
                return OandaTradeOrder({"id": order_id, "state": "CANCELLED", "instrument": "UNKNOWN"}, order_type_override=OrderType.MARKET)
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), retry=retry_if_exception_type(V20Error))
    async def close_position(self, instrument: str, units: Optional[str] = "ALL") -> OandaTradeOrder:
        # units: "ALL" or specific amount like "-100" to close 100 long units.
        # Closing a long position means selling. Closing a short position means buying.
        # OANDA requires specifying which side to close (long or short).
        # For simplicity, this example closes all units of the specified instrument.
        # A more robust version would check if it's a long or short position first.

        # Close all long units
        long_units_data = {"longUnits": "ALL"} if units == "ALL" else {
            "longUnits": str(abs(float(units)))}
        # Close all short units
        short_units_data = {"shortUnits": "ALL"} if units == "ALL" else {
            "shortUnits": str(abs(float(units)))}

        # Attempt to close long side first, then short side if units="ALL"
        # This is a simplification. Ideally, you know if you are long or short.
        closed_order_response = None
        try:
            r_long = positions.PositionClose(
                accountID=self.account_id, instrument=instrument, data=long_units_data)
            self.api.request(r_long)
            logger.info(
                f"OANDA PositionClose (long) Response for {instrument}: {r_long.response}")
            # Response contains 'longOrderFillTransaction' or 'longOrderCreateTransaction'
            closed_order_response = r_long.response.get("longOrderFillTransaction") or \
                r_long.response.get("longOrderCreateTransaction") or \
                r_long.response  # Fallback
        except V20Error as e_long:
            # If no long position, OANDA might error. That's okay if we intend to close short next.
            logger.warning(
                f"Error or no action closing long side for {instrument}: {e_long} - {r_long.response if 'r_long' in locals() else 'N/A'}")
            # Not a "no position" error
            if not (e_long.code == 400 and "POSITION_CLOSEOUT_FAILED" in str(e_long) and "UNITS_REDUCE_ONLY" in str(e_long)):
                pass  # Could raise if it's not a "no position" error and units != "ALL"

        # If closing all or closing a short by buying
        if units == "ALL" or (units is not None and float(units) > 0):
            try:
                r_short = positions.PositionClose(
                    accountID=self.account_id, instrument=instrument, data=short_units_data)
                self.api.request(r_short)
                logger.info(
                    f"OANDA PositionClose (short) Response for {instrument}: {r_short.response}")
                # Use this response if it's more relevant (e.g., we were short)
                closed_order_response = r_short.response.get("shortOrderFillTransaction") or \
                    r_short.response.get("shortOrderCreateTransaction") or \
                    r_short.response  # Fallback
            except V20Error as e_short:
                logger.warning(
                    f"Error or no action closing short side for {instrument}: {e_short} - {r_short.response if 'r_short' in locals() else 'N/A'}")
                if closed_order_response is None:  # If long close also failed or didn't happen
                    if not (e_short.code == 400 and "POSITION_CLOSEOUT_FAILED" in str(e_short) and "UNITS_REDUCE_ONLY" in str(e_short)):
                        raise V20Error(
                            msg=f"Failed to close both long and short for {instrument}") from e_short

        if closed_order_response is None:
            # This can happen if there was no position to close.
            # OANDA might return a 400 error with "POSITION_CLOSEOUT_FAILED" if no units to close.
            logger.warning(
                f"No position found or closed for {instrument}. Assuming already flat or error handled.")
            # Return a mock "filled" order indicating nothing was done or it was already closed.
            return OandaTradeOrder({"id": "N/A_NO_POSITION", "state": "FILLED", "instrument": instrument, "units": "0"}, order_type_override=OrderType.MARKET)

        return OandaTradeOrder(closed_order_response, order_type_override=OrderType.MARKET)

    async def get_historical_data(
        self,
        instrument: str,
        granularity: str,
        count: Optional[int] = None,
        from_time: Optional[pd.Timestamp] = None,
        to_time: Optional[pd.Timestamp] = None,
    ) -> pd.DataFrame:
        # This is a synchronous wrapper for consistency with abstract method.
        # The main data ingestion should use data_ingest.oanda_client for async calls.
        from data_ingest.oanda_client import OandaClient as IngestOandaClient
        ingest_client = IngestOandaClient(
            self.access_token, self.account_id, self.environment)

        # The ingest client's get_historical_candles is async.
        # This broker client method is also async, so we can await it.
        candles_models = await ingest_client.get_historical_candles(
            instrument=instrument,
            granularity=granularity,
            count=count,
            from_time=from_time.to_pydatetime() if from_time else None,
            to_time=to_time.to_pydatetime() if to_time else None,
        )
        # Use .model_dump() for Pydantic v2
        df = pd.DataFrame([c.model_dump(by_alias=False)
                          for c in candles_models])
        if not df.empty:
            df['time'] = pd.to_datetime(df['time'])
            df = df.set_index('time')
        return df
