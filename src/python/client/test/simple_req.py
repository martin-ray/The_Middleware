import requests
import _mgard as mgard
import numpy as np
import matplotlib.pyplot as plt

# URL of the server
url = "http://localhost:8080"

while True:
    # Get user input for parameters # ここはstrがたじゃないとダメ見たいですね。
    time = (input("Enter timestep: "))
    x = (input("Enter x: "))
    y = (input("Enter y: "))
    z = (input("Enter z: "))
    tol = (input("Enter tol:"))
    
    # Define parameters for the request
    header = {
        'type':'BlockReq',
        'timestep': time,
        'x': x,
        'y': y,
        'z': z,
        'tol':tol
    }
    
    # Send the HTTP GET request
    response = requests.get(url, headers=header)
    response_content = response.content
    response_content_size = len(response_content)
    numpy_array = np.frombuffer(response_content, dtype=np.uint8)

    decompressed = mgard.decompress(numpy_array).astype(np.float32)

    print("{}(compressed) -> {}(decompressed)".format(response_content_size,decompressed.nbytes))

    # convert to 2d
    data = decompressed[0,:,:]
    plt.imshow(data, cmap='jet')
    plt.title("tol={}.timestep={}.x={}.y={}.z={}".format(tol,time,x,y,z))
    plt.savefig("./tol={}.timestep={}.x={}.y={}.z={}.png".format(tol,time,x,y,z))

    # Process the response if needed
    if response.status_code == 200:
        print("Request successful")
        # print("Response body:\n",numpy_array)
    else:
        print("Request failed")

    # Ask if the user wants to make another request
    another_request = input("Do you want to make another request? (yes/no): ")
    if another_request.lower() != 'yes':
        break
