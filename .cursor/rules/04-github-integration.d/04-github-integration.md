# GitHub統合 - Issue管理・ステータス・報告

このファイルは、GitHub Projects管理、Issueステータス管理、Issue完了報告の運用ルールを統合したものです。

---

## 🔴 重要: GitHub CLI実行時の権限設定

**GitHub CLI (`gh`) コマンドは、必ず`required_permissions: ['all']`を指定してください。**

### 対象コマンド

以下のコマンドは**すべて`all`権限が必要**：

1. **Issue操作**: `gh issue view`, `gh issue comment`, `gh issue list`
2. **PR操作**: `gh pr view`, `gh pr create`, `gh pr comment`
3. **Projects操作**: `gh project item-list`, `gh api graphql`
4. **ワークフロースクリプト**: `./scripts/github/workflow/start-task.sh`

### 理由

- **証明書検証**: HTTPSでのGitHub API接続
- **認証トークン**: GitHub Personal Access Tokenへのアクセス
- **環境変数**: `GH_TOKEN`などの機密情報
- **ネットワークアクセス**: API呼び出し

### 実装例

```typescript
// ✅ 正しい
run_terminal_cmd({
  command: 'gh issue view 248 --json number,title,body',
  required_permissions: ["all"]
})

// ✅ 正しい
run_terminal_cmd({
  command: './scripts/github/workflow/start-task.sh',
  required_permissions: ["all"]
})

// ❌ エラーになる（証明書検証失敗）
run_terminal_cmd({
  command: 'gh issue view 248',
  required_permissions: ["network"]
})

// ❌ エラーになる（権限不足）
run_terminal_cmd({
  command: './scripts/github/workflow/start-task.sh'
  // required_permissions指定なし
})
```

**Issue #248の経験: `network`権限だけでは証明書検証エラーが発生。最初から`all`権限で実行すること。**

---

## 📋 目次

