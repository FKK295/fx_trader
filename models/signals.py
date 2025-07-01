from enum import Enum
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd
import talib
from pydantic import BaseModel, Field, validator

from config import settings
from utils.logging import get_logger

logger = get_logger(__name__)


class SignalActionType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    CLOSE_LONG = "CLOSE_LONG"  # Explicitly close an existing long
    CLOSE_SHORT = "CLOSE_SHORT"  # Explicitly close an existing short


class Signal(BaseModel):
    """
    Represents a trading signal.
    """
    action: SignalActionType
    pair: str
    timestamp: pd.Timestamp  # Timestamp of the data point that generated the signal
    # Suggested entry price (e.g., current close)
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None  # Suggested stop loss
    take_profit: Optional[float] = None  # Suggested take profit
    # Confidence score for the signal
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    strategy_name: str
    # For strategy-specific details, e.g., indicator values
    details: Dict[str, Any] = Field(default_factory=dict)

    @validator("timestamp", pre=True)
    def _parse_timestamp(cls, value: Any) -> pd.Timestamp:
        if isinstance(value, pd.Timestamp):
            return value
        return pd.to_datetime(value)


def _calculate_ema_crossover_signal(df: pd.DataFrame, short_window: int, long_window: int) -> SignalActionType:
    """Generates signal based on EMA crossover."""
    if len(df) < long_window:
        return SignalActionType.HOLD

    df['ema_short'] = talib.EMA(df['close'], timeperiod=short_window)
    df['ema_long'] = talib.EMA(df['close'], timeperiod=long_window)

    last = df.iloc[-1]
    prev = df.iloc[-2]

    if pd.isna(last['ema_short']) or pd.isna(last['ema_long']) or \
       pd.isna(prev['ema_short']) or pd.isna(prev['ema_long']):
        return SignalActionType.HOLD

    # Buy signal: short EMA crosses above long EMA
    if last['ema_short'] > last['ema_long'] and prev['ema_short'] <= prev['ema_long']:
        return SignalActionType.BUY
    # Sell signal: short EMA crosses below long EMA
    elif last['ema_short'] < last['ema_long'] and prev['ema_short'] >= prev['ema_long']:
        return SignalActionType.SELL
    return SignalActionType.HOLD


def _calculate_rsi_signal(df: pd.DataFrame, period: int, oversold_threshold: int, overbought_threshold: int) -> SignalActionType:
    """Generates signal based on RSI."""
    if len(df) < period:
        return SignalActionType.HOLD

    df['rsi'] = talib.RSI(df['close'], timeperiod=period)
    last_rsi = df['rsi'].iloc[-1]

    if pd.isna(last_rsi):
        return SignalActionType.HOLD

    if last_rsi < oversold_threshold:
        return SignalActionType.BUY
    elif last_rsi > overbought_threshold:
        return SignalActionType.SELL
    return SignalActionType.HOLD


def _calculate_bollinger_bands_signal(df: pd.DataFrame, period: int, std_dev: float) -> SignalActionType:
    """Generates signal based on Bollinger Bands (example: breakout)."""
    if len(df) < period:
        return SignalActionType.HOLD

    upper, middle, lower = talib.BBANDS(
        df['close'], timeperiod=period, nbdevup=std_dev, nbdevdn=std_dev, matype=0)
    df['bb_upper'] = upper
    df['bb_middle'] = middle
    df['bb_lower'] = lower

    last = df.iloc[-1]
    if pd.isna(last['bb_upper']) or pd.isna(last['close']):
        return SignalActionType.HOLD

    # Example Breakout: Buy if closes above upper band
    if last['close'] > last['bb_upper']:
        return SignalActionType.BUY
    # Example Breakout: Sell if closes below lower band
    elif last['close'] < last['bb_lower']:
        return SignalActionType.SELL
    # Example Reversal (more complex, would need to check previous candles)
    # if last_close < last_lower_band and prev_close > prev_lower_band: return SignalActionType.BUY (reversal from low)
    return SignalActionType.HOLD


