import numpy as np
from collections import defaultdict ## thread safe dictionary
import threading
from collections import OrderedDict

# 最後にリクエストされた点の中心部分を常に追いかける必要がある気がします。
class TSDynamic_cache: # 自分で自分のロックを持っているので、スレッドセーフです
    def __init__(self,capacity,offsetSize):
        self.capacity = capacity
        self.usedSize = 0
        self.usedSizeInMiB = 0
        self.SizeOfFloat = 4
        self.offsetSize = offsetSize
        self.BlockX = offsetSize
        self.BlockY = offsetSize
        self.BlockZ = offsetSize
        self.OneBlockSize = offsetSize**3*4/1024/1024
        self.capacityInMiB = offsetSize**3*4*capacity/1024/1024
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
    def __init__(self, capacityInMiB, offsetSize=256):
        self.usedSizeInMiB = 0
        self.SizeOfFloat = 4
        self.offsetSize = offsetSize
        self.BlockX = offsetSize
        self.BlockY = offsetSize
        self.BlockZ = offsetSize
        self.OneBlockSize = offsetSize ** 3 * self.SizeOfFloat
        self.capacityInMiB = capacityInMiB
        self.cache = OrderedDict()  # Use OrderedDict to maintain order
        self.CacheLock = threading.Lock()
        self.printInitInfo()
        self.printInfo()

    def get(self, key):
        with self.CacheLock:
            if key in self.cache:
                self.cache.move_to_end(key)
                return self.cache[key]
        return None

    def put(self, key, value):
        if self.capacityInMB == 0:
            return
        with self.CacheLock:
            if key in self.cache:
                self.cache.move_to_end(key)
            # elif len(self.cache) >= self.capacity:
            elif self.usedSizeInMiB > self.capacityInMiB:
                # Evict the least recently used item
                removedItem = self.cache.popitem(last=False)
                self.usedSizeInMiB -= removedItem[1].nbytes/1024/1024
            self.cache[key] = value
            self.usedSizeInMiB += value.nbytes/1024/1024

    def getUsedSize(self):
        return len(self.cache)
    
    def getUsedSizeInMiB(self):
        return self.usedSizeInMB
    

    def printInitInfo(self):
        print("############ cache initial info ###########")
        print("capacity = {}\nblockOffset = {}\ncapacityInMb = {}\n".format(self.capacity,self.offsetSize,self.capacity))

    def printInfo(self):
        print("usedSizeInMB/capacityInMb = {}/{}\n".format(
            self.getUsedSizeInMb(),self.capacityInMB)
            )
        
    def printAllKeys(self):
        keys = self.cache.keys()
        print(keys)

    def clearCache(self):
        self.cache = OrderedDict() 

    def changeCapacity(self,capacity):
        self.capacity = capacity
        self.capacityInMiB = self.offsetSize ** 3 * self.SizeOfFloat * capacity / 1024 / 1024
        self.OneBlockSize = self.offsetSize ** 3 * self.SizeOfFloat

    def changeBlockoffset(self,blockOffset):
        self.offsetSize = blockOffset
        self.OneBlockSize = self.offsetSize ** 3 * self.SizeOfFloat
        self.capacityInMiB = self.offsetSize ** 3 * self.SizeOfFloat * self.capacity / 1024 / 1024

    def calCapacityFromGiB(self,GiB):
        self.capacity = GiB*1024*1024*1024/(self.offsetSize**3 * self.SizeOfFloat)
        self.capacityInMiB = GiB*1024
        return self.capacity
    
    def setCacheSizeInGiB(self,GiB):
        self.capacity = GiB*1024*1024*1024/(self.offsetSize**3 * self.SizeOfFloat)
        self.capacityInMiB = GiB*1024
        return self.capacity


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
