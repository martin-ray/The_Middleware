from collections import deque
import asyncio
import numpy as np
import threading
from slice import TileDBSlicer
from compressor import compressor

class L3Prefetcher:

    def __init__(self,L3Cache,L4Cache,L4Prefetcher,dataDim, userUsingGPU,userUsingStorage,blockOffset=256, targetTol=0.1 ,n_vector_fetch = 2) -> None:

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
        self.userPoint = None
        self.n_vector_fetch = n_vector_fetch

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

        self.radius = 3 #self.getRadiusFromCapacity()
        self.estimatedCompratios = {
            0.1 : 25,
            0.01 : 13,
            0.001 : 6,
            0.0001 : 4,
            0.00001 : 2
        }

        # スレッドを止めるためのフラグ
        self.stop_thread = False

        # ユーザのリクエストシーケンス
        self.RequestSequence = []

        # フェッチループを起動
        if self.L3Cache.capacityInMiB == 0:
            # L3キャッシュが0の時はL3Prefetcherはスタートしない
            pass
        else :
            print("start L3 prefetcher")
            self.thread = threading.Thread(target=self.thread_func)
            self.thread.start()

        # for stats
        self.numPrefetches = 0
        self.numL4Hits = 0


    ### 初期化系のメソッド ###    
    def startPrefetching(self):
        self.stop_thread = False
        if self.L3Cache.capacityInMiB > 0:
            self.thread = threading.Thread(target=self.thread_func)
            self.thread.start()
            self.numPrefetches = 0
            self.numL4Hits = 0
            print("restarted L3 prefetcher!")
        else :
            print("L3 cache size is 0. So L3 prefetcher is not starting")

    # プリフェッチスレッドを停止
    def stop(self):
        self.stop_thread = True

    def InitializeSetting(self,blockOffset,targetTol):
        self.Slicer.changeBlockSize(blockOffset)
        self.prefetchedSet = set()
        self.gonnaPrefetchSet = set()
        self.prefetch_q = deque()
        self.blockOffset = blockOffset
        self.TargetTol = float(targetTol)
        self.radius = self.getRadiusFromCapacity()
        self.RequestSequence = []

    def changeBlockOffset(self,blockOffset):
        self.blockOffset = blockOffset        

    def getRadiusFromCapacity(self):
        capacityInMiB = self.L3Cache.capacityInMiB*self.estimatedCompratios[self.TargetTol] # 実際の容量
        OneElementSizeInByte = 4
        blockSizeInByte = OneElementSizeInByte*self.blockOffset**3
        radius = 0
        print(f"capacityInMiB = {capacityInMiB},blockSizeInByte={blockSizeInByte}")
        while((2*radius+1)**3 +2 <= capacityInMiB*1024*1024/blockSizeInByte):
            radius += 1
        print(f"L3 caches radius={radius}")
        return radius


    ### プリフェッチ系のメソッド ###

    async def fetchLoop(self):

        while not self.stop_thread:

            if (not self.prefetch_q_empty()) and (self.L3Cache.usedSizeInMiB < self.L3Cache.capacityInMiB) and (not self.userUsingGPU.is_locked() and (not self.userUsingStorage.is_locked())):
                


                nextBlockId = self.prefetch_q.popleft()
                distance = self.calHops(self.userPoint,nextBlockId)
                # print(f"L3pref : Prefetching {nextBlockId}. distance : {distance}")

                if distance > self.radius: 
                    # print("L3pref : The distance between userPoint and going to prefetch block is more than cache radius")
                    continue

                if self.prefetchedSet.__contains__(nextBlockId):
                    # print(f"L3pref : skipping {nextBlockId}")
                    continue
                    
                self.numPrefetches += 1
                original = self.L4Cache.get(nextBlockId)
                
                if original is None:    
                    try:
                        # L4のプリフェッチ予定から削除
                        self.L4Pref.prefetch_q.remove(nextBlockId)
                        # print("succeed in deleting {} in L4's prefetch Q".format(nextBlockId))
                    except Exception as e:
                        pass

                    d = self.Slicer.sliceData(nextBlockId)
                    self.L4Cache.put(nextBlockId,d) # write to L4 also (inclusive)
                    tol = self.TargetTol
                    compressed = self.compressor.compress(d,tol)
                    self.L3Cache.put(nextBlockId,compressed)
                else:
                    tol = self.TargetTol
                    compressed = self.compressor.compress(original,tol)
                    self.L3Cache.put(nextBlockId,compressed)
                self.prefetchedSet.add(nextBlockId)
                self.enque_neighbor_blocks(nextBlockId)

            else:
                print("L3: Queue empty?={}, Cache full?={}, GPU locked = {}, Storage locked={}".format(
                    self.prefetch_q_empty(),
                    self.L3Cache.usedSizeInMiB >= self.L3Cache.capacityInMiB,
                    self.userUsingGPU.is_locked(),
                    self.userUsingStorage.is_locked()
                ))
                await asyncio.sleep(0.05)  # Sleep for 1 second, or adjust as needed
    

    def enque_neighbor_blocks(self,centerBlock):

        tol = self.TargetTol
        timestep = centerBlock[1]
        x = centerBlock[2]
        y = centerBlock[3]
        z = centerBlock[4]

        # 時間方向に1つづれたブロックは1ホップ
        for dt in [-1,1]:
            if (self.gonnaPrefetchSet.__contains__((tol,timestep+dt, x, y, z))
                        or (timestep+dt < 0) or (timestep+dt >= self.maxTimestep)):
                continue
            else:
                self.prefetch_q.append((tol,timestep + dt, x, y, z))
                self.gonnaPrefetchSet.add((tol,timestep + dt, x, y, z))  

        for dx in [-self.blockOffset, 0, self.blockOffset]:
            for dy in [-self.blockOffset, 0, self.blockOffset]:
                for dz in [-self.blockOffset, 0, self.blockOffset]:
                    if (self.gonnaPrefetchSet.__contains__((tol, timestep, x + dx, y + dy, z + dz))
                        or (x + dx < 0) or (x + dx >= self.maxX)
                        or (y + dy < 0) or (y+dy >= self.maxY)
                        or (z + dz < 0) or (z+dz >= self.maxZ)):
                        continue
                    else:
                        self.prefetch_q.append((tol, timestep, x + dx, y + dy, z + dz))
                        self.gonnaPrefetchSet.add((tol,timestep, x + dx, y + dy, z + dz))

    def enque_neighbor_blocks_to_front(self,centerBlock):
        
        tol = self.TargetTol
        timestep = centerBlock[1]
        x = centerBlock[2]
        y = centerBlock[3]
        z = centerBlock[4]

        # 時間方向に1つづれたブロックは1ホップ
        for dt in [-1,1]:
            if self.gonnaPrefetchSet.__contains__((tol,timestep + dt, x, y, z)):
                self.prefetch_q.appendleft((tol,timestep+dt, x, y, z))
            elif((timestep+dt < 0) or (timestep+dt >= self.maxTimestep)):
                continue
            else:
                self.prefetch_q.appendleft((tol,timestep+dt, x, y, z))
                self.gonnaPrefetchSet.add((tol,timestep+dt, x, y, z))  

        for dx in [-self.blockOffset, 0, self.blockOffset]:
            for dy in [-self.blockOffset, 0, self.blockOffset]:
                for dz in [-self.blockOffset, 0, self.blockOffset]:
                    if self.gonnaPrefetchSet.__contains__((tol,timestep, x + dx, y + dy, z + dz)):
                        self.prefetch_q.appendleft((tol,timestep, x + dx, y + dy, z + dz))
                        pass
                    elif ((x + dx < 0) or (x + dx >= self.maxX)
                        or (y + dy < 0) or (y + dy >= self.maxY)
                        or (z + dz < 0) or (z + dz >= self.maxZ)):
                        continue
                    else:
                        self.prefetch_q.appendleft((tol,timestep, x + dx, y + dy, z + dz))
                        self.gonnaPrefetchSet.add((tol,timestep, x + dx, y + dy, z + dz))
                        
    def prefetch_q_empty(self):
        if(len(self.prefetch_q) == 0):
            return True
        else:
            return False
        
    def print_prefetch_q(self):
        print(self.prefetch_q)

    # ブロック間の距離はシェビチェフ距離で計算。時間方向は足し算。
    def calHops(self,centerBlockId,targetBlockId):
        timeHops = abs(centerBlockId[1] - targetBlockId[1])
        xHops = abs(centerBlockId[2] - targetBlockId[2])
        yHops = abs(centerBlockId[3] - targetBlockId[3])
        zHops = abs(centerBlockId[4] - targetBlockId[4])
        spaceHops = max(xHops,yHops,zHops) // self.blockOffset
        return timeHops + spaceHops
    
    def InformL3MissAndL4Miss(self,blockId): # これは必要。
        print("L3 Missed and L4 Miss:{}\n".format(blockId))
        self.prefetchedSet.add(blockId)


    def InformUserPoint(self,userPoint):
        print(f"L3pref : get informed userpoint : {userPoint}")
        self.RequestSequence.append(userPoint)
        self.userPoint = userPoint
        if(self.cal_move_vector_and_prefetch()):
            self.update_cache(userPoint)
        else:
            self.update_cache(userPoint)
            self.updatePrefetchQ(userPoint)


    def update_cache(self, userPoint):
        print("L3pref : in update_cache method....")
        
        # Create a list of keys to iterate over
        keys_to_remove = []
        
        for blockId in self.L3Cache.cache.keys():
            hops = self.calHops(userPoint, blockId)
            # print(f"L3pref : {blockId} - {userPoint} = {hops} : radius : {self.radius}")
            
            if hops > self.radius:
                print(f"L3pref : evicting block : {blockId}")
                
                # Add the key to the list of keys to remove
                keys_to_remove.append(blockId)
        
        # Remove the keys from the dictionary and sets
        for blockId in keys_to_remove:
            self.L3Cache.evict_a_block(blockId)
            self.prefetchedSet.discard(blockId)
            self.gonnaPrefetchSet.discard(blockId)

    # ユーザの位置が知らされるたびにこれ、もしくは、vector prefetchを実行
    def updatePrefetchQ(self,userPoint):
        self.enque_neighbor_blocks_to_front(userPoint) # でいんじゃね？って思った。
    
    def thread_func(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.fetchLoop())          

    def clearQueue(self):
        while not self.prefetch_q_empty():
            blockId = self.prefetch_q.popleft()
            self.gonnaPrefetchSet.discard(blockId)
        

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
                print(f"L3pref : vector prefetch : {(tol,timestep + n*dt, x + n*dx, y + n*dy, z + n*dz)}")
                
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
        
