import pytest
from execution.risk_manager import RiskManager
from execution.oanda_broker_client import OandaBrokerClient

@pytest.fixture
def risk_manager():
    """リスクマネージャーのテストフィクスチャ"""
    return RiskManager()


def test_risk_manager_position_size(risk_manager):
    """ポジションサイズ計算テスト"""
    result = risk_manager.calculate_position_size(
        account_balance=100000,
        risk_percentage=0.01,
        stop_loss_pips=50,
        price=135.00,
        pair="USD/JPY"
    )
    assert result > 0
    assert isinstance(result, float)


def test_risk_manager_check_risk_limits(risk_manager):
    """リスク制限チェックテスト"""
    # テスト用のデータ
    positions = {
        "USD_JPY": 100000,
        "EUR_USD": 50000
    }
    
    # リスク制限内の場合
    result = risk_manager.check_risk_limits(
        positions=positions,
        new_position_size=50000,
        pair="USD_JPY"
    )
    assert result is True
    
    # リスク制限を超える場合
    result = risk_manager.check_risk_limits(
        positions=positions,
        new_position_size=200000,
        pair="USD_JPY"
    )
    assert result is False


def test_oanda_broker_client_order(oanda_broker_client):
    """OANDA注文テスト"""
    # テスト用のデータ
    mock_order = {
        "instrument": "USD_JPY",
        "units": 10000,
        "type": "MARKET",
        "timeInForce": "FOK",
        "positionFill": "DEFAULT"
    }
    
    # モックのレスポンスを返す
    with pytest.raises(NotImplementedError):
        # 実際のAPI呼び出しはテスト環境では実行しない
        oanda_broker_client.create_order(mock_order)
