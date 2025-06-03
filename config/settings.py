import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional, Type

import yaml
from pydantic import (
    BaseSettings,
    Field,
    PostgresDsn,
    RedisDsn,
    validator,
)

from fx_trader.config.trading_params import TradingParameters

logger = logging.getLogger(__name__)


def yaml_config_settings_source(settings: BaseSettings) -> Dict[str, Any]:
    """
    A Pydantic settings source that loads variables from a YAML file.
    Allows for a `config.dev.yaml` for local overrides.
    """
    config_file_path_str = os.getenv(
        "CONFIG_FILE_PATH", "config/config.dev.yaml")
    config_file_path = Path(config_file_path_str)

    if config_file_path.exists():
        logger.info(
            f"Loading configuration from YAML file: {config_file_path}")
        with open(config_file_path, "r") as f:
            try:
                return yaml.safe_load(f) or {}
            except yaml.YAMLError as e:
                logger.error(
                    f"Error parsing YAML config file {config_file_path}: {e}")
                return {}
    logger.warning(
        f"YAML config file not found at {config_file_path}. "
        "Relying on environment variables and defaults."
    )
    return {}


class Settings(BaseSettings):
    # --- API Keys & Access Credentials ---
    OANDA_ACCOUNT_ID: str = Field(..., env="OANDA_ACCOUNT_ID")
    OANDA_ACCESS_TOKEN: str = Field(..., env="OANDA_ACCESS_TOKEN")
    OANDA_ENVIRONMENT: str = Field(
        default="practice", env="OANDA_ENVIRONMENT")  # 'practice' or 'live'

    FRED_API_KEY: Optional[str] = Field(None, env="FRED_API_KEY")
    ALPHAVANTAGE_API_KEY: Optional[str] = Field(
        None, env="ALPHAVANTAGE_API_KEY")

    # --- Vault Configuration ---
    VAULT_ADDR: str = Field(default="http://localhost:8200", env="VAULT_ADDR")
    VAULT_ROLE_ID: Optional[str] = Field(None, env="VAULT_ROLE_ID")
    VAULT_SECRET_ID: Optional[str] = Field(None, env="VAULT_SECRET_ID")
    # For token-based auth if not AppRole
    VAULT_TOKEN: Optional[str] = Field(None, env="VAULT_TOKEN")
    VAULT_KV_MOUNT_POINT: str = Field(
        default="secret", env="VAULT_KV_MOUNT_POINT")
    VAULT_SECRET_PATH: str = Field(
        default="fx_trader/api_keys", env="VAULT_SECRET_PATH")
    VAULT_RENEW_TOKEN: bool = Field(default=True, env="VAULT_RENEW_TOKEN")
    VAULT_CACHE_TTL_SECONDS: int = Field(
        default=300, env="VAULT_CACHE_TTL_SECONDS")  # 5 minutes

    # --- Infrastructure URLs & Credentials ---
    DB_USER: str = Field(default="fx_user", env="DB_USER")
    DB_PASSWORD: str = Field(default="fx_password", env="DB_PASSWORD")
    DB_HOST: str = Field(default="localhost", env="DB_HOST")
    DB_PORT: int = Field(default=5432, env="DB_PORT")
    DB_NAME: str = Field(default="fx_trader_db", env="DB_NAME")
    POSTGRES_DSN: Optional[PostgresDsn] = None  # Assembled below

    @validator("POSTGRES_DSN", pre=True, always=True)
    def assemble_postgres_dsn(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            user=values.get("DB_USER"),
            password=values.get("DB_PASSWORD"),
            host=values.get("DB_HOST"),
            port=str(values.get("DB_PORT")),
            path=f"/{values.get('DB_NAME') or ''}",
        )

    MLFLOW_TRACKING_URI: str = Field(
        default="http://localhost:5001", env="MLFLOW_TRACKING_URI")
    MLFLOW_S3_ENDPOINT_URL: str = Field(
        default="http://localhost:9000", env="MLFLOW_S3_ENDPOINT_URL")
    MLFLOW_ARTIFACT_ROOT: str = Field(
        default="s3://mlflow-artifacts", env="MLFLOW_ARTIFACT_ROOT")
    AWS_ACCESS_KEY_ID: Optional[str] = Field(
        None, env="AWS_ACCESS_KEY_ID")  # For MinIO/S3
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(
        None, env="AWS_SECRET_ACCESS_KEY")  # For MinIO/S3

    FEAST_REGISTRY_PATH: str = Field(
        default="feature_store/registry.db", env="FEAST_REGISTRY_PATH")
    FEAST_OFFLINE_STORE_PATH: str = Field(
        default="feature_store/data/offline_store.parquet", env="FEAST_OFFLINE_STORE_PATH")
    FEAST_ONLINE_STORE_CONFIG_PATH: str = Field(
        default="feature_store/online_store.yaml", env="FEAST_ONLINE_STORE_CONFIG_PATH")

    REDIS_HOST: str = Field(default="localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, env="REDIS_PORT")
    REDIS_DB_APP: int = Field(default=0, env="REDIS_DB_APP")
    REDIS_DB_FEAST: int = Field(default=1, env="REDIS_DB_FEAST")
    REDIS_URL: Optional[RedisDsn] = None  # Assembled below for app Redis

    @validator("REDIS_URL", pre=True, always=True)
    def assemble_redis_url(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return RedisDsn.build(
            scheme="redis",
            host=values.get("REDIS_HOST"),
            port=str(values.get("REDIS_PORT")),
            path=f"/{values.get('REDIS_DB_APP') or 0}",
        )

    # --- Notification Service (Telegram) ---
    TELEGRAM_BOT_TOKEN: Optional[str] = Field(None, env="TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID: Optional[str] = Field(None, env="TELEGRAM_CHAT_ID")

    # --- Trading Parameters ---
    # This will instantiate TradingParameters and load its values from ENV VARS if they are set,
    # otherwise defaults from TradingParameters model will be used.
    # ENV VARS for TradingParameters should be prefixed, e.g., FX_TRADER_MAX_POSITIONS_PER_CURRENCY
    TRADING: TradingParameters = Field(default_factory=TradingParameters)

    # --- General Application Settings ---
    # DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    # development, staging, production
    APP_ENV: str = Field(default="development", env="APP_ENV")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        # env_nested_delimiter = '__' # If you want to set TRADING__MAX_POSITIONS_PER_CURRENCY
        # Optional: prefix for all env vars, e.g. FX_TRADER_OANDA_ACCOUNT_ID
        env_prefix = "FX_TRADER_"

        @classmethod
        def customise_sources(
            cls,
            init_settings,
            env_settings,
            file_secret_settings,
        ):
            return (
                init_settings,
                env_settings,
                yaml_config_settings_source,  # Load from YAML first
                file_secret_settings,
            )


settings = Settings()

# Example: Accessing a trading parameter
# print(settings.TRADING.MAX_DRAWDOWN_PCT)
# Example: Accessing a general setting
# print(settings.OANDA_ACCOUNT_ID)
