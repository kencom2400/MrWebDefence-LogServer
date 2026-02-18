# 運用マニュアル

MrWebDefence-LogServerの日常運用手順書

## 目次

1. [起動・停止](#起動停止)
2. [モニタリング](#モニタリング)
3. [ログ管理](#ログ管理)
4. [トラブルシューティング](#トラブルシューティング)
5. [定期メンテナンス](#定期メンテナンス)
6. [バックアップ・リストア](#バックアップリストア)
7. [スケーリング](#スケーリング)

---

## 起動・停止

### LogServerの起動

```bash
# バックグラウンドで起動
docker-compose up -d

# ログを表示しながら起動（フォアグラウンド）
docker-compose up
```

### LogServerの停止

```bash
# 正常停止（バッファをフラッシュしてから停止）
docker-compose stop

# 強制停止（緊急時のみ）
docker-compose kill
```

### LogServerの再起動

```bash
# 設定変更後の再起動
docker-compose restart

# または、停止してから起動
docker-compose down
docker-compose up -d
```

### ログの確認

```bash
# リアルタイムでログを表示
docker-compose logs -f fluentd

# 最新100行を表示
docker-compose logs --tail=100 fluentd
```

---

## モニタリング

### ヘルスチェック

**手動実行**:
```bash
# ヘルスチェックスクリプト
./scripts/healthcheck.sh
```

**自動監視**:
```bash
# Cron設定例（5分ごと）
*/5 * * * * /path/to/MrWebDefence-LogServer/scripts/healthcheck.sh || /path/to/alert-script.sh
```

### Prometheusメトリクス

**メトリクス取得**:
```bash
curl http://localhost:24231/metrics
```

**主要メトリクス**:

| メトリクス名 | 説明 | 正常範囲 |
|------------|------|---------|
| `fluentd_input_status_num_records_total` | 受信ログ数 | - |
| `fluentd_output_status_num_records_total` | 出力ログ数 | - |
| `fluentd_output_status_buffer_total_bytes` | バッファサイズ | < 1GB |
| `fluentd_output_status_retry_count` | リトライ回数 | 0 |

**アラート設定の推奨**:
- バッファサイズが1GB超過
- リトライ回数が継続的に増加
- 受信ログ数と出力ログ数に大きな乖離

### Monitor Agent

```bash
# Monitor Agent API
curl http://localhost:24220/api/plugins.json
```

---

## ログ管理

### ログの保存場所

**本番環境**（Dockerボリューム）:
```bash
# ログボリュームの確認
docker volume inspect mrwebdefence-logserver_logs

# ログボリューム内のファイルを確認
docker run --rm -v mrwebdefence-logserver_logs:/data alpine ls -lah /data
```

**ログディレクトリ構造**:
```
/var/log/mrwebdefence/
├── {customer_name}/
│   ├── nginx/
│   │   └── {fqdn}/
│   │       └── {YYYY}/
│   │           └── {MM}/
│   │               └── {DD}/
│   │                   └── {HH}.log.gz
│   └── openappsec/
│       └── {fqdn}/
│           └── {YYYY}/
│               └── {MM}/
│                   └── {DD}/
│                       └── {HH}.log.gz
```

### ログローテーション

Fluentdの`timekey`設定で自動的に1時間ごとにローテーションされます。

**手動でバッファをフラッシュ**:
```bash
# USR1シグナルを送信
docker exec mrwebdefence-logserver kill -USR1 1
```

### ログアーカイブ

**手動実行**:
```bash
# 環境変数を設定
export S3_BUCKET=mrwebdefence-logs
export S3_PREFIX=archive
export ARCHIVE_DAYS=30
export DELETE_DAYS=90

# アーカイブスクリプトを実行
./scripts/archive-logs.sh
```

**自動実行（Cron）**:
```bash
# /etc/cron.d/logserver-archive
0 3 * * * root /path/to/scripts/archive-logs.sh >> /var/log/archive-logs.log 2>&1
```

**アーカイブ設定のカスタマイズ**:
- `ARCHIVE_DAYS`: アーカイブ対象の日数（デフォルト: 30日）
- `DELETE_DAYS`: 削除対象の日数（デフォルト: 90日）
- `S3_BUCKET`: S3バケット名
- `S3_PREFIX`: S3内のプレフィックス

---

## トラブルシューティング

### 症状1: LogServerが起動しない

**確認項目**:
1. Docker/Docker Composeのバージョン
2. ポートの競合（8888, 8889, 24220, 24231）
3. 証明書ファイルの存在

**診断コマンド**:
```bash
# ポート確認
netstat -tuln | grep -E '8888|8889|24220|24231'

# 証明書確認
ls -lh certs/

# Fluentdログ確認
docker-compose logs fluentd
```

**対処法**:
```bash
# 競合するコンテナを停止
docker ps -a | grep 8888

# 証明書を再生成
./scripts/generate-certs.sh

# 再起動
docker-compose down
docker-compose up -d
```

### 症状2: ログが保存されない

**確認項目**:
1. Engine Fluentdから正常にログが送信されているか
2. バッファがフルになっていないか
3. ファイルシステムに空き容量があるか

**診断コマンド**:
```bash
# メトリクス確認
curl http://localhost:24231/metrics | grep fluentd_input_status_num_records_total
curl http://localhost:24231/metrics | grep fluentd_output_status_buffer_total_bytes

# ディスク容量確認
df -h

# バッファディレクトリ確認
docker run --rm -v mrwebdefence-logserver_buffer:/data alpine ls -lah /data
```

**対処法**:
```bash
# バッファをフラッシュ
docker exec mrwebdefence-logserver kill -USR1 1

# ディスク容量が不足している場合は古いログをアーカイブ
./scripts/archive-logs.sh
```

### 症状3: バッファが溜まり続ける

**原因**:
- ディスクI/O性能の不足
- ファイルシステムの権限エラー
- 設定ミス

**診断コマンド**:
```bash
# バッファサイズ確認
curl http://localhost:24231/metrics | grep fluentd_output_status_buffer_total_bytes

# リトライ回数確認
curl http://localhost:24231/metrics | grep fluentd_output_status_retry_count

# Fluentdログでエラー確認
docker-compose logs fluentd | grep ERROR
```

**対処法**:
```bash
# 設定を確認
cat config/fluentd/conf.d/03-output.conf

# ワーカー数を増やす（fluent.confを編集）
# workers 2 → workers 4

# flush_intervalを調整（03-output.confを編集）
# flush_interval 10s → flush_interval 30s

# 再起動
docker-compose restart
```

### 症状4: TLSハンドシェイクエラー

**症状**:
Engine FluentdからLogServerへの接続が失敗する。

**診断コマンド**:
```bash
# Engine側のログ確認
# SSL_connect returned=1 errno=0 state=error: certificate verify failed

# LogServer側の証明書検証
openssl s_client -connect localhost:8888 \
  -CAfile certs/ca.crt \
  -cert tests/certs/engine.crt \
  -key tests/certs/engine.key
```

**対処法**:
1. CA証明書がEngine側に正しく配布されているか確認
2. 証明書の有効期限を確認
3. 必要に応じて証明書を再生成

詳細は[SSL/TLS設定ガイド](../setup/ssl-setup.md)を参照。

---

## 定期メンテナンス

### 日次タスク

- [ ] ヘルスチェックの確認
- [ ] メトリクスの確認（バッファサイズ、リトライ回数）
- [ ] ディスク容量の確認

### 週次タスク

- [ ] ログ出力量の傾向確認
- [ ] エラーログの確認
- [ ] バックアップの実行確認

### 月次タスク

- [ ] ログアーカイブの実行確認
- [ ] 証明書の有効期限確認（残り3ヶ月以内なら更新）
- [ ] Docker Imageのアップデート確認

### 四半期タスク

- [ ] 設定のレビューと最適化
- [ ] 容量計画の見直し

---

## バックアップ・リストア

### バックアップ対象

1. **設定ファイル**: `config/fluentd/`
2. **証明書**: `certs/`
3. **ログデータ**: Dockerボリュームまたはアーカイブ

### バックアップ手順

**設定ファイルと証明書**:
```bash
# tarアーカイブ作成
tar czf logserver-config-$(date +%Y%m%d).tar.gz config/ certs/

# S3にアップロード
aws s3 cp logserver-config-$(date +%Y%m%d).tar.gz s3://backup-bucket/logserver/
```

**Dockerボリューム**:
```bash
# ログボリュームをバックアップ
docker run --rm \
  -v mrwebdefence-logserver_logs:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/logs-backup-$(date +%Y%m%d).tar.gz /data
```

### リストア手順

**設定ファイルと証明書**:
```bash
# バックアップから復元
tar xzf logserver-config-YYYYMMDD.tar.gz

# LogServerを再起動
docker-compose restart
```

**Dockerボリューム**:
```bash
# ログボリュームをリストア
docker run --rm \
  -v mrwebdefence-logserver_logs:/data \
  -v $(pwd):/backup \
  alpine sh -c "cd / && tar xzf /backup/logs-backup-YYYYMMDD.tar.gz"
```

---

## スケーリング

### 垂直スケーリング（リソース増強）

**CPU・メモリの増強**:
```yaml
# docker-compose.yml
services:
  fluentd:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          cpus: '2'
          memory: 4G
```

**ワーカー数の増加**:
```conf
# config/fluentd/fluent.conf
<system>
  log_level info
  workers 4  # 2 → 4に増やす
</system>
```

### 水平スケーリング（複数インスタンス）

**ロードバランサー経由でのスケール**:

```
[Engine 1] ─┐
[Engine 2] ─┼─→ [Load Balancer] ─┐
[Engine 3] ─┘                      ├─→ [LogServer 1]
                                   ├─→ [LogServer 2]
                                   └─→ [LogServer 3]
```

**注意事項**:
- 各LogServerインスタンスは独立したストレージを持つ
- ログの集約・検索にはElasticsearchなどの外部システムが必要

---

## 参考資料

- [設計書](../design/MWD-53-log-collection.md)
- [テスト設計書](../design/MWD-53-test-design.md)
- [SSL/TLS設定ガイド](../setup/ssl-setup.md)
- [Fluentd公式ドキュメント](https://docs.fluentd.org/)
