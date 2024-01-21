import h5py 
import numpy as np
import _mgard as mgard
import tiledb
import threading
import time
import threading


class Slicer:
    # default 引数
    def __init__(self,blockOffset=256,filename="/scratch/aoyagir/step1_256_test_0902.h5") -> None:
        self.filename = filename
        self.blockOffset = blockOffset
        self.file = h5py.File(filename, 'r')
        self.dataset = self.file['data']
        self.timesteps = self.dataset.shape[0]
        self.xMax = self.dataset.shape[1]
        self.yMax = self.dataset.shape[2]
        self.zMax = self.dataset.shape[3]
        self.lock = threading.Lock()
        self.printDataInfo()

    # Access specific elements in the concatenated array
    def access_array_element(self,timestep, x, y, z):
        element = self.dataset[timestep, x, y, z]
        return element

    # Access a subset of the concatenated array
    def slice_multiple_step(self, file, timestep_start, timestep_end, x_start, x_end, y_start, y_end, z_start, z_end):
        subset = self.dataset[timestep_start:timestep_end, x_start:x_end, y_start:y_end, z_start:z_end]
        return subset
    
    def slice_single_step(self, timestep,  x_start, x_end, y_start, y_end, z_start, z_end):
        subset = self.dataset[timestep,  x_start:x_end, y_start:y_end, z_start:z_end]
        retsubset = np.squeeze(subset)
        return retsubset
    
    # blockId = (tol,timestep,x,y,z)
    def sliceData(self,blockId):
        # with self.lock:
        _ = blockId[0]
        t = blockId[1]
        x = blockId[2]
        y = blockId[3]
        z = blockId[4]
        return self.slice_single_step(t,x,x+self.blockOffset,y,y+self.blockOffset,z,z+self.blockOffset)

    def changeBlockSize(self,blockSize):
        print("changin block size from {} to {}".format(self.blockOffset,blockSize))
        self.blockOffset = blockSize
    
    def printBlocksize(self):
        print(self.blockOffset)

    def printDataInfo(self):
        print("##### Row data INFO #####")
        print("timesteps:{}\nx:{}\ny:{}\nz:{}\n"
              .format(self.timesteps,self.xMax,self.yMax,self.zMax))
        
    def getDataDim(self):
        return self.dataset.shape


class TileDBSlicer:
    def __init__(self,blockOffset=256,cacheSize=0,filename="/scratch/aoyagir/tiledb_data/array64") -> None:
        
        # Create a TileDB config
        self.config = tiledb.Config()
        self.config["sm.tile_cache_size"] = cacheSize
        self.ctx = tiledb.Ctx(self.config)
        self.filename = filename
        self.blockOffset = blockOffset
        self.timesteps = None
        self.xMax = 1024
        self.yMax = 1024
        self.zMax = 1024
        self.shape = [self.timesteps,self.xMax,self.yMax,self.zMax]

        # self.getDim()
        # self.printDataInfo()

    def getDim(self):
        with tiledb.open(self.filename, mode="r", ctx=self.ctx) as array:
            # Retrieve and print the array schema
            array_schema = array.schema
            print("Array Schema:")
            print(array_schema)
            # You can also access other information about the array, such as its domain and attributes
            domain = array_schema.domain
            i = 0
            for s in domain:
                print(s)
                print(s.name)
                print(s.domain)
                print(s.domain[1])
                self.shape[i] = s.domain[1] + 1
                i += 1

    def slice_single_step(self,timestep,x,xx,y,yy,z,zz):
        with tiledb.DenseArray(self.filename, mode="r", ctx=self.ctx) as array:
            data = array[timestep,x:xx, y:yy, z:zz]['data']
            return data
    
    # blockId = (tol,timestep,x,y,z)
    def sliceData(self,blockId):
        # with self.lock:
        _ = blockId[0]
        t = blockId[1]
        x = blockId[2]
        y = blockId[3]
        z = blockId[4]
        return self.slice_single_step(t,x,x+self.blockOffset,y,y+self.blockOffset,z,z+self.blockOffset)

    def changeBlockSize(self,blockSize):
        print("changin block size from {} to {}".format(self.blockOffset,blockSize))
        self.blockOffset = blockSize
    
    def printBlocksize(self):
        print(self.blockOffset)

    def printDataInfo(self):
        print("##### Row data INFO #####")
        print("timesteps:{}\nx:{}\ny:{}\nz:{}\n"
              .format(self.timesteps,self.xMax,self.yMax,self.zMax))
        
    def getDataDim(self):
        self.getDim()
        return self.shape