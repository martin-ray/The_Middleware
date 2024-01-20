from collections import deque
import asyncio
import threading

# from L1_L2Cache import dynamic_cache
from NetInterface import NetIF
from decompressor import Decompressor
import time


class L2Prefetcher:

    #################### コンストラクタ ####################
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

        # フェッチループを起動
        if self.L2Cache.capacityInMiB == 0 and OnSwitch == False:
            pass
        else:
            self.thread = threading.Thread(target=self.thread_func)
            self.thread.start()

    ################## 初期化系メソッド ####################
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

    def changeBlockOffset(self,blockOffset):
        self.blockOffset = blockOffset

    ################# プリフェッチループ系メソッド ##############
    async def fetchLoop(self):
        while not self.stop_thread:
            if (not self.prefetch_q_empty()) and (self.L2Cache.usedSizeInMiB < self.L2Cache.capacityInMiB):
                print("L2 pref looping")
                nextBlockId,d = self.pop_front()
                compressed = self.Netif.send_req_urgent(nextBlockId)
                self.L2Cache.put(nextBlockId,compressed)
                self.enque_neighbor_blocks(nextBlockId,d) # ここ、あってるかもう一度確認してくれ。頼む。

            else:
                await asyncio.sleep(0.01)  # Sleep for 1 second, or adjust as needed

    def thread_func(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.fetchLoop())          

    def clearQueue(self):
        while not self.prefetch_q_empty():
            blockId = self.pop_front()
            self.gonnaPrefetchSet.discard(blockId)
            self.Netif.sendQ.clear()

    ################## 置換、プリフェッチ系メソッド ############### 
    def enque_neighbor_blocks(self,centerBlock,d):
            print(centerBlock)
            tol = self.targetTol # centerBlock[0] 
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
        tol = self.targetTol # centerBlock[0] 
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
                        
    def pop_front(self):
        return self.prefetch_q.popleft()
    
    def prefetch_q_empty(self):
        if(len(self.prefetch_q) == 0):
            return True
        else:
            return False

    def InformL2MissByL1Pref(self,blockId):
        print("L1 prefetcher missed to catch on L2 cache:{}\n".format(blockId))

    def InformL2MissByUser(self,blockId):
        # print("L1 and L2 Missed the request by user:{}\n",blockId)
        self.prefetchedSet.add(blockId)

    def InformL1MissL2HitByUser(self,blockId):
        print("the data was catched in L2: {}\n".format(blockId))

    def calHops(self,centerBlockId,targetBlockId):
        timeHops = abs(centerBlockId[1]-targetBlockId[1])
        xHops = abs(centerBlockId[2]- targetBlockId[2])
        yHops = abs(centerBlockId[3]- targetBlockId[3])
        zHops = abs(centerBlockId[4]- targetBlockId[4])
        spaceHops = max(xHops,yHops,zHops)//self.blockOffset # これでホップ数が出る
        return timeHops + spaceHops

    def InformUserPoint(self,blockId):
        self.userPoint = blockId
        self.evict(blockId)
        self.updatePrefetchQ(blockId)

    def evict(self,userPoint):
        # print("evicting")
        for blockId in self.L2Cache.cache.keys():
            hops = self.calHops(userPoint,blockId)
            if (hops > self.radius) and self.L2Cache.isCacheFull():
                self.L2Cache.evict_a_block(blockId)
                self.prefetchedSet.discard(blockId)

    # ユーザの位置が知らされるたびにこれを実行する。内容は簡単。
    def updatePrefetchQ(self,userPoint):
        self.enque_neighbor_blocks_to_front(userPoint,0) # でいんじゃね？って思った。

