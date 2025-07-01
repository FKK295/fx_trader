# FX Trader 設定ドキュメント

このドキュメントでは、FX Trader システムで利用可能な設定オプションについて説明します。

## 1. 環境変数

### 1.1 コア設定

```yaml
# .env ファイル

# アプリケーション設定
FX_TRADER_ENV=development  # 環境: development（開発） | production（本番） | test（テスト）
FX_TRADER_LOG_LEVEL=info   # ログレベル: debug | info | warning | error | critical
FX_TRADER_API_KEY=your_api_key_here  # アプリケーションAPIキー

# データベース設定
DB_HOST=localhost  # データベースホスト名
DB_PORT=5432  # データベースポート番号
DB_NAME=fx_trader_db  # データベース名
DB_USER=fx_user  # データベースユーザー名
DB_PASSWORD=fx_password  # データベースパスワード

# Redis 設定
REDIS_HOST=localhost  # Redis ホスト名
REDIS_PORT=6379  # Redis ポート番号
REDIS_PASSWORD=your_redis_password  # Redis パスワード
REDIS_DB_APP=0  # アプリケーションキャッシュ用 Redis データベース番号
REDIS_DB_FEAST=1  # Feast オンラインストア用 Redis データベース番号

# MinIO 設定
MINIO_HOST=localhost  # MinIO ホスト名
MINIO_PORT=9000  # MinIO ポート番号
MINIO_ACCESS_KEY=minio_access_key  # MinIO アクセスキー
MINIO_SECRET_KEY=minio_secret_key  # MinIO シークレットキー

# Vault 設定
VAULT_HOST=localhost  # Vault ホスト名
VAULT_PORT=8200  # Vault ポート番号
VAULT_TOKEN=root  # 開発用のルートトークン（本番環境では使用しないでください）
VAULT_ROLE_ID=your_role_id  # Vault AppRole 認証用のロールID
VAULT_SECRET_ID=your_secret_id  # Vault AppRole 認証用のシークレットID
VAULT_KV_MOUNT_POINT=secret  # Vault KV シークレットエンジンのマウントポイント
VAULT_SECRET_PATH=fx_trader  # シークレットのベースパス

# MLflow 設定
MLFLOW_TRACKING_URI=http://mlflow_server:5000  # MLflow トラッキングサーバーのURI
MLFLOW_S3_ENDPOINT_URL=http://minio:9000  # MLflow アーティファクト用S3互換ストレージのエンドポイント
MLFLOW_ARTIFACT_ROOT=mlflow-artifacts  # MLflow アーティファクトのルートパス
MLFLOW_EXPERIMENT_NAME=default  # デフォルトの実験名

# Prometheus 設定
PROMETHEUS_PORT=9090  # Prometheus メトリクスエンドポイントのポート番号

# Grafana 設定
GRAFANA_PORT=3000  # Grafana ダッシュボードのポート番号
GRAFANA_ADMIN_PASSWORD=grafana_admin_password  # Grafana 管理者パスワード

# Alertmanager 設定
ALERTMANAGER_PORT=9093  # Alertmanager のポート番号

# OANDA API 設定
OANDA_ACCOUNT_ID=YOUR_OANDA_ACCOUNT_ID_HERE  # OANDA アカウントID
OANDA_ACCESS_TOKEN=YOUR_OANDA_ACCESS_TOKEN_HERE  # OANDA API アクセストークン
OANDA_ENVIRONMENT=practice  # 環境: 'practice' (デモ口座) または 'live' (本番口座)

# FRED API 設定
FRED_API_KEY=YOUR_FRED_API_KEY_HERE  # FRED 経済データAPIキー

# AlphaVantage API 設定
ALPHAVANTAGE_API_KEY=YOUR_ALPHAVANTAGE_API_KEY_HERE  # AlphaVantage APIキー

# Vault 設定
VAULT_ADDR=http://localhost:8200  # Vault サーバーアドレス
VAULT_ROLE_ID=  # AppRole 認証用ロールID
VAULT_SECRET_ID=  # AppRole 認証用シークレットID
VAULT_KV_MOUNT_POINT=secret  # KV シークレットエンジンのマウントポイント
VAULT_SECRET_PATH=fx_trader/api_keys  # シークレットのパス

# PostgreSQL 接続設定
POSTGRES_DSN=postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}  # 接続文字列

# MLflow 設定
MLFLOW_S3_ENDPOINT_URL=http://localhost:9000  # S3互換ストレージのエンドポイント
MLFLOW_ARTIFACT_ROOT=s3://mlflow-artifacts  # アーティファクト保存先
AWS_ACCESS_KEY_ID=minio_access_key  # S3互換ストレージのアクセスキー
AWS_SECRET_ACCESS_KEY=minio_secret_key  # S3互換ストレージのシークレットキー

# Feast 設定
FEAST_REGISTRY_PATH=feature_store/registry.db  # レジストリデータベースのパス
FEAST_OFFLINE_STORE_PATH=feature_store/data/offline_store.parquet  # オフラインストアのパス
FEAST_ONLINE_STORE_CONFIG_PATH=feature_store/online_store.yaml  # オンラインストア設定ファイルのパス

# Redis 接続設定
REDIS_URL=redis://${REDIS_HOST}:${REDIS_PORT}/${REDIS_DB_APP}  # Redis接続URL

# 通知設定 (Telegram)
TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN_HERE  # Telegram ボットトークン
TELEGRAM_CHAT_ID=YOUR_TELEGRAM_CHAT_ID_HERE  # 通知先チャットID

# 取引パラメータ (オプション - デフォルト値は config/trading_params.py を参照)
# MAX_POSITIONS_PER_CURRENCY=2  # 通貨ペアごとの最大ポジション数
# MAX_DRAWDOWN_PCT=0.1  # 最大ドローダウン率 (0.1 = 10%)
# DEFAULT_SL_PIPS=50.0  # デフォルトのストップロス (pips)
# DEFAULT_TP_PIPS=100.0  # デフォルトのテイクプロフィット (pips)
# SLIPPAGE_TOLERANCE_BPS=5  # 許容スリッページ (basis points)
# ATR_PERIOD_FOR_SIZING=14  # ポジションサイジング用ATR期間
# ATR_PERIOD_FOR_SLTP=14  # ストップロス/テイクプロフィット計算用ATR期間
# DEFAULT_TIMEFRAME=H1  # デフォルトの時間足
# NEWS_SENTIMENT_THRESHOLD=0.2  # ニュース感情分析の閾値
# CORRELATION_THRESHOLD=0.7  # 相関閾値
```

