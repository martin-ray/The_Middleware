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
import subprocess 
import pickle

interface = "eno1"
initial_latency = "0ms"
serverURL = "http://172.20.2.254:8080" # muffin2

def getAvrExcludingZero(array):
    try:
        non_zero_elements = [x for x in array if x != 0]
        average = sum(non_zero_elements) / len(non_zero_elements)
        standard_deviation = np.std(non_zero_elements)
        return (average,standard_deviation)
    except Exception as e:
        return (-1,-1)
        


# simTim : 追加してくれ
def OneExp(tol,L1Size,L2Size,L3Size,L4Size,blockSize,request_sequence,analisisTime=0,networkLatency=0,num_gpus=1):
    reqs = request_sequence
    reqsTiledb = copy.deepcopy(reqs)
    print(f"\n\n###### Starting the server with setting #####\n:L1Size={L1Size},L2Size={L2Size},L3Size={L3Size},L4Size={L4Size}\n")
    # print(reqs)
    numReqs = len(reqs)
    cli = ClientAPI(L1Size=L1Size,L2Size=L2Size,L3Size=L3Size,L4Size=L4Size,
                    blockSize=blockSize,serverURL=serverURL)
    
    print("creating tiledb client")
    tiledbCli = TiledbConnector(L1Size+L2Size)
    
    # box of every latency
    latencies = []
    PropBytes = 0

    while len(reqs) > 0:
        req = reqs.pop(0)
        
        try : 
            one_req_start = time.time()
            cli.getBlocks(tol=0.1,timestep=req[1],x=req[2],y=req[3],z=req[4],xEnd=req[2] + blockSize ,
                        yEnd=req[3] + blockSize, zEnd=req[4] + blockSize)
            print("the rest of request:{}".format(len(reqs)))
            one_req_end = time.time()
            latencies.append(one_req_end - one_req_start)
            time.sleep(analisisTime)
        except Exception as e:
            print(e)
        
    q1 = np.percentile(latencies, 25)
    median = np.percentile(latencies, 50)
    q3 = np.percentile(latencies, 75)
    iqr = q3 - q1
    # lower_boundが何かわからないんだけれども、maxとminではないってことがわかった。
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    std_dev = np.std(latencies)
    avg_latency = np.average(latencies)
    stats = cli.GetStats()
    
    stats["AllMiss"] = numReqs - stats["nL1Hit"] - stats["nL2Hit"] - stats["nL3Hit"] - stats["nL4Hit"]
    print(f"num_reqs={numReqs},nL1={stats['nL1Hit']}")

    stats["PropAverageLatency"] = avg_latency
    stats["analisisTime"] = analisisTime
    stats["q1"] = q1
    stats["q3"] = q3
    stats["median"] = median
    stats["iqr"] = iqr
    stats["lower_bound"] = lower_bound
    stats["upper_bound"] = upper_bound
    stats["std_dev"] = std_dev
    # stop 
    cli.StopPrefetching()

    stats["storageAvg"] = getAvrExcludingZero(stats["StorageReadTime"])[0]
    stats["compAvg"] = getAvrExcludingZero(stats["CompTime"])[0]
    stats["networkAvg"] = getAvrExcludingZero(stats["networkLatencys"])[0]
    stats["decompAvg"] = getAvrExcludingZero(stats["DecompElapsed"])[0]
    stats["systemOverhead"] = None
    stats["systemOverheadAvg"] = -1

    try:
        # 「リクエストを出してから帰ってくるまでの時間」から、各所要時間を引いたもの
        stats["systemOverhead"] = np.array(latencies) - np.array(stats["StorageReadTime"]) \
        - np.array(stats["CompTime"]) - np.array(stats["DecompElapsed"]) -np.array(stats["networkLatencys"])
        stats["systemOverheadAvg"] = getAvrExcludingZero(stats["systemOverhead"])[0] # 0 for avg

    except Exception as e:
        print(e)
        stats["systemOverheadAvg"] = -1 # stats["PropAverageLatency"] - (stats["storageAvg"] +  stats["compAvg"] + stats["networkAvg"] + stats["decompAvg"])

    stats["numL3PrefFromStorage"] = stats["NumL3Prefetch"] - stats["NumL3PrefetchL4Hit"]

    # TileDB experiment from here
    start_time = time.time()
    tiledbBytes = 0
    print(f"l1={L1Size},l2={L2Size},l3={L3Size},l4={L4Size}")

    # L3 L4の変化はTileDBには関係ない。つまり、
    if(L3Size + L4Size != 0 or analisisTime != 0) :
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
    cli.StopPrefetching() # いらなくね？

    return stats