class L4Prefetcher:

    def __init__(self,L4Cache,dataDim,blockSize,userUsingGPU,userUsingStorage,targetTol = 0.1,n_vector_fetch = 2):

        self.userUsingGPU = userUsingGPU
        self.userUsingStorage = userUsingStorage
        self.L4Cache = L4Cache


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
        self.TargetTol = targetTol
        self.n_vector_fetch = n_vector_fetch

        # 計算式が間違っているか、そんな気がする。
        self.radius = self.getRadiusFromCapacity() 

        # フェッチループ起動
        if self.L4Cache.capacityInMiB == 0:
            print("Not starting L4 Prefetcher because the capacity size is 0")
        else :
            print("L4pref : start prefetcher")
            self.thread = threading.Thread(target=self.thread_func)
            self.thread.start()
            self.enqueue_first_blockId()

        # for stats
        self.numPrefetches = 0

        # req sequence
        self.RequestSequence = []
    ### 初期化系メソッド ###
            
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

    def InitializeSetting(self,blockOffset,targetTol):
        self.Slicer.changeBlockSize(blockOffset)
        self.prefetchedSet = set()
        self.gonnaPrefetchSet = set()
        self.prefetch_q = deque()
        self.TargetTol = float(targetTol)
        self.blockOffset = blockOffset
        self.radius = 10 #self.getRadiusFromCapacity()
        self.RequestSequence = []

    ### フェッチスレッド用メソッド ###
    
    # 別スレッドで実行されるループ
    async def fetchLoop(self):

        while not self.stop_thread:
            
            # self.L4Cache.printInfo()

            if (not self.prefetch_q_empty()) and (self.L4Cache.usedSizeInMiB <  self.L4Cache.capacityInMiB) and (not self.userUsingStorage.is_locked()):
                nextBlockId = self.prefetch_q.popleft() # distanceはいらない。ここで取り出したときに、ユーザとの距離を測って、一定以内だったら入れるでいいやん
                # というのも、distanceは、キューに入れられた時点でのuserとの距離なわけじゃないですか。
                distance = self.calHops(self.userPoint,nextBlockId)
                if distance > self.radius:
                    continue

                if self.prefetchedSet.__contains__(nextBlockId):
                    continue

                self.numPrefetches += 1
                print(f"L4pref: block",nextBlockId)
                data = self.Slicer.sliceData(nextBlockId)
                self.L4Cache.put(nextBlockId,data)
                self.prefetchedSet.add(nextBlockId)
                self.enque_neighbor_blocks(nextBlockId)

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

    def enque_neighbor_blocks(self,centerBlock):
        tol = self.TargetTol
        timestep = centerBlock[1]
        x = centerBlock[2]
        y = centerBlock[3]
        z = centerBlock[4]

        # 時間方向に1つづれたブロックは1ホップ
        for dt in [-1,1]:
            if (self.gonnaPrefetchSet.__contains__((tol,timestep + dt, x, y, z))
                        or (timestep + dt < 0) or (timestep+dt >= self.maxTimestep)):
                continue
            else:
                self.prefetch_q.append((tol,timestep+dt, x, y, z))
                self.gonnaPrefetchSet.add((tol,timestep+dt, x, y, z))  

        for dx in [-self.blockOffset, 0, self.blockOffset]:
            for dy in [-self.blockOffset, 0, self.blockOffset]:
                for dz in [-self.blockOffset, 0, self.blockOffset]:
                    if (self.gonnaPrefetchSet.__contains__((tol,timestep, x+dx, y+dy, z+dz))
                        or (x + dx < 0) or (x + dx >= self.maxX)
                        or (y + dy < 0) or (y + dy >= self.maxY)
                        or (z + dz < 0) or (z + dz >= self.maxZ)):
                        continue
                    else:
                        self.prefetch_q.append((tol,timestep, x+dx, y+dy, z+dz))
                        self.gonnaPrefetchSet.add((tol,timestep, x+dx, y+dy, z+dz))

    def enque_neighbor_blocks_to_front(self,centerBlock):
        
        tol = self.TargetTol  
        timestep = centerBlock[1]
        x = centerBlock[2]
        y = centerBlock[3]
        z = centerBlock[4]

        # 時間方向に1つづれたブロックは1ホップ
        for dt in [-1,1]:
            if self.gonnaPrefetchSet.__contains__((tol,timestep + dt, x, y, z)):
                self.prefetch_q.appendleft((tol,timestep+dt, x, y, z))
            
            elif ((timestep + dt < 0) or (timestep+dt >= self.maxTimestep)):
                continue
            
            else:
                self.prefetch_q.appendleft((tol,timestep + dt, x, y, z))
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
                        self.prefetch_q.appendleft((tol,timestep, x + dx, y + dy, z + dz))
                        self.gonnaPrefetchSet.add((tol,timestep, x + dx, y + dy, z + dz))

    ### ミスをした時の挙動を決定するメソッド ###
                        
    def InformL3MissAndL4Miss(self,blockId): # これはいる
        # self.prefetch_q.append((blockId,0)) # いや、これはもうすでに取ってあるから今から取りに行ったってもう意味ないのよ。
        self.prefetchedSet.add(blockId)

    # 再初期化で使う
    def clearQueue(self):
        while not self.prefetch_q_empty():
            blockId = self.prefetch_q.popleft()
            self.gonnaPrefetchSet.discard(blockId)                       

    ### 置換方針とプリフェッチ方針を決定するメソッド ###
                    
    def prefetch_q_empty(self):
        if(len(self.prefetch_q) == 0):
            return True
        else:
            return False
        
    def print_prefetch_q(self):
        print(self.prefetch_q)

    # 2つのブロック間のちぇびちぇふ距離を計算
    def calHops(self,centerBlockId,targetBlockId):
        timeHops = abs(centerBlockId[1] - targetBlockId[1])
        xHops = abs(centerBlockId[2] - targetBlockId[2])
        yHops = abs(centerBlockId[3] - targetBlockId[3])
        zHops = abs(centerBlockId[4] - targetBlockId[4])
        spaceHops = max(xHops,yHops,zHops) // self.blockOffset # これでホップ数が出る
        return timeHops + spaceHops

    def InformUserPoint(self,blockId):
        print(f"L4pref : get informed userpoint : {blockId}")
        self.RequestSequence.append(blockId)
        self.userPoint = blockId
        if(self.cal_move_vector_and_prefetch()):
            self.update_cache(blockId)
        else:
            self.update_cache(blockId)
            self.updatePrefetchQ(blockId)

    def update_cache(self,userPoint):
        for blockId,blockValue in self.L4Cache.cache.items():
            hops = self.calHops(userPoint,blockId)
            if (hops > self.radius) and self.L4Cache.isCacheFull():
                # print(f"L4pref : evicting a block : {blockId}")
                self.L4Cache.evict_a_block(blockId)
                self.prefetchedSet.discard(blockId)
                self.gonnaPrefetchSet.discard(blockId)

    # ユーザの位置が知らされるたびにこれを実行
    def updatePrefetchQ(self,userPoint):
        self.enque_neighbor_blocks_to_front(userPoint)

    def cal_move_vector_and_prefetch(self,numSeq=3): # numSeq : ラストnumSeq個のnumSeqから、方向を算出
        
        latest_sequences = self.RequestSequence[-numSeq:] # 中身は、(tol,x,y,z) のtuple
        if len(latest_sequences) <= 2 :
            return # バグ防止
        # print(f"Reqsequence : {self.RequestSequence}")

        v1 = np.subtract(latest_sequences[2],latest_sequences[1])
        v0 = np.subtract(latest_sequences[1],latest_sequences[0])

        if (np.array_equal(v1, v0)):

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
                print(f"L4pref : vector prefetch : {(tol,timestep + n*dt, x + n*dx, y + n*dy, z + n*dz)}")
                
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
        else: # vector prefetchをしない
            return False