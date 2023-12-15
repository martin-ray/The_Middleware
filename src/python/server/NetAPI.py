from collections import deque
import asyncio
import numpy as np
import threading
from slice import Slicer
from compressor import compressor
from L3_L4Cache import LRU_cache
from L3_L4prefetcher import L3Prefetcher,L4Prefetcher
import time
import threading
from flag import Flag
import time


class HttpAPI:
    def __init__(self,L3CacheSize=4096*8,L4CacheSize=0,blockSize=256,serverIp="http://localhost:8080"):
        # user is coming flag to control the GPU and storage resource
        self.userUsingGPU = Flag()
        self.userUsingStorage = Flag()
        self.Slicer = Slicer(blockOffset=blockSize)
        self.DataDim = self.Slicer.getDataDim()
        self.L3Cache = LRU_cache(L3CacheSize,offsetSize=blockSize)
        self.L4Cache = LRU_cache(L4CacheSize,offsetSize=blockSize)
        self.compressor = compressor(self.L3Cache)
        self.L4Pref = L4Prefetcher(self.L4Cache,dataDim=self.DataDim,blockSize=blockSize,userUsingGPU=self.userUsingGPU,userUsingStorage=self.userUsingStorage)
        self.L3Pref = L3Prefetcher(self.L3Cache, self.L4Cache,dataDim=self.DataDim,
                                   L4Prefetcher=self.L4Pref,blockOffset=blockSize,
                                   userUsingGPU=self.userUsingGPU,userUsingStorage=self.userUsingStorage)
        self.sendQ = deque() # いる？
        self.blockSize = blockSize

        # for stats
        self.numReqs = 0
        self.numL3Hit = 0
        self.numL4Hit = 0
        self.numL3L4Miss = 0 # numReqs == numL3Hit + numL4Hit + numL3L4Missって計算式になります



    def reInit(self,L3CacheSize,L4CacheSize,blockSize,policy='LRU'):
        self.blockSize = blockSize

        # 別スレッドで走っているプリフェッチを停止
        # RuntimeError: threads can only be started onceというエラーをいただきましたので、
        # 止めずにやる / 新しくスレッドを作るのにたくですね。
        print("stopping the prefetch thread")
        self.L3Pref.stop()
        self.L4Pref.stop()
        print("waiting for the threads to finish...")
        time.sleep(10)

        # プリフェッチのサイズも変更
        self.L3Cache.changeBlockoffset(self.blockSize)
        self.L4Cache.changeBlockoffset(self.blockSize)

        # スライサにもブロックサイズの変更を伝達 (CAUTION!!) L3prefetcherとL4Prefethcerは別々でSlicerインスタンスを持っているので、それもやらないとだめです！！！
        self.Slicer.changeBlockSize(self.blockSize) 
        print("changed block size in slicer!")
        self.Slicer.printBlocksize()

        # サイズを変更
        print("changing the cache size and block offset")
        self.L3Cache.changeCapacity(L3CacheSize)
        self.L4Cache.changeCapacity(L4CacheSize)
        
        # キャッシュをクリア
        print("clearing the cache")
        self.L3Cache.clearCache()
        self.L4Cache.clearCache()

        # スタッツをクリア
        self.numReqs = 0
        self.numL3Hit = 0
        self.numL4Hit = 0
        self.numL3L4Miss = 0
        
        # 別スレッドで動いているぷりふぇっちゃーの設定を変更
        self.L3Pref.InitializeSetting(self.blockSize)
        self.L4Pref.InitializeSetting(self.blockSize)

        # 情報を出力
        print("restarting the system with the following setting:\n")
        print("L3Size:{}\nL4Size:{}\nblockSize:{}\nReplacementPolicy:{}\n".format
              (self.L3Cache.capacityInMiB,
               self.L4Cache.capacityInMiB,
               self.blockSize,
               "LRU for now"))
        
        print("start prefetching")

        # # プリフェッチを開始
        self.L4Pref.startPrefetching()
        time.sleep(0.1) # これをやらないとL4のプリフェッチが始まらない。L3に消されちゃって (おそらく)
        self.L3Pref.startPrefetching()


    # 呼び出し側が、別スレッドで実行
    def getUsr(self,blockId):
        # ユーザが来たので、ほかのリソースはみんないったん止まってくださいってことです。
        print("locked the GPU access")
        start_time = time.time()
        tol = blockId[0]
        L3data = self.L3Cache.get(blockId)
        self.numReqs += 1
        if L3data is None:
            L4data = self.L4Cache.get(blockId)

            if L4data is None:
                self.numL3L4Miss += 1
                self.L3Pref.InformL3MissAndL4Miss(blockId) # ここで知らせることで、2じゅうにフェッチすることを防いでいます。
                self.L4Pref.InformL3MissAndL4Miss(blockId) # プリフェッチポリシーの変更はプリふぇっちゃー側で変更してください
                
                # ここ、L3とL4キャッシュに登録しなくても大丈夫か？まあいいか。
                start_reading_time = time.time()
                self.userUsingStorage.set_lock()
                original = self.Slicer.sliceData(blockId)
                self.userUsingStorage.unlock()
                end_reading_time = time.time()
                
                self.userUsingGPU.set_lock()
                compressed = self.compressor.compress(original,tol)
                self.userUsingGPU.unlock()
                end_compression_time = time.time()
                
                print(f"time_to_read={end_reading_time-start_reading_time}\ntime_to_compress={end_compression_time-end_reading_time}")
                return compressed
            
            else:
                self.numL4Hit += 1

                self.L3Pref.InformL3MissAndL4Hit(blockId)
                self.L4Pref.InformL3MissAndL4Hit(blockId)
                
                start_compressing_time = time.time()
                self.userUsingGPU.set_lock()
                compressed = self.compressor.compress(L4data,tol)
                self.userUsingGPU.unlock()
                end_compressing_time = time.time()
                
                print(f"time_to_compress={end_compressing_time-start_compressing_time}")
                return compressed
            
        else:
            self.numL3Hit += 1
            self.L3Pref.InformL3Hit(blockId)
            self.L4Pref.InformL3Hit(blockId)
            L3_hit_time = time.time()
            print(f"time_to_read_from_l3={L3_hit_time-start_time}")
            return L3data
        

        
    def get(self,blockId):
        tol = blockId[0]
        L3data = self.L3Cache.get(blockId)
        if L3data is None:
            L4data = self.L4Cache.get(blockId)
            if L4data is None:
                self.L3Pref.InformL3MissAndL4Miss(blockId)
                self.L4Pref.InformL3MissAndL4Miss(blockId) # プリフェッチポリシーの変更はプリふぇっちゃー側で変更してください
                original = self.Slicer.sliceData(blockId)
                compressed = self.compressor.compress(original,tol)
                return compressed
            else:
                self.L3Pref.InformL3MissAndL4Hit(blockId)
                self.L4Pref.InformL3MissAndL4Hit(blockId)
                return self.compressor.compress(L4data,tol)
        else:
            self.L3Pref.InformL3Hit(blockId)
            self.L4Pref.InformL3Hit(blockId)
            return L3data
    
    def getOriginal(self,blockId):
        tol = blockId[0]
        self.numReqs += 1
        L4data = self.L4Cache.get(blockId)
        if L4data is None:
            self.numL3L4Miss += 1
            self.L3Pref.InformL3MissAndL4Miss(blockId)
            self.L4Pref.InformL3MissAndL4Miss(blockId) # プリフェッチポリシーの変更はプリふぇっちゃー側で変更してください
            original = self.Slicer.sliceData(blockId)
            return original
        else:
            self.numL4Hit += 1
            self.L3Pref.InformL3MissAndL4Hit(blockId)
            self.L4Pref.InformL3MissAndL4Hit(blockId)
            return L4data
        
    # tuple is imutable
    def adjustBlockId(self,blockId):
        blockId2 = blockId[2]//self.blockSize*self.blockSize
        blockId3 = blockId[3]//self.blockSize*self.blockSize
        blockId4 = blockId[4]//self.blockSize*self.blockSize
        return (blockId[0],blockId[1],blockId2,blockId3,blockId4)
    

    def informUserPoint(self,blockId):
        self.L3Pref.InformUserPoint(blockId)
        self.L4Pref.InformUserPoint(blockId)
