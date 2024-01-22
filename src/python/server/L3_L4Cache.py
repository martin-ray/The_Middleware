import numpy as np
import threading
from collections import OrderedDict
import sys

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
        self.cache = {} # OrderedDict()  # Use OrderedDict to maintain orderなんの
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
            else:
                self.cache[key] = value
                self.usedSizeInMiB += len(value)/1024/1024
      


        # if (self.capacityInMiB) == 0:
        #     return
        
        # with self.CacheLock:
        #     if key in self.cache:
        #         pass
        #     elif self.usedSizeInMiB >= self.capacityInMiB:
        #         removedItem = self.cache.popitem(last=False) # returns (key,value).
        #         self.usedSizeInMiB -=  len(removedItem[1])/1024/1024# removedItem[1].nbytes/1024/1024
        #     self.cache[key] = value
        #     self.usedSizeInMiB += len(value)/1024/1024

    def calHops(self,centerBlockId,targetBlockId):
        timeHops = abs(centerBlockId[1]-targetBlockId[1])
        xHops = abs(centerBlockId[2]- targetBlockId[2])
        yHops = abs(centerBlockId[3]- targetBlockId[3])
        zHops = abs(centerBlockId[4]- targetBlockId[4])
        spaceHops = max(xHops,yHops,zHops)//self.blockOffset # これでホップ数が出る
        return timeHops + spaceHops
    
    def evict_a_block(self,key):
        print("evictiong a block")
        block = self.cache.pop(key)
        self.usedSizeInMiB -= len(block)/1024/1024


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

