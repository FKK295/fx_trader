import pytest
import logging
from pathlib import Path
from config.settings import settings

# テスト用の設定
@pytest.fixture(scope="session")
def test_settings():
    """テスト用の設定を返す"""
    # テスト用の設定ファイルを使用
    test_config_path = Path("config/test_config.yaml")
    if test_config_path.exists():
        settings.config_file_path = str(test_config_path)
    return settings

# ログ設定
@pytest.fixture(scope="session")
def test_logger():
    """テスト用のロガーを返す"""
    logger = logging.getLogger("test")
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

# テスト用のデータ
@pytest.fixture(scope="session")
def test_data():
    """テスト用のデータを返す"""
    return {
        "sample_price_data": {
            "timestamp": "2025-06-06T10:00:00+09:00",
            "bid": 135.00,
            "ask": 135.05,
            "volume": 100
        },
        "sample_trading_params": {
            "MAX_POSITIONS_PER_CURRENCY": 2,
            "MAX_DRAWDOWN_PCT": 0.1,
            "DEFAULT_SL_PIPS": 50.0,
            "DEFAULT_TP_PIPS": 100.0
        }
    }
