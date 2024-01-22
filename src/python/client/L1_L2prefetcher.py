from collections import deque
import asyncio
import threading
import numpy as np
from NetInterface import NetIF
from decompressor import Decompressor


class L2Prefetcher:

    def __init__(self,L2Cache,GPUmutex,maxTimestep=63,serverURL="http://172.20.2.253:8080",OnSwitch=True,targetTol= 0.1,n_vector_fetch=2) -> None:
        
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
        self.TargetTol = targetTol
        self.estimatedCompratios = {
            0.1 : 25,
            0.01 : 13,
            0.001 : 6,
            0.0001 : 4,
            0.00001 : 2
        }

        self.radius = self.getRadiusFromCapacity()
        
        self.n_vector_fetch = n_vector_fetch

  

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
    

    def getRadiusFromCapacity(self):
        capacityInMiB = self.L2Cache.capacityInMiB*self.estimatedCompratios[self.TargetTol] # 実際の容量
        OneElementSizeInByte = 4
        blockSizeInByte = OneElementSizeInByte*self.blockOffset**3
        radius = 0
        print(f"capacityInMiB = {capacityInMiB},blockSizeInByte={blockSizeInByte}")
        while((2*radius+1)**3 + 2 <= capacityInMiB*1024*1024/blockSizeInByte):
            radius += 1
        print(f"L3 caches radius={radius}")
        return radius
    

    ### プリフェッチループ系メソッド ###
    async def fetchLoop(self):
        
        while not self.stop_thread:
            
            if (not self.prefetch_q_empty()) and (self.L2Cache.usedSizeInMiB < self.L2Cache.capacityInMiB):

                nextBlockId = self.prefetch_q.popleft()
                compressed = self.Netif.send_req_pref(nextBlockId)
                self.L2Cache.put(nextBlockId,compressed)
                self.enque_neighbor_blocks(nextBlockId) # ここ、あってるかもう一度確認してくれ。頼む。

            else:
                print(f"L2pref : Stalling. PrefetchQ empty? ={self.prefetch_q_empty()},cache has room ? ={self.L2Cache.usedSizeInMiB < self.L2Cache.capacityInMiB}")
                await asyncio.sleep(0.1)  # Sleep for 1 second, or adjust as needed

    def thread_func(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.fetchLoop())          


    ### 置換、プリフェッチ系メソッド ### 
    def enque_neighbor_blocks(self,centerBlock): # 緊急を要さないプリフェッチリクエスト
            
            tol = self.TargetTol # centerBlock[0] 
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
        
        tol = self.TargetTol 
        timestep = centerBlock[1]
        x = centerBlock[2]
        y = centerBlock[3]
        z = centerBlock[4]

        # 時間方向に1つづれたブロックは1ホップ
        for dt in [-1, 1]:
            if (self.gonnaPrefetchSet.__contains__((tol,timestep+dt, x, y, z))): # 先頭に持ってくる
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
                        # self.prefetch_q.remove((tol,timestep, x+dx, y+dy, z+dz))
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

        print(f"L2pref : get informed userpoint : {blockId}")
        self.RequestSequence.append(blockId)
        self.userPoint = blockId
        if(self.cal_move_vector_and_prefetch()):
            self.update_cache(blockId)
        else:
            self.update_cache(blockId)
            self.updatePrefetchQ(blockId)


    def update_cache(self, userPoint):
        # print("L2pref : in update_cache method....")
        
        # Create a list of keys to iterate over
        keys_to_remove = []
        
        for blockId in self.L2Cache.cache.keys():
            hops = self.calHops(userPoint, blockId)
            # print(f"L3pref : {blockId} - {userPoint} = {hops} : radius : {self.radius}")
            
            if hops > self.radius:
                print(f"L2pref : evicting block : {blockId}")
                
                # Add the key to the list of keys to remove
                keys_to_remove.append(blockId)
        
        # Remove the keys from the dictionary and sets
        for blockId in keys_to_remove:
            self.L2Cache.evict_a_block(blockId)
            self.prefetchedSet.discard(blockId)
            self.gonnaPrefetchSet.discard(blockId)


    # ユーザの位置が知らされるたびにこれを実行.ユーザの位置の周りのブロックをプリフェッチ対象に追加
    def updatePrefetchQ(self,userPoint):
        self.enque_neighbor_blocks_to_front(userPoint) # でいんじゃね？って思った。


    # 方向ベクトルの計算
    def cal_move_vector_and_prefetch(self,numSeq=3): # numSeq : ラストnumSeq個のnumSeqから、方向を算出
        
        latest_sequences = self.RequestSequence[-numSeq:] # 中身は、(tol,x,y,z) のtuple
        if len(latest_sequences) <= 2 :
            return # バグ防止
        
        # print(f"Reqsequence : {self.RequestSequence}")
        v1 = np.subtract(latest_sequences[2],latest_sequences[1])
        v0 = np.subtract(latest_sequences[1],latest_sequences[0])

        if (np.array_equal(v1, v0)):
            # そっち方向のベクトルをfetch_numsこ、プリフェッチキューの先頭に入れさせていただきます。
            tol = self.TargetTol
            timestep = self.userPoint[1]
            x = self.userPoint[2]
            y = self.userPoint[3]
            z = self.userPoint[4]
            
            dt = int(v1[1])
            dx = int(v1[2])
            dy = int(v1[3])
            dz = int(v1[4])

            # print(f"v1 : {v1}, v0 : {v0}")
            # print(f"dt:{dt},dx:{dx},dy:{dy},dz:{dz}")

            for n in range(1,self.n_vector_fetch + 1):
                # print(f"L2pref : vector prefetch : {(tol,timestep + n*dt, x + n*dx, y + n*dy, z + n*dz)}")
                
                if ((timestep + n*dt < 0 or timestep + n*dt > self.maxTimestep ) or 
                    (x + n*dx < 0 or x + n*dx > self.maxX) or 
                    (y + n*dy < 0 or y + n*dy > self.maxY) or 
                    (z + n*dz < 0 or z + n*dz > self.maxZ)):
                    continue

                elif self.prefetchedSet.__contains__((tol,timestep + n*dt, x + n*dx, y + n*dy, z + n*dz)):
                    continue # もうとってきていた

                elif self.gonnaPrefetchSet.__contains__((tol,timestep + n*dt, x + n*dx, y + n*dy, z + n*dz)):
                    self.prefetch_q.appendleft((tol,timestep + n*dt, x + n*dx, y + n*dy, z + n*dz))
                else:

                    self.prefetch_q.appendleft((tol,timestep + n*dt, x + n*dx, y + n*dy, z + n*dz))
                    self.gonnaPrefetchSet.add((tol,timestep + n*dt, x + n*dx, y + n*dy, z + n*dz))
                
            return True
        else:
            return False