1. [GitHub Projects設定](#1-github-projects設定)
2. [Issueステータス管理](#2-issueステータス管理)
3. [Issue完了報告](#3-issue完了報告)
4. [PRコメント投稿](#4-prコメント投稿)
5. [@start-task統合](#5-start-task統合)

---

## 1. GitHub Projects設定

### プロジェクト情報

- **プロジェクト名**: Account Book Development
- **プロジェクト番号**: #1
- **プロジェクトID**: `PVT_kwHOANWYrs4BIOm-`
- **所有者**: @kencom2400

### ステータスフィールド

**ステータス一覧（順序）:**

1. 🎯 Epic (ID: `9aa232cf`)
2. 📋 Backlog (ID: `f908f688`)
3. 📝 To Do (ID: `f36fcf60`)
4. 🚧 In Progress (ID: `16defd77`)
5. 👀 Review (ID: `0f0f2f26`)
6. ✅ Done (ID: `2f722d70`)

**ステータスフィールドID**: `PVTSSF_lAHOANWYrs4BIOm-zg4wCDo`

### Issueワークフロー

```
📋 Backlog → 📝 To Do → 🚧 In Progress → 👀 Review → ✅ Done
```

**ステータス遷移のタイミング:**

- **Backlog**: Issue作成時（自動設定）
- **To Do**: 次に取り組むIssueとして選択した時
- **In Progress**: 実際の作業を開始した時
- **Review**: PRを作成し、レビューを依頼した時
- **Done**: PRがマージされ、Issueをクローズした時

### 🚨 Issue作成方法（重要）

**✅ 必須: 専用スクリプトを使用**

新規Issueを作成する際は、**必ず以下のスクリプトを使用**してください：

#### 方法1: GraphQL統合スクリプト（推奨）

複雑なIssueや長い本文のIssueを作成する場合は、GraphQL統合スクリプトを使用してください：

```bash
# 対話型モード
./scripts/github/issues/create-issue-graphql.sh

# バッチモード（コマンドライン引数）
./scripts/github/issues/create-issue-graphql.sh \
  --title "[bug] タイトル" \
  --body "本文" \
  --labels "bug,testing" \
  --priority "high"

# ファイルから本文を読み込み
./scripts/github/issues/create-issue-graphql.sh \
  --title "[feature] タイトル" \
  --body-file ./scripts/github/issues/templates/feature-template.md \
  --labels "feature,backend" \
  --priority "medium"
```

**メリット:**

- ✅ エスケープ処理が不要
- ✅ プロジェクトへの追加とステータス設定が自動
- ✅ エラーハンドリングが強化されている
- ✅ 対話型とバッチモードの両対応
- ✅ 再現性が高い

**詳細**: `./scripts/github/issues/create-issue-graphql.README.md`

#### 方法2: ファイルベーススクリプト（大量作成向け）

YAML/JSONファイルから大量のIssueを作成する場合は、ファイルベーススクリプトを使用してください：

```bash
# 1. Issue用のJSONまたはYAMLファイルを作成
cat > scripts/github/issues/issue-data/drafts/my-issue.json << EOF
{
  "title": "[FEATURE] 新機能の実装",
  "labels": ["feature", "backend"],
  "body": "## 概要\n\n詳細な説明..."
}
EOF

# 2. スクリプトでIssue作成
./scripts/github/issues/create-issue.sh scripts/github/issues/issue-data/drafts/my-issue.json
```

**メリット:**

- ✅ テンプレート管理が簡単
- ✅ 大量のIssueを一括作成できる
- ✅ バージョン管理が可能

**詳細**: `./scripts/github/issues/README.md`

#### 使い分け

| 用途                       | スクリプト                | 理由                                 |
| -------------------------- | ------------------------- | ------------------------------------ |
| **1つのIssueをすぐに作成** | `create-issue-graphql.sh` | コマンドラインで直接指定可能         |
| **複雑な本文のIssue**      | `create-issue-graphql.sh` | テンプレートファイルから読み込み可能 |
| **大量のIssueを一括作成**  | `create-issue.sh`         | ファイルベースで管理しやすい         |
| **対話型で作成**           | `create-issue-graphql.sh` | 対話型モード対応                     |

**❌ 禁止: GitHub CLI直接使用**

```bash
# ❌ これは使用しないでください
gh issue create --title "..." --body "..."
```

**理由:**

- プロジェクトに自動追加されません
- ステータスが"No Status"になります
- 手動でプロジェクトに追加する手間が発生します

**例外:**

テスト目的など、意図的にプロジェクトに追加したくない場合のみ、GitHub CLI直接使用を許可します。

---

## 2. Issueステータス管理

### 基本方針

**AIアシスタントは、ユーザーとの会話の文脈を理解し、適切なタイミングでIssue/PRのステータスを更新します。**

- ✅ 自然な対話フローの中で状態を確認
- ✅ 文脈に応じた適切な判断
- ✅ ユーザーの意図を尊重
- ❌ 機械的・自動的な更新は行わない

### トリガー条件

#### 1. PR関連の会話

**マージ完了時:**

```
ユーザー: "PRをマージしました"
ユーザー: "マージ完了"
ユーザー: "#217をマージした"
```

**アクション:**

1. PRの状態を確認（`gh pr view <PR番号> --json state,mergedAt`）
2. マージされている場合（`state: "MERGED"`）、関連Issueを特定
   - PR本文から「Closes #XXX」「Fixes #XXX」「Resolves #XXX」を抽出
   - 会話の文脈から関連Issueを特定
3. **プロジェクトステータスを「✅ Done」に更新**（`./scripts/github/projects/set-issue-done.sh <issue番号>`）
4. Issueをクローズ（必要に応じて）

**重要**: ユーザーが「マージします」と言った場合、マージ実行後に自動的にステータスを更新する

#### 2. 作業完了の報告

```
ユーザー: "実装完了"
ユーザー: "タスク完了"
ユーザー: "#219の作業が終わりました"
```

**アクション:**

1. 作業内容を確認
2. PRが作成されているか確認
3. PRの状態に応じてIssueステータスを更新

#### 3. 明示的な指示

```
ユーザー: "Issueステータスを更新して"
ユーザー: "#219をDoneにして"
```

**アクション:**

1. 指示に従ってステータスを更新
2. 更新結果を報告

### 実行フロー

#### ステップ1: PR状態の確認

```bash
# PRの詳細を取得
gh pr view <PR番号> --json number,title,state,mergedAt,closedAt,body
```

**判定条件:**

- `state: "MERGED"` かつ `mergedAt` が存在 → マージ済み
- `state: "CLOSED"` かつ `mergedAt` が null → クローズのみ
- `state: "OPEN"` → まだオープン

#### ステップ2: 関連Issueの特定

PRの本文から関連Issueを抽出：

```typescript
// 複数のIssueキーワードに対応
const issueKeywords = ['Closes', 'Fixes', 'Resolves', 'closes', 'fixes', 'resolves'];
const issueNumbers: number[] = [];

for (const keyword of issueKeywords) {
  const regex = new RegExp(`${keyword}\\s+#(\\d+)`, 'g');
  let match;
  while ((match = regex.exec(prBody)) !== null) {
    const issueNumber = parseInt(match[1], 10);
    if (!issueNumbers.includes(issueNumber)) {
      issueNumbers.push(issueNumber);
    }
  }
}
```

#### ステップ3: Issueステータスの更新

```bash
# In Progressに変更
./scripts/github/projects/set-issue-in-progress.sh <issue番号>

# Doneに変更
./scripts/github/projects/set-issue-done.sh <issue番号>
```

#### ステップ4: 確認メッセージ

更新結果をユーザーに報告：

```
✅ Issue #209のステータスを「✅ Done」に更新しました
✅ プロジェクト: Account Book Development
```

### 注意事項

#### 1. 確認してから更新

**常にPRの状態を確認してから更新する**:

```bash
# 良い例: 状態確認後に更新
gh pr view 217 --json state
# state が MERGED であることを確認してから
./scripts/github/projects/set-issue-done.sh 209
```

#### 2. ユーザーの意図を尊重

機械的に更新せず、必要に応じて確認

#### 3. エラーハンドリング

スクリプト実行時のエラーを適切に処理

#### 4. 複数Issue対応

1つのPRが複数のIssueに関連する場合：

```
PR本文: "Closes #209, Closes #210"
```

全ての関連Issueのステータスを更新する。

---

## 3. Issue完了報告

```
╔══════════════════════════════════════════════════════════════╗
║  🚨 Issue作業完了時は必ずGitHub Issueに報告コメント 🚨      ║
║                                                              ║
║  タイミング:                                                 ║
║  1. commit完了後（push前でも可）                             ║
║  2. 長時間作業（4時間超）の場合は途中報告                    ║
║                                                              ║
║  方法: gh issue comment コマンドで自動投稿                   ║
╚══════════════════════════════════════════════════════════════╝
```

### トリガー条件

以下のいずれかが満たされた時、自動的に報告コメントを作成：

1. **commit完了時**: 最終コミット完了後（push前でも可）
2. **作業完了を明示的に宣言した時**: 「作業完了」「完了しました」等のキーワード
3. **長時間作業の途中**: 4時間経過時

**推奨フロー**:

```
1. 作業完了
   ↓
2. git commit（すべての変更をコミット）
   ↓
3. Issue報告コメント投稿 ⭐ ここで報告
   ↓
4. git push
   ↓
5. PR作成
```

### 報告対象のIssueタイプ

すべてのIssueタイプで報告を行う：

- `feature`, `task`, `bug`, `enhancement`, `process`, `documentation`

### 除外対象

**Issueが存在しない場合のみ除外**

### 報告コマンドの実行

#### 基本フォーマット

```bash
# コメント本文をヒアドキュメントで変数に格納
BODY=$(cat <<'EOF'
## 🎉 作業完了報告

Issue #<ISSUE_NUMBER>「<Issueタイトル>」の作業が完了しました。

---

## 📊 実施した作業

### <作業項目1>

**内容**:
- <詳細内容>

**成果物**:
- <ファイル1>
- <ファイル2>

**コミット**: `<コミットメッセージ>`

---

## 📂 成果物

### 新規作成ファイル（合計Xファイル）

1. **<カテゴリ1>** (Xファイル)
   - `path/to/file1`
   - `path/to/file2`

### 更新ファイル（合計Xファイル）

1. **<ファイル名>**
   - `path/to/file`
   - <変更内容の概要>

---

## ✅ 達成した目標

### Issueの受入基準

- [x] <受入基準1>
- [x] <受入基準2>

### 期待される効果

✅ **<効果1>**
- <詳細>

---

## 🚀 次のステップ

### 1. レビュー依頼
- [ ] <レビュー項目1>

### 2. マージ後
- [ ] <実施事項1>

---

## 📊 作業時間

- <作業項目1>: 約X時間
- **合計**: 約X時間

---

## 🔗 関連リンク

- **PR**: <PR URL または「作成予定」>
- **ブランチ**: `feature/issue-XXX-description`
- **コミット数**: X

---

以上で、Issue #<ISSUE_NUMBER>の作業が完了しました。

**次のアクション**:
- [ ] git push
- [ ] PR作成
- [ ] レビュー依頼
EOF
)

# GitHub CLIでコメント投稿
gh issue comment <ISSUE_NUMBER> --body "$BODY"
```

### 必須項目

1. **実施した作業**: 作業項目ごとに内容・成果物・コミットを記載
2. **成果物サマリ**: 新規作成ファイルと更新ファイルをカテゴリ別に整理
3. **達成した目標**: 受入基準チェックと期待される効果
4. **次のステップ**: レビュー依頼とマージ後のタスク
5. **メタ情報**: 作業時間と関連リンク

### チェックリスト

報告前に以下を確認：

- [ ] Issue番号が正しい
- [ ] 実施した作業が具体的に記載されている
- [ ] 成果物（ファイル）が列挙されている
- [ ] 受入基準の達成状況が明記されている
- [ ] 次のステップ（レビュー依頼等）が明記されている
- [ ] PRへのリンクが含まれている
- [ ] コミット情報が含まれている

---

## 4. PRコメント投稿

```
╔══════════════════════════════════════════════════════════════╗
║  🚨 PRコメント投稿時は必ず正しい形式で投稿 🚨                ║
║                                                              ║
║  重要原則:                                                   ║
║  1. --body を使用（--body-file は使わない）                  ║
║  2. 投稿前に内容を確認                                       ║
║  3. 投稿後に表示を検証                                       ║
║  4. 1コメントずつ投稿（まとめて投稿しない）                  ║
║  5. 失敗したらすぐ削除（再投稿は1度だけ）                    ║
╚══════════════════════════════════════════════════════════════╝
```

### 基本原則

**❌ 絶対にやってはいけないこと:**

```bash
# ❌ JSONファイルをそのまま投稿（JSONが表示される）
gh pr comment 29 --body-file /tmp/comment.json

# ❌ 複数のコメントをまとめて投稿
gh pr comment 29 --body "コメント1"
gh pr comment 29 --body "コメント2"
gh pr comment 29 --body "コメント3"  # 順序が崩れる
```

**✅ 正しい方法:**

```bash
# ✅ --body で直接Markdownテキストを投稿
gh pr comment 29 --body "## タイトル

詳細内容...

- リスト1
- リスト2

Commit: abc1234"

# ✅ 投稿後すぐに表示確認
gh pr view 29 --comments | tail -50
```

### 投稿前チェックリスト

PRコメントを投稿する前に、必ず以下を確認：

- [ ] `--body` オプションを使用しているか？（`--body-file` ではない）
- [ ] コメント内容はMarkdown形式か？（JSONではない）
- [ ] 特殊文字（バッククォート、ドル記号等）は適切にエスケープされているか？
- [ ] コメント内容を`echo`等で事前確認したか？
- [ ] `required_permissions: ["all"]` を指定しているか？

### 投稿コマンドの形式

#### パターン1: 短いコメント（直接指定）

```bash
gh pr comment <PR番号> --body "コメント内容"
```

#### パターン2: 長いコメント（ヒアドキュメント）

```bash
gh pr comment <PR番号> --body "## タイトル

### セクション1

内容...

### セクション2

内容...

Commit: abc1234"
```

**重要: バッククォートのエスケープ**

```bash
# ✅ 正しい（バッククォートをエスケープ）
gh pr comment 29 --body "コードは\`sudo rm -rf\`を使用"

# または引用符を使い分ける
gh pr comment 29 --body 'コードは`sudo rm -rf`を使用'
```

### 投稿後の検証（必須）

**コメント投稿後、必ず表示を確認する:**

```bash
# 方法1: 最新50行を表示
gh pr view <PR番号> --comments | tail -50

# 方法2: Webブラウザで確認
gh pr view <PR番号> --web
```

**確認項目:**

- [ ] コメントが正しくMarkdownでレンダリングされているか？
- [ ] JSONがそのまま表示されていないか？
- [ ] 特殊文字が正しく表示されているか？
- [ ] コードブロック、リスト、リンクが正しく機能しているか？

### 失敗時の対応フロー

```
1. 投稿
   ↓
2. 表示確認
   ↓
3. 問題発見（JSONが表示される等）
   ↓
4. すぐに削除（ユーザーやレビュアーが見る前に）
   ↓
5. 原因を特定
   ↓
6. 修正して再投稿（1度だけ）
   ↓
7. 表示を再確認
```

**コメント削除コマンド:**

```bash
# ステップ1: 自分のコメントIDを取得
gh api repos/<owner>/<repo>/issues/<PR番号>/comments | \
  jq -r '.[] | select(.user.login == "<your_username>") | "\(.id) | \(.created_at) | \(.body[0:50])"'

# ステップ2: 削除
gh api -X DELETE repos/<owner>/<repo>/issues/comments/<comment_id>
```

### 投稿タイミングのベストプラクティス

**❌ 悪い例（今回の失敗）:**

```
1. コミット1完了 → コメント投稿（失敗）
2. コミット2完了 → コメント投稿（失敗）
3. コミット3完了 → コメント投稿（失敗）
4. 問題発覚 → 3つまとめて削除・再投稿
   結果: 順序が崩れ、レビュアーが混乱
```

**✅ 良い例:**

```
1. コミット1完了 → コメント投稿 → 表示確認 → OK
2. レビュアーの返信待ち（必要に応じて）
3. コミット2完了 → コメント投稿 → 表示確認 → OK
4. レビュアーの返信待ち（必要に応じて）
5. コミット3完了 → コメント投稿 → 表示確認 → OK
   結果: 時系列が明確、議論が追いやすい
```

### エスケープが必要な文字

Markdown内で特別な意味を持つ文字は、適切にエスケープする必要があります：

| 文字 | エスケープ方法 | 例 |
|------|----------------|-----|
| バッククォート \` | `\`` または `'...'`で囲む | `\`code\`` または `'`code`'` |
| ドル記号 $ | `\$` | `\${variable}` |
| バックスラッシュ \ | `\\` | `path\\to\\file` |
| アスタリスク * | `\*` | `\*not italic\*` |
| アンダースコア _ | `\_` | `file\_name` |

### コマンド実行時の権限

**PRコメント投稿は必ず`required_permissions: ["all"]`を指定:**

```typescript
// ✅ 正しい
run_terminal_cmd({
  command: 'gh pr comment 29 --body "..."',
  required_permissions: ["all"]
})

// ❌ エラーになる
run_terminal_cmd({
  command: 'gh pr comment 29 --body "..."'
  // required_permissionsなし
})
```

### よくある失敗パターンと対策

#### 失敗1: JSONがそのまま表示される

**原因**: `--body-file` でJSONファイルを渡した

```bash
# ❌ 失敗例
echo '{"body": "コメント"}' > /tmp/comment.json
gh pr comment 29 --body-file /tmp/comment.json
# 結果: {"body": "コメント"} がそのまま表示
```

**対策**: `--body` で直接Markdownテキストを渡す

```bash
# ✅ 正しい
gh pr comment 29 --body "コメント"
```

#### 失敗2: 特殊文字が正しく表示されない

**原因**: エスケープ不足

```bash
# ❌ 失敗例
gh pr comment 29 --body "コードは `sudo rm -rf` です"
# 結果: バッククォートが解釈されてしまう
```

**対策**: 適切にエスケープ

```bash
# ✅ 正しい
gh pr comment 29 --body 'コードは `sudo rm -rf` です'
# または
gh pr comment 29 --body "コードは\`sudo rm -rf\`です"
```

#### 失敗3: 複数コメントを連続投稿

**原因**: まとめて投稿し、削除・再投稿で順序が崩れた

**対策**: 1つずつ投稿し、表示確認してから次へ

### チェックリスト（投稿時）

```markdown
## PRコメント投稿チェックリスト

投稿前:
- [ ] `--body` オプションを使用
- [ ] Markdown形式で記述
- [ ] 特殊文字をエスケープ
- [ ] `required_permissions: ["all"]` を指定

投稿後:
- [ ] `gh pr view --comments` で表示確認
- [ ] Markdownが正しくレンダリングされているか確認
- [ ] 失敗していたらすぐ削除

複数コメント投稿時:
- [ ] 1つずつ投稿
- [ ] 各コメント投稿後に表示確認
- [ ] 必要に応じてレビュアーの返信を待つ
```

---

## 5. @start-task統合

### 🚨 トリガー: `@start-task` コマンド

**🔴 重要: 実行権限について**

`@start-task`コマンドの実行時は、以下の理由から**必ず`required_permissions: ['all']`を指定**してください：

1. **GitHub API呼び出し**: Issue情報の取得、プロジェクトステータスの更新
2. **Git操作**: ブランチの作成、チェックアウト
3. **証明書検証**: HTTPSでのGitHub接続

**サンドボックス環境ではこれらの操作がエラーになるため、最初からall権限で実行すること。**

```typescript
// ✅ 正しい実行方法
run_terminal_cmd({
  command: "./scripts/github/workflow/start-task.sh",
  required_permissions: ["all"]
})

// ❌ サンドボックスではエラーになる
run_terminal_cmd({
  command: "./scripts/github/workflow/start-task.sh",
  // required_permissionsなし、またはnetworkのみ
})
```

**実行内容:**

0. **ルールファイル再読込**（最優先）
   - すべてのルールファイルを読み込む（@inc-all-rulesと同じ処理）
   - 最新のプロジェクトルールに従って作業を実行

1. **Issue取得**
   - GitHub Projectsから「📝 To Do」ステータスのIssueを取得
   - 各IssueのAssignee情報を確認
   - 自分にアサインされているOPENなIssueをフィルタリング

2. **優先順位判定とソート**
   - `priority: critical` → レベル4
   - `priority: high` → レベル3
   - `priority: medium` → レベル2
   - `priority: low` → レベル1
   - ラベルなし → レベル0
   - 同じ優先度の場合、Issue番号が小さい方を優先

3. **最優先Issueの選択と開始**
   - ソート後の最初のIssueを選択
   - Issueの詳細を表示
   - mainブランチを最新化してからブランチを作成
   - **GitHub ProjectsのステータスをIn Progressに変更**
   - Issueの内容に従って作業を即座に開始

### ✨ 新機能: start-task.sh スクリプト

Issue #201で実装された`start-task.sh`スクリプトを使用して、Issue開始を自動化できます。

#### 基本的な使い方

```bash
# 最優先Issueを自動選択
./scripts/github/workflow/start-task.sh

# Issue番号を指定して開始
./scripts/github/workflow/start-task.sh #201
./scripts/github/workflow/start-task.sh 201  # #なしでもOK

# ヘルプ表示
./scripts/github/workflow/start-task.sh --help
```

#### 機能

**自動選択モード（引数なし）:**

- GitHub Projectsから「📝 To Do」ステータスのIssueを取得
- 優先度順に自動ソート
- 最優先Issueを自動的に開始

**Issue ID指定モード（引数あり）:**

- 指定したIssue番号で作業を開始
- Issue存在確認、ステータス確認を自動実行

#### スクリプトが実行する処理

1. Issue情報の取得と確認
   - Issue存在確認
   - OPENステータス確認
   - アサイン状況確認
2. 自分にアサイン（未アサインの場合）
3. mainブランチの最新化
4. フィーチャーブランチの作成（`feature/issue-{番号}-{タイトル}`）
5. GitHub ProjectsでステータスをIn Progressに変更

#### エラーハンドリング

- Issue不存在時: エラーメッセージを表示して終了
- クローズ済みIssue: エラーメッセージを表示して終了
- 既にアサイン済み: 確認プロンプトを表示
- 他の人にアサイン済み: エラーメッセージを表示して終了
- 無効な形式: エラーメッセージと正しい形式を表示

詳細は[scripts/github/workflow/README.md](../../../scripts/github/workflow/README.md)を参照してください。

### Issue取得コマンド（手動実行の場合）

**🔴 重要: Issue詳細取得のベストプラクティス**

Issue詳細を取得する際は、**必ず`required_permissions: ['all']`を指定**してください。
サンドボックス環境では証明書検証やネットワークアクセスの制限により、GitHub API呼び出しが失敗します。

```typescript
// ✅ 正しい実行方法
run_terminal_cmd({
  command: "gh issue view 248 --json number,title,body,labels",
  required_permissions: ["all"]
})

// ❌ サンドボックスではエラーになる
run_terminal_cmd({
  command: "gh issue view 248 --json number,title,body,labels",
  required_permissions: ["network"]  // これでもエラーになる
})
```

**エラーの理由:**
- 証明書検証の問題
- GitHub APIのHTTPS接続
- 環境変数やトークンへのアクセス

**GitHub CLI (`gh`) コマンドを実行する際は、常に`all`権限を使用すること。**

```bash
# ステップ1: GitHub Projectsから "📝 To Do" ステータスのIssue番号を取得
PROJECT_NUMBER=1
OWNER="kencom2400"

TODO_ISSUES=$(gh project item-list "$PROJECT_NUMBER" --owner "$OWNER" --format json --limit 9999 | \
  jq -r '.items[] | select(.status == "📝 To Do") | .content.number')

# ステップ2: 各IssueのAssignee情報とState（OPEN/CLOSED）を確認
ASSIGNED_ISSUES=()
for issue_num in $TODO_ISSUES; do
  assignee=$(gh issue view "$issue_num" --json assignees --jq '.assignees[].login' 2>/dev/null)
  issue_state=$(gh issue view "$issue_num" --json state --jq '.state' 2>/dev/null)
  current_user=$(gh api user --jq '.login')

  # OPENなIssueかつ自分にアサインされているもののみを対象
  if [ "$issue_state" = "OPEN" ] && echo "$assignee" | grep -q "$current_user"; then
    ASSIGNED_ISSUES+=("$issue_num")
  fi
done

# ステップ3: アサインされているIssueの詳細を取得
if [ ${#ASSIGNED_ISSUES[@]} -eq 0 ]; then
  echo "[]"
else
  for issue_num in "${ASSIGNED_ISSUES[@]}"; do
    gh issue view "$issue_num" --json number,title,labels,url
  done | jq -s '.'
fi
```

### ブランチ作成とステータス更新

```bash
# mainブランチを最新化
git checkout main
git pull origin main

# 新しいブランチを作成
git checkout -b feature/issue-<番号>-<説明>

# GitHub ProjectsのステータスをIn Progressに変更
./scripts/github/projects/set-issue-in-progress.sh <issue番号>
```

**重要事項:**

- ✅ 質問・確認なしで即座に実行
- ✅ GitHub ProjectsのステータスをIn Progressに変更
- ✅ 各IssueのAssignee情報を確認し、自分にアサインされているものをフィルタリング
- ✅ CLOSEDなIssueは除外（OPENなもののみ対象）

### 自動実行の対象外

以下のIssueは自動的に除外される：

- ✅ クローズ済みのIssue（`--state open` で除外）
- 👤 他のユーザーにアサインされているIssue（Assignee情報で除外）
- 📝 「📝 To Do」ステータス以外のIssue
- 📋 「📋 Backlog」ステータスのIssue

---

## 📚 よく使うコマンド集

### Issue操作

```bash
# Issue一覧取得
gh issue list --limit 100

# 特定ステータスのIssue取得（Project経由）
gh project item-list 1 --owner @me --format json | jq '.items[] | select(.status == "📝 To Do")'

# Issueのステータス更新
gh api graphql -f query="mutation {
  updateProjectV2ItemFieldValue(input: {
    projectId: \"PVT_kwHOANWYrs4BIOm-\"
    itemId: \"<PROJECT_ITEM_ID>\"
    fieldId: \"PVTSSF_lAHOANWYrs4BIOm-zg4wCDo\"
    value: { singleSelectOptionId: \"f36fcf60\" }
  }) {
    projectV2Item { id }
  }
}"
```

### Project操作

```bash
# Project全体の状態確認
gh project view 1 --owner @me

# Project Item一覧（JSON）
gh project item-list 1 --owner @me --format json --limit 200

# ステータス別集計
gh project item-list 1 --owner @me --format json | jq '[.items[] | {number: .content.number, status: .status}] | group_by(.status) | map({status: .[0].status, count: length})'
```

### PR状態確認

```bash
# PR詳細取得
gh pr view <PR番号> --json number,title,state,mergedAt,closedAt,body

# PRリスト取得
gh pr list --state all --limit 10

# 特定IssueのPR検索
gh pr list --search "Closes #209"
```

---

## 🔄 他のルールとの連携

### commit.md との連携

作業完了時：

1. コミット作成
2. PRプッシュ
3. **PRマージ後、プロジェクトステータスを「✅ Done」に更新**
   - `./scripts/github/projects/set-issue-done.sh <issue番号>`を実行
   - 関連するすべてのIssueのステータスを更新

---

## 📚 参考資料

- `.cursor/rules/00-WORKFLOW-CHECKLIST.md` - ワークフロー全体
- `.cursor/rules/03-git-workflow.md` - Git ワークフロー
- `templates/issue-report.md` - Issue報告テンプレート
