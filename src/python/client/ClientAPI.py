import numpy as np
from decompressor import Decompressor
from NetInterface import NetIF
from L1_L2prefetcher import L2Prefetcher,L1Prefetcher
from L1_L2Cache import LRU_cache
from L1_L2Cache import spatial_cache
from recomposer import Recomposer
import threading
import time
import concurrent.futures

class ClientAPI:
    def __init__(self,L1Size, L2Size, L3Size, L4Size,blockSize=256,
                 L1PrefOn=True,L2PrefOn=True,L3PrefOn=True,L4PrefOn=True,
                 serverURL="http://172.20.2.254:8080"): 

        self.serverURL = serverURL
        self.L1CacheSize = L1Size
        self.L2CacheSize = L2Size
        self.L3CacheSize = L3Size
        self.L4CacheSize = L4Size
        self.blockOffset = blockSize

        # GPUの利用権。できればロックフリーにしたいんだけど、さすがに俺には難しい。
        self.GPUmutex = threading.Lock()
        

        self.L1Cache = spatial_cache(self.L1CacheSize,self.blockOffset)
        self.L2Cache = spatial_cache(self.L2CacheSize,self.blockOffset)
        self.decompressor = Decompressor(L1Cache=self.L1Cache)

        # sendLoop threadはconstructorの中で起動 -> いや、起動しなくてよくね？L2が自分で取りに行く方式にする
        self.netIF = NetIF(L2Cache=self.L2Cache,serverURL=self.serverURL)

        # 初期コンタクト
        response_code = self.netIF.firstContact(BlockOffset=blockSize,L3Size=L3Size,L4Size=L4Size)
        if (response_code != 200):
            print("initialization failed in server.")
            exit(0)
        else:
            print("Initalization Success")

        # fetchLoop threadはconstructorの中で起動
        self.L2pref = L2Prefetcher(L2Cache=self.L2Cache,GPUmutex=self.GPUmutex,serverURL=self.serverURL) 

        # fetchLoop threadはconstructorの中で起動。L1prefは自分でdecompressorのインスタンスを持っている
        self.L1pref = L1Prefetcher(L1Cache=self.L1Cache,L2Cache=self.L2Cache,offsetSize=self.blockOffset,GPUmutex=self.GPUmutex)
        self.recomposer = Recomposer(blockOffset=self.blockOffset)

        # スレッド数
        self.thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=8)

        # stats (L1Hit L2Hit ServerRequest)
        self.numL1Hit = 0
        self.numL2Hit = 0
        self.numReqTime = 0
        self.DecompElapsed = [] 

    def reInit(self,L1CacheSize,L2CacheSize,L3CacheSize,L4CacheSize,blockSize,policy='LRU'):
        self.blockSize = blockSize

        # 別スレッドで走っているプリフェッチを停止 (RuntimeError: threads can only be started onceに注意)
        print("stopping the prefetch thread")
        self.L1pref.stop()
        self.L2pref.stop()

        # プリフェッチのサイズも変更
        self.L1Cache.changeBlockoffset(self.blockSize)
        self.L2Cache.changeBlockoffset(self.blockSize)

        # サイズを変更
        print("changin the cache size and block offset")
        self.L1Cache.changeCapacity(L1CacheSize)
        self.L2Cache.changeCapacity(L2CacheSize)
        self.L1CacheSize = L1CacheSize
        self.L2CacheSize = L2CacheSize
        self.L3CacheSize = L3CacheSize
        self.L4CacheSize = L4CacheSize
        
        # キャッシュをクリア
        print("clearing the cache")
        self.L1Cache.clearCache()
        self.L2Cache.clearCache()
        
        # 別スレッドで動いているぷりふぇっちゃーの設定を変更
        self.L1pref.InitializeSetting(self.blockSize)
        self.L2pref.InitializeSetting(self.blockSize)

        # スタッツをクリア
        self.numL1Hit = 0
        self.numL2Hit = 0
        self.numReqTime = 0
        self.DecompElapsed = []

        # 情報を出力
        print("Restarting the system with the following setting:\n")
        print("L3Size:{}\nL4Size:{}\nblockSize:{}\n".format
              (self.L1CacheSize,
               self.L2CacheSize,
                self.L3Cache.capacity,
               self.L4Cache.capacity,
               self.blockSize,
               ))
        
        
        self.netIF.reInitRequest(self.blockOffset,L3CacheSize,L4CacheSize)
        print("Request accepted by the Server")

        time.sleep(6) # give the server some time
        print("Start prefetching")

        # プリフェッチを開始
        self.L2pref.startPrefetching()
        self.L1pref.startPrefetching()

    def StopPrefetching(self):
        print("Stopping the prefetch thread")
        self.L1pref.stop()
        self.L2pref.stop()
        
        print("Clearing the cache")
        self.L1Cache.clearCache()
        self.L2Cache.clearCache()    

    
    
    def L2MissHandler(self,blockId,BlockAndData):

        compressed = self.netIF.send_req_urgent_usr(blockId)
        self.L2Cache.put(blockId,compressed)

        decomp_start = time.time()
        original = self.decompressor.decompress(compressed)
        decomp_end = time.time()

        self.L1Cache.put(blockId,original)
        print("Put Data to L1 by L2MissHandler!")
        self.DecompElapsed.append(decomp_end - decomp_start)
        BlockAndData[blockId] = original


    def L2HitHandler(self,blockId,BlockAndData):
        
        compressed = self.L2Cache.get(blockId)

        decomp_start = time.time()
        original = self.decompressor.decompress(compressed)
        decomp_end = time.time()

        self.L1Cache.put(blockId,original)
        print("Put Data to L1 by L2HitHandler!")
        self.DecompElapsed.append(decomp_end - decomp_start)
        BlockAndData[blockId] = original

    def getBlocksById(self, blockId):
        pass


    def getBlocks(self, tol, timestep, x, y, z, xEnd, yEnd, zEnd):
        req = (x,xEnd,y,yEnd,z,zEnd)
        # print("request:",req)
        BlockIds = self.Block2BlockIds(tol, timestep, x, y, z, xEnd, yEnd, zEnd)
        # print("to ",BlockIds)
        BlockAndData = {}
        threads = []

        for blockId in BlockIds:
            L1data = self.L1Cache.get(blockId)

            # inform user point to all prefetchers
            self.L2pref.InformUserPoint(blockId)
            self.L1pref.InformUserPoint(blockId)
            self.netIF.send_user_point(blockId)

            if L1data is None: # L1 Miss

                print("L1 Miss Happend")
                self.L1pref.InformL1MissByUser(blockId)
                L2data = self.L2Cache.get(blockId)

                if L2data is None: # L2 Miss
                    print("L2 Miss Happend")
                    self.numReqTime += 1
                    self.L2pref.InformL2MissByUser(blockId)
                    future = self.thread_pool.submit(self.L2MissHandler, blockId, BlockAndData)
                    threads.append(future)

                else: # L2 Hit
                    print("L2 Hit")
                    self.numL2Hit += 1
                    self.L2pref.InformL1MissL2HitByUser(blockId)
                    future = self.thread_pool.submit(self.L2HitHandler, blockId, BlockAndData)
                    threads.append(future)

            else: # L1 Hit!
                print("L1 hit")
                self.DecompElapsed.append(0)
                self.numL1Hit += 1
                BlockAndData[blockId] = L1data

        concurrent.futures.wait(threads)

        # BlockAndData = (key,value) = (blockId,OriginalData),  xyzRange = (x,xOffset,y,yOffset,z,zOffset) -> recomposed data.
        xyzRange = (x,xEnd,y,yEnd,z,zEnd)
        recompsedArray = self.recomposer.recompose(BlockAndData,xyzRange)
        return recompsedArray
    

    # 端っこは切り上げ、下側は切り下げ
    def Block2BlockIds(self,tol,timestep,x,y,z,xEnd,yEnd,zEnd):
        xStartIdx = x//self.blockOffset*self.blockOffset
        xEndPointIdx = (xEnd)//self.blockOffset*self.blockOffset # + self.blockOffset -1 
        xStartIdxs = np.arange(xStartIdx,xEndPointIdx,self.blockOffset)

        # yStartIdx = y//self.blockOffset*self.blockOffset
        # yEndPointIdx = (y + yOffset + self.blockOffset)//self.blockOffset*self.blockOffset
        # if (y + yOffset) % self.blockOffset == 0:
        #     yEndPointIdx = (y + yOffset)//self.blockOffset*self.blockOffset
        # xStartIdxs = np.arrange(yStartIdx,yEndPointIdx,self.blockOffset)
        yStartIdx = y//self.blockOffset*self.blockOffset
        yEndPointIdx = (yEnd)//self.blockOffset*self.blockOffset # + self.blockOffset -1 
        yStartIdxs = np.arange(yStartIdx,yEndPointIdx,self.blockOffset)

        zStartIdx = z//self.blockOffset*self.blockOffset
        zEndPointIdx = (zEnd)//self.blockOffset*self.blockOffset # + self.blockOffset -1 
        # zEndPointIdxは入らないから気をつけて
        zStartIdxs = np.arange(zStartIdx,zEndPointIdx,self.blockOffset)

        BlockIds = []
        for xIdx in xStartIdxs:
            for yIdx in yStartIdxs:
                for zIdx in zStartIdxs:
                    BlockIds.append((tol,timestep,xIdx,yIdx,zIdx))
        
        return BlockIds

    def GetStats(self):
        # サーバからのスタッツを取ってくる
        stats = self.netIF.requestStats()

        # クライアント側のスタッツ
        stats["nL1Hit"] = self.numL1Hit
        stats["nL2Hit"] = self.numL2Hit
        stats["reqs"] = self.numReqTime
        stats["DecompElapsed"] = self.DecompElapsed
        return stats
