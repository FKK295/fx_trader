import pytest
from backtest.runner import BacktestRunner
from backtest.strategies.ema_crossover_strategy import EMACrossoverStrategy

@pytest.fixture
def backtest_runner():
    """バックテストランナーのテストフィクスチャ"""
    return BacktestRunner()


def test_backtest_runner_init(backtest_runner):
    """バックテストランナー初期化テスト"""
    assert backtest_runner.data is None
    assert backtest_runner.strategy is None
    assert backtest_runner.results is None


def test_backtest_ema_crossover_strategy():
    """EMAクロスオーバー戦略のテスト"""
    strategy = EMACrossoverStrategy(
        fast_ema=12,
        slow_ema=26,
        timeframe="H1"
    )
    
    # テスト用のデータ
    mock_data = {
        "timestamp": ["2025-06-06T10:00:00+09:00", "2025-06-06T11:00:00+09:00"],
        "close": [135.00, 135.50]
    }
    
    # バックテスト実行
    results = strategy.run_backtest(mock_data)
    
    assert results is not None
    assert "returns" in results
    assert "trades" in results
