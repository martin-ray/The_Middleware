import socket

# Define the server address and port
server_address = ('localhost', 12345)

# Create a socket to connect to the server
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    # Connect to the server
    client_socket.connect(server_address)

    # Command to clear the page cache
    command = "echo 1 > /proc/sys/vm/drop_caches"

    # Send the command to the server
    client_socket.send(command.encode())
    print("Command sent to server")

    # Receive the response from the server
    response = client_socket.recv(1024).decode()
    print("Server response:", response)

except Exception as e:
    print("Error:", str(e))

finally:
    # Close the client socket
    client_socket.close()
