"""
OANDAクライアントモジュールのユニットテスト
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from datetime import datetime, timedelta

from data_ingest.oanda_client import OandaClient

class TestOandaClient:
    @pytest.fixture
    def mock_requests(self):
        with patch('data_ingest.oanda_client.requests') as mock:
            yield mock
    
    @pytest.fixture
    def oanda_client(self):
        """テスト用のOANDAクライアント"""
        return OandaClient(
            account_id="test-account",
            access_token="dummy-token",
            environment="practice"
        )
    
    def test_initialization(self, oanda_client):
        """初期化テスト"""
        assert oanda_client.account_id == "test-account"
        assert oanda_client.access_token == "dummy-token"
        assert oanda_client.environment == "practice"
        assert oanda_client.base_url == "https://api-fxpractice.oanda.com/v3"
    
    def test_get_headers(self, oanda_client):
        """認証ヘッダーのテスト"""
        headers = oanda_client._get_headers()
        assert "Authorization" in headers
        assert "Content-Type" in headers
        assert headers["Content-Type"] == "application/json"
    
    @patch('data_ingest.oanda_client.requests.get')
    def test_get_account_summary(self, mock_get, oanda_client):
        """アカウントサマリー取得のテスト"""
        # モックの設定
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"account": {"balance": "10000.00"}}
        mock_get.return_value = mock_response
        
        # テスト実行
        result = oanda_client.get_account_summary()
        
        # 検証
        assert isinstance(result, dict)
        assert "account" in result
        assert "balance" in result["account"]
        mock_get.assert_called_once()
    
    @patch('data_ingest.oanda_client.requests.get')
    def test_get_historical_prices(self, mock_get, oanda_client):
        """履歴価格取得のテスト"""
        # モックの設定
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candles": [
                {"time": "2023-01-01T00:00:00.000000000Z", "mid": {"o": "1.1000", "h": "1.1010", "l": "1.0990", "c": "1.1005"}, "volume": 1000},
                {"time": "2023-01-02T00:00:00.000000000Z", "mid": {"o": "1.1005", "h": "1.1020", "l": "1.1000", "c": "1.1015"}, "volume": 1200}
            ]
        }
        mock_get.return_value = mock_response
        
        # テスト実行
        df = oanda_client.get_historical_prices(
            instrument="EUR_USD",
            granularity="D",
            count=2
        )
        
        # 検証
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert "open" in df.columns
        assert "high" in df.columns
        assert "low" in df.columns
        assert "close" in df.columns
        assert "volume" in df.columns
    
    @patch('data_ingest.oanda_client.requests.get')
    def test_get_historical_prices_with_dates(self, mock_get, oanda_client):
        """日付指定での履歴価格取得テスト"""
        # モックの設定
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"candles": []}
        mock_get.return_value = mock_response
        
        # テスト実行
        start = datetime(2023, 1, 1)
        end = datetime(2023, 1, 31)
        df = oanda_client.get_historical_prices(
            instrument="EUR_USD",
            granularity="D",
            start=start,
            end=end
        )
        
        # 検証
        assert isinstance(df, pd.DataFrame)
        mock_get.assert_called_once()
        
        # リクエストパラメータの検証
        args, kwargs = mock_get.call_args
        assert "params" in kwargs
        assert "from" in kwargs["params"]
        assert "to" in kwargs["params"]
    
    @patch('data_ingest.oanda_client.requests.get')
    def test_get_instruments(self, mock_get, oanda_client):
        """取引商品一覧取得のテスト"""
        # モックの設定
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "instruments": [
                {"name": "EUR_USD", "type": "CURRENCY", "displayName": "EUR/USD"},
                {"name": "USD_JPY", "type": "CURRENCY", "displayName": "USD/JPY"}
            ]
        }
        mock_get.return_value = mock_response
        
        # テスト実行
        instruments = oanda_client.get_instruments()
        
        # 検証
        assert isinstance(instruments, list)
        assert len(instruments) == 2
        assert "name" in instruments[0]
        assert "type" in instruments[0]
        assert "displayName" in instruments[0]
    
    @patch('data_ingest.oanda_client.requests.get')
    def test_error_handling(self, mock_get, oanda_client):
        """エラーハンドリングのテスト"""
        # エラーレスポンスのモック
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"errorMessage": "Invalid access token"}
        mock_get.return_value = mock_response
        
        # テスト実行と例外検証
        with pytest.raises(Exception) as excinfo:
            oanda_client.get_account_summary()
        
        assert "API request failed" in str(excinfo.value)

if __name__ == "__main__":
    pytest.main(["-v", __file__])
