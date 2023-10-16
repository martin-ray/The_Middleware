import numpy as np
import threading
from collections import OrderedDict

class LRU_cache_old:
    def __init__(self, capacity,offsetSize=100): # offsetSize知る必要ある？
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
        maxCapacityFlag = False
        with self.CacheLock:
            if key in self.cache:
                # Update the value and move the item to the end
                self.order.remove(key)
            elif len(self.cache) >= self.capacity:
                # Evict the least recently used item. これのtimecomplextyがO(n)なので、別のやつにしました
                oldest_key = self.order.pop(0)
                self.cache.pop(oldest_key)
                self.usedSize = self.capacity
                maxCapacityFlag = True
                print("cache is full! replacing!")
            self.cache[key] = value
            self.order.append(key)
            if not maxCapacityFlag:
                self.usedSize = self.usedSize + 1
                self.usedSizeInMB = self.usedSizeInMB + self.OneBlockSize

    def printInitInfo(self):
        print("############ cache initial info ###########")
        print("capacity = {}\nblockOffset = {}\ncapacityInMb = {}\n".format(self.capacity,self.offsetSize,self.capacity))

    def printInfo(self):
        print("usedSizeInMB/capacityInMb = {}/{}\n".format(
            self.usedSizeInMB,self.capacityInMB)
            )
        
    def printAllKeys(self):
        keys = self.cache.keys()
        print(keys)

    def clearCache(self):
        self.cache = {}
        self.order = []

    def changeCapacity(self,capacity):
        self.capacity = capacity


class LRU_cache:
    def __init__(self, capacity, offsetSize=256):
        self.capacity = capacity ## block that can be store
        self.usedSize = 0
        self.usedSizeInMB = 0
        self.SizeOfFloat = 4
        self.offsetSize = offsetSize
        self.BlockX = offsetSize
        self.BlockY = offsetSize
        self.BlockZ = offsetSize
        self.OneBlockSize = offsetSize ** 3 * self.SizeOfFloat
        self.capacityInMB = offsetSize ** 3 * self.SizeOfFloat * capacity / 1024 / 1024
        self.cache = OrderedDict()  # Use OrderedDict to maintain order
        self.CacheLock = threading.Lock()
        self.printInitInfo()
        self.printInfo()

    def get(self, key):
        with self.CacheLock:
            if key in self.cache:
                # Move the accessed item to the end
                self.cache.move_to_end(key)
                return self.cache[key]
        return None

    def put(self, key, value):
        with self.CacheLock:
            if key in self.cache:
            # If the key already exists, move it to the end
                self.cache.move_to_end(key)
            elif len(self.cache) >= self.capacity:
                # Evict the least recently used item (first item in OrderedDict)
                self.cache.popitem(last=False)
                print("cache is full! replacing!")
            self.cache[key] = value

    def getUsedSize(self):
        return len(self.cache)
    
    def getUsedSizeInMb(self):
        return self.OneBlockSize*len(self.cache)/1024/1024
    

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
        self.cache = {}
        self.order = []

    def changeCapacity(self,capacity):
        self.capacity = capacity
    
    def changeBlockoffset(self,blockOffset):
        self.offsetSize = blockOffset

class dynamic_cache:
    def __init__(self,size):
        self.size = size
    
    def add(self):
        pass
    def prefetch(self):
        pass


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

    
    lru_cache.put("key4", "value4")  # This will evict "key1" as it's the least recently used
    lru_cache.put("key5","data")
    print(lru_cache.get("key1"))  # Output: None, as "key1" was evicted
    print(lru_cache.get(key1))
    print(lru_cache.get(key2)) # key2 == key1なのでね。
    print(lru_cache.get(key3))

    if lru_cache.get("key5") == -1:
        print("go get to next level cache")
    else:
        print("hit!honto?")
