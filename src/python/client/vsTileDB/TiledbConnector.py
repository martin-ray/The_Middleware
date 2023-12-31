import os
import sys
import ctypes
import math
import numpy
import numpy as np
import h5py
import tiledb

# Total number of time steps
# num_time_steps = 257
num_time_steps = 129

class TiledbConnector:
    def __init__(self,cacheSize,arrayBucket=f"s3://array64lz") -> None: # cacheSize in MiB
        self.config = tiledb.Config() 
        self.config["vfs.s3.scheme"] = "http"
        self.config["vfs.s3.region"] = ""
        self.config["vfs.s3.endpoint_override"] = "172.20.2.253:9000"
        self.config["vfs.s3.use_virtual_addressing"] = "false"
        self.config["vfs.s3.aws_access_key_id"] = "189XB7837GTE0Kt1lv6b"
        self.config["vfs.s3.aws_secret_access_key"] = "aQ3nGhtwk8Qod24f201KAMzShU5Y5VUgVOQL0XG5"
        self.config["sm.tile_cache_size"] = cacheSize*1024*1024
        # Create contex
        self.ctx = tiledb.Ctx(self.config)
        self.array_uri = arrayBucket

    def getDim(self):
        with tiledb.open(self.array_uri, mode="r", ctx=self.ctx) as array:
            # Retrieve and print the array schema
            array_schema = array.schema
            print("Array Schema:")
            print(array_schema)
            # You can also access other information about the array, such as its domain and attributes
            domain = array_schema.domain
            print("Domain:", domain)

    def get(self,timestep,x,xx,y,yy,z,zz):
        with tiledb.DenseArray(self.array_uri, mode="r", ctx=self.ctx) as array:
            # Read the sliced data from the TileDB array using 'from' and 'to' expressions
            data = array[timestep,x:xx, y:yy, z:zz]
            return data
        

if __name__ == "__main__":
    print("main!!")
    Cli = TiledbConnector()
    Cli.getDim()
    # d = Cli.get(0,0,256,0,256,0,256)
    # d = Cli.get(0,0,256,0,256,0,256)
    print(d)