import requests
import _mgard as mgard
import numpy as np
import matplotlib.pyplot as plt
import queue
from collections import deque

from L1_L2Cache import LRU_cache
from L1_L2Cache import dynamic_cache


class L2Prefetcher:
    def __init__(self,L2Cache,serverURL="http://localhost:8080") -> None:
        self.URL = serverURL
        # これ何のためだっけ？
        self.Tols = []
        self.maxTimestep = 1024
        self.maxX = 1024
        self.maxY = 1024
        self.maxZ = 1024
        self.default_offset = 256
        self.L2Cache = L2Cache
        self.prefetchedSet = s = set()
        self.fetch_q = deque() # blocks going to get

    def first_contact(self):
        # 初期コンタクトでそれぞれの次元の大きさを決める。
        # ブロックサイズも決める。
        # 5次元のブロックの通し番号のつけ方、さらに隣接しているかどうかの判別の仕方、結構難しいと思う。
        pass

    def enque_neighbor_blocks(self,centerBlock):

        tol = centerBlock[0] 
        timestep = centerBlock[1]
        x = centerBlock[2]
        y = centerBlock[3]
        z = centerBlock[4]

        ## tolをどうするかはちょっと考えてください。粗い方のtolはいらない気がするんですよね。
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


    # ここ、リクエスト情報はヘッダーに入れて、ボディーは科学技術データだけにしたい。
    # 今はurlにパラメータを入れているけど、それじゃあちょっとって感じです。
    def fetch(self,block):

        tol = block[0] 
        timestep = block[1]
        x = block[2]
        y = block[3]
        z = block[4]

        # ここで、L2キャッシュの容量が満杯だったら、リクエストを一回辞められるようにしたいのよね。つまり非同期に処理したいって感じです。
        params = {
            'time': timestep,
            'x': x,
            'y': y,
            'z': z,
            'tol':tol
        }

        blockId = (tol,timestep,x,y,z)

        # ここでブロッキングが発生するのはすごく残念ですね。仕方ないのかな。
        response = requests.get(self.URL, params=params)

        if response.status_code == 200:
            print("Request successful")
            response_content = response.content
            numpy_array = np.frombuffer(response_content, dtype=np.uint8)

            # put to L2 cache by put(key,value) method
            self.L2Cache.put(blockId,numpy_array)
            
            # register the prefetched block to prefetcheSet set.
            self.prefetchedSet(blockId) # Do not forget to abondon it from set when move to L1 cache

            # enque neighbour blocks of input block
            self.enque_neighbor_blocks(blockId)

            return
        
        else:
            print("Request failed")
            return None
    
    # block = (tol,timestep,x,y,z)
    def fetch_test(self,block):


        tol = block[0] 
        timestep = block[1]
        x = block[2]
        y = block[3]
        z = block[4]
        
        # ここで、L2キャッシュの容量が満杯だったら、リクエストを一回辞められるようにしたいのよね。つまり非同期に処理したいって感じです。
        params = {
            'time': timestep,
            'x': x,
            'y': y,
            'z': z,
            'tol':tol
        }

        blockId = (tol,timestep,x,y,z)
        self.prefetchedSet.add(blockId)
        print("fetching {}".format(blockId))

    def urgent_fetch(self,block):
        pass




class L1Prefetcher:
    def __init__(self,decompressor):
        pass


if __name__ == "__main__":

    lru_cache = LRU_cache(capacity=100,offsetSize=256)
    prefetcher = L2Prefetcher(lru_cache)
    tol = 0.1
    t = 0
    x,y,z = 0,0,0
    first_point = (tol,t,x,y,z)
    prefetcher.fetch_test(first_point)
    prefetcher.enque_neighbor_blocks(first_point)

    # フェッチキューがからじゃない間取ってくるだと、無限に取ってきてしまう。L2キャッシュの容量も見ないといけない。
    # L2キャッシュが満杯だったら取ってくるのをやめる、もしくは、L2キャッシュの内容をL1キャッシュに退避させて取り続ける？

    while ((not prefetcher.fetch_q_empty()) 
           and (prefetcher.L2Cache.current_size < prefetcher.L2Cache.capacity)):
        print("curernt_cache_size=",prefetcher.L2Cache.current_size)
        next = prefetcher.pop_front()
        prefetcher.fetch_test(next)
        data = np.random.random_sample(
            (prefetcher.default_offset,prefetcher.default_offset,prefetcher.default_offset))
        lru_cache.put(next,data)
        prefetcher.enque_neighbor_blocks(next)


         



