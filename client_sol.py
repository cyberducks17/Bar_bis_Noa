import random
import socket
import json
import base64
import webbrowser
import os


SEND_BLOCK_SIZE = 8192
FILE_READ_BLOCK = 4096


# Handle the three way handshake (the start of the connection)
def three_way_handshake(client_socket):
    client_seq = random.randint(0, 1000)  # Initialize the SEQ value for the client (in real life it can go up to 2.1B+)
    data_to_send = {"SYN": 1, "SEQ": client_seq}  # Create dictionry with the values to send
    client_socket.send(str(data_to_send).encode())  # Send first SYN to server
    client_seq += 1

    data = client_socket.recv(SEND_BLOCK_SIZE).decode()  # Recve first SYN ACK from server
    # When dict int python use ' insted of " so in order that the json will work you need to change it to "
    headers_and_data = json.loads(data.replace("'", '"'))

    # Get the values of the flags in the packet the client had sent
    server_ack = int(headers_and_data["ACK"])
    server_seq = int(headers_and_data["SEQ"])
    server_syn = int(headers_and_data["SYN"])

    client_ack = server_seq + server_syn  # Update the client ack value.

    data_to_send = {"ACK": client_ack, "SEQ": client_seq}  # Create dictionry with the values to send.
    
    client_socket.send(str(data_to_send).encode())  # Send back ACK to server and this way established the connection.
    return client_ack, client_seq  # Return the client ack and seq for future packets.


# Get the html data from server and as part of ex2 will also cut and decode it accordingly
def recive_data_from_server(client_socket, client_ack, client_seq):
    html_data = ""

    data_to_send = {"ACK": client_ack, "SEQ": client_seq, "DATA": "Hi SpongeBob SquarePants it Patrick!"}  # Create dictionry with the values to send
    client_socket.send(str(data_to_send).encode())  # Send the request to the server.

    client_seq += len(data_to_send["DATA"])  # Update the client SEQ value

    # Recve the ACK from the server to the request that he send.
    # Becouse this sol is just poc it doas not check the values of the of ACK and SEQ.
    # In a real sol they need to check the values and not trust the server.
    data = client_socket.recv(SEND_BLOCK_SIZE).decode()
    data = client_socket.recv(SEND_BLOCK_SIZE).decode()

    # When dict int python use ' insted of " so in order that the json will work you need to change it to "
    headers_and_data = json.loads(data.replace("'", '"'))

    # Get the values of the flags in the packet the client had sent
    server_ack = int(headers_and_data["ACK"])
    server_seq = int(headers_and_data["SEQ"])
    server_data = headers_and_data["DATA"]
    
    client_ack += len(server_data)  # Update the client ACK value

    # Part of the ex2 remove the string that single the start of the main data from the server to later decode it with base64
    server_data = server_data.replace("START\n", "")
    
    # Run until the server dont have anymore to send know it by that that the data will end with the string END
    while "\nEND" not in server_data:
        
        # Part of the ex2 decode the data with base64 to later save the html file and show it
        server_data = base64.b64decode(server_data).decode()
        html_data += server_data  # Put togther the html data as part of ex2
        
        data_to_send = {"ACK": client_ack, "SEQ": client_seq}  # Create dictionry with the values to send
        client_socket.send(str(data_to_send).encode())
        
        data = client_socket.recv(SEND_BLOCK_SIZE).decode()
        # When dict int python use ' insted of " so in order that the json will work you need to change it to "
        headers_and_data = json.loads(data.replace("'", '"'))

        # Get the values of the flags in the packet the client had sent
        server_ack = int(headers_and_data["ACK"])
        server_seq = int(headers_and_data["SEQ"])
        server_data = headers_and_data["DATA"]

        client_ack += len(server_data)
    # Part of the ex2 remove the string that single the start of the main data from the server to later decode it with base64
    server_data = server_data.replace("\nEND", "")
    # Part of the ex2 decode the data with base64 to later save the html file and show it
    server_data = base64.b64decode(server_data).decode()
    html_data += server_data  # Put togther the html data as part of ex2
    
    data_to_send = {"ACK": client_ack, "SEQ": client_seq}  # Create dictionry with the values to send
    client_socket.send(str(data_to_send).encode())

    # return the client seq and ack for future packets and the html data as part of ex2 
    return client_ack, client_seq, html_data


# Handle the three way FIN handshake (the end of the connection)
def fin_handshake(client_socket, client_ack, client_seq):
    data_to_send = {"ACK": client_ack, "SEQ": client_seq, "FIN": 1}  # Create dictionry with the values to send
    client_seq += 1
    client_socket.send(str(data_to_send).encode())  # Send the FIN flag to the server

    data = client_socket.recv(SEND_BLOCK_SIZE).decode()  # Receve the FIN flag from the server
    # When dict int python use ' insted of " so in order that the json will work you need to change it to "
    headers_and_data = json.loads(data.replace("'", '"'))

    # Get the values of the flags in the packet the client had sent
    server_ack = int(headers_and_data["ACK"])
    server_seq = int(headers_and_data["SEQ"])
    server_FIN = int(headers_and_data["FIN"])
    client_ack += server_FIN

    data_to_send = {"ACK": client_ack, "SEQ": client_seq}  # Create dictionry with the values to send
    client_socket.send(str(data_to_send).encode())  # Send the finale ACK to the server to end the connection
    return client_ack, client_seq


def client_program():

    host = socket.gethostname()  # as both code is running on same pc
    port = 5000  # socket server port number

    client_socket = socket.socket()  # instantiate
    client_socket.connect((host, port))  # connect to the server
    client_ack, client_seq = three_way_handshake(client_socket)
    client_ack, client_seq, html_data = recive_data_from_server(client_socket, client_ack, client_seq)
    client_ack, client_seq = fin_handshake(client_socket, client_ack, client_seq)

    data = client_socket.recv(SEND_BLOCK_SIZE).decode()  # If all the discussion went smoothly the will recve ainput that passed the ex1
    print(data)

    client_socket.close()

    # all the next code is for ex2 to show the input in the web browser.
    html_file = open("data.html", "w")
    html_file.write(html_data)
    html_file.close()

    webbrowser.open('file://' + os.path.realpath("data.html"))


if __name__ == '__main__':
    client_program()
