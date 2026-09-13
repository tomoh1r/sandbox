# Erlang：2台つながるとちょっと感動するクラスタ体験

外部ライブラリや rebar3 は不要。Erlang 標準の分散機能だけで、別マシンの
プロセスへメッセージを送り、両マシンで同時に計算します。
まず `pong`、次に相手の端末に自分のメッセージが出たら成功です！

## Podman で2コンテナを動かす（1台で試す）

ホストに Erlang をインストールせずに試せます。イメージは **CentOS Stream 9** と
EPEL の Erlang を使います。ホスト OS は Stream 10 でも構いません。
以下は Linux 上の Podman を想定し、すべて同じ一般ユーザーで操作します。
CentOS のホストで Podman がなければ `sudo dnf install -y podman` で導入してください。
この Podman 手順は、リポジトリのルート（`sandbox/`）から移動せずに実行できます。

### イメージをビルドする

リポジトリのルートで実行します。初回はイメージとパッケージを取得するため
インターネット接続が必要です。

```bash
podman build -t localhost/erlang-cluster:stream9 \
  -f erlang-cluster/Containerfile erlang-cluster/
```

最後の `erlang-cluster/` は、ビルドに渡すファイルの基準ディレクトリです。
以降のネットワーク作成・起動・attach・後片付けも、そのままルートから実行できます。
コードを変更した場合は再ビルドし、コンテナを作り直してください。

### ネットワークと共通 cookie を用意する

```bash
podman network create --subnet 10.89.42.0/24 erlang-demo-net
od -An -N24 -tx1 /dev/urandom | tr -d ' \n' | podman secret create erlang-demo-cookie -
```

`10.89.42.0/24` が既存の LAN・VPN・コンテナネットワークと重なる場合は、
未使用のサブネットに変更し、以下の `.11` / `.12` の IP も対応させてください。
同名のネットワークや secret がすでにある場合は、別の名前にするか、以前のデモを
後述の手順で片付けてください。

cookie はイメージやホストの `~/.erlang.cookie` に保存せず、Podman secret で両方に
渡します。コンテナは UID/GID `1000:1000` で動き、起動時に secret の内容を
コンテナ内の `~/.erlang.cookie` に権限 `600` でコピーします。

### 2ノードを起動する

```bash
podman run -dit --name erlang-demo-a --hostname machine-a \
  --network erlang-demo-net --ip 10.89.42.11 \
  --secret erlang-demo-cookie,target=erlang-cookie,uid=1000,gid=1000,mode=0400 \
  localhost/erlang-cluster:stream9 demo1@10.89.42.11

podman run -dit --name erlang-demo-b --hostname machine-b \
  --network erlang-demo-net --ip 10.89.42.12 \
  --secret erlang-demo-cookie,target=erlang-cookie,uid=1000,gid=1000,mode=0400 \
  localhost/erlang-cluster:stream9 demo2@10.89.42.12

podman logs erlang-demo-a -f
podman logs erlang-demo-b -f
```

両方に `[ready]` が出れば準備完了です。`-dit` はバックグラウンドで
対話シェルを維持する指定です。別々のネットワーク名前空間なので、両方とも TCP 9100 を
使えます。通信は同じ Podman ネットワーク内で完結し、ホストへの `-p` による
ポート公開や、下の実マシン用 firewalld 設定は不要です。
通常の分散 Erlang は暗号化されないため、このネットワークには信頼できるコンテナだけを参加させます。

### 相手の端末にメッセージを表示する

端末Aで `podman attach erlang-demo-a`、端末Bで `podman attach erlang-demo-b` を実行し、
必要なら Enter を押して Erlang のプロンプトを表示します。
`podman exec ... erl` ではなく **attach** で起動済みのシェルに接続してください。

A の Erlang シェルで（各式の最後に `.` が必要）：

```erlang
cluster_demo:connect('demo2@10.89.42.12').
cluster_demo:members().
cluster_demo:say("Hello from container A!").
cluster_demo:parallel(12).
```

`pong` が返り、B の端末に次のメッセージが出れば成功です。

```text
[message on 'demo2@10.89.42.12'] 'demo1@10.89.42.11' says: Hello from container A!
```

並列計算は `host => "machine-a"` / `host => "machine-b"` を含む2件の
`square => 144` を返します。B からも返信できます。

```erlang
cluster_demo:say("Hello A, this is container B!").
```

