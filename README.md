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
- [ ] traditional approach (つまり、ftpとかgridftpで必要なデータを交換してから読み出すやつね。これも評価出来たらめっちゃいいなーって思っています！)

scpによるmonaka　→　muffin2のデータ転送は、
22.0 ~ 23.0 MB/sでした。この数値を使ってやってもいいと思いますよ！
ちなみに、ftpはめっちゃ早くて、ほぼ帯域幅を使い切れるようにできているみたいです。
大体6倍くらい早いんだけど、
22*6*8 = 1056Mb/s
って感じで、ちゃんと帯域幅を使い切ってくれていますね。これは意外です。

うん、普通にこの数値を使ってやりたいと思います。
ちなみに、研究室ネットワークのnetwork latencyは、約0.1msです。
で、iperfを使って調べたネットワークの帯域幅は、約960Mb/sでしたね。

# 評価のためのメモ
./client/eval_dataの中に評価で得たcsvファイル一式と、csvファイルを読み込んで
グラフを出力するjupyter notebookのプログラムが入っています。
どうぞ、よろしくお願いします。

# 評価指標
1. 1リクエストに対する遅延。これは、上の対戦相手全部で試せます。FP16とFP8も行けるんで。
2. n個のリクエストに対する平均遅延。分散やほかの指標も入れる。
3. psnrも評価に入れた方がいいかもしれない。入れようか

# parameters for access patern
独自のパラメータをい定義した。
1. 同じデータを何回踏むか : data_recycle_ratio

```
1 - num_of_unique_blocks_in_requests/num_of_requests
```

2. アクセス密度 : アクセスシーケンスのブロックの中で一番離れているブロック間のチェビチェフ距離 / アクセスシーケンスの長さ
まあ、これ、なかなかクセのあるパラメータでね。一タイムステップの中で一番離れている点は、対角ブロックで、この距離はたったの4なんだよね。で、タイムステップを考えると、64タイムステップあって、タイムステップは別に加算するから、
どんなに離れていても、4 + 64 = 68しか離れられないんだよね。
だから、分母をアクセスシーケンスの長さにするのはちょっと刻なのではないかな？とも思っているわけです。
つまり、もしかしたら、パラメータを変えた方がいいのかもしれない。が、まだ何がいいかはちょっとわかっていない。

```

```

# clione上でのsingularity環境起動コマンド（--bindでのマウントを忘れずに）
muffin2上でもこれで問題なく行けた。いい感じだ。

```
singularity shell --bind /scratch/:/scratch/ --nv  pymgard.sif
```

## 変数とほしいデータ
1. キャッシュ構成
2. キャッシュのサイズ
3. ユーザの処理時間
4. アクセスパターン
5. 許容誤差

はっきり言って、この5つしかない。俺が変えられる変数は。

## 変数の変化に伴うレイテンシーの変化を裏付けるための情報
1. キャッシュのヒット率
2. ユーザがリクエストした時にそれぞれの処理にかかった時間

まあ、簡単に言うと、

```
latency = latency(キャッシュ構成、キャッシュのサイズ、ユーザの処理時間、アクセスパターン、許容誤差)
cacheHitRatio = latency(キャッシュ構成、キャッシュのサイズ、ユーザの処理時間、アクセスパターン、許容誤差)
各処理にかかった時間 = 各処理にかかる(キャッシュ構成、キャッシュのサイズ、ユーザの処理時間、アクセスパターン、許容誤差)
```

縦軸は、絶対にレイテンシーにしないといけません。
そして、横軸は、5つある変数の内の4つを固定して、残りの1つを変化させてみる、って感じです。

## どういうグラフが欲しいか？
1. ある変数を固定した時の、レイテンシーと、キャッシュのヒット率折れ線になっているグラフ
2. 1を補助するグラフとして、横にキャッシュヒットの内訳を積み上げグラフとしておいておきたい
3. さらに、この横に、ユーザがリクエストした時の各処理にかかった時間を積み上げグラフとしておいておきたい
1,2,3がワンセットになっている。上にも書いた通り、キャッシュのヒット率とユーザがリクエストした時にそれぞれの処理にかかった時間がレイテンシーを説明するものだからね。

