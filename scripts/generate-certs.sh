#!/bin/bash
# 証明書生成スクリプト
# MrWebDefence-LogServer用の自己署名証明書を生成

set -euo pipefail

# 設定
CERT_DIR="${CERT_DIR:-./certs}"
CA_SUBJECT="/C=JP/ST=Tokyo/L=Tokyo/O=MrWebDefence/OU=IT/CN=MrWebDefence-CA"
SERVER_SUBJECT="/C=JP/ST=Tokyo/L=Tokyo/O=MrWebDefence/OU=LogServer/CN=logserver-01"
DAYS="${CERT_VALIDITY_DAYS:-365}"

# 証明書ディレクトリの作成
echo "Creating certificate directory: ${CERT_DIR}"
mkdir -p "${CERT_DIR}"

# CA証明書の生成
echo "Generating CA certificate..."
openssl genrsa -out "${CERT_DIR}/ca.key" 4096
openssl req -new -x509 -days ${DAYS} -key "${CERT_DIR}/ca.key" \
  -out "${CERT_DIR}/ca.crt" -subj "${CA_SUBJECT}"

# サーバー秘密鍵の生成
echo "Generating server private key..."
openssl genrsa -out "${CERT_DIR}/logserver.key" 4096

# サーバー証明書署名要求（CSR）の生成
echo "Generating server CSR..."
openssl req -new -key "${CERT_DIR}/logserver.key" \
  -out "${CERT_DIR}/logserver.csr" -subj "${SERVER_SUBJECT}"

# サーバー証明書の生成（CAで署名）
echo "Signing server certificate with CA..."
openssl x509 -req -days ${DAYS} -in "${CERT_DIR}/logserver.csr" \
  -CA "${CERT_DIR}/ca.crt" -CAkey "${CERT_DIR}/ca.key" \
  -CAcreateserial -out "${CERT_DIR}/logserver.crt"

# CSRファイルの削除（不要）
rm -f "${CERT_DIR}/logserver.csr"

# 証明書の検証
echo "Verifying server certificate..."
openssl verify -CAfile "${CERT_DIR}/ca.crt" "${CERT_DIR}/logserver.crt"

# 権限設定
chmod 600 "${CERT_DIR}"/*.key
chmod 644 "${CERT_DIR}"/*.crt

echo "Certificate generation completed!"
echo "Generated files:"
echo "  - CA Certificate: ${CERT_DIR}/ca.crt"
echo "  - CA Private Key: ${CERT_DIR}/ca.key"
echo "  - Server Certificate: ${CERT_DIR}/logserver.crt"
echo "  - Server Private Key: ${CERT_DIR}/logserver.key"
echo ""
echo "IMPORTANT:"
echo "1. Copy ca.crt to Engine Fluentd servers for mTLS validation"
echo "2. Keep ca.key and logserver.key secure and never commit to version control"
echo "3. Update .gitignore to exclude certs/ directory"
