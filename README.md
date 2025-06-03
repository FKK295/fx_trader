# FX Automated Trading System

[![Python Version](https://img.shields.io/badge/python-3.9%20%7C%203.10-blue.svg)](https://www.python.org/)
[![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)](https://python-poetry.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://github.com/YOUR_GITHUB_USERNAME/YOUR_REPO_NAME/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_GITHUB_USERNAME/YOUR_REPO_NAME/actions/workflows/ci.yml)
[![Coverage Status](https://coveralls.io/repos/github/YOUR_GITHUB_USERNAME/YOUR_REPO_NAME/badge.svg?branch=main)](https://coveralls.io/github/YOUR_GITHUB_USERNAME/YOUR_REPO_NAME?branch=main)
<!-- Add Codecov badge if you prefer: [![codecov](https://codecov.io/gh/YOUR_GITHUB_USERNAME/YOUR_REPO_NAME/branch/main/graph/badge.svg?token=YOUR_CODECOV_TOKEN)](https://codecov.io/gh/YOUR_GITHUB_USERNAME/YOUR_REPO_NAME) -->
[![Mutation Score](https://img.shields.io/badge/mutation%20score-を目指す%2080%2B-orange)](https://mutmut.readthedocs.io/)
<!-- You might need a custom way to display mutmut score badge, or integrate with a service that supports it -->

A production-grade, event-driven, automated FX trading system built with Python. This framework provides a robust foundation for developing, backtesting, and deploying algorithmic trading strategies.

## Features

*   **Modular Design**: Clearly separated components for data ingestion, feature engineering, model training, signal generation, execution, and risk management.
*   **Configuration Management**: Pydantic `BaseSettings` for environment-based configuration with local overrides.
*   **Secret Management**: Integration with HashiCorp Vault for secure handling of API keys and credentials.
*   **Data Ingestion**: Clients for OANDA (REST & streaming), FRED (economic data), and news APIs.
*   **Data Quality**: Great Expectations for data validation and integrity checks.
*   **Feature Store**: Feast for managing and serving features for training and live trading.
*   **MLOps**: MLflow for experiment tracking, model management, and Optuna for hyperparameter optimization. Evidently AI for drift detection.
*   **Backtesting**: `backtrader` engine with Dask for parallelization, cost simulation, and performance reporting (QuantStats).
*   **Signal Generation**: Flexible signal generation module supporting various strategies.
*   **Execution Engine**: Abstract broker interface with OANDA and MT5 (optional) implementations.
*   **Risk Management**: Comprehensive risk checks (position sizing, drawdown, correlation).
*   **Workflow Orchestration**: Example DAGs/Flows for Airflow and Prefect.
*   **Monitoring & Alerting**: Prometheus metrics, Grafana dashboards, and Alertmanager for critical alerts via Telegram.
*   **CI/CD**: GitHub Actions for automated linting, testing, Docker builds, and optional retraining workflows.
*   **Containerization**: Dockerized services orchestrated with Docker Compose for local development.
*   **Best Practices**: Type hints, structured logging (`structlog`), retries (`tenacity`), comprehensive testing (`pytest`, `mutmut`).

## Architecture Overview

```mermaid
graph TD
    subgraph User Interaction
        CLI_User[CLI / User]
    end

    subgraph Orchestration
        Orchestrator[Airflow / Prefect]
    end

    subgraph Data Ingestion
        OANDA_API[OANDA API]
        FRED_API[FRED API]
        News_API[News API]
        OANDA_Client[data_ingest/oanda_client.py]
        FRED_Client[data_ingest/fred_client.py]
        News_Client[data_ingest/news_client.py]
    end

    subgraph Data Storage & Processing
        MinIO[MinIO (Artifacts, Offline Store)]
        PostgreSQL[PostgreSQL (MLflow, Feast Registry)]
        Redis[Redis (Feast Online Store, Celery)]
    end

    subgraph Data Quality
        GreatExpectations[quality_checks/validate.py + GE Suites]
    end

    subgraph Feature Engineering
        Feast_FS[Feature Store (Feast)]
        FeatureDefs[feature_store/feature_definitions.py]
    end

    subgraph Model Lifecycle (MLOps)
        MLflow_Server[MLflow Tracking Server]
        Vault[HashiCorp Vault]
        Train[mlops/train.py w/ Optuna]
        Retrain[mlops/retrain.py w/ Evidently]
        ForecastModel[models/forecast.py]
    end

    subgraph Trading Logic
        SignalGen[models/signals.py]
        Backtester[backtest/runner.py w/ Backtrader & Dask]
        RiskManager[execution/risk_manager.py]
        BrokerClient[execution/*_broker_client.py]
    end

    subgraph Live Execution
        BrokerAPI[Broker API (OANDA/MT5)]
        APIServer[API Server (FastAPI - Optional)]
        CeleryWorker[Celery Worker (Optional)]
    end

    subgraph Monitoring & Alerting
        Prometheus[Prometheus]
        Grafana[Grafana]
        Alertmanager[Alertmanager]
        Telegram[Telegram Notifications]
    end

    CLI_User --> Orchestrator
    Orchestrator -- Triggers --> OANDA_Client
    Orchestrator -- Triggers --> FRED_Client
    Orchestrator -- Triggers --> News_Client
    OANDA_Client -- Ingests Data --> MinIO
    FRED_Client -- Ingests Data --> MinIO
    News_Client -- Ingests Data --> MinIO
    OANDA_Client -- Streams Data --> SignalGen
    MinIO -- Raw Data --> GreatExpectations
    GreatExpectations -- Validated Data --> Feast_FS
    FeatureDefs -- Defines Features --> Feast_FS
    Feast_FS -- Serves Features --> Train
    Feast_FS -- Serves Features --> SignalGen
    Feast_FS -- Stores Features --> Redis
    Feast_FS -- Stores Features --> MinIO
    Train -- Logs to --> MLflow_Server
    Train -- Uses Models from --> ForecastModel
    Retrain -- Uses Models from --> ForecastModel
    Retrain -- Detects Drift, Triggers --> Train
    Retrain -- Logs to --> MLflow_Server
    MLflow_Server -- Stores Artifacts --> MinIO
    MLflow_Server -- Uses DB --> PostgreSQL
    Vault -- Provides Secrets --> OANDA_Client
    Vault -- Provides Secrets --> FRED_Client
    Vault -- Provides Secrets --> News_Client
    Vault -- Provides Secrets --> BrokerClient
    SignalGen -- Generates Signals --> RiskManager
    RiskManager -- Checks Risk, Approves Order --> BrokerClient
    BrokerClient -- Executes Trades --> BrokerAPI
    Backtester -- Uses --> SignalGen
    Backtester -- Uses --> RiskManager
    Backtester -- Simulates --> BrokerAPI
    Backtester -- Logs Results --> MinIO
    APIServer -- Exposes Endpoints --> Orchestrator
    CeleryWorker -- Executes Tasks --> BrokerClient
    BrokerClient -- Emits Metrics --> Prometheus
    APIServer -- Emits Metrics --> Prometheus
    Prometheus -- Scrapes Metrics --> Grafana
    Prometheus -- Sends Alerts --> Alertmanager
    Alertmanager -- Notifies --> Telegram
```

## Tech Stack

*   **Python**: 3.9 / 3.10
*   **Dependency Management**: Poetry
*   **Configuration**: Pydantic
*   **Data Handling**: Pandas, NumPy
*   **API Interaction**: HTTPX, Tenacity, OandapyV20, websockets
*   **Caching**: DiskCache, Cachetools
*   **Data Quality**: Great Expectations
*   **Feature Store**: Feast
*   **ML Experimentation**: MLflow, Optuna
*   **Drift Detection**: Evidently AI
*   **Forecasting (Optional)**: Prophet, XGBoost, Scikit-learn
*   **Backtesting**: Backtrader, Dask, QuantStats
*   **Databases**: PostgreSQL, Redis
*   **Secret Management**: HashiCorp Vault (via HVAC)
*   **Orchestration**: Airflow / Prefect (stubs provided)
*   **API Framework (Optional)**: FastAPI, Uvicorn
*   **Task Queue (Optional)**: Celery
*   **Monitoring**: Prometheus, Grafana, Alertmanager
*   **Notifications**: Telegram
*   **Containerization**: Docker, Docker Compose
*   **CI/CD**: GitHub Actions
*   **Linting/Formatting**: Black, isort, Flake8, Mypy, Safety
*   **Testing**: Pytest, Pytest-Cov, Mutmut

## Prerequisites

*   Python 3.9 or 3.10
*   Poetry (version 1.2+ recommended)
*   Docker & Docker Compose (latest stable versions)
*   Git
*   **TA-Lib C Library**: This must be installed on your system before installing Python dependencies.
    *   On macOS: `brew install ta-lib`
    *   On Ubuntu/Debian: `sudo apt-get install libta-lib-dev`
    *   For other systems, refer to TA-Lib documentation.
*   **(Optional) MetaTrader 5 Terminal**: If using the `mt5_broker_client.py`, the MetaTrader 5 terminal must be installed and running on a Windows machine or a Windows VM accessible by the Python script.

## Setup Instructions (Local Development)

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/YOUR_GITHUB_USERNAME/YOUR_REPO_NAME.git fx_trader
    cd fx_trader
    ```

2.  **Configure Environment Variables**:
    Copy the example environment file and customize it with your actual secrets and configurations:
    ```bash
    cp .env.example .env
    ```
    **IMPORTANT**: Edit `.env` and fill in all `YOUR_*_HERE` placeholders and other relevant settings.
    For local development, you can also create `config/config.dev.yaml` to override settings (gitignored). Environment variables will always take precedence.

3.  **Install Python Dependencies using Poetry**:
    ```bash
    poetry install --with dev,test --sync
    ```
    *Note: This command also creates/updates `poetry.lock` if necessary.*

4.  **Install Pre-commit Hooks**:
    ```bash
    poetry run pre-commit install
    ```

5.  **Start Base Infrastructure Services**:
    This brings up PostgreSQL, MinIO, Vault (in dev mode), MLflow server, and Redis.
    ```bash
    docker-compose up --build -d postgres minio vault mlflow_server redis_app redis_feast
    ```
    Verify services are healthy: `docker-compose ps` and `docker-compose logs <service_name>`.

6.  **Vault Dev Mode Initialization (One-time setup)**:
    The `vault` service in `docker-compose.yml` starts Vault in dev mode with a root token `root`.
    *   **Access Vault UI**: Open `http://localhost:8200` in your browser. Use `root` as the token.
    *   **Enable AppRole Auth Method**:
        ```bash
        docker-compose exec vault vault auth enable approle
        ```
    *   **Create a Policy for the App** (e.g., `fx-trader-policy.hcl`):
        ```hcl
        # fx-trader-policy.hcl
        path "secret/data/fx_trader/*" {
          capabilities = ["read"]
        }
        path "secret/metadata/fx_trader/*" { # if using KV v2
          capabilities = ["list"]
        }
        ```
        Apply the policy:
        ```bash
        docker-compose exec vault vault policy write fx-trader - < ./path/to/your/fx-trader-policy.hcl
        # (Adjust path to policy file if it's not in the root)
        # Or, create it via UI: Policies -> Create ACL policy
        ```
    *   **Create an AppRole**:
        ```bash
        docker-compose exec vault vault write auth/approle/role/fx-trader-role token_policies="fx-trader" token_ttl=1h token_max_ttl=4h
        ```
    *   **Get RoleID and SecretID**:
        ```bash
        docker-compose exec vault vault read auth/approle/role/fx-trader-role/role-id
        # Output: role_id     <YOUR_VAULT_ROLE_ID>

        docker-compose exec vault vault write -f auth/approle/role/fx-trader-role/secret-id
        # Output: secret_id          <YOUR_VAULT_SECRET_ID>
        #         secret_id_accessor ...
        ```
    *   **Update `.env`**: Set `VAULT_ROLE_ID` and `VAULT_SECRET_ID` with the values obtained.
    *   **Seed Initial Secrets**:
        You can use the Vault UI (Secrets -> secret (kv) -> Create Secret) or CLI.
        Example for KV v2 (default mount path `secret/`):
        ```bash
        docker-compose exec vault vault kv put secret/fx_trader/api_keys \
            OANDA_ACCESS_TOKEN="your_oanda_token_from_env_or_real" \
            FRED_API_KEY="your_fred_key_from_env_or_real" \
            ALPHAVANTAGE_API_KEY="your_alphavantage_key_from_env_or_real"
        ```
        Ensure the path matches `VAULT_KV_MOUNT_POINT` and `VAULT_SECRET_PATH` in your `.env` and `config/settings.py`.

7.  **MLflow Setup**:
    *   The MLflow server should be running (from `docker-compose up`). Access UI at `http://localhost:5001`.
    *   Create the `mlflow-artifacts` bucket in MinIO:
        *   Access MinIO UI: `http://localhost:9000` (Credentials: `minio_access_key` / `minio_secret_key` from `.env`).
        *   Click "Create Bucket" and name it `mlflow-artifacts` (or whatever you set in `MLFLOW_ARTIFACT_ROOT`).

8.  **Feast Setup**:
    Initialize the Feast feature repository if it doesn't exist (the `feature_store` directory is already structured, so this might be more about applying definitions).
    Ensure your `feature_store/feature_repo_config.py` (or similar, depending on Feast version and template) points to the correct registry and online/offline stores as per `.env`.
    ```bash
    # cd feature_store # If your feast project is rooted here
    # poetry run feast init my_feature_repo # Only if starting from scratch

    # Apply feature definitions (assuming feature_store is the context)
    poetry run feast -c feature_store apply

    # Materialize some initial data (example for data up to now)
    # You'll need to have some data in your offline store sources first.
    # poetry run feast -c feature_store materialize-incremental $(date +%Y-%m-%dT%H:%M:%S)
    ```
    *Note: The exact Feast commands might vary slightly based on the Feast version and how you structure `feature_store/example_repo.py` or `feature_store/feature_store.yaml`.*
    The provided structure assumes `feature_store/registry.db` (SQLite) and `feature_store/online_store.yaml` (for Redis).

9.  **Start All Application Services**:
    If you stopped them, or to bring up the `app` (FastAPI), `worker` (Celery), `dask-scheduler`, `dask-worker`, etc.
    ```bash
    docker-compose up --build -d
    ```

10. **Verify Services**:
    Check logs for any errors:
    ```bash
    docker-compose logs -f app
    docker-compose logs -f worker
    # etc.
    ```

## Service URLs (Local Development)

*   **FastAPI App (if running)**: `http://localhost:8000/docs`
*   **Grafana**: `http://localhost:3000` (Default login: admin/admin, or as configured in `docker-compose.yml` environment variables for Grafana)
*   **MLflow UI**: `http://localhost:5001`
*   **MinIO Console**: `http://localhost:9000` (Credentials from `.env`)
*   **Vault UI**: `http://localhost:8200` (Token: `root` for dev mode, or AppRole for app)
*   **Prometheus**: `http://localhost:9090`
*   **Alertmanager**: `http://localhost:9093`
*   **Airflow UI (if configured & running)**: `http://localhost:8080` (or as per Airflow setup)
*   **Prefect UI (if configured & running)**: `http://localhost:4200` (or as per Prefect setup)
*   **Flower (Celery Monitor - if `worker` service includes it)**: `http://localhost:5555`

## Running the System

*   **Trigger Orchestrator Flows**:
    *   Manually trigger DAGs/Flows via Airflow/Prefect UI.
    *   Or run specific scripts: `poetry run python -m orchestrator.your_main_script`
*   **Run Backtests Manually**:
    ```bash
    poetry run python -m backtest.runner --strategy EMACrossover --pair EUR_USD --start-date 2022-01-01 --end-date 2022-12-31
    ```
    Use `poetry run python -m backtest.runner --help` for all options.
*   **Run Model Training Manually**:
    ```bash
    poetry run python -m mlops.train
    ```
*   **Run Data Ingestion Manually (Example)**:
    ```bash
    poetry run python -m data_ingest.main_ingest_script # (You'll need to create this script)
    ```
*   **Using Docker Compose Exec**:
    For running commands within a running service container:
    ```bash
    docker-compose exec app poetry run python -m mlops.train
    docker-compose exec app poetry run pytest
    ```

## Trading Strategies

*   **EMA Crossover**: Buys when short-term EMA crosses above long-term EMA, sells on reverse.
*   **RSI Oscillator**: Buys on oversold RSI (e.g., <30), sells on overbought RSI (e.g., >70).
*   **Bollinger Band Breakout/Reversal**: Trades breakouts above/below bands or reversals from bands.

Parameters for each strategy are configurable. See `models/signals.py` and `config/trading_params.py`.

## Monitoring & Alerts

*   **Grafana Dashboards**: Access Grafana at `http://localhost:3000`. A pre-configured dashboard JSON (`monitoring/grafana_dashboard.json`) can be imported.
*   **Key Metrics**: PnL, drawdown, open trades, API latency, slippage, error counts.
*   **Alert Types**: Configured in `monitoring/alertmanager/config.yml`. Critical alerts (drawdown breaches, ingestion failures, model drift, execution errors) are routed to Telegram.

## Troubleshooting

*   **`docker-compose logs <service_name>`**: Your first stop for debugging service issues.
*   **Poetry issues**: Ensure `poetry shell` is active or prefix commands with `poetry run`.
*   **TA-Lib installation**: If `poetry install` fails related to TA-Lib, ensure the C library is installed correctly on your system (see Prerequisites).
*   **Port conflicts**: Ensure ports defined in `docker-compose.yml` and `.env` are free.

## Contributing

1.  Fork the repository.
2.  Create a new feature branch (`git checkout -b feature/your-feature-name`).
3.  Make your changes.
4.  Ensure pre-commit hooks pass (`poetry run pre-commit run --all-files`).
5.  Write tests for your changes. Ensure `poetry run pytest` passes and coverage is maintained.
6.  Push your branch and create a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details (you'll need to create this file, e.g., with standard MIT license text).

---

*Disclaimer: Trading foreign exchange on margin carries a high level of risk and may not be suitable for all investors. The high degree of leverage can work against you as well as for you. Before deciding to trade foreign exchange you should carefully consider your investment objectives, level of experience, and risk appetite. The possibility exists that you could sustain a loss of some or all of your initial investment and therefore you should not invest money that you cannot afford to lose. You should be aware of all the risks associated with foreign exchange trading and seek advice from an independent financial advisor if you have any doubts. This software is for educational and research purposes only and does not constitute financial advice.*