# htmx + Flask Quick Win

タスクを追加・完了／未完了・削除できる、ローカル利用向けの MVP です。

Flask が HTML を返し、htmx がタスク領域だけを更新します。
SQLite に保存するため再起動後もデータが残ります。

## 起動

Python 3.10 以上を使用してください。

```bash
cd /home/tomo/sandbox/htmx-flask-quickwin
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask --app app run --debug
```

http://127.0.0.1:5000 を開きます。
DB は初回起動時に `instance/tasks.sqlite3` に自動作成します。

htmx はバージョン固定の CDN から読み込むため、部分更新にはインターネット接続が必要です。
読み込めない場合も通常のフォーム送信で操作できます。

## 構成

```text
app.py                  アプリ生成・ルート・SQLite・CSRF 検証
templates/index.html    ページ全体
templates/partials/     htmx で差し替える HTML
static/                 CSS・通信エラー表示
tests/                  基本動作のテスト
requirements.txt        Python 依存関係
instance/               実行時のデータ（Git 管理対象外）
```

## テスト

```bash
python -m unittest discover -s tests -v
```

認証やユーザー別データ分離は未実装です。
ローカルの個人用として利用してください。

`SECRET_KEY` 環境変数を設定すると再起動してもセッション署名キーを維持できます。
未設定の場合は起動ごとに生成します。

参考:
[Flask](https://flask.palletsprojects.com/en/stable/quickstart/) /
[htmx](https://htmx.org/docs/)
