# MrWebDefence-LogServer

[![CI/CD - LogServer Tests](https://github.com/kencom2400/MrWebDefence-LogServer/actions/workflows/ci.yml/badge.svg)](https://github.com/kencom2400/MrWebDefence-LogServer/actions/workflows/ci.yml)

このリポジトリは、MrWebDefenceシステムのログ収集・管理サーバーです。

## 📋 現在のステータス

**Phase**: 実装完了

Task 8.1（ログ収集機能実装）が完了し、Fluentd ベースの実装でテスト済みです。

## 📖 ドキュメント

- [設計書: Task 8.1 ログ収集機能](docs/design/MWD-53-log-collection.md)

## 🎯 プロジェクト概要

MrWebDefence-Engine（WAFエンジン）から転送されるログを受信し、正規化・保存する機能を提供します。

### 主な機能

- **ログ受信**: HTTP経由でのログ受信（Engine Fluentdから）✅
- **ログ正規化**: メタデータ追加・Path Traversal対策 ✅
- **バッファリング**: 時間ベース・サイズベースのチャンキング（DoS対策付き）✅
- **ファイルストレージ**: gzip圧縮・時間別自動ローテーション ✅
- **モニタリング**: Prometheusメトリクス・ヘルスチェックエンドポイント ✅

### システムアーキテクチャ

```
[MrWebDefence-Engine]
WAF (Nginx + OpenAppSec)
  ↓ ログファイル（共有ボリューム）
Engine Fluentd
  ↓ HTTP/JSON + Bearer認証
[MrWebDefence-LogServer]
LogServer Fluentd (HTTP受信)
  ↓ フィルタ・正規化
  ↓ バッファリング
File Storage (gzip圧縮・時間別)
```

詳細は[設計書](docs/design/MWD-53-log-collection.md)を参照してください。

## 🚀 セットアップ

### 必要要件

- Docker & Docker Compose
- curl（テスト用）

### インストール

```bash
# リポジトリをクローン
git clone https://github.com/kencom2400/MrWebDefence-LogServer.git
cd MrWebDefence-LogServer

# 環境変数ファイルを作成
cp .env.example .env
# 必要に応じて .env を編集
```

### 設定

`.env` ファイルで設定をカスタマイズ:

```bash
# Fluentdログレベル（trace, debug, info, warn, error, fatal）
FLUENTD_LOG_LEVEL=info

# Fluentdワーカー数（デフォルト: 2）
FLUENTD_WORKERS=2

# モニタリングエンドポイントのバインドアドレス（デフォルト: 127.0.0.1）
# 127.0.0.1 - ローカルホストのみ（最も安全、推奨）
# 0.0.0.0 - 全インターフェース公開（VPCやファイアウォールで制御すること）
# 特定IP - 特定のサブネットIPアドレス（例: 10.0.1.100）
MONITORING_BIND_ADDR=127.0.0.1
```

### Engine側との連携

**Engine側の設定** (`MrWebDefence-Engine`):

Engine側の Fluentd 設定で以下の環境変数を設定してください:

```bash
# LogServerのURL（HTTP）
FLUENTD_OUTPUT_URL=http://logserver:8888/

# Bearer認証トークン（Engine側が送信、LogServerは検証しない）
FLUENTD_OUTPUT_AUTH=your-bearer-token-here
```

Engine側の設定例（`docker/fluentd/forwarder.d/http-output.conf`）:

```xml
<match {nginx,openappsec}.**>
  @type http
  endpoint "#{ENV['FLUENTD_OUTPUT_URL']}"
  http_method post
  <headers>
    Authorization "Bearer #{ENV['FLUENTD_OUTPUT_AUTH']}"
  </headers>
  
  <buffer>
    @type file
    path /var/log/fluentd/buffer/to_logserver
    flush_interval 5s
    flush_at_shutdown true
  </buffer>
</match>
```

### セキュリティに関する注意

本実装では、LogServer側でBearer認証の検証は行っていません。必要に応じて以下の対策を検討してください:

1. **ネットワーク分離**: LogServerをプライベートネットワークに配置し、EngineからのみアクセスできるようにFirewallで制限
2. **リバースプロキシ**: Nginx等でBearerトークンの検証を実施
3. **VPN/VPC**: Engine-LogServer間をVPNまたはVPC内通信に限定

### 起動

```bash
# 本番環境用
docker compose up -d

# ログの確認
docker compose logs -f fluentd
```

### ヘルスチェック

LogServerが正常に起動しているか確認:

```bash
# ヘルスチェックエンドポイント（コンテナ内から）
docker exec mrwebdefence-logserver curl -f http://localhost:8889/health

# Prometheusメトリクス（デフォルトではローカルホストのみ）
# MONITORING_BIND_ADDR=0.0.0.0 の場合に外部からアクセス可能
curl http://localhost:24231/metrics
```

**モニタリングエンドポイントの公開範囲について:**

デフォルトでは、モニタリングエンドポイント（24220, 24231）は`127.0.0.1`にバインドされ、コンテナ内からのみアクセス可能です。外部のモニタリングシステム（Prometheus等）から収集する場合は、`.env`で以下のように設定してください:

```bash
# 特定のサブネットからのみアクセス許可（推奨）
MONITORING_BIND_ADDR=10.0.1.100  # LogServerのプライベートIP

# またはファイアウォールで制御した上で全公開
MONITORING_BIND_ADDR=0.0.0.0
```

## 🧪 テスト

### テストの実行

```bash
# すべてのテストを実行
./tests/scripts/test-config.sh      # 設定検証
./tests/scripts/test-http-input.sh  # HTTP入力テスト
./tests/scripts/test-security.sh    # セキュリティテスト
./tests/scripts/test-e2e.sh         # E2Eテスト
```

### テストログの送信

```bash
# Nginxログを送信
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%S+00:00")
curl -X POST http://localhost:8888/nginx.access \
  -H "Content-Type: application/json" \
  -d "{
    \"time\":\"${TIMESTAMP}\",
    \"customer_name\":\"test-customer\",
    \"fqdn\":\"example.com\",
    \"message\":\"test log\",
    \"status\":200
  }"

# OpenAppSecセキュリティログを送信
curl -X POST http://localhost:8888/openappsec.security \
  -H "Content-Type: application/json" \
  -d "{
    \"time\":\"${TIMESTAMP}\",
    \"customer_name\":\"test-customer\",
    \"fqdn\":\"example.com\",
    \"message\":\"security event\",
    \"severity\":\"high\"
  }"
```

### ログファイルの確認

```bash
# ログファイルの場所を確認
docker exec mrwebdefence-logserver find /var/log/mrwebdefence/logs -name "*.log.gz"

# ログ内容を確認
docker exec mrwebdefence-logserver zcat /var/log/mrwebdefence/logs/access.YYYYMMDDHH_0.log.gz | jq .
```

### CIでのテスト実行

GitHub Actionsで自動的にテストが実行されます:

- **Configuration Validation**: Fluentd設定の文法チェック
- **HTTP Input Test**: ログ受信の基本機能テスト
- **Security Test**: Path Traversal対策の検証
- **E2E Integration Test**: エンドツーエンドのログフロー検証
- **ShellCheck**: シェルスクリプトの静的解析
- **Docker Build**: Dockerイメージのビルドテスト

## 📁 プロジェクト構造

```
MrWebDefence-LogServer/
├── config/
│   └── fluentd/
│       ├── fluent.conf              # メイン設定
│       └── conf.d/
│           ├── 01-source.conf       # 入力設定（HTTP受信）
│           ├── 02-filter.conf       # フィルタ設定（正規化）
│           └── 03-output.conf       # 出力設定（ファイル保存）
├── tests/
│   └── scripts/
│       ├── test-config.sh           # 設定検証
│       ├── test-http-input.sh       # HTTP入力テスト
│       ├── test-security.sh         # セキュリティテスト
│       └── test-e2e.sh              # E2Eテスト
├── docker-compose.yml               # 本番用
├── docker-compose.test.yml          # テスト用
├── Dockerfile                       # Fluentdイメージ
└── docs/
    └── design/
        └── MWD-53-log-collection.md # 設計書
```

## 📊 モニタリング

### エンドポイント

- **ログ受信**: `http://localhost:8888/` (nginx.access, openappsec.security 等)
- **ヘルスチェック**: `http://localhost:8889/health` (コンテナ内から)
- **モニタリング**: `http://localhost:24220/` (Fluentd monitor_agent)
- **メトリクス**: `http://localhost:24231/metrics` (Prometheus形式)

### ログ出力先

- **正常ログ**: `/var/log/mrwebdefence/logs/access.YYYYMMDDHH_N.log.gz`
- **処理不能ログ**: `/var/log/fluentd/unmatched/unmatched.YYYYMMDDHH_0.log`

### バッファ

- **ストレージバッファ**: `/var/log/fluentd/buffer/storage/`
- **Unmatchedバッファ**: `/var/log/fluentd/buffer/unmatched/`

## 🔗 関連リポジトリ

- [MrWebDefence-Engine](https://github.com/kencom2400/MrWebDefence-Engine) - WAFエンジン（ログ送信側）
  - [MWD-40: ログ転送機能実装 実装設計書](https://github.com/kencom2400/MrWebDefence-Engine/blob/main/docs/design/MWD-40-implementation-plan.md)
  - Engine側の設定: `docker/fluentd/forwarder.d/http-output.conf`

## 🛠️ トラブルシューティング

### Fluentdが起動しない

```bash
# ログを確認
docker compose logs fluentd

# 設定ファイルの検証
docker compose exec fluentd fluentd --dry-run -c /fluentd/etc/fluent.conf
```

### ログが受信されない

```bash
# Fluentdプロセスが起動しているか確認
docker exec mrwebdefence-logserver pgrep -f fluentd

# ポート8888が利用可能か確認
curl -v http://localhost:8888/

# Fluentdのログを確認
docker compose logs -f fluentd | grep -i "error\|warn"
```

### ファイルが出力されない

```bash
# バッファにデータがあるか確認
docker exec mrwebdefence-logserver ls -la /var/log/fluentd/buffer/storage/

# フラッシュ設定の確認（flush_interval: 10s）
# ログ送信後15秒待機してから確認

# 出力先ディレクトリの権限確認
docker exec mrwebdefence-logserver ls -la /var/log/mrwebdefence/logs/
```

## ライセンス

Proprietary
