# 本番環境デプロイガイド

このドキュメントでは、FX Trader アプリケーションを本番環境にデプロイする手順を説明します。

## 前提条件

- Linux サーバー (Ubuntu 20.04/22.04 推奨)
- Docker と Docker Compose
- ドメイン名 (オプション、推奨)
- SSL 証明書 (Let's Encrypt 推奨)

## デプロイ手順

### 1. サーバーの準備

#### 1.1 必要なパッケージのインストール

```bash
# システムアップデート
sudo apt update && sudo apt upgrade -y

# 必要なパッケージのインストール
sudo apt install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git \
    nginx \
    certbot \
    python3-certbot-nginx
```

#### 1.2 Docker のインストール

```bash
# Docker の公式GPGキーを追加
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Docker リポジトリを設定
echo \
  "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Docker エンジンをインストール
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# 現在のユーザーを docker グループに追加
sudo usermod -aG docker $USER

# Docker Compose のインストール
sudo curl -L "https://github.com/docker/compose/releases/download/v2.3.3/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. アプリケーションのデプロイ

#### 2.1 リポジトリのクローン

```bash
# アプリケーションディレクトリを作成
sudo mkdir -p /opt/fx_trader
sudo chown $USER:$USER /opt/fx_trader
cd /opt/fx_trader

# リポジトリをクローン
git clone https://github.com/your-org/fx_trader.git .
```

#### 2.2 環境変数の設定

`.env` ファイルを作成し、本番環境用の設定を記述します：

```bash
cp .env.example .env
nano .env  # またはお好みのエディタで編集
```

以下の環境変数が正しく設定されていることを確認してください：

```env
# 本番環境設定
ENV=production
DEBUG=false
SECRET_KEY=your-secret-key-here

# データベース設定
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=fx_trader
POSTGRES_USER=fx_trader
POSTGRES_PASSWORD=your-secure-password

# Redis 設定
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=your-secure-password

# API 設定
API_V1_STR=/api/v1
SERVER_NAME=your-domain.com
SERVER_HOST=https://your-domain.com

# セキュリティ設定
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24時間
```

#### 2.3 SSL 証明書の取得 (Let's Encrypt)

Nginx を一時的に起動して、Let's Encrypt の検証を行います：

```bash
# Nginx 設定ファイルを作成
sudo tee /etc/nginx/sites-available/fx_trader << 'EOF'
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}
EOF

# シンボリックリンクを作成
sudo ln -sf /etc/nginx/sites-available/fx_trader /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl restart nginx

