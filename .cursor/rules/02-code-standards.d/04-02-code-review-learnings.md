# コードレビューで学んだ観点

**優先度レベル**: `04-XX` - **推奨（SHOULD）** - できる限り従うべきルール

## 📚 Gemini Code Reviewから学んだこと

このファイルは、Gemini Code Assistのレビューで指摘された改善点を記録し、
今後の開発で同様の問題を防ぐためのガイドラインです。

---

## 1. ドキュメント内のハードコードされた値

### 問題

README.mdなどのドキュメントで、具体的な日付や値をハードコードすると：
- 時間経過で陳腐化する
- 実際の値と混同される可能性
- メンテナンスの手間が増える

### 指摘事例（MWD-54）

```bash
# ❌ 悪い例: 具体的な日付をハードコード
docker exec mrwebdefence-logserver ls -lh /var/log/mrwebdefence/customer-name/nginx/example.com/2026/02/19/

# ✅ 良い例: プレースホルダーを使用
docker exec mrwebdefence-logserver ls -lh /var/log/mrwebdefence/{customer-name}/nginx/{fqdn}/YYYY/MM/DD/
```

### ベストプラクティス

#### サンプルコマンドで使用すべきプレースホルダー

| 項目 | ハードコード例 | プレースホルダー |
|------|----------------|------------------|
| 日付 | `2026/02/19` | `YYYY/MM/DD` |
| 時刻 | `10:00:00` | `HH:MM:SS` |
| 時間 | `10.log.gz` | `HH.log.gz` |
| 顧客名 | `customer1` | `{customer-name}` |
| FQDN | `example.com` | `{fqdn}` |
| ユーザー名 | `john` | `{username}` |
| ID | `12345` | `{id}` |
| URL | `https://api.example.com` | `{api-url}` |

#### プレースホルダーの表記方法

```markdown
## 良い例

1. 波括弧で囲む: `{placeholder}`
2. 大文字で示す: `YYYY-MM-DD`
3. 山括弧で囲む: `<placeholder>`

## 実例

- ファイルパス: `/var/log/{service}/{YYYY}/{MM}/{DD}/`
- API URL: `https://api.example.com/v1/users/{user-id}`
- コマンド: `docker exec {container-name} ls -l`
```

### チェックリスト

ドキュメント作成・更新時：

- [ ] サンプルコマンドに具体的な日付が含まれていないか？
- [ ] 環境依存の値（ホスト名、IPアドレス等）がハードコードされていないか？
- [ ] プレースホルダーを使用して汎用的な説明になっているか？
- [ ] プレースホルダーの意味が明確か？

---

## 2. ログファイルのローテーション

### 問題

長期運用するログファイル（特に運用ログ）にローテーション設定がないと：
- ディスク使用量が無限に増大
- パフォーマンスの低下
- 運用の持続可能性の欠如

### 指摘事例（MWD-54）

**archive.log**: ログアーカイブスクリプトの実行ログ

```bash
# cron設定
0 3 * * * /opt/mrwebdefence/scripts/archive-logs.sh >> /var/log/mrwebdefence/archive.log 2>&1
```

このままでは `archive.log` が無限に増大する。

### 対策: logrotate設定

```bash
# /etc/logrotate.d/mrwebdefence-archive
/var/log/mrwebdefence/archive.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    create 0644 root root
    dateext
}
```

### ベストプラクティス

#### ローテーション対象の判定

以下のログファイルは**必ずローテーション設定が必要**：

1. **cronジョブの出力ログ**
   - 例: `archive.log`, `backup.log`, `cleanup.log`

2. **アプリケーションログ**
   - 例: `app.log`, `error.log`, `access.log`

3. **デーモンプロセスのログ**
   - 例: `daemon.log`, `service.log`

4. **システムログ**
   - 例: `system.log`, `audit.log`

#### ローテーション設定のテンプレート

```bash
# /etc/logrotate.d/{service-name}
/var/log/{service}/{log-file}.log {
    # ローテーション頻度
    daily                    # 日次（daily/weekly/monthly）
    
    # 保持期間
    rotate 30                # 30世代保持
    
    # サイズ制限（オプション）
    size 100M                # 100MB超えたらローテーション
    
    # 圧縮
    compress                 # gzip圧縮
    delaycompress            # 最新は圧縮しない
    
    # エラーハンドリング
    missingok                # ファイルがなくてもエラーにしない
    notifempty               # 空ファイルはローテーションしない
    
    # 権限
    create 0644 user group   # 新ファイルの権限
    
    # 日付サフィックス
    dateext                  # log-20260225形式
    dateformat -%Y%m%d
    
    # 後処理（オプション）
    postrotate
        # サービスリロード等
        systemctl reload {service} > /dev/null 2>&1 || true
    endscript
}
```

#### logrotateのテスト方法

```bash
# 設定の検証（dry-run）
sudo logrotate -d /etc/logrotate.d/{config-name}

