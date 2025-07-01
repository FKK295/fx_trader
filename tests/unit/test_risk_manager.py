"""
リスク管理モジュールのユニットテスト
"""
import pytest
from unittest.mock import Mock, patch
import pandas as pd
import numpy as np

from execution.risk_manager import RiskManager

class TestRiskManager:
    @pytest.fixture
    def risk_manager(self):
        """リスクマネージャーのテストフィクスチャ"""
        return RiskManager(
            max_drawdown_pct=10.0,
            max_position_size_pct=2.0,
            max_risk_per_trade_pct=1.0,
            atr_period=14,
            atr_multiplier=2.0
        )
    
    def test_initialization(self, risk_manager):
        """初期化テスト"""
        assert risk_manager.max_drawdown_pct == 10.0
        assert risk_manager.max_position_size_pct == 2.0
        assert risk_manager.max_risk_per_trade_pct == 1.0
        assert risk_manager.atr_period == 14
        assert risk_manager.atr_multiplier == 2.0
    
    @pytest.mark.parametrize("equity, max_risk, expected", [
        (10000, 1.0, 100),  # 1% of 10,000 = 100
        (5000, 0.5, 25),     # 0.5% of 5,000 = 25
        (0, 1.0, 0),         # 0 equity
    ])
    def test_calculate_position_size(self, risk_manager, equity, max_risk, expected):
        """ポジションサイズ計算のテスト"""
        result = risk_manager.calculate_position_size(equity, max_risk)
        assert result == expected
    
    def test_check_drawdown_limit(self, risk_manager):
        """ドローダウン制限チェックのテスト"""
        # ドローダウンが制限内
        assert risk_manager.check_drawdown_limit(10000, 9500) is False  # 5% drawdown < 10% limit
        
        # ドローダウンが制限を超えた場合
        with patch('execution.risk_manager.logger.warning') as mock_warning:
            assert risk_manager.check_drawdown_limit(10000, 8900) is True  # 11% drawdown > 10% limit
            mock_warning.assert_called_once()
    
    def test_calculate_atr(self, risk_manager):
        """ATR計算のテスト"""
        # テスト用の価格データ
        prices = pd.DataFrame({
            'high': [10.5, 11.0, 10.8, 11.5, 12.0],
            'low': [9.8, 10.2, 10.0, 10.5, 11.0],
            'close': [10.0, 10.5, 10.3, 11.0, 11.5]
        })
        
        atr = risk_manager.calculate_atr(prices)
        assert isinstance(atr, float)
        assert atr > 0
    
    def test_validate_trade(self, risk_manager):
        """取引検証のテスト"""
        # 有効な取引
        assert risk_manager.validate_trade(
            symbol="USD_JPY", 
            side="buy", 
            size=0.1, 
            current_price=150.0, 
            account_balance=10000.0
        ) == (True, "")
        
        # 無効な取引（サイズが大きすぎる）
        is_valid, reason = risk_manager.validate_trade(
            symbol="USD_JPY",
            side="buy",
            size=100.0,  # 大きすぎるサイズ
            current_price=150.0,
            account_balance=1000.0  # 残高不足
        )
        assert not is_valid
        assert "position size" in reason.lower()

if __name__ == "__main__":
    pytest.main(["-v", __file__])