### 1.2 Trading Parameters

```yaml
# config/trading_params.py

# Position Sizing
MAX_POSITIONS_PER_CURRENCY: 2
MAX_DRAWDOWN_PCT: 0.1
DEFAULT_SL_PIPS: 50.0
DEFAULT_TP_PIPS: 100.0
SLIPPAGE_TOLERANCE_BPS: 5

# ATR Parameters
ATR_PERIOD_FOR_SIZING: 14
ATR_MULTIPLIER_FOR_SL: 2.0
ATR_MULTIPLIER_FOR_TP: 3.0

# Timeframes
DEFAULT_TIMEFRAME: "H1"

# Risk Management
MAX_POSITION_SIZE: 100000  # Maximum position size per trade
MAX_EXPOSURE_PER_CURRENCY: 200000  # Maximum exposure per currency pair
CORRELATION_THRESHOLD: 0.7  # Maximum allowed correlation between positions

# News Sentiment
NEWS_SENTIMENT_THRESHOLD: 0.2  # Minimum sentiment score to trigger trades

# Strategy Parameters
STRATEGY_PARAMS:
  EMA_CROSSOVER:
    fast_ema: 12
    slow_ema: 26
    timeframe: "H1"
  RSI:
    period: 14
    overbought: 70
    oversold: 30
    timeframe: "H1"
  BOLLINGER_BANDS:
    period: 20
    deviation: 2
    timeframe: "H1"
```

### 1.3 Broker Configuration

```yaml
# config/broker_config.py

# OANDA Configuration
OANDA_CONFIG:
  ENVIRONMENT: practice  # practice | live
  ACCESS_TOKEN: your_oanda_token
  ACCOUNT_ID: your_account_id
  STREAM_TIMEOUT: 300  # 5 minutes
  MAX_RETRIES: 3
  RETRY_DELAY: 5  # seconds

# MT5 Configuration (Optional)
MT5_CONFIG:
  SERVER: "your_mt5_server"
  LOGIN: your_login
  PASSWORD: your_password
  PATH: "C:\\Program Files\\MetaTrader 5\\terminal64.exe"
```

## 2. Feature Store Configuration

```yaml
# feature_store/feature_store.yaml

project: fx_trader
registry: feature_store/registry.db
provider: local
online_store:
  type: redis
  connection:
    host: localhost
    port: 6379
    db: 1  # Redis DB for Feast online store
    password: your_redis_password

offline_store:
  type: file
  path: feature_store/offline_store
```

## 3. MLflow Configuration

```yaml
# mlflow/mlflow.yaml

tracking:
  uri: http://mlflow_server:5000
  artifact_location: s3://mlflow-artifacts
  experiment_name: default

model:
  registry_uri: http://mlflow_server:5000
  model_name: fx_trader_model
  stage: Production

tracking:
  uri: http://mlflow_server:5000
  artifact_location: s3://mlflow-artifacts
  experiment_name: default

model:
  registry_uri: http://mlflow_server:5000
  model_name: fx_trader_model
  stage: Production
```

## 4. Monitoring Configuration

### 4.1 Prometheus Metrics

```yaml
# monitoring/prometheus.yml

scrape_configs:
  - job_name: 'fx_trader'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'

  - job_name: 'broker'
    static_configs:
      - targets: ['localhost:8001']
    metrics_path: '/broker/metrics'

  - job_name: 'data_feeds'
    static_configs:
      - targets: ['localhost:8002']
    metrics_path: '/data/metrics'
```