# 強制実行（テスト）
sudo logrotate -f /etc/logrotate.d/{config-name}

# 状態確認
cat /var/lib/logrotate/status
```

### チェックリスト

ログファイル追加時：

- [ ] ログファイルは長期運用で増大するか？
- [ ] logrotate設定を追加したか？
- [ ] ローテーション頻度は適切か？（daily/weekly/monthly）
- [ ] 保持期間は要件を満たしているか？
- [ ] 圧縮設定を有効にしたか？
- [ ] テスト実行で動作確認したか？

---

## 3. Path Traversal対策の徹底

### 問題（MWD-54で指摘）

ユーザー入力をファイルパスに使用する際、サニタイズロジックは実装されていたが、
**サニタイズ済み変数が実際には使用されていなかった**。

### 指摘内容

```ruby
# 02-filter.conf: サニタイズ処理は存在
safe_customer_name ${(record["customer_name"] || "unknown").gsub(/[^a-zA-Z0-9_-]/, '_')}
safe_fqdn ${(record["fqdn"] || "unknown").gsub(/[^a-zA-Z0-9._-]/, '_')}

# 03-output.conf: しかしサニタイズ前の変数を使用（問題）
path /var/log/mrwebdefence/${customer_name}/${log_type}/${fqdn}/...  # ❌

# 修正後: サニタイズ済み変数を使用
path /var/log/mrwebdefence/${safe_customer_name}/${log_type}/${safe_fqdn}/...  # ✅
```

### ベストプラクティス

#### サニタイズの3原則

1. **入力値をそのまま使わない**
   - 必ずサニタイズ処理を通す

2. **サニタイズ済み変数を明示的に命名**
   - `safe_*`, `sanitized_*`, `validated_*` などの接頭辞
   - 元の変数とサニタイズ済み変数を区別

3. **使用箇所で必ずサニタイズ済み変数を使用**
   - コードレビューで確認
   - 静的解析ツールで検出

#### サニタイズ実装のパターン

```ruby
# パターン1: Fluentd（Ruby）
<record>
  # 元の値を保持
  original_customer_name ${record["customer_name"] || "unknown"}
  
  # サニタイズ済み変数（ファイルパスに使用）
  safe_customer_name ${(record["customer_name"] || "unknown").gsub(/[^a-zA-Z0-9_-]/, '_')}
</record>

# 出力では必ずsafe_*を使用
path /var/log/${safe_customer_name}/...
```

```typescript
// パターン2: TypeScript/Node.js
function sanitizeForPath(input: string): string {
  return input.replace(/[^a-zA-Z0-9._-]/g, '_');
}

const originalCustomerName = req.body.customer_name;
const safeCustomerName = sanitizeForPath(originalCustomerName);

// ファイルパスには必ずsafeを使用
const logPath = `/var/log/${safeCustomerName}/...`;
```

```python
# パターン3: Python
import re

def sanitize_for_path(input_str: str) -> str:
    return re.sub(r'[^a-zA-Z0-9._-]', '_', input_str)

original_customer_name = request.json['customer_name']
safe_customer_name = sanitize_for_path(original_customer_name)

# ファイルパスには必ずsafeを使用
log_path = f"/var/log/{safe_customer_name}/..."
```

#### 危険な文字の一覧

| 文字 | リスク | サニタイズ方法 |
|------|--------|----------------|
| `../` | Path Traversal | 削除または置換 |
| `/` | ディレクトリ区切り | `_` に置換 |
| `\` | Windowsパス区切り | `_` に置換 |
| `..` | 親ディレクトリ | `_` に置換 |
| `~` | ホームディレクトリ | `_` に置換 |
| `$` | 変数展開 | `_` に置換 |
| `` ` `` | コマンド実行 | `_` に置換 |
| `;` | コマンド連結 | `_` に置換 |
| `|` | パイプ | `_` に置換 |
| `&` | バックグラウンド実行 | `_` に置換 |

#### ホワイトリスト方式の推奨

