
# サーバが動いている
## 初期コンタクトでは、データサイズ、ブロックサイズなどをやり取りする。

## timestep0,x,y,z = 0からスタートするので、それを最初に取ってくる

## decompressorは最初にインスタンスとして作ってしまう。それをみんなで共有して使う感じ。
### decompressorインスタンスを共有するインスタンスは
#### L1プリふぇっちゃかな。
#### L2プリふぇっちゃも保持してないとだめだね。緊急ジョブが入ってきたときにL2から直接decompressorインスタンスに渡すこともあるので
#### L2キャッシュも持ってないとだめな気がしてきた。L1キャッシュでノンヒットだったときは、L2キャッシュを見に行って、そこでヒットしたら
#### すぐにdecompressを始めないといけないからね。
#### decompressorで処理するためのデータ用のキューも用意する必要ある感じかな？

## ユーザが指定したtol,timestep,x,y,z, offset*3を使って、データを再構築する役割を担うのが、recomposerだね。
### こいつは、L1キャッシュを保持している。
### ユーザが指定したtol,timestep,x,y,z, offset*3 --> set of (tol,timestep,x,y,z)を作る。おそらくtolとtimestepは
### 一定だから、(x,y,z)のセットを作ればいい。で、キャッシュにアクセスして、キャッシュに入っているやつはsetから捨てる。
### 入ってないやつは、誰からもらうんだ？　

## プリふぇっちゃーは二つあるってはなし。一つは、ネットワーク側のプリふぇっちゃL2プリふぇっちゃね。
### こいつは単独で自分のスレッドで動いている。
### が、L2キャッシュから、もってこーい、って指示を受けることもある。
### それは、L1キャッシュでもL2キャッシュでもヒットしなかった時だよね
### L2キャッシュでヒットしたら、L2Cacheがdecompressして、それを誰に返すんだ？循環参照が起こりすぎて辛い。。


## もう一つは、L1とL2の間にいるプリふぇっちゃ。こいつは、decompressorに指示を出す権限を持っている。
### L1キャッシュでノンヒットした場合、まずは、L2を見に行く。それでヒットすれば、でコンプレッサーを起動してバーッてやればいい。
### L2でもヒットしなかった場合が面倒で、この場合は、割り込みが生じる感じになるのか。今やっていることを一回全部やめて、最優先タスクが投入される。
### 最優先タスクとは、ユーザがほしいって指示したやつをネットワーク越しに持ってくるお仕事
### この時、LRUキャッシュは特に何もやらない。てか、LRUキャッシュってプリフェッチもしなくないか？って今思った。
### プリフェッチポリシーは同じにしてあげよう


## L2プリふぇっちゃーは、内部にでキューを持っていて、でキューから先頭要素をポップして、それをネットワークでアクセス
## して取ってきますね。
### でキューである理由は、割り込みを生じさせるためです。割り込みを所持させて、行きたいと思います。
### あと、プリふぇっちゃーはある点の周辺からどんどんデータを取ってくるわけですが、周りを見ることで実現するんですね。
### もうすでにキューの中に入っているかの確認はどうやってしましょうか、というのが課題ですね。setとかで別に管理するのがいいのかな。
### 一戸出す。リクエストが返ってくる。その周りのタイルを持ってくる。つまり、キューに入れる。で一戸リクエストを出す。周りのタイルがあるか確認して
### って感じだから。周りのタイルをキューに入れる時点で同時にsetも使えばいいんだ。なるほど。図にした方がいいかな。