で、変数を一つ一つ固定して、進めていきますよと。

1. 
組み合わせ (この時、それぞれのキャッシュサイズ、
処理時間、許容誤差、は固定されている)

2. 
キャッシュのサイズ (このとき、一つのキャッシュ構成に対して、増やしていったときどうなるか)
だから、L1のみで、キャッシュサイズを横軸にとってどんどん大きくしていったとき
2^4通りのグラフができるよね

3. 
ユーザの処理時間 (一つのキャッシュ構成に対して、ユーザの処理時間が増えていったときにどうなるか)
これも2^4通りのグラフができるよね。

4. 
アクセスパターン 4通り

5. 
許容誤差


# bestな選択
横に、2^4のキャッシュ構成のパターンを全部おいて、
縦に、
## どういう結果になることを想定しているか？


## 1/8のTODO
- [ ] とりあえず、データが分析できるように、既存のデータを使って、データを解析、グラフ化するためのプログラムはもう作っておいて
- [ ] データたちをまとめる。
- [ ] 明日の準備をする



## 1/9のTODO
- [ ] muffin2にa100をのっけて、GPUを2基使えるようにする！
- [ ] ポスターをぼちぼち作る。

## 時間があったらのTODO
- [ ] 多少は予測をしてプリフェッチをするようにしないといけない。

# TODO
## overall
- [ ] apdcmに出す

## client
- [ ] L2プリフェッチャがちゃんと働いていない可能性。ユーザ地点がちゃんとL2に伝えられていて、さらに
サーバ側にリクエストを送っているか確認。

## server
- [ ] 置換とプリフェッチをするメカニズムは実装しました。あとは、計算量が少なくなるように、アルゴリズムとデータ構造を最適化してください。

## Done Things
## overall
- [x] シンギュラリティーコンテナを作る。たのむ。動いてくれ。clientはsharkとかで動かそう。って話だ。
ー－＞解決
- [x] バグの個所を先生に見てもらう-->解決。

- [x] 一回、評価をしたい。マジで。これが終わった後にキャッシュのヒット率に関してはやりたいと思う。
csvは入っている、のでできる。
- [x] TileDBフォーマットでデータを流し込む--> /scratch/aoyagir/tiledb
- [x] clioneのSSDを確認--> もういっぱいだし、なさそう。新しいやつを設置する以外になさそうかな。
--> 先生に新しいnvmeを買ってくれるように頼みました。ただ、home2経由で2つのGPUで動くかどうかはすぐに確認できると思うので、やってみてください。
- [x] multiGPUを使えるシステムを構築！んで、クライアントからGPU数を設定できるようにサーバを改造。これができれば、評価げーに持っていける。それをいうのであれば、tiledbとhdf5のどちらを使うかもクライアントから設定できるようになったらめっちゃいいよね。
--> できたんだけど、なんだかclioneが耐え切れなくて死んでしまう。あちゃちゃーー。

- [x] CUPYの速度を調べる。あと、1点ではなく、いろんな点でpsnrを測定する必要があるよね。
--> インストール中。インストールが終わった。あのね、cupyとの比較なんだけど、
numpyとcupy、float16はどっちも同じくらいの時間がかかることがわかりました。
どっちも同じです。なぜか？わかりません。しかし、もうそれでやるしかないでしょう。お願いします。
で、制度についてなんだけど、max_errorもそうなんだけど、mseもみておきましょうか。
--> 明日、グラフにして何が一番いいのか、確認してください。

