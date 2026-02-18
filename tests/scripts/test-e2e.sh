#!/bin/bash
# E2Eインテグレーションテスト
# エンドツーエンドのログフロー検証

set -euo pipefail

echo "=== E2E Integration Test ==="

# テスト用証明書生成
echo "Generating test certificates..."
CERT_DIR=./tests/certs
mkdir -p "${CERT_DIR}"

openssl genrsa -out "${CERT_DIR}/ca.key" 2048 2>/dev/null
openssl req -new -x509 -days 365 -key "${CERT_DIR}/ca.key" \
  -out "${CERT_DIR}/ca.crt" \
  -subj "/C=JP/O=Test/CN=Test-CA" 2>/dev/null

openssl genrsa -out "${CERT_DIR}/logserver.key" 2048 2>/dev/null
openssl req -new -key "${CERT_DIR}/logserver.key" \
  -out "${CERT_DIR}/logserver.csr" \
  -subj "/C=JP/O=Test/CN=localhost" 2>/dev/null
openssl x509 -req -days 365 -in "${CERT_DIR}/logserver.csr" \
  -CA "${CERT_DIR}/ca.crt" -CAkey "${CERT_DIR}/ca.key" \
  -CAcreateserial -out "${CERT_DIR}/logserver.crt" 2>/dev/null

rm -f "${CERT_DIR}/logserver.csr"

# テスト環境起動
echo "Starting test environment..."
docker compose -f docker-compose.test.yml up -d

# Fluentd起動待機
echo "Waiting for Fluentd to be healthy..."
for i in {1..30}; do
  if curl -fs http://localhost:8889/health > /dev/null 2>&1; then
    echo "Fluentd is ready"
    break
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
sleep 5

# ログファイル検証
echo ""
echo "Verifying log storage..."

# ディレクトリ構造の確認
EXPECTED_DIR="./tests/tmp/logs/${CUSTOMER}/nginx/${FQDN}"
if [ -d "${EXPECTED_DIR}" ]; then
  echo "✓ Log directory structure correct"
else
  echo "✗ Log directory structure incorrect"
  echo "Expected: ${EXPECTED_DIR}"
  ls -R ./tests/tmp/logs/ || true
  ((FAILED++))
fi

# ログファイルの存在確認
LOG_COUNT=$(find "${EXPECTED_DIR}" -name "*.log" -type f 2>/dev/null | wc -l)
if [ "${LOG_COUNT}" -gt 0 ]; then
  echo "✓ Log files created (${LOG_COUNT} files)"
else
  echo "✗ No log files found"
  ((FAILED++))
fi

# ログ内容の確認
if [ "${LOG_COUNT}" -gt 0 ]; then
  LOG_FILE=$(find "${EXPECTED_DIR}" -name "*.log" -type f | head -1)
  if grep -q "test log" "${LOG_FILE}"; then
    echo "✓ Log content verified"
  else
    echo "✗ Log content verification failed"
    ((FAILED++))
  fi
fi

# メトリクス確認
echo ""
echo "Verifying metrics..."
METRICS=$(curl -s http://localhost:24231/metrics)

if echo "${METRICS}" | grep -q "fluentd_input_status_num_records_total"; then
  echo "✓ Metrics endpoint working"
else
  echo "✗ Metrics endpoint not working"
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
  echo "=== E2E test passed ==="
  exit 0
else
  echo "=== $FAILED test(s) failed ==="
  exit 1
fi