**Ctrl-P、続けて Ctrl-Q** で、コンテナを動かしたまま attach から抜けられます。
切断を試す場合はホストの別端末で `podman stop erlang-demo-b` を実行します。
A の `[node DOWN]` を確認後、`podman start erlang-demo-b` で起動し直し、
A のシェルから再び `cluster_demo:connect('demo2@10.89.42.12').` を実行してください。
再起動直後は準備やネットワークの更新が間に合わず `pang` になることがあります。
`podman logs --tail 10 erlang-demo-b` で今回の起動の `[ready]` を確認し、
少し待ってから再度 `connect/1` を実行してください。
状態やメッセージ履歴は保存されません。

### 後片付け

ホストのシェルで、このデモで作ったリソースだけを削除します。

```bash
podman stop erlang-demo-a erlang-demo-b
podman rm erlang-demo-a erlang-demo-b
podman network rm erlang-demo-net
podman secret rm erlang-demo-cookie
# イメージも不要なら実行
podman rmi localhost/erlang-cluster:stream9
```

イメージ内で既存の自動テストだけを実行する場合は、次のコマンドを使えます。
これは1コンテナ内の2 VM を検証するテストです。

```bash
podman run --rm --entrypoint bash localhost/erlang-cluster:stream9 test/smoke.sh
```

