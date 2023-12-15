from collections import deque
import asyncio
import numpy as np
import threading
import time
from slice import Slicer
from compressor import compressor

class L3Prefetcher:

    # コンストラクタ
    def __init__(self,L3Cache,L4Cache,L4Prefetcher,dataDim, userIsComing,blockOffset=256) -> None:

        self.userIsComing = userIsComing
        self.dataDim = dataDim
        self.maxTimestep = dataDim[0]
        self.maxX = dataDim[1]
        self.maxY = dataDim[2]
        self.maxZ = dataDim[3]
        self.blockOffset = blockOffset
        self.L3Cache = L3Cache
        self.L4Cache = L4Cache

        # L3PrefetcherとL4Prefetcherで別々のもの持ってないと片方が一生使えなくなる->そんなことはないっぽいけど、別々に持ってた方がいい性能が出るんだよね。
        self.Slicer = Slicer(blockOffset=blockOffset)
        self.compressor = compressor(self.L3Cache)
        self.L4Pref = L4Prefetcher

        # 取りに行く予定があるブロックのセット
        self.gonnaPrefetchSet = set()

        # すでに取ってきたブロックのセット
        self.prefetchedSet = set()

        # 取りに行く予定があるブロックが順番に入っているセット。この順番を動的に管理したいのよね。
        # つまり、ここは、ユーザが見ているブロックとの距離が小さい順に並ぶようになっていてほしいのよね。
        self.prefetch_q = deque() # blocks going to get
        self.thread = None

        # tol = 0.1の場合は、大体圧縮率が25倍なので、25倍はいるってことですね。
        self.estimatedCompratio = 25 # when tol = 0.1の時
        self.radius = self.getRadiusFromCapacity()*self.estimatedCompratio

        # スレッドを止めるためのフラグ
        self.stop_thread = False

        # フェッチループを起動
        if self.L3Cache.capacityInMiB == 0:
            # L3キャッシュが0の時はL3Prefetcherはスタートしない
            pass
        else :
            print("start L3 prefetcher")
            self.thread = threading.Thread(target=self.thread_func)
            self.thread.start()

            # 最初のブロックを投下。最初は絶対にミスしますが。
            self.enqueue_first_blockId()


############### 初期化系のメソッド ###########
            
    def startPrefetching(self):
        self.stop_thread = False
        if self.L3Cache.capacityInMiB > 0:
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
        self.radius = self.getRadiusFromCapacity()*self.estimatedCompratio

    def changeBlockOffset(self,blockOffset):
        self.blockOffset = blockOffset        

    def getRadiusFromCapacity(self):
        capacity = self.L3Cache.capacityInMiB
        blockSize = self.blockOffset**3
        radius = 0
        while((2*radius+1)**3 +2 <= capacity/blockSize):
            radius += 1
        print(f"radius={radius}")
        return radius

