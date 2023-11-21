from ClientAPI import ClientAPI
from vsTileDB.TiledbConnector import TiledbConnector

from request_maker.request_maker import requestMaker
import time
import requests
import copy
import numpy as np
import _mgard as mgard
import csv
import datetime

# simTim : 追加してくれ
def OneExp(tol,L1Size,L2Size,L3Size,L4Size,blockSize,numReqs,radomRatio,analisisTime=0):
    reqMaker = requestMaker(blockSize,9)
    print("create request maker")
    reqs = reqMaker.randAndcontMixRequester(numReqs,radomRatio)
    reqsTiledb = copy.deepcopy(reqs)

    cli = ClientAPI(L1Size=L1Size,L2Size=L2Size,L3Size=L3Size,L4Size=L4Size,
                    blockSize=blockSize)
    
    print("creating tiledb client")
    tiledbCli = TiledbConnector(L1Size+L2Size)
    
    start_time = time.time()
    PropBytes = 0
    while len(reqs) > 0:
        req = reqs.pop(0)
        try : 
            cli.getBlocks(tol=0.1,timestep=req[1],x=req[2],y=req[3],z=req[4],xEnd=req[2] + blockSize -1 ,
                        yEnd=req[3] + blockSize - 1, zEnd=req[4] + blockSize -1)
            print("the rest of request:{}".format(len(reqs)))
            time.sleep(analisisTime)
        except Exception as e:
            print(e)
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(elapsed_time)
    stats = cli.GetStats()

    stats["AllMiss"] = numReqs - stats["nL1Hit"] - stats["nL2Hit"] - stats["nL3Hit"] - stats["nL4Hit"]
    stats["tat"] = elapsed_time
    stats["PropAverageLatency"] = elapsed_time/numReqs
    cli.StopPrefetching()



    start_time = time.time()
    tiledbBytes = 0
    while len(reqsTiledb) > 0:
        req = reqsTiledb.pop(0)
        try : 
            data = tiledbCli.get(timestep=req[1],
                          x=req[2],xx=req[2] + blockSize - 1,
                          y=req[3],yy=req[3] + blockSize - 1,
                          z=req[4],zz=req[4] + blockSize - 1
                        )
            print("the rest of request:{}".format(len(reqsTiledb)))
            time.sleep(analisisTime)
            # print(data)
            tiledbBytes += data['data'].nbytes
            print(tiledbBytes)
            print(data['data'].shape)
        except Exception as e:
            print(e)
    end_time = time.time()
    elapsed_time = end_time - start_time
    print("tiledb_elapsed=",elapsed_time)
    stats["TiledbAverageLatency"] = elapsed_time/numReqs
    cli.StopPrefetching()

    return stats



if __name__ == "__main__":

    print("start program")
    # tols = [0.3, 0.1 , 0.01, 0.001, 0] # 0 for no compress
    tols = [0.1]
    L1Sizes = [0,512, 1024, 2048, 4096, 4096*2 ,4096*4]
    L2Sizes = [0,512, 1024, 2048, 4096]
    L3Sizes = [0,512, 1024, 2048, 4096]
    L4Sizes = [0,512, 1024, 2048, 4096, 4096*2 ,4096*4]
    # blockSizes = [64, 128, 256, 512]
    blockSizes = [256]
    num_requests = [100,200,400]
    randomRatios = np.random.randint(0,100,25) # 何パーセントランダムか？0の時は、完全に連続。100の時は完全にランダム
    #randomRatios = np.linspace(0, 100, 25) / 100.0
    header = ['tol','L1Size', 'L2Size', 'L3Size', 'L4Size', 'blockSize',
               'num_requests', 'request_pattern', 'tatime', 'numL1Hits', 
               'numL2Hits', 'numL3Hits', 'numL4Hits','AllMiss','PropAvrLatency','TileDbArvLatency'] # num_requests = numL1Hits + numL2Hits + numL3Hits + numL4Hits


        # Create the file name based on the timestamp
    current_datetime = 1025# datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')  # Adjust the format as needed

    # Construct the file name
    csv_file_name = f'sim_{current_datetime}.dat'


    with open(csv_file_name, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)

# なんか知らないけど、バグが起こっています。これを直すまでは帰れまてんね。おそらく、あの部分だと思う。
# 複数のリクエストを作ってくれるところあるじゃない。そこだね。完全に。

    # 順番は最適化してほしい
    print("here in front of loop")
    for tol in tols:
        for randomRatio in randomRatios:
            for num_request in num_requests:
                for L1Size in L1Sizes:
                    for L2Size in L2Sizes:
                        for L3Size in L3Sizes:
                            for L4Size in L4Sizes:
                                for blockSize in blockSizes:
                                    stats = OneExp(tol,L1Size,L2Size,L3Size,L4Size,
                                                   blockSize,num_request,randomRatio)
                                    new_data = [tol,L1Size,L2Size,L3Size,L4Size,blockSize,
                                                num_request,randomRatio,stats["tat"],
                                                stats["nL1Hit"],stats["nL2Hit"],
                                                stats["nL3Hit"],stats["nL4Hit"],
                                                stats["AllMiss"],
                                                stats["PropAverageLatency"],
                                                stats["TiledbAverageLatency"]]
                                    with open(csv_file_name, "a", newline="") as f:
                                        writer = csv.writer(f)
                                        writer.writerow(new_data)


