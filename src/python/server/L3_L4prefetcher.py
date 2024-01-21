from collections import deque
import asyncio
import numpy as np
import threading
import time
from slice import Slicer
from slice import TileDBSlicer
from compressor import compressor
import queue

class L3Prefetcher:

    # コンストラクタ
    def __init__(self,L3Cache,L4Cache,L4Prefetcher,dataDim, userUsingGPU,userUsingStorage,blockOffset=256, targetTol=0.1) -> None:

        self.userUsingGPU = userUsingGPU
        self.userUsingStorage = userUsingStorage
        self.dataDim = dataDim
        self.maxTimestep = dataDim[0]
        self.maxX = dataDim[1]
        self.maxY = dataDim[2]
        self.maxZ = dataDim[3]
        self.blockOffset = blockOffset
        self.L3Cache = L3Cache
        self.L4Cache = L4Cache
        self.TargetTol = targetTol

        # L3PrefetcherとL4Prefetcherで別々のもの持ってないと片方が一生使えなくなる->そんなことはないっぽいけど、別々に持ってた方がいい性能が出るんだよね。
        self.Slicer = TileDBSlicer(blockOffset=blockOffset)
        self.compressor = compressor(self.L3Cache) # 0 for a100 40G 1 for a100 80G
        self.L4Pref = L4Prefetcher

        # 取りに行く予定があるブロックのセット (重複を避けるために)
        self.gonnaPrefetchSet = set()

        # すでに取ってきたブロックのセット
        self.prefetchedSet = set()

        # 取りに行く予定があるブロックが順番に入っているセット。
        self.prefetch_q = deque() 
        self.thread = None

        # tol = 0.1の場合は、大体圧縮率が25倍なので、25倍はいるってことですね。
        self.estimatedCompratio = 25 # when tol = 0.1の時
        self.radius = self.getRadiusFromCapacity()

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

        # for stats
        self.numPrefetches = 0
        self.numL4Hits = 0
############### 初期化系のメソッド ###########
            
    def startPrefetching(self):
        self.stop_thread = False
        if self.L3Cache.capacityInMiB > 0:
            self.thread = threading.Thread(target=self.thread_func)
            self.thread.start()
            self.numPrefetches = 0
            self.numL4Hits = 0
            self.enqueue_first_blockId()
            print("restarted L3 prefetcher!")
        else :
            print("L3 cache size is 0. So L3 prefetcher is not starting")

    # プリフェッチスレッドを停止
    def stop(self):
        self.stop_thread = True
        # return {"numPrefetch":self.numPrefetches,"numL4Hits":self.numL4Hits}

    def InitializeSetting(self,blockOffset,targetTol):
        self.Slicer.changeBlockSize(blockOffset)
        self.prefetchedSet = set()
        self.gonnaPrefetchSet = set()
        self.prefetch_q = deque()
        self.blockOffset = blockOffset
        self.TargetTol = float(targetTol)
        self.radius = self.getRadiusFromCapacity()*self.estimatedCompratio

    def changeBlockOffset(self,blockOffset):
        self.blockOffset = blockOffset        

    def getRadiusFromCapacity(self):
        capacityInMiB = self.L3Cache.capacityInMiB*self.estimatedCompratio # 実際の容量
        OneElementSizeInByte = 4
        blockSizeInByte = OneElementSizeInByte*self.blockOffset**3
        radius = 0
        print(f"capacityInMiB = {capacityInMiB},blockSizeInByte={blockSizeInByte}")
        while((2*radius+1)**3 +2 <= capacityInMiB*1024*1024/blockSizeInByte):
            radius += 1
        print(f"L3 caches radius={radius}")
        return radius