- [x] なぜかわかりませんが、ネットワークが極端に遅くなっているのです。しかしこれはネットワークの転送そのものにかかる時間ではなく、OSのシステムコールあたりが問題になっている可能性もかなり高いと考えている。
というのも、ネットワークそのものが遅くなるなんてことはあまり考えられないからです。
どこがボトルネックになっているのか？Networkのところだけ、タイムスタンプを押して転送する必要がありそうです。
これができれば、ソフトウェアの仕組み、つまり、機能を実現するためのオーバヘッドも出せるよね。
--> いや、でも目視でネットワークの転送にかかる時間を見てみたけど、やっぱり多くなっている。
ふつーに、システムコールにも時間がかかっているって考えるのがいいと思う。うん、それでいいよ。
システムのオーバヘッドが0.01とかで、それでいいんじゃないかなあ。
0.02とかでもいいけど。それともそこもちゃんとやるか?? どうしようかね。

- [x] プリフェッチの精度も入れた方がいい。これも頑張ってくれ。頼む。
--> データの再利用率がわかれば、それなりの情報は取れるだろ。

## access patern
- [x] アクセスパターンについて。同じデータに何回アクセスするかっていう指標は作る。再利用率
- [x] アクセスパターンを定義する入力パラメータを考える。これに関しては、雅先生からもらった論文を読むのが一番早いかもしれない。
- [x] アクセスパターンはランダムに何個か作って、それを全部出力させておくのがいいと思う。パラメータと一緒に。というのも、パラーメータを入力させてアクセスパターンを生成するのは難しいと思う。逆問題的なね。
だから、アクセスパターンをランダムにたくさん生成して、アクセスパターンを定義するパラメータを算出して
その中から、目的のものを抽出する方が簡単だと思います。


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
- [x] L2プリフェッチャが動いてなくて、単なるキャッシュになっている問題を解決したい。
- [x] 最初のプリフェッチがうまくいっていない。データ転送でエラーが生じる。
--> これのせいで、コネクション張りすぎだって怒られてしまうエラーが起こるので早く解決してほしいです。
The above exception was the direct cause of the following exception:
- [x] L1プリえっちゃは、L2を見てなかったら、もうあきらめましょう。そういう設定にした方がいいです。
- [x] 連続リクエストとランダムのミックスが対話的解析のリクエストとして妥当性があるのかどうか？そこを示す論文を探さないといけない。
---> これについては連続でないと勝ち目がないとわかりました。連続の中でも何個かパターンを作ってやりたいと思います。
- [x] 初期コンタクトでサーバからデータの範囲を受信。つまり、(t,x,y,z)ね。
- [x] リクエストとレスポンスにそれぞれの処理時間をのっけた評価
--> ユーザがリクエストしたやつだけでいい。その平均を出せるようにしておく

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
- [x] ストレージ読み出し速度の測定。これでHDF5 > TileDBだったら、めっちゃ悲しいぞ。
--> Tiledbはめちゃめちゃスケーラブルである、ということが判明した。
これが何でか？なんだけど、おそらく、hdf5は全データを一つのファイルで管理しているのに対して、
Tiledbは全データをでぃれくとりに分割している。pararell Readをサポートしているのがtiledbで
hdf5はどうやらサポートしていないみたいなんだよね。これはすごい。
めちゃめちゃ性能が上がる気がする。いや、HDF5もpararell Readをサポートしているでしょ。さすがに。
- [x] HDF5 -> TileDBに変更。これでミドルウェア単体の性能を評価できる。
- [x] ユーザの動きを常に把握しながら、そのポイントを中心にプリフェッチをするプログラムを書いてください。
--> 現在、ユーザの位置を通知するインターフェースは作った。あとは、中心を知らせたときに、中心の半径に入っていないやつらを抜きつつ、半径以内にいるのにキャッシュには含まれていないやつらをプリフェッチするプログラムを書いてください。よろしくお願いします。どうやってやるか？だけど、ユーザの位置は常に各レイヤーのプリフェッチャに通知されるようにしてください。
で、そのブロックとキャッシュに入っているブロックとの位置を計算します。O(n)ですね。で、radisu以上だったら抜いてください。(積極的追い出し/消極的追い出しかはあとで考える)。これはevictメソッドで実装します。
それだけではなく、プリフェッチしに行くコンポーネントも更新する必要があります。
この二つをいかに効率よくやるかが、システムソフトなので、全体の性能に影響してきます。
アルゴリズムとデータ構造のお話だよね。 (最優先)

