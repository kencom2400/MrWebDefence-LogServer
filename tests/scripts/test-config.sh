#!/bin/bash
# 設定バリデーションテスト
# Fluentd設定ファイルの文法チェック

set -euo pipefail

echo "=== Configuration Validation Test ==="

# テスト環境起動
echo "Starting test environment..."
docker compose -f docker-compose.test.yml up -d

# Fluentd起動待機
echo "Waiting for Fluentd to start..."
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

# 設定ファイルの検証
echo "Validating configuration..."
if docker compose -f docker-compose.test.yml exec -T fluentd fluentd --dry-run -c /fluentd/etc/fluent.conf > /dev/null 2>&1; then
  echo "✓ Configuration validation passed"
  RESULT=0
else
  echo "✗ Configuration validation failed"
  RESULT=1
fi

# クリーンアップ
docker compose -f docker-compose.test.yml down
sudo rm -rf ./tests/tmp/* 2>/dev/null || true

exit $RESULT