############### プリフェッチ系のメソッド ################

    async def fetchLoop(self):
        while not self.stop_thread:
            if (not self.prefetch_q_empty()) and (self.L3Cache.usedSizeInMiB < self.L3Cache.capacityInMiB) and (not self.userUsingGPU.is_locked() and (not self.userUsingStorage.is_locked())):
                
                # print("L3 PREFETCHER IS READING FROM STORAGE")
                nextBlockId,distance = self.pop_front()

                if distance > self.radius: # このdistanceを一回一回更新した方がいいのではないか？てか、これを優先度つきのキューで持ちたいんだが。
                    print("the block in the prefetch queue is no more needed")
                    continue

                self.numPrefetches += 1
                original = self.L4Cache.get(nextBlockId)
                if original is None:
                    
                    try:
                        # L4のプリフェッチ予定から削除
                        self.L4Pref.prefetch_q.remove(nextBlockId)
                        print("succeed in deleting {} in L4's prefetch Q".format(nextBlockId))
                    except Exception as e:
                        pass

                    d = self.Slicer.sliceData(nextBlockId)
                    self.L4Cache.put(nextBlockId,d) # write to L4 also (inclusive)
                    tol = self.TargetTol
                    compressed = self.compressor.compress(d,tol)
                    self.L3Cache.put(nextBlockId,compressed)
                else:
                    self.numL4Hits
                    print("L4 HIT! when L3 Prefetching from L4",nextBlockId,"distance:",distance)
                    tol = self.TargetTol
                    compressed = self.compressor.compress(original,tol)
                    print("compressed size : {}".format(compressed.nbytes/1024/1024))
                    self.L3Cache.put(nextBlockId,compressed)
                self.prefetchedSet.add(nextBlockId)
                self.enque_neighbor_blocks(nextBlockId,distance)

            else:
                print("L3: Queue empty?={}, Cache full?={}, GPU locked = {}, Storage locked={}".format(
                    self.prefetch_q_empty(),
                    self.L3Cache.usedSizeInMiB >= self.L3Cache.capacityInMiB,
                    self.userUsingGPU.is_locked(),
                    self.userUsingStorage.is_locked()
                ))
                await asyncio.sleep(0.05)  # Sleep for 1 second, or adjust as needed
    

    # 距離パラメータを追加すればいいと思います！
    def enque_neighbor_blocks(self,centerBlock,d):
        tol = self.TargetTol
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

    def enque_neighbor_blocks_to_front(self,centerBlock,d):
        tol = self.TargetTol
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
                self.prefetch_q.appendleft(((tol,timestep+dt, x, y, z),distance))
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
                        self.prefetch_q.appendleft(((tol,timestep, x+dx, y+dy, z+dz),distance))
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
    
    def InformL3MissAndL4Hit(self,blockId):
        print("L3Miss and L4 Hit")
    
    def InformL3MissAndL4Miss(self,blockId):
        print("L3 Missed and L4 Miss:{}\n".format(blockId))
        self.prefetchedSet.add(blockId)

    def InformL4MissByPref(self,blockId):
        print("L3 Prefetcher missed L4 and brought from disk:{}\n",blockId)

    def InformUserPoint(self,blockId):
        print(f"L3 : user is at{blockId}")
        start = time.time()
        self.evict(blockId)
        self.updatePrefetchQ(blockId)
        end = time.time()
        print("L3 : time to update cache info {}".format(
            end - start
        ))

    # ここ結構時間かかりそうだけど、大丈夫？
    def evict(self,userPoint):
        # キャッシュの要素を取り出していく。
        for blockId in self.L3Cache.cache.keys():
            hops = self.calHops(userPoint,blockId)
            if (hops > self.radius) and self.L3Cache.isCacheFull():
                print(f"L3 pref evicting block : {blockId}")
                self.L3Cache.evict_a_block(blockId)
                self.prefetchedSet.discard(blockId)

    # ユーザの位置が知らされるたびにこれを実行する。内容は簡単。
    def updatePrefetchQ(self,userPoint):
        self.enque_neighbor_blocks_to_front(userPoint,0) # でいんじゃね？って思った。
    
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
    def __init__(self,L4Cache,dataDim,blockSize,userUsingGPU,userUsingStorage,targetTol = 0.1):
        # user is coming flag
        self.userUsingGPU = userUsingGPU
        self.userUsingStorage = userUsingStorage
        self.L4Cache = L4Cache
        # self.Slicer = Slicer(blockOffset=blockSize)
        self.Slicer = TileDBSlicer(blockOffset=blockSize)
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
        self.userPoint = None

        # ここで、頑張って変えてください。
        self.TargetTol = targetTol


        # 計算式が間違っているか、そんな気がする。
        self.radius = self.getRadiusFromCapacity() 

        # フェッチループ起動
        if self.L4Cache.capacityInMiB == 0:
            print("Not starting L4 Prefetcher because the capacity size is 0")
            pass
        else :
            print("start L4 prefetcher")
            self.thread = threading.Thread(target=self.thread_func)
            self.thread.start()
            self.enqueue_first_blockId()

        # for stats
        self.numPrefetches = 0
    ####################### 初期化系メソッド ###########################
            
    def getRadiusFromCapacity(self):
        capacityInMiB = self.L4Cache.capacityInMiB
        OneElementSizeInByte = 4
        blockSizeInByte = OneElementSizeInByte*self.blockOffset**3
        radius = 0
        print(f"capacityInMiB = {capacityInMiB},blockSizeInByte={blockSizeInByte}")
        while((2*radius+1)**3 +2 <= capacityInMiB*1024*1024/blockSizeInByte):
            radius += 1
        print(f"L4 caches radius={radius}")
        return radius

    def startPrefetching(self):
        self.stop_thread = False
        if self.L4Cache.capacityInMiB > 0:
            self.thread = threading.Thread(target=self.thread_func)
            self.thread.start()
            self.numPrefetches = 0
            print("Restarted L4 prefetcher")
        else :
            print("L4 cache size is 0 so L4 prefetcher is not starting")
        
    def changeBlockOffset(self,blockOffset):
        self.blockOffset = blockOffset

    # プリフェッチスレッドを停止するメソッド
    def stop(self):
        self.stop_thread = True
        # return {"numPrefetch":self.numPrefetches}

    def InitializeSetting(self,blockOffset,targetTol):
        self.Slicer.changeBlockSize(blockOffset)
        self.prefetchedSet = set()
        self.gonnaPrefetchSet = set()
        self.prefetch_q = deque()
        self.TargetTol = float(targetTol)
        self.blockOffset = blockOffset
        self.radius = 10 #self.getRadiusFromCapacity()

    ######################## フェッチスレッド用メソッド #########################
    
    # 別スレッドで実行される本体
    async def fetchLoop(self):

        while not self.stop_thread:
            self.L4Cache.printInfo()

            # print(f"target tol is ={self.TargetTol}")

            # ここで帯域幅の奪い合いが生じる。どうする！
            if (not self.prefetch_q_empty()) and (self.L4Cache.usedSizeInMiB <  self.L4Cache.capacityInMiB) and (not self.userUsingStorage.is_locked()):
                nextBlockId,distance = self.pop_front()
                # distanceがいらない説が出てきた。
                # というのも、distanceは、キューに入れられた時点でのuserとの距離なわけじゃないですか。
                # その代わり、ユーザの位置はクラス内で持っておく必要がある気がしてきた。
                if distance > self.radius:
                    continue
                self.numPrefetches += 1
                data = self.Slicer.sliceData(nextBlockId)
                self.L4Cache.put(nextBlockId,data)
                self.prefetchedSet.add(nextBlockId)
                self.enque_neighbor_blocks(nextBlockId,distance)
            else:
                # print("L4: Queue empty?={}, Cache full?={}, Storage locked={}".format(
                #     self.prefetch_q_empty(),
                #     self.L4Cache.usedSizeInMiB >= self.L4Cache.capacityInMiB,
                #     self.userUsingStorage.is_locked()
                # ))
                await asyncio.sleep(0.05)  # Sleep for 1 second, or adjust as needed
                
                
    
    # 実際はここで実行される
    def thread_func(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.fetchLoop())    

    # TODO forループの順番。時間方向か、空間、どちらを優先的に取ってくるのか
    def enque_neighbor_blocks(self,centerBlock,d):
        tol = self.TargetTol# centerBlock[0] 
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

    def enque_neighbor_blocks_to_front(self,centerBlock,d):
        tol = self.TargetTol # centerBlock[0] 
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
                self.prefetch_q.appendleft(((tol,timestep+dt, x, y, z),distance))
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
                        self.prefetch_q.appendleft(((tol,timestep, x+dx, y+dy, z+dz),distance))
                        self.gonnaPrefetchSet.add((tol,timestep, x+dx, y+dy, z+dz))

    ############ ミスをした時の挙動を決定するメソッド (ユーザからのミス) #################
                        
    def InformL3Hit(self,blockId):
        print("L3 hit! nice! from L4 prefetcher")
        pass

    def InformL3MissAndL4Hit(self,blockId):
        print("L3Miss and L4 Hit")
        # self.enque_neighbor_blocks_to_front(blockId,0)

    def InformL3MissAndL4Miss(self,blockId):
        print("L3 Miss and L4 Miss:{}\n".format(blockId))
        # self.prefetch_q.append((blockId,0)) # いや、これはもうすでに取ってあるから今から取りに行ったってもう意味ないのよ。
        # self.gonnaPrefetchSet.add(blockId)
        self.prefetchedSet.add(blockId)
        # self.clearQueue() # ここで結構時間食ってる説あるよね。
        # self.enque_neighbor_blocks_to_front(blockId,0)

    def InformL4MissByPref(self,blockId):
        print("L3 Prefetcher missed L4 and brought from disk:{}\n",blockId)

    # このメソッドは使いたくないのです。
    def clearQueue(self):
        while not self.prefetch_q_empty():
            blockId = self.pop_front()
            self.gonnaPrefetchSet.discard(blockId)                       

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

    def InformUserPoint(self,blockId):
        print(f"L4 : user is at{blockId}")
        self.userPoint = blockId
        start = time.time()
        self.evict(blockId)
        self.updatePrefetchQ(blockId)
        end = time.time()
        print(f"L4 : time to update cache info = {end - start}")

    # ここ結構時間かかりそうだけど、大丈夫？
    def evict(self,userPoint):
        # キャッシュの要素を取り出していく。
        for blockId,blockValue in self.L4Cache.cache.items():
            hops = self.calHops(userPoint,blockId)
            if (hops > self.radius) and self.L4Cache.isCacheFull():
                print(f"L4 pref evicting a block : {blockId}")
                self.L4Cache.evict_a_block(blockId)
                self.prefetchedSet.discard(blockId)

    # ユーザの位置が知らされるたびにこれを実行する。内容は簡単。
    def updatePrefetchQ(self,userPoint):
        self.enque_neighbor_blocks_to_front(userPoint,0) # でいんじゃね？って思った。




