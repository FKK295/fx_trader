from prometheus_client import Gauge, Counter, Histogram
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# メトリクスの定義
# ポジション関連
POSITIONS_TOTAL = Gauge(
    'fx_trader_positions_total',
    'Total number of open positions',
    ['currency_pair']
)

POSITIONS_PNL = Gauge(
    'fx_trader_positions_pnl',
    'Total PnL of open positions',
    ['currency_pair']
)

POSITIONS_SIZE = Gauge(
    'fx_trader_positions_size',
    'Total position size',
    ['currency_pair']
)

# 取引関連
TRADES_TOTAL = Counter(
    'fx_trader_trades_total',
    'Total number of trades executed',
    ['currency_pair', 'side']
)

TRADES_SUCCESS = Counter(
    'fx_trader_trades_success',
    'Number of successful trades',
    ['currency_pair', 'side']
)

TRADES_FAILED = Counter(
    'fx_trader_trades_failed',
    'Number of failed trades',
    ['currency_pair', 'side']
)

# データ関連
DATA_LATENCY = Histogram(
    'fx_trader_data_latency_seconds',
    'Latency of data updates',
    ['source']
)

DATA_ERRORS = Counter(
    'fx_trader_data_errors_total',
    'Number of data errors',
    ['source', 'type']
)

class MetricsCollector:
    """メトリクス収集クラス"""
    
    @staticmethod
    def update_position_metrics(positions):
        """ポジション関連のメトリクスを更新"""
        for position in positions:
            POSITIONS_TOTAL.labels(
                currency_pair=position['instrument']
            ).set(position['units'])
            
            POSITIONS_PNL.labels(
                currency_pair=position['instrument']
            ).set(position['unrealizedPL'])
            
            POSITIONS_SIZE.labels(
                currency_pair=position['instrument']
            ).set(position['units'])
    
    @staticmethod
    def update_trade_metrics(trade):
        """取引関連のメトリクスを更新"""
        TRADES_TOTAL.labels(
            currency_pair=trade['instrument'],
            side=trade['side']
        ).inc()
        
        if trade['status'] == 'SUCCESS':
            TRADES_SUCCESS.labels(
                currency_pair=trade['instrument'],
                side=trade['side']
            ).inc()
        else:
            TRADES_FAILED.labels(
                currency_pair=trade['instrument'],
                side=trade['side']
            ).inc()
    
    @staticmethod
    def update_data_metrics(source, latency, error_type=None):
        """データ関連のメトリクスを更新"""
        if error_type:
            DATA_ERRORS.labels(
                source=source,
                type=error_type
            ).inc()
        else:
            DATA_LATENCY.labels(source=source).observe(latency)
