import numpy as np

class Recomposer:
    def __init__(self, blockOffset):
        self.blockOffset = blockOffset
        self.xyzSize = 1024

    # input is sets of (blockId,blockdata) 
    def recompose(self,blocksData,xyzRange):
        xStart = xyzRange[0]
        xEnd = xyzRange[1]
        yStart = xyzRange[2]
        yEnd = xyzRange[3]
        zStart = xyzRange[4]
        zEnd = xyzRange[5]

        # create a empty block to fill in プラス1いらなくね？
        synthesized_block = np.zeros((xEnd - xStart + 1), (yEnd - yStart + 1), (zEnd - zStart + 1)) 
        
        # Determine the dimensions of the synthesized block based on the maximum blockId
        min_x, min_y, min_z = (self.xyzSize, self.xyzSize, self.xyzSize)
        for block_id, _ in blocksData:
            x, y, z = block_id
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            min_z = min(min_z, z)

        # Fill in the synthesized block with block data
        for block_id, block_data in blocksData:
            x, y, z = block_id
            xPoint = x - min_x
            yPoint = y - min_y
            zPoint = z - min_z
            block_shape = block_data.shape
            synthesized_block[xPoint:xPoint+block_shape[0],yPoint:yPoint+block_shape[1], zPoint:zPoint+block_shape[2]] = block_data
        return synthesized_block


if __name__ == "__main__":
    recomposer = Recomposer(256)
    