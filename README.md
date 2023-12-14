# The_Middleware
A middleware to support on-demand massive-scientific-data-visualization 

# HTTP interface

## header type
1. FirstContact (再初期化も含む)

header = {
    'type':'init',
    'offset':BlockOffset,
    'L3Size' : 1000,
    'L4Size': 1000,
    'Policy' :'LRU',
    'FileName' : 'test',
}

L3Sizeが0の時にはoffってことにします。

ここにリプレイスメントポリシーを入れるって感じにしたいと思います。キャッシュサイズも決められるようにしたいと思います。

2. BlockRequest

header = {
    'type':'BlockReq',
    'tol':BlockId[0],
    'timestep':BlockId[1],
    'x': BlockId[2],
    'y': BlockId[3],
    'z': BlockId[4]
}

3. noCompress

header = {
    'type':'noCompress',
    'timestep':BlockId[1],
    'x': BlockId[2],
    'y': BlockId[3],
    'z': BlockId[4]
}

圧縮せずに全部持ってくる感じです！！

4. userPoint


5. getStats



6. BlockReqUsr
これは、ユーザがリクエストしたってことです。


## body
compressed array


# NEW TODO
- [ ] HDF5 -> TileDBに変更。これでミドルウェア単体の性能を評価できる。
- [ ] TileDBフォーマットでデータを流し込む
- [ ] 競合 (というか、並列読み出しにより読み出しのバンド幅が各プロセスで割られてしまう問題) の解消。具体的には、slicerにキューを持たせて解決？
しかし、ここで問題なのが、なんかわからんけど、複数スレッドで同じインスタンスのメソッドを使おうとするとあるスレッドからは全く受け付けない、みたいなことが生じてしまこと。(だから、今はL3 pref, L4 pref, User reqがそれぞれでSlicerインスタンスを持っている)これは、マルチスレッドによる制御がうまくいっていないからだろうね。ここがうまくいったらいいのですが。つまり、今考えられる解決方法、簡単な方から上げていくと、
1. ただのMutexによる共有資源 (ストレージ) へのアクセス制御
2. slicerにキューを持たせて、L3やユーザはそのキューを介して資源を使えるようにする。しかしこの場合は、ユーザ、L3, L4みんなで同じSlicerインスタンスを共有しないといけない。その時に、上の問題を解決しないといけない。その方法を考えたい。どうやるか？次のキーワードで検索してみよう。
「How to controle a situation where Multiple threads want to use a class's methods?」的な感じで。ここをうまくやらないといけないんですわ。逆にここがうまくいけばかち。
- [ ] multiGPUを使えるシステムを構築！
- [ ] ここまで来たら、リクエストとレスポンスにそれぞれの処理時間をのっけた評価をしたい！
- [ ] 評価の時は、平均レイテンシーだけではなく、分散や標準偏差も出したいと思っている！

--> これに関して、おそらくすごく単純な問題だったみたいなので、ここで共有したいと思います。
本当か？まあ明日やってみよう。
```
import threading

class Slicer:
    def __init__(self, blockOffset=256, filename="/scratch/aoyagir/step1_256_test_0902.h5"):
        # ... (rest of your __init__ method remains the same)
        self.lock = threading.Lock()

    # Other methods remain unchanged

    def slice_single_step(self, timestep, x_start, x_end, y_start, y_end, z_start, z_end):
        with self.lock:
            subset = self.dataset[timestep, x_start:x_end, y_start:y_end, z_start:z_end]
            retsubset = np.squeeze(subset)
            return retsubset
```
これでconcurenncy controlができるらしい。セマフォを使うと同時に実行できるスレッド数を制限することもできますよ。こんな感じで。
```

class Slicer:
    def __init__(self, blockOffset=256, filename="/scratch/aoyagir/step1_256_test_0902.h5"):
        # ... (rest of your __init__ method remains the same)
        self.semaphore = threading.Semaphore(2)  # Initialize with a limit of 2 threads

    # Other methods remain unchanged

    def slice_single_step(self, timestep, x_start, x_end, y_start, y_end, z_start, z_end):
        with self.semaphore:
            subset = self.dataset[timestep, x_start:x_end, y_start:y_end, z_start:z_end]
            retsubset = np.squeeze(subset)
            return retsubset
```
うん。グローバルスペースで生成して、それを複数スレッドで共有する感じにしたいです。

ここまでを来週の水曜日までに終わらせたいのです！来週の水曜日までに全部の評価を持っていきたいのです。。。！
- [ ] そして論文を書きたいのです。やっぱり一本、ちゃんとしたところに通したい！


# 対戦相手一覧
- [ ] HDF5とTileDBどっちも
- [ ] Pure TileDB
- [ ] FP16
- [ ] FP8
- [ ] traditional approach (つまり、ftpとかgridftpで必要なデータを交換してから読み出すやつね。これも評価出来たらめっちゃいいなーって思っています！)

# psnrも評価に入れた方がいいかもしれない

# TODO
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

- [ ] 連続リクエストとランダムのミックスが対話的解析のリクエストとして妥当性があるのかどうか？そこを示す論文を探さないといけない。
- [ ] 初期コンタクトでサーバからデータの範囲を受信

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

- [ ] サーバ側で、キャッシュのヒット率 (ユーザからのリクエストに応じた) を出せるようにしてほしい。これすごく大事。
なんだけど、これやるためには、クライアントから来る2つのリクエスト (ユーザが出すリクエスト、プリフェッチャーが出すリクエスト) の二つを区別する必要があります。そこまで来ると、もうwebsocketで書き直した方が早い気がするのですが。。。えええ。

- [ ] キャッシュのサイズから、最大の半径を計算するプログラムを書いてください。
--> いい感じのところまで来ました。
- [ ] やはりHTTPだとオーバヘッドが大きい。というのも、一回一回コネクションを張らないといけないから。これのせいで、セッションも管理しないといけない。pythonでできるかわからないけど、通信部分も自分で書いた方がいいかもしれない。
- [ ] ユーザの動きを常に把握しながら、そのポイントを中心にプリフェッチをするプログラムを書いてください。
--> 現在、ユーザの位置を通知するインターフェースは作った。あとは、中心を知らせたときに、中心の半径に入っていないやつらを抜きつつ、半径以内にいるのにキャッシュには含まれていないやつらをプリフェッチするプログラムを書いてください。よろしくお願いします。


## overall
- [x] シンギュラリティーコンテナを作る。たのむ。動いてくれ。clientはsharkとかで動かそう。って話だ。
ー－＞解決
- [x] バグの個所を先生に見てもらう-->解決。

- [ ] 一回、評価をしたい。マジで。これが終わった後にキャッシュのヒット率に関してはやりたいと思う。
csvは入っている、のでできる。

```
# Create the file name based on the timestamp
csv_file = f'bench_{timestamp}_timestep_{timestep}.txt'

import csv

header = ['tol', 'OriginalSizeInByte','CompressedSizeInByte','CompRatio','avg_load_time', 'std_dev_load_time','load_throughput'
            ,'avg_comp_time', 'std_dev_comp_time','comp_throughput', 'avg_decomp_time',
            'std_dev_decomp_time', 'decomp_throughput', 'devName']

with open(csv_file, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(header)
```
こんな感じでいける。
```
header = ['tol',]
```


- [ ] wayを追加？どうやって？
- [ ] onion-cache


## Done ones