if __name__ == "__main__":

    print("start program")
    # tols = [0.3, 0.1 , 0.01, 0.001, 0] # 0 for no compress
    tols = [0.1,0.01,0.001,0.0001]

    # L1Sizes = [0,512, 1024, 2048, 4096, 4096*2 ,4096*4]
    L1Sizes = [0,512,512*2,512*4,512*8]

    # L2Sizes = [0,512, 1024, 2048, 4096]
    L2Sizes = [0,512,1024]
    # L2Sizes = [0,512]

    #L3Sizes = [0,512, 1024, 2048, 4096]
    L3Sizes = [0,512,1024]
    # L3Sizes = [0,512]

    # L4Sizes = [0,512, 1024, 2048, 4096, 4096*2 ,4096*4]
    L4Sizes = [0,2048,2048*2,2048*4]
    # L4Sizes = [2048]
    # L4Sizes = [0,2048,2048*2,]

    # blockSizes = [64, 128, 256, 512]
    
    # 大事なのは、ブロックはやり取りをする基本単位である、というだけで、リクエストの大きさは変えないってことね。大事。
    blockSizes = [256]
    
    num_requests = [64, 128] # これを、外部ファイルからの読み出しにする。
    # 外部ファイルとして、お願いします。
    
    # randomRatios = np.arange(0,100,25) # 何パーセントランダムか？0の時は、完全に連続。100の時は完全にランダム
    randomRatios = [0]

    anal_time = [0.1, 0.5, 1.0]
    # anal_time = [0]

    header = ['tol','L1Size', 'L2Size', 'L3Size', 'L4Size', 'blkSize',
               'nReqs', 'reqPatrn', 'nL1Hits', 
               'nL2Hits', 'nL3Hits', 'nL4Hits','nAllMis',
               'AvrLat','TDbArvLat',
               'networkAvg','storageAvg','compAvg',
               'decompAvg','sysOvrHdAvg','nL3PrefTimes','NL3PreL4HitTimes',
               'nL3PrefFromStrg',
               'nL4Pref','anlTime',"netLat",
               'q1','q3','median','iqr','lower_bound','upper_bound',"std_dev",
               "recycleRatio",
               "maxDist",
                "num_gpus"] 
    
    # Create the file name based on the timestamp
    current_datetime =  datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')  # Adjust the format as needed

    # Construct the file name
    csv_file_name = f'sim_{current_datetime}.csv'


    with open(csv_file_name, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
    
    
    # 順番は最適化してほしい
    print("here in front of loop")
    # request sequenceの設定
    maxtimestep=63
    
    for tol in tols:
        for blockSize in blockSizes:
            for num_request in num_requests:
                for randomRatio in randomRatios:


                    recycleRatio = 25.0
                    maxdistance = 5.0
                    filename = f'./request_maker/request_files/64Reqs/numReqs={num_request}_recycleRatio={recycleRatio}_maxdistance={maxdistance}.pkl'
                    loaded_data = None
                    
                    with open(filename, 'rb') as file:
                        loaded_data = pickle.load(file)
                    reqs = loaded_data #reqMaker.randAndcontMixRequester(num_request,randomRatio)
                    print(f"loaded:{filename}")
                    
                    for L1Size in L1Sizes:
                        for L2Size in L2Sizes:
                            for L3Size in L3Sizes:
                                for L4Size in L4Sizes:
                                    for analtime in anal_time:

                                        request_sequence = copy.deepcopy(reqs)
                                        stats = OneExp(tol,L1Size,L2Size,L3Size,L4Size,
                                                    blockSize,request_sequence,analisisTime=analtime)
                                        new_data = None
                                        
                                        round_precision = 4

                                        try:
                                            new_data = [tol,L1Size,L2Size,L3Size,L4Size,blockSize,
                                                        num_request,"sequential",
                                                        stats["nL1Hit"],stats["nL2Hit"],
                                                        stats["nL3Hit"],stats["nL4Hit"],
                                                        stats["AllMiss"],
                                                        round(stats["PropAverageLatency"],round_precision),
                                                        round(stats["TiledbAverageLatency"],round_precision),
                                                        round(stats["networkAvg"],round_precision),
                                                        round(stats["storageAvg"],round_precision),
                                                        round(stats["compAvg"],round_precision),
                                                        round(stats["decompAvg"],round_precision),
                                                        round(stats["systemOverheadAvg"],round_precision),
                                                        round(stats["NumL3Prefetch"],),
                                                        stats["NumL3PrefetchL4Hit"],
                                                        stats["numL3PrefFromStorage"],
                                                        stats["numL4Prefetch"],
                                                        stats["analisisTime"],
                                                        0, # network latency
                                                        round(stats["q1"],round_precision),
                                                        round(stats["q3"],round_precision),
                                                        round(stats["median"],round_precision),
                                                        round(stats["iqr"],round_precision),
                                                        round(stats["lower_bound"],round_precision),
                                                        round(stats["upper_bound"],round_precision),
                                                        round(stats["std_dev"],round_precision),
                                                        recycleRatio,
                                                        maxdistance]
                                            

                                        except Exception as e:
                                            print(e)
                                        with open(csv_file_name, "a", newline="") as f:
                                            writer = csv.writer(f)
                                            writer.writerow(new_data)