- [x] L3プリフェッチャはL4プリフェッチャに読み出しをお願いする感じにしたいんですけど。どうですか？？絶対にそっちの方がいいと思います。そうしましょう。L1プリフェッチャもL2プリフェッチャにお願いする感じにしましょう。なかったら。slicerがクライアント側のnet_interfaceと同じ役割を担っている。なので、L3,L4のreadRequestに対しては、Slicerが一挙に担う感じのアーキテクチャを一回試してみたいのですが、どうでしょう！うん。グローバルスペースで生成して、それを複数スレッドで共有する感じにしたいです。
--> これなんだけど、どんなに頑張って制御しようとしても、結局は読み出しを共有させて各スレッドのバンド幅を落とすか、mutexとかで排他制御して、読み出しをシーケンシャルにするかで、何かしらのブレイクスルーがないとだめだってことに気が付いた。結局はトレードオフだと。で、そのトレードオフを緩和してくれたのが、
TileDBっていう話。

- [x] hdf5がスレッド間並列をサポートしていないことが判明しました。ってことで、Tiledbを今後は使いたいたいのですが、現在、プリフェッチャごとに別々のインスタンスを持っているんですよね。TileDBの。これを一つにまとめた方がなんとなくパフォーマンスが上がる気がするのですが、どうでしょうかね。
ーー＞これは、結局ユーザはhdf5を使うインスタンスを持っていたせいじゃないかと今思っているのですが。
ちょっと後でやってみましょう。
- [x] リクエストとレスポンスにそれぞれの処理時間をのっけた評価
--> --> ユーザがリクエストしたやつだけでいい。その平均を出せるようにしておく



- [x] まずは、思い出すために一回プログラムを走らせてくれ、muffin2で。
- [x] レスポンスに各処理時間をのっけてくれ
ー＞最後にスタッツとしてクライアントがもらう設計にした。
- [x] 各プリフェッチャのOn/Offを決められるようにする。これ、別にそんなに大変じゃない。スイッチがOffだったら、プリフェッチループをしなければいいだけ。Ok?
-> これはもういいわ。
- [x] プリフェッチ精度を見るために、各プリフェッチャがプリフェッチした回数をスタッツとして残すことにした。これのプログラムを書いてくれ。
- [x] クライアントとサーバ間でどこにもバグが生じていないことを確認するために、今夜、一晩で、GPU一つでの解析を流し続けてみよう。
- [x] decomp timeが非常に遅い。これはおそらく、わざわざ別スレッドで実行しているのが原因であると考えられる。同じスレッドで実行していいですよ。--> いや、これは安定しているし、わざわざ変えなくてもいいところではある。
まあ、提案手法そのものの良さを上げたいのであれば、変えた方がいいが、ていあんしゅほうないで差を出したいのであればそこまで変化はないのでやらなくてもいいです。
- [x] 4パターンくらいのアクセスパターンを作る。でパターンを外部ファイルに書き出して、外部ファイルとしてたまったアクセスパターンを読み出せるようにしたい。
アクセスパターンについては、データの再利用率と探索空間の広がり、という二つの指標で評価することにした。とにかく、ランダムでたくさんのデータを作って、
そこから、データの再利用率と探索空間の広がりがいい感じになっているやつを選んで持ってくるようにしたい。


