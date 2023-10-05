import _mgard as mgard
import numpy as np

class Decompressor:
    def __init__(self,device = "GPU") -> None:
        # configure device
        self.config = mgard.Config()
        if device == "OMP":
            self.config.dev_type = mgard.DeviceType.OMP
        elif device == "SERIAL":
            self.config.dev_type = mgard.DeviceType.SERIAL

    def decompress_req(self,compressed):
        pass
    

    def decompress_req_urgent(self,compressed):
        decompressed = mgard.decompress(compressed).astype(np.float32)
        return decompressed
    
    def decompress(self):
        pass
