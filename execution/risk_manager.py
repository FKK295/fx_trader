from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import talib

from fx_trader.config import settings
from fx_trader.config.trading_params import TradingParameters
from fx_trader.models.signals import Signal, SignalActionType
from fx_trader.utils.logging import get_logger

logger = get_logger(__name__)


class RiskManager:
    def __init__(
        self,
        trading_params: TradingParameters = settings.TRADING,
        account_balance: float = 100000.0,  # Initial or current balance
        # current_positions: List[Dict[str, Any]] # List of open positions with details
    ):
        self.params = trading_params
        self.account_balance = account_balance
        # self.current_positions = current_positions # For portfolio-level checks

    def _calculate_atr(self, historical_df: pd.DataFrame, period: int) -> Optional[float]:
        """Calculates the Average True Range (ATR)."""
        if len(historical_df) < period + 1:  # Need enough data for ATR
            logger.warning(
                f"Not enough data ({len(historical_df)}) to calculate ATR with period {period}.")
            return None
        try:
            atr = talib.ATR(
                historical_df['high'].values,
                historical_df['low'].values,
                historical_df['close'].values,
                timeperiod=period
            )
            return atr[-1] if atr is not None and len(atr) > 0 and not np.isnan(atr[-1]) else None
        except Exception as e:
            logger.error(f"Error calculating ATR: {e}")
            return None

    def calculate_position_size(
        self,
        pair: str,
        entry_price: float,
        stop_loss_price: float,
        # For dynamic ATR sizing
        historical_df_for_atr: Optional[pd.DataFrame] = None,
        # For USD-denominated accounts and standard lots on XXX/USD pairs
        pip_value_per_lot: float = 10.0,
        leverage: float = 1.0,  # Account leverage, if applicable for margin calcs
    ) -> Optional[float]:
        """
        Calculates position size based on ATR or fixed risk.
        Assumes standard lot (100,000 units of base currency).
        Returns size in lots.
        """
        risk_per_trade_abs = self.account_balance * \
            self.params.ACCOUNT_RISK_PER_TRADE_PCT

        if entry_price == stop_loss_price:
            logger.error(
                "Entry price and stop loss price cannot be the same for position sizing.")
            return None

        risk_per_unit_currency = abs(entry_price - stop_loss_price)
        if risk_per_unit_currency == 0:
            logger.warning(
                "Risk per unit is zero. Cannot calculate position size.")
            return None

        # Determine pip size for the pair (simplified, assumes USD quote or cross)
        # For XXX/YYY, pip_size is 0.0001, for XXX/JPY it's 0.01
        # This needs to be accurate for the specific pair.
        pip_size = 0.0001 if "JPY" not in pair.upper() else 0.01

        # This is a simplification. Real pip value depends on quote currency and current rate.
        # For a pair like EUR/USD, if account is USD, pip value for 1 lot is $10.
        # For USD/CAD, if account is USD, pip value for 1 lot is $10 / USDCAD_rate.
        # This needs a proper lookup or calculation based on current market rates.
        # Let's assume pip_value_per_lot is for the quote currency of the pair.

        # Risk in pips
        risk_in_pips = risk_per_unit_currency / pip_size
        if risk_in_pips == 0:
            logger.warning(
                "Risk in pips is zero. Cannot calculate position size.")
            return None

        # Value per pip for one lot (e.g., $10 for EURUSD standard lot)
        # This is a critical parameter that needs to be accurate for the pair and account currency.
        # For simplicity, we use a default pip_value_per_lot.

        # Number of lots
        # units = risk_per_trade_abs / risk_per_unit_currency
        # position_size_lots = units / 100000 # Convert units to lots

        # Simpler: Lots = (AccountRiskAmount) / (PipsAtRisk * ValuePerPipPerLot)
        position_size_lots = risk_per_trade_abs / \
            (risk_in_pips * pip_value_per_lot)

        # Apply leverage constraints if necessary (more for margin calculation by broker)
        # Max position size based on leverage: (AccountBalance * Leverage) / EntryPrice / LotSize
        # max_leveraged_lots = (self.account_balance * leverage) / (entry_price * 100000)
        # position_size_lots = min(position_size_lots, max_leveraged_lots)

        if position_size_lots <= 0:
            logger.warning(
                f"Calculated position size is {position_size_lots:.4f}, too small or invalid. Check risk parameters.")
            return None

        # TODO: Add check for broker's minimum and maximum lot size
        # TODO: Add check for max positions per currency from self.params.MAX_POSITIONS_PER_CURRENCY

        logger.info(
            f"Calculated position size for {pair}: {position_size_lots:.4f} lots")
        return round(position_size_lots, 4)  # Round to typical lot precision

    def calculate_sl_tp(
        self,
        signal: Signal,
        historical_df: pd.DataFrame,  # For ATR calculation
    ) -> Tuple[Optional[float], Optional[float]]:
        """Calculates Stop Loss and Take Profit levels."""
        entry = signal.entry_price
        if entry is None:
            logger.error(
                "Entry price not available in signal for SL/TP calculation.")
            return None, None

        atr = self._calculate_atr(
            historical_df, self.params.ATR_PERIOD_FOR_SLTP)

        # Determine pip size for the pair
        pip_size = 0.0001 if "JPY" not in signal.pair.upper() else 0.01

        sl, tp = None, None

        if atr is not None and atr > 0:
            atr_sl_distance = atr * self.params.ATR_MULTIPLIER_FOR_SL
            atr_tp_distance = atr * self.params.ATR_MULTIPLIER_FOR_TP

            if signal.action == SignalActionType.BUY:
                sl = entry - atr_sl_distance
                tp = entry + atr_tp_distance
            elif signal.action == SignalActionType.SELL:
                sl = entry + atr_sl_distance
                tp = entry - atr_tp_distance
        else:  # Fallback to fixed pips if ATR is not available
            logger.warning(
                f"ATR not available for {signal.pair}, using fixed pip SL/TP.")
            if signal.action == SignalActionType.BUY:
                sl = entry - (self.params.DEFAULT_SL_PIPS * pip_size)
                tp = entry + (self.params.DEFAULT_TP_PIPS * pip_size)
            elif signal.action == SignalActionType.SELL:
                sl = entry + (self.params.DEFAULT_SL_PIPS * pip_size)
                tp = entry - (self.params.DEFAULT_TP_PIPS * pip_size)

        # Ensure SL/TP are reasonably placed (e.g., SL not through entry for a new trade)
        if sl is not None and tp is not None:
            if signal.action == SignalActionType.BUY and (sl >= entry or tp <= entry):
                logger.warning(
                    f"Invalid SL/TP for BUY signal on {signal.pair}: SL={sl}, TP={tp}, Entry={entry}")
                return None, None  # Or adjust to min distance
            if signal.action == SignalActionType.SELL and (sl <= entry or tp >= entry):
                logger.warning(
                    f"Invalid SL/TP for SELL signal on {signal.pair}: SL={sl}, TP={tp}, Entry={entry}")
                return None, None  # Or adjust to min distance

        return sl, tp

    def pre_trade_checks(
        self,
        signal: Signal,
        proposed_size_lots: float,
        # current_portfolio_value: float, # Needed for drawdown check
        # open_positions: List[Any], # Detailed list of open positions
    ) -> bool:
        """Performs pre-trade risk checks."""
        # 1. Max Drawdown Check (requires tracking portfolio value over time)
        # if (self.account_balance - current_portfolio_value) / self.account_balance > self.params.MAX_DRAWDOWN_PCT:
        #     logger.error(f"Max drawdown limit ({self.params.MAX_DRAWDOWN_PCT*100}%) breached. No new trades.")
        #     return False
        logger.warning(
            "Max drawdown check is a placeholder and needs portfolio value tracking.")

        # 2. Max Concurrent Positions (overall and per currency)
        # num_open_positions = len(open_positions)
        # if num_open_positions >= self.params.MAX_CONCURRENT_POSITIONS:
        #     logger.warning(f"Max concurrent positions ({self.params.MAX_CONCURRENT_POSITIONS}) reached. Cannot open new trade for {signal.pair}.")
        #     return False
        #
        # positions_for_pair = [p for p in open_positions if p.instrument == signal.pair]
        # if len(positions_for_pair) >= self.params.MAX_POSITIONS_PER_CURRENCY:
        #     logger.warning(f"Max positions for {signal.pair} ({self.params.MAX_POSITIONS_PER_CURRENCY}) reached.")
        #     return False
        logger.warning(
            "Max concurrent positions check is a placeholder and needs open positions data.")

        # 3. Portfolio Correlation Check (Optional, more complex)
        # if self.params.CORRELATION_THRESHOLD < 1.0:
        #     # Calculate correlation of the new trade's asset with existing portfolio
        #     # If high correlation and same direction, might reject or reduce size
        #     logger.warning("Portfolio correlation check is a placeholder.")
        #     pass

        # 4. Check if proposed size is valid (e.g., not zero or negative)
        if proposed_size_lots <= 0:
            logger.error(
                f"Invalid proposed position size ({proposed_size_lots}) for {signal.pair}.")
            return False

        logger.info(
            f"Pre-trade checks passed for {signal.pair} with size {proposed_size_lots} lots.")
        return True
