import _mgard as mgard
from collections import deque


# コンプレッサーの扱い方について今迷っています。i/oみたいに、一回一回、お願いするか、キューみたいなのを用意しておいて、
# 別スレッドで動いているコンプレッサーが自分でキューからデータを取ってくるか。どっちにするか。
class compressor:
    def __init__(self,L3Cache,device = "GPU") -> None:
        self.L3Cache = L3Cache
        self.originalQ = deque()
        
        # configure device
        self.config = mgard.Config()
        if device == "OMP":
            self.config.dev_type = mgard.DeviceType.OMP
        elif device == "SERIAL":
            self.config.dev_type = mgard.DeviceType.SERIAL
    
    def compress_req(self,blockId,original):
        tol = blockId[0]
        compressed = mgard.compress(original,tol, 0, mgard.ErrorBoundType.REL, self.config)
        self.L3Cache.put(blockId,compressed)
        return
    
    def compress(self,original,tol):
        compressed = mgard.compress(original, tol, 0, mgard.ErrorBoundType.REL, self.config)
        return compressed
    
