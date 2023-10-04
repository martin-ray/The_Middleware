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
import requests

class NetIF:
    def __init__(self,L2Cache,serverIp="http://localhost:8080"):
        self.L2Cache = L2Cache
        self.sendQ = deque() 
        self.URL = serverIp
        pass

    # 末尾に追加
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
        
    # 実際に送信。これは別スレッドで実行される
    async def sendLoop(self):
        while True:
            if self.IsSendQEmpty():
                await asyncio.sleep(0.1)
            else:
                BlockId = self.sendQ.popleft()
                
                header = {
                    'tol':BlockId[0],
                    'timestep':BlockId[1],
                    'x': BlockId[2],
                    'y': BlockId[3],
                    'z': BlockId[4]
                }

                response = requests.get(self.URL,headers=header)
                self.L2Cache.put(BlockId,response.content)
