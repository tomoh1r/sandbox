#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
# 本体とテストをコンパイルする。警告もエラーとして扱う。
mkdir -p ebin
erlc -Werror -o ebin src/*.erl test/*.erl
# 一時 cookie でテストを実行し、完了後に VM を終了する。
erl +S 2:2 -noshell -name smoke@127.0.0.1 \
    -setcookie "smoke_${RANDOM}_$$" -pa ebin \
    -s cluster_demo start -s cluster_demo_smoke run -s init stop
