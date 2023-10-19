import requests
import numpy as np
import matplotlib.pyplot as plt
import queue
from collections import deque
import asyncio
import numpy as np
import threading
import time

# self-defined libraries
import _mgard as mgard
from L3_L4Cache import LRU_cache
from L3_L4Cache import dynamic_cache
from slice import Slicer
from compressor import compressor

# L3キャッシュとL4キャッシュプリふぇっちゃで同じスライサーを共有すると、なぜか片方が全く取れなくなるという現象に遭遇
class L3Prefetcher:
    def __init__(self,L3Cache,L4Cache,L4Prefetcher,dataDim, blockOffset=256) -> None:
        # ToleranceArray
        self.Tols = [0.0001,0.001,0.01,0.1,0.2,0.3,0.4,0.5]
        self.dataDim = dataDim
        self.maxTimestep = dataDim[0]
        self.maxX = dataDim[1]
        self.maxY = dataDim[2]
        self.maxZ = dataDim[3]
        self.blockOffset = blockOffset
        self.L3Cache = L3Cache
        self.L4Cache = L4Cache
        # これね、L3PrefetcherとL4Prefetcherで別々のもの持ってないとなんか片方が一生使えなくなる
        self.Slicer = Slicer(blockOffset=blockOffset)
        self.compressor = compressor(self.L3Cache)
        self.L4Pref = L4Prefetcher
        self.gonnaPrefetchSet = set()
        self.prefetchedSet = set()
        self.prefetch_q = deque() # blocks going to get
        self.thread = None
        # キャッシュに入れるブロックの半径
        self.radius = 10 # for now.

        # スレッドを止めるためのフラグ
        self.stop_thread = False

        # フェッチループを起動
        if self.L3Cache.capacity == 0:
            # L3キャッシュが0の時は、L3Prefetcherはスタートしないと
            pass
        else :
            print("start L3 prefetcher")
            self.thread = threading.Thread(target=self.thread_func)
            self.thread.start()
            # 最初のブロックを投下
            self.enqueue_first_blockId()
        
    # 距離パラメータを追加すればいいと思います！
    def enque_neighbor_blocks(self,centerBlock,d):
        tol = centerBlock[0] 
        timestep = centerBlock[1]
        x = centerBlock[2]
        y = centerBlock[3]
        z = centerBlock[4]
        distance = d + 1

        ## TODO tolの扱い。tolはあくまで、インタラクティブにするために必要なものなので、tolの次元は無視していい。
        ## tolまで入れるとだいぶ厳しくなる。容量的に。
        for dt in [-1,0,1]:
            for dx in [-self.blockOffset, 0, self.blockOffset]:
                for dy in [-self.blockOffset, 0, self.blockOffset]:
                    for dz in [-self.blockOffset, 0, self.blockOffset]:
                        if (self.gonnaPrefetchSet.__contains__((tol,timestep+dt, x+dx, y+dy, z+dz))
                            or (timestep+dt < 0) or (timestep+dt >= self.maxTimestep) 
                            or (x+dx < 0) or (x+dx >= self.maxX)
                            or (y+dy < 0) or (y+dy >= self.maxY)
                            or (z+dz < 0) or (z+dz >= self.maxZ)):
                            continue
                        else:
                            self.prefetch_q.append((tol,timestep+dt, x+dx, y+dy, z+dz))
                            self.gonnaPrefetchSet.add((tol,timestep+dt, x+dx, y+dy, z+dz))

    def enqueue_first_blockId(self,blockId=(0.1, 0, 0 ,0 ,0 ),d=0):
        self.prefetch_q.append(blockId)
        self.gonnaPrefetchSet.add(blockId)

    def pop_front(self):
        return self.prefetch_q.popleft()
    
    def prefetch_q_empty(self):
        if(len(self.prefetch_q) == 0):
            return True
        else:
            return False
        
    def print_prefetch_q(self):
        print(self.prefetch_q)



    def getRadiusFromCapacity(self):
        capacity = self.L3Cache.capacity
        blockSize = self.blockOffset
        # how to get radius? 4/3*pi*r**3が球の体積だけど、ここ、
        # どうにかしてキャッシュの容量から、その容量を満たす半径を出したいんだよね。
        # 2Dでは、8ブロックが隣接,3Dでは、26このブロックが隣接。4Dでは、80個らしい。
        # n次元立方体の頂点の数は2^nで一般化できる。で、一つの頂点二着重くしたときに、これができれば、話は簡単だ
        # おそらく。まて、
        # n次元立方体の面の数は2nこ。
        # 辺の数は、n*2^(n-1)こ
        # 頂点の数は、2^n
        # で、一つの立方体を考えると、面で接しているのが2n、辺で接しているのがn*2^(n-1)頂点で接しているのが、2^n
        # つまり、2n + n*2^(n-1) + 2^n 
        # n = 2の時、4 + 4 + 4 = 12いや間違ってるわ！
        # 超体積から考えると、a^nなので、aが3の時、3^3 - 1 = 26
        # 3^4 - 1 = 80
        # 3^n - 1で合っているんじゃないか？そんな気がしてきたわ。26*3 + 2 も行けるね、4次元なら、
        # これは、今自分がいる時間に26個隣接していて、隣接する時間それぞれに27 (26 + 1)あるからっていう式
        # よくて、5ホップとかな気がする。
        # ちなみに、4次元球の面積は、pi*pi*r*r*r*r/2
        # また、4次元立方体の体積はa^4
        # blockSize が合って、これは置いておいて、
        # 例えば、16GiBって、何個の要素が入るのか？
        # elements(個)*4(byte/個) = 16*1024*1024*1024 (bytes)
        # elements = 4*1024*1024*1024個
        # 4*1024*1024*1024 = a^4をとくとどうなる？
        # 2^(8*4) = a^4
        # a = 2^8 = 256だってさ。まじで？
        # 今やりたいことは、キャッシュのサイズがあって、その周りなんホップまでそのキャッシュに入れられるか？のホップ数を
        # 出したいんですよね。4次元で。とりあえず、一遍の長さ
        # ホップするごとに増える要素数を数えればいいんだ
        # n = 2 の時、　0ホップ　ー＞　1、 1ホップ　→　３、2ホップ、５
        # n = 3の時0、０ホップ：１、1ホップ：２７、２ホップ、125(5*3)とかな気がしています。
        # n = 4の時：0ホップ：1、1ホップ：81 (3*4):、2ホップ(5**4) = 625、3ホップ(7**4) = 2401、4ホップ(9**4) = 6551
        # ホップ数は半径ですね。なるほど、こういう感じで増えていくのか。
        # つまり、4次元空間で、半径2(今いるブロックから2ホップいるブロックから2ホップ以内の)のブロックを全部持ってこようと
        # すると、なんと625個も必要になるんですね。これは大変ですね。
        # 256**3*4*625 = 2**24*625 = 16*625MiB= 10GiBって感じですね。
        # これ、半径を3にすると、どうなるんだろう？ってことで、1ブロックを256で計算した場合、
        # 256**3*4*2401 = 16*2401MiB = 38416MiB = 38.4GiBって感じですね。これはいける。
        # 半径を4にすると、どうなるのか？104.816GiBって感じになりました。だいぶ多いですね。Muffin2じゃないと評価が厳しいかもです。
        # で、L1とL4は生データを保持しているので、サイズからすぐにホップ数が計算できると。
        # 問題は、L3とL2よね。圧縮されている、さらに圧縮率にもばらつきがあるので、サイズから一位にホップ数を決めることができないのよね。
        # まあそこは仕方がない。
        radius = 10
        return radius
    
    def stopPrefetchingAndChangeCenter(self,centerBlockId):
        # まず、一回プリフェッチをやめる。
        # prefetch_Qを空にする。これをやるだけで、いい？
        # 新しいセンターポイントがわかる。
        # 新しいセンターポイントとキャッシュに入っている各要素との距離(ホップ数を計算する)。ここのけいさんが難しい。
        # どうやってやるのか俺にはわからん calcHops()で計算
        # で、そのホップ数が、指定半径(ホップ数)よりも大きい場合にはキャッシュからリムーブする。
        for blockId,blockValue in self.L3Cache.cache.items():
            hops = self.calcHops(centerBlockId,blockId)
            if hops > self.radius:
                self.L3Cache.cache.pop(blockId)
                self.prefetchedSet.discard(blockId)
        
        # enqueBlockId.enqueueが完了すれば、あとは自動でプリフェッチが始まる。
        # てか、ミスした後にこれをプリフェッチキューに入れてももう遅いとは思うんだけどね。（笑）
        self.enqueue_first_blockId(centerBlockId,0)


    def calcHops(self,centerBlockId,targetBlockId):
        pass

    # ここでどういう風にプリフェッチポリシーを変えるかというのもなかなか見ものであるところです
    def InformL3Hit(self,blockId):
        print("L3 hit ! nice! From L3 prefetcher")
        pass

    def InformL3MissAndL4Hit(self,blockId):
        print("L3Miss and L4 Hit")
    
    def InformL3MissAndL4Miss(self,blockId):
        print("L3 Missed and L4 Miss:{}\n".format(blockId))
        # TODO 何かしらのプリフェッチポリシーの変更を加える必要
        pass

    def InformL4MissByPref(self,blockId):
        print("L3 Prefetcher missed L4 and brought from disk:{}\n",blockId)

    
    async def fetchLoop(self):
        while not self.stop_thread:
            # print("L3 cache:")
            # self.L3Cache.printInfo()
            # self.L3Cache.printAllKeys()
            if (not self.prefetch_q_empty()) and (len(self.L3Cache.cache) < self.L3Cache.capacity):
                nextBlockId = self.pop_front()
                original = self.L4Cache.get(nextBlockId)
                if original is None:
                    try:
                        self.L4Pref.prefetch_q.remove(nextBlockId)
                        print("succeed in deleting {} in L4's prefetch Q".format(nextBlockId))
                    except Exception as e:
                        pass
                    d = self.Slicer.sliceData(nextBlockId)
                    # print("nextBlockId=",nextBlockId)
                    # print("blocks size=",d.nbytes)
                    # write to L4 also
                    self.L4Cache.put(nextBlockId,d)
                    tol = nextBlockId[0]
                    compressed = self.compressor.compress(d,tol)
                    self.L3Cache.put(nextBlockId,compressed)
                else:
                    print("L4 HIT! when L3 Prefetching from L4",nextBlockId)
                    tol = nextBlockId[0]
                    compressed = self.compressor.compress(original,tol)
                    self.L3Cache.put(nextBlockId,compressed)
                self.prefetchedSet.add(nextBlockId)
                self.enque_neighbor_blocks(nextBlockId)
            else:
                await asyncio.sleep(0.1)  # Sleep for 1 second, or adjust as needed
    
    def startPrefetching(self):
        self.stop_thread = False
        if self.L3Cache.capacity > 0:
            self.thread = threading.Thread(target=self.thread_func)
            self.thread.start()
            self.enqueue_first_blockId()
            print("restarted L3 prefetcher!")
        else :
            print("L3 cache size is 0. So L3 prefetcher is not starting")

    def stop(self):
        self.stop_thread = True

    def InitializeSetting(self,blockOffset):
        self.Slicer.changeBlockSize(blockOffset)
        self.prefetchedSet = set()
        self.gonnaPrefetchSet = set()
        self.prefetch_q = deque()
        self.blockOffset = blockOffset

    def changeBlockOffset(self,blockOffset):
        self.blockOffset = blockOffset

    def thread_func(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.fetchLoop())          


