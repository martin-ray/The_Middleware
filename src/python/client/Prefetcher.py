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
# from L1_L2Cache import dynamic_cache
from NetInterface import NetIF

class L2Prefetcher:
    def __init__(self,L2Cache,Netif,maxTimestep=9,serverURL="http://localhost:8080") -> None:
        self.URL = serverURL

        # ToleranceArray
        self.Tols = [0.0001,0.001,0.01,0.1,0.2,0.3,0.4,0.5]
        self.maxTimestep = maxTimestep
        self.maxX = 1024
        self.maxY = 1024
        self.maxZ = 1024
        self.default_offset = 256
        self.L2Cache = L2Cache
        self.gonnaPrefetchSet = set()
        self.prefetchedSet = set()
        self.prefetch_q = deque() # blocks going to get
        self.Netif = Netif
        self.stop_thread = False

        # フェッチループを起動
        if self.L2Cache.capacity == 0:
            pass
        else:
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
                        if (self.gonnaPrefetchSet.__contains__((tol,timestep+dt, x+dx, y+dy, z+dz))
                            or (timestep+dt < 0) or (timestep+dt >= self.maxTimestep) 
                            or (x+dx < 0) or (x+dx >= self.maxX)
                            or (y+dy < 0) or (y+dy >= self.maxY)
                            or (z+dz < 0) or (z+dz >= self.maxZ)):
                            continue
                        else:
                            print("appending {}".format((tol,timestep+dt, x+dx, y+dy, z+dz)))
                            self.prefetch_q.append((tol,timestep+dt, x+dx, y+dy, z+dz))
                            self.gonnaPrefetchSet.add((tol,timestep+dt, x+dx, y+dy, z+dz))

    def pop_front(self):
        return self.prefetch_q.popleft()
    
    def prefetch_q_empty(self):
        if(len(self.prefetch_q) == 0):
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

    async def fetchLoop(self):
        while not self.stop_thread:
            print("L2:")
            self.L2Cache.printAllKeys()
            if (not self.prefetch_q_empty()) and (self.L2Cache.usedSize < self.L2Cache.capacity):
                self.L2Cache.printInfo()
                nextBlockId = self.pop_front()
                self.Netif.send_req(nextBlockId) # 別スレッドで実行されるキュー
                self.enque_neighbor_blocks(nextBlockId)
            else:
                await asyncio.sleep(0.1)  # Sleep for 1 second, or adjust as needed

    def thread_func(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.fetchLoop())          

    def startPrefetching(self):
        self.stop_thread = False
        if self.L2Cache.capacity > 0:
            self.thread = threading.Thread(target=self.thread_func)
            self.thread.start()
            self.enqueue_first_blockId()
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

    def enqueue_first_blockId(self):
        firstBlock = (0.1, 0, 0 ,0 ,0 )
        self.prefetch_q.append(firstBlock)
        self.gonnaPrefetchSet.add(firstBlock)

# TODO 継承
class L1Prefetcher:
    def __init__(self,decompressor,Netif,L1Cache,L2Cache,maxTimestep=9,offsetSize=256):
        self.decompressor = decompressor
        self.Netif = Netif
        self.L1Cache = L1Cache
        self.L2Cache = L2Cache

        self.Tols = [0.0001,0.001,0.01,0.1,0.2,0.3,0.4,0.5]
        self.maxTimestep = maxTimestep
        self.maxX = 1024
        self.maxY = 1024
        self.maxZ = 1024
        self.default_offset = offsetSize
        self.gonnaPrefetchSet = set()
        self.prefetchedSet = set()
        self.prefetch_q = deque()
        self.stop_thread = False

        # フェッチループ起動
        if self.L1Cache.capacity == 0:
            pass
        else:
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
                        if (self.gonnaPrefetchSet.__contains__((tol,timestep+dt, x+dx, y+dy, z+dz))
                            or (timestep+dt < 0) or (timestep+dt >= self.maxTimestep) 
                            or (x+dx < 0) or (x+dx >= self.maxX)
                            or (y+dy < 0) or (y+dy >= self.maxY)
                            or (z+dz < 0) or (z+dz >= self.maxZ)):
                            continue
                        else:
                            print("appending {}".format((tol,timestep+dt, x+dx, y+dy, z+dz)))
                            self.prefetch_q.append((tol,timestep+dt, x+dx, y+dy, z+dz))
                            self.gonnaPrefetchSet.add((tol,timestep+dt, x+dx, y+dy, z+dz))


    def enqueue_first_blockId(self):
        firstBlock = (0.1, 0, 0 ,0 ,0 )
        self.prefetch_q.append(firstBlock)
        self.gonnaPrefetchSet.add(firstBlock)


    def pop_front(self):
        return self.prefetch_q.popleft()
    
    def letKnowCenterPoint(self,blockId):
        pass

    def InformL1MissByUser(self,blockId):
        print("User missed to catch in L1: {}\n".format(blockId))

    def InformL1MissAndL2Hit(self,blockId):
        print("User missed to catch in L1 and Hit on L2: {}\n".format(blockId))

    def InformL1MissAndL2Miss(self,blockId):
        print("L1 miss and L2 miss: {}\n".format(blockId))
    
    def prefetch_q_empty(self):
        if(len(self.prefetch_q) == 0):
            return True
        else:
            return False
    
    async def fetchLoop(self):
        while not self.stop_thread:
            print("L1 cache:")
            self.L1Cache.printAllKeys()
            if (not self.prefetch_q_empty()) and (self.L1Cache.usedSize < self.L1Cache.capacity):
                self.L1Cache.printInfo()
                nextBlockId = self.pop_front()
                compressed = self.L2Cache.get(nextBlockId)
                if compressed is None:
                    # L2のプリフェッチポリシーを変更.どうやって？今までキューにたまっているものを捨てる？どうする？わかりまてー－ん。
                    compressed = self.Netif.send_req_urgent(nextBlockId)
                    print("send req urgent sent")
                    original = self.decompressor.decompress(compressed)
                    print("decompression done!")
                    self.L1Cache.put(nextBlockId,original)
                    print()
                else: # L2Hit
                    original = self.decompressor(compressed)
                    self.L1Cache.put(nextBlockId,original)   

                # 忘れずに！
                self.enque_neighbor_blocks(nextBlockId)
            else:
                await asyncio.sleep(0.1)  # Sleep for 1 second, or adjust as needed

    def thread_func(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.fetchLoop())       

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
        self.prefetchedSet = set()
        self.gonnaPrefetchSet = set()
        self.prefetch_q = deque()
        self.blockOffset = blockOffset



# unit test
if __name__ == "__main__":
    print("test")



         



