import numpy as np
from decompressor import Decompressor
from NetInterface import NetIF
from Prefetcher import L2Prefetcher
from L1_L2Cache import LRU_cache
from recomposer import Recomposer


class UI:
    # サーバが動いている
    ## 初期コンタクトでは、データサイズ、ブロックサイズなどをやり取りする。

## timestep0,x,y,z = 0からスタートするので、それを最初に取ってくる

## decompressorは最初にインスタンスとして作ってしまう。それをみんなで共有して使う感じ。
    
    def __init__(self):
        self.decompressor = Decompressor()
        
        # decompressorインスタンスを共有するインスタンスは
        self.L1CacheSize = 100
        self.L2CacheSize = 1000
        self.blockOffset = 256
        
        # ここの、キャッシュサイズは変えてみるとおもろいって話
        # 生データが入っている
        self.L1Cache = LRU_cache(self.L1CacheSize,self.blockOffset,decompressor=self.decompressor)
        
        # 圧縮されたデータが入っている
        self.L2Cache = LRU_cache(self.L2CacheSize,self.blockOffset)

        # netInterface
        self.netIF = NetIF(L2Cache=self.L2Cache)

        # L2プリふぇっちゃー (L2キャッシュに圧縮されたデータをガンガン持ってくる担当)
        self.prefetcher = L2Prefetcher(L2Cache=self.L2Cache,NetIF=self.netIF)

        # recomposer
        self.recomposer = Recomposer()

        # この辺で、ループをスタートする。
        start_loop()
    


    def getBlocks(self,tol,timestep,x,y,z,xOffset,yOffset,zOffset):
        # まずは、x,y,z,offsetsから、self.blockOffsetに合うように、ブロックを作らないといけないのよ。
        
        BlockIds = self.Block2BlockIds(tol,timestep,x,y,z,xOffset,yOffset,zOffset)
        BlockAndData = {}

        for blockId in BlockIds:
            L1data = self.L1Cache.get(blockId)
            if L1data == None:
                L2data = self.L2Cache.get(blockId)
                if L2data == None:
                    # urget fetch using NetIF directly
                    compressed = self.netIF.send_req_urgent(blockId)
                    original = self.decompressor(compressed)
                    BlockAndData[blockId] = original
                else :
                    original = self.decompressor(L2data)
                    BlockAndData[blockId] = original
                    
                
        

    def Block2BlockIds(self,tol,timestep,x,y,z,xOffset,yOffset,zOffset):
        xStartIdx = x//self.blockOffset*self.blockOffset
        xEndPointIdx = (x + xOffset + self.blockOffset)//self.blockOffset*self.blockOffset
        if (x + xOffset) % self.blockOffset == 0:
            xEndPointIdx = (x + xOffset)//self.blockOffset*self.blockOffset
        xStartIdxs = np.arrange(xStartIdx,xEndPointIdx,self.blockOffset)

        yStartIdx = y//self.blockOffset*self.blockOffset
        yEndPointIdx = (y + yOffset + self.blockOffset)//self.blockOffset*self.blockOffset
        if (y + yOffset) % self.blockOffset == 0:
            yEndPointIdx = (y + yOffset)//self.blockOffset*self.blockOffset
        xStartIdxs = np.arrange(yStartIdx,yEndPointIdx,self.blockOffset)

        zStartIdx = z//self.blockOffset*self.blockOffset
        zEndPointIdx = (z + zOffset + self.blockOffset)//self.blockOffset*self.blockOffset
        if (z + zOffset) % self.blockOffset == 0:
            zEndPointIdx = (z + zOffset)//self.blockOffset*self.blockOffset
        zStartIdxs = np.arrange(zStartIdx,zEndPointIdx,self.blockOffset)

        BlockIds = []
        for xIdx in xStartIdxs:
            for yIdx in yStartIdx:
                for zIdx in zStartIdx:
                    BlockIds.append(tol,timestep,xIdx,yIdx,zIdx)

        return BlockIds
    
#### L1プリふぇっちゃかな。
#### L2プリふぇっちゃも保持してないとだめだね。緊急ジョブが入ってきたときにL2から直接decompressorインスタンスに渡すこともあるので
#### L2キャッシュも持ってないとだめな気がしてきた。L1キャッシュでノンヒットだったときは、L2キャッシュを見に行って、そこでヒットしたら
#### すぐにdecompressを始めないといけないからね。ー－＞いや、L2はdecompressorインスタンスを持っている必要はないです。
#### L1が、L2を見に行ってなかったらもう直接取りに行きます。ということにしていい？なぜかというと、L1を見て、L2を見て、って
#### 担当者が多岐にわたると、誰が担当だったか忘れてしまうから。
#### decompressorで処理するためのデータ用のキューも用意する必要ある感じかな？あるねー－－。この辺、goだったらチャネルを使って
#### 簡単に実現できるんだけど。

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
### L2とL1はそのうち3 wayとかにするのもマジで面白そうだけどね。

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

