# Sandbox Pulse

Python 3.11+ の `asyncio.TaskGroup` と `asyncio.to_thread` を使う、依存パッケージなしのフォルダー健康診断です。

```bash
cd /home/tomo/sandbox
python3 pulse.py
```

実行後、`outputs/pulse.html` をブラウザーで開くと、ファイル数・合計容量・種類・大きいファイル・短縮 SHA-256 を確認できます。別の場所を調べる場合は次のように指定します。

```bash
python3 python-pulse/pulse.py python-pulse/ --out python-pulse/outputs/
```

除外対象は `.git`、`.venv`、`__pycache__`、`node_modules` です。