```regex
# 推奨: ホワイトリスト（許可する文字のみ残す）
/[^a-zA-Z0-9._-]/g  → '_'

# 非推奨: ブラックリスト（危険な文字を除去）
/[\.\/\\~$`;&|]/g  → ''  # 漏れのリスクが高い
```

### チェックリスト

ユーザー入力をファイルパスに使用する際：

- [ ] サニタイズ処理を実装したか？
- [ ] サニタイズ済み変数を明示的に命名したか？（`safe_*` など）
- [ ] **全ての使用箇所でサニタイズ済み変数を使用しているか？**（最重要）
- [ ] ホワイトリスト方式を採用しているか？
- [ ] テストでPath Traversal攻撃を試行したか？

---

## 4. DoS対策: リソース枯渇の防止

### 問題（Geminiの指摘傾向）

ユーザー入力に基づいて動的にリソース（ファイル、ディレクトリ、バッファ等）を
作成する場合、**無制限に作成できると DoS 攻撃のリスク**。

### 指摘事例

```ruby
# 問題: customer_nameとfqdnに基づいてディレクトリを無制限に作成
path /var/log/mrwebdefence/${safe_customer_name}/${log_type}/${safe_fqdn}/...
```

攻撃者が大量の異なる `customer_name` や `fqdn` を送信すると、
ファイルシステムが枯渇する可能性。

### 対策

#### 1. ホワイトリスト検証

```ruby
# 許可された顧客のみ受け入れ
<filter>
  @type grep
  <regexp>
    key customer_name
    pattern /^(customer1|customer2|customer3)$/
  </regexp>
</filter>
```

#### 2. 制限値の設定

```yaml
# 最大ディレクトリ数の制限
max_directories: 1000

# 最大ファイル数の制限
max_files_per_directory: 10000
```

#### 3. モニタリングとアラート

```bash
# ディスク使用量の監視
df -h /var/log/mrwebdefence

# ディレクトリ数の監視
find /var/log/mrwebdefence -type d | wc -l
```

### チェックリスト

動的リソース作成時：

- [ ] リソース作成数に上限はあるか？
- [ ] ホワイトリスト検証を実装したか？
- [ ] ディスク使用量のモニタリングを設定したか？
- [ ] DoS攻撃のテストを実施したか？

---

## 5. 権限昇格（Privilege Escalation）のリスク

### 問題（Geminiの指摘傾向）

低権限ユーザーが書き込み可能なログファイルに、高権限プロセス（cron等）が
出力すると、**権限昇格のリスク**。

### 指摘事例

```bash
# cron（root権限）がユーザー書き込み可能なディレクトリにログ出力
0 3 * * * /opt/mrwebdefence/scripts/archive-logs.sh >> /var/log/mrwebdefence/archive.log 2>&1
```

もし `/var/log/mrwebdefence/` が低権限ユーザーで書き込み可能なら、
攻撃者が `archive.log` をシンボリックリンクで置き換え、任意のファイルに
書き込める可能性。

### 対策

#### 1. 適切なディレクトリ権限

```bash
# rootのみ書き込み可能
sudo mkdir -p /var/log/mrwebdefence
sudo chmod 755 /var/log/mrwebdefence  # root:rwx, other:r-x
sudo chown root:root /var/log/mrwebdefence
```

#### 2. 専用ディレクトリの使用

```bash
# システムログ用の専用ディレクトリ
/var/log/system/{service}/archive.log
```

#### 3. ログファイルの権限

```bash
# logrotateで適切な権限を設定
create 0644 root root
```

### チェックリスト

高権限プロセスからのログ出力時：

- [ ] ログディレクトリの権限は適切か？（root所有、755）
- [ ] ログファイルの権限は適切か？（644以下）
- [ ] 低権限ユーザーが書き込み可能なディレクトリではないか？
- [ ] シンボリックリンク攻撃のリスクはないか？

---

## まとめ

### コードレビューで確認すべき5つのポイント

1. **ドキュメント**: ハードコードされた値はプレースホルダーに
2. **ログローテーション**: 長期運用ログは必ず設定
3. **Path Traversal**: サニタイズ済み変数を確実に使用
4. **DoS対策**: 動的リソース作成に上限設定
5. **権限昇格**: 高権限プロセスのログ出力先を確認

### レビューチェックリスト

PRレビュー時に確認：

- [ ] README等でハードコードされた日付・値を使用していないか？
- [ ] 新規ログファイルにローテーション設定があるか？
- [ ] Path Traversal対策でサニタイズ済み変数を使用しているか？
- [ ] 動的リソース作成に上限があるか？
- [ ] ログ出力先のディレクトリ権限は適切か？

---

## 参考資料

- [OWASP Path Traversal](https://owasp.org/www-community/attacks/Path_Traversal)
- [OWASP Denial of Service](https://owasp.org/www-community/attacks/Denial_of_Service)
- [Linux logrotate(8)](https://linux.die.net/man/8/logrotate)
