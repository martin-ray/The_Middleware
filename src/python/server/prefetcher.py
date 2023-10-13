import requests
import numpy as np
import matplotlib.pyplot as plt
import queue
from collections import deque
import asyncio
import numpy as np
import threading
# self-defined libraries
import _mgard as mgard
from L3_L4Cache import LRU_cache
from L3_L4Cache import dynamic_cache

class L3Prefetcher:
    def __init__(self,L3Cache,L4Cache,Slicer,compressor, blockOffset=256) -> None:
        # ToleranceArray
        self.Tols = [0.0001,0.001,0.01,0.1,0.2,0.3,0.4,0.5]
        self.maxTimestep = 1024
        self.maxX = 1024
        self.maxY = 1024
        self.maxZ = 1024
        self.default_offset = blockOffset
        self.L3Cache = L3Cache
        self.L4Cache = L4Cache
        self.Slicer = Slicer
        self.compressor = compressor
        self.prefetchedSet = s = set()
        self.fetch_q = deque() # blocks going to get
        
        # フェッチループを起動
        self.thread = threading.Thread(target=self.thread_func)
        self.thread.start()

        # 最初のブロックを投下
        self.enqueue_first_blockId()

    def enque_neighbor_blocks(self,centerBlock):
        tol = centerBlock[0] 
        timestep = centerBlock[1]
        x = centerBlock[2]
        y = centerBlock[3]
        z = centerBlock[4]

        ## TODO tolの扱い
        for dt in [-1,0,1]:
            for dx in [-self.default_offset, 0, self.default_offset]:
                for dy in [-self.default_offset, 0, self.default_offset]:
                    for dz in [-self.default_offset, 0, self.default_offset]:
                        if (self.prefetchedSet.__contains__((tol,timestep+dt, x+dx, y+dy, z+dz))
                            or (timestep+dt < 0) or (timestep+dt > self.maxTimestep) 
                            or (x+dx < 0) or (x+dx >= self.maxX)
                            or (y+dy < 0) or (y+dy >= self.maxY)
                            or (z+dz < 0) or (z+dz >= self.maxZ)):
                            continue
                        else:
                            print("appending {}".format((tol,timestep+dt, x+dx, y+dy, z+dz)))
                            self.fetch_q.append((tol,timestep+dt, x+dx, y+dy, z+dz))
                            self.prefetchedSet.add((tol,timestep+dt, x+dx, y+dy, z+dz))

    def pop_front(self):
        return self.fetch_q.popleft()
    
    def fetch_q_empty(self):
        if(len(self.fetch_q) == 0):
            return True
        else:
            return False
    
    def enqueue_first_blockId(self):
        firstBlock = (0.1, 0, 0 ,0 ,0 )
        self.fetch_q.append(firstBlock)

    def fetch(self,blockId):
        self.prefetchedSet.add(blockId)
        self.Netif.send_req(blockId)
    
    # block = (tol,timestep,x,y,z)
    def fetch_test(self,blockId):
        self.prefetchedSet.add(blockId)
        print("fetching {}".format(blockId))

    # ここでどういう風にプリフェッチポリシーを変えるかっていうのもかなり見ものではある
    # なかなか気になるところですね。
    def InformL3MissByAPI(self,blockId):
        print("L3 Missed By API:{}\n".format(blockId))
        # TODO 何かしらのプリフェッチポリシーの変更を加える必要
        pass

    def InformL4MissByPref(self,blockId):
        print("L3 Prefetcher missed L4 and brought from disk:{}\n",blockId)

    def InformL4MissByAPI(self,blockId):
        print("the data was catched in L2: {}\n".format(blockId))
        pass

    async def fetch_loop_test(self):
        while True:
            if (not self.fetch_q_empty()) and (self.L3Cache.usedSize < self.L3Cache.capacity):
                next = self.pop_front()
                self.fetch_test(next)
                data = np.random.random_sample(
                    (self.default_offset, self.default_offset, self.default_offset)
                ).astype(np.float32)
                self.L3Cache.put(next, data)
                self.enque_neighbor_blocks(next)
            else:
                await asyncio.sleep(1)  # Sleep for 1 second, or adjust as needed


    # ここで、
    def L4MisssHandler(self,nextBlockId):
        d = self.Slicer.sliceData(nextBlockId)
        tol = nextBlockId[0]
        compressed = self.compressor.compress(d,tol)
        self.L3Cache.put(nextBlockId,compressed)

    def L4HitHandler(self,nextBlockId,original):
        tol = nextBlockId[0]
        compressed = self.compressor.compress(original,tol)
        self.L3Cache.put(nextBlockId,compressed)

    
    async def fetchLoop(self):
        while True:
            if (not self.fetch_q_empty()) and (self.L3Cache.usedSize < self.L3Cache.capacity):
                self.L3Cache.printInfo()
                nextBlockId = self.pop_front()
                compressed = self.L4Cache.get(nextBlockId)
                if compressed == None:
                    print("L4 Miss")
                    thread = threading.Thread(target=self.L4MissHandler, args=(nextBlockId))
                    thread.start()
                else:
                    thread = threading.Thread(target=self.L4HitHandler, args=(nextBlockId,compressed))
                    thread.start()
                self.enque_neighbor_blocks(nextBlockId)
            else:
                await asyncio.sleep(0.1)  # Sleep for 1 second, or adjust as needed

    def thread_func(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.fetchLoop())          


