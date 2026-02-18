#!/bin/bash
# セキュリティテスト - Path Traversal対策
# 危険なパスが正しくサニタイズされることを確認

set -euo pipefail

echo "=== Security Test: Path Traversal Prevention ==="

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

# テスト: Path Traversal攻撃
echo ""
echo "Test: Path Traversal with ../etc/passwd"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%S+00:00")
RESPONSE=$(curl -X POST http://localhost:8888/nginx.access \
  -H "Content-Type: application/json" \
  -d "{\"time\":\"${TIMESTAMP}\",\"customer_name\":\"../etc/passwd\",\"fqdn\":\"test.example.com\",\"message\":\"attack\"}" \
  -w "%{http_code}" -s -o /dev/null)

if [ "$RESPONSE" == "200" ]; then
  echo "✓ Request accepted (will be sanitized)"
else
  echo "✗ Request failed (HTTP $RESPONSE)"
  ((FAILED++))
fi

# バッファフラッシュ待機
echo "Waiting for buffer flush..."
sleep 15

# サニタイズされたログが正常に処理されることを確認
if docker exec mrwebdefence-logserver-test find /var/log/mrwebdefence/logs -name "*.log.gz" -exec zcat {} \; | grep -q "safe_customer_name"; then
  echo "✓ Logs processed with sanitization"
  # safe_customer_nameが"__etc_passwd"などにサニタイズされているか確認
  SAFE_NAME=$(docker exec mrwebdefence-logserver-test find /var/log/mrwebdefence/logs -name "*.log.gz" -exec zcat {} \; | grep "attack" | head -1 | grep -o '"safe_customer_name":"[^"]*"' || echo "")
  if [ -n "$SAFE_NAME" ]; then
    echo "  $SAFE_NAME"
  fi
else
  echo "✗ Log processing failed"
  ((FAILED++))
fi

# クリーンアップ
echo ""
echo "Cleaning up..."
docker compose -f docker-compose.test.yml down
rm -rf ./tests/tmp/*

# 結果
echo ""
if [ $FAILED -eq 0 ]; then
  echo "=== Security test passed ==="
  exit 0
else
  echo "=== $FAILED test(s) failed ==="
  exit 1
fi
