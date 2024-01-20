import numpy as np
from collections import defaultdict ## thread safe dictionary
import threading
from collections import OrderedDict

class spatial_cache:
    def __init__(self, capacityInMiB, offsetSize=256):
        self.usedSizeInMiB = 0
        self.capacityInMiB = capacityInMiB
        self.SizeOfFloat = 4
        self.offsetSize = offsetSize
        self.BlockX = offsetSize
        self.BlockY = offsetSize
        self.BlockZ = offsetSize
        self.OneBlockSize = offsetSize ** 3 * self.SizeOfFloat
        self.cache = OrderedDict()  # Use OrderedDict to maintain orderなんの
        self.CacheLock = threading.Lock()
        self.radius = 0
        self.printInitInfo()
        self.printInfo()

    def get(self, key):
        with self.CacheLock:
            if key in self.cache:
                return self.cache[key]
        return None

    def put(self, key, value):     # key = tuple, value = {"data":ndarray,"distance":dist_from_userpoint}
        if (self.capacityInMiB) == 0:
            return
        
        with self.CacheLock:
            if key in self.cache:
                pass
            elif self.usedSizeInMiB >= self.capacityInMiB:
                removedItem = self.cache.popitem(last=False) # returns (key,value).
                self.usedSizeInMiB -= removedItem[1].nbytes/1024/1024
            self.cache[key] = value
            print(f"type of a value is {type(value)}")
            # ここ、valueはバイト列だから、lenじゃないとだめ。なんか、
            self.usedSizeInMiB += len(value)/1024/1024 #value.nbytes/1024/1024

    def calHops(self,centerBlockId,targetBlockId):
        timeHops = abs(centerBlockId[1]-targetBlockId[1])
        xHops = abs(centerBlockId[2]- targetBlockId[2])
        yHops = abs(centerBlockId[3]- targetBlockId[3])
        zHops = abs(centerBlockId[4]- targetBlockId[4])
        spaceHops = max(xHops,yHops,zHops)//self.blockOffset # これでホップ数が出る
        return timeHops + spaceHops
    
    def evict_a_block(self,key):
        # Iterate through the OrderedDict using a for loop. # value["distance"],value["data"]
        print("evicting a block")
        data = self.cache.pop(key)
        self.usedSizeInMiB -= data.nbytes/1024/1024

    def getRadiusFromCapacity(self):
        capacityInMiB = self.capacityInMiB
        blockSizeInByte = self.SizeOfFloat*self.blockOffset**3
        print(f"capacityInMiB = {capacityInMiB},blockSizeInByte={blockSizeInByte}")
        while((2*self.radius+1)**3 +2 <= capacityInMiB*1024*1024/blockSizeInByte):
            self.radius += 1
        print(f"L4 caches radius={self.radius}")

    def getUsedSize(self):
        return len(self.cache)
    
    def getUsedSizeInMiB(self):
        return self.usedSizeInMiB
    
    def printInitInfo(self):
        print("############ cache initial info ###########")
        print("capacityInMiB = {}\nblockOffset = {}\n".format(self.capacityInMiB,self.offsetSize))

    def printInfo(self):
        print("usedSizeInMB/capacityInMb = {}/{}\n".format(
            self.usedSizeInMiB,self.capacityInMiB)
            )
        
    def printAllKeys(self):
        keys = self.cache.keys()
        print(keys)

    def clearCache(self):
        self.cache = OrderedDict() 
        self.usedSizeInMiB = 0

    def changeCapacity(self,capacityInMiB):
        self.capacityInMiB = capacityInMiB
        self.OneBlockSize = self.offsetSize ** 3 * self.SizeOfFloat

    def changeBlockoffset(self,blockOffset):
        self.offsetSize = blockOffset
        self.OneBlockSize = self.offsetSize ** 3 * self.SizeOfFloat

    def calCapacityFromMiB(self,MiB):
        self.capacity = MiB*1024*1024*1024/(self.offsetSize**3 * self.SizeOfFloat)
        return self.capacity
    
    def setCacheSizeInGiB(self,GiB):
        self.capacity = GiB*1024*1024*1024/(self.offsetSize**3 * self.SizeOfFloat)
        return self.capacity
    
    def isCacheFull(self):
        return self.capacityInMiB <= self.usedSizeInMiB



# Example usage and test
# if __name__ == "__main__":
#     cache_capacity = 10
#     lru_cache = LRU_cache(cache_capacity)

#     lru_cache.put("key1", "value1")
#     lru_cache.put("key2", "value2")
#     lru_cache.put("key3", "value3")
#     key1 = (0.2,100,1,1,1)
#     key2 = (0.2,100,1,1,1) # 上と同じ
#     key3 = (0.2,100,1,1,2)
#     data = np.random.random_sample((100, 100, 100))
#     lru_cache.put(key1,data)
#     print(lru_cache.get("key2"))  # Output: "value2"
#     print(lru_cache.usedSize)
#     lru_cache.put("key4", "value4")  # This will evict "key1" as it's the least recently used
#     lru_cache.put("key5","data")
#     print(lru_cache.get("key1"))  # Output: None, as "key1" was evicted
#     print(lru_cache.get(key1))
#     print(lru_cache.get(key2))
#     print(lru_cache.get(key3))
#     print(lru_cache.usedSize)

#     if lru_cache.get("key5") == None:
#         print("go get to next level cache")
#     else:
        print("hit!")
