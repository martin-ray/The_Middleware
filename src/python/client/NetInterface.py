from collections import deque
import asyncio
import numpy as np
import threading
import requests
import time

class NetIF:
    def __init__(self,L2Cache,serverURL="http://172.20.2.253:8080"):
        self.L2Cache = L2Cache
        # self.sendQ = deque() 
        self.URL = serverURL

        # # ここで、送信スレッドを起動する
        # self.thread = threading.Thread(target=self.net_thread_func)
        # self.thread.start()

        # for stats
        self.networkLatencys = []

    
    def send_user_point(self,BlockId):
        
        header = {
            'type':'userPoint',
            'tol':str(BlockId[0]),
            'timestep':str(BlockId[1]),
            'x': str(BlockId[2]),
            'y': str(BlockId[3]),
            'z': str(BlockId[4])
        }

        requests.get(self.URL,headers=header)
        return
    
    
    # プリフェッチャのリクエストはこっちで処理される
    def send_req_urgent(self,BlockId):

        header = {
            'type':'BlockReq',
            'tol':str(BlockId[0]),
            'timestep':str(BlockId[1]),
            'x': str(BlockId[2]),
            'y': str(BlockId[3]),
            'z': str(BlockId[4])
        }
        response = requests.get(self.URL,headers=header)

        return response.content

    # ユーザからのリクエストはこっちで処理される
    def send_req_urgent_usr(self,BlockId):

        header = {
            'type':'BlockReqUsr',
            'tol':str(BlockId[0]),
            'timestep':str(BlockId[1]),
            'x': str(BlockId[2]),
            'y': str(BlockId[3]),
            'z': str(BlockId[4])
        }

        start_time = time.time()*1000
        response = requests.get(self.URL,headers=header)
        end_time = time.time()*1000

        # Extract the timestamp from the response headers
        network_time = int(response.headers.get('X-Network-Time', -1))
        
        if network_time != -1:
            transfer_time = end_time - network_time
            self.networkLatencys.append(transfer_time/1000)
            # print(f"Network Transfer Time: {transfer_time} ms")
        else:
            print("failed to get data network data!! FUCK")
        
        return response.content
    


    def requestStats(self):

        header = {
            'type':'getStats'
        }

        response = requests.get(self.URL, headers=header).json()
        response["networkLatencys"] = self.networkLatencys
        self.networkLatencys = []
        return response

    
    def reInitRequest(self,BlockOffset,L3Size,L4Size,targetTol):
        # # 送信キューのクリア
        # self.sendQ.clear()

        # 諸々変更する必要があります。サーバサイドと同じで。
        header = {
            'type':'init',
            'offset':str(BlockOffset),
            'L3' : str(L3Size),
            'L4' : str(L4Size),
            'targetTol' : str(targetTol),
            'Policy': 'LRU',
            'FileName':'test'
        }

        response = requests.get(self.URL,headers=header)
        return response.status_code
    
    def firstContact(self,BlockOffset,L3Size,L4Size,targetTol):
        # # 送信キューのクリア
        # self.sendQ.clear()

        # 諸々変更する必要があります。サーバサイドと同じで。
        header = {
            'type':'init',
            'offset':str(BlockOffset),
            'L3Size' : str(L3Size),
            'L4Size' : str(L4Size),
            'targetTol' : str(targetTol),
            'Policy': 'LRU',
            'FileName':'test'
        }
        print("First contact with setting",header)
        response = requests.get(self.URL,headers=header)
        return response.status_code
    



### 使わないこ

    # # 末尾に追加
    # def send_req(self,blockId):
    #     self.sendQ.append(blockId)

    
    # def IsSendQEmpty(self):
    #     if(len(self.sendQ) == 0):
    #         return True
    #     else:
    #         return False

    # def send_req_original_urgent(self,BlockId):
        
    #     header = {
    #         'type':'noCompress',
    #         'tol':str(BlockId[0]),
    #         'timestep': str(BlockId[1]),
    #         'x': str(BlockId[2]),
    #         'y': str(BlockId[3]),
    #         'z': str(BlockId[4])
    #     }
    #     response = requests.get(self.URL, headers=header)
    #     response_content = response.content
    #     numpy_array = np.frombuffer(response_content, dtype=np.float32)
    #     return numpy_array

    # 別スレッドで実行される送信ループ
    # async def sendLoop(self):
    #     while True:
    #         if self.IsSendQEmpty():
    #             await asyncio.sleep(0.1)
    #         else:
    #             BlockId = self.sendQ.popleft()
                
    #             try:

    #                 header = {
    #                     'type':'BlockReq',
    #                     'tol':str(BlockId[0]),
    #                     'timestep':str(BlockId[1]),
    #                     'x': str(BlockId[2]),
    #                     'y': str(BlockId[3]),
    #                     'z': str(BlockId[4])
    #                 }

    #                 response = requests.get(self.URL,headers=header)
    #                 self.L2Cache.put(BlockId,response.content)
    #             except Exception as e:
    #                 print("送信スレッドでexeptionが発生!")
    #                 print(e)

    # def net_thread_func(self):
    #     loop = asyncio.new_event_loop()
    #     asyncio.set_event_loop(loop)
    #     loop.run_until_complete(self.sendLoop())   

    # TODO gridFTPの追加?
    # TODO 時間があったら、いい感じの送信プロトコルを追加。なんかいいやつあるかなー。
    # TODO CPPで独自プロトコルを実装してやるのが一番いいと感じている。まじで。