参考：[Podman run](https://docs.podman.io/en/latest/markdown/podman-run.1.html) /
[Podman secret create](https://docs.podman.io/en/latest/markdown/podman-secret-create.1.html)

## 用意するもの

- **CentOS Stream 9 のマシンを2台**（VM でも可）。同じ Erlang/OTP バージョンを使います。
- 両方向に通信できるプライベートネットワークと、sudo できる一般ユーザー。
- マシンごとに SSH などで開いた端末1つずつ。

この手順では次の例を使います。IP は必ず各マシンの実際の IPv4 アドレスに置き換えてください。
NAT 越しではなく、互いの IP に直接到達できる構成を使います。

| マシン | プライベート IP | Erlang ノード名 |
|---|---|---|
| A | `192.168.56.11` | `demo1@192.168.56.11` |
| B | `192.168.56.12` | `demo2@192.168.56.12` |

`名前@IP` は Erlang VM の名前です。Linux のホスト名を変える必要はありません。
このデモは `-name`（長いノード名）に統一し、DNS の設定を省けるよう IP を使います。

> 通常の分散 Erlang 通信は暗号化されません。同じ cookie を持つ接続相手はコードを
> 実行できるので、信頼できるマシンだけの閉じたネットワークで試してください。
> インターネットにポートを公開しないでください。

CentOS Linux 7/8 はサポート終了のため対象外です。Stream 10 のパッケージ提供状況も
この手順の対象には含めていません。

## 1. Erlang を入れる（A・B 両方）

```bash
cat /etc/centos-release
sudo dnf install -y dnf-plugins-core
sudo dnf config-manager --set-enabled crb
sudo dnf install -y epel-release epel-next-release
sudo dnf install -y erlang-erts erlang-compiler

erl -noshell -eval 'io:format("OTP ~s~n", [erlang:system_info(otp_release)]), halt().'
command -v erlc
```

EPEL の Erlang ランタイムとコンパイラを使います。必要な kernel / stdlib などは
依存パッケージとして導入されます。両マシンで同じリポジトリ・バージョンを使ってください。

## 2. コードを両方に置く

この `erlang-cluster` ディレクトリ全体を A・B の `~/erlang-cluster` に置きます。
例えば A に置いた後、A から B へ（`YOUR_USER` は B の SSH ユーザー名に変更）：

```bash
scp -r ~/erlang-cluster YOUR_USER@192.168.56.12:~/
```

リポジトリ全体を clone 済みなら、その中の `erlang-cluster` ディレクトリを使っても構いません。
以下の `cd ~/erlang-cluster` をそのパスに読み替えてください。
両方に同じ `.erl` ソースが必要です。ノードを接続するだけではコードは配布されません。

## 3. 共通の cookie を設定する（A・B 両方）

cookie はノード同士の認証に使う共有秘密です。**両マシンに同じ値**を設定します。
A で次を実行し、出てきたランダムな値を控えます。

```bash
od -An -N24 -tx1 /dev/urandom | tr -d ' \n'; echo
```

A・B それぞれ、Erlang を起動する一般ユーザーで実行します。入力は端末に表示されません。
既存の `~/.erlang.cookie` がある場合は、他の Erlang アプリと共有していないか確認し、
必要なら先にバックアップしてください。

```bash
read -rsp '両マシン共通の cookie を入力: ' DEMO_COOKIE; echo
if [ -n "$DEMO_COOKIE" ]; then
  (umask 077; printf '%s\n' "$DEMO_COOKIE" > ~/.erlang.cookie)
  chmod 600 ~/.erlang.cookie
fi
unset DEMO_COOKIE
```

cookie を Git に追加しないでください。以降は `sudo erl` ではなく一般ユーザーで起動します。

## 4. 通信を許可する（A・B 両方）

必要な TCP ポートは **4369（epmd：接続先ポートを案内）** と
**9100（このデモの Erlang ノード通信）** です。起動スクリプトで 9100 に固定します。

firewalld を使っている場合、相手の IP だけを許可します。
まず `sudo firewall-cmd --get-active-zones` でプライベート通信のインターフェースが属する
ゾーンを調べます。以下の `public` はそのゾーン名に変更してください。

A では：

```bash
PEER_IP=192.168.56.12
ZONE=public
```

B では：

```bash
PEER_IP=192.168.56.11
ZONE=public
```

続けて両方で：

```bash
for PORT in 4369 9100; do
  sudo firewall-cmd --permanent --zone="$ZONE" \
    --add-rich-rule="rule family=ipv4 source address=$PEER_IP/32 port port=$PORT protocol=tcp accept"
done
sudo firewall-cmd --reload
```

firewalld が動いていなければ、利用中のファイアウォールで同じ条件を設定します。
クラウドのセキュリティグループや VM のネットワーク設定も、両方向でこの2ポートを
通してください。SELinux やファイアウォール全体を無効化する必要はありません。

## 5. ノードを起動する

A の端末で：

```bash
cd ~/erlang-cluster
bash scripts/start.sh demo1@192.168.56.11
```

B の端末で：

```bash
cd ~/erlang-cluster
bash scripts/start.sh demo2@192.168.56.12
```

起動時に自動でコンパイルされ、`[ready] 'demo1@192.168.56.11'` などと
Erlang シェルが表示されます。**これ以降は Erlang シェルに入力します。
各式の最後の `.` を忘れずに。**

## 6. つなぐ → 相手に届く！

A の Erlang シェルで：

```erlang
cluster_demo:connect('demo2@192.168.56.12').
```

`pong` が返り、両方の端末に `[node UP]` が出れば接続成功です。
`pang` は失敗なので、後述のトラブルシューティングを確認してください。

```erlang
node().
nodes().
cluster_demo:members().
cluster_demo:say("Hello from machine A!").
```

`node()` は自分、`nodes()` は接続相手、`members()` は自分を含む全ノードです。
**B の端末にも**次のようなメッセージが表示されます。

```text
[message on 'demo2@192.168.56.12'] 'demo1@192.168.56.11' says: Hello from machine A!
```

A には各ノードからの受領応答が返ります。

```erlang
[{'demo1@192.168.56.11',ok},{'demo2@192.168.56.12',ok}]
```

B からも返信できます：

```erlang
cluster_demo:say("Hello A, this is B!").
```

## 7. 両マシンを同時に働かせる

A で：

```erlang
cluster_demo:parallel(12).
```

出力例（PID・ホスト名・時間は環境で変わります）：

```erlang
#{elapsed_ms => 1002,
  replies =>
      [#{node => 'demo1@192.168.56.11', host => "machine-a",
         pid => <0.100.0>, square => 144},
       #{node => 'demo2@192.168.56.12', host => "machine-b",
         pid => <9000.100.0>, square => 144}],
  unreachable => []}
```

`rpc:multicall/5` で全ノードに同時に仕事を依頼しています。各ノードは1秒待ってから
二乗を計算し、**実際に実行したノード名・OS ホスト名・PID** を返します。
2台でそれぞれ1秒待っても、全体はおよそ1秒です。待機は並列性を体感するための演出で、
計算性能のベンチマークではありません。

## 8. B を止める → A は動き続ける → 再参加

B の Erlang シェルで：

```erlang
init:stop().
```

A に `[node DOWN] 'demo2@192.168.56.12'` と出たら、A で：

```erlang
cluster_demo:members().
cluster_demo:parallel(7).
```

A だけが表示され、計算結果も A の `square => 49` だけになります。
B を手順5のコマンドで起動し直し、A からもう一度：

```erlang
cluster_demo:connect('demo2@192.168.56.12').
cluster_demo:parallel(7).
```

また2台分の結果が返ります。これはノードの接続・監視のデモです。自動再接続、
データ複製、失敗した仕事の再実行は実装していません。
計算中にノードが落ちると `unreachable` にそのノードが入り、リモート実行のエラーは
`replies` の `{badrpc, ...}` に現れることがあります。

3台目も同じセットアップで `demo3@そのIP` を起動し、既存ノードに `connect/1` します。
全マシン間の通信を許可し、cookie とコードをそろえると、通常の可視ノードは相互接続されます。

## 終了と後片付け

各 Erlang シェルで `init:stop().` を実行します。
追加した firewalld ルールが不要になったら、手順4と同じ `PEER_IP` / `ZONE` を設定して：

```bash
for PORT in 4369 9100; do
  sudo firewall-cmd --permanent --zone="$ZONE" \
    --remove-rich-rule="rule family=ipv4 source address=$PEER_IP/32 port port=$PORT protocol=tcp accept"
done
sudo firewall-cmd --reload
```

`epmd` は VM 終了後も残ることがあります。このユーザーの他の Erlang ノードが動いて
いない場合は `epmd -kill` で終了できます。cookie は他アプリが使っていない場合のみ
削除するか、バックアップした元の内容に戻してください。

## つながらないとき

| 症状 | 確認すること |
|---|---|
| `pang` | B が起動中か、IP・ノード名のつづりが正しいか、両方向の TCP 4369 / 9100 が通るか |
| `Invalid challenge reply` / cookie 関連エラー | 両マシンの起動ユーザーの cookie が同じか、権限が `600` か。変更後はノードを再起動 |
| `eaddrinuse` / 名前が使用中 | 同じ名前の VM や、9100 を使う別プロセスがいないか |
| `nodistribution` / 名前関連エラー | 自分の実 IP で `-name` 起動しているか。`-sname` と混在させない |
| `{badrpc, undef}` | 両マシンに同じソースがあるか。起動スクリプトから再起動してコンパイル |
| `say/1` が `{error, ...}` を返す | 接続相手で `cluster_demo:start().` が動いているか |
| `No match for argument: erlang-...` | Stream **9** か、EPEL / EPEL Next / CRB が有効かを `dnf repolist` で確認 |

Linux 側の確認コマンド（別の SSH 端末で実行）：

```bash
ip -4 addr
epmd -names
ss -ltn | rg ':4369|:9100'  # rg がなければ grep -E ':4369|:9100'
stat -c '%a %U' ~/.erlang.cookie
```

`epmd -names` に `name demo1 at port 9100` などが出るのが正常です。
ネットワーク断では `[node DOWN]` の検出に時間がかかる場合があります。

## 1台で予習する場合

同じマシンの端末2つで、cookie 設定後にそれぞれ実行します。
1台に VM を2つ立てるので、ノード名と通信ポートを変えます。

```bash
# 端末1
bash scripts/start.sh demo1@127.0.0.1 9100
# 端末2
bash scripts/start.sh demo2@127.0.0.1 9101
```

端末1の Erlang シェルで `cluster_demo:connect('demo2@127.0.0.1').` とします。
ループバック上の体験で、複数マシン間のネットワーク疎通を検証するものではありません。

## コードと自動テスト

- `src/cluster_demo.erl`：メッセージ受信、接続監視、並列 RPC。
- `scripts/start.sh`：コンパイル・固定ポートで起動。
- `Containerfile` / `.containerignore`：CentOS Stream 9 イメージのビルド定義と送信対象。
- `scripts/container-entrypoint.sh`：Podman secret から cookie を設定して起動。
- `test/smoke.sh`：2つの Erlang VM で通信・計算・切断・再接続を検証（OTP 25 以上）。

```bash
bash test/smoke.sh
```

成功すると `PASS: two nodes, messages, parallel work, disconnect, reconnect` と出ます。
テストは一時的な cookie と `127.0.0.1` を使い、既存の cookie ファイルを変更しません。

検証済み環境：CentOS Stream 10 のホスト上の Podman、CentOS Stream 9 コンテナ、
Erlang/OTP 26.2.5。イメージのビルド、上記自動テスト、2コンテナ間の双方向メッセージ、
並列計算、停止・再起動後の再接続を確認しました。実マシン2台の通信は未検証です。

## 参考資料

- [Erlang 公式：Distributed Erlang](https://www.erlang.org/docs/26/reference_manual/distributed.html)
- [Erlang 公式：Distribution Protocol（epmd / TCP 4369）](https://www.erlang.org/docs/26/apps/erts/erl_dist_protocol.html)
- [Fedora EPEL 導入手順](https://docs.fedoraproject.org/en-US/epel/getting-started/)
- [Fedora の Erlang パッケージ（EPEL 9）](https://packages.fedoraproject.org/pkgs/erlang/erlang/)
- [CentOS Linux のサポート終了について](https://www.centos.org/centos-linux/)
