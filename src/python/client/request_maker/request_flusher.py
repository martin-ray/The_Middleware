from request_maker import requestMaker
from request_analizer import request_analiser
import pickle


blockSize = 256
maxtimestep = 63
num_request = 256
randomRatio = 0


for _ in range(256*10):
        
    reqMaker = requestMaker(blockSize,maxtimestep)
    reqs = reqMaker.randAndcontMixRequester(num_request,randomRatio)

    numReqs = len(reqs)
    access_report = request_analiser(reqs)
    recycleRatio = round(access_report["recycle_ratio"]*100,2)
    maxdistance = access_report["maxDistance"]
    accessDensity = round(access_report["access_density"]*100,2)

    # save the access pattern to file
    filename = f'./request_files/numReqs={numReqs}_recycleRatio={recycleRatio}_accessDensity={accessDensity}.pkl'

    # Save the data to a file
    with open(filename, 'wb') as file:
        pickle.dump(reqs, file)