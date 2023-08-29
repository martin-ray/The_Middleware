import http.server
import socketserver
import urllib.parse
import numpy as np
import io
import gzip
from slice import Slicer
import _mgard as mgard


# slicer instance
slicer = Slicer() 

# Define the server request handler
class CMP_Handler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        
        # Extract parameters from the query string
        time = int(query_params.get('time', [0])[0])
        x = int(query_params.get('x', [0])[0])
        y = int(query_params.get('y', [0])[0])
        z = int(query_params.get('z', [0])[0])
        tol = 0.1
        
        # slice the data
        data = slicer.slice_single_step(time,x,x+100,y,y+100,z,z+100)
        compressed = mgard.compress(data, tol, 0)

        
        # Send the compressed block as response
        self.send_response(200)
        self.send_header("Content-type", "application/octet-stream")
        self.end_headers()
        self.wfile.write(compressed)
        print(data.nbytes)

class Ori_Handler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        
        # Extract parameters from the query string
        time = int(query_params.get('time', [0])[0])
        x = int(query_params.get('x', [0])[0])
        y = int(query_params.get('y', [0])[0])
        z = int(query_params.get('z', [0])[0])
        tol = 0.1
        
        # slice the data
        data = slicer.slice_single_step(time,x,x+100,y,y+100,z,z+100)
        compressed = mgard.compress(data, tol, 0)

        
        # Send the compressed block as response
        self.send_response(200)
        self.send_header("Content-type", "application/octet-stream")
        self.end_headers()
        self.wfile.write(compressed)
        # print(data)
        print("size:",data.nbytes)



if __name__ == "__main__":

    # Set up the server returning compressed data
    PORT = 8080
    Handler = CMP_Handler
    httpd = socketserver.TCPServer(("", PORT), Handler)

    print("Server running on port", PORT)
    httpd.serve_forever()

    # Set up the server returning original data
    # あー、そっか、pythonは非同期プログラミングじゃないからこういう風に登録してもだめなんだった。
    ORI_PORT = 8081
    OHandler = Ori_Handler
    Ohttpd = socketserver.TCPServer(("",ORI_PORT),OHandler)
    print("And on {} for original data".format(ORI_PORT))
    Ohttpd.serve_forever()
