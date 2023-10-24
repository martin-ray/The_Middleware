from ClientAPI import ClientAPI
from agent.request_maker import requestMaker
import time
import requests
import copy
import numpy as np
import _mgard as mgard
import csv
import datetime

# simTim : 追加してくれ
def OneExp(tol,L1Size,L2Size,L3Size,L4Size,blockSize,numReqs,radomRatio):
    reqMaker = requestMaker(blockSize,9)
    print("create request maker")
    reqs = reqMaker.randAndcontMixRequester(numReqs,radomRatio)

    cli = ClientAPI(L1Size=L1Size,L2Size=L2Size,L3Size=L3Size,L4Size=L4Size,
                    blockSize=blockSize)
    
    start_time = time.time()
    while len(reqs) > 0:
        req = reqs.pop(0)
        cli.getBlocks(tol=0.1,timestep=req[1],x=req[2],y=req[3],z=req[4],xEnd=req[2] + blockSize -1 ,
                      yEnd=req[3] + blockSize - 1, zEnd=req[4] + blockSize -1)
        print("the rest of request:{}".format(len(reqs)))
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(elapsed_time)
    stats = cli.GetStats()

    stats["AllMiss"] = numReqs - stats["nL1Hit"] - stats["nL2Hit"] - stats["nL3Hit"] - stats["nL4Hit"]
    stats["tat"] = elapsed_time
    stats["averageLatency"] = elapsed_time/numReqs
    cli.StopPrefetching()
    return stats



if __name__ == "__main__":

    print("start program")
    # tols = [0.3, 0.1 , 0.01, 0.001, 0] # 0 for no compress
    tols = [0.1]
    L1Sizes = [512, 1024, 2048, 4096, 4096*2 ,4096*4]
    L2Sizes = [512, 1024, 2048, 4096]
    L3Sizes = [512, 1024, 2048, 4096]
    L4Sizes = [512, 1024, 2048, 4096, 4096*2 ,4096*4, 4096*8]
    blockSizes = [64, 128, 256, 512]
    num_requests = [100,200,400,800,1600,3200]
    request_patterns = np.random.randint(0,100,10) # 何パーセントランダムか？0の時は、完全に連続。100の時は完全にランダム

    header = ['tol','L1Size', 'L2Size', 'L3Size', 'L4Size', 'blockSize',
               'num_requests', 'request_pattern', 'tatime', 'numL1Hits', 
               'numL2Hits', 'numL3Hits', 'numL4Hits','AllMiss'] # num_requests = numL1Hits + numL2Hits + numL3Hits + numL4Hits


        # Create the file name based on the timestamp
    current_datetime = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')  # Adjust the format as needed

    # Construct the file name
    csv_file_name = f'sim_{current_datetime}.dat'


    with open(csv_file_name, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)


    # 順番は最適化してほしい
    print("here in front of loop")
    for tol in tols:
        for request_pattern in request_patterns:
            for num_request in num_requests:
                for L1Size in L1Sizes:
                    for L2Size in L2Sizes:
                        for L3Size in L3Sizes:
                            for L4Size in L4Sizes:
                                for blockSize in blockSizes:
                                    stats = OneExp(tol,L1Size,L2Size,L3Size,L4Size,
                                                   blockSize,num_request,request_pattern)
                                    new_data = [tol,L1Size,L2Size,L3Size,L4Size,blockSize,
                                                num_request,request_pattern,stats["tat"],
                                                stats["nL1Hit"],stats["nL2Hit"],stats["nL3Hit"],stats["nL4Hit"]
                                                ,stats["AllMiss"]]
                                    with open(csv_file_name, "a", newline="") as f:
                                        writer = csv.writer(f)
                                        writer.writerow(new_data)


