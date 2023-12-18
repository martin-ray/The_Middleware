# The_Middleware
A middleware to support on-demand massive-scientific-data-visualization 

# HTTP interface

## header type
1. FirstContact (再初期化も含む)

```
header = {
    'type':'init',
    'offset':BlockOffset,
    'L3Size' : 1000,
    'L4Size': 1000,
    'Policy' :'LRU',
    'FileName' : 'test',
}
```

例えば、L3Sizeが0の時にはL3cacheがoffってことを意味します。

ここにリプレイスメントポリシーを入れるって感じにしたいと思います。キャッシュサイズも決められるようにしたいと思います。
ーー＞ここは直そう

2. BlockRequest
これは、ユーザではなく、プリフェッチャがサーバにリクエストするための関数です。

```
header = {
    'type':'BlockReq',
    'tol':BlockId[0],
    'timestep':BlockId[1],
    'x': BlockId[2],
    'y': BlockId[3],
    'z': BlockId[4]
}
```

3. noCompress
なんだこれ？このシステムに必要か？ああ、実験のためのね。
圧縮せずに全部持ってくる感じです！！作ったな。

```
header = {
    'type':'noCompress',
    'timestep':BlockId[1],
    'x': BlockId[2],
    'y': BlockId[3],
    'z': BlockId[4]
}
```

4. userPoint
これは、L1とL2でヒットしたとき、データをサーバにリクエストすることはないけど、ユーザの位置を知らせる必要があるってことで、その関数です。
```
header = {
    'type':'userPoint',
    'timestep':BlockId[1],
    'x': BlockId[2],
    'y': BlockId[3],
    'z': BlockId[4]
}
```

5. getStats
ユーザのリクエストシーケンスが0になった後に
サーバ側でのキャッシュヒットがどうだったかをリクエストするためのやつです。

```
header = {
    'type':'getStats'
}
```

6. BlockReqUsr
これは、ユーザがリクエストしたってことです。

header = {
    'type':'BlockReqUsr',
    'tol':BlockId[0],
    'timestep':BlockId[1],
    'x': BlockId[2],
    'y': BlockId[3],
    'z': BlockId[4]
}

## body
compressed array

# 対戦相手と提案手法の亜種一覧
- [ ] HDF5とTileDBどっちも
- [ ] multipleGPU/singleGPU
- [ ] Pure TileDB
- [ ] FP16
- [ ] FP8
- [ ] traditional approach (つまり、ftpとかgridftpで必要なデータを交換してから読み出すやつね。これも評価出来たらめっちゃいいなーって思っています！)

# 評価指標
1. 1リクエストに対する遅延。これは、上の対戦相手全部で試せます。FP16とFP8も行けるんで。
2. n個のリクエストに対する平均遅延。分散やほかの指標も入れる。
3. psnrも評価に入れた方がいいかもしれない。入れようか

# TODO

## 下のTODOを優先度順に並び変えて、今日のTODO
- [ ] 置換がうまくいっているか、目視テスト
- [ ] HDF5 -> TileDBに変更。これでミドルウェア単体の性能を評価できる。
- [ ] TileDBフォーマットでデータを流し込む
- [ ] リクエストとレスポンスにそれぞれの処理時間をのっける。


## overall
- [ ] TileDBフォーマットでデータを流し込む
- [ ] multiGPUを使えるシステムを構築！んで、クライアントからGPU数を設定できるようにサーバを改造。これができれば、評価げーに持っていける。
- [ ] リクエストとレスポンスにそれぞれの処理時間をのっけた評価をしたい！
- [ ] L3プリフェッチャはL4プリフェッチャに読み出しをお願いする感じにしたいんですけど。どうですか？？絶対にそっちの方がいいと思います。そうしましょう。L1プリフェッチャもL2プリフェッチャにお願いする感じにしましょう。なかったら。slicerがクライアント側のnet_interfaceと同じ役割を担っている。なので、L3,L4のreadRequestに対しては、Slicerが一挙に担う感じのアーキテクチャを一回試してみたいのですが、どうでしょう！うん。グローバルスペースで生成して、それを複数スレッドで共有する感じにしたいです。
- [ ] L1 / L2がOnになっているとき、一発目の通信がミスってしまうのをどうにかして直したいのです！
ここまでを来週の水曜日までに終わらせたいのです！来週の水曜日までに全部の評価を持っていきたいのです。。。！
- [ ] そして論文を書きたいのです。やっぱり一本、ちゃんとしたところに通したい！　(last)

## client
- [ ] L1プリえっちゃは、L2を見てなかったら、もうあきらめましょう。そういう設定にした方がいいです。
- [ ] 連続リクエストとランダムのミックスが対話的解析のリクエストとして妥当性があるのかどうか？そこを示す論文を探さないといけない。
- [ ] 初期コンタクトでサーバからデータの範囲を受信。つまり、(t,x,y,z)ね。

