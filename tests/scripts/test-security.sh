#!/bin/bash
# セキュリティテスト - Path Traversal対策
# 危険なパスが正しくサニタイズされることを確認

set -euo pipefail

echo "=== Security Test: Path Traversal Prevention ==="

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
docker-compose -f docker-compose.test.yml up -d

# Fluentd起動待機
echo "Waiting for Fluentd to be healthy..."
for i in {1..30}; do
  if curl -fs http://localhost:8889/health > /dev/null 2>&1; then
    echo "Fluentd is ready"
    break
  fi
  if [ $i -eq 30 ]; then
    echo "Error: Fluentd failed to start"
    docker-compose -f docker-compose.test.yml logs fluentd
    docker-compose -f docker-compose.test.yml down
    exit 1
  fi
  sleep 1
done

FAILED=0

# テスト: Path Traversal攻撃
echo ""
echo "Test: Path Traversal with ../etc/passwd"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%S+00:00")
curl -X POST http://localhost:8888/nginx.access \
  -H "Content-Type: application/json" \
  -d "{\"time\":\"${TIMESTAMP}\",\"customer_name\":\"../etc/passwd\",\"fqdn\":\"test.example.com\",\"message\":\"attack\"}" \
  -s -o /dev/null

# バッファフラッシュ待機
sleep 3

# サニタイズされたパスが作成されていないことを確認
if [ -d "./tests/tmp/logs/__/etc/passwd" ] || [ -d "./tests/tmp/logs/../etc/passwd" ]; then
  echo "✗ Path Traversal not prevented (dangerous path created)"
  ((FAILED++))
else
  echo "✓ Path Traversal prevented (dangerous path not created)"
fi

# invalidログに記録されていることを確認
if [ -f "./tests/tmp/invalid/invalid.log" ]; then
  echo "✓ Invalid log recorded"
else
  echo "✗ Invalid log not recorded"
  ((FAILED++))
fi

# クリーンアップ
echo ""
echo "Cleaning up..."
docker-compose -f docker-compose.test.yml down
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
