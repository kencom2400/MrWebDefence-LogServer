#!/bin/bash
# HTTP入力テスト
# ログ受信エンドポイントの基本機能テスト

set -euo pipefail

echo "=== HTTP Input Test ==="

# テスト環境起動
echo "Starting test environment..."
docker compose -f docker-compose.test.yml up -d

# Fluentd起動待機
echo "Waiting for Fluentd to be healthy..."
for i in {1..30}; do
  if docker exec mrwebdefence-logserver-test pgrep -f fluentd > /dev/null 2>&1; then
    echo "Fluentd process is running"
    sleep 3  # ポート準備のための追加待機
    # ポート8888が利用可能か確認
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8888/ 2>&1 | grep -qE "^(200|400|404)"; then
      echo "Fluentd is ready"
      break
    fi
  fi
  if [ $i -eq 30 ]; then
    echo "Error: Fluentd failed to start"
    docker compose -f docker-compose.test.yml logs fluentd
    docker compose -f docker-compose.test.yml down
    exit 1
  fi
  sleep 1
done

FAILED=0

# テスト1: 正常なNginxログ
echo ""
echo "Test 1: Valid Nginx log"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%S+00:00")
RESPONSE=$(curl -X POST http://localhost:8888/nginx.access \
  -H "Content-Type: application/json" \
  -d "{\"time\":\"${TIMESTAMP}\",\"customer_name\":\"test-customer\",\"fqdn\":\"test.example.com\",\"message\":\"test log\"}" \
  -w "%{http_code}" -s -o /dev/null)

if [ "$RESPONSE" == "200" ]; then
  echo "✓ Test 1 passed (HTTP $RESPONSE)"
else
  echo "✗ Test 1 failed (HTTP $RESPONSE)"
  ((FAILED++))
fi

# テスト2: 正常なOpenAppSecログ
echo ""
echo "Test 2: Valid OpenAppSec log"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%S+00:00")
RESPONSE=$(curl -X POST http://localhost:8888/openappsec.security \
  -H "Content-Type: application/json" \
  -d "{\"time\":\"${TIMESTAMP}\",\"customer_name\":\"test-customer\",\"fqdn\":\"test.example.com\",\"message\":\"security event\",\"severity\":\"high\"}" \
  -w "%{http_code}" -s -o /dev/null)

if [ "$RESPONSE" == "200" ]; then
  echo "✓ Test 2 passed (HTTP $RESPONSE)"
else
  echo "✗ Test 2 failed (HTTP $RESPONSE)"
  ((FAILED++))
fi

# テスト3: customer_name欠損（フィルタで"unknown"に変換される）
echo ""
echo "Test 3: Missing customer_name"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%S+00:00")
RESPONSE=$(curl -X POST http://localhost:8888/nginx.access \
  -H "Content-Type: application/json" \
  -d "{\"time\":\"${TIMESTAMP}\",\"fqdn\":\"test.example.com\",\"message\":\"test log\"}" \
  -w "%{http_code}" -s -o /dev/null)

if [ "$RESPONSE" == "200" ]; then
  echo "✓ Test 3 passed (HTTP $RESPONSE)"
else
  echo "✗ Test 3 failed (HTTP $RESPONSE)"
  ((FAILED++))
fi

# バッファフラッシュ待機
echo ""
echo "Waiting for buffer flush..."
sleep 15

# ログファイル確認
echo ""
echo "Verifying log files..."
if docker exec mrwebdefence-logserver-test find /var/log/mrwebdefence/logs -name "*.log.gz" | grep -q .; then
  echo "✓ Log files created"
  LOG_COUNT=$(docker exec mrwebdefence-logserver-test find /var/log/mrwebdefence/logs -name "*.log.gz" -exec zcat {} \; | wc -l)
  echo "  Total log entries: $LOG_COUNT"
else
  echo "✗ Log files not found"
  ((FAILED++))
fi

# クリーンアップ
echo ""
echo "Cleaning up..."
docker compose -f docker-compose.test.yml down
# tests/tmp内のファイルはfluentdユーザーが所有しているため、sudoで削除
sudo rm -rf ./tests/tmp/* 2>/dev/null || true

# 結果
echo ""
if [ $FAILED -eq 0 ]; then
  echo "=== All tests passed ==="
  exit 0
else
  echo "=== $FAILED test(s) failed ==="
  exit 1
fi