## server
- [ ] HDF5 -> TileDBに変更。これでミドルウェア単体の性能を評価できる。
- [ ] ユーザの動きを常に把握しながら、そのポイントを中心にプリフェッチをするプログラムを書いてください。
--> 現在、ユーザの位置を通知するインターフェースは作った。あとは、中心を知らせたときに、中心の半径に入っていないやつらを抜きつつ、半径以内にいるのにキャッシュには含まれていないやつらをプリフェッチするプログラムを書いてください。よろしくお願いします。どうやってやるか？だけど、ユーザの位置は常に各レイヤーのプリフェッチャに通知されるようにしてください。
で、そのブロックとキャッシュに入っているブロックとの位置を計算します。O(n)ですね。で、radisu以上だったら抜いてください。(積極的追い出し/消極的追い出しかはあとで考える)。これはevictメソッドで実装します。
それだけではなく、プリフェッチしに行くコンポーネントも更新する必要があります。
この二つをいかに効率よくやるかが、システムソフトなので、全体の性能に影響してきます。
アルゴリズムとデータ構造のお話だよね。 (最優先)


## 今後の展望
- [ ] wayを追加？どうやって？
- [ ] onion-cache。exclusive cacheにした方がメモリ効率は良くなるよねって話。まあ、時間もないだろうし、厳しいんじゃない？
今後の展望ってことで。
- [ ] c++で書き直す。やっぱシステムソフトなので、c/c++の方がぽい。通信部分も一回一回コネクションを張るやつではなく、
javidexさんのあの自作プロトコルがいいと思う。
- [ ] やはりHTTPだとオーバヘッドが大きい。というのも、一回一回コネクションを張らないといけないから。これのせいで、セッションも管理しないといけない。pythonでできるかわからないけど、通信部分も自分で書いた方がいいかもしれない。

## Done Things
## overall
- [x] シンギュラリティーコンテナを作る。たのむ。動いてくれ。clientはsharkとかで動かそう。って話だ。
ー－＞解決
- [x] バグの個所を先生に見てもらう-->解決。

- [x] 一回、評価をしたい。マジで。これが終わった後にキャッシュのヒット率に関してはやりたいと思う。
csvは入っている、のでできる。

## client
- [x] リクエストを連続的に送信
- [x] 統計的に提案手法有意義であることを示すために、様々な解析パターンをどうにか用意しないといけない。どうすればいいのだろうか？--> 連続リクエストとランダムのミックスを使うしかないと思う。
- 現状、クライアントのAPIにリクエストするよりも、それをすっ飛ばして直接サーバにリクエストした方が早く終わる、という結果が出ています。つまり、クライアント側でバグが起こっていますと。どこで起こっているのか、解析しないといけません。そのために、pythonのプロファイラを使いたいと思います。
ー－＞これ、ちゃんといい結果が出るようになったので気にしなくていいです。

```
python -m cProfile -o main.prof my_script.py
```
このように実行することでプロファイルできますと。
さらに、line_profileっていうのもあるから、自分で調べてみて。

## server
- [x] 各キャッシュのサイズをクライアント側から設定できるように
- [x] 各キャッシュのOn/Offをクライアント側からできるように
- [x] slicerがインデックス以上を読み込まないように注意。最初にスライサーを起動して各次元を読み込んできてもらって、それを各コンポーネントに渡す感じがいいと思う。
- [x] バグ：リスタートした後、L3Prefetcherが動かないことがある。これ、どうやって解決する？リスタート自体は、別にシステムに必須ではない。
--> これおそらく、ブロックサイズが大きすぎて、GPUが圧縮できないことに起因している気がしています。いや、普通に動いている。問題ない
- [x] 二つのブロックがなんホップ離れているかを計算する関数
- [x] 現在、キャッシュのサイズは、そこに格納できる要素数で規定している。が、そうではなく、GiBで規定できるようにしたい。
- [x] L3キャッシュの使用容量だけど、今は、圧縮前のサイズで計算している。これ、圧縮したデータを追加するようにしてほしい。よろしくお願いします。
- [x] キャッシュミスをしたときに、ミスをした箇所からプリフェッチを再開するみたいな。ミスが生じたときに、そのポイントから再びプリフェッチを始めるようなプログラムを書いてください
- [x] プレイフェッチポリシー、リプレイスメントポリシーを多数用意

- [x] サーバ側で、キャッシュのヒット率 (ユーザからのリクエストに応じた) を出せるようにしてほしい。これすごく大事。
なんだけど、これやるためには、クライアントから来る2つのリクエスト (ユーザが出すリクエスト、プリフェッチャーが出すリクエスト) の二つを区別する必要があります。そこまで来ると、もうwebsocketで書き直した方が早い気がするのですが。。。えええ。

- [x] キャッシュのサイズから、最大の半径を計算するプログラムを書いてください。
--> いい感じのところまで来ました。

