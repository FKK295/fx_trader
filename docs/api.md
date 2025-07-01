# FX Trader API Documentation

This document provides detailed information about the REST API endpoints available in the FX Trader system.

## Base URL

The API is available at: `http://localhost:8000` (when running locally)

## Authentication

The API requires authentication using an API key. The API key should be passed in the `Authorization` header:

```http
Authorization: Bearer YOUR_API_KEY
```

## API Endpoints

### 1. Trading Endpoints

#### 1.1 Get Current Positions

```http
GET /api/v1/positions
```

**Parameters:**
- None

**Response:**
```json
{
    "positions": [
        {
            "instrument": "USD_JPY",
            "side": "BUY",
            "units": 10000,
            "average_price": 130.50,
            "current_price": 130.55,
            "unrealized_pl": 50,
            "created_at": "2024-01-01T12:00:00Z"
        }
    ]
}
```

#### 1.2 Place Trade

```http
POST /api/v1/trades
```

**Request Body:**
```json
{
    "instrument": "USD_JPY",
    "side": "BUY",
    "units": 10000,
    "type": "MARKET",
    "take_profit": 131.00,
    "stop_loss": 129.00
}
```

**Response:**
```json
{
    "trade_id": "123456",
    "status": "OPEN",
    "instrument": "USD_JPY",
    "side": "BUY",
    "units": 10000,
    "price": 130.50,
    "time": "2024-01-01T12:00:00Z"
}
```

#### 1.3 Close Trade

```http
DELETE /api/v1/trades/{trade_id}
```

**Parameters:**
- `trade_id`: ID of the trade to close

**Response:**
```json
{
    "trade_id": "123456",
    "status": "CLOSED",
    "realized_pl": 50,
    "close_price": 130.55,
    "close_time": "2024-01-01T12:05:00Z"
}
```

### 2. Data Endpoints

#### 2.1 Get Market Data

```http
GET /api/v1/market/{instrument}
```

**Parameters:**
- `instrument`: Currency pair (e.g., USD_JPY)
- `granularity`: Timeframe (e.g., H1, M15)
- `count`: Number of candles to retrieve

**Response:**
```json
{
    "instrument": "USD_JPY",
    "granularity": "H1",
    "candles": [
        {
            "time": "2024-01-01T12:00:00Z",
            "open": 130.50,
            "high": 130.55,
            "low": 130.45,
            "close": 130.52,
            "volume": 100000
        }
    ]
}
```

#### 2.2 Get Economic Data

```http
GET /api/v1/economic
```

**Parameters:**
- `indicator`: Economic indicator (e.g., CPI, GDP)
- `country": Country code (e.g., US, JP)
- `start_date": Start date for data
- `end_date": End date for data

**Response:**
```json
{
    "indicator": "CPI",
    "country": "US",
    "data": [
        {
            "date": "2024-01-01",
            "value": 2.5,
            "previous": 2.3,
            "forecast": 2.4
        }
    ]
}
```

### 3. Strategy Endpoints

#### 3.1 Get Available Strategies

```http
GET /api/v1/strategies
```

**Response:**
```json
{
    "strategies": [
        {
            "name": "EMA_Crossover",
            "description": "Simple EMA crossover strategy",
            "parameters": {
                "fast_ema": 12,
                "slow_ema": 26,
                "timeframe": "H1"
            }
        },
        {
            "name": "RSI",
            "description": "RSI based trading strategy",
            "parameters": {
                "rsi_period": 14,
                "overbought": 70,
                "oversold": 30,
                "timeframe": "H1"
            }
        }
    ]
}
```

#### 3.2 Run Backtest

```http
POST /api/v1/backtest
```

**Request Body:**
```json
{
    "strategy": "EMA_Crossover",
    "instrument": "USD_JPY",
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "parameters": {
        "fast_ema": 12,
        "slow_ema": 26,
        "timeframe": "H1"
    }
}
```

**Response:**
```json
{
    "backtest_id": "bt_123456",
    "status": "RUNNING",
    "progress": 0,
    "start_time": "2024-01-01T12:00:00Z"
}
```

### 4. Risk Management Endpoints

#### 4.1 Get Risk Metrics

```http
GET /api/v1/risk
```

**Response:**
```json
{
    "metrics": {
        "total_exposure": 20000,
        "max_position_size": 10000,
        "current_drawdown": 0.02,
        "max_drawdown": 0.05,
        "correlation_matrix": {
            "USD_JPY": {
                "EUR_JPY": 0.85,
                "GBP_JPY": 0.75
            }
        }
    }
}
```

### 5. Monitoring Endpoints

#### 5.1 Get System Health

```http
GET /api/v1/health
```

**Response:**
```json
{
    "status": "HEALTHY",
    "components": {
        "database": "OK",
        "broker": "OK",
        "data_feeds": {
            "oanda": "OK",
            "fred": "OK",
            "news": "OK"
        }
    },
    "metrics": {
        "latency": {
            "oanda": 150,
            "fred": 200,
            "news": 100
        },
        "error_rates": {
            "oanda": 0.01,
            "fred": 0.00,
            "news": 0.00
        }
    }
}
```

### 6. Feature Store Endpoints

#### 6.1 Get Feature Values

```http
GET /api/v1/features/{feature_name}
```

**Parameters:**
- `feature_name`: Name of the feature
- `instrument": Currency pair
- `start_time": Start time for data
- `end_time": End time for data

**Response:**
```json
{
    "feature_name": "ema_12",
    "instrument": "USD_JPY",
    "values": [
        {
            "time": "2024-01-01T12:00:00Z",
            "value": 130.50
        }
    ]
}
```

## Error Responses

All endpoints return standard error responses in the following format:

```json
{
    "error": {
        "code": "ERROR_CODE",
        "message": "Error message",
        "details": {
            "field": "error details"
        }
    }
}
```

## Rate Limiting

The API implements rate limiting:
- 100 requests per minute per API key
- 1000 requests per hour per API key

## Versioning

The API uses semantic versioning in the URL path (e.g., `/api/v1/`).

## Security

- All endpoints require API key authentication
- Sensitive data is encrypted at rest
- Rate limiting is enforced
- Input validation is performed on all requests
- CORS is restricted to authorized origins
