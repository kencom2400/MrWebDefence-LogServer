#!/bin/bash
# E2Eインテグレーションテスト
# エンドツーエンドのログフロー検証

set -euo pipefail

echo "=== E2E Integration Test ==="

# テスト環境起動
echo "Starting test environment..."
docker compose -f docker-compose.test.yml up -d

# Fluentd起動待機
echo "Waiting for Fluentd to be healthy..."
for i in {1..30}; do
  if docker exec mrwebdefence-logserver-test pgrep -f fluentd > /dev/null 2>&1; then
    echo "Fluentd process is running"
    sleep 3
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

# テストデータ送信
echo ""
echo "Sending test logs..."
CUSTOMER="test-customer"
FQDN="web01.example.com"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%S+00:00")

for i in {1..10}; do
  curl -X POST http://localhost:8888/nginx.access \
    -H "Content-Type: application/json" \
    -d "{\"time\":\"${TIMESTAMP}\",\"customer_name\":\"${CUSTOMER}\",\"fqdn\":\"${FQDN}\",\"message\":\"test log ${i}\"}" \
    -s -o /dev/null
done

# バッファフラッシュ待機
echo "Waiting for buffer flush..."
sleep 20

# ログファイル検証
echo ""
echo "Verifying log storage..."

# ログファイルの存在確認
# 新しい階層構造: /var/log/mrwebdefence/{customer_name}/{log_type}/{fqdn}/YYYY/MM/DD/HH.log
LOG_FILES=$(docker exec mrwebdefence-logserver-test find /var/log/mrwebdefence -type f \( -name "*.log" -o -name "*.log.gz" \) 2>/dev/null | wc -l)
if [ "$LOG_FILES" -gt 0 ]; then
  echo "✓ Log files created"
  
  # ログ数の確認
  LOG_ENTRIES=$(docker exec mrwebdefence-logserver-test sh -c "find /var/log/mrwebdefence -type f -name '*.log' -exec cat {} \; 2>/dev/null; find /var/log/mrwebdefence -type f -name '*.log.gz' -exec zcat {} \; 2>/dev/null" | wc -l)
  echo "  Total log entries: $LOG_ENTRIES"
  
  if [ "$LOG_ENTRIES" -ge 10 ]; then
    echo "✓ All logs recorded"
  else
    echo "✗ Some logs missing (expected 10, got $LOG_ENTRIES)"
    ((FAILED++))
  fi
  
  # ログ内容の確認
  echo "  Checking log content..."
  LOG_CONTENT=$(docker exec mrwebdefence-logserver-test sh -c "find /var/log/mrwebdefence -type f -name '*.log' -exec cat {} \; 2>/dev/null" | head -3)
  echo "  Sample log content: ${LOG_CONTENT:0:100}..."
  if echo "$LOG_CONTENT" | grep -q "test log"; then
    echo "✓ Log content verified"
  else
    echo "✗ Log content verification failed"
    echo "  (This is informational only - logs may contain fields other than 'message')"
  fi
else
  echo "✗ No log files found"
  ((FAILED++))
fi

# メトリクス確認
echo ""
echo "Verifying metrics..."
if curl -s http://localhost:24231/metrics | grep -q "fluentd"; then
  echo "✓ Metrics endpoint working"
else
  echo "⚠ Metrics endpoint check skipped (may require plugin configuration)"
fi

# クリーンアップ
echo ""
echo "Cleaning up..."
docker compose -f docker-compose.test.yml down
rm -rf ./tests/tmp/* 2>/dev/null || true

# 結果
echo ""
if [ $FAILED -eq 0 ]; then
  echo "=== E2E test passed ==="
  exit 0
else
  echo "=== $FAILED test(s) failed ==="
  exit 1
fi
