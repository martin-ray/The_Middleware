from collections import deque
import asyncio
import threading
import numpy as np
from NetInterface import NetIF
from decompressor import Decompressor


class L2Prefetcher:

    def __init__(self,L2Cache,GPUmutex,maxTimestep=63,serverURL="http://172.20.2.253:8080",OnSwitch=True,targetTol= 0.1) -> None:
        
        self.URL = serverURL
        self.maxTimestep = maxTimestep
        self.maxX = 1024
        self.maxY = 1024
        self.maxZ = 1024
        self.blockOffset = 256
        self.L2Cache = L2Cache
        self.gonnaPrefetchSet = set()
        self.prefetchedSet = set()
        self.prefetch_q = deque() # blocks going to get
        self.Netif = NetIF(self.L2Cache,serverURL)
        self.stop_thread = False
        self.thread = None
        self.userPoint = None
        self.radius = 10

        self.targetTol = targetTol

        # GPUmutex
        self.GPUmutex = GPUmutex

        # ユーザのリクエストシーケンス
        self.RequestSequence = []

        # フェッチループを起動
        if self.L2Cache.capacityInMiB == 0 and OnSwitch == False:
            print("L2pref : Not start prefetching because L2 cache size is 0")
            pass
        else:
            self.thread = threading.Thread(target=self.thread_func)
            self.thread.start()

    ### 初期化系メソッド ###
    def startPrefetching(self):
        self.stop_thread = False
        if self.L2Cache.capacityInMiB > 0:
            self.thread = threading.Thread(target=self.thread_func)
            self.thread.start()
            # self.enqueue_first_blockId()
            print("restarted L2 prefetcher!")
        else :
            print("L2 cache size is 0. So L2 prefetcher is not starting")

    def stop(self):
        self.stop_thread = True

    def InitializeSetting(self,blockOffset):
        self.prefetchedSet = set()
        self.gonnaPrefetchSet = set()
        self.prefetch_q = deque()
        self.blockOffset = blockOffset
        self.RequestSequence = []

    def changeBlockOffset(self,blockOffset):
        self.blockOffset = blockOffset

    ### プリフェッチループ系メソッド ###
    async def fetchLoop(self):
        while not self.stop_thread:
            if (not self.prefetch_q_empty()) and (self.L2Cache.usedSizeInMiB < self.L2Cache.capacityInMiB):
                nextBlockId = self.prefetch_q.popleft()
                compressed = self.Netif.send_req_pref(nextBlockId)
                self.L2Cache.put(nextBlockId,compressed)
                self.enque_neighbor_blocks(nextBlockId) # ここ、あってるかもう一度確認してくれ。頼む。

            else:
                print(f"L1pref : prefetchQ empty? ={self.prefetch_q_empty()},cache has room ? ={self.L2Cache.usedSizeInMiB < self.L2Cache.capacityInMiB}")
                await asyncio.sleep(0.1)  # Sleep for 1 second, or adjust as needed

    def thread_func(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.fetchLoop())          

    def clearQueue(self): # 初期化に使われる
        while not self.prefetch_q_empty():
            blockId = self.prefetch_q.popleft()
            self.gonnaPrefetchSet.discard(blockId)
            self.Netif.sendQ.clear()

    ### 置換、プリフェッチ系メソッド ### 
    def enque_neighbor_blocks(self,centerBlock): # 緊急を要さないプリフェッチリクエスト
            
            tol = self.targetTol # centerBlock[0] 
            timestep = centerBlock[1]
            x = centerBlock[2]
            y = centerBlock[3]
            z = centerBlock[4]

            # 時間方向に1つづれたブロックは1ホップ
            for dt in [-1,1]:
                if (self.gonnaPrefetchSet.__contains__((tol,timestep + dt, x, y, z))
                            or (timestep+dt < 0) or (timestep + dt >= self.maxTimestep)):
                    continue
                else:
                    self.prefetch_q.append((tol,timestep + dt, x, y, z))
                    self.gonnaPrefetchSet.add((tol,timestep+dt, x, y, z))  

            for dx in [-self.blockOffset, 0, self.blockOffset]:
                for dy in [-self.blockOffset, 0, self.blockOffset]:
                    for dz in [-self.blockOffset, 0, self.blockOffset]:
                        if (self.gonnaPrefetchSet.__contains__((tol,timestep, x + dx, y + dy, z + dz))
                            or (x + dx < 0) or (x + dx >= self.maxX)
                            or (y + dy < 0) or (y + dy >= self.maxY)
                            or (z + dz < 0) or (z + dz >= self.maxZ)):
                            continue
                        else:
                            self.prefetch_q.append((tol,timestep, x + dx, y + dy, z + dz))
                            self.gonnaPrefetchSet.add((tol,timestep, x + dx, y + dy, z + dz))


    def enque_neighbor_blocks_to_front(self,centerBlock):
        
        tol = self.targetTol 
        timestep = centerBlock[1]
        x = centerBlock[2]
        y = centerBlock[3]
        z = centerBlock[4]

        # 時間方向に1つづれたブロックは1ホップ
        for dt in [-1, 1]:
            if (self.gonnaPrefetchSet.__contains__((tol,timestep+dt, x, y, z))): # 先頭に持ってくる
                self.prefetch_q.remove((tol,timestep+dt, x, y, z))
                self.prefetch_q.appendleft((tol,timestep+dt, x, y, z))
            elif (timestep+dt < 0) or (timestep+dt >= self.maxTimestep):
                continue
            else:
                self.prefetch_q.appendleft((tol,timestep+dt, x, y, z))
                self.gonnaPrefetchSet.add((tol,timestep+dt, x, y, z))  

        for dx in [-self.blockOffset, 0, self.blockOffset]:
            for dy in [-self.blockOffset, 0, self.blockOffset]:
                for dz in [-self.blockOffset, 0, self.blockOffset]:
                    if (self.gonnaPrefetchSet.__contains__((tol,timestep, x+dx, y+dy, z+dz))):
                        self.prefetch_q.remove((tol,timestep, x+dx, y+dy, z+dz))
                        self.prefetch_q.appendleft((tol,timestep, x+dx, y+dy, z+dz))

                    elif ((x + dx < 0) or (x + dx >= self.maxX)
                        or (y + dy < 0) or (y + dy >= self.maxY)
                        or (z + dz < 0) or (z + dz >= self.maxZ)): # 範囲外
                        continue

                    else:
                        self.prefetch_q.appendleft((tol, timestep, x + dx, y + dy, z + dz))
                        self.gonnaPrefetchSet.add((tol,timestep, x + dx, y + dy, z + dz))
                        

    def prefetch_q_empty(self):
        if(len(self.prefetch_q) == 0):
            return True
        else:
            return False

    def calHops(self,centerBlockId,targetBlockId):
        timeHops = abs(centerBlockId[1]-targetBlockId[1])
        xHops = abs(centerBlockId[2]- targetBlockId[2])
        yHops = abs(centerBlockId[3]- targetBlockId[3])
        zHops = abs(centerBlockId[4]- targetBlockId[4])
        spaceHops = max(xHops,yHops,zHops)//self.blockOffset
        return timeHops + spaceHops

    def InformUserPoint(self,blockId):
        self.RequestSequence.append(blockId)
        self.userPoint = blockId
        self.cal_move_vector_and_prefetch()
        self.update_cache(blockId)
        self.updatePrefetchQ(blockId)

    def update_cache(self,userPoint):
        for blockId in self.L2Cache.cache.keys():
            hops = self.calHops(userPoint,blockId)
            if (hops > self.radius) and self.L2Cache.isCacheFull():
                self.L2Cache.evict_a_block(blockId)
                self.prefetchedSet.discard(blockId)

    # ユーザの位置が知らされるたびにこれを実行.ユーザの位置の周りのブロックをプリフェッチ対象に追加
    def updatePrefetchQ(self,userPoint):
        self.enque_neighbor_blocks_to_front(userPoint) # でいんじゃね？って思った。


    # 方向ベクトルの計算
    def cal_move_vector_and_prefetch(self,numSeq=3,fetch_nums = 5): # numSeq : ラストnumSeq個のnumSeqから、方向を算出
        print("here in cal_move_vector")
        latest_sequences = self.RequestSequence[-numSeq:] # 中身は、(tol,x,y,z) のtuple
        if len(latest_sequences) <= 2 :
            return # バグるので
        
        v1 = np.subtract(latest_sequences[2] - latest_sequences[1])
        v0 = np.subtract(latest_sequences[1] - latest_sequences[0])

        if (v1 == v0):
            # そっち方向のベクトルをfetch_numsこ、プリフェッチキューの先頭に入れさせていただきます。
            tol = self.targetTol
            timestep = self.userPoint[1]
            x = self.userPoint[2]
            y = self.userPoint[3]
            z = self.userPoint[4]
            
            dt = v1[1]
            dx = v1[2]
            dy = v1[3]
            dz = v1[4]

            for n in range(fetch_nums):
                if self.gonnaPrefetchSet.__contains__((tol,timestep + n*dt, x + n*dx, y + n*dy, z + n*dz)):
                    self.prefetch_q.remove((tol,timestep + n*dt, x + n*dx, y + n*dy, z + n*dz))
                    self.prefetch_q.appendleft((tol,timestep + n*dt, x + n*dx, y + n*dy, z + n*dz))
                else:
                    self.prefetch_q.appendleft((tol,timestep + n*dt, x + n*dx, y + n*dy, z + n*dz))
                    self.gonnaPrefetchSet.add((tol,timestep + n*dt, x + n*dx, y + n*dy, z + n*dz))

