#!/usr/bin/env bash
set -euo pipefail

# 共有秘密はイメージに含めず、Podman secret から起動時に読み込む。
cookie_file=/run/secrets/erlang-cookie
if [[ ! -s $cookie_file || ! -r $cookie_file ]]; then
    echo "Mount the erlang-cookie secret (see README.md)." >&2
    exit 1
fi
umask 077
cat "$cookie_file" > "$HOME/.erlang.cookie"
chmod 600 "$HOME/.erlang.cookie"

# 既存の起動処理を利用し、Erlang VM をコンテナの主プロセスにする。
exec bash /app/scripts/start.sh "$@"
