import numpy as np
import random

class requestMaker:
    def __init__(self,blockSize,maxTimestep) -> None:
        self.blockSize = blockSize
        self.maxTimestep = maxTimestep
        self.maxX = 1023
        self.maxY = 1023
        self.maxZ = 1023
        self.targetTol = 0.1
        self.moveDirection = ['timestep','x','y','z']

    def random_xyz(self):
        return random.randint(0, 1023)
    
    def random_timestep(self):
        return random.randint(0,9)
    
    def random_choice(self):
        return random.choice([1, -1])
    
    def random_direction(self):

        return self.moveDirection[random.randint(0,3)]
    
    def randomRequester(self,length):
        requests = []
        for req in range(length):
            nextReq = (self.targetTol,
                       self.random_timestep(),
                       self.random_xyz(),
                       self.random_xyz(),
                       self.random_xyz())
            requests.append(nextReq)     
        return requests

    def continuousRequester(self,length):
        requests = []
        firstRequest = (self.targetTol,0,0,0,0)
        requests.append(firstRequest)
        previousRequest = firstRequest
        req_n = 0
        while req_n < length:
            direction = self.random_direction()
            nexRequest = None
            if direction == 'timestep':
                nexRequest = (previousRequest[0],
                              previousRequest[1] + self.random_choice(),
                              previousRequest[2],
                              previousRequest[3],
                              previousRequest[4])
            elif direction == 'x':
                nexRequest = (previousRequest[0],
                              previousRequest[1],
                              previousRequest[2] + self.random_choice()*self.blockSize,
                              previousRequest[3],
                              previousRequest[4])
            elif direction == 'y':
                nexRequest = (previousRequest[0],
                              previousRequest[1],
                              previousRequest[2],
                              previousRequest[3] + self.random_choice()*self.blockSize,
                              previousRequest[4])
            elif direction == 'z':
                nexRequest = (previousRequest[0],
                              previousRequest[1],
                              previousRequest[2],
                              previousRequest[3],
                              previousRequest[4] + self.random_choice()*self.blockSize)
                
            # 範囲を超えていたら整形
            if nexRequest[1] < 0 or nexRequest[1] > self.maxTimestep:
                pass
            elif nexRequest[2] < 0 or nexRequest[2] > self.maxX - self.blockSize:
                pass
            elif nexRequest[3] < 0 or nexRequest[3] > self.maxY - self.blockSize:
                pass
            elif nexRequest[4] < 0 or nexRequest[4] > self.maxZ - self.blockSize:
                pass
            else :
                requests.append(nexRequest) 
                req_n += 1  
                previousRequest = nexRequest
        return requests
    
    def random_float(self):
        return random.uniform(0, 1)
    
    def randAndcontMixRequester(self,length,randomToContRatio=0.5):
        
        requests = []
        previousReq = None
        nextReq = None
        firstRequest = (self.targetTol,0,0,0,0)
        requests.append(firstRequest)
        previousRequest = firstRequest
        req_n = 0
        while req_n < length:
            num = self.random_float()
            if num > randomToContRatio:
                # continuous
                direction = self.random_direction()
                nexRequest = None
                if direction == 'timestep':
                    nexRequest = (previousRequest[0],
                                previousRequest[1] + self.random_choice(),
                                previousRequest[2],
                                previousRequest[3],
                                previousRequest[4])
                elif direction == 'x':
                    nexRequest = (previousRequest[0],
                                previousRequest[1],
                                previousRequest[2] + self.random_choice()*self.blockSize,
                                previousRequest[3],
                                previousRequest[4])
                elif direction == 'y':
                    nexRequest = (previousRequest[0],
                                previousRequest[1],
                                previousRequest[2],
                                previousRequest[3] + self.random_choice()*self.blockSize,
                                previousRequest[4])
                elif direction == 'z':
                    nexRequest = (previousRequest[0],
                                previousRequest[1],
                                previousRequest[2],
                                previousRequest[3],
                                previousRequest[4] + self.random_choice()*self.blockSize)
                
                # 整形
                if nexRequest[1] < 0 or nexRequest[1] > self.maxTimestep - self.blockSize:
                    pass
                elif nexRequest[2] < 0 or nexRequest[2] > self.maxX - self.blockSize:
                    pass
                elif nexRequest[3] < 0 or nexRequest[3] > self.maxY - self.blockSize:
                    pass
                elif nexRequest[4] < 0 or nexRequest[4] > self.maxZ - self.blockSize:
                    pass
                else :
                    requests.append(nexRequest) 
                    req_n += 1 
                    previousReq = nexRequest

            else:
                nextReq = (self.targetTol,
                       self.random_timestep(),
                       self.random_xyz(),
                       self.random_xyz(),
                       self.random_xyz())
                requests.append(nextReq) 
                previousRequest = nextReq
        return requests

if __name__ == "__main__":
    maker = requestMaker(256,9)
    requests = maker.continuousRequester(100)
    for req in requests:
        print(req)
