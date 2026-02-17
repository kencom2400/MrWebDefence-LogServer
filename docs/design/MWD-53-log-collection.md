# Task 8.1: ログ収集機能実装 - 設計書

**Issue**: MWD-53  
**作成日**: 2026-02-17  
**更新日**: 2026-02-17 (再設計)  
**ステータス**: Design Phase - Planning

---

## 📋 目次

1. [概要](#概要)
2. [参照設計書](#参照設計書)
3. [システムアーキテクチャ](#システムアーキテクチャ)
4. [実装計画](#実装計画)
5. [テスト計画](#テスト計画)

---

## 概要

### なぜやるか

WAFエンジン（MrWebDefence-Engine）から転送されるログを受信し、保存する機能が必要。

### 何をやるか

（TBD: 再設計中）

### 受け入れ条件

- [ ] TBD

---

## 参照設計書

本設計は、MrWebDefence-Engineのログ転送設計と連携します：

- **[MWD-40: Fluentd設定ファイルのモジュール化計画](https://github.com/kencom2400/MrWebDefence-Engine/blob/main/docs/design/MWD-40-fluentd-modularization-plan.md)**
  - Engine側のFluentd設定構造
  - label/includeを使ったモジュール化方針
  
- **[MWD-40: ログ転送機能実装 実装設計書](https://github.com/kencom2400/MrWebDefence-Engine/blob/main/docs/design/MWD-40-implementation-plan.md)**
  - ログ形式、タグ設計
  - メタデータ構造（customer_name、fqdn、year/month/day/hour等）
  - 転送エンドポイント仕様
  
- **[MWD-40: ログ連携方法比較検討](https://github.com/kencom2400/MrWebDefence-Engine/blob/main/docs/design/MWD-40-log-integration-analysis.md)**
  - 共有ボリューム方式 vs ログドライバ方式
  - 推奨方式: 共有ボリューム方式（デフォルト）

---

## システムアーキテクチャ

（TBD: 再設計中）

---

## 実装計画

（TBD: 再設計中）

---

## テスト計画

（TBD: 再設計中）
