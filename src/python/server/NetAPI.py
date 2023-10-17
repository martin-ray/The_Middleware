from collections import deque
import asyncio
import numpy as np
import threading
from slice import Slicer
from compressor import compressor
from L3_L4Cache import LRU_cache
from prefetcher import L3Prefetcher,L4Prefetcher

class HttpAPI:
    def __init__(self,L3CacheSize=500,L4CacheSize=250,blockSize=256,serverIp="http://localhost:8080"):
        self.L3Cache = LRU_cache(L3CacheSize)
        self.L4Cache = LRU_cache(L4CacheSize)
        self.compressor = compressor(self.L3Cache)
        self.Slicer = Slicer()
        self.L4Pref = L4Prefetcher(L4Cache=self.L4Cache)
        self.L3Pref = L3Prefetcher(self.L3Cache, self.L4Cache, compressor=self.compressor, L4Prefetcher=self.L4Pref)
        self.sendQ = deque() # いる？
        self.blockSize = blockSize

    def reInit(self,L3CacheSize,L4CacheSize,blockSize,policy='LRU'):
        self.blockSize = blockSize

        # 別スレッドで走っているプリフェッチを停止
        # RuntimeError: threads can only be started onceというエラーをいただきましたので、
        # 止めずにやる / 新しくスレッドを作るのにたくですね。
        print("stopping the prefetch thread")
        self.L3Pref.stop()
        self.L4Pref.stop()

        # プリフェッチのサイズも変更
        self.L3Pref.blockOffset = self.blockSize
        self.L4Pref.blockOffset = self.blockSize
        self.Slicer.changeBlockSize = self.blockSize

        # サイズを変更
        print("changin the cache size and block offset")
        self.L3Cache.changeCapacity(L3CacheSize)
        self.L4Cache.changeCapacity(L4CacheSize)
        
        # キャッシュをクリア
        print("clearing the cache")
        self.L3Cache.clearCache()
        self.L4Cache.clearCache()
        
        # 別スレッドで動いているぷりふぇっちゃーの設定を変更
        self.L3Pref.InitializeSetting()
        self.L4Pref.InitializeSetting()

        # 情報を出力
        print("restarting the system with the following setting:\n")
        print("L3Size:{}\nL4Size:{}\nblockSize:{}\nReplacementPolicy:{}\n".format
              (self.L3Cache.capacity,
               self.L4Cache.capacity,
               self.blockSize,
               "LRU for now"))
        
        print("start prefetching")

        # # プリフェッチを開始
        self.L3Pref.startPrefetching()
        self.L4Pref.startPrefetching()

    # 呼び出し側が、別スレッドで実行
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
        
    # tuple is imutable
    def adjustBlockId(self,blockId):
        blockId2 = blockId[2]//self.blockSize*self.blockSize
        blockId3 = blockId[3]//self.blockSize*self.blockSize
        blockId4 = blockId[4]//self.blockSize*self.blockSize
        return (blockId[0],blockId[1],blockId2,blockId3,blockId4)

class NetAPIWebsock:
    def __init__(self,L3Cache,serverIp="http://localhost:8080"):
        self.L3Cache = L3Cache
        self.sendQ = deque() 
        pass

    # 末尾に追加。これはwebsocketだったらいいよね。ただ、httpだったら、incoming requestに対して、必ず返さないとだめ。それが面倒くさいのか～って話だよね。
    def send_req(self,blockId):
        self.sendQ.append(blockId)
    
    # 緊急なので、前に追加
    def send_req_urgent(self,blockId):
        self.sendQ.appendleft(blockId)
    
    def IsSendQEmpty(self):
        if(len(self.sendQ) == 0):
            return True
        else:
            return False
    
    async def listenLoop(self):
        pass
    
    # 実際に送信。これは別スレッドで実行される
    async def sendLoop(self):
        while True:
            if self.IsSendQEmpty():
                await asyncio.sleep(0.1)
            else:
                req = self.sendQ.popleft()
                print("sending ",req)


