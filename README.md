# MrWebDefence-LogServer

このリポジトリは、MrWebDefenceシステムのログ収集・管理サーバーです。

## 📋 現在のステータス

**Phase**: 設計フェーズ

現在、Task 8.1（ログ収集機能実装）の設計書を作成中です。

## 📖 ドキュメント

- [設計書: Task 8.1 ログ収集機能](docs/design/MWD-53-log-collection.md)

## 🎯 プロジェクト概要

MrWebDefence-Engine（WAFエンジン）から転送されるログを受信し、正規化・保存する機能を提供します。

### 主な機能（予定）

- **ログ受信**: HTTP経由でのログ受信（Engine Fluentdから）
- **ログパース**: Engine側で整形されたJSON形式ログの検証
- **正規化**: LogServer内部データモデルへの変換
- **タイムスタンプ補正**: タイムゾーン変換、欠損補完、未来時刻補正
- **バッファリング**: メモリ上での一時保持と効率的な非同期書き込み
- **ストレージ**: ファイルベースの永続化（顧客別・FQDN別・時間別）

### システムアーキテクチャ（予定）

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

## 🔗 関連リポジトリ

- [MrWebDefence-Engine](https://github.com/kencom2400/MrWebDefence-Engine) - WAFエンジン（ログ送信側）
  - [MWD-40: ログ転送機能実装 実装設計書](https://github.com/kencom2400/MrWebDefence-Engine/blob/main/docs/design/MWD-40-implementation-plan.md)

## ライセンス

Proprietary