- [x] 競合 (というか、並列読み出しにより読み出しのバンド幅が各プロセスで割られてしまう問題) の解消。具体的には、slicerにキューを持たせて解決？
しかし、ここで問題なのが、なんかわからんけど、複数スレッドで同じインスタンスのメソッドを使おうとするとあるスレッドからは全く受け付けない、みたいなことが生じてしまこと。(だから、今はL3 pref, L4 pref, User reqがそれぞれでSlicerインスタンスを持っている)これは、マルチスレッドによる制御がうまくいっていないからだろうね。ここがうまくいったらいいのですが。つまり、今考えられる解決方法、簡単な方から上げていくと、
1. ただのMutexによる共有資源 (ストレージ) へのアクセス制御
2. slicerにキューを持たせて、L3やユーザはそのキューを介して資源を使えるようにする。しかしこの場合は、ユーザ、L3, L4みんなで同じSlicerインスタンスを共有しないといけない。その時に、上の問題を解決しないといけない。その方法を考えたい。どうやるか？次のキーワードで検索してみよう。
「How to controle a situation where Multiple threads want to use a class's methods?」的な感じで。ここをうまくやらないといけないんですわ。逆にここがうまくいけばかち。
--> これなんだけど、なんかもう限界に達している気がする。だから、L4のプリフェッチャの動きをちゃんとしたい。
つまり、ユーザの動きに合わせてちゃんとプリフェッチしてほしい。
あと、キューをクリアするのにかかる時間はほとんどないからそんなに気にしなくていいよ。
evictionにかかる時間はほぼないから気にしなくていい。
まあ、この問題は、結局どんなに頑張っても、マルチスレッドで実行すると、sequentialにやるか、一緒にやって、バンド幅を減らすか、それしかないので
これ以上の向上は望めないということで。あきらめましょう。ユーザの解析時間をついかすることでバックグラウンド実行ができるようになるので
ましにはなるかと思います。

- [x] いろいろと確認するところがありますね。２重で取ってきたりしていないか。これはすごく大事なポイントだね。
ー＞これがあるとすごくもったいないっていうのはわかるよね。なさそうですね。
Informするところでこの問題は解決されている。

- [x] えーっと、一つのシステムの設定ごとにアクセスパターンを変更してしまっているので、公平な評価ができていません。
何をすればいいかというと、アクセスパターンのリクエストシーケンスは固定してください。
で、いちばん外側のループでリクエストシーケンスを変更してください。で、生じる遅延の平均だけではなく、分散も評価してください。

- [x] missした時にクリアとかしない方が早くなる。これは大事やな。クリアで使う時間がもったいなさすぎる。

- [x] で、L3入れるとやっぱり読み出しで競合が発生しているみたいだね。
プリフェッチャが読み出しているところをクリアできれば最高なんだけどな。
1つのリソースを使ってやる場合、多少の競合は不可避である。メモリからの読み出しもそう。
- [x] 評価の時は、平均レイテンシーだけではなく、分散や標準偏差も出したいと思っている！。1リクエストのレイテンシーを配列にためて、それを単純にnumpyにかければ一発でした。
- [x] ユーザの動きを常に把握しながら、そのポイントを中心にプリフェッチをするプログラムを書いてください。
--> 現在、ユーザの位置を通知するインターフェースは作った。あとは、中心を知らせたときに、中心の半径に入っていないやつらを抜きつつ、半径以内にいるのにキャッシュには含まれていないやつらをプリフェッチするプログラムを書いてください。よろしくお願いします。どうやってやるか？だけど、ユーザの位置は常に各レイヤーのプリフェッチャに通知されるようにしてください。
で、そのブロックとキャッシュに入っているブロックとの位置を計算します。O(n)ですね。で、radisu以上だったら抜いてください。(積極的追い出し/消極的追い出しかはあとで考える)。これはevictメソッドで実装します。
それだけではなく、プリフェッチしに行くコンポーネントも更新する必要があります。
この二つをいかに効率よくやるかが、システムソフトなので、全体の性能に影響してきます。
アルゴリズムとデータ構造のお話だよね。 (最優先)

# メモ？
つまり、まずはちゃんと狙いすましてプリフェッチしよう。キャッシュのヒット率を上げればだいぶ解消されるはずです。
まあつまり、無駄なプリフェッチをなくしてくれや。
ーーー＞ロックをかけるとさらに遅くなってしまうという現象が起こっている。これね、どうするかね。
ーー＞おそらくmutexでロックをかけるのがシステムコールだからさらに遅くなってしまうってことなんだよね。
だからね、これは、mutexではなく、自作ロックでいいってことにしよう。
strictLock (0.49418292999267577)
のところ、
looseLock (0.48913016319274905) No cache　って感じです。
ちなみに、なんでコンテキストスイッチでオーバヘッドが大きくなるんだ。

結局、無駄な読み出しをどれだけ削減できるかが大事になってくる。
これは、論文にも書いた方がいい。実際そうだから。
もう少し連携を高めよう。マジで。連携な。