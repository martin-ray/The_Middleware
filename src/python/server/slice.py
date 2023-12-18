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
    def __init__(self,blockOffset=256,cacheSize=0,filename="/scratch/aoyagir/minio_data/tiledb/array5") -> None:
        # Create a TileDB config
        self.config = tiledb.Config()
        self.filename = filename
        self.blockOffset = blockOffset
        self.timesteps = None
        self.xMax = None
        self.yMax = None
        self.zMax = None
        self.lock = threading.Lock()
        self.printDataInfo()
        self.ctx = tiledb.Ctx(self.config)

    def printDataInfo(self):
        print("##### Row data INFO #####")
        print("timesteps:{}\nx:{}\ny:{}\nz:{}\n"
              .format(self.timesteps,self.xMax,self.yMax,self.zMax))

    def getDim(self):
        with tiledb.open(self.filename, mode="r", ctx=self.ctx) as array:
            # Retrieve and print the array schema
            array_schema = array.schema
            print("Array Schema:")
            print(array_schema)
            # You can also access other information about the array, such as its domain and attributes
            domain = array_schema.domain
            print("Domain:", domain)

    def get(self,timestep,x,xx,y,yy,z,zz):
        with tiledb.DenseArray(self.filename, mode="r", ctx=self.ctx) as array:
            # Read the sliced data from the TileDB array using 'from' and 'to' expressions
            data = array[timestep,x:xx, y:yy, z:zz]
            return data



import concurrent.futures
class TileDBReaderThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.tiledb_reader = TileDBSlicer()

    def run(self):
        a = self.tiledb_reader.get(0, 0, 256, 0, 256, 0, 256)
        for _ in range(100):
            s = time.time()
            a = self.tiledb_reader.get(0, 0, 256, 0, 256, 0, 256)
            e = time.time()
            print(e - s)
        print(a)


# test
class TileDBReader:
    def __init__(self):
        self.tiledb_reader = TileDBSlicer()

    def read_and_measure(self, thread_id):
        a = self.tiledb_reader.get(0, 0, 256, 0, 256, 0, 256)
        i = thread_id
        for _ in range(100):
            s = time.time()
            if thread_id <=3:
                a = self.tiledb_reader.get(0, i*256, i*256 + 256, i*256, i*256 + 256, i*256, i*256 + 256)
            else :
                i -=3
                a = self.tiledb_reader.get(0, i*256, i*256 + 256, i*256, i*256 + 256, i*256, i*256 + 256)
            e = time.time()
            print(f"Thread {thread_id}: {e - s} seconds")

class HDF5Reader:
    def __init__(self):
        self.hdf5_reader = Slicer()

    def read_and_measure(self, thread_id):
        a = self.hdf5_reader.sliceData((0.1, 0, 0, 0, 0))
        for _ in range(100):
            s = time.time()
            a = self.hdf5_reader.sliceData((0.1, 0,0,0,0))
            e = time.time()
            print(f"Thread {thread_id}: {e - s} seconds")


if __name__ == "__main__":
    num_threads = 8  # Adjust the number of threads as needed
    tiledb_readers = [TileDBReader() for _ in range(num_threads)]
    hdf5_readers = [HDF5Reader() for _ in range(num_threads)]

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        for i in range(num_threads):
            executor.submit(tiledb_readers[i].read_and_measure, i)

    print("HDF5 scalability")
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        for i in range(num_threads):
            executor.submit(hdf5_readers[i].read_and_measure, i)

