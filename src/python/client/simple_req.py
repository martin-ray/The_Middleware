import requests
import _mgard as mgard
import numpy as np

# URL of the server
url = "http://localhost:8080"

while True:
    # Get user input for parameters
    time = int(input("Enter timestep: "))
    x = int(input("Enter x: "))
    y = int(input("Enter y: "))
    z = int(input("Enter z: "))
    
    # Define parameters for the request
    params = {
        'time': time,
        'x': x,
        'y': y,
        'z': z
    }
    
    # Send the HTTP GET request
    response = requests.get(url, params=params)
    response_content = response.content
    numpy_array = np.frombuffer(response_content, dtype=np.uint8)
    decompressed = mgard.decompress(numpy_array)
    print("size decompressed data:",decompressed.nbytes)

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