############### プリフェッチ系のメソッド ################

    async def fetchLoop(self):
        while not self.stop_thread:
            # print("L3 cache:")
            # self.L3Cache.printInfo()
            # self.L3Cache.printAllKeys()
            # TODO いや、つまり、ユーザが来てるときはL3Prefetcherすらもよみださない、ということか。そうか、じゃあ、　L4プリフェッチャとユーザの読み出しで競合が起こっていると考えた方がいいのか。なるほど。
            if (not self.prefetch_q_empty()) and (self.L3Cache.usedSizeInMiB < self.L3Cache.capacityInMiB) and (not self.userIsComing.is_locked()):
                
                print("L3 PREFETCHER IS READING FROM STORAGE")
                nextBlockId,distance = self.pop_front()
                if distance > self.radius:
                    print("the block in the prefetch queue is no more needed")
                    continue
                original = self.L4Cache.get(nextBlockId)
                if original is None:
                    try:
                        self.L4Pref.prefetch_q.remove(nextBlockId)
                        print("succeed in deleting {} in L4's prefetch Q".format(nextBlockId))
                    except Exception as e:
                        pass
                    d = self.Slicer.sliceData(nextBlockId)
                    self.L4Cache.put(nextBlockId,d) # write to L4 also (inclusive)
                    tol = nextBlockId[0]
                    compressed = self.compressor.compress(d,tol)
                    self.L3Cache.put(nextBlockId,compressed)
                else:
                    print("L4 HIT! when L3 Prefetching from L4",nextBlockId,"distance:",distance)
                    tol = nextBlockId[0]
                    compressed = self.compressor.compress(original,tol)
                    print("compressed size : {}".format(compressed.nbytes/1024/1024))
                    self.L3Cache.put(nextBlockId,compressed)
                self.prefetchedSet.add(nextBlockId)
                self.enque_neighbor_blocks(nextBlockId,distance)
            else:
                await asyncio.sleep(0.1)  # Sleep for 1 second, or adjust as needed
    

    # 距離パラメータを追加すればいいと思います！
    def enque_neighbor_blocks(self,centerBlock,d):
        tol = centerBlock[0] 
        timestep = centerBlock[1]
        x = centerBlock[2]
        y = centerBlock[3]
        z = centerBlock[4]
        distance = d + 1

        # 時間方向に1つづれたブロックは1ホップ
        for dt in [-1,1]:
            if (self.gonnaPrefetchSet.__contains__((tol,timestep+dt, x, y, z))
                        or (timestep+dt < 0) or (timestep+dt >= self.maxTimestep)):
                continue
            else:
                self.prefetch_q.append(((tol,timestep+dt, x, y, z),distance))
                self.gonnaPrefetchSet.add((tol,timestep+dt, x, y, z))  

        for dx in [-self.blockOffset, 0, self.blockOffset]:
            for dy in [-self.blockOffset, 0, self.blockOffset]:
                for dz in [-self.blockOffset, 0, self.blockOffset]:
                    if (self.gonnaPrefetchSet.__contains__((tol,timestep, x+dx, y+dy, z+dz))
                        or (x+dx < 0) or (x+dx >= self.maxX)
                        or (y+dy < 0) or (y+dy >= self.maxY)
                        or (z+dz < 0) or (z+dz >= self.maxZ)):
                        continue
                    else:
                        self.prefetch_q.append(((tol,timestep, x+dx, y+dy, z+dz),distance))
                        self.gonnaPrefetchSet.add((tol,timestep, x+dx, y+dy, z+dz))

    def enqueue_first_blockId(self,blockId=(0.1, 0, 0 ,0 ,0 ),d=0):
        self.prefetch_q.append((blockId,d))
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


    # ブロック間の距離はシェビチェフ距離で計算。時間方向は足し算。
    def calHops(self,centerBlockId,targetBlockId):
        timeHops = abs(centerBlockId[1]-targetBlockId[1])
        xHops = abs(centerBlockId[2]- targetBlockId[2])
        yHops = abs(centerBlockId[3]- targetBlockId[3])
        zHops = abs(centerBlockId[4]- targetBlockId[4])
        spaceHops = max(xHops,yHops,zHops)//self.blockOffset
        return timeHops + spaceHops

    # TODO プリフェッチ方針を変えるか
    def InformL3Hit(self,blockId):
        print("L3 hit ! nice! From L3 prefetcher")
        pass

    # 全部捨てる必要はなくない？
    def InformL3MissAndL4Hit(self,blockId):
        print("L3Miss and L4 Hit")
        self.clearQueue()
        self.enque_neighbor_blocks(blockId,0)
    
    def InformL3MissAndL4Miss(self,blockId):
        print("L3 Missed and L4 Miss:{}\n".format(blockId))
        # self.prefetch_q.append((blockId,0)) # いや、informされた後にそれを取りに行ってももう遅いやろ。
        # self.gonnaPrefetchSet.add(blockId)
        self.prefetchedSet.add(blockId)

    def InformL4MissByPref(self,blockId):
        print("L3 Prefetcher missed L4 and brought from disk:{}\n",blockId)

    def InformUserPoint(self,blockId):
        pass

    def evict(self,centerBlockId):
        # キャッシュの要素を取り出していく。
        for blockId,blockValue in self.L3Cache.cache.items():
            hops = self.calcHops(centerBlockId,blockId)
            if hops > self.radius:
                self.L3Cache.cache.pop(blockId)
                self.prefetchedSet.discard(blockId)

        self.enqueue_first_blockId(centerBlockId,0)
    


    def thread_func(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.fetchLoop())          

    def clearQueue(self):
        start_ms = time.time()
        while not self.prefetch_q_empty():
            blockId = self.pop_front()
            self.gonnaPrefetchSet.discard(blockId)
        end_ms = time.time()
        print("time to clear queue = ",end_ms - start_ms)


