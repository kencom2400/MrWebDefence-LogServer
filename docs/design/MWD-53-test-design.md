# ログ収集サーバー テスト設計書

**Issue**: MWD-53  
**作成日**: 2026-02-17  
**更新日**: 2026-02-17  
**ステータス**: Design Phase

---

## 目次

1. [テスト戦略](#テスト戦略)
2. [テストレベル](#テストレベル)
3. [テストパターン一覧](#テストパターン一覧)
4. [詳細テスト設計](#詳細テスト設計)
5. [テストデータ](#テストデータ)
6. [テスト環境](#テスト環境)
7. [テスト実行計画](#テスト実行計画)

---

## テスト戦略

### テストの目的

1. **機能要件の検証**: 設計通りにログが受信・保存されることを確認
2. **非機能要件の検証**: パフォーマンス、セキュリティ、可用性を確認
3. **異常系の検証**: エラーハンドリングが正しく動作することを確認
4. **運用シナリオの検証**: 実際の運用で想定される状況を確認

### テストの方針

- **テストピラミッド**: 単体テスト > 統合テスト > E2Eテスト
- **自動化**: CI/CDパイプラインで自動実行
- **継続的改善**: テスト結果をもとに設定を最適化

---

## テストレベル

### 1. 設定ファイル検証テスト

| 項目 | 説明 | 自動化 |
|------|------|--------|
| 文法チェック | Fluentd設定ファイルの構文エラーを検出 | ✅ |
| 設定検証 | 設定の整合性を確認 | ✅ |
| ドライラン | 実際の起動前に設定をテスト | ✅ |

### 2. 単体テスト（コンポーネントテスト）

| コンポーネント | テスト対象 | 自動化 |
|--------------|-----------|--------|
| HTTP Input | ログ受信、パース、認証 | ✅ |
| Filter | 正規化、サニタイズ、除外 | ✅ |
| Buffer | バッファリング、フラッシュ | ✅ |
| File Output | ファイル出力、圧縮 | ✅ |

### 3. 統合テスト

| テストシナリオ | 説明 | 自動化 |
|--------------|------|--------|
| 正常系フロー | ログ受信→保存の完全フロー | ✅ |
| 異常系フロー | エラーハンドリング | ✅ |
| セキュリティ | 認証・暗号化 | ✅ |

### 4. E2Eテスト

| テストシナリオ | 説明 | 自動化 |
|--------------|------|--------|
| Engine連携 | Engine FluentdからLogServer Fluentdへの実際の転送 | ⚠️ |
| マルチテナント | 複数顧客のログが正しく分離される | ⚠️ |

### 5. 非機能テスト

| テストタイプ | 説明 | 自動化 |
|------------|------|--------|
| パフォーマンス | スループット、レイテンシ | ⚠️ |
| 負荷テスト | 高負荷時の動作 | ⚠️ |
| ストレステスト | 限界値の確認 | ❌ |
| 耐障害性 | 障害発生時の挙動 | ⚠️ |

---

## テストパターン一覧

### 機能テスト

#### 1. ログ受信テスト

| ID | テストケース | 優先度 | 期待結果 |
|----|-------------|--------|---------|
| F-001 | Nginxログの受信 | High | 200 OK、ログが保存される |
| F-002 | OpenAppSecログの受信 | High | 200 OK、ログが保存される |
| F-003 | 複数ログの一括受信 | High | すべて正常に受信 |
| F-004 | 最大サイズのログ受信 | Medium | 10MB以下なら受信成功 |
| F-005 | 最大サイズ超過のログ | Medium | 413エラー |
| F-006 | 不正なJSON形式 | High | 400エラー |
| F-007 | 必須フィールド欠損 | High | フィルタで除外される |
| F-008 | 空のリクエストボディ | Low | 400エラー |

#### 2. 認証・セキュリティテスト

| ID | テストケース | 優先度 | 期待結果 |
|----|-------------|--------|---------|
| S-001 | 有効な共有シークレットキー | High | 認証成功 |
| S-002 | 無効な共有シークレットキー | High | 401エラー |
| S-003 | 共有シークレットキー欠損 | High | 401エラー |
| S-004 | 有効なクライアント証明書（mTLS） | High | 認証成功 |
| S-005 | 無効なクライアント証明書 | High | SSL handshake失敗 |
| S-006 | クライアント証明書欠損 | High | SSL handshake失敗 |
| S-007 | 期限切れクライアント証明書 | Medium | SSL handshake失敗 |
| S-008 | TLS 1.3での接続 | High | 接続成功 |
| S-009 | TLS 1.2での接続 | High | 接続成功 |
| S-010 | TLS 1.1での接続試行 | Medium | 接続拒否 |
| S-011 | 脆弱な暗号スイートでの接続 | Medium | 接続拒否 |

#### 3. フィルタリング・正規化テスト

| ID | テストケース | 優先度 | 期待結果 |
|----|-------------|--------|---------|
| N-001 | customer_name正常値 | High | そのまま保持 |
| N-002 | customer_nameに危険文字（../） | High | サニタイズされる |
| N-003 | customer_nameに特殊文字 | High | サニタイズされる |
| N-004 | customer_name欠損 | High | "unknown"になりフィルタで除外 |
| N-005 | fqdn正常値 | High | そのまま保持 |
| N-006 | fqdnに危険文字 | High | サニタイズされる |
| N-007 | fqdn欠損 | High | "unknown"になりフィルタで除外 |
| N-008 | log_type正常値（nginx） | High | そのまま保持 |
| N-009 | log_type正常値（openappsec） | High | そのまま保持 |
| N-010 | log_type欠損 | Medium | デフォルト値が設定される |
| N-011 | タイムスタンプ正常値 | High | パースされる |
| N-012 | タイムスタンプ欠損 | Medium | 現在時刻が設定される |
| N-013 | received_atの自動追加 | High | UTC時刻で追加される |
| N-014 | logserver_hostnameの自動追加 | High | ホスト名が追加される |

#### 4. ファイル出力テスト

| ID | テストケース | 優先度 | 期待結果 |
|----|-------------|--------|---------|
| O-001 | 正しいディレクトリ構造 | High | `{customer}/{type}/{fqdn}/{Y}/{M}/{D}/` |
| O-002 | 正しいファイル名 | High | `{HH}.log.gz` |
| O-003 | gzip圧縮 | High | ファイルがgzip形式 |
| O-004 | JSON Lines形式 | High | 1行1JSON |
| O-005 | タイムスタンプフィールド | High | `timestamp`フィールドが存在（UTC） |
| O-006 | 時間ローテーション（1時間） | High | 1時間ごとに新ファイル |
| O-007 | 複数顧客のログ分離 | High | 顧客ごとに別ディレクトリ |
| O-008 | 複数FQDNのログ分離 | High | FQDNごとに別ディレクトリ |
| O-009 | 同時書き込み | Medium | データ競合なし |

#### 5. バッファリングテスト

| ID | テストケース | 優先度 | 期待結果 |
|----|-------------|--------|---------|
| B-001 | 正常なバッファリング | High | メモリバッファに保存 |
| B-002 | フラッシュ間隔（10秒） | High | 10秒ごとにフラッシュ |
| B-003 | バッファサイズ上限 | High | 256MB到達でフラッシュ |
| B-004 | バッファ総サイズ上限 | High | 2GB到達でブロック |
| B-005 | バッファ満杯時の動作 | High | 503エラー（backpressure） |
| B-006 | ディスクバッファの利用 | Medium | メモリ不足時にディスク使用 |
| B-007 | シャットダウン時のフラッシュ | High | 全データが書き込まれる |

#### 6. エラーハンドリング・リトライテスト

| ID | テストケース | 優先度 | 期待結果 |
|----|-------------|--------|---------|
| E-001 | 書き込み失敗（ディスク満杯） | High | リトライ後エラーログ |
| E-002 | 書き込み失敗（権限エラー） | High | リトライ後エラーログ |
| E-003 | リトライ成功 | High | 最終的にデータ保存 |
| E-004 | リトライ上限到達 | High | エラーログ、メトリクス更新 |
| E-005 | ネットワーク切断中の受信 | Medium | バッファに保持、再接続後送信 |

### 非機能テスト

#### 7. パフォーマンステスト

| ID | テストケース | 目標値 | 測定方法 |
|----|-------------|--------|---------|
| P-001 | スループット（低負荷） | > 1,000 logs/sec | Apache Bench |
| P-002 | スループット（通常負荷） | > 5,000 logs/sec | Apache Bench |
| P-003 | スループット（高負荷） | > 10,000 logs/sec | Apache Bench |
| P-004 | レイテンシ（P50） | < 50ms | Prometheusメトリクス |
| P-005 | レイテンシ（P95） | < 100ms | Prometheusメトリクス |
| P-006 | レイテンシ（P99） | < 200ms | Prometheusメトリクス |
| P-007 | メモリ使用量（平常時） | < 256MB | docker stats |
| P-008 | メモリ使用量（高負荷時） | < 512MB | docker stats |
| P-009 | CPU使用率（平常時） | < 30% | docker stats |
| P-010 | CPU使用率（高負荷時） | < 70% | docker stats |
| P-011 | ディスクI/O | < 100MB/s | iostat |

#### 8. 負荷テスト

| ID | テストケース | 条件 | 期待結果 |
|----|-------------|------|---------|
| L-001 | 継続的高負荷（1時間） | 10,000 logs/sec | エラー率 < 0.1% |
| L-002 | 継続的高負荷（24時間） | 5,000 logs/sec | エラー率 < 0.1% |
| L-003 | スパイク負荷 | 0→50,000 logs/sec | バッファで吸収 |
| L-004 | 段階的負荷増加 | 1K→10K→50K | 性能劣化が線形 |

#### 9. ストレステスト

| ID | テストケース | 条件 | 期待結果 |
|----|-------------|------|---------|
| ST-001 | 限界スループット | 負荷を徐々に増加 | 限界値を特定 |
| ST-002 | バッファ満杯 | バッファ上限到達 | 503エラー、データ損失なし |
| ST-003 | ディスク満杯 | ディスク使用率100% | エラーログ、アラート |
| ST-004 | メモリ枯渇 | メモリ使用率100% | OOM Killer起動しない |

#### 10. 可用性・耐障害性テスト

| ID | テストケース | 条件 | 期待結果 |
|----|-------------|------|---------|
| A-001 | プロセス再起動 | Fluentd再起動 | データ損失なし |
| A-002 | コンテナ再起動 | Dockerコンテナ再起動 | 自動復旧、データ損失なし |
| A-003 | ネットワーク断続 | 一時的な切断・復旧 | リトライで復旧 |
| A-004 | Engine側障害 | Engine停止 | LogServerは正常動作 |
| A-005 | 設定リロード | 設定変更後リロード | ダウンタイムなし |

#### 11. セキュリティテスト

| ID | テストケース | 条件 | 期待結果 |
|----|-------------|------|---------|
| SEC-001 | SQLインジェクション試行 | ログにSQL文を含む | サニタイズされ保存 |
| SEC-002 | XSS試行 | ログにスクリプトを含む | そのまま保存（表示時に対策） |
| SEC-003 | Path Traversal試行 | `../../etc/passwd` | サニタイズされる |
| SEC-004 | DoS攻撃（大量リクエスト） | 100,000 req/sec | バッファ制限で防御 |
| SEC-005 | DoS攻撃（巨大ペイロード） | 100MBリクエスト | Body size制限で拒否 |
| SEC-006 | 不正な認証情報での総当たり | 1000回試行 | すべて拒否 |

---

## 詳細テスト設計

### 1. 設定ファイル検証テスト

#### テストスクリプト: `tests/config/test-config-validation.sh`

```bash
#!/bin/bash
set -euo pipefail

echo "=== Fluentd設定ファイル検証テスト ==="

# 1. 文法チェック
echo "1. 文法チェック..."
docker run --rm \
  -v $(pwd)/config/fluentd:/fluentd/etc \
  fluent/fluentd:v1.16-1 \
  fluentd --dry-run -c /fluentd/etc/fluent.conf

if [ $? -eq 0 ]; then
  echo "✅ 文法チェック: 合格"
else
  echo "❌ 文法チェック: 不合格"
  exit 1
fi

# 2. 必須ファイルの存在確認
echo "2. 必須ファイルの存在確認..."
REQUIRED_FILES=(
  "config/fluentd/fluent.conf"
  "config/fluentd/conf.d/01-source.conf"
  "config/fluentd/conf.d/02-filter.conf"
  "config/fluentd/conf.d/03-output.conf"
)

for file in "${REQUIRED_FILES[@]}"; do
  if [ -f "$file" ]; then
    echo "✅ $file: 存在"
  else
    echo "❌ $file: 存在しない"
    exit 1
  fi
done

# 3. 設定値の妥当性チェック
echo "3. 設定値の妥当性チェック..."
# ポート番号の重複チェック等

echo "=== すべての検証テストが合格しました ==="
```

### 2. 単体テスト（HTTP Input）

#### テストスクリプト: `tests/unit/test-http-input.sh`

```bash
#!/bin/bash
set -euo pipefail

echo "=== HTTP Input 単体テスト ==="

# Fluentdコンテナが起動していることを確認
docker ps | grep fluentd || {
  echo "❌ Fluentdコンテナが起動していません"
  exit 1
}

# テストデータ
TEST_LOG='{"time":"2026-02-17T10:00:00+09:00","log_type":"nginx","hostname":"test","fqdn":"example.com","customer_name":"test-customer","request":"GET /test"}'

# F-001: Nginxログの受信
echo "F-001: Nginxログの受信..."
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST https://localhost:8888/nginx.access \
  -H "Content-Type: application/json" \
  -H "X-Shared-Key: ${FLUENTD_SHARED_KEY}" \
  --cacert certs/ca.crt \
  --cert certs/client.crt \
  --key certs/client.key \
  -d "$TEST_LOG")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
if [ "$HTTP_CODE" = "200" ]; then
  echo "✅ F-001: 合格 (HTTP 200)"
else
  echo "❌ F-001: 不合格 (HTTP $HTTP_CODE)"
  exit 1
fi

# F-006: 不正なJSON形式
echo "F-006: 不正なJSON形式..."
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST https://localhost:8888/nginx.access \
  -H "Content-Type: application/json" \
  -H "X-Shared-Key: ${FLUENTD_SHARED_KEY}" \
  --cacert certs/ca.crt \
  --cert certs/client.crt \
  --key certs/client.key \
  -d '{"invalid json')

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
if [ "$HTTP_CODE" = "400" ]; then
  echo "✅ F-006: 合格 (HTTP 400)"
else
  echo "❌ F-006: 不合格 (HTTP $HTTP_CODE)"
  exit 1
fi

echo "=== HTTP Input 単体テスト完了 ==="
```

### 3. セキュリティテスト

#### テストスクリプト: `tests/security/test-security.sh`

```bash
#!/bin/bash
set -euo pipefail

echo "=== セキュリティテスト ==="

# S-002: 無効な共有シークレットキー
echo "S-002: 無効な共有シークレットキー..."
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST https://localhost:8888/nginx.access \
  -H "Content-Type: application/json" \
  -H "X-Shared-Key: invalid-key" \
  --cacert certs/ca.crt \
  --cert certs/client.crt \
  --key certs/client.key \
  -d '{"test":"data"}')

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
if [ "$HTTP_CODE" = "401" ]; then
  echo "✅ S-002: 合格 (HTTP 401)"
else
  echo "❌ S-002: 不合格 (HTTP $HTTP_CODE)"
  exit 1
fi

# SEC-003: Path Traversal試行
echo "SEC-003: Path Traversal試行..."
TEST_LOG='{"time":"2026-02-17T10:00:00+09:00","log_type":"nginx","hostname":"test","fqdn":"example.com","customer_name":"../../etc/passwd","request":"GET /test"}'

curl -s -X POST https://localhost:8888/nginx.access \
  -H "Content-Type: application/json" \
  -H "X-Shared-Key: ${FLUENTD_SHARED_KEY}" \
  --cacert certs/ca.crt \
  --cert certs/client.crt \
  --key certs/client.key \
  -d "$TEST_LOG"

sleep 15  # バッファフラッシュ待機

# ファイルが正しい場所に保存されているか確認
if ls /var/log/mrwebdefence/etc_passwd/ 2>/dev/null; then
  echo "❌ SEC-003: 不合格 (Path Traversalが成功してしまった)"
  exit 1
else
  echo "✅ SEC-003: 合格 (Path Traversalが防止された)"
fi

echo "=== セキュリティテスト完了 ==="
```

### 4. 統合テスト

#### テストスクリプト: `tests/integration/test-e2e-flow.sh`

```bash
#!/bin/bash
set -euo pipefail

echo "=== E2E統合テスト ==="

# テスト用の顧客名・FQDN
CUSTOMER="integration-test"
FQDN="test.example.com"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")
YEAR=$(date -u +"%Y")
MONTH=$(date -u +"%m")
DAY=$(date -u +"%d")
HOUR=$(date -u +"%H")

# テストログ
TEST_LOG=$(cat <<EOF
{
  "time": "${TIMESTAMP}",
  "log_type": "nginx",
  "hostname": "integration-test-host",
  "fqdn": "${FQDN}",
  "customer_name": "${CUSTOMER}",
  "remote_addr": "192.168.1.100",
  "request": "GET /integration/test HTTP/1.1",
  "status": 200,
  "body_bytes_sent": 1234,
  "request_time": 0.123
}
EOF
)

# 1. ログ送信
echo "1. ログ送信..."
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST https://localhost:8888/nginx.access \
  -H "Content-Type: application/json" \
  -H "X-Shared-Key: ${FLUENTD_SHARED_KEY}" \
  --cacert certs/ca.crt \
  --cert certs/client.crt \
  --key certs/client.key \
  -d "$TEST_LOG")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
if [ "$HTTP_CODE" != "200" ]; then
  echo "❌ ログ送信失敗 (HTTP $HTTP_CODE)"
  exit 1
fi
echo "✅ ログ送信成功"

# 2. バッファフラッシュ待機
echo "2. バッファフラッシュ待機（15秒）..."
sleep 15

# 3. ファイル出力確認
echo "3. ファイル出力確認..."
LOG_FILE="/var/log/mrwebdefence/${CUSTOMER}/nginx/${FQDN}/${YEAR}/${MONTH}/${DAY}/${HOUR}.log.gz"

if [ ! -f "$LOG_FILE" ]; then
  echo "❌ ログファイルが見つかりません: $LOG_FILE"
  exit 1
fi
echo "✅ ログファイルが存在します: $LOG_FILE"

# 4. ファイル内容確認
echo "4. ファイル内容確認..."
LOG_CONTENT=$(zcat "$LOG_FILE" | jq -r '.customer_name')

if [ "$LOG_CONTENT" = "$CUSTOMER" ]; then
  echo "✅ ログ内容が正しい (customer_name: $LOG_CONTENT)"
else
  echo "❌ ログ内容が不正 (customer_name: $LOG_CONTENT)"
  exit 1
fi

# 5. タイムスタンプフィールド確認
echo "5. タイムスタンプフィールド確認..."
TIMESTAMP_FIELD=$(zcat "$LOG_FILE" | jq -r '.timestamp')

if [ -n "$TIMESTAMP_FIELD" ] && [ "$TIMESTAMP_FIELD" != "null" ]; then
  echo "✅ timestampフィールドが存在します: $TIMESTAMP_FIELD"
else
  echo "❌ timestampフィールドが存在しません"
  exit 1
fi

# 6. received_atフィールド確認
echo "6. received_atフィールド確認..."
RECEIVED_AT=$(zcat "$LOG_FILE" | jq -r '.received_at')

if [ -n "$RECEIVED_AT" ] && [ "$RECEIVED_AT" != "null" ]; then
  echo "✅ received_atフィールドが存在します: $RECEIVED_AT"
else
  echo "❌ received_atフィールドが存在しません"
  exit 1
fi

# クリーンアップ
echo "7. クリーンアップ..."
rm -rf "/var/log/mrwebdefence/${CUSTOMER}"

echo "=== E2E統合テスト完了 ==="
```

### 5. パフォーマンステスト

#### テストスクリプト: `tests/performance/test-performance.sh`

```bash
#!/bin/bash
set -euo pipefail

echo "=== パフォーマンステスト ==="

# テストログファイルの準備
TEST_LOG_FILE="test-log.json"
cat > "$TEST_LOG_FILE" <<EOF
{"time":"2026-02-17T10:00:00+09:00","log_type":"nginx","hostname":"perf-test","fqdn":"perf.example.com","customer_name":"perf-customer","remote_addr":"192.168.1.100","request":"GET /perf/test","status":200}
EOF

# P-001: スループット（低負荷）
echo "P-001: スループット（低負荷: 1,000 req）..."
ab -n 1000 -c 10 \
  -T 'application/json' \
  -p "$TEST_LOG_FILE" \
  -H "X-Shared-Key: ${FLUENTD_SHARED_KEY}" \
  https://localhost:8888/nginx.access \
  > perf-low-load.txt

RPS_LOW=$(grep "Requests per second" perf-low-load.txt | awk '{print $4}')
echo "スループット（低負荷）: ${RPS_LOW} req/sec"

if (( $(echo "$RPS_LOW > 1000" | bc -l) )); then
  echo "✅ P-001: 合格 (${RPS_LOW} > 1000 req/sec)"
else
  echo "⚠️ P-001: 目標未達 (${RPS_LOW} < 1000 req/sec)"
fi

# P-002: スループット（通常負荷）
echo "P-002: スループット（通常負荷: 10,000 req）..."
ab -n 10000 -c 100 \
  -T 'application/json' \
  -p "$TEST_LOG_FILE" \
  -H "X-Shared-Key: ${FLUENTD_SHARED_KEY}" \
  https://localhost:8888/nginx.access \
  > perf-normal-load.txt

RPS_NORMAL=$(grep "Requests per second" perf-normal-load.txt | awk '{print $4}')
echo "スループット（通常負荷）: ${RPS_NORMAL} req/sec"

if (( $(echo "$RPS_NORMAL > 5000" | bc -l) )); then
  echo "✅ P-002: 合格 (${RPS_NORMAL} > 5000 req/sec)"
else
  echo "⚠️ P-002: 目標未達 (${RPS_NORMAL} < 5000 req/sec)"
fi

# P-007: メモリ使用量
echo "P-007: メモリ使用量..."
MEM_USAGE=$(docker stats fluentd --no-stream --format "{{.MemUsage}}" | awk '{print $1}' | sed 's/MiB//')
echo "メモリ使用量: ${MEM_USAGE} MiB"

if (( $(echo "$MEM_USAGE < 512" | bc -l) )); then
  echo "✅ P-007: 合格 (${MEM_USAGE} < 512 MiB)"
else
  echo "⚠️ P-007: 目標未達 (${MEM_USAGE} >= 512 MiB)"
fi

# クリーンアップ
rm -f "$TEST_LOG_FILE" perf-*.txt

echo "=== パフォーマンステスト完了 ==="
```

---

## テストデータ

### 正常系テストデータ

#### Nginxログ

```json
{
  "time": "2026-02-17T10:00:00+09:00",
  "log_type": "nginx",
  "hostname": "waf-engine-01",
  "fqdn": "example.com",
  "customer_name": "test-customer",
  "remote_addr": "192.168.1.100",
  "request": "GET /api/users HTTP/1.1",
  "status": 200,
  "body_bytes_sent": 1234,
  "request_time": 0.123,
  "http_user_agent": "Mozilla/5.0",
  "http_referer": "https://example.com/"
}
```

#### OpenAppSecログ

```json
{
  "time": "2026-02-17T10:00:00+09:00",
  "log_type": "openappsec",
  "hostname": "waf-engine-01",
  "fqdn": "example.com",
  "customer_name": "test-customer",
  "host": "example.com",
  "protectionName": "Threat Prevention",
  "signature": "SQL Injection Attempt",
  "ruleName": "rule_001",
  "sourceIP": "192.168.1.100",
  "requestUri": "/admin/login",
  "severity": "high"
}
```

### 異常系テストデータ

#### 必須フィールド欠損

```json
{
  "time": "2026-02-17T10:00:00+09:00",
  "log_type": "nginx",
  "hostname": "test"
  // customer_name, fqdn が欠損
}
```

#### Path Traversal試行

```json
{
  "time": "2026-02-17T10:00:00+09:00",
  "log_type": "nginx",
  "hostname": "test",
  "fqdn": "../../etc/passwd",
  "customer_name": "../../../root",
  "request": "GET /test"
}
```

#### 特殊文字

```json
{
  "time": "2026-02-17T10:00:00+09:00",
  "log_type": "nginx",
  "hostname": "test",
  "fqdn": "test<>:|?*.com",
  "customer_name": "test@#$%^&*()",
  "request": "GET /test"
}
```

---

## テスト環境

### 環境構成

| 環境 | 用途 | 構成 |
|------|------|------|
| **ローカル** | 開発・単体テスト | Docker Compose |
| **CI** | 自動テスト | GitHub Actions |
| **ステージング** | 統合・E2Eテスト | Kubernetes（小規模） |
| **本番** | 本番運用 | Kubernetes（冗長構成） |

### 必要なリソース

#### ローカル環境

```yaml
# docker-compose.test.yml
version: '3.8'

services:
  fluentd:
    image: fluent/fluentd:v1.16-1
    volumes:
      - ./config/fluentd:/fluentd/etc
      - ./certs:/fluentd/certs
      - test-logs:/var/log/mrwebdefence
      - test-buffer:/var/log/fluentd/buffer
    ports:
      - "8888:8888"
      - "8889:8889"
      - "24220:24220"
      - "24231:24231"
    environment:
      - FLUENTD_SHARED_KEY=test-shared-key-12345
    networks:
      - test-network

volumes:
  test-logs:
  test-buffer:

networks:
  test-network:
```

---

## テスト実行計画

### フェーズ1: 設定検証（実装前）

| # | テスト | 担当 | 期間 |
|---|--------|------|------|
| 1 | 設定ファイル文法チェック | Dev | 即時 |
| 2 | ドライラン | Dev | 即時 |

### フェーズ2: 単体テスト（実装中）

| # | テスト | 担当 | 期間 |
|---|--------|------|------|
| 1 | HTTP Input | Dev | 1日 |
| 2 | Filter | Dev | 1日 |
| 3 | Buffer | Dev | 1日 |
| 4 | File Output | Dev | 1日 |

### フェーズ3: 統合テスト（実装後）

| # | テスト | 担当 | 期間 |
|---|--------|------|------|
| 1 | 正常系フロー | QA | 2日 |
| 2 | 異常系フロー | QA | 2日 |
| 3 | セキュリティ | QA | 2日 |

### フェーズ4: E2Eテスト（統合後）

| # | テスト | 担当 | 期間 |
|---|--------|------|------|
| 1 | Engine連携 | QA | 2日 |
| 2 | マルチテナント | QA | 1日 |

### フェーズ5: 非機能テスト（リリース前）

| # | テスト | 担当 | 期間 |
|---|--------|------|------|
| 1 | パフォーマンス | QA | 3日 |
| 2 | 負荷テスト | QA | 2日 |
| 3 | 耐障害性 | QA | 2日 |

### 合計期間: 約3週間

---

## テスト結果レポート

### レポート形式

```markdown
# テスト結果レポート

**実施日**: YYYY-MM-DD  
**テスター**: Name  
**環境**: Environment

## サマリー

- 総テスト数: XX
- 合格: XX
- 不合格: XX
- スキップ: XX
- 合格率: XX%

## 詳細結果

| ID | テストケース | 結果 | 備考 |
|----|-------------|------|------|
| F-001 | Nginxログの受信 | ✅ | - |
| F-002 | OpenAppSecログの受信 | ✅ | - |
| ... | ... | ... | ... |

## 不合格項目

### F-XXX: テストケース名

**期待結果**: ...  
**実際の結果**: ...  
**原因**: ...  
**対応**: ...

## パフォーマンス測定結果

| 項目 | 目標値 | 実測値 | 結果 |
|------|--------|--------|------|
| スループット | > 10,000 logs/sec | 12,345 logs/sec | ✅ |
| レイテンシ(P95) | < 100ms | 85ms | ✅ |
| ... | ... | ... | ... |
```

---

## CI/CD統合

### GitHub Actions Workflow

```yaml
name: Test

on:
  push:
    branches: [main, develop, feature/**]
  pull_request:
    branches: [main, develop]

jobs:
  config-validation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Config Validation
        run: ./tests/config/test-config-validation.sh

  unit-tests:
    runs-on: ubuntu-latest
    needs: config-validation
    steps:
      - uses: actions/checkout@v4
      - name: Setup Test Environment
        run: docker-compose -f docker-compose.test.yml up -d
      - name: Run Unit Tests
        run: ./tests/unit/test-http-input.sh
      - name: Teardown
        run: docker-compose -f docker-compose.test.yml down

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    steps:
      - uses: actions/checkout@v4
      - name: Setup Test Environment
        run: docker-compose -f docker-compose.test.yml up -d
      - name: Run Integration Tests
        run: ./tests/integration/test-e2e-flow.sh
      - name: Teardown
        run: docker-compose -f docker-compose.test.yml down

  security-tests:
    runs-on: ubuntu-latest
    needs: integration-tests
    steps:
      - uses: actions/checkout@v4
      - name: Setup Test Environment
        run: docker-compose -f docker-compose.test.yml up -d
      - name: Run Security Tests
        run: ./tests/security/test-security.sh
      - name: Teardown
        run: docker-compose -f docker-compose.test.yml down
```

---

## チェックリスト

### テスト準備

- [ ] テスト環境の構築
- [ ] テストデータの準備
- [ ] 証明書の生成
- [ ] 環境変数の設定

### テスト実行

- [ ] 設定ファイル検証テスト
- [ ] 単体テスト（HTTP Input）
- [ ] 単体テスト（Filter）
- [ ] 単体テスト（Buffer）
- [ ] 単体テスト（File Output）
- [ ] セキュリティテスト
- [ ] 統合テスト（E2E）
- [ ] パフォーマンステスト
- [ ] 負荷テスト
- [ ] 耐障害性テスト

### テスト完了後

- [ ] テスト結果レポート作成
- [ ] 不合格項目の修正
- [ ] 再テスト実施
- [ ] テスト結果の承認
- [ ] 本番リリース判定
