I want to generate a **production‑grade FX automated trading system** in Python—complete codebase, configuration, and operational artifacts—ready to clone, configure, and run. Follow modern best practices throughout:

* **Type hints** everywhere, validated with Mypy  
* **Pydantic BaseSettings** for configuration (config/settings.py), with a nested TradingParameters model (config/trading\_params.py)  
* **Structured JSON logging** via structlog, including contextual fields for order events, errors, risk‑management triggers, and API calls  
* **Retries** with tenacity (exponential backoff \+ clear fallback actions) on all external API calls and transient operations  
* **Thorough tests**: pytest \+ pytest‑cov for coverage, mutmut for mutation testing (aim ≥ 80% score)  
* **Pre‑commit** hooks: Black, isort, flake8, Mypy, Safety  
* **CI/CD** via GitHub Actions for linting, testing, building, and optionally deploying  
* **Containerization**: Docker for each service \+ Docker Compose for local orchestration  
* **Clear docs**: README.md with badges, architecture overview, detailed setup & usage examples

## **1\. Project root & tooling**

* **Python**: 3.9–3.10  
* **Poetry** (pyproject.toml) with pinned versions for core libs (others can float within compatible ranges). Example pins:  
  pandas \= "^1.5.3"  
  xgboost \= "^1.7.5"  
  prophet \= "^1.1.0"  
  structlog \= "^21.5.0"  
  tenacity \= "^8.2.0"  
  pydantic \= "^1.10.7"  
  httpx \= "^0.24.1"  
  diskcache \= "^5.6.1"  
  great-expectations \= "^0.18.15"  
  feast \= "^0.34.1"  
  mlflow-skinny \= "^2.6.0"  
  optuna \= "^3.1.0"  
  evidently \= "^0.3.1"  
  backtrader \= "^1.9.76.123"  
  dask \= "^2024.1.0"  
  TA-Lib \= "^0.4.24"  
  hvac \= "^1.1.0"  
  oandapyV20 \= "^0.7.0"  
  MetaTrader5 \= "^5.0.45"  
  redis \= "^4.5.5"  
  psycopg2-binary \= "^2.9.7"  
  fastapi \= "^0.100.0"  
  uvicorn \= "^0.23.2"  
  celery \= "^5.3.2"  
  prometheus-client \= "^0.17.0"  
  python-telegram-bot \= "^20.5"

* Generate .env.example listing all required ENV vars (with comments):  
  \# OANDA  
  OANDA\_ACCOUNT\_ID=  
  OANDA\_ACCESS\_TOKEN=  
  OANDA\_ENVIRONMENT=practice

  \# FRED & News  
  FRED\_API\_KEY=  
  ALPHAVANTAGE\_API\_KEY=

  \# Vault  
  VAULT\_ADDR=  
  VAULT\_ROLE\_ID=  
  VAULT\_SECRET\_ID=

  \# Database  
  POSTGRES\_DSN=postgresql://user:pass@host:port/db

  \# MLflow & MinIO  
  MLFLOW\_TRACKING\_URI=http://localhost:5001  
  MLFLOW\_ARTIFACT\_ROOT=s3://mlflow-artifacts/  
  AWS\_ACCESS\_KEY\_ID=  
  AWS\_SECRET\_ACCESS\_KEY=

  \# Feast  
  FEAST\_OFFLINE\_STORE\_PATH=  
  FEAST\_ONLINE\_STORE\_CONFIG\_PATH=

  \# Redis & Celery  
  REDIS\_URL=redis://localhost:6379/0

  \# Notifications  
  TELEGRAM\_BOT\_TOKEN=  
  TELEGRAM\_CHAT\_ID=

  \# TradingParameters (optional overrides)  
  MAX\_POSITIONS\_PER\_CURRENCY=  
  MAX\_DRAWDOWN\_PCT=  
  DEFAULT\_SL\_PIPS=  
  DEFAULT\_TP\_PIPS=  
  SLIPPAGE\_TOLERANCE\_BPS=  
  ATR\_PERIOD\_FOR\_SIZING=  
  ATR\_PERIOD\_FOR\_SLTP=  
  DEFAULT\_TIMEFRAME=  
  NEWS\_SENTIMENT\_THRESHOLD=

* Add .pre-commit-config.yaml with Black, isort, flake8, Mypy, Safety  
* Create README.md with badges (build, coverage, version), clear setup & run instructions

## **2\. Directory structure**

fx\_trader/  
├ .github/workflows/           \# CI/CD (ci.yml, retrain.yml)  
├ .vscode/                     \# VSCode settings & extensions  
├ docker-compose.yml  
├ Dockerfile  
├ pyproject.toml  
├ poetry.lock  
├ .env.example  
├ .pre-commit-config.yaml  
├ config/  
│  ├ settings.py              \# Pydantic BaseSettings  
│  └ trading\_params.py        \# Pydantic TradingParameters  
├ README.md  
├ data\_ingest/  
│  ├ oanda\_client.py  
│  ├ fred\_client.py  
│  └ news\_client.py  
├ quality\_checks/  
│  └ validate.py  
├ great\_expectations/  
│  ├ expectations/            \# suites for price, macro, news  
│  └ checkpoints/  
├ feature\_store/  
│  ├ data\_sources.py  
│  └ feature\_definitions.py   \# Feast FeatureViews  
├ models/  
│  ├ signals.py  
│  └ forecast.py  
├ backtest/  
│  ├ strategies/              \# Backtrader strategies  
│  └ runner.py  
├ execution/  
│  ├ abstract\_broker\_client.py  
│  ├ oanda\_broker\_client.py  
│  ├ mt5\_broker\_client.py  
│  └ risk\_manager.py  
├ monitoring/  
│  ├ exporters.py  
│  ├ grafana\_dashboard.json  
│  └ alertmanager-config.yml  
├ mlops/  
│  ├ vault\_client.py  
│  ├ train.py  
│  └ retrain.py  
├ orchestrator/  
│  ├ airflow\_dag.py  
│  └ prefect\_flow.py  
└ tests/  
   ├ unit/  
   └ integration/

