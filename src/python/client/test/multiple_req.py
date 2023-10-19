import requests
import _mgard as mgard
import numpy as np
import matplotlib.pyplot as plt
import time
from request_maker import requestMaker

# URL of the server
url = "http://localhost:8080"
maker = requestMaker(256,9)

reqs = maker.randomRequester(100)

req_start_time = time.time()
while len(reqs) > 0:
    req = reqs.pop(0)
    
    # Define parameters for the request
    tol = req[0]
    timestep = req[1]
    x = req[2]
    y = req[3]
    z = req[4]

    header = {
        'type':'BlockReq',
        'tol':str(req[0]),
        'timestep': str(req[1]),
        'x': str(req[2]),
        'y': str(req[3]),
        'z': str(req[4])
    }
    
    # Send the HTTP GET request
    start_time = time.time()
    response = requests.get(url, headers=header)
    response_content = response.content
    response_content_size = len(response_content)
    numpy_array = np.frombuffer(response_content, dtype=np.uint8)

    decompressed = mgard.decompress(numpy_array).astype(np.float32)
    end_time = time.time()
    elapsed_time = end_time - start_time

    print("{}(compressed) -> {}(decompressed)".format(response_content_size,decompressed.nbytes))

    print("time to get the block:{} s".format(elapsed_time))
    # convert to 2d
    data = decompressed[0,:,:]

    # Process the response if needed
    if response.status_code == 200:
        print("Request successful")
        # print("Response body:\n",numpy_array)
    else:
        print("Request failed")

req_end_time = time.time()
total_time_to_finish = req_end_time - req_start_time
print(total_time_to_finish)