class L1Prefetcher:

    ################## コンストラクタ ##################
    def __init__(self,L1Cache,L2Cache,GPUmutex,maxTimestep=9,offsetSize=256,OnSwitch=True, TargetTol= 0.1):


        self.L1Cache = L1Cache
        self.L2Cache = L2Cache
        self.decompressor = Decompressor(self.L1Cache)

        # 自分で持つことにしました。
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

        # フェッチループ起動
        if self.L1Cache.capacityInMiB == 0 and OnSwitch == False:
            pass
        else:
            self.thread = threading.Thread(target=self.thread_func)
            self.thread.start()

    ############## 初期化系のメソッド #############

    def startPrefetching(self):
        self.stop_thread = False
        if self.L3Cache.capacity > 0:
            self.thread = threading.Thread(target=self.thread_func)
            self.thread.start()
            print("Started L1 prefetcher!")
        else :
            print("L1 cache size is 0. So L1 prefetcher is not starting")

    def stop(self):
        self.stop_thread = True

    def InitializeSetting(self,blockOffset):
        self.prefetchedSet = set()
        self.gonnaPrefetchSet = set()
        self.prefetch_q = deque()
        self.blockOffset = blockOffset

    def clearQueue(self):
        while not self.prefetch_q_empty():
            blockId = self.pop_front()
            self.gonnaPrefetchSet.discard(blockId)

    ############# フェッチループ系のメソッド ###########
    async def fetchLoop(self):

        while not self.stop_thread:
            
            print("L1 prefetcher is looping")

            if (not self.prefetch_q_empty()) and (self.L1Cache.usedSizeInMiB < self.L1Cache.capacityInMiB):
            
                nextBlockId,distance = self.pop_front()
                compressed = self.L2Cache.get(nextBlockId)

                if compressed is None: # L2Miss
                    # これ以上、下にリクエストするのをあきらめる
                    pass

                else: # L2Hit
                    original = None
                    with self.GPUmutex:
                        original = self.decompressor.decompress(compressed)
                    self.L1Cache.put(nextBlockId,original)   

                self.enque_neighbor_blocks(nextBlockId,distance)
            else:
                print(f"L1 prefethcer:prefetchQ empty? ={self.prefetch_q_empty()}, \
                      cache has room ? ={self.L1Cache.usedSizeInMiB < self.L1Cache.capacityInMiB}")
                await asyncio.sleep(0.1)  # Sleep for 0.1 second, or adjust as needed

    def thread_func(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.fetchLoop())       


    ############# 更新系メソッド ##############

    def enque_neighbor_blocks(self,centerBlock,d):
            tol = self.targetTol # centerBlock[0] 
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
        tol = self.targetTol # centerBlock[0] 
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
                        

    def pop_front(self):
        return self.prefetch_q.popleft()
    
    def InformUserPoint(self,blockId):

        self.userPoint = blockId
        self.evict(blockId)
        self.updatePrefetchQ(blockId)


    def InformL1MissByUser(self,blockId):
        print("User missed to catch in L1: {}\n".format(blockId))

    def InformL1MissAndL2Hit(self,blockId):
        print("User missed to catch in L1 and Hit on L2: {}\n".format(blockId))

    def InformL1MissAndL2Miss(self,blockId):
        print("L1 miss and L2 miss: {}\n".format(blockId))
        self.clearQueue()
        self.enque_neighbor_blocks(blockId)
    
    def prefetch_q_empty(self):
        if(len(self.prefetch_q) == 0):
            return True
        else:
            return False

    # キャッシュの要素をひとつづつ見て、半径に収まらない場合は、捨てる
    def evict(self,userPoint):
        print("L1 prefetcher is evicting")
        for blockId in self.L1Cache.cache.keys():
            hops = self.calHops(userPoint,blockId)
            if (hops > self.radius) and self.L1Cache.isCacheFull():
                self.L1Cache.evict_a_block(blockId)
                self.prefetchedSet.discard(blockId)

    # ユーザの位置が知らされるたびにこれを実行する。内容は簡単。
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
    
# unit test
if __name__ == "__main__":
    print("test")



         



