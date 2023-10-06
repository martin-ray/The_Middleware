import h5py 
import numpy as np
import _mgard as mgard


class Slicer:
    # default 引数
    def __init__(self,blockOffset,filename="/scratch/aoyagir/step1_500_test.h5") -> None:
        self.filename = filename
        self.blockOffset = blockOffset
        self.file = h5py.File(filename, 'r')
        self.dataset = self.file['data']
        print(self.dataset.shape)

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
        tol = blockId[0]
        t = blockId[1]
        x = blockId[2]
        y = blockId[3]
        z = blockId[4]
        return self.slice_single_step(t,x,x+self.blockOffset,y,y+self.blockOffset,z,z+self.blockOffset)


if __name__ == "__main__":
    slicer = Slicer()
    original = slicer.slice_single_step(1, 0, 100, 0, 100, 0, 100)
    print(original.shape)
    print(type(original))


    tol = 0.1

    print("original=",original.nbytes,"bytes")
    print("original dtype",original.dtype)

    compressed = mgard.compress(original, tol, 0)
    print("compressed=",compressed.nbytes,"bytes")
    print("compressed type",type(compressed))
    print("compressed dtype",compressed.dtype)
    decompressed = mgard.decompress(compressed)
    print("compression ratio:",original.nbytes/compressed.nbytes)
    e = original - decompressed
    print("max-e:",e.max())
    print("decompressed:",decompressed.nbytes,"bytes")
    print("decompressed dtype",decompressed.dtype)
    print("convert to float32")
    decompressed = decompressed.astype(np.float32)
    print("converted decompressed dtype",decompressed.dtype)
    print("size",decompressed.nbytes)
