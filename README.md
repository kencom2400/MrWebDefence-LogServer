# MrWebDefence-LogServer

このリポジトリは、MrWebDefenceシステムのログ収集・管理サーバーです。

## 📋 現在のステータス

**Phase**: 設計フェーズ

現在、Task 8.1（ログ収集機能実装）の設計書を作成中です。

## 📖 ドキュメント

- [設計書: Task 8.1 ログ収集機能](docs/design/MWD-53-log-collection.md)

## 🎯 プロジェクト概要

WAFエンジンから転送されるログを受信し、パース・正規化・保存する機能を提供します。

### 主な機能（予定）

- **ログ受信**: HTTP/TCP経由でのログ受信
- **ログパース**: JSON、Syslog、プレーンテキスト形式に対応
- **正規化**: 共通フォーマットへの変換
- **タイムスタンプ補正**: タイムゾーン変換、欠損補完
- **バッファリング**: メモリ上での一時保持と効率的な書き込み
- **ストレージ**: ファイルベースの永続化

### システムアーキテクチャ（予定）

```
WAF Engine → Fluent Bit → Log Server → Storage
```

詳細は[設計書](docs/design/MWD-53-log-collection.md)を参照してください。

## ライセンス

Proprietary