def generate_signal(
    historical_df: pd.DataFrame,
    pair: str,
    strategy_name: str,
    strategy_config: Dict[str, Any],
    live_data_point: Optional[Dict[str, Any]] = None,
    # e.g., output from models.forecast.PriceForecaster
    forecast_output: Optional[Any] = None,
    news_sentiment_score: Optional[float] = None,
) -> Optional[Signal]:
    """
    Generates a trading signal based on the provided data and strategy.

    Args:
        historical_df: DataFrame with historical OHLCV data. Must have 'open', 'high', 'low', 'close', 'volume' columns
                       and a DatetimeIndex or a 'time' column.
        pair: The currency pair for the signal (e.g., "EUR_USD").
        strategy_name: Name of the strategy to use (e.g., "EMACrossover", "RSI").
        strategy_config: Dictionary of parameters for the chosen strategy.
        live_data_point: Optional dictionary for the most recent (potentially incomplete) candle data.
                         If provided, it's appended to historical_df for calculation.
                         Expected keys: 'time', 'open', 'high', 'low', 'close', 'volume'.
        forecast_output: Optional output from a forecasting model.
        news_sentiment_score: Optional aggregated news sentiment score.

    Returns:
        A Signal object if a BUY/SELL signal is generated, otherwise None for HOLD.
    """
    if historical_df.empty:
        logger.warning(
            f"Historical data for {pair} is empty. Cannot generate signal.")
        return None

    df = historical_df.copy()
    if 'time' in df.columns and not isinstance(df.index, pd.DatetimeIndex):
        df = df.set_index(pd.to_datetime(df['time']))
    elif not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError(
            "historical_df must have a DatetimeIndex or a 'time' column.")

    if live_data_point:
        live_point_df = pd.DataFrame([live_data_point])
        live_point_df['time'] = pd.to_datetime(live_point_df['time'])
        live_point_df = live_point_df.set_index('time')
        df = pd.concat([df, live_point_df])

    df = df.sort_index()  # Ensure data is sorted by time

    action = SignalActionType.HOLD
    signal_details = {}

    if strategy_name == "EMACrossover":
        action = _calculate_ema_crossover_signal(df, strategy_config.get(
            "short_window", 10), strategy_config.get("long_window", 30))
        signal_details = {
            "ema_short": df['ema_short'].iloc[-1], "ema_long": df['ema_long'].iloc[-1]}
    elif strategy_name == "RSI":
        action = _calculate_rsi_signal(df, strategy_config.get("period", 14), strategy_config.get(
            "oversold", 30), strategy_config.get("overbought", 70))
        signal_details = {"rsi": df['rsi'].iloc[-1]}
    elif strategy_name == "BollingerBands":
        action = _calculate_bollinger_bands_signal(df, strategy_config.get(
            "period", 20), strategy_config.get("std_dev", 2.0))
        signal_details = {"bb_upper": df['bb_upper'].iloc[-1],
                          "bb_middle": df['bb_middle'].iloc[-1], "bb_lower": df['bb_lower'].iloc[-1]}
    # Add more strategies here
    else:
        logger.warning(f"Strategy '{strategy_name}' not implemented.")
        return None

    # Optional: Filter/adjust signal based on news sentiment
    if news_sentiment_score is not None and settings.TRADING.NEWS_SENTIMENT_THRESHOLD != 0:
        sentiment_threshold = settings.TRADING.NEWS_SENTIMENT_THRESHOLD
        if action == SignalActionType.BUY and news_sentiment_score < -sentiment_threshold:
            logger.info(
                f"BUY signal for {pair} overridden by negative news sentiment ({news_sentiment_score:.2f})")
            action = SignalActionType.HOLD
        elif action == SignalActionType.SELL and news_sentiment_score > sentiment_threshold:
            logger.info(
                f"SELL signal for {pair} overridden by positive news sentiment ({news_sentiment_score:.2f})")
            action = SignalActionType.HOLD
        signal_details["news_sentiment_score_used"] = news_sentiment_score

    # Optional: Incorporate forecast_output
    if forecast_output is not None:
        # Example: if forecast predicts strong up-move, increase confidence of BUY signal
        # This logic would be highly dependent on the nature of forecast_output
        signal_details["forecast_considered"] = True  # Placeholder

    if action != SignalActionType.HOLD:
        current_price = df['close'].iloc[-1]
        signal_timestamp = df.index[-1]

        return Signal(
            action=action,
            pair=pair,
            timestamp=signal_timestamp,
            entry_price=current_price,
            # SL/TP can be calculated later by RiskManager or set here with basic logic
            confidence=0.75,  # Example confidence, could be dynamic
            strategy_name=strategy_name,
            details=signal_details
        )

    return None  # No actionable signal