## **3\. Configuration**

* **config/settings.py**: Load all ENV vars (overriding config.dev.yaml if present).  
* **config/trading\_params.py**: Model defaults and bounds for: MAX\_POSITIONS\_PER\_CURRENCY, MAX\_DRAWDOWN\_PCT, DEFAULT\_SL\_PIPS, DEFAULT\_TP\_PIPS, SLIPPAGE\_TOLERANCE\_BPS, ATR\_PERIOD\_FOR\_SIZING, ATR\_PERIOD\_FOR\_SLTP, DEFAULT\_TIMEFRAME, NEWS\_SENTIMENT\_THRESHOLD, CORRELATION\_THRESHOLD.

## **4\. Secrets (mlops/vault\_client.py)**

* Authenticate via hvac AppRole.  
* Fetch and cache dynamic secrets, with automatic renewal before TTL.

## **5\. Data ingestion**

* **OANDA**: HTTPX \+ tenacity (REST), async websockets for v20 pricing.  
* **FRED & News**: HTTPX \+ tenacity, diskcache, Pydantic response models.

## **6\. Data quality (quality\_checks/validate.py)**

* Run Great Expectations suites on raw data; output JSON reports to MinIO; raise on failures.

## **7\. Feature store (feature\_store/feature\_definitions.py)**

* **Feast entities \+ FeatureViews**:  
  * price\_technical\_features (MA, EMA, RSI, MACD, Bollinger, ATR)  
  * macro\_news\_features (CPI, rates, aggregated sentiment)  
* **Offline store** (Parquet/SQLite), **online store** (Redis).

## **8\. Models & experiments**

* **mlops/train.py**: Feast batch features → train XGBoost, Prophet, optional LSTM → log to MLflow → tag runs → Optuna tuning.  
* **mlops/retrain.py**: Evidently drift detection → conditional retrain → backtest comparison → promote model if improved.

## **9\. Backtesting (backtest/runner.py)**

* Backtrader \+ Dask parallel sweeps; realistic spreads, commissions, slippage; walk‑forward optimization; CLI flags; save HTML/JSON reports to MinIO.

## **10\. Signals (models/signals.py)**

* generate\_signals(...) → SignalAction Pydantic model; strategies: EMA cross, RSI oscillator, Bollinger breakout, optional sentiment filter; unit tests on synthetic data.

## **11\. Execution & risk (execution/…)**

* **risk\_manager.py**: ATR sizing, pre‑trade checks (position, exposure, drawdown, correlation), SL/TP (ATR, S/R fallback, fixed PIPs, trailing).  
* **broker\_clients**: Abstract base \+ OANDA/MT5 implementations with structured logging, retries, error translation.

## **12\. Orchestration**

* **Airflow DAG**: daily cycle (ingest → validate → feature\_update → drift\_check → backtest\_validation → signals → execute).  
* **Prefect Flow**: equivalent, with retries, caching, Telegram failure notifications.

## **13\. Monitoring & alerts**

* Prometheus metrics (PnL, drawdown, open trades, latency, slippage, errors).  
* Blackbox Exporter for API health.  
* Grafana dashboard JSON with trading KPIs & system health.  
* Alertmanager config for Telegram alerts on critical events (drawdown breach, ingestion failures, drift, execution errors).

## **14\. CI/CD (GitHub Actions)**

* **ci.yml**: checkout → Poetry install → linters → pytest (parallel) → mutmut → build & push Docker image → upload coverage to Codecov.  
* **retrain.yml**: scheduled/webhook drift retraining → run retrain.py → optionally open PR or deploy staging.

## **15\. Docker & Compose**

* **Dockerfile**: multi‑stage build (Poetry), non‑root user, entrypoint CLI.  
* **docker-compose.yml**: app, worker, dask, postgres, redis, minio, vault, mlflow\_server, prometheus, grafana, alertmanager, (optional: Loki/Tempo/Seq) with healthchecks, volumes, env injection.

## **16\. README.md**

* Overview, Features, Architecture Diagram, Tech Stack  
* Prerequisites, Setup (clone, .env, Poetry, pre‑commit, Docker Compose, Vault dev init, Feast apply, MLflow server)  
* Service URLs, Usage examples (backtest, train, orchestrate, API)  
* Trading strategies doc, Monitoring & alerts, Troubleshooting, Contributing, License  
* Generate all code modules, configs, Docker artifacts, GitHub workflows, pyproject.toml, .pre-commit-config.yaml, .env.example, and README.md—complete with comments, strict type hints, and at least one unit and one integration test per module, covering normal flows and common failures. After following README, running:  
  git clone \<repo\>  
  cd fx\_trader  
  cp .env.example .env   \# fill in secrets  
  poetry install \--with dev,test  
  poetry run pre-commit install  
  docker-compose up \--build

* must yield a fully functional, monitored, and well‑tested FX automated trading pipeline.