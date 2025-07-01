import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# プロジェクトのルートディレクトリを設定
from pathlib import Path
import sys

# プロジェクトのルートをPythonのパスに追加
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

# 環境変数をロード
from dotenv import load_dotenv
load_dotenv()

# 設定をインポート
from fx_trader.config import settings

# Alembicの設定を取得
config = context.config

# データベースURLを設定
config.set_main_option('sqlalchemy.url', settings.DATABASE_URL)

# モデルをインポートしてメタデータを取得
from fx_trader.db.base import Base
target_metadata = Base.metadata

# ロギング設定
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# コンテキストの設定
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
