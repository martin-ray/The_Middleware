from ClientAPI import ClientAPI
from agent.request_maker import requestMaker
import time
import requests
import copy
import numpy as np
import _mgard as mgard
import csv




if __name__ == "__main__":


    tols = [0.3, 0.1 , 0.01, 0.001, 0] # 0 for no compress
    L1Sizes = [512, 1024, 2048, 4096, 4096*2 ,4096*4]
    L2Sizes = [512, 1024, 2048, 4096]
    L3Sizes = [512, 1024, 2048, 4096]
    L4Sizes = [512, 1024, 2048, 4096, 4096*2 ,4096*4, 4096*8]
    blockSizes = [64, 128, 256, 512]
    num_requests = [100,200,400,800,1600,3200]
    request_patterns = np.random.randint(0,100,10) # 何パーセントランダムか？0の時は、完全に連続。100の時は完全にランダム

    header = ['tol','L1Size', 'L2Size', 'L3Size', 'L4Size', 'blockSize',
               'num_requests', 'request_pattern', 'tatime', 'numL1Hits', 
               'numL1Hits', 'numL2Hits', 'numL3Hits', 'numL4Hits'] # num_requests = numL1Hits + numL2Hits + numL3Hits + numL4Hits
    
    # 順番は最適化してほしい
    for tol in tols:
        for L1Size in L1Sizes:
            for L2Size in L2Sizes:
                for L3Size in L3Sizes:
                    for L4Size in L4Sizes:
                        for blockSize in blockSizes:
                            for num_request in num_requests:
                                for request_pattern in request_patterns:
                                    pass


    print("client!")
    blockSize = 256
    maker = requestMaker(blockSize,maxTimestep=9)
    print("making request")
    reqs = maker.continuousRequester(500)
    req2 = copy.deepcopy(reqs)
    req3 = copy.deepcopy(reqs)
    req4 = copy.deepcopy(reqs)
    req5 = copy.deepcopy(reqs)
    req6 = copy.deepcopy(reqs)
    req7 = copy.deepcopy(reqs)

    cli = ClientAPI(L1Size=4096*2,L2Size=4096*4,L3Size=4096,L4Size=4096*5,blockSize=blockSize)
    
    print("start getting !")
    start_time = time.time()
    while len(reqs) > 0:
        req = reqs.pop(0)
        cli.getBlocks(tol=0.1,timestep=req[1],x=req[2],y=req[3],z=req[4],xEnd=req[2] + blockSize -1 ,
                      yEnd=req[3] + blockSize - 1, zEnd=req[4] + blockSize -1)
        print("the rest of request:{}".format(len(reqs)))
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(elapsed_time)

    cli.StopPrefetching()

    # 実験2
    reqs = reqs
        # 諸々変更する必要があります。サーバサイドと同じで。
    header = {
        'type':'init',
        'offset':str(blockSize),
        'L3Size' : str(4096),
        'L4Size' : str(4096*4),
        'Policy': 'LRU',
        'FileName':'test'
    }
    print("sending",header)

    url = "http://172.20.2.253:8080"
    response = requests.get(url,headers=header)
    req_start_time = time.time()
    while len(req2) > 0:
        req = req2.pop(0)
        
        # Define parameters for the request
        tol = req[0]
        timestep = req[1]
        x = req[2]
        y = req[3]
        z = req[4]

        header = {
            'type':'BlockReq',
            'tol':str(req[0]),
            'timestep': str(req[1]),
            'x': str(req[2]),
            'y': str(req[3]),
            'z': str(req[4])
        }
        
        # Send the HTTP GET request
        start_time = time.time()
        response = requests.get(url, headers=header)
        response_content = response.content
        response_content_size = len(response_content)
        numpy_array = np.frombuffer(response_content, dtype=np.uint8)

        decompressed = mgard.decompress(numpy_array).astype(np.float32)
        end_time = time.time()
        elapsed_time = end_time - start_time

    req_end_time = time.time()
    total_time_to_finish = req_end_time - req_start_time
    print("L4+L3")
    print(total_time_to_finish)

        # 諸々変更する必要があります。サーバサイドと同じで。
    header = {
        'type':'init',
        'offset':str(blockSize),
        'L3Size' : str(0),
        'L4Size' : str(400),
        'Policy': 'LRU',
        'FileName':'test'
    }

    print("sending",header)

    response = requests.get(url,headers=header)
    req_start_time = time.time()
    while len(req3) > 0:
        req = req3.pop(0)
        
        # Define parameters for the request
        tol = req[0]
        timestep = req[1]
        x = req[2]
        y = req[3]
        z = req[4]

        header = {
            'type':'BlockReq',
            'tol':str(req[0]),
            'timestep': str(req[1]),
            'x': str(req[2]),
            'y': str(req[3]),
            'z': str(req[4])
        }
        
        # Send the HTTP GET request
        start_time = time.time()
        response = requests.get(url, headers=header)
        response_content = response.content
        response_content_size = len(response_content)
        numpy_array = np.frombuffer(response_content, dtype=np.uint8)

        decompressed = mgard.decompress(numpy_array).astype(np.float32)
        end_time = time.time()
        elapsed_time = end_time - start_time

        # print("{}(compressed) -> {}(decompressed)".format(response_content_size,decompressed.nbytes))

        # print("time to get the block:{} s".format(elapsed_time))


    req_end_time = time.time()
    total_time_to_finish = req_end_time - req_start_time
    print("L4 only")
    print(total_time_to_finish)



        # 諸々変更する必要があります。サーバサイドと同じで。
    header = {
        'type':'init',
        'offset':str(blockSize),
        'L3Size' : str(0),
        'L4Size' : str(0),
        'Policy': 'LRU',
        'FileName':'test'
    }
    print("sending",header)

    response = requests.get(url,headers=header)
    req_start_time = time.time()
    while len(req4) > 0:
        req = req4.pop(0)
        
        # Define parameters for the request
        tol = req[0]
        timestep = req[1]
        x = req[2]
        y = req[3]
        z = req[4]

        header = {
            'type':'BlockReq',
            'tol':str(req[0]),
            'timestep': str(req[1]),
            'x': str(req[2]),
            'y': str(req[3]),
            'z': str(req[4])
        }
        
        # Send the HTTP GET request
        start_time = time.time()
        response = requests.get(url, headers=header)
        response_content = response.content
        response_content_size = len(response_content)
        numpy_array = np.frombuffer(response_content, dtype=np.uint8)

        decompressed = mgard.decompress(numpy_array).astype(np.float32)
        end_time = time.time()
        elapsed_time = end_time - start_time

        # print("{}(compressed) -> {}(decompressed)".format(response_content_size,decompressed.nbytes))

        # print("time to get the block:{} s".format(elapsed_time))
        # # convert to 2d
        # data = decompressed[0,:,:]

        # Process the response if needed
        # if response.status_code == 200:
        #     print("Request successful")
        #     # print("Response body:\n",numpy_array)
        # else:
        #     print("Request failed")

    req_end_time = time.time()
    total_time_to_finish = req_end_time - req_start_time
    print("no cache")
    print(total_time_to_finish)


    header = {
            'type':'init',
            'offset':str(blockSize),
            'L3Size' : str(400),
            'L4Size' : str(0),
            'Policy': 'LRU',
            'FileName':'test'
        }
    print("sending",header)

    response = requests.get(url,headers=header)
    req_start_time = time.time()
    while len(req5) > 0:
        req = req5.pop(0)
        
        # Define parameters for the request
        tol = req[0]
        timestep = req[1]
        x = req[2]
        y = req[3]
        z = req[4]

        header = {
            'type':'BlockReq',
            'tol':str(req[0]),
            'timestep': str(req[1]),
            'x': str(req[2]),
            'y': str(req[3]),
            'z': str(req[4])
        }
        
        # Send the HTTP GET request
        start_time = time.time()
        response = requests.get(url, headers=header)
        response_content = response.content
        response_content_size = len(response_content)
        numpy_array = np.frombuffer(response_content, dtype=np.uint8)

        decompressed = mgard.decompress(numpy_array).astype(np.float32)
        end_time = time.time()
        elapsed_time = end_time - start_time


    req_end_time = time.time()
    total_time_to_finish = req_end_time - req_start_time
    print("L3 only")
    print(total_time_to_finish)


