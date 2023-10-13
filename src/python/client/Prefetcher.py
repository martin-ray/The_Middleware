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
from L1_L2Cache import LRU_cache
from L1_L2Cache import dynamic_cache
from NetInterface import NetIF

class L2Prefetcher:
    def __init__(self,L2Cache,NetIF,serverURL="http://localhost:8080") -> None:
        self.URL = serverURL

        # ToleranceArray
        self.Tols = [0.0001,0.001,0.01,0.1,0.2,0.3,0.4,0.5]
        self.maxTimestep = 1024
        self.maxX = 1024
        self.maxY = 1024
        self.maxZ = 1024
        self.default_offset = 256
        self.L2Cache = L2Cache
        self.prefetchedSet = s = set()
        self.fetch_q = deque() # blocks going to get
        self.Netif = NetIF
        # フェッチループを起動
        self.thread = threading.Thread(target=self.thread_func(self.fetchLoop))
        self.thread.start()

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

    def fetch(self,blockId):
        self.prefetchedSet.add(blockId)
        self.Netif.send_req(blockId)
    
    # block = (tol,timestep,x,y,z)
    def fetch_test(self,blockId):
        self.prefetchedSet.add(blockId)
        print("fetching {}".format(blockId))

    # ここでどういう風にプリフェッチポリシーを変えるかっていうのもかなり見ものではある
    # なかなか気になるところですね。
    def InformL2MissByL1Pref(self,blockId):
        print("L1 prefetcher missed to catch on L2 cache:{}\n".format(blockId))
        # TODO 何かしらのプリフェッチポリシーの変更を加える必要
        pass

    def InformL2MissByUser(self,blockId):
        print("L1 and L2 Missed the request by user:{}\n",blockId)

    def InformL1MissByUser(self,blockId):
        print("the data was catched in L2: {}\n".format(blockId))
        # L2でぎりぎりキャッチできたので、何かしらのL2のプリフェッチポリシーをここで変更する必要があるかもしれない。
        pass

    async def fetch_loop_test(self):
        while True:
            if (not self.fetch_q_empty()) and (self.L2Cache.usedSize < self.L2Cache.capacity):
                self.L2Cache.printInfo()
                next = self.pop_front()
                self.fetch_test(next)
                data = np.random.random_sample(
                    (self.default_offset, self.default_offset, self.default_offset)
                ).astype(np.float32)
                self.L2Cache.put(next, data)
                self.enque_neighbor_blocks(next)
            else:
                await asyncio.sleep(1)  # Sleep for 1 second, or adjust as needed

    async def fetchLoop(self):
        while True:
            if (not self.fetch_q_empty()) and (self.L2Cache.usedSize < self.L2Cache.capacity):
                self.L2Cache.printInfo()
                nextBlockId = self.pop_front()
                # ここはべすすれっどに処理を任せた方がいいかもしれません
                self.Netif.send_req(nextBlockId)
                self.enque_neighbor_blocks(nextBlockId)
            else:
                await asyncio.sleep(0.1)  # Sleep for 1 second, or adjust as needed

    def thread_func(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.fetchLoop())          


# TODO 継承
class L1Prefetcher:
    def __init__(self,decompressor,NetIF,L1Cache,L2Cache):
        self.decompressor = decompressor
        self.Netif = NetIF
        self.L1Cache = L1Cache
        self.L2Cache = L2Cache

        self.Tols = [0.0001,0.001,0.01,0.1,0.2,0.3,0.4,0.5]
        self.maxTimestep = 1024
        self.maxX = 1024
        self.maxY = 1024
        self.maxZ = 1024
        self.default_offset = 256
        self.prefetchedSet = set()
        self.fetch_q = deque()
        
        # フェッチループ起動
        self.thread = threading.Thread(target=self.thread_func(self.fetchLoop))
        self.thread.start()

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
    
    def letKnowCenterPoint(self,blockId):
        pass

    def InformL1MissByUser(self,blockId):
        print("User missed to catch in L1: {}\n".format(blockId))

    def L2MissHandler(self,blockId,BlockAndData):
        compressed = self.netIF.send_req_urgent(blockId)
        original = self.decompressor.decompress(compressed)
        self.L1Cache.put(blockId,original)

    def L2HitHandler(self,blockId,compressed):
        original = self.decompressor(compressed)
        self.L1Cache.put(blockId,original)   
    
    async def fetchLoopTest(self):
        while True:
            if (not self.fetch_q_empty()) and (self.L1Cache.usedSize < self.L1Cache.capacity):
                self.L1Cache.printInfo()
                nextBlockId = self.pop_front()
                compressed = self.L2Cache.get(nextBlockId)
                if compressed == None: #L2Miss
                    # L2のプリフェッチポリシーを変更.どうやって？今までキューにたまっているものを捨てる？どうする？わかりまてー－ん。
                    self.L2Cache.InformL2MissByL1Pref(nextBlockId)
                    thread = threading.Thread(target=self.L2MissHandler, args=(nextBlockId))
                    thread.start()
                else: # L2Hit
                    thread = threading.Thread(target=self.L2HitHandler, args=(nextBlockId,compressed))
                    thread.start()
            else:
                await asyncio.sleep(0.1)  # Sleep for 1 second, or adjust as needed
        

    async def fetchLoop(self):
        while True:
            if (not self.fetch_q_empty()) and (self.L1Cache.usedSize < self.L1Cache.capacity):
                self.L1Cache.printInfo()
                nextBlockId = self.pop_front()
                self.L2Cache.get(nextBlockId)
                # self.Netif.send_req(nextBlockId)
                self.enque_neighbor_blocks(nextBlockId)
            else:
                await asyncio.sleep(0.1)  # Sleep for 1 second, or adjust as needed

    def thread_func(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.fetchLoop())       

## for test
def thread_func(prefetcher):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(prefetcher.fetch_loop())    


def move_to_l1():
    pass 

# unit test
if __name__ == "__main__":

    lru_cache = LRU_cache(capacity=300,offsetSize=256)
    netIF = NetIF(lru_cache)
    prefetcher = L2Prefetcher(lru_cache,netIF)
    
    tol = 0.1
    t = 0
    x,y,z = 0,0,0
    first_point = (tol,t,x,y,z)
    prefetcher.fetch_test(first_point)
    prefetcher.enque_neighbor_blocks(first_point)
    thread = threading.Thread(target=thread_func(prefetcher))
    thread.start()



         



