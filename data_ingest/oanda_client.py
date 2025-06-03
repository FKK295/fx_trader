import asyncio
import json
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

import httpx
import pandas as pd
import websockets
from oandapyV20 import API, V20Error
from oandapyV20.endpoints import accounts, instruments, pricing, trades
from oandapyV20.exceptions import V20Error as OandaV20LibError
from pydantic import BaseModel, Field, validator
from tenacity import retry, stop_after_attempt, wait_exponential

from fx_trader.config import settings
from fx_trader.utils.http_client import get_async_http_client, make_request_with_retry
from fx_trader.utils.logging import get_logger

logger = get_logger(__name__)


class OandaCandle(BaseModel):
    time: datetime
    open: float = Field(alias="o")
    high: float = Field(alias="h")
    low: float = Field(alias="l")
    close: float = Field(alias="c")
    volume: int = Field(alias="v")
    complete: bool

    @validator("time", pre=True)
    def parse_time(cls, value: Union[str, float, int]) -> datetime:
        # OANDA v20 returns time as a string like "2023-01-01T00:00:00.000000000Z"
        # or sometimes as a float/int timestamp for streaming
        if isinstance(value, str):
            try:  # Handle nanosecond precision if present
                return datetime.strptime(value.split('.')[0], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
            except ValueError:
                return pd.to_datetime(value).to_pydatetime().replace(tzinfo=timezone.utc)
        elif isinstance(value, (float, int)):
            return datetime.fromtimestamp(value, tz=timezone.utc)
        raise ValueError(f"Invalid time format: {value}")


class OandaPriceTick(BaseModel):
    type: str
    time: datetime
    instrument: str
    bid: float
    ask: float
    status: Optional[str] = None  # e.g. 'tradeable' or 'non-tradeable'

    @validator("time", pre=True)
    def parse_time(cls, value: str) -> datetime:
        return pd.to_datetime(value).to_pydatetime().replace(tzinfo=timezone.utc)

    @validator("bid", "ask", pre=True)
    def parse_float_from_string(cls, value: Any) -> float:
        # OANDA sometimes sends bids/asks as list of dicts
        if isinstance(value, list) and value:
            return float(value[0]['price'])
        return float(value)


class OandaClient:
    def __init__(
        self,
        access_token: str = settings.OANDA_ACCESS_TOKEN,
        account_id: str = settings.OANDA_ACCOUNT_ID,
        environment: str = settings.OANDA_ENVIRONMENT,  # "practice" or "live"
    ):
        self.access_token = access_token
        self.account_id = account_id
        self.environment = environment
        self.base_url = (
            "https://api-fxpractice.oanda.com/v3"
            if environment == "practice"
            else "https://api-fxtrade.oanda.com/v3"
        )
        self.streaming_url = (
            "wss://stream-fxpractice.oanda.com/v3"
            if environment == "practice"
            else "wss://stream-fxtrade.oanda.com/v3"
        )
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        # For synchronous operations using oandapyV20
        self.sync_api = API(access_token=self.access_token,
                            environment=self.environment)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_historical_candles(
        self,
        instrument: str,
        granularity: str = "H1",  # e.g., S5, M1, H1, D
        count: Optional[int] = None,
        from_time: Optional[datetime] = None,
        to_time: Optional[datetime] = None,
        price: str = "M",  # M = Midpoint, B = Bid, A = Ask
    ) -> List[OandaCandle]:
        """Fetches historical candle data."""
        params: Dict[str, Any] = {"granularity": granularity, "price": price}
        if count:
            params["count"] = count
        if from_time:
            params["from"] = from_time.isoformat().replace("+00:00", "Z")
        if to_time:
            params["to"] = to_time.isoformat().replace("+00:00", "Z")

        endpoint = f"/instruments/{instrument}/candles"
        async with await get_async_http_client(base_url=self.base_url, headers=self.headers) as client:
            try:
                response = await make_request_with_retry(client, "GET", endpoint, params=params)
                data = response.json()
                return [OandaCandle(**candle) for candle in data.get("candles", [])]
            except httpx.HTTPStatusError as e:
                logger.error(
                    f"OANDA API error fetching candles for {instrument}: {e.response.text}")
                raise
            except Exception as e:
                logger.error(
                    f"Unexpected error fetching OANDA candles for {instrument}: {e}")
                raise

    async def stream_prices(
        self, instruments: List[str]
    ) -> AsyncGenerator[OandaPriceTick, None]:
        """Streams real-time pricing data for a list of instruments."""
        uri = f"{self.streaming_url}/accounts/{self.account_id}/pricing/stream?instruments={','.join(instruments)}"
        headers = {"Authorization": f"Bearer {self.access_token}"}

        while True:  # Outer loop for reconnections
            try:
                # type: ignore
                async with websockets.connect(uri, extra_headers=headers) as websocket:
                    logger.info(
                        f"Connected to OANDA price stream for {instruments}")
                    while True:
                        try:
                            message_str = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                            message = json.loads(message_str)  # type: ignore

                            if message.get("type") == "PRICE":
                                # OANDA sends bid/ask as list of dicts, need to extract
                                bid = float(message["bids"][0]["price"]) if message.get(
                                    "bids") else 0.0
                                ask = float(message["asks"][0]["price"]) if message.get(
                                    "asks") else 0.0

                                tick_data = {
                                    "type": message["type"],
                                    "time": message["time"],
                                    "instrument": message["instrument"],
                                    "bid": bid,
                                    "ask": ask,
                                    "status": message.get("status")
                                }
                                yield OandaPriceTick(**tick_data)
                            elif message.get("type") == "HEARTBEAT":
                                logger.debug(f"OANDA Heartbeat: {message}")
                            else:
                                logger.warning(
                                    f"Received unhandled OANDA message type: {message}")

                        except asyncio.TimeoutError:
                            logger.warning(
                                "OANDA stream timeout, sending keepalive/ping.")
                            try:
                                await websocket.ping()
                            except websockets.ConnectionClosed:
                                logger.warning(
                                    "OANDA stream connection closed while sending ping.")
                                break  # Break inner loop to reconnect
                        except websockets.ConnectionClosed as e:
                            logger.warning(
                                f"OANDA stream connection closed: {e}. Reconnecting...")
                            break  # Break inner loop to reconnect
                        except json.JSONDecodeError as e:
                            logger.error(
                                f"Error decoding JSON from OANDA stream: {e}. Message: {message_str}")
                        except Exception as e:
                            logger.error(f"Error in OANDA price stream: {e}")
                            # Wait before continuing or breaking
                            await asyncio.sleep(5)
                            break  # Break inner loop to reconnect

            except websockets.exceptions.InvalidStatusCode as e:  # type: ignore
                logger.error(
                    f"Failed to connect to OANDA stream (Invalid Status Code {e.status_code}): {e}. Retrying in 10s.")
            except ConnectionRefusedError:
                logger.error(
                    "OANDA stream connection refused. Retrying in 10s.")
            except Exception as e:
                logger.error(
                    f"Unexpected error connecting to OANDA stream: {e}. Retrying in 10s.")

            await asyncio.sleep(10)  # Wait before attempting to reconnect

    # Example of using the synchronous library for other operations (e.g., trading)
    # This would typically be in execution_client.py but shown here for oandapyV20 usage
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_account_summary(self) -> Dict[str, Any]:
        try:
            r = accounts.AccountSummary(accountID=self.account_id)
            self.sync_api.request(r)
            return r.response  # type: ignore
        except OandaV20LibError as e:
            logger.error(
                f"OANDA API error (sync) getting account summary: {e}")
            raise
