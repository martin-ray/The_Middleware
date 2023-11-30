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
    
    maxtimestep=63
    reqMaker = requestMaker(blockSize,maxtimestep)
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
            cli.getBlocks(tol=0.1,timestep=req[1],x=req[2],y=req[3],z=req[4],xEnd=req[2] + blockSize ,
                        yEnd=req[3] + blockSize, zEnd=req[4] + blockSize)
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
    print(f"l1={L1Size},l2={L2Size},l3={L3Size},l4={L4Size}")
    # L3 L4の変化はTileDBには関係ない。つまり、
    if(L3Size + L4Size != 0) :
        # 一回だけでいいのです！    
        print("skipping tiledb")
        stats["TiledbAverageLatency"] = 0
        return stats
    
    while len(reqsTiledb) > 0:
        req = reqsTiledb.pop(0)
        try : 
            data = tiledbCli.get(timestep=req[1],
                          x=req[2],xx=req[2] + blockSize, #- 1,
                          y=req[3],yy=req[3] + blockSize,# - 1,
                          z=req[4],zz=req[4] + blockSize,# - 1
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
    # L1Sizes = [0,512, 1024, 2048, 4096, 4096*2 ,4096*4]
    L1Sizes = [0,512,512*2,512*4,512*8]
    # L2Sizes = [0,512, 1024, 2048, 4096]
    L2Sizes = [0,512]

    #L3Sizes = [0,512, 1024, 2048, 4096]
    L3Sizes = [0,512]
    # L4Sizes = [0,512, 1024, 2048, 4096, 4096*2 ,4096*4]
    L4Sizes = [0,2048,2048*2,2048*4,2048*8]
    # blockSizes = [64, 128, 256, 512]
    blockSizes = [256]
    num_requests = [100,200,400]
    randomRatios = np.arange(0,100,25) # 何パーセントランダムか？0の時は、完全に連続。100の時は完全にランダム
    anal_time = [0]

    #randomRatios = np.linspace(0, 100, 25) / 100.0
    header = ['tol','L1Size', 'L2Size', 'L3Size', 'L4Size', 'blockSize',
               'num_requests', 'request_pattern', 'numL1Hits', 
               'numL2Hits', 'numL3Hits', 'numL4Hits','AllMiss','PropAvrLatency','TileDbArvLatency','analisisTime'] # num_requests = numL1Hits + numL2Hits + numL3Hits + numL4Hits


        # Create the file name based on the timestamp
    current_datetime = 1121# datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')  # Adjust the format as needed

    # Construct the file name
    csv_file_name = f'sim_{current_datetime}.dat'


    with open(csv_file_name, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
    
    
    # 順番は最適化してほしい
    print("here in front of loop")
    print(randomRatios)
    for tol in tols:
        for randomRatio in randomRatios:
            for num_request in num_requests:
                for L1Size in L1Sizes:
                    for L2Size in L2Sizes:
                        for L3Size in L3Sizes:
                            for L4Size in L4Sizes:
                                for blockSize in blockSizes:
                                    for analtime in anal_time:
                                        stats = OneExp(tol,L1Size,L2Size,L3Size,L4Size,
                                                    blockSize,num_request,randomRatio)
                                        new_data = None
                                        try:
                                            new_data = [tol,L1Size,L2Size,L3Size,L4Size,blockSize,
                                                        num_request,randomRatio,
                                                        stats["nL1Hit"],stats["nL2Hit"],
                                                        stats["nL3Hit"],stats["nL4Hit"],
                                                        stats["AllMiss"],
                                                        stats["PropAverageLatency"],
                                                        stats["TiledbAverageLatency"]]
                                        except Exception as e:
                                            print(e)
                                        with open(csv_file_name, "a", newline="") as f:
                                            writer = csv.writer(f)
                                            writer.writerow(new_data)


