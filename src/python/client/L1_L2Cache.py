import numpy as np
from collections import defaultdict ## thread safe dictionary
import threading

# 最後にリクエストされた点の中心部分を常に追いかける必要がある気がします。
class TSDynamic_cache: # 自分で自分のロックを持っているので、スレッドセーフです
    def __init__(self,capacity,offsetSize):
        self.capacity = capacity
        self.usedSize = 0
        self.usedSizeInMB = 0
        self.SizeOfFloat = 4
        self.offsetSize = offsetSize
        self.BlockX = offsetSize
        self.BlockY = offsetSize
        self.BlockZ = offsetSize
        self.OneBlockSize = offsetSize**3*4/1024/1024
        self.capacityInMB = offsetSize**3*4*capacity/1024/1024
        self.blocksize = self.SizeOfFloat*self.BlockX*self.BlockY*self.BlockZ
        self.cache = {}  # Dictionary to store cached items key = (tol,t,x,y,z), value = compressedData/decompressedData
        self.radius = 100 # for now.
        self.CacheLock = threading.Lock()


    # key = (tol,time,x,y,z), value = compressedData/decompressedData
    def add(self,key,value):
        with self.CacheLock:
            self.cache[key] = value

    def delete(self,key):
        with self.CacheLock:
            self.cache.pop(key)

    # 別スレッドで常に実行。ユーザが見るポイントが変わったら、その点を中心に
    async def radiusSearch(self,userPoint):
        while True:
            # ユーザが見ている点と、注目点の距離がradiusより大きかったらそれを取り出す
            for key, _ in self.cache:
                if (key - userPoint)**2 > self.radius**2:
                    self.delete(key)
                else:
                    # そのデータはほっておいてok
                    pass
            pass

# スレッドセーフになってる
class LRU_cache:
    def __init__(self, capacity=100, offsetSize=256, decompressor=None): # offsetSize知る必要ある？
        self.capacity = capacity
        self.usedSize = 0
        self.usedSizeInMB = 0
        self.SizeOfFloat = 4
        self.offsetSize = offsetSize
        self.BlockX = offsetSize
        self.BlockY = offsetSize
        self.BlockZ = offsetSize
        self.OneBlockSize = offsetSize**3*4/1024/1024
        self.capacityInMB = offsetSize**3*4*capacity/1024/1024
        self.blocksize = self.SizeOfFloat*self.BlockX*self.BlockY*self.BlockZ
        self.cache = {}  # Dictionary to store cached items
        self.order = []  # List to maintain the order of items
        self.CacheLock = threading.Lock()
        self.printInitInfo()
        self.printInfo()


    # key = (tol,timestep,x,y,z) x,y,zはブロックのサイズで割れる値です。
    def get(self, key):
        with self.CacheLock:
            if key in self.cache:
                # Move the accessed item to the end (most recently used)
                self.order.remove(key)
                self.order.append(key)
                return self.cache[key]
            return None

    def put(self, key, value):
        with self.CacheLock:
            maxCapacityFlag = False
            if key in self.cache:
                # Update the value and move the item to the end
                self.order.remove(key)
            elif len(self.cache) >= self.capacity:
                # Evict the least recently used item
                oldest_key = self.order.pop(0)
                self.cache.pop(oldest_key)
                self.usedSize = cache_capacity
                maxCapacityFlag = True
            self.cache[key] = value
            self.order.append(key)
            if not maxCapacityFlag:
                self.usedSize = self.usedSize + 1
                self.usedSizeInMB = self.usedSizeInMB + self.OneBlockSize

    def printInitInfo(self):
        print("############ cache initial info ###########\n")
        print("capacity = {}\nblockOffset = {}\n,capacityInMb = {}".format(self.capacity,self.offsetSize,self.capacity))

    def printInfo(self):
        print("############ cache info ###########\n")
        print("usedSize/capacity = {}/{}\nusedSizeInMB/capacityInMb = {}/{}".format(
            self.usedSize,self.capacity,
            self.usedSizeInMB,self.capacityInMB)
            )

# Example usage and test
if __name__ == "__main__":
    cache_capacity = 10
    lru_cache = LRU_cache(cache_capacity)

    lru_cache.put("key1", "value1")
    lru_cache.put("key2", "value2")
    lru_cache.put("key3", "value3")
    key1 = (0.2,100,1,1,1)
    key2 = (0.2,100,1,1,1) # 上と同じ
    key3 = (0.2,100,1,1,2)
    data = np.random.random_sample((100, 100, 100))
    lru_cache.put(key1,data)
    print(lru_cache.get("key2"))  # Output: "value2"
    print(lru_cache.usedSize)
    lru_cache.put("key4", "value4")  # This will evict "key1" as it's the least recently used
    lru_cache.put("key5","data")
    print(lru_cache.get("key1"))  # Output: None, as "key1" was evicted
    print(lru_cache.get(key1))
    print(lru_cache.get(key2))
    print(lru_cache.get(key3))
    print(lru_cache.usedSize)

    if lru_cache.get("key5") == None:
        print("go get to next level cache")
    else:
        print("hit!")
