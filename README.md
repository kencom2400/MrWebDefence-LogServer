# MrWebDefence-LogServer

このリポジトリは、MrWebDefenceシステムのログ収集・管理サーバーです。

## 📋 現在のステータス

**Phase**: 実装フェーズ

Task 8.1（ログ収集機能実装）の初期実装が完了しました。

## 📖 ドキュメント

- [設計書: Task 8.1 ログ収集機能](docs/design/MWD-53-log-collection.md)

## 🎯 プロジェクト概要

MrWebDefence-Engine（WAFエンジン）から転送されるログを受信し、正規化・保存する機能を提供します。

### 主な機能

- **ログ受信**: HTTP経由でのログ受信（Engine Fluentdから）✅
- **ログパース**: Engine側で整形されたJSON形式ログの検証（DoS対策付き）✅
- **正規化**: LogServer内部データモデルへの変換 ✅
- **タイムスタンプ補正**: タイムゾーン変換、欠損補完、未来時刻補正 ✅
- **バッファリング**: メモリ上での一時保持と効率的な非同期書き込み（バックプレッシャー機能付き）✅
- **ストレージ**: ファイルベースの永続化（顧客別・FQDN別・時間別、Path Traversal対策付き）✅

### システムアーキテクチャ

```
[MrWebDefence-Engine]
WAF (Nginx + OpenAppSec)
  ↓ ログファイル（共有ボリューム）
Fluentd
  ↓ HTTP/JSON
[MrWebDefence-LogServer]
Log Receiver (FastAPI)
  ↓
Parser → Normalizer → Time Corrector → Buffer
  ↓ 非同期書き込み
File Storage
```

詳細は[設計書](docs/design/MWD-53-log-collection.md)を参照してください。

## 🚀 セットアップ

### 必要要件

- Python 3.12+
- Poetry（パッケージ管理）

### インストール

```bash
# 依存関係のインストール
poetry install

# 開発環境用の依存関係も含める場合
poetry install --with dev
```

### 設定

設定ファイルをコピーしてカスタマイズ:

```bash
cp config/server.yaml.example config/server.local.yaml
# server.local.yaml を環境に合わせて編集
```

### 起動

```bash
# サーバーを起動
poetry run python -m src.main

# または
poetry run uvicorn src.server.api:app --host 0.0.0.0 --port 8080
```

## 🧪 テスト

### ユニットテストの実行

```bash
# すべてのユニットテストを実行
poetry run pytest tests/unit/ -v

# 特定のテストファイルを実行
poetry run pytest tests/unit/test_parser.py -v

# カバレッジレポート付きで実行
poetry run pytest tests/unit/ --cov=src --cov-report=html
```

### 統合テストの実行

```bash
# 統合テストを実行
poetry run pytest tests/integration/ -v

# すべてのテストを実行
poetry run pytest tests/ -v
```

## 📁 プロジェクト構造

```
MrWebDefence-LogServer/
├── src/                        # ソースコード
│   ├── models.py              # データモデル（LogEntry、エラークラス）
│   ├── parser/                # ログパーサー
│   │   ├── log_parser.py     # 入力検証
│   │   └── normalizer.py     # 正規化
│   ├── corrector/             # 時刻補正
│   │   └── time_corrector.py
│   ├── buffer/                # ログバッファ
│   │   └── log_buffer.py     # バックプレッシャー付きバッファリング
│   ├── storage/               # ストレージ
│   │   └── file_storage.py   # ファイル保存（Path Traversal対策付き）
│   ├── server/                # FastAPIサーバー
│   │   └── api.py            # APIエンドポイント
│   └── main.py                # エントリーポイント
├── tests/                      # テストコード
│   ├── unit/                  # ユニットテスト
│   ├── integration/           # 統合テスト
│   └── fixtures/              # テストフィクスチャ
├── config/                     # 設定ファイル
├── docs/                       # ドキュメント
└── logs/                       # ログ保存先（実行時に作成）
```

## 🔗 関連リポジトリ

- [MrWebDefence-Engine](https://github.com/kencom2400/MrWebDefence-Engine) - WAFエンジン（ログ送信側）
  - [MWD-40: ログ転送機能実装 実装設計書](https://github.com/kencom2400/MrWebDefence-Engine/blob/main/docs/design/MWD-40-implementation-plan.md)

## ライセンス

Proprietary
