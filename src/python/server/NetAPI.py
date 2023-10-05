# すべてのリクエストはここを通ってなされます。
# NetIFはL1も持ってるし、L2も持ってます。
# まあ、こいつは、ただ、L1とL2からリクエストを受けて、そのリクエストをサーバに投げるってだけだな。
# 戻ってくるデータは全部compressedされている。L1がリクエストしたら、それをdecompressするまでセットかな。
# ただ、気になるのが、L1からのリクエストは緊急なわけです。L2はどんどんリクエスト送るけど、
# L1のリクエストを優先する何か、仕組みが欲しいんですね。


# dequeはスレッドセーフ
from collections import deque
import asyncio
import numpy as np
import threading
from slice import Slicer

class HttpAPI:
    def __init__(self,L3Cache,L4Cache,Slicer,compressor,serverIp="http://localhost:8080"):
        self.L3Cache = L3Cache
        self.L4Cache = L4Cache
        self.Slicer = Slicer
        self.compressor = compressor
        self.sendQ = deque()

    def get(self,blockId):
        L3data = self.L3Cache.get(blockId)
        if L3data == None:
            L4data = self.L4Cache.get(blockId)
            if L4data == None:
                original = self.Slicer.sliceData(blockId)
                compressed = self.compressor.compress(original)
                return compressed
            else:
                return self.compressor.compress(L4data)
        else:
            return L3data

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


