-module(cluster_demo).
-behaviour(gen_server).

-export([start/0, connect/1, members/0, say/1, parallel/1, work/1]).
-export([init/1, handle_call/3, handle_cast/2, handle_info/2]).

%% このノードに名前付きの受信プロセスを起動。起動済みならその PID を返す。
start() ->
    case gen_server:start({local, ?MODULE}, ?MODULE, [], []) of
        {ok, Pid} -> {ok, Pid};
        {error, {already_started, Pid}} -> {ok, Pid}
    end.

%% 相手に接続し、成功なら pong、失敗なら pang を返す。
connect(Node) -> net_adm:ping(Node).
%% 自分と接続中のノードを、重複のない一覧にする。
members() -> lists:usort([node() | nodes()]).

%% 全ノードへメッセージを送り、各受信プロセスからの応答を待つ。
say(Text) ->
    [{N, deliver(N, Text)} || N <- members()].

%% 相手の名前付きプロセスを呼び出す。切断やタイムアウトはエラーとして返す。
deliver(Node, Text) ->
    try gen_server:call({?MODULE, Node}, {say, node(), Text}, 3000)
    catch exit:Reason -> {error, Reason}
    end.

%% 自分を含む全ノードで work/1 を並列実行し、結果と所要時間をまとめる。
parallel(Number) when is_integer(Number) ->
    Targets = members(),
    {Elapsed, {Replies, BadNodes}} = timer:tc(
        fun() -> rpc:multicall(Targets, ?MODULE, work, [Number], 5000) end),
    #{elapsed_ms => Elapsed div 1000,
      replies => Replies, unreachable => BadNodes}.

work(Number) when is_integer(Number) ->
    %% 並列実行を体感するため1秒待つ。性能測定用の処理ではない。
    timer:sleep(1000),
    {ok, Hostname} = inet:gethostname(),
    %% 計算結果に実行先の情報を添え、別マシンで動いたことを確認できるようにする。
    #{node => node(), host => Hostname, pid => self(), square => Number * Number}.

%% ノードの接続・切断通知を受け取る。このデモでは状態を保持しない。
init([]) ->
    ok = net_kernel:monitor_nodes(true),
    io:format("[ready] ~p~n", [node()]),
    {ok, undefined}.

%% 受信したメッセージをこのノードの端末に表示し、送信元へ ok を返す。
handle_call({say, From, Text}, _Caller, State) ->
    io:format("[message on ~p] ~p says: ~ts~n", [node(), From, Text]),
    {reply, ok, State};
handle_call(_Request, _Caller, State) ->
    {reply, {error, unknown_request}, State}.

%% 応答不要のメッセージは、このデモでは使わない。
handle_cast(_Message, State) -> {noreply, State}.

%% 接続・切断を端末に表示する。その他の通知は無視する。
handle_info({nodeup, Node}, State) ->
    io:format("[node UP] ~p~n", [Node]),
    {noreply, State};
handle_info({nodedown, Node}, State) ->
    io:format("[node DOWN] ~p~n", [Node]),
    {noreply, State};
handle_info(_Message, State) -> {noreply, State}.
