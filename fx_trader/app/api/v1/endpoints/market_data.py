"""
Market data endpoints for the FX Trader API.

This module provides endpoints for accessing real-time and historical
market data, including price quotes, candlestick data, and order book data.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field, validator, conint, confloat

from utils.logging import get_logger
from config import settings

# Initialize logger
logger = get_logger(__name__)

# Create router
router = APIRouter(prefix="/market", tags=["market"])

# Constants
SUPPORTED_INTERVALS = ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1M"]
SUPPORTED_EXCHANGES = ["OANDA", "FXCM", "DUKASCOPY"]


class OHLCVData(BaseModel):
    """OHLCV (Open-High-Low-Close-Volume) data point."""
    timestamp: datetime = Field(..., description="Timestamp of the data point")
    open: float = Field(..., gt=0, description="Opening price")
    high: float = Field(..., gt=0, description="Highest price")
    low: float = Field(..., gt=0, description="Lowest price")
    close: float = Field(..., gt=0, description="Closing price")
    volume: float = Field(..., ge=0, description="Trading volume")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class OrderBookLevel(BaseModel):
    """Single level in an order book."""
    price: float = Field(..., gt=0, description="Price level")
    volume: float = Field(..., ge=0, description="Total volume at this price level")
    orders: Optional[int] = Field(None, description="Number of orders at this price level")


class OrderBookData(BaseModel):
    """Order book snapshot."""
    timestamp: datetime = Field(..., description="Timestamp of the order book snapshot")
    symbol: str = Field(..., description="Trading pair symbol")
    bids: List[OrderBookLevel] = Field(..., description="List of bid levels")
    asks: List[OrderBookLevel] = Field(..., description="List of ask levels")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class TickerData(BaseModel):
    """Real-time ticker data."""
    symbol: str = Field(..., description="Trading pair symbol")
    timestamp: datetime = Field(..., description="Timestamp of the last update")
    bid: float = Field(..., gt=0, description="Best bid price")
    ask: float = Field(..., gt=0, description="Best ask price")
    last: float = Field(..., gt=0, description="Last traded price")
    volume: float = Field(..., ge=0, description="24-hour trading volume")
    high: float = Field(..., gt=0, description="24-hour highest price")
    low: float = Field(..., gt=0, description="24-hour lowest price")
    open: float = Field(..., gt=0, description="24-hour opening price")
    change: float = Field(..., description="Price change since 24h ago")
    change_percent: float = Field(..., description="Price change percentage since 24h ago")
    vwap: Optional[float] = Field(None, description="Volume weighted average price")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


@router.get("/ohlcv/{symbol}", response_model=List[OHLCVData])
async def get_ohlcv_data(
    symbol: str,
    interval: str = Query("1h", description=f"Candlestick interval. Supported: {', '.join(SUPPORTED_INTERVALS)}"),
    start_time: Optional[datetime] = Query(None, description="Start time (inclusive)"),
    end_time: Optional[datetime] = Query(None, description="End time (inclusive)"),
    limit: int = Query(100, le=1000, description="Maximum number of data points to return")
):
    """
    Get OHLCV (Open-High-Low-Close-Volume) data.
    
    This endpoint returns historical candlestick data for the specified symbol and time range.
    """
    logger.info(
        f"Fetching OHLCV data for {symbol} with interval={interval}, "
        f"start_time={start_time}, end_time={end_time}, limit={limit}"
    )
    
    # Validate interval
    if interval not in SUPPORTED_INTERVALS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported interval. Supported intervals: {', '.join(SUPPORTED_INTERVALS)}"
        )
    
    # Validate symbol format (basic validation)
    try:
        base, quote = symbol.split('_')
        if len(base) != 3 or len(quote) != 3:
            raise ValueError
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid symbol format. Expected format: 'BASE_QUOTE' (e.g., 'USD_JPY')"
        )
    
    # Set default time range if not provided
    end_time = end_time or datetime.utcnow()
    start_time = start_time or (end_time - timedelta(days=7))  # Default to 1 week of data
    
    # TODO: Implement actual OHLCV data retrieval
    # This is a placeholder implementation that returns mock data
    
    # Generate mock OHLCV data
    ohlcv_data = []
    current_time = start_time
    interval_seconds = _interval_to_seconds(interval)
    
    # Ensure we have enough data points
    num_points = min(limit, 1000)  # Cap at 1000 points
    
    for i in range(num_points):
        # Generate some price movement
        base_price = 100.0 + (i * 0.1)  # Slight upward trend
        spread = 0.1  # 1 pip spread
        
        # Add some randomness to the prices
        import random
        open_price = base_price + (random.random() * 0.2 - 0.1)
        close_price = base_price + (random.random() * 0.2 - 0.1)
        high = max(open_price, close_price) + (random.random() * 0.1)
        low = min(open_price, close_price) - (random.random() * 0.1)
        volume = random.uniform(100, 1000)
        
        ohlcv_data.append(
            OHLCVData(
                timestamp=current_time,
                open=open_price,
                high=high,
                low=low,
                close=close_price,
                volume=volume
            )
        )
        
        # Move to the next interval
        current_time += timedelta(seconds=interval_seconds)
        if current_time > end_time:
            break
    
    return ohlcv_data


def _interval_to_seconds(interval: str) -> int:
    """Convert interval string to seconds."""
    unit = interval[-1]
    value = int(interval[:-1])
    
    if unit == 'm':
        return value * 60
    elif unit == 'h':
        return value * 60 * 60
    elif unit == 'd':
        return value * 24 * 60 * 60
    elif unit == 'w':
        return value * 7 * 24 * 60 * 60
    elif unit == 'M':
        return value * 30 * 24 * 60 * 60  # Approximate
    else:
        return 60  # Default to 1 minute


@router.get("/orderbook/{symbol}", response_model=OrderBookData)
async def get_order_book(
    symbol: str,
    depth: int = Query(10, ge=1, le=100, description="Number of price levels to return")
):
    """
    Get order book data.
    
    This endpoint returns the current order book (market depth) for the specified symbol.
    """
    logger.info(f"Fetching order book for {symbol} with depth={depth}")
    
    # Validate symbol format (basic validation)
    try:
        base, quote = symbol.split('_')
        if len(base) != 3 or len(quote) != 3:
            raise ValueError
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid symbol format. Expected format: 'BASE_QUOTE' (e.g., 'USD_JPY')"
        )
    
    # TODO: Implement actual order book retrieval
    # This is a placeholder implementation that returns mock data
    
    # Generate mock order book data
    mid_price = 110.50  # Example mid price
    spread = 0.02  # 2 pip spread
    
    # Generate bids (descending order)
    bids = []
    for i in range(depth):
        price = mid_price - (i * 0.01) - (spread / 2)
        volume = 1000000 * (depth - i) / depth  # Decreasing volume as we go down
        bids.append(OrderBookLevel(price=price, volume=volume, orders=5))
    
    # Generate asks (ascending order)
    asks = []
    for i in range(depth):
        price = mid_price + (i * 0.01) + (spread / 2)
        volume = 1000000 * (depth - i) / depth  # Decreasing volume as we go up
        asks.append(OrderBookLevel(price=price, volume=volume, orders=5))
    
    return OrderBookData(
        timestamp=datetime.utcnow(),
        symbol=symbol,
        bids=bids,
        asks=asks
    )


@router.get("/ticker/{symbol}", response_model=TickerData)
async def get_ticker(symbol: str):
    """
    Get real-time ticker data.
    
    This endpoint returns the latest ticker data for the specified symbol.
    """
    logger.info(f"Fetching ticker data for {symbol}")
    
    # Validate symbol format (basic validation)
    try:
        base, quote = symbol.split('_')
        if len(base) != 3 or len(quote) != 3:
            raise ValueError
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid symbol format. Expected format: 'BASE_QUOTE' (e.g., 'USD_JPY')"
        )
    
    # TODO: Implement actual ticker data retrieval
    # This is a placeholder implementation that returns mock data
    
    # Generate mock ticker data
    import random
    from datetime import datetime, timezone
    
    base_price = 110.50
    spread = 0.02  # 2 pip spread
    
    # Add some randomness to simulate market movement
    price_change = (random.random() * 0.02) - 0.01  # -1% to +1% change
    current_price = base_price * (1 + price_change)
    
    return TickerData(
        symbol=symbol,
        timestamp=datetime.utcnow(),
        bid=current_price - (spread / 2),
        ask=current_price + (spread / 2),
        last=current_price,
        volume=random.uniform(1000000, 10000000),
        high=current_price * 1.005,  # 0.5% higher than current
        low=current_price * 0.995,    # 0.5% lower than current
        open=base_price,
        change=current_price - base_price,
        change_percent=price_change * 100,
        vwap=current_price * 0.999  # Slightly below current price
    )


@router.get("/symbols", response_model=List[Dict[str, str]])
async def list_symbols(
    exchange: Optional[str] = Query(None, description=f"Filter by exchange. Supported: {', '.join(SUPPORTED_EXCHANGES)}")
):
    """
    List all available trading symbols.
    
    This endpoint returns a list of all available trading symbols,
    optionally filtered by exchange.
    """
    logger.info(f"Listing symbols with exchange filter: {exchange}")
    
    # Validate exchange if provided
    if exchange and exchange.upper() not in SUPPORTED_EXCHANGES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported exchange. Supported exchanges: {', '.join(SUPPORTED_EXCHANGES)}"
        )
    
    # TODO: Implement actual symbol listing with exchange filtering
    # This is a placeholder implementation
    
    # Common forex pairs
    common_pairs = [
        "USD_JPY", "EUR_USD", "GBP_USD", "USD_CHF", "AUD_USD",
        "USD_CAD", "NZD_USD", "EUR_GBP", "EUR_JPY", "GBP_JPY"
    ]
    
    # If exchange is specified, add exchange-specific pairs
    if exchange == "OANDA":
        symbols = common_pairs + [
            "EUR_CAD", "EUR_AUD", "GBP_AUD", "GBP_NZD", "AUD_CAD"
        ]
    elif exchange == "FXCM":
        symbols = common_pairs + [
            "EUR_CHF", "GBP_CHF", "AUD_JPY", "CAD_JPY", "CHF_JPY"
        ]
    elif exchange == "DUKASCOPY":
        symbols = common_pairs + [
            "USD_NOK", "USD_SEK", "USD_DKK", "USD_HKD", "USD_SGD"
        ]
    else:
        # Return all symbols if no exchange is specified
        symbols = list(set(common_pairs + [
            "EUR_CAD", "EUR_AUD", "GBP_AUD", "GBP_NZD", "AUD_CAD",
            "EUR_CHF", "GBP_CHF", "AUD_JPY", "CAD_JPY", "CHF_JPY",
            "USD_NOK", "USD_SEK", "USD_DKK", "USD_HKD", "USD_SGD"
        ]))
    
    # Return as list of dicts with symbol and description
    return [{"symbol": s, "description": f"{s[:3]}/{s[4:]} Forex Pair"} for s in sorted(symbols)]
