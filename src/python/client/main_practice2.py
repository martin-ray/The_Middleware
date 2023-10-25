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
def OneExp(tol,L1Size,L2Size,L3Size,L4Size,blockSize,numReqs,reqs):


    cli = ClientAPI(L1Size=L1Size,L2Size=L2Size,L3Size=L3Size,L4Size=L4Size,
                    blockSize=blockSize)
    
    if tol == 0:
        start_time = time.time()
        while len(reqs) > 0:
            req = reqs.pop(0)
            cli.getBlocksNoComp(tol=0.1,timestep=req[1],x=req[2],y=req[3],z=req[4],xEnd=req[2] + blockSize -1 ,
                        yEnd=req[3] + blockSize - 1, zEnd=req[4] + blockSize -1)
            print("the rest of request:{}".format(len(reqs)))
        end_time = time.time()        
    else :
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
    print(stats)
    stats["AllMiss"] = numReqs - stats["nL1Hit"] - stats["nL2Hit"] - stats["nL3Hit"] - stats["nL4Hit"]
    stats["tat"] = elapsed_time
    stats["averageLatency"] = elapsed_time/numReqs
    cli.StopPrefetching()
    
    return stats



if __name__ == "__main__":

    print("start program")
    # tols = [0.3, 0.1 , 0.01, 0.001, 0] # 0 for no compress
    tols = [0]
    L1Sizes = [0, 1024, 2048, 4096]
    L2Sizes = [0, 512, 1024]
    L3Sizes = [0, 512, 1024]
    L4Sizes = [0, 1024, 2048, 4096, 4096*2]
    # blockSizes = [64, 128, 256, 512]
    blockSizes = [256]
    num_requests = [100,200,400]
    sim_times = 3
    randomRatios = 0 # # 何パーセントランダムか？0の時は、完全に連続。100の時は完全にランダム

    header = ['tol','L1Size', 'L2Size', 'L3Size', 'L4Size', 'blockSize',
               'num_requests', 'request_pattern', 'tatime', 'numL1Hits', 
               'numL2Hits', 'numL3Hits', 'numL4Hits','AllMiss'] # num_requests = numL1Hits + numL2Hits + numL3Hits + numL4Hits


        # Create the file name based on the timestamp
    current_datetime = 1025# datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')  # Adjust the format as needed

    # Construct the file name
    csv_file_name = f'./eval_data/sim_{current_datetime}.dat'


    with open(csv_file_name, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)

# なんか知らないけど、バグが起こっています。これを直すまでは帰れまてんね。おそらく、あの部分だと思う。
# 複数のリクエストを作ってくれるところあるじゃない。そこだね。完全に。
    for num_request in num_requests:
        for blockSize in blockSizes:
            for _ in range(sim_times):
                reqMaker = requestMaker(blockSize,9)
                print("create request maker")
                reqs = reqMaker.continuousRequester(num_request)
                print("num of reqs = ",len(reqs))
                for tol in [0, 0.1]:
                    for L1Size in L1Sizes:
                        for L2Size in L2Sizes:
                            for L3Size in L3Sizes:
                                for L4Size in L4Sizes:
                                        if tol == 0.1:
                                            request = copy.deepcopy(reqs)
                                            stats = OneExp(tol,L1Size,L2Size,L3Size,L4Size,
                                                            blockSize,num_request,request)
                                            new_data = [tol,L1Size,L2Size,L3Size,L4Size,blockSize,
                                                        num_request,0,stats["tat"],
                                                        stats["nL1Hit"],stats["nL2Hit"],
                                                        stats["nL3Hit"],stats["nL4Hit"],
                                                        stats["AllMiss"]]
                                            with open(csv_file_name, "a", newline="") as f:
                                                writer = csv.writer(f)
                                                writer.writerow(new_data)
                                        elif tol == 0:
                                            if L2Size == 0 and L3Size == 0:
                                                request = copy.deepcopy(reqs)
                                                stats = OneExp(tol,L1Size,L2Size,L3Size,L4Size,
                                                                blockSize,num_request,request)
                                                new_data = [tol,L1Size,L2Size,L3Size,L4Size,blockSize,
                                                            num_request,0,stats["tat"],
                                                            stats["nL1Hit"],stats["nL2Hit"],
                                                            stats["nL3Hit"],stats["nL4Hit"],
                                                            stats["AllMiss"]]
                                                with open(csv_file_name, "a", newline="") as f:
                                                    writer = csv.writer(f)
                                                    writer.writerow(new_data)


    # tol = 0
    # L1Sizes = [1024, 2048, 4096]
    # L2Sizes = [0]
    # L3Sizes = [0]
    # L4Sizes = [0, 1024, 2048, 4096, 4096*2,4096*4]
    # for num_request in num_requests:
    #     for _ in range(sim_times):
    #         for blockSize in blockSizes:
    #             reqMaker = requestMaker(blockSize,9)
    #             print("create request maker")
    #             reqs = reqMaker.continuousRequester(num_request)
    #             print("num of reqs = ",len(reqs))

    #             for L1Size in L1Sizes:
    #                 for L2Size in L2Sizes:
    #                     for L3Size in L3Sizes:
    #                         for L4Size in L4Sizes:

    #                                 request = copy.deepcopy(reqs)
    #                                 stats = OneExp(tol,L1Size,L2Size,L3Size,L4Size,
    #                                                 blockSize,num_request,request)
    #                                 new_data = [tol,L1Size,L2Size,L3Size,L4Size,blockSize,
    #                                             num_request,0,stats["tat"],
    #                                             stats["nL1Hit"],stats["nL2Hit"],
    #                                             stats["nL3Hit"],stats["nL4Hit"],
    #                                             stats["AllMiss"]]
    #                                 with open(csv_file_name, "a", newline="") as f:
    #                                     writer = csv.writer(f)
    #                                     writer.writerow(new_data)


