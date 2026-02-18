# SSL/TLS設定ガイド

MrWebDefence-LogServerのSSL/TLS（mTLS）設定手順書

## 概要

LogServerとEngine Fluentd間の通信は、相互TLS（mTLS）で暗号化されます。

**セキュリティレベル**:
- TLS 1.3 / TLS 1.2
- Forward Secrecy対応暗号スイート
- クライアント証明書検証（mTLS）
- 共有シークレットキー認証

---

## 前提条件

- OpenSSLがインストールされていること
- LogServerとEngine Fluentdが通信可能であること

---

## 証明書の生成

### 1. CA証明書とサーバー証明書の生成

LogServer側で以下のスクリプトを実行します。

```bash
# 証明書生成スクリプトの実行
cd /path/to/MrWebDefence-LogServer
./scripts/generate-certs.sh
```

**生成されるファイル**:
- `certs/ca.crt` - CA証明書（公開）
- `certs/ca.key` - CA秘密鍵（機密）
- `certs/logserver.crt` - LogServerサーバー証明書（公開）
- `certs/logserver.key` - LogServer秘密鍵（機密）

### 2. Engine側のクライアント証明書生成

Engine Fluentd側で、LogServerのCAを使ってクライアント証明書を生成します。

```bash
# Engine側での実行
CERT_DIR="./certs"
CLIENT_SUBJECT="/C=JP/ST=Tokyo/L=Tokyo/O=MrWebDefence/OU=Engine/CN=engine-client-01"

# クライアント秘密鍵の生成
openssl genrsa -out "${CERT_DIR}/engine.key" 4096

# クライアントCSRの生成
openssl req -new -key "${CERT_DIR}/engine.key" \
  -out "${CERT_DIR}/engine.csr" -subj "${CLIENT_SUBJECT}"

# クライアント証明書の生成（LogServerのCAで署名）
openssl x509 -req -days 3650 -in "${CERT_DIR}/engine.csr" \
  -CA "${CERT_DIR}/ca.crt" -CAkey "${CERT_DIR}/ca.key" \
  -CAcreateserial -out "${CERT_DIR}/engine.crt"

# CSRファイルの削除
rm -f "${CERT_DIR}/engine.csr"
```

---

## 証明書の配布

### LogServer → Engine Fluentd

以下のファイルをEngine Fluentdサーバーに配布します。

1. `ca.crt` - CA証明書（LogServerの検証用）

**配布方法**:
```bash
# SCPでの配布例
scp certs/ca.crt user@engine-server:/path/to/engine/certs/
```

### LogServer ← Engine Fluentd

LogServerは`ca.crt`でEngine側のクライアント証明書を検証するため、追加の配布は不要です。

---

## Fluentd設定

### LogServer側の設定

`config/fluentd/conf.d/01-source.conf`で既に設定済みです。

```xml
<source>
  @type http
  port 8888
  
  <transport tls>
    version TLSv1_3,TLSv1_2
    ciphers ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES128-GCM-SHA256
    
    cert_path /etc/fluentd/certs/logserver.crt
    private_key_path /etc/fluentd/certs/logserver.key
    
    client_cert_auth true
    ca_path /etc/fluentd/certs/ca.crt
  </transport>
  
  <security>
    self_hostname logserver-01
    shared_key "#{ENV['FLUENTD_SHARED_KEY']}"
  </security>
</source>
```

### Engine Fluentd側の設定

Engine側の`forward`出力を以下のように設定します。

```xml
<match {nginx,openappsec}.**>
  @type forward
  
  <server>
    host logserver.example.com
    port 8888
  </server>
  
  <transport tls>
    version TLSv1_3,TLSv1_2
    ciphers ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES128-GCM-SHA256
    
    cert_path /etc/fluentd/certs/engine.crt
    private_key_path /etc/fluentd/certs/engine.key
    ca_path /etc/fluentd/certs/ca.crt
    
    cert_verify true
  </transport>
  
  <security>
    self_hostname engine-01
    shared_key "#{ENV['FLUENTD_SHARED_KEY']}"
  </security>
</match>
```

---

## 共有シークレットキーの設定

### 1. セキュアなキーの生成

```bash
# ランダムなキーを生成（64文字）
openssl rand -base64 48
```

### 2. 環境変数への設定

LogServerとEngine Fluentdの両方で同じキーを設定します。

**LogServer側**:
```bash
# .envファイルに追加
FLUENTD_SHARED_KEY=your-generated-key-here
```

**Engine Fluentd側**:
```bash
# .envファイルまたは環境変数に追加
export FLUENTD_SHARED_KEY=your-generated-key-here
```

---

## 動作確認

### 1. LogServerの起動

```bash
# LogServer起動
docker-compose up -d

# ログ確認
docker-compose logs -f fluentd
```

### 2. 証明書の検証

```bash
# LogServerのサーバー証明書を検証
openssl s_client -connect localhost:8888 \
  -CAfile certs/ca.crt \
  -cert certs/engine.crt \
  -key certs/engine.key
```

### 3. Engine Fluentdからのログ送信テスト

Engine Fluentdを起動して、ログが正常にLogServerに届くことを確認します。

```bash
# Engine Fluentd側でテストログを送信
echo '{"message":"test","customer_name":"test-customer","fqdn":"test.example.com"}' | \
  docker exec -i engine-fluentd fluentd-cat nginx.access
```

---

## トラブルシューティング

### TLSハンドシェイクエラー

**症状**: `SSL_connect returned=1 errno=0 state=error: certificate verify failed`

**原因**:
- CA証明書が正しく配布されていない
- クライアント証明書が無効

**対策**:
1. `ca.crt`が正しくEngine側に配布されているか確認
2. Engine側のクライアント証明書が正しくCAで署名されているか確認

```bash
# 証明書の検証
openssl verify -CAfile ca.crt engine.crt
```

### 共有シークレットキー不一致

**症状**: `shared_key mismatch`

**対策**:
1. LogServerとEngine Fluentdで同じ`FLUENTD_SHARED_KEY`を設定しているか確認
2. 環境変数が正しく読み込まれているか確認

```bash
# 環境変数の確認
docker exec fluentd env | grep FLUENTD_SHARED_KEY
```

### 証明書の有効期限切れ

**対策**:
証明書を再生成します。

```bash
# LogServer側で証明書を再生成
./scripts/generate-certs.sh

# Engine側でクライアント証明書を再生成
# （上記の手順を参照）

# Fluentdを再起動
docker-compose restart fluentd
```

---

## セキュリティのベストプラクティス

1. **秘密鍵の保護**:
   - `*.key`ファイルは絶対にバージョン管理にコミットしない
   - ファイル権限を`600`に設定

2. **証明書のローテーション**:
   - 証明書の有効期限を定期的に確認
   - 年1回のローテーションを推奨

3. **共有シークレットキー**:
   - 64文字以上のランダムな文字列を使用
   - 定期的にキーをローテーション

4. **アクセス制限**:
   - LogServerのポート8888はEngine Fluentdからのみアクセス可能にする
   - ファイアウォールで適切にフィルタリング

---

## 関連ドキュメント

- [MrWebDefence-LogServer設計書](../design/MWD-53-log-collection.md)
- [MrWebDefence-Engine Fluentd設計書](https://github.com/kencom2400/MrWebDefence-Engine/blob/main/docs/design/MWD-40-fluentd-modularization-plan.md)
