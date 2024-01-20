import http.server
import socketserver
import threading
import json
from NetAPI import HttpAPI
import time

# Define the request handler class
class MyRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, HttpApi, *args, **kwargs):

        # 設定変更可能
        self.HttpAPI = HttpApi
        super().__init__(*args, **kwargs)

    def do_GET(self):
        # Access the custom variable in GET request
        msgType = (self.headers.get('type'))
        
        if msgType == 'init' :
            blockOffset = int(self.headers.get('offset'))
            L3Size = int(self.headers.get('L3Size'))
            L4Size = int(self.headers.get('L4Size'))
            Policy = self.headers.get('Policy')
            targetTol = self.headers.get('targetTol')
            FileName = self.headers.get('FileName') # FileName to save the file in
            self.HttpAPI.reInit(blockSize=blockOffset,L3CacheSize=L3Size,L4CacheSize=L4Size,policy=Policy,targetTol= targetTol)
            self.send_response(200)
            self.end_headers()
            # TODO データの範囲を送信

        elif msgType == 'BlockReq':
            print("Got request from prefetcher")
            tol = float(self.headers.get('tol'))
            timestep = int(self.headers.get('timestep'))
            x = int(self.headers.get('x'))
            y = int(self.headers.get('y'))
            z = int(self.headers.get('z'))
            blockId = (tol,timestep,x,y,z)
            blockId = self.HttpAPI.adjustBlockId(blockId)
            compressed = self.HttpAPI.get(blockId)

            # Capture the current timestamp in milliseconds
            timestamp_ms = int(time.time() * 1000)

            # Add the timestamp to the response header
            self.send_response(200)
            self.send_header('X-Network-Time', str(timestamp_ms)) 
            self.end_headers()
            self.wfile.write(compressed)
            # print(f"Sent back the block. size is {compressed.nbytes}")

        # cache hit率を測定するために必要な部分
        elif msgType == 'BlockReqUsr':
            tol = float(self.headers.get('tol'))
            timestep = int(self.headers.get('timestep'))
            x = int(self.headers.get('x'))
            y = int(self.headers.get('y'))
            z = int(self.headers.get('z'))
            blockId = (tol,timestep,x,y,z)
            blockId = self.HttpAPI.adjustBlockId(blockId)
            compressed = self.HttpAPI.getUsr(blockId)

            timestamp_ms = int(time.time() * 1000)

            # Add the timestamp to the response header
            self.send_response(200)
            self.send_header('X-Network-Time', str(timestamp_ms)) 
            self.end_headers()
            self.wfile.write(compressed)

        elif msgType == 'noCompress':
            timestep = int(self.headers.get('timestep'))
            tol = float(self.headers.get('tol'))
            x = int(self.headers.get('x'))
            y = int(self.headers.get('y'))
            z = int(self.headers.get('z'))
            blockId = (tol,timestep,x,y,z)
            blockId = self.HttpAPI.adjustBlockId(blockId)
            original = self.HttpAPI.getOriginal(blockId)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(original)


        elif msgType == 'userPoint':
            timestep = int(self.headers.get('timestep'))
            tol = float(self.headers.get('tol'))
            x = int(self.headers.get('x'))
            y = int(self.headers.get('y'))
            z = int(self.headers.get('z'))
            blockId = (tol,timestep,x,y,z)
            self.HttpAPI.informUserPoint(blockId)
            self.HttpAPI.informUserPoint(blockId)
            self.send_response(200)
            self.end_headers()

        elif msgType == 'getStats':
            totalReqs = self.HttpAPI.numReqs
            nL3Hit = self.HttpAPI.numL3Hit
            nL4Hit = self.HttpAPI.numL4Hit
            StorageReadTime = self.HttpAPI.StorageReadTime
            CompTime = self.HttpAPI.CompTime
            NumL3Prefetch = self.HttpAPI.L3Pref.numPrefetches
            NumL3PrefetchL4Hit = self.HttpAPI.L3Pref.numL4Hits
            numL4Prefetch = self.HttpAPI.L4Pref.numPrefetches

            # Create a dictionary with the stats
            stats_data = {
                'ReqsToServer': totalReqs,
                'nL3Hit': nL3Hit,
                'nL4Hit': nL4Hit,
                'NumL3Prefetch':NumL3Prefetch,
                'NumL3PrefetchL4Hit':NumL3PrefetchL4Hit,
                'numL4Prefetch':numL4Prefetch,
                'StorageReadTime':StorageReadTime,
                'CompTime':CompTime
            }

            # Convert the dictionary to JSON
            stats_json = json.dumps(stats_data)

            # Send the JSON response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(stats_json.encode('utf-8'))



# Create a threaded HTTP server
class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    pass

def main():
    
    # interface to interact with the system 
    httpApi = HttpAPI(blockSize=256)

    # Set the server address and port
    server_address = ('', 8080)

    # Create and start the threaded HTTP server
    httpd = ThreadedHTTPServer(server_address, lambda *args, **kwargs: MyRequestHandler(httpApi, *args, **kwargs))

    # Start a separate thread for the server
    server_thread = threading.Thread(target=httpd.serve_forever)
    server_thread.daemon = True  # The server thread will exit when the main program exits
    server_thread.start()

    print(f"Server started on port {server_address[1]}")
    
    try:
        # Keep the main thread alive while the server runs in the background
        server_thread.join()
    except KeyboardInterrupt:
        # Handle Ctrl+C to gracefully shut down the server
        print("Shutting down the server")
        httpd.shutdown()

        
if __name__ == '__main__':
    main()