# TODO 継承
class L4Prefetcher:
    def __init__(self,L4Cache,Slicer):
        self.L4Cache = L4Cache
        self.Slicer = Slicer

        self.Tols = [0.0001,0.001,0.01,0.1,0.2,0.3,0.4,0.5]
        self.maxTimestep = 1024
        self.maxX = 1024
        self.maxY = 1024
        self.maxZ = 1024
        self.default_offset = 256
        self.prefetchedSet = set()
        self.fetch_q = deque()
        
        # フェッチループ起動
        self.thread = threading.Thread(target=self.thread_func)
        self.thread.start()

        self.enqueue_first_blockId()

    def enque_neighbor_blocks(self,centerBlock):

        tol = centerBlock[0] 
        timestep = centerBlock[1]
        x = centerBlock[2]
        y = centerBlock[3]
        z = centerBlock[4]

        ## TODO tolの扱い
        for dt in [-1,0,1]:
            for dx in [-self.default_offset, 0, self.default_offset]:
                for dy in [-self.default_offset, 0, self.default_offset]:
                    for dz in [-self.default_offset, 0, self.default_offset]:
                        if (self.prefetchedSet.__contains__((tol,timestep+dt, x+dx, y+dy, z+dz))
                            or (timestep+dt < 0) or (timestep+dt > self.maxTimestep) 
                            or (x+dx < 0) or (x+dx >= self.maxX)
                            or (y+dy < 0) or (y+dy >= self.maxY)
                            or (z+dz < 0) or (z+dz >= self.maxZ)):
                            continue
                        else:
                            print("appending {}".format((tol,timestep+dt, x+dx, y+dy, z+dz)))
                            self.fetch_q.append((tol,timestep+dt, x+dx, y+dy, z+dz))
                            self.prefetchedSet.add((tol,timestep+dt, x+dx, y+dy, z+dz))

    def pop_front(self):
        return self.fetch_q.popleft()
    
    def fetch_q_empty(self):
        if(len(self.fetch_q) == 0):
            return True
        else:
            return False
        
    def enqueue_first_blockId(self):
        firstBlock = (0.1, 0, 0 ,0 ,0 )
        self.fetch_q.append(firstBlock)
    
    def letKnowCenterPoint(self,blockId):
        pass

    def InformL3MissByUser(self,blockId):
        print("User missed to catch in L1: {}\n".format(blockId))
        

    async def fetchLoop(self):
        while True:
            if (not self.fetch_q_empty()) and (self.L4Cache.usedSize < self.L4Cache.capacity):
                self.L4Cache.printInfo()
                nextBlockId = self.pop_front()
                data = self.Slicer.sliceData(nextBlockId)
                self.L4Cache(data)
                self.enque_neighbor_blocks(nextBlockId)
            else:
                await asyncio.sleep(0.1)  # Sleep for 1 second, or adjust as needed

    def thread_func(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.fetchLoop())       

  






         



