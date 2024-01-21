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
        self.rtt = [] # round trip time

    
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
    def send_req_pref(self,BlockId):

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
    def send_req_usr(self,BlockId):

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
            rtt = ( end_time - start_time ) 
            self.rtt.append(rtt/1000)
            print(f"NetIF : Network Transfer Time: {transfer_time} ms")
            print(f"NetIF : RRT : {rtt}")
        else:
            print("NetIF : Failed to get data network data")
        
        return response.content
    
    def requestStats(self):

        header = {
            'type':'getStats'
        }

        response = requests.get(self.URL, headers=header).json()
        response["networkLatencys"] = self.networkLatencys
        response["rtt"] = self.rtt
        self.networkLatencys = []
        self.rtt = []
        return response
    
    def reInitRequest(self,BlockOffset,L3Size,L4Size,targetTol):

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

        header = {
            'type':'init',
            'offset':str(BlockOffset),
            'L3Size' : str(L3Size),
            'L4Size' : str(L4Size),
            'targetTol' : str(targetTol),
            'Policy': 'LRU',
            'FileName':'test'
        }

        print("NetIF : First contact with server. Sending Server settings")
        response = requests.get(self.URL,headers=header)
        return response.status_code