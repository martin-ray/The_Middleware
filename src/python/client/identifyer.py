

import numpy as np

class Identifiyer:
    def __init__(self,tolerance=5, timestep=256, x_size=1024, y_size=1024, z_size=1024, block_size=256):
        self.tollerance=tolerance
        self.timestep = timestep
        self.x_size = x_size
        self.y_size = y_size
        self.z_size = z_size
        self.block_size = block_size
        array = np.empty((tolerance, timestep, x_size, y_size, z_size), dtype=int)

    def create_5d_array_id(self,tolerance=5, timestep=10, x_size=100, y_size=100, z_size=100):
        for tol in range(tolerance):
            for t in range(timestep):
                for x in range(x_size):
                    for y in range(y_size):
                        for z in range(z_size):
                            unique_id = (tol * timestep * x_size * y_size * z_size) + (t * x_size * y_size * z_size) + (x * y_size * z_size) + (y * z_size) + z
                            self.array[tol, t, x, y, z] = unique_id
                            

    def request2blockId(self,tolerance, timestep, x, y, z):
        return self.array[tolerance][timestep][x // self.block_size][y // self.block_size][z // self.block_size]
        
    def get_neighboring_ids(id_value, tolerance, timestep, x_size, y_size, z_size):
        neighboring_ids = []
        pass





