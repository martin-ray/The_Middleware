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
        # ここで、送信スレッドを起動する
        self.thread = threading.Thread(target=self.thread_func(self.sendLoop))
        self.thread.start()

    # 末尾に追加
    def send_req(self,blockId):
        self.sendQ.append(blockId)
    
    # 緊急なので、前に追加、というより、もうすぐにリクエスト送らないとだめじゃね？
    def send_req_urgent(self,BlockId):

        header = {
            'type':'BlockReq',
            'tol':BlockId[0],
            'timestep':BlockId[1],
            'x': BlockId[2],
            'y': BlockId[3],
            'z': BlockId[4]
        }

        response = requests.get(self.URL,headers=header)
        return response.content
    
    def IsSendQEmpty(self):
        if(len(self.sendQ) == 0):
            return True
        else:
            return False
    
    def firstContact(self,BlockOffset):
        header = {
            'type':'FirstContact',
            'offset':BlockOffset
        }
        response = requests.get(self.URL,headers=header)
        return response.status_code
    
    # 別スレッドで実行される送信ループ
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

    def thread_func(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.sendLoop())   


    # TODO websocketのついか
    async def sendLoopSocket(websocket):
        pass