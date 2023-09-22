import requests
import _mgard as mgard
import numpy as np
import matplotlib.pyplot as plt
import queue
from collections import deque

from L1_L2Cache import LRU_cache
from L1_L2Cache import dynamic_cache


class Prefetcher:
    def __init__(self,L2Cache,serverURL="http://localhost:8080") -> None:
        self.URL = serverURL
        # これ何のためだっけ？
        self.Tols = []
        self.default_offset = 256
        self.L2Cache = L2Cache
        self.prefetchedSet = s = set()
        self.q = deque()

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

        ## tolをどうするかはちょっと考えてください。
        for dt in [-1,0,1]:
            for dx in [-self.default_offset, 0, self.default_offset]:
                for dy in [-self.default_offset, 0, self.default_offset]:
                    for dz in [-self.default_offset, 0, self.default_offset]:
                        if self.prefetchedSet.__contains__((tol,timestep+dt, x+dx, y+dy, z+dz)):
                            continue
                        else:
                            self.q.append((tol,timestep+dt, x+dx, y+dy, z+dz))



    def fetch(self,timestep,x,y,z,tol):

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
    

    def urgent_fetch(self,timestep,x,y,z,tol):
        pass


