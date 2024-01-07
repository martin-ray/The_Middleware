import socket

class ServerClient:
    def __init__(self, server_address=('localhost', 12345)):
        self.server_address = server_address
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        try:
            self.client_socket.connect(self.server_address)
            print("Connected to the server")
        except Exception as e:
            print("Error:", str(e))

    def send_command(self, command):
        try:
            # Send the command to the server
            self.client_socket.send(command.encode())
            print("Command sent to server")

            # Receive the response from the server
            response = self.client_socket.recv(1024).decode()
            print("Server response:", response)
        except Exception as e:
            print("Error:", str(e))

    def close(self):
        try:
            # Close the client socket
            self.client_socket.close()
            print("Client socket closed")
        except Exception as e:
            print("Error:", str(e))

# Example usage:
if __name__ == "__main__":
    client = ServerClient()
    client.connect()

    command_to_send = "echo 1 > /proc/sys/vm/drop_caches"
    client.send_command(command_to_send)

    client.close()

