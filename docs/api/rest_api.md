# FX Trader REST API ドキュメント

## 基本情報

- **ベースURL**: `/api/v1`
- **認証**: Bearer トークン認証
- **レスポンス形式**: JSON
- **エンコーディング**: UTF-8

## エンドポイント一覧

### アカウント関連
- `GET /accounts` - アカウント一覧の取得
- `POST /accounts` - 新しいアカウントの作成
- `GET /accounts/{account_id}` - アカウント詳細の取得
- `PATCH /accounts/{account_id}` - アカウント情報の更新
- `GET /accounts/{account_id}/transactions` - 取引履歴の取得

### 注文関連
- `GET /orders` - 注文一覧の取得
- `POST /orders` - 新しい注文の作成
- `GET /orders/{order_id}` - 注文詳細の取得
- `PATCH /orders/{order_id}` - 注文の更新
- `DELETE /orders/{order_id}` - 注文のキャンセル

### ポジション関連
- `GET /positions` - ポジション一覧の取得
- `GET /positions/{position_id}` - ポジション詳細の取得
- `PATCH /positions/{position_id}` - ポジションの更新
- `POST /positions/{position_id}/close` - ポジションのクローズ

### マーケットデータ
- `GET /market/ohlcv/{symbol}` - OHLCVデータの取得
- `GET /market/orderbook/{symbol}` - 板情報の取得
- `GET /market/ticker/{symbol}` - ティッカー情報の取得
- `GET /market/symbols` - 取引ペア一覧の取得

### バックテスト
- `POST /backtesting` - バックテストの開始
- `GET /backtesting/{backtest_id}` - バックテスト結果の取得
- `GET /backtesting/{backtest_id}/trades` - バックテストのトレード履歴
- `GET /backtesting/{backtest_id}/equity` - バックテストのエクイティカーブ

## エラーハンドリング

### エラーレスポンス形式

```json
{
  "detail": "Error message",
  "status": 400,
  "code": "invalid_request",
  "request_id": "req_1234567890"
}
```

### エラーコード一覧

| ステータスコード | エラーコード | 説明 |
|----------------|-------------|------|
| 400 | invalid_request | リクエストが不正です |
| 401 | unauthorized | 認証に失敗しました |
| 403 | forbidden | 権限がありません |
| 404 | not_found | リソースが見つかりません |
| 429 | rate_limit_exceeded | レート制限を超えました |
| 500 | internal_server_error | サーバーエラーが発生しました |

## レートリミット

- 認証済みリクエスト: 1分間に100リクエスト
- 未認証リクエスト: 1分間に10リクエスト

レートリミットを超えると、`429 Too Many Requests` エラーが返されます。
レスポンスヘッダーに以下の情報が含まれます：

- `X-RateLimit-Limit`: 制限回数
- `X-RateLimit-Remaining`: 残りリクエスト数
- `X-RateLimit-Reset`: 制限がリセットされるUNIXタイムスタンプ

## バージョニング

APIのバージョンはURLに含まれます（例: `/api/v1/...`）。
後方互換性のない変更を行う場合は、メジャーバージョンを上げます。
