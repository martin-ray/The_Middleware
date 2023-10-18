import _mgard as mgard
import numpy as np

class Decompressor:
    def __init__(self,L1Cache,device = "GPU") -> None:
        self.L1Cache = L1Cache
        # configure device
        self.config = mgard.Config()
        if device == "OMP":
            self.config.dev_type = mgard.DeviceType.OMP
        elif device == "SERIAL":
            self.config.dev_type = mgard.DeviceType.SERIAL

    def decompress_req(self,blockId,compressed):
        decompressed = mgard.decompress(compressed).astype(np.float32)
        self.L1Cache.put(blockId,decompressed)
        return
    
    def decompress_req_urgent(self,blockId,compressed):
        decompressed = mgard.decompress(compressed).astype(np.float32)
        return decompressed
    
    # 呼び出し側はblockIdを持っている状態
    def decompress(self,compressed):
        decompressed = mgard.decompress(compressed).astype(np.float32)
        return decompressed