- [x] OSのファイルキャッシュがOnになっている可能性があるので、必ずoffにしてください。これを実現する方法についても、どうにかして調べてください。
実際にふぃあるI/Oが実施されているか確認するためのモニタリングツールとかもあると最高だよね。探してみよう。
--> file_cacheを半永久的にoffにする方法はない。しかし、clearする方法はある。
それが、
```
"echo 1 > /proc/sys/vm/drop_caches"
```
なんですね。しかしね、これ、singularityの中から実行することはできないんです。
singularityないではsudoを実行できないので。だから、違う方法を使うしかないんです。
ってことで、file_cache_server をmuffin2の上で動かしておいて、
muffin2のThe_middlewareサーバのreInit()メソッドの中で、file_cache_clientがサーバにクリアリクエストを送って、クリアされる感じにしたいんですね。


- [x] 寝ている間に、ちゃんと全部動くかの実験をする。tmuxでセッションを作って。よろしくお願いします。

- [x] クライアントの方のバグを直してくれ。恐らくL2プリフェッチャが機能していない。ただのキャッシュになっている。解決してくれ。よろしく頼む。

```
Exception in thread Thread-423 (thread_func):
Traceback (most recent call last):
  File "/usr/lib/python3.10/threading.py", line 1016, in _bootstrap_inner
    self.run()
  File "/usr/lib/python3.10/threading.py", line 953, in run
    self._target(*self._args, **self._kwargs)
  File "/import/gp-home.ciero/aoyagir/new_research/The_Middleware/src/python/client/L1_L2prefetcher.py", line 86, in thread_func
    loop.run_until_complete(self.fetchLoop())
  File "/usr/lib/python3.10/asyncio/base_events.py", line 649, in run_until_complete
    return future.result()
  File "/import/gp-home.ciero/aoyagir/new_research/The_Middleware/src/python/client/L1_L2prefetcher.py", line 78, in fetchLoop
    self.enque_neighbor_blocks(nextBlockId,0) # ここ、あってるかもう一度確認してくれ。頼む。
  File "/import/gp-home.ciero/aoyagir/new_research/The_Middleware/src/python/client/L1_L2prefetcher.py", line 98, in enque_neighbor_blocks
    x = centerBlock[2]
IndexError: tuple index out of range
送信スレッドでexeptionが発生!
tuple index out of range
```
このバグが発生するせいで、クライアントの方で、ソケットが開いて、空いたままになって、閉じられない、ってうバグが発生している気がする。これを直した方がいいですね。

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
--> これだね。本当に、どうやって無駄なプリフェッチを減らすかが大事。でも、そこは俺の研究範囲ではないのでお暇する。
これは、論文にも書いた方がいい。実際そうだから。
もう少し連携を高めよう。マジで。連携な。

キャッシュミスのペナルティーがめちゃめちゃでかい！



## 今後の展望
- [ ] wayを追加？どうやって？
- [ ] onion-cache。exclusive cacheにした方がメモリ効率は良くなるよねって話。まあ、時間もないだろうし、厳しいんじゃない？
今後の展望ってことで。
- [ ] c++で書き直す。やっぱシステムソフトなので、c/c++の方がぽい。通信部分も一回一回コネクションを張るやつではなく、
javidexさんのあの自作プロトコルがいいと思う。
- [ ] やはりHTTPだとオーバヘッドが大きい。というのも、一回一回コネクションを張らないといけないから。これのせいで、セッションも管理しないといけない。pythonでできるかわからないけど、通信部分も自分で書いた方がいいかもしれない。


## hdf5 > tiledbである理由
https://docs.h5py.org/en/stable/mpi.html
この辺を読んでください。hdf5はsingle fileで全部管理するのですが、スレッド並列をサポートしていないんですよね。プロセス並列はサポートしているんですけど。だから、3つのスレッドが例えば、aaa,bbb,cccっていうデータを読み出したいときに、それぞれの読み出しがシリアライズされて、こんな感じで、
abcabcabcになるんですよね。だからめっちゃ遅くなるって話です。はあ、って感じですね。低レイヤー勉強して俺が作り直したるわ、って感じです。