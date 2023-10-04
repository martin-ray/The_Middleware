# すべてのリクエストはここを通ってなされます。
# NetIFはL1も持ってるし、L2も持ってます。
# まあ、こいつは、ただ、L1とL2からリクエストを受けて、そのリクエストをサーバに投げるってだけだな。
# 戻ってくるデータは全部compressedされている。L1がリクエストしたら、それをdecompressするまでセットかな。
# ただ、気になるのが、L1からのリクエストは緊急なわけです。L2はどんどんリクエスト送るけど、
# L1のリクエストを優先する何か、仕組みが欲しいんですね。


# dequeはスレッドセーフ
from collections import deque


class NetIF:
    def __init__(self,Cache,serverIp):
        self.Cache = Cache
        self.sendQ = deque() 
        pass

    # 末尾に追加
    def send_req(self,blockId):
        self.sendQ.append(blockId)
    
    # 緊急なので、前に追加
    def send_req_urget(self,blockId):
        self.sendQ.appendleft(blockId)
    
    # 実際に送信。これは別スレッドで実行される
    def send(self):
        req = self.sendQ.popleft()
        print("sending ",req)

        # 帰ってきたら、ちゃんとキャッシュに入れてください！！
        pass