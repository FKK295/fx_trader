import pytest
from config.settings import Settings
from config.trading_params import TradingParameters


def test_settings_load_from_env():
    """環境変数から設定の読み込みテスト"""
    # 環境変数の設定
    os.environ["OANDA_ACCOUNT_ID"] = "test123"
    os.environ["OANDA_ACCESS_TOKEN"] = "test_token"
    os.environ["OANDA_ENVIRONMENT"] = "practice"

    settings = Settings()
    
    assert settings.OANDA_ACCOUNT_ID == "test123"
    assert settings.OANDA_ACCESS_TOKEN == "test_token"
    assert settings.OANDA_ENVIRONMENT == "practice"


def test_trading_params_validation():
    """取引パラメータのバリデーションテスト"""
    params = TradingParameters(
        MAX_POSITIONS_PER_CURRENCY=2,
        MAX_DRAWDOWN_PCT=0.1,
        DEFAULT_SL_PIPS=50.0,
        DEFAULT_TP_PIPS=100.0
    )
    
    assert params.MAX_POSITIONS_PER_CURRENCY == 2
    assert params.MAX_DRAWDOWN_PCT == 0.1
    assert params.DEFAULT_SL_PIPS == 50.0
    assert params.DEFAULT_TP_PIPS == 100.0

    # 無効な値のテスト
    with pytest.raises(ValueError):
        TradingParameters(MAX_POSITIONS_PER_CURRENCY=0)
    
    with pytest.raises(ValueError):
        TradingParameters(MAX_DRAWDOWN_PCT=1.5)