# # no compress test

    header = {
            'type':'init',
            'offset':str(blockSize),
            'L3Size' : str(0),
            'L4Size' : str(4096*10),
            'Policy': 'LRU',
            'FileName':'test'
        }
    
    print("sending",header)

    response = requests.get(url,headers=header)
    req_start_time = time.time()
    while len(req6) > 0:
        req = req6.pop(0)
        # Define parameters for the request
        tol = req[0]
        timestep = req[1]
        x = req[2]
        y = req[3]
        z = req[4]

        header = {
            'type':'noCompress',
            'tol':str(0.1),
            'timestep': str(req[1]),
            'x': str(req[2]),
            'y': str(req[3]),
            'z': str(req[4])
        }
        
        # Send the HTTP GET request
        response = requests.get(url, headers=header)
        response_content = response.content
        response_content_size = len(response_content)
        numpy_array = np.frombuffer(response_content, dtype=np.float32)

    req_end_time = time.time()
    total_time_to_finish = req_end_time - req_start_time
    print("No compress + L4")
    print(total_time_to_finish)


    header = {
            'type':'init',
            'offset':str(blockSize),
            'L3Size' : str(0),
            'L4Size' : str(0),
            'Policy': 'LRU',
            'FileName':'test'
        }
    
    print("sending",header)

    response = requests.get(url,headers=header)
    req_start_time = time.time()
    while len(req7) > 0:
        req = req7.pop(0)
        # Define parameters for the request
        tol = req[0]
        timestep = req[1]
        x = req[2]
        y = req[3]
        z = req[4]

        header = {
            'type':'noCompress',
            'tol':str(0.1),
            'timestep': str(req[1]),
            'x': str(req[2]),
            'y': str(req[3]),
            'z': str(req[4])
        }
        
        # Send the HTTP GET request
        response = requests.get(url, headers=header)
        response_content = response.content
        response_content_size = len(response_content)
        numpy_array = np.frombuffer(response_content, dtype=np.float32)

    req_end_time = time.time()
    total_time_to_finish = req_end_time - req_start_time
    print("No compress + No cache")
    print(total_time_to_finish)