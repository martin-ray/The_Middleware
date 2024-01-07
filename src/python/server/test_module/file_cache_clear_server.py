import socket
import os

# Define the server address and port
server_address = ('localhost', 12345)

# Create a socket to listen for incoming connections
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(server_address)
server_socket.listen(1)

print("Server is listening on {}:{}".format(*server_address))

while True:
    # Wait for a connection
    print("Waiting for a connection...")
    client_socket, client_address = server_socket.accept()
    print("Connection established with {}:{}".format(*client_address))

    try:
        # Receive the command from the client
        command = client_socket.recv(1024).decode()
        print("Received command: {}".format(command))

        # Execute the received command
        result = os.system(command)

        # Send the result back to the client
        response = "Command executed with exit code {}".format(result)
        client_socket.send(response.encode())
        print("Response sent to client")

    except Exception as e:
        print("Error:", str(e))

    finally:
        # Close the client socket
        client_socket.close()
