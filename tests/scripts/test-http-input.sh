#!/bin/bash
# HTTP入力テスト
# ログ受信エンドポイントの基本機能テスト

set -euo pipefail

echo "=== HTTP Input Test ==="

# テスト用証明書生成
echo "Generating test certificates..."
CERT_DIR=./tests/certs
mkdir -p "${CERT_DIR}"

# CA証明書
openssl genrsa -out "${CERT_DIR}/ca.key" 2048 2>/dev/null
openssl req -new -x509 -days 365 -key "${CERT_DIR}/ca.key" \
  -out "${CERT_DIR}/ca.crt" \
  -subj "/C=JP/O=Test/CN=Test-CA" 2>/dev/null

# サーバー証明書
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
docker compose -f docker compose.test.yml up -d

# Fluentd起動待機
echo "Waiting for Fluentd to be healthy..."
for i in {1..30}; do
  if curl -fs http://localhost:8889/health > /dev/null 2>&1; then
    echo "Fluentd is ready"
    break
  fi
  if [ $i -eq 30 ]; then
    echo "Error: Fluentd failed to start"
    docker compose -f docker compose.test.yml logs fluentd
    docker compose -f docker compose.test.yml down
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

# テスト3: customer_name欠損（invalidログとして記録されるべき）
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
sleep 3

# ログファイル確認
echo ""
echo "Verifying log files..."
if [ -d "./tests/tmp/logs/test-customer" ]; then
  echo "✓ Log directory created"
else
  echo "✗ Log directory not found"
  ((FAILED++))
fi

# クリーンアップ
echo ""
echo "Cleaning up..."
docker compose -f docker compose.test.yml down
rm -rf ./tests/tmp/*

# 結果
echo ""
if [ $FAILED -eq 0 ]; then
  echo "=== All tests passed ==="
  exit 0
else
  echo "=== $FAILED test(s) failed ==="
  exit 1
fi