class L1Prefetcher:

    def __init__(self,L1Cache,L2Cache,GPUmutex,maxTimestep=9,offsetSize=256,OnSwitch=True, TargetTol= 0.1):

        self.L1Cache = L1Cache
        self.L2Cache = L2Cache
        self.decompressor = Decompressor(self.L1Cache)
        self.Netif = NetIF(self.L2Cache)
        
        self.maxTimestep = maxTimestep
        self.maxX = 1024
        self.maxY = 1024
        self.maxZ = 1024
        self.default_offset = offsetSize
        self.blockOffset = offsetSize
        
        self.gonnaPrefetchSet = set()
        self.prefetchedSet = set()
        self.prefetch_q = deque()
        self.stop_thread = False
        self.thread = None
        self.userPoint = None

        self.radius = self.getRadiusFromCapacity()

        self.targetTol = TargetTol

        # GPUのmutex
        self.GPUmutex = GPUmutex

        # ユーザのリクエストシーケンス
        self.RequestSequence = []

        # フェッチループ起動
        if self.L1Cache.capacityInMiB == 0 and OnSwitch == False:
            pass
        else:
            self.thread = threading.Thread(target=self.thread_func)
            self.thread.start()

    ### 初期化系のメソッド ###

    def startPrefetching(self):
        self.stop_thread = False
        if self.L3Cache.capacity > 0:
            self.thread = threading.Thread(target=self.thread_func)
            self.thread.start()
            print("L1pref : Start prefetching")
        else :
            print("L1pref : L1 cache size is 0 So L1 prefetcher is not starting")

    def stop(self):
        self.stop_thread = True

    def InitializeSetting(self,blockOffset):
        self.prefetchedSet = set()
        self.gonnaPrefetchSet = set()
        self.prefetch_q = deque()
        self.blockOffset = blockOffset
        self.RequestSequence = []

    def clearQueue(self):
        while not self.prefetch_q_empty():
            blockId = self.self.prefetch_q.popleft()
            self.gonnaPrefetchSet.discard(blockId)

    ### フェッチループ系のメソッド ###
    async def fetchLoop(self):

        while not self.stop_thread:

            if (not self.prefetch_q_empty()) and (self.L1Cache.usedSizeInMiB < self.L1Cache.capacityInMiB):

                nextBlockId = self.prefetch_q.popleft()
                compressed = self.L2Cache.get(nextBlockId)

                if compressed is None: # L2Miss
                    self.gonnaPrefetchSet.discard(nextBlockId) # 取りに行こうとしたけど、いけなかったので、取りに行く予定リストから出す

                else: # L2Hit
                    print("L1pref : prefetched from L2")
                    original = None
                    with self.GPUmutex:
                        original = self.decompressor.decompress(compressed)
                    self.L1Cache.put(nextBlockId,original)   

            else:
                print(f"L1pref : Stall prefetcing.prefetchQ empty? ={self.prefetch_q_empty()},cache has room ? ={self.L1Cache.usedSizeInMiB < self.L1Cache.capacityInMiB}")
                await asyncio.sleep(0.2)  

    def thread_func(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.fetchLoop())       


    ### 更新系メソッド ###

    def enque_neighbor_blocks(self,centerBlock): # 急を要さないプリフェッチリクエスト
            
            tol = self.targetTol  
            timestep = centerBlock[1]
            x = centerBlock[2]
            y = centerBlock[3]
            z = centerBlock[4]

            # 時間方向に1つづれたブロックは1ホップ
            for dt in [-1,1]:
                if (self.gonnaPrefetchSet.__contains__((tol,timestep+dt, x, y, z))
                            or (timestep + dt < 0) or (timestep + dt >= self.maxTimestep)):
                    continue
                else:
                    self.prefetch_q.append((tol, timestep + dt, x, y, z))
                    self.gonnaPrefetchSet.add((tol,timestep + dt, x, y, z))  

            for dx in [-self.blockOffset, 0, self.blockOffset]:
                for dy in [-self.blockOffset, 0, self.blockOffset]:
                    for dz in [-self.blockOffset, 0, self.blockOffset]:
                        if (self.gonnaPrefetchSet.__contains__((tol,timestep, x + dx, y + dy, z + dz))
                            or (x + dx < 0) or (x + dx >= self.maxX)
                            or (y + dy < 0) or (y + dy >= self.maxY)
                            or (z + dz < 0) or (z + dz >= self.maxZ)):
                            continue
                        else:
                            self.prefetch_q.append((tol,timestep, x + dx, y + dy, z + dz))
                            self.gonnaPrefetchSet.add((tol,timestep, x + dx, y + dy, z + dz))

    def enque_neighbor_blocks_to_front(self,centerBlock): # ここで、すでにgonnaPrefetchsetにはいってるからスルーされると見た。

        tol = self.targetTol
        timestep = centerBlock[1]
        x = centerBlock[2]
        y = centerBlock[3]
        z = centerBlock[4]

        # 時間方向に1つづれたブロックは1ホップ
        for dt in [-1, 1]:
            if (self.gonnaPrefetchSet.__contains__((tol,timestep+dt, x, y, z))): # 先頭に持ってくる
                self.prefetch_q.remove((tol,timestep+dt, x, y, z))
                self.prefetch_q.appendleft((tol,timestep+dt, x, y, z))
            elif (timestep+dt < 0) or (timestep+dt >= self.maxTimestep):
                continue
            else:
                self.prefetch_q.appendleft((tol,timestep+dt, x, y, z))
                self.gonnaPrefetchSet.add((tol,timestep+dt, x, y, z))  

        for dx in [-self.blockOffset, 0, self.blockOffset]:
            for dy in [-self.blockOffset, 0, self.blockOffset]:
                for dz in [-self.blockOffset, 0, self.blockOffset]:
                    if (self.gonnaPrefetchSet.__contains__((tol,timestep, x+dx, y+dy, z+dz))):
                        self.prefetch_q.remove((tol,timestep, x+dx, y+dy, z+dz))
                        self.prefetch_q.appendleft((tol,timestep, x+dx, y+dy, z+dz))

                    elif ((x + dx < 0) or (x + dx >= self.maxX)
                        or (y + dy < 0) or (y + dy >= self.maxY)
                        or (z + dz < 0) or (z + dz >= self.maxZ)): # 範囲外
                        continue

                    else:
                        self.prefetch_q.appendleft((tol, timestep, x + dx, y + dy, z + dz))
                        self.gonnaPrefetchSet.add((tol,timestep, x + dx, y + dy, z + dz))
                    
    
    def InformUserPoint(self,blockId):
        self.RequestSequence.append(blockId)
        self.userPoint = blockId
        self.cal_move_vector_and_prefetch()
        self.update_cache(blockId)
        self.updatePrefetchQ(blockId)
    
    def prefetch_q_empty(self):
        if(len(self.prefetch_q) == 0):
            return True
        else:
            return False

    # キャッシュの要素をひとつづつ見て、半径に収まらない場合は、捨てる
    def update_cache(self,userPoint):
        for blockId in self.L1Cache.cache.keys():
            hops = self.calHops(userPoint,blockId)
            if (hops > self.radius) and self.L1Cache.isCacheFull():
                print(f"L1pref : evicting {blockId}. distance with userPoint {userPoint} is {hops}")
                self.L1Cache.evict_a_block(blockId)
                self.prefetchedSet.discard(blockId)

    # ユーザの位置が知らされるたびにこれを実行.内容は簡単。
    def updatePrefetchQ(self,userPoint):
        self.enque_neighbor_blocks_to_front(userPoint,0) # でいんじゃね？って思った。

    def calHops(self,centerBlockId,targetBlockId):
        timeHops = abs(centerBlockId[1]-targetBlockId[1])
        xHops = abs(centerBlockId[2]- targetBlockId[2])
        yHops = abs(centerBlockId[3]- targetBlockId[3])
        zHops = abs(centerBlockId[4]- targetBlockId[4])
        spaceHops = max(xHops,yHops,zHops)//self.blockOffset # これでホップ数が出る
        return timeHops + spaceHops

    def getRadiusFromCapacity(self):
        capacityInMiB = self.L1Cache.capacityInMiB
        OneElementSizeInByte = 4
        blockSizeInByte = OneElementSizeInByte*self.blockOffset**3
        radius = 0
        print(f"capacityInMiB = {capacityInMiB},blockSizeInByte={blockSizeInByte}")
        while((2*radius+1)**3 +2 <= capacityInMiB*1024*1024/blockSizeInByte):
            radius += 1
        print(f"L1 caches radius={radius}")
        return radius
    
    # 方向ベクトルの計算
    def cal_move_vector_and_prefetch(self,numSeq=3,fetch_nums = 5): # numSeq : ラストnumSeq個のnumSeqから、方向を算出
        print("here in cal_move_vector")
        latest_sequences = self.RequestSequence[-numSeq:] # 中身は、(tol,x,y,z) のtuple
        if len(latest_sequences) <= 2 :
            return # バグるので
        
        v1 = np.subtract(latest_sequences[2] - latest_sequences[1])
        v0 = np.subtract(latest_sequences[1] - latest_sequences[0])

        if (v1 == v0):
            # そっち方向のベクトルをfetch_numsこ、プリフェッチキューの先頭に入れさせていただきます。
            tol = self.targetTol
            timestep = self.userPoint[1]
            x = self.userPoint[2]
            y = self.userPoint[3]
            z = self.userPoint[4]
            
            dt = v1[1]
            dx = v1[2]
            dy = v1[3]
            dz = v1[4]

            for n in range(fetch_nums):
                if self.gonnaPrefetchSet.__contains__((tol,timestep + n*dt, x + n*dx, y + n*dy, z + n*dz)):
                    self.prefetch_q.remove((tol,timestep + n*dt, x + n*dx, y + n*dy, z + n*dz))
                    self.prefetch_q.appendleft((tol,timestep + n*dt, x + n*dx, y + n*dy, z + n*dz))
                else:
                    self.prefetch_q.appendleft((tol,timestep + n*dt, x + n*dx, y + n*dy, z + n*dz))
                    self.gonnaPrefetchSet.add((tol,timestep + n*dt, x + n*dx, y + n*dy, z + n*dz))



         



