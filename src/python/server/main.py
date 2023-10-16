import http.server
import socketserver
import threading

from NetAPI import HttpAPI


# Define the request handler class
class MyRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, HttpApi, *args, **kwargs):
        self.HttpApi = HttpApi
        super().__init__(*args, **kwargs)

    def do_GET(self):
        # Access the custom variable in your GET request handling
        msgType = (self.headers.get('type'))
        if msgType == 'init' :
            blockOffset = int(self.headers.get('offset'))
            L3Size = int(self.headers.get('L3Size'))
            L4Size = int(self.headers.get('L4Suze'))
            Policy = self.headers.get('Policy')
            FileName = self.headers.get('FileName') # FileName to save the file in
            HttpAPI.reInit(blockSize=blockOffset,L3CacheSize=L3Size,L4CacheSize=L4Size,policy=Policy)

        elif msgType == 'BlockReq':
            tol = float(self.headers.get('tol'))
            timestep = int(self.headers.get('timestep'))
            x = int(self.headers.get('x'))
            y = int(self.headers.get('y'))
            z = int(self.headers.get('z'))
            blockId = (tol,timestep,x,y,z)
            print("get : ",blockId)
            compressed = self.HttpApi.get(blockId)
            self.send_response(200)
            # self.send_header("Content-type", "application/octet-stream")  # Set the appropriate content type
            self.end_headers()
            self.wfile.write(compressed)




# Create a threaded HTTP server
class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    pass

def main():
    
    # interface to interact with the system 
    httpApi = HttpAPI()

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
