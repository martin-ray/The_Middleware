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

# L3キャッシュとL4キャッシュプリふぇっちゃで同じスライサーを共有すると、なぜか片方が全く取れなくなるという現象に遭遇
class L3Prefetcher:
    def __init__(self,L3Cache,L4Cache,compressor,L4Prefetcher, blockOffset=256) -> None:
        # ToleranceArray
        self.Tols = [0.0001,0.001,0.01,0.1,0.2,0.3,0.4,0.5]
        self.maxTimestep = 1024
        self.maxX = 1024
        self.maxY = 1024
        self.maxZ = 1024
        self.default_offset = blockOffset
        self.L3Cache = L3Cache
        self.L4Cache = L4Cache
        # これね、L3PrefetcherとL4Prefetcherで別々のもの持ってないとなんか片方が一生使えなくなる
        self.Slicer = Slicer()
        self.compressor = compressor
        self.L4Pref = L4Prefetcher
        self.gonnaPrefetchSet = set()
        self.prefetchedSet = set()
        self.prefetch_q = deque() # blocks going to get
        
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
                            self.prefetch_q.append((tol,timestep+dt, x+dx, y+dy, z+dz))
                            self.prefetchedSet.add((tol,timestep+dt, x+dx, y+dy, z+dz))

    def pop_front(self):
        return self.prefetch_q.popleft()
    
    def prefetch_q_empty(self):
        if(len(self.prefetch_q) == 0):
            return True
        else:
            return False
        
    def print_prefetch_q(self):
        print(self.prefetch_q)

    def enqueue_first_blockId(self):
        firstBlock = (0.1, 0, 0 ,0 ,0 )
        self.prefetch_q.append(firstBlock)

    def fetch(self,blockId):
        self.prefetchedSet.add(blockId)
        self.Netif.send_req(blockId)

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

    
    async def fetchLoop(self):
        while True:
            if (not self.prefetch_q_empty()) and (self.L3Cache.usedSize < self.L3Cache.capacity):
                
                nextBlockId = self.pop_front()
                original = self.L4Cache.get(nextBlockId)
                if original is None:

                    print("L4 Miss!",nextBlockId)
                    try:
                        self.L4Pref.prefetch_q.remove(nextBlockId)
                        print("succeed in deleting {} in L4's prefetch Q".format(nextBlockId))
                    except Exception as e:
                        print("{} doesn't exist in L4's prefetch Q".format(nextBlockId))
                        print("L4 prefetchQ:")
                        print(self.L4Pref.prefetch_q)
                    d = self.Slicer.sliceData(nextBlockId)

                    # write to L4 also
                    self.L4Cache.put(nextBlockId,d)
                    tol = nextBlockId[0]
                    compressed = self.compressor.compress(d,tol)
                    self.L3Cache.put(nextBlockId,compressed)
                    print("L3 keys")
                    self.L3Cache.printAllKeys()
                    print("L4 keys")
                    self.L4Cache.printAllKeys()
                else:
                    print("L4 HIT! nice!",nextBlockId)
                    print("L3 keys")
                    self.L3Cache.printAllKeys()
                    print("L4 keys")
                    self.L4Cache.printAllKeys()
                    tol = nextBlockId[0]
                    compressed = self.compressor.compress(original,tol)
                    self.L3Cache.put(nextBlockId,compressed)
                self.enque_neighbor_blocks(nextBlockId)
            else:
                await asyncio.sleep(0.1)  # Sleep for 1 second, or adjust as needed

    def thread_func(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.fetchLoop())          


# TODO 継承
class L4Prefetcher:
    def __init__(self,L4Cache):
        self.L4Cache = L4Cache
        self.Slicer = Slicer()

        self.Tols = [0.0001,0.001,0.01,0.1,0.2,0.3,0.4,0.5]
        self.maxTimestep = 1024
        self.maxX = 1024
        self.maxY = 1024
        self.maxZ = 1024
        self.default_offset = 256
        self.gonnaPrefetchSet = set() # プリフェッチしに行くセット
        self.prefetchedSet = set() # プリフェッチしたセット
        self.prefetch_q = deque()
        
        # フェッチループ起動
        self.thread = threading.Thread(target=self.thread_func)
        self.thread.start()

        # L4に最初のものを円キューしたわけですよ。
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
                        if (self.gonnaPrefetchSet.__contains__((tol,timestep+dt, x+dx, y+dy, z+dz))
                            or (timestep+dt < 0) or (timestep+dt > self.maxTimestep) 
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


    def enqueue_first_blockId(self):
        firstBlock = (0.1, 0, 0 ,0 ,0 )
        self.prefetch_q.append(firstBlock)
    
    def letKnowCenterPoint(self,blockId):
        pass

    def InformL3MissByUser(self,blockId):
        print("User missed to catch in L1: {}\n".format(blockId))
        

    async def fetchLoop(self):
        while True:
            if (not self.prefetch_q_empty()) and (self.L4Cache.usedSize < self.L4Cache.capacity):
                nextBlockId = self.pop_front()
                data = self.Slicer.sliceData(nextBlockId)
                self.L4Cache.put(nextBlockId,data)
                self.prefetchedSet.add(nextBlockId)
                self.enque_neighbor_blocks(nextBlockId)
            else:
                await asyncio.sleep(0.1)  # Sleep for 1 second, or adjust as needed

    def thread_func(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.fetchLoop())       

  






         