# TODO 継承
class L4Prefetcher:
    def __init__(self,L4Cache,dataDim,blockSize):
        self.L4Cache = L4Cache
        self.Slicer = Slicer(blockOffset=blockSize)
        self.Tols = [0.0001,0.001,0.01,0.1,0.2,0.3,0.4,0.5]
        self.dataDim = dataDim
        self.maxTimestep = dataDim[0]
        self.maxX = dataDim[1]
        self.maxY = dataDim[2]
        self.maxZ = dataDim[3]
        self.blockOffset = blockSize
        self.gonnaPrefetchSet = set() # プリフェッチしに行くセット
        self.prefetchedSet = set() # プリフェッチしたセット
        self.prefetch_q = deque()
        self.stop_thread = False
        self.thread = None

        # フェッチループ起動
        if self.L4Cache.capacity == 0:
            pass
        else :
            print("start L4 prefetcher")
            self.thread = threading.Thread(target=self.thread_func)
            self.thread.start()
            self.enqueue_first_blockId()



# ここのforループの順番を変えることで、時間なのか、空間なのか、どっちの情報を優先的に取ってくるのかを決められる。どうするか？
    def enque_neighbor_blocks(self,centerBlock):

        tol = centerBlock[0] 
        timestep = centerBlock[1]
        x = centerBlock[2]
        y = centerBlock[3]
        z = centerBlock[4]

        ## TODO tolの扱い
        for dt in [-1,0,1]:
            for dx in [-self.blockOffset, 0, self.blockOffset]:
                for dy in [-self.blockOffset, 0, self.blockOffset]:
                    for dz in [-self.blockOffset, 0, self.blockOffset]:
                        if (self.gonnaPrefetchSet.__contains__((tol,timestep+dt, x+dx, y+dy, z+dz))
                            or (timestep+dt < 0) or (timestep+dt >= self.maxTimestep) 
                            or (x+dx < 0) or (x+dx >= self.maxX)
                            or (y+dy < 0) or (y+dy >= self.maxY)
                            or (z+dz < 0) or (z+dz >= self.maxZ)):
                            continue
                        else:
                            self.prefetch_q.append((tol,timestep+dt, x+dx, y+dy, z+dz))
                            self.gonnaPrefetchSet.add((tol,timestep+dt, x+dx, y+dy, z+dz))

    def pop_front(self):
        return self.prefetch_q.popleft()
    
    def prefetch_q_empty(self):
        if(len(self.prefetch_q) == 0):
            return True
        else:
            return False
        
    def print_prefetch_q(self):
        print(self.prefetch_q)


    def enqueue_blockId(self,blockId):
        self.prefetch_q.append(blockId)

    def enqueue_first_blockId(self):
        firstBlock = (0.1, 0, 0 ,0 ,0 )
        self.prefetch_q.append(firstBlock)
        self.gonnaPrefetchSet.add(firstBlock)

    def InformL3Hit(self,blockId):
        print("L3 hit! nice! from L4 prefetcher")
        pass

    def InformL3MissAndL4Hit(self,blockId):
        print("L3Miss and L4 Hit")
    
    def InformL3MissAndL4Miss(self,blockId):
        print("L3 Miss and L4 Miss:{}\n".format(blockId))
        # TODO 何かしらのプリフェッチポリシーの変更を加える必要
        pass

    def InformL4MissByPref(self,blockId):
        print("L3 Prefetcher missed L4 and brought from disk:{}\n",blockId)

    def clearPrifetchingQ(self):
        self.prefetch_q = deque()

    async def fetchLoop(self):
        while not self.stop_thread:
            # print("L4 cache:")
            # self.L4Cache.printInfo()
            # self.L4Cache.printAllKeys()
            if (not self.prefetch_q_empty()) and (len(self.L4Cache.cache) < self.L4Cache.capacity):
                nextBlockId = self.pop_front()
                data = self.Slicer.sliceData(nextBlockId)
                self.L4Cache.put(nextBlockId,data)
                self.prefetchedSet.add(nextBlockId)
                self.enque_neighbor_blocks(nextBlockId)
            else:
                await asyncio.sleep(0.1)  # Sleep for 1 second, or adjust as needed
    

    def startPrefetching(self):
        self.stop_thread = False
        if self.L4Cache.capacity > 0:
            self.thread = threading.Thread(target=self.thread_func)
            self.thread.start()
            self.enqueue_first_blockId()
            print("restarted L4 prefetcher!")
        else :
            print("L4 cache size is 0. So L4 prefetcher is not starting")
        
    def changeBlockOffset(self,blockOffset):
        self.blockOffset = blockOffset

    def stop(self):
        self.stop_thread = True

    def InitializeSetting(self,blockOffset):
        self.Slicer.changeBlockSize(blockOffset)
        self.prefetchedSet = set()
        self.gonnaPrefetchSet = set()
        self.prefetch_q = deque()
        self.blockOffset = blockOffset

    def thread_func(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.fetchLoop())       

  






         



