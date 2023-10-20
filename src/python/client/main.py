from ClientAPI import ClientAPI
from agent.request_maker import requestMaker
import time
import requests
import copy
import numpy as np
import _mgard as mgard

if __name__ == "__main__":
    print("client!")
    blockSize = 256
    maker = requestMaker(blockSize,maxTimestep=9)
    print("making request")
    reqs = maker.continuousRequester(300)
    req2 = copy.deepcopy(reqs)
    req3 = copy.deepcopy(reqs)
    req4 = copy.deepcopy(reqs)

    cli = ClientAPI(L1Size=100,L2Size=200,L3Size=300,L4Size=400,blockSize=blockSize)
    
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
        'offset':str(256),
        'L3Size' : str(300),
        'L4Size' : str(400),
        'Policy': 'LRU',
        'FileName':'test'
    }
    print("sending",header)

    url = "http://localhost:8080"
    response = requests.get("http://localhost:8080",headers=header)
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
    print(total_time_to_finish)

        # 諸々変更する必要があります。サーバサイドと同じで。
    header = {
        'type':'init',
        'offset':str(256),
        'L3Size' : str(0),
        'L4Size' : str(400),
        'Policy': 'LRU',
        'FileName':'test'
    }

    print("sending",header)

    url = "http://localhost:8080"
    response = requests.get("http://localhost:8080",headers=header)
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
    print(total_time_to_finish)



        # 諸々変更する必要があります。サーバサイドと同じで。
    header = {
        'type':'init',
        'offset':str(256),
        'L3Size' : str(0),
        'L4Size' : str(0),
        'Policy': 'LRU',
        'FileName':'test'
    }
    print("sending",header)

    url = "http://localhost:8080"
    response = requests.get("http://localhost:8080",headers=header)
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
    print(total_time_to_finish)
