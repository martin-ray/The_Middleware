import numpy as np

class Recomposer:
    def __init__(self, blockOffset):
        self.blockOffset = blockOffset

    # input is sets of (blockId,blockdata) 
    def recompose(self,blocksData):
        # Determine the dimensions of the synthesized block based on the maximum blockId
        max_x, max_y, max_z = (0, 0, 0)
        for block_id, _ in blocksData:
            x, y, z = block_id
            max_x = max(max_x, x)
            max_y = max(max_y, y)
            max_z = max(max_z, z)
        
        # Initialize the synthesized block with zeros
        synthesized_block = np.zeros(((max_x + 1) * self.blockOffset, (max_y + 1) * self.blockOffset, (max_z + 1) * self.blockOffset))
        
        # Fill in the synthesized block with block data
        for block_id, block_data in blocksData:
            x, y, z = block_id
            x_offset = x * self.blockOffset
            y_offset = y * self.blockOffset
            z_offset = z * self.blockOffset
            block_shape = block_data.shape
            synthesized_block[x_offset:x_offset+block_shape[0], y_offset:y_offset+block_shape[1], z_offset:z_offset+block_shape[2]] = block_data
        
        return synthesized_block


if __name__ == "__main__":
    recomposer = Recomposer(256)
    