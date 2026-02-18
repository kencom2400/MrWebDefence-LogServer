# MrWebDefence-LogServer

このリポジトリは、MrWebDefenceシステムのログ収集・管理サーバーです。

## 📋 現在のステータス

**Phase**: 設計フェーズ（Fluentdベース）

Task 8.1（ログ収集機能実装）をFluentdベースで設計中です。

## 📖 ドキュメント

- [設計書: Task 8.1 ログ収集機能（Fluentdベース）](docs/design/MWD-53-log-collection.md)

## 🎯 プロジェクト概要

MrWebDefence-Engine（WAFエンジン）から転送されるログをFluentdで受信し、正規化・保存する機能を提供します。

### 主な機能

- **ログ受信**: Fluentd HTTP Input Plugin（Engine Fluentdから）
- **ログ正規化**: Record Transformer Filter
- **バッファリング**: Fluentdの組み込みバッファ機能
- **ストレージ**: File Output Plugin（顧客別・FQDN別・時間別）
- **セキュリティ**: TLS暗号化（mTLS）、共有シークレット認証

### システムアーキテクチャ

```
[MrWebDefence-Engine]
WAF (Nginx + OpenAppSec)
  ↓ ログファイル（共有ボリューム）
Fluentd (Engine)
  ↓ HTTP/JSON + TLS暗号化 + 認証
[MrWebDefence-LogServer]
Fluentd (LogServer)
  ↓ Filter (正規化・メタデータ追加)
  ↓ Buffer (メモリ/ディスク)
File Storage (顧客別・FQDN別・時間別)
```

### 技術選定の理由

**Fluentdを選択した理由**:
- **シンプル**: 設定ファイルのみで実装可能、車輪の再発明を回避
- **実績**: 大規模本番環境での豊富な実績、枯れた技術
- **パフォーマンス**: C実装による高速・低メモリフットプリント
- **拡張性**: プラグインエコシステムで将来の機能追加が容易
- **統一性**: Engine側もFluentdなので設定の一貫性が高い
- **運用**: 既存のFluentd運用ノウハウをそのまま活用可能

詳細は[設計書](docs/design/MWD-53-log-collection.md)を参照してください。

## 🔗 関連リポジトリ

- [MrWebDefence-Engine](https://github.com/kencom2400/MrWebDefence-Engine) - WAFエンジン（ログ送信側）
  - [MWD-40: ログ転送機能実装 実装設計書](https://github.com/kencom2400/MrWebDefence-Engine/blob/main/docs/design/MWD-40-implementation-plan.md)

## ライセンス

Proprietary