# TODO 継承
class L4Prefetcher:

    # コンストラクタ
    def __init__(self,L4Cache,dataDim,blockSize,userIsComing):
        # user is coming flag
        self.userIsComing = userIsComing
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

        self.radius = 10 # for now

        # フェッチループ起動
        if self.L4Cache.capacityInMiB == 0:
            pass
        else :
            print("start L4 prefetcher")
            self.thread = threading.Thread(target=self.thread_func)
            self.thread.start()
            self.enqueue_first_blockId()

    
    
    
    ####################### 初期化系メソッド ###########################
            
    def getRadiusFromCapacity(self):
        capacity = self.L3Cache.capacityInMiB
        blockSize = self.blockOffset**3
        radius = 0
        while((2*radius+1)**3 +2 <= capacity/blockSize):
            radius += 1
        print(f"radius={radius}")
        return radius


    def startPrefetching(self):
        self.stop_thread = False
        if self.L4Cache.capacityInMiB > 0:
            self.thread = threading.Thread(target=self.thread_func)
            self.thread.start()
            self.enqueue_first_blockId()
            print("restarted L4 prefetcher!")
        else :
            print("L4 cache size is 0. So L4 prefetcher is not starting")
        
    def changeBlockOffset(self,blockOffset):
        self.blockOffset = blockOffset

    # プリフェッチスレッドを止めます。
    def stop(self):
        self.stop_thread = True

    def InitializeSetting(self,blockOffset):
        self.Slicer.changeBlockSize(blockOffset)
        self.prefetchedSet = set()
        self.gonnaPrefetchSet = set()
        self.prefetch_q = deque()
        self.blockOffset = blockOffset
        self.radius = self.getRadiusFromCapacity()*self.estimatedCompratio

    ######################## フェッチスレッド用メソッド #########################
    
    # 別スレッドで実行される本体
    async def fetchLoop(self):
        while not self.stop_thread:
            self.L4Cache.printInfo()
            # self.L4Cache.printAllKeys()
            # if (not self.prefetch_q_empty()) and (self.L4Cache.usedSizeInMiB < self.L4Cache.capacityInMiB) and (not self.userIsComing.is_locked()):
            # ここだろ。ここで競合が発生するのだ。つまり、ここを解消すればいいのだ、ロックをかけるのだ！！
            if (not self.prefetch_q_empty()) and (self.L4Cache.usedSizeInMiB < self.L4Cache.capacityInMiB):
                print("L4 PREFETCHER IS READING FROM STORAGE")
                nextBlockId,distance = self.pop_front()
                if distance > self.radius:
                    continue
                data = self.Slicer.sliceData(nextBlockId)
                self.L4Cache.put(nextBlockId,data)
                self.prefetchedSet.add(nextBlockId)
                self.enque_neighbor_blocks(nextBlockId,distance)
            else:
                print("L4 prefetcher is waiting because user is comming.")
                await asyncio.sleep(0.05)  # Sleep for 1 second, or adjust as needed
    
    # 実際はここで実行される
    def thread_func(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.fetchLoop())    

    # TODO forループの順番。時間方向か、空間、どちらを優先的に取ってくるのか
    def enque_neighbor_blocks(self,centerBlock,d):
        tol = centerBlock[0] 
        timestep = centerBlock[1]
        x = centerBlock[2]
        y = centerBlock[3]
        z = centerBlock[4]
        distance = d + 1

        # 時間方向に1つづれたブロックは1ホップ
        for dt in [-1,1]:
            if (self.gonnaPrefetchSet.__contains__((tol,timestep+dt, x, y, z))
                        or (timestep+dt < 0) or (timestep+dt >= self.maxTimestep)):
                continue
            else:
                self.prefetch_q.append(((tol,timestep+dt, x, y, z),distance))
                self.gonnaPrefetchSet.add((tol,timestep+dt, x, y, z))  

        for dx in [-self.blockOffset, 0, self.blockOffset]:
            for dy in [-self.blockOffset, 0, self.blockOffset]:
                for dz in [-self.blockOffset, 0, self.blockOffset]:
                    if (self.gonnaPrefetchSet.__contains__((tol,timestep, x+dx, y+dy, z+dz))
                        or (x+dx < 0) or (x+dx >= self.maxX)
                        or (y+dy < 0) or (y+dy >= self.maxY)
                        or (z+dz < 0) or (z+dz >= self.maxZ)):
                        continue
                    else:
                        self.prefetch_q.append(((tol,timestep, x+dx, y+dy, z+dz),distance))
                        self.gonnaPrefetchSet.add((tol,timestep, x+dx, y+dy, z+dz))

    ############ 置換方針とプリフェッチ方針を決定するメソッド #####################
                        
    def pop_front(self):
        return self.prefetch_q.popleft()
    
    def prefetch_q_empty(self):
        if(len(self.prefetch_q) == 0):
            return True
        else:
            return False
        
    def print_prefetch_q(self):
        print(self.prefetch_q)

    # 2つのブロック間のちぇびちぇふ距離を計算
    def calHops(self,centerBlockId,targetBlockId):
        timeHops = abs(centerBlockId[1]-targetBlockId[1])
        xHops = abs(centerBlockId[2]- targetBlockId[2])
        yHops = abs(centerBlockId[3]- targetBlockId[3])
        zHops = abs(centerBlockId[4]- targetBlockId[4])
        spaceHops = max(xHops,yHops,zHops)//self.blockOffset # これでホップ数が出る
        return timeHops + spaceHops
    
    def enqueue_blockId(self,blockId):
        self.prefetch_q.append(blockId)

    def enqueue_first_blockId(self,blockId = (0.1, 0, 0 ,0 ,0 ),d=0):
        self.prefetch_q.append((blockId,d))
        self.gonnaPrefetchSet.add(blockId)

    def InformL3Hit(self,blockId):
        print("L3 hit! nice! from L4 prefetcher")
        pass

    def InformL3MissAndL4Hit(self,blockId):
        print("L3Miss and L4 Hit")
        self.clearQueue() # ここで結構時間食ってる説あるよね。
        self.enque_neighbor_blocks(blockId,0)

    def InformL3MissAndL4Miss(self,blockId):
        print("L3 Miss and L4 Miss:{}\n".format(blockId))
        # self.prefetch_q.append((blockId,0)) # いや、これはもうすでに取ってあるから今から取りに行ったってもう意味ないのよ。
        # self.gonnaPrefetchSet.add(blockId)
        self.prefetchedSet.add(blockId)

    def InformL4MissByPref(self,blockId):
        print("L3 Prefetcher missed L4 and brought from disk:{}\n",blockId)

    def clearQueue(self):
        while not self.prefetch_q_empty():
            blockId = self.pop_front()
            self.gonnaPrefetchSet.discard(blockId)
 
    def InformUserPoint(self,blockId):
        pass