### 4.2 Alertmanager Rules

```yaml
# monitoring/alertmanager/alerts.yml

groups:
  - name: fx_trader_alerts
    rules:
      - alert: HighPositionExposure
        expr: fx_trader_position_exposure > 100000
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High position exposure detected"
          description: "Position exposure exceeds threshold"

      - alert: NegativePnL
        expr: fx_trader_pnl < -1000
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Negative PnL detected"
          description: "PnL dropped below threshold"

      - alert: HighTradeFailureRate
        expr: rate(fx_trader_trade_failures[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High trade failure rate"
          description: "More than 10% of trades are failing"

      - alert: DataLatency
        expr: fx_trader_data_latency > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High data latency"
          description: "Data feed latency exceeds 5 seconds"
```

## 5. Logging Configuration

```yaml
# config/logging.yaml

version: 1
formatters:
  json:
    class: structlog.stdlib.ProcessorFormatter
    processors:
      - structlog.processors.TimeStamper(fmt="iso")
      - structlog.processors.JSONRenderer()

handlers:
  console:
    class: logging.StreamHandler
    formatter: json
    level: INFO

  file:
    class: logging.handlers.RotatingFileHandler
    filename: logs/fx_trader.log
    maxBytes: 10485760  # 10MB
    backupCount: 5
    formatter: json
    level: DEBUG

loggers:
  fx_trader:
    level: INFO
    handlers: [console, file]
    propagate: False

root:
  level: INFO
  handlers: [console, file]
```

## 6. Configuration Best Practices

1. **Environment Variables**
   - Use `.env` for development
   - Use Kubernetes secrets or Vault for production
   - Never commit sensitive credentials

2. **Configuration Files**
   - Use YAML for better readability
   - Keep sensitive data in Vault
   - Use environment-specific configurations

3. **Monitoring**
   - Set appropriate alert thresholds
   - Monitor all critical components
   - Regularly review and adjust metrics

4. **Security**
   - Use secure connections (HTTPS)
   - Implement proper authentication
   - Regularly rotate secrets
   - Use environment-specific configurations

5. **Backup**
   - Regularly backup configuration files
   - Keep multiple versions
   - Test restore procedures

## 7. Configuration Validation

```python
# config/validators.py

def validate_config(config: dict) -> None:
    """Validate configuration values."""
    
    # Validate trading parameters
    assert 0 < config['MAX_DRAWDOWN_PCT'] <= 1, "MAX_DRAWDOWN_PCT must be between 0 and 1"
    assert config['DEFAULT_SL_PIPS'] > 0, "DEFAULT_SL_PIPS must be positive"
    assert config['DEFAULT_TP_PIPS'] > 0, "DEFAULT_TP_PIPS must be positive"
    
    # Validate broker settings
    assert config['OANDA_CONFIG']['ENVIRONMENT'] in ['practice', 'live'], "Invalid OANDA environment"
    assert config['MT5_CONFIG']['SERVER'], "MT5 server must be specified"
    
    # Validate monitoring thresholds
    assert config['ALERTS']['HighPositionExposure']['threshold'] > 0, "Threshold must be positive"
    assert config['ALERTS']['NegativePnL']['threshold'] < 0, "Threshold must be negative"
```

## 8. Configuration Management

1. **Version Control**
   - Keep all configuration files in version control
   - Use meaningful commit messages
   - Review changes before deployment

2. **Environment Management**
   - Use separate configurations for dev, test, and prod
   - Implement configuration overrides
   - Use feature flags for new features

3. **Change Management**
   - Document all configuration changes
   - Test changes in staging before production
   - Maintain change logs

4. **Documentation**
   - Keep configuration documentation up to date
   - Document all configuration options
   - Include examples and best practices

## 9. Troubleshooting

### Common Issues

1. **Missing Configuration**
   ```bash
   # Check if required variables are set
   env | grep FX_TRADER_
   
   # Check configuration files
   cat config/trading_params.py
   ```

2. **Invalid Values**
   ```bash
   # Validate configuration
   python -m config.validators validate
   
   # Check logs for errors
   tail -f logs/fx_trader.log
   ```

3. **Connection Issues**
   ```bash
   # Check database connection
   psql -h ${DB_HOST} -U ${DB_USER} -d ${DB_NAME}
   
   # Check Redis connection
   redis-cli -h ${REDIS_HOST} -p ${REDIS_PORT} ping
   ```

### Best Practices

1. **Configuration Management**
   - Use environment variables for sensitive data
   - Keep configuration files organized
   - Document all changes

2. **Monitoring**
   - Monitor configuration changes
   - Track performance metrics
   - Set up alerts for critical issues

3. **Security**
   - Rotate secrets regularly
   - Use secure connections
   - Implement proper authentication

4. **Backup**
   - Regularly backup configurations
   - Test restore procedures
   - Keep multiple versions
