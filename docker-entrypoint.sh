#!/bin/bash
# Fluentd entrypoint script
# ログディレクトリの作成と権限設定

set -e

# ログディレクトリが存在しない場合は作成
mkdir -p /var/log/mrwebdefence/logs
mkdir -p /var/log/fluentd/buffer
mkdir -p /var/log/fluentd/invalid
mkdir -p /var/log/fluentd/unmatched

# 権限設定（ボリュームマウントで上書きされた場合に備えて）
chown -R fluent:fluent /var/log/mrwebdefence 2>/dev/null || true
chown -R fluent:fluent /var/log/fluentd 2>/dev/null || true

# Fluentdをfluentユーザーで起動
exec gosu fluent fluentd -c /fluentd/etc/fluent.conf "$@"
