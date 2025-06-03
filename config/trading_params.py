from typing import List, Literal

from pydantic import BaseModel, Field, validator


class TradingParameters(BaseModel):
    """
    Defines trading parameters with sensible defaults and validation.
    These can be overridden by environment variables if corresponding
    variables are set in the main Settings class.
    """

    MAX_POSITIONS_PER_CURRENCY: int = Field(
        default=2, ge=1, description="Maximum open positions per currency pair."
    )
    MAX_CONCURRENT_POSITIONS: int = Field(
        default=5, ge=1, description="Maximum total concurrent open positions across all pairs."
    )
    MAX_DRAWDOWN_PCT: float = Field(
        default=0.1, ge=0.01, le=0.5, description="Maximum portfolio drawdown percentage (e.g., 0.1 for 10%)."
    )
    ACCOUNT_RISK_PER_TRADE_PCT: float = Field(
        default=0.01, ge=0.001, le=0.05, description="Percentage of account balance to risk per trade."
    )
    DEFAULT_SL_PIPS: float = Field(
        default=50.0, ge=5.0, description="Default Stop Loss in pips if not dynamically calculated."
    )
    DEFAULT_TP_PIPS: float = Field(
        default=100.0, ge=10.0, description="Default Take Profit in pips if not dynamically calculated."
    )
    SLIPPAGE_TOLERANCE_BPS: int = Field(
        default=5, ge=0, le=50, description="Slippage tolerance in basis points (0.01%)."
    )
    ATR_PERIOD_FOR_SIZING: int = Field(
        default=14, ge=5, description="ATR period used for position sizing."
    )
    ATR_MULTIPLIER_FOR_SL: float = Field(
        default=2.0, ge=0.5, description="ATR multiplier for calculating Stop Loss."
    )
    ATR_MULTIPLIER_FOR_TP: float = Field(
        default=3.0, ge=0.5, description="ATR multiplier for calculating Take Profit (can be optional)."
    )
    DEFAULT_TIMEFRAME: str = Field(
        default="H1", description="Default trading timeframe (e.g., M1, M5, M15, M30, H1, H4, D1)."
    )
    NEWS_SENTIMENT_THRESHOLD: float = Field(
        default=0.2, ge=-1.0, le=1.0, description="Threshold for news sentiment to influence trading decisions."
    )
    CORRELATION_THRESHOLD: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Portfolio correlation threshold to avoid over-exposure."
    )
    ALLOWED_CURRENCY_PAIRS: List[str] = Field(
        default=["EUR_USD", "USD_JPY", "GBP_USD", "AUD_USD", "USD_CAD"],
        description="List of currency pairs allowed for trading."
    )
    MIN_TRADE_DURATION_MINUTES: int = Field(
        default=15, ge=0, description="Minimum duration for a trade to be considered valid (e.g., to avoid high-frequency scalping issues)."
    )

    # TODO: Add more parameters as needed, e.g., for specific strategies
