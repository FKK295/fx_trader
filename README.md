# FX 自動売買システム

[![CI Status](https://github.com/FKK295/fx_trader/actions/workflows/ci.yml/badge.svg)](https://github.com/FKK295/fx_trader/actions/workflows/ci.yml)

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)

本プロジェクトは、Pythonで構築されたアルゴリズム取引システムの開発、バックテスト、本番運用を支援するための包括的なプラットフォームです。FastAPIによるAPI、コンテナ技術、MLOpsツール、監視基盤などを統合し、再現性と拡張性の高い取引環境の構築を目指します。

## 目次

- [主な特徴](#主な特徴)
- [技術スタック](#技術スタック)
- [クイックスタート](#クイックスタート)
- [開発ガイド](#開発ガイド)
- [API ドキュメント](#api-ドキュメント)
- [デプロイガイド](#デプロイガイド)
- [ディレクトリ構成](#ディレクトリ構成)
- [貢献方法](#貢献方法)
- [ライセンス](#ライセンス)

## 主な特徴

- **モジュラー設計**: データ収集、特徴量エンジニアリング、モデル学習、注文実行、リスク管理を明確に分離
- **MLOps統合**: MLflowによる実験管理、Optunaによるハイパーパラメータ最適化、Evidently AIによるドリフト検出
- **堅牢なバックテスト**: backtraderエンジンとDaskによる並列処理、QuantStatsによる詳細なパフォーマンス分析
- **包括的な監視**: Prometheus、Grafana、Alertmanagerを活用したリアルタイム監視
- **コンテナ化**: DockerとDocker Composeによる一貫した開発・本番環境
- **セキュアな構成**: HashiCorp Vaultによるシークレット管理、RBAC対応

## 技術スタック

### コア技術
- **言語**: Python 3.10+
- **APIフレームワーク**: FastAPI, Uvicorn
- **データベース**: PostgreSQL 14+, Redis 6+
- **コンテナ化**: Docker, Docker Compose, Kubernetes

### データ処理 & 機械学習
- **データ操作**: Pandas, NumPy, Dask
- **特徴量管理**: Feast
- **データ品質**: Great Expectations
- **MLOps**: MLflow, Optuna, Evidently AI
- **機械学習**: Scikit-learn, XGBoost

### バックテスト & 取引
- **バックテストエンジン**: backtrader
- **パフォーマンス分析**: QuantStats
- **ブローカー統合**: OANDA, MT5 (MetaTrader 5)

### 監視 & 運用
- **メトリクス**: Prometheus
- **可視化**: Grafana
- **アラート**: Alertmanager, Telegram Bot API
- **ロギング**: structlog, ELK Stack (オプション)

### 開発ツール
- **依存関係管理**: Poetry
- **コード品質**: Black, isort, Flake8, Mypy
- **テスト**: pytest, mutmut, pytest-cov
- **CI/CD**: GitHub Actions
- **ドキュメント**: Sphinx, MkDocs

### オーケストレーション (オプション)
- **ワークフロー管理**: Airflow, Prefect
- **スケジューリング**: Celery, RQ

## 環境構築ガイド

### 前提条件

- **Docker**: 20.10 以上
- **Docker Compose**: 2.0 以上
- **Git**: 最新バージョン推奨

### 1. リポジトリのクローン

```bash
git clone https://github.com/FKK295/fx_trader.git
cd fx_trader
```

### 2. 環境変数の設定

```bash
# 環境変数テンプレートをコピー
cp .env.example .env

# .env ファイルを編集（必要に応じて）
# 主な設定項目：
# - POSTGRES_*: データベース接続情報
# - REDIS_*: Redis接続情報
# - OANDA_*: OANDA API認証情報
# - MLFLOW_TRACKING_URI: MLflowトラッキングサーバーURI
```

### 3. コンテナのビルドと起動

サービスは依存関係に基づいて段階的に起動します。一部のサービスは完全に起動するまでに時間を要するため、段階的な起動を推奨します。

#### オプション1: 推奨 - 段階的起動

```bash
# 1. 基盤サービスのみを起動
docker-compose up -d postgres redis minio vault mlflow_server

# 2. 監視サービスの起動
docker-compose up -d prometheus grafana alertmanager

# 3. アプリケーションの起動
docker-compose up -d --build app

# アプリケーションのログを確認（Ctrl+Cで終了）
docker-compose logs -f app
```

#### オプション2: シンプルな起動（開発用）

```bash
# すべてのサービスを一度に起動
docker-compose up -d --build
```

> **トラブルシューティング**: アプリケーションが依存サービスに接続できない場合は、以下のコマンドで各サービスの状態を確認してください。
> 
> ```bash
> # 全サービスの状態確認
> docker-compose ps
> 
> # データベース接続確認
> docker-compose exec postgres pg_isready
> 
> # Redis接続確認
> docker-compose exec redis_app redis-cli ping
> 
> # Vaultの状態確認
> docker-compose exec vault vault status
> 
> # コンテナの再ビルド（必要に応じて）
> docker-compose build --no-cache
> ```

### 4. 初期設定

<details>
<summary>Vault の設定（開発モード）

```bash
# Vault コンテナ内で実行（自動的に初期化・アンシール済み）
docker-compose exec vault vault status

# 開発用ルートトークンでログイン
docker-compose exec vault vault login root-token

# シークレットの設定例（.env.example に基づく）
docker-compose exec vault vault kv put secret/application/docker \
  OANDA_ACCOUNT_ID=YOUR_OANDA_ACCOUNT_ID_HERE \
  OANDA_ACCESS_TOKEN=YOUR_OANDA_ACCESS_TOKEN_HERE \
  OANDA_ENVIRONMENT=practice \
  FRED_API_KEY=YOUR_FRED_API_KEY_HERE \
  ALPHAVANTAGE_API_KEY=YOUR_ALPHAVANTAGE_API_KEY_HERE \
  DB_USER=fx_user \
  DB_PASSWORD=fx_password \
  AWS_ACCESS_KEY_ID=minioadmin \
  AWS_SECRET_ACCESS_KEY=minioadmin \
  TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN_HERE \
  TELEGRAM_CHAT_ID=YOUR_TELEGRAM_CHAT_ID_HERE
```
</details>

<details>
<summary>MinIO バケットの作成

1. ブラウザで [MinIO コンソール](http://localhost:9001) にアクセス
2. ログイン（デフォルト: minioadmin / minioadmin）
3. 左メニューから「Buckets」を選択し、「Create Bucket」をクリック
4. 以下のバケットを作成：
   - mlflow-artifacts
   - models
   - datasets
   - features
   - artifacts
5. 各バケットのアクセスポリシーを「public」に設定

または、コマンドラインで作成する場合：

```bash
docker-compose exec minio sh -c '
  mc alias set local http://localhost:9000 minioadmin minioadmin && \
  for bucket in mlflow-artifacts models datasets features artifacts; do \
    mc mb local/$bucket && \
    mc policy set download local/$bucket && \
    mc policy set upload local/$bucket && \
    mc policy set list local/$bucket && \
    mc policy set delete local/$bucket; \
  done'
```
</details>

### 5. データベースの初期化

```bash
# マイグレーション用のディレクトリを作成（初回のみ）
mkdir -p fx_trader/db/migrations/versions

# マイグレーションの初期化（初回のみ）
docker-compose exec app alembic revision --autogenerate -m "Initial migration"

# マイグレーションの適用
docker-compose exec app alembic upgrade head
```

### 6. アプリケーションの動作確認

#### API ドキュメント
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

#### 管理ツール
- **MLflow UI**: http://localhost:5001
- **MinIO コンソール**: http://localhost:9001
- **Grafana ダッシュボード**: http://localhost:3000
- **Prometheus**: http://localhost:9090
- **Alertmanager**: http://localhost:9093

## 開発ツール

### コマンド実行方法

すべてのコマンドはコンテナ内で実行することを推奨します：

```bash
# コンテナ内で対話的にコマンドを実行
docker-compose exec app bash

# または、直接コマンドを実行
docker-compose exec app <command>
```

### よく使うコマンド

<details>
<summary>コードフォーマット</summary>

```bash
docker-compose exec app black .
docker-compose exec app isort .
docker-compose exec app flake8 .
```
</details>

<details>
<summary>テストの実行</summary>

```bash
# すべてのテストを実行
docker-compose exec app pytest

# カバレッジレポート付きで実行
docker-compose exec app pytest --cov=fx_trader tests/

# 特定のテストを実行
docker-compose exec app pytest tests/unit/test_models.py -v
```
</details>

<details>
<summary>データベースマイグレーション</summary>

```bash
# マイグレーションファイルの自動作成
docker-compose exec app alembic revision --autogenerate -m "説明文"

# マイグレーションの適用
docker-compose exec app alembic upgrade head
```
</details>

## トラブルシューティング

<details>
<summary>コンテナが起動しない場合</summary>

1. ログを確認：
   ```bash
   docker-compose logs <service_name>
   ```

2. 依存関係の問題を確認：
   ```bash
   docker-compose build --no-cache
   docker-compose up -d
   ```
</details>

<details>
<summary>データベース接続エラー</summary>

1. データベースが起動しているか確認：
   ```bash
   docker-compose ps | grep postgres
   ```

2. 接続情報を確認：
   ```bash
   docker-compose exec app env | grep POSTGRES_
   ```
</details>

<details>
<summary>Vault の設定がリセットされた</summary>

開発モードでは、コンテナを再起動するとVaultのデータはリセットされます。
永続化する場合は、`docker-compose.yml` のVault設定を本番モードに変更してください。
</details>

### 7. 動作確認

```bash
# ヘルスチェック
curl http://localhost:8000/health

# バージョン確認
curl http://localhost:8000/version
```

## API ドキュメント

### 基本情報

- **ベースURL**: `http://localhost:8000/api/v1`
- **認証**: JWTベアートークン
- **レスポンス形式**: JSON
- **レート制限**: 認証済み 60リクエスト/分、未認証 10リクエスト/分

### 認証

#### トークン取得
```http
POST /api/v1/auth/token
Content-Type: application/x-www-form-urlencoded

username=your_username&password=your_password
```

#### リクエストヘッダー
```
Authorization: Bearer {access_token}
Content-Type: application/json
```

### 主要エンドポイント

#### 1. アカウント管理
| エンドポイント | メソッド | 説明 | 認証 |
|--------------|---------|------|------|
| `/accounts` | GET | アカウント一覧 | 必須 |
| `/accounts` | POST | 新規アカウント作成 | 必須 |
| `/accounts/{id}` | GET | アカウント詳細 | 必須 |
| `/accounts/{id}/balance` | GET | 残高確認 | 必須 |

#### 2. トレード管理
| エンドポイント | メソッド | 説明 | 認証 |
|--------------|---------|------|------|
| `/trades` | GET | トレード一覧 | 必須 |
| `/trades` | POST | 新規トレード実行 | 必須 |
| `/trades/{id}` | GET | トレード詳細 | 必須 |
| `/trades/summary` | GET | トレードサマリー | 必須 |

#### 3. マーケットデータ
| エンドポイント | メソッド | 説明 | パラメータ |
|--------------|---------|------|-----------|
| `/market/rates/{pair}` | GET | 為替レート | `pair`: 通貨ペア (例: USD_JPY) |
| `/market/ohlc/{pair}` | GET | OHLCデータ | `interval`: 間隔 (1m, 5m, 15m, 1h, 1d) |
| `/market/orderbook/{pair}` | GET | 板情報 | `depth`: 取得深さ (デフォルト: 10) |

#### 4. 戦略管理
| エンドポイント | メソッド | 説明 | 認証 |
|--------------|---------|------|------|
| `/strategies` | GET | 戦略一覧 | 必須 |
| `/strategies` | POST | 新規戦略作成 | 必須 |
| `/strategies/{id}` | GET | 戦略詳細 | 必須 |
| `/strategies/{id}/backtest` | POST | バックテスト実行 | 必須 |

### レスポンス形式

#### 成功レスポンス
```json
{
  "success": true,
  "data": {
    // レスポンスデータ
  },
  "message": "Operation completed",
  "timestamp": "2025-06-28T01:23:45.678901"
}
```

#### エラーレスポンス
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Error description",
    "details": {
      // 追加のエラー詳細
    }
  },
  "message": "Operation failed",
  "timestamp": "2025-06-28T01:23:45.678901"
}
```

### エラーコード

| コード | 説明 | HTTP ステータス |
|-------|------|----------------|
| 1001 | 認証エラー | 401 |
| 1002 | 権限エラー | 403 |
| 1003 | リソースが見つかりません | 404 |
| 2001 | バリデーションエラー | 400 |
| 2002 | レート制限超過 | 429 |
| 3001 | 内部サーバーエラー | 500 |

### インタラクティブドキュメント

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

## ディレクトリ構成

```
fx_trader/
├── .github/               # GitHub Actions ワークフロー
├── .vscode/               # VSCode 設定
├── config/                # 設定ファイル
├── data/                  # データファイル
│   ├── models/            # 学習済みモデル
│   └── datasets/          # データセット
├── docker/                # Docker関連ファイル
├── docs/                  # ドキュメント
├── feature_store/         # 特徴量ストア設定 (Feast)
│   ├── data_sources.py    # データソース定義
│   ├── entities.py        # エンティティ定義
│   └── feature_views/     # 特徴量ビュー定義
├── fx_trader/             # メインアプリケーション
│   ├── __init__.py
│   ├── main.py            # エントリーポイント (FastAPIアプリケーション)
│   ├── api/               # APIルーター
│   ├── core/              # コア機能
│   ├── db/                # データベース設定
│   ├── models/            # SQLAlchemyモデル
│   ├── schemas/           # Pydanticスキーマ
│   └── services/          # ビジネスロジック
├── notebooks/             # Jupyterノートブック
├── scripts/               # ユーティリティスクリプト
├── tests/                 # テスト
├── .env.example          # 環境変数テンプレート
├── .gitignore
├── docker-compose.yml     # Docker Compose設定
├── Dockerfile            # アプリケーションDockerfile
├── poetry.lock           # 依存関係ロックファイル
└── pyproject.toml        # プロジェクト設定
```

## 貢献方法

### 開発フロー

1. **Issueの作成**
   - 機能追加やバグ修正の前にIssueを作成
   - 既存のIssueを確認し、重複を避ける
   - テンプレートに従って必要な情報を記入

2. **ブランチ戦略**
   - `main`: 安定版リリースブランチ（保護済み）
   - `develop`: 開発ブランチ（保護済み）
   - `feature/*`: 新機能開発用（例: `feature/add-user-auth`）
   - `bugfix/*`: バグ修正用（例: `bugfix/fix-login-issue`）
   - `hotfix/*`: 緊急修正用（例: `hotfix/security-patch`）
   - `docs/*`: ドキュメント更新用

3. **プルリクエスト**
   - 1つのPRは1つの機能/修正に絞る
   - タイトルは変更内容を簡潔に記述
   - 説明欄には以下の項目を含める：
     - 変更内容の詳細
     - 変更の背景・目的
     - テスト方法
     - スクリーンショット（UI変更の場合）
     - 関連するIssue番号（`Closes #123` など）
   - コードレビューを依頼する前に、CIがパスすることを確認

### コーディング規約

- **コードスタイル**: Black と isort で自動フォーマット
  ```bash
  # コードのフォーマット
  black .
  isort .
  ```

- **型ヒント**: すべての関数・メソッドに型ヒントを付与
  ```python
  def get_user(user_id: int) -> User:
      """ユーザーを取得します。
      
      Args:
          user_id: ユーザーID
          
      Returns:
          User: ユーザーオブジェクト
          
      Raises:
          UserNotFoundError: ユーザーが存在しない場合
      """
  ```

- **ドキュメント**: 公開APIにはGoogleスタイルのdocstringを記述
- **テスト**: 新機能・修正には必ずテストを追加（カバレッジ80%以上を目標）

### コミットメッセージ

[Conventional Commits](https://www.conventionalcommits.org/) に従ってください：

```
<タイプ>[オプションのスコープ]: <説明>

[オプションの本文]

[オプションのフッター]
```

**タイプ**: 
- `feat`: 新機能
- `fix`: バグ修正
- `docs`: ドキュメントの変更
- `style`: コードの意味に影響しない変更（フォーマットなど）
- `refactor`: リファクタリング
- `perf`: パフォーマンス改善
- `test`: テストの追加・修正
- `chore`: ビルドプロセスやツールの変更

**例**:
```
feat(api): ユーザー認証APIを追加

- JWT認証を実装
- ログイン/ログアウトエンドポイントを追加
- ユーザー認証ミドルウェアを実装

Closes #123
```

### テスト

```bash
# すべてのテストを実行
pytest

# カバレッジレポート付きで実行
pytest --cov=fx_trader --cov-report=html

# 特定のテストを実行
pytest tests/unit/test_models.py -v

# 統合テストを実行
pytest tests/integration/ -v

# カバレッジレポートを表示
python -m http.server 8000 -d htmlcov/
```

### コードレビュー

- コードレビューは丁寧に行い、建設的なフィードバックを提供
- 指摘には必ず理由を添える
- 承認は最低2名のメンバーから得る
- セルフレビューを徹底する

### ドキュメントの更新

コード変更に伴い、以下のドキュメントも更新してください：
- APIドキュメント（docstring）
- README.md
- 関連するWikiページ

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 免責事項

このプロジェクトは、投資勧誘や金融商品の取引を推奨するものではありません。このソフトウェアを使用して生じたいかなる損害についても、開発者およびコントリビューターは一切の責任を負いません。

実際の取引を行う前に、必ず十分なテストを行い、リスクを十分に理解した上で自己責任でご利用ください。

## システムアーキテクチャ

```mermaid
graph TD
    A[ユーザー] -->|HTTP/WebSocket| B[APIサーバー (FastAPI)]
    B -->|gRPC/HTTP| C[MLモデルサーバー (BentoML)]
    B --> C
    C --> D[特徴量ストア (Feast)]
    D --> E[データソース]
    E -->|バッチ/ストリーム| F[データパイプライン (Airflow/Prefect)]
    F --> G[データレイク (MinIO)]
    G --> H[データ処理 (Spark/Dask)]
    H --> I[特徴量エンジニアリング]
    I --> D
    B --> J[メッセージブローカー (NATS/JetStream)]
    J --> K[ストラテジーワーカー (Python)]
    K --> L[取引実行 (OANDA v20)]
    K --> M[バックテストエンジン (Backtrader)]
    M --> N[パフォーマンス分析 (Pyfolio)]
    N --> O[可視化 (Grafana)]
    O --> P[ダッシュボード]
    P --> Q[アラート (AlertManager)]
    Q --> R[通知 (Slack/Email)]
    S[設定管理 (Vault)] --> B
    S --> K
    T[監視 (Prometheus)] --> B
    T --> K
    U[ログ管理 (Loki)] --> B
    U --> K
    V[トレーシング (Jaeger)] --> B
    V --> K

    subgraph 特徴量エンジニアリング
        Feast_FS[特徴量ストア (Feast)]
        特徴量定義[feature_store/feature_definitions.py]
    end

    subgraph モデルライフサイクル (MLOps)
        MLflow_サーバー[MLflow トラッキングサーバー]
        Vault[HashiCorp Vault]
        トレーニング[mlops/train.py w/ Optuna]
        再トレーニング[mlops/retrain.py w/ Evidently]
        予測モデル[models/forecast.py]
    end

    subgraph 取引ロジック
        シグナル生成[models/signals.py]
        バックテスター[backtest/runner.py w/ Backtrader & Dask]
        リスク管理[execution/risk_manager.py]
        ブローカークライアント[execution/*_broker_client.py]
    end

    subgraph ライブ取引
        ブローカーAPI[ブローカーAPI (OANDA/MT5)]
        APIサーバー[APIサーバー (FastAPI - オプション)]
        Celeryワーカー[Celeryワーカー (オプション)]
    end

    subgraph 監視とアラート
        Prometheus[Prometheus]
        Grafana[Grafana]
        Alertmanager[Alertmanager]
        Telegram[Telegram通知]
    end

    CLI_ユーザー --> オーケストレーター
    オーケストレーター -- トリガー --> OANDA_クライアント
    オーケストレーター -- トリガー --> FRED_クライアント
    オーケストレーター -- トリガー --> ニュース_クライアント
    OANDA_クライアント -- データ取得 --> MinIO
    FRED_クライアント -- データ取得 --> MinIO
    ニュース_クライアント -- データ取得 --> MinIO
    MinIO --> GreatExpectations
    GreatExpectations --> FeatureDefs
    FeatureDefs --> Feast_FS
    Feast_FS --> SignalGen
    SignalGen --> RiskManager
    RiskManager --> BrokerClient
    BrokerClient --> BrokerAPI
    RiskManager --> Backtester
    Backtester --> SignalGen
    SignalGen --> MLflow_Server
    MLflow_Server --> Train
    トレーニング --> 再トレーニング
    再トレーニング --> 予測モデル
    予測モデル --> シグナル生成
    シグナル生成 --> APIサーバー
    APIサーバー --> Celeryワーカー
    Celeryワーカー --> ブローカークライアント
    ブローカークライアント --> Prometheus
    Prometheus --> Grafana
    Prometheus --> Alertmanager
    Alertmanager --> Telegram
```

## 免責事項

外国為替証拠金取引には高いリスクが伴い、すべての投資家に適しているとは限りません。レバレッジの高さは、あなたに有利にも不利にも働く可能性があります。外国為替取引を始める前に、投資目的、経験レベル、リスク許容度を慎重に検討する必要があります。初期投資の一部または全部を失う可能性があり、失う余裕のない資金を投資すべきではありません。外国為替取引に関連するすべてのリスクを認識し、疑問がある場合は独立した金融アドバイザーに相談する必要があります。このソフトウェアは教育・研究目的のみを意図しており、金融アドバイスを構成するものではありません。

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は[LICENSE](LICENSE)ファイルをご覧ください。