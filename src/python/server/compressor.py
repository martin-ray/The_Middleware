import _mgard as mgard

class compressor:
    def __init__(self,L3Cache,device = "GPU") -> None:
        self.L3Cache = L3Cache

        # configure device
        self.config = mgard.Config()
        if device == "OMP":
            self.config.dev_type = mgard.DeviceType.OMP
        elif device == "SERIAL":
            self.config.dev_type = mgard.DeviceType.SERIAL
    
    def compress_req(self,blockId,original,tol):
        compressed = mgard.compress(original, tol, 0, mgard.ErrorBoundType.REL, self.config)
        self.L3Cache.put(blockId,compressed)
        return
    
    def decompress(self,original):
        compressed = mgard.compress(original, tol, 0, mgard.ErrorBoundType.REL, self.config)
        return compressed
    
