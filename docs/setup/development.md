# 開発環境セットアップガイド

このドキュメントでは、FX Trader アプリケーションの開発環境をセットアップする手順を説明します。

## 前提条件

- Python 3.10 以上
- Docker と Docker Compose
- Git
- (オプション) pyenv または anyenv (Python バージョン管理用)

## セットアップ手順

### 1. リポジトリのクローン

```bash
git clone https://github.com/your-org/fx_trader.git
cd fx_trader
```

### 2. Python 環境のセットアップ

#### pyenv を使用する場合:

```bash
# Python バージョンのインストール
pyenv install 3.10.0

# プロジェクトディレクトリで使用するPythonバージョンを設定
pyenv local 3.10.0

# 仮想環境の作成と有効化
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# または
.venv\Scripts\activate    # Windows
```

### 3. 依存関係のインストール

```bash
# 開発用依存関係を含むすべてのパッケージをインストール
poetry install
```

### 4. 環境変数の設定

`.env` ファイルを作成し、必要な環境変数を設定します：

```bash
cp .env.example .env
```

`.env` ファイルを編集して、実際の値に置き換えてください。

### 5. データベースのセットアップ

Docker Compose を使用してデータベースを起動します：

```bash
docker-compose up -d postgres redis
```

### 6. データベースマイグレーションの実行

```bash
alembic upgrade head
```

### 7. 開発サーバーの起動

```bash
uvicorn fx_trader.app.main:app --reload
```

これで、開発サーバーが `http://localhost:8000` で起動します。

## 開発ワークフロー

### テストの実行

```bash
# すべてのテストを実行
pytest

# 特定のテストを実行
pytest tests/unit/test_models.py

# カバレッジレポート付きでテストを実行
pytest --cov=fx_trader tests/
```

### コードフォーマットとリンター

```bash
# コードのフォーマット
black .


# インポートのソート
isort .

# 型チェック
mypy .

# コードスタイルチェック
flake8
```

### コミット前のチェック

```bash
# コミット前フックを実行
pre-commit run --all-files
```

## トラブルシューティング

### 依存関係の競合が発生した場合

```bash
poetry lock  # 依存関係のロックファイルを更新
poetry install  # 依存関係を再インストール
```

### データベース接続エラーが発生した場合

1. Docker コンテナが実行中か確認：
   ```bash
   docker ps
   ```

2. コンテナのログを確認：
   ```bash
   docker-compose logs postgres
   ```

3. データベースを再作成：
   ```bash
   docker-compose down -v
docker-compose up -d postgres redis
alembic upgrade head
   ```

## ヘルプ

問題が解決しない場合は、以下の情報を添えて Issue を作成してください：

- 実行したコマンド
- エラーメッセージ
- オペレーティングシステムとバージョン
- Python バージョン (`python --version`)
- 関連するログ