class L1Prefetcher:

    def __init__(self,L1Cache,L2Cache,GPUmutex,maxTimestep=9,offsetSize=256,OnSwitch=True, TargetTol= 0.1, n_vector_fetch=2):

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

        self.TargetTol = TargetTol

        # GPUのmutex
        self.GPUmutex = GPUmutex

        # ユーザのリクエストシーケンス
        self.RequestSequence = []
        self.n_vector_fetch = n_vector_fetch

        # フェッチループ起動
        if self.L1Cache.capacityInMiB == 0 :
            pass
        else:
            self.thread = threading.Thread(target=self.thread_func)
            self.thread.start()

    ### 初期化系のメソッド ###

    def startPrefetching(self):
        self.stop_thread = False
        if self.L1Cache.capacity > 0:
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
            
            tol = self.TargetTol  
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

        tol = self.TargetTol
        timestep = centerBlock[1]
        x = centerBlock[2]
        y = centerBlock[3]
        z = centerBlock[4]

        # 時間方向に1つづれたブロックは1ホップ
        for dt in [-1, 1]:
            if (self.gonnaPrefetchSet.__contains__((tol,timestep+dt, x, y, z))): # 先頭に持ってくる
                # self.prefetch_q.remove((tol,timestep+dt, x, y, z))
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
                        # self.prefetch_q.remove((tol,timestep, x+dx, y+dy, z+dz))
                        self.prefetch_q.appendleft((tol,timestep, x+dx, y+dy, z+dz))

                    elif ((x + dx < 0) or (x + dx >= self.maxX)
                        or (y + dy < 0) or (y + dy >= self.maxY)
                        or (z + dz < 0) or (z + dz >= self.maxZ)): # 範囲外
                        continue

                    else:
                        self.prefetch_q.appendleft((tol, timestep, x + dx, y + dy, z + dz))
                        self.gonnaPrefetchSet.add((tol,timestep, x + dx, y + dy, z + dz))
                    
    ## キーとなるメソッド
    def InformUserPoint(self,blockId):
        print(f"L1pref : get informed userpoint : {blockId}")
        self.RequestSequence.append(blockId)
        self.userPoint = blockId
        if(self.cal_move_vector_and_prefetch()):
            self.update_cache(blockId)
        else:
            self.update_cache(blockId)
            self.updatePrefetchQ(blockId)
        
    
    def prefetch_q_empty(self):
        if( len(self.prefetch_q) == 0 ):
            return True
        else:
            return False

    # キャッシュの要素をひとつづつ見て、半径に収まらない場合は、捨てる
    def update_cache(self, userPoint):
        print("L1pref : in update_cache method....")
        
        # Create a list of keys to iterate over
        keys_to_remove = []
        
        for blockId in self.L1Cache.cache.keys():
            hops = self.calHops(userPoint, blockId)
            # print(f"L1pref : {blockId} - {userPoint} = {hops} : radius : {self.radius}")
            
            if hops > self.radius:
                print(f"L1pref : evicting block : {blockId}")
                
                # Add the key to the list of keys to remove
                keys_to_remove.append(blockId)
        
        # Remove the keys from the dictionary and sets
        for blockId in keys_to_remove:
            self.L1Cache.evict_a_block(blockId)
            self.prefetchedSet.discard(blockId)
            self.gonnaPrefetchSet.discard(blockId)


    # ユーザの位置が知らされるたびに、これか、vector_prefetchを実行
    def updatePrefetchQ(self,userPoint):
        self.enque_neighbor_blocks_to_front(userPoint) # でいんじゃね？って思った。


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
    def cal_move_vector_and_prefetch(self,numSeq=3): # numSeq : ラストnumSeq個のnumSeqから、方向を算出
        
        latest_sequences = self.RequestSequence[-numSeq:] # 中身は、(tol,x,y,z) のtuple
        if len(latest_sequences) <= 2 :
            return # バグ防止
        
        # print(f"Reqsequence : {self.RequestSequence}")
        v1 = np.subtract(latest_sequences[2],latest_sequences[1])
        v0 = np.subtract(latest_sequences[1],latest_sequences[0])

        if (np.array_equal(v1, v0)):
            # そっち方向のベクトルをfetch_numsこ、プリフェッチキューの先頭に入れさせていただきます。
            tol = self.TargetTol
            timestep = self.userPoint[1]
            x = self.userPoint[2]
            y = self.userPoint[3]
            z = self.userPoint[4]
            
            dt = int(v1[1])
            dx = int(v1[2])
            dy = int(v1[3])
            dz = int(v1[4])

            # print(f"v1 : {v1}, v0 : {v0}")
            # print(f"dt:{dt},dx:{dx},dy:{dy},dz:{dz}")

            for n in range(1,self.n_vector_fetch + 1):
                # print(f"L1pref : vector prefetch : {(tol,timestep + n*dt, x + n*dx, y + n*dy, z + n*dz)}")
                
                if ((timestep + n*dt < 0 or timestep + n*dt > self.maxTimestep ) or 
                    (x + n*dx < 0 or x + n*dx > self.maxX) or 
                    (y + n*dy < 0 or y + n*dy > self.maxY) or 
                    (z + n*dz < 0 or z + n*dz > self.maxZ)):
                    continue

                elif self.prefetchedSet.__contains__((tol,timestep + n*dt, x + n*dx, y + n*dy, z + n*dz)):
                    continue # もうとってきていた

                elif self.gonnaPrefetchSet.__contains__((tol,timestep + n*dt, x + n*dx, y + n*dy, z + n*dz)):
                    self.prefetch_q.appendleft((tol,timestep + n*dt, x + n*dx, y + n*dy, z + n*dz))
                else:

                    self.prefetch_q.appendleft((tol,timestep + n*dt, x + n*dx, y + n*dy, z + n*dz))
                    self.gonnaPrefetchSet.add((tol,timestep + n*dt, x + n*dx, y + n*dy, z + n*dz))
                
            return True
        else:
            return False
         



