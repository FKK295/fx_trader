# fx_trader/backtest/strategies/__init__.py
from .bollinger_bands_strategy import BollingerBandsStrategy
from .ema_crossover_strategy import EMACrossoverStrategy
from .rsi_strategy import RSIStrategy

# To make it easy to get strategy class by name
STRATEGY_MAPPING = {"EMACrossover": EMACrossoverStrategy,
                    "RSI": RSIStrategy, "BollingerBands": BollingerBandsStrategy}
