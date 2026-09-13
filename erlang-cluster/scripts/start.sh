#!/usr/bin/env bash
set -euo pipefail
# どのディレクトリから実行しても、プロジェクト直下を基準にする。
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."

# ノード名（名前@IPv4）と、省略可能な通信ポートを確認する。
if [[ $# -lt 1 || $# -gt 2 || ! $1 =~ ^[a-zA-Z][a-zA-Z0-9_]*@[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Usage: bash scripts/start.sh demo1@192.168.56.11 [distribution-port]" >&2
    exit 1
fi
port=${2:-9100}
if [[ ! $port =~ ^[0-9]{4,5}$ ]] || (( 10#$port < 1024 || 10#$port > 65535 )); then
    echo "Port must be between 1024 and 65535." >&2
    exit 1
fi
port=$((10#$port))
# 実行環境と共有 cookie が準備されているか確認する。
for tool in erl erlc; do
    command -v "$tool" >/dev/null || { echo "Install Erlang first (see README.md)." >&2; exit 1; }
done
if [[ ! -s $HOME/.erlang.cookie ]]; then
    echo "Create a shared ~/.erlang.cookie first (see README.md)." >&2
    exit 1
fi
# ソースをコンパイルし、通信ポートを固定して Erlang シェルを起動する。
mkdir -p ebin
erlc -Werror -o ebin src/cluster_demo.erl
exec erl -name "$1" -pa ebin \
    -kernel inet_dist_listen_min "$port" inet_dist_listen_max "$port" \
    -s cluster_demo start