# certbot で SSL 証明書を取得
sudo mkdir -p /var/www/certbot
sudo certbot certonly --webroot -w /var/www/certbot -d your-domain.com -d www.your-domain.com
```

#### 2.4 Nginx の設定

```bash
# SSL 対応の Nginx 設定を作成
sudo tee /etc/nginx/sites-available/fx_trader << 'EOF'
upstream fx_trader {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # SSL 設定
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'TLS_AES_128_GCM_SHA256:TLS_AES_256_GCM_SHA384:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_session_tickets off;

    # セキュリティヘッダー
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self' https: data: 'unsafe-inline' 'unsafe-eval';" always;

    # ログ設定
    access_log /var/log/nginx/fx_trader_access.log;
    error_log /var/log/nginx/fx_trader_error.log;

    # アップロードサイズの制限
    client_max_body_size 10M;

    # ヘルスチェック
    location /health {
        proxy_pass http://fx_trader/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API リクエスト
    location /api {
        proxy_pass http://fx_trader;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # 静的ファイル
    location /static/ {
        alias /opt/fx_trader/static/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    # メンテナンスページ
    error_page 503 @maintenance;
    location @maintenance {
        if (-f /opt/fx_trader/maintenance.html) {
            return 503;
        }
        return 404;
    }
}
EOF

# 設定をテストして適用
sudo nginx -t && sudo systemctl restart nginx
```

#### 2.5 アプリケーションのビルドと起動

```bash
# Docker イメージのビルド
docker-compose -f docker-compose.prod.yml build

# データベースのマイグレーション
docker-compose -f docker-compose.prod.yml run --rm app alembic upgrade head

# アプリケーションの起動
docker-compose -f docker-compose.prod.yml up -d

# ログの確認
docker-compose -f docker-compose.prod.yml logs -f
```

### 3. セットアップの確認

アプリケーションが正しく起動したか確認します：

```bash
# コンテナの状態を確認
docker-compose -f docker-compose.prod.yml ps

# ヘルスチェック
curl -k https://your-domain.com/health
```

### 4. メンテナンス

#### 4.1 アプリケーションの更新

```bash
# 最新のコードを取得
cd /opt/fx_trader
git pull

# 依存関係の更新
docker-compose -f docker-compose.prod.yml build

# データベースのマイグレーション
docker-compose -f docker-compose.prod.yml run --rm app alembic upgrade head

# アプリケーションの再起動
docker-compose -f docker-compose.prod.yml up -d --no-deps app
```

#### 4.2 バックアップ

定期的なバックアップを設定します：

```bash
# バックアップ用スクリプトを作成
sudo tee /usr/local/bin/backup_fx_trader.sh << 'EOF'
#!/bin/bash

# バックアップディレクトリ
BACKUP_DIR="/var/backups/fx_trader/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# データベースのバックアップ
docker-compose -f /opt/fx_trader/docker-compose.prod.yml exec -T postgres pg_dump -U fx_trader fx_trader > "$BACKUP_DIR/db_dump.sql"

# アップロードファイルのバックアップ
cp -r /opt/fx_trader/uploads "$BACKUP_DIR/"

# 古いバックアップを削除 (30日以上前)
find /var/backups/fx_trader -type d -mtime +30 -exec rm -rf {} \;

echo "Backup completed: $BACKUP_DIR"
EOF

# スクリプトに実行権限を付与
sudo chmod +x /usr/local/bin/backup_fx_trader.sh

# 毎日午前3時にバックアップを実行するように設定
(crontab -l 2>/dev/null; echo "0 3 * * * /usr/local/bin/backup_fx_trader.sh") | crontab -
```

#### 4.3 ログローテーション

ログローテーションを設定します：

```bash
# ログローテーションの設定
sudo tee /etc/logrotate.d/fx_trader << 'EOF'
/var/log/nginx/fx_trader_*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 www-data adm
    sharedscripts
    postrotate
        [ -f /var/run/nginx.pid ] && kill -USR1 `cat /var/run/nginx.pid`
    endscript
}

/opt/fx_trader/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 $USER $USER
    sharedscripts
    postrotate
        docker-compose -f /opt/fx_trader/docker-compose.prod.yml kill -s USR1 app
    endscript
}
EOF
```

## トラブルシューティング

### アプリケーションが起動しない

```bash
# ログを確認
docker-compose -f docker-compose.prod.yml logs app

# コンテナの状態を確認
docker-compose -f docker-compose.prod.yml ps
```

### データベース接続エラー

```bash
# データベースのログを確認
docker-compose -f docker-compose.prod.yml logs postgres

# データベースに接続して確認
docker-compose -f docker-compose.prod.yml exec postgres psql -U fx_trader -d fx_trader
```

### SSL 証明書の更新

Let's Encrypt の証明書は90日で期限切れになります。自動更新を設定します：

```bash
# テスト用の更新
sudo certbot renew --dry-run

# 自動更新を設定
(crontab -l 2>/dev/null; echo "0 0,12 * * * /usr/bin/certbot renew --quiet") | crontab -
```

## セキュリティチェックリスト

- [ ] デフォルトのパスワードを変更しましたか？
- [ ] 不要なポートは閉じていますか？
- [ ] ファイアウォールは適切に設定されていますか？
- [ ] 定期的なセキュリティアップデートを適用していますか？
- [ ] バックアップは定期的に取得され、テストされていますか？

## サポート

問題が発生した場合は、以下の情報を添えてサポートチケットを作成してください：

1. エラーメッセージ
2. 関連するログ
3. 再現手順
4. 期待される動作と実際の動作
