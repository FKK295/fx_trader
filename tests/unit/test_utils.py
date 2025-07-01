import pytest
from datetime import datetime
from utils import utils


def test_convert_timestamp():
    """タイムスタンプ変換のテスト"""
    timestamp = "2025-06-06T10:00:00+09:00"
    result = utils.convert_timestamp(timestamp)
    assert isinstance(result, datetime)
    assert result.year == 2025
    assert result.month == 6
    assert result.day == 6
    assert result.hour == 10
    assert result.minute == 0
    assert result.second == 0


def test_calculate_pips():
    """ピップス計算のテスト"""
    # メジャー通貨ペア（USD/JPY）の場合
    result = utils.calculate_pips(135.00, 135.50, "USD/JPY")
    assert result == 50

    # マイナー通貨ペア（EUR/USD）の場合
    result = utils.calculate_pips(1.1000, 1.1050, "EUR/USD")
    assert result == 50


def test_calculate_position_size():
    """ポジションサイズ計算のテスト"""
    # リスクベースのポジションサイズ計算
    result = utils.calculate_position_size(
        account_balance=100000,
        risk_percentage=0.01,
        stop_loss_pips=50,
        price=135.00,
        pair="USD/JPY"
    )
    assert result > 0
    assert isinstance(result, float)
