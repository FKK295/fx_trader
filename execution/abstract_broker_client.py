from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from models.signals import Signal, SignalActionType


class OrderType(str):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    # Add more as needed (e.g., TAKE_PROFIT_ORDER, STOP_LOSS_ORDER for OANDA)


class OrderStatus(str):
    PENDING = "PENDING"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"


class TradeOrder(ABC):  # Could be a Pydantic model too
    order_id: str
    client_order_id: Optional[str] = None
    instrument: str
    units: float  # Positive for buy, negative for sell
    order_type: OrderType
    price: Optional[float] = None  # For LIMIT/STOP orders
    stop_loss_on_fill: Optional[Dict[str, Any]
                                ] = None  # e.g., {"price": 1.2345}
    take_profit_on_fill: Optional[Dict[str, Any]
                                  ] = None  # e.g., {"price": 1.2365}
    status: Optional[OrderStatus] = None
    # Add more fields like creation_timestamp, filled_timestamp, avg_fill_price etc.


class Position(ABC):  # Could be a Pydantic model
    instrument: str
    long_units: float
    short_units: float
    unrealized_pnl: float
    # Add more fields like average_entry_price, margin_used etc.


class AbstractBrokerClient(ABC):
    """
    Abstract base class for broker clients.
    Defines the interface for interacting with different brokers.
    """

    @abstractmethod
    async def connect(self) -> None:
        """Connects to the broker's API."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnects from the broker's API."""
        pass

    @abstractmethod
    async def get_account_summary(self) -> Dict[str, Any]:
        """Retrieves account summary/balance information."""
        pass

    @abstractmethod
    async def place_order(self, order_details: Dict[str, Any]) -> TradeOrder:
        """Places a new trade order."""
        pass

    @abstractmethod
    async def get_open_positions(self) -> List[Position]:
        """Retrieves all open positions."""
        pass

    @abstractmethod
    async def get_order_status(self, order_id: str) -> TradeOrder:
        """Retrieves the status of a specific order."""
        pass

    @abstractmethod
    async def modify_order_sltp(self, order_id: str, sl_price: Optional[float], tp_price: Optional[float]) -> TradeOrder:
        """Modifies the Stop Loss or Take Profit for an open order or position."""
        pass

    @abstractmethod
    async def cancel_order(self, order_id: str) -> TradeOrder:
        """Cancels an open (pending) order."""
        pass

    @abstractmethod
    async def close_position(self, instrument: str, units: Optional[str] = "ALL") -> TradeOrder:
        """Closes an open position for a given instrument."""
        # units can be "ALL" or a specific amount.
        pass

    @abstractmethod
    async def get_historical_data(
        self,
        instrument: str,
        granularity: str,
        count: Optional[int] = None,
        from_time: Optional[pd.Timestamp] = None,
        to_time: Optional[pd.Timestamp] = None,
    ) -> pd.DataFrame:
        """Fetches historical candle data (primarily for consistency, data_ingest is main source)."""
        pass
