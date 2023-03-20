import socket


def client_program():
    RECV_BLOCK_SIZE = 8192 # Max size of input from socket in a single recv
    host = "IP" # The ip that you will connect to
    port = 5000  # Socket server port number

    client_socket = socket.socket()  # Instantiate
    client_socket.connect((host, port))  # Connect to the server

    client_socket.send("message".encode())  # Send message (must encode it to bytes)
    data = client_socket.recv(RECV_BLOCK_SIZE).decode()  # Receive message (must decode it from bytes to string)

    client_socket.close()  # Close the connection


if __name__ == '__main__':
    client_program()