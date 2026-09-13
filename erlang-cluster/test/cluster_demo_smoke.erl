-module(cluster_demo_smoke).
-export([run/0]).

run() ->
    %% 同じマシン上に、同じ cookie を持つテスト用の別 VM を起動する。
    Options = #{name => worker, host => "127.0.0.1", longnames => true,
                connection => standard_io,
                args => ["+S", "2:2", "-pa", filename:absname("ebin"),
                         "-setcookie", atom_to_list(erlang:get_cookie())]},
    ok = net_kernel:monitor_nodes(true),
    {ok, Peer, Remote} = peer:start_link(Options),
    try
        %% 接続通知、ノード一覧、メッセージの受領応答を確認する。
        {ok, _} = peer:call(Peer, cluster_demo, start, []),
        pong = cluster_demo:connect(Remote),
        receive {nodeup, Remote} -> ok after 5000 -> error(no_nodeup) end,
        Expected = lists:sort([node(), Remote]),
        Expected = cluster_demo:members(),
        [{_, ok}, {_, ok}] = cluster_demo:say("hello from smoke test"),
        %% 両ノードから 12 の二乗が返り、実行先も異なることを確認する。
        #{replies := Replies, unreachable := []} = cluster_demo:parallel(12),
        2 = length(Replies),
        Expected = lists:sort([N || #{node := N, square := 144} <- Replies]),
        %% 相手を停止し、切断検出後も自分だけで計算できることを確認する。
        peer:stop(Peer),
        receive {nodedown, Remote} -> ok after 5000 -> error(no_nodedown) end,
        [Local] = cluster_demo:members(),
        Local = node(),
        pang = cluster_demo:connect(Remote),
        #{replies := [#{node := Local, square := 9}], unreachable := []} =
            cluster_demo:parallel(3),
        %% 同じ名前で再起動し、再接続とメッセージ送信を確認する。
        {ok, Peer2, Remote} = peer:start_link(Options),
        try
            {ok, _} = peer:call(Peer2, cluster_demo, start, []),
            pong = cluster_demo:connect(Remote),
            Expected = cluster_demo:members(),
            [{_, ok}, {_, ok}] = cluster_demo:say("welcome back")
        after peer:stop(Peer2)
        end,
        io:format("PASS: two nodes, messages, parallel work, disconnect, reconnect~n")
    after
        %% テスト途中で失敗した場合も、起動した VM を終了する。
        catch peer:stop(Peer)
    end.
