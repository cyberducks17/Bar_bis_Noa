import random
import socket
import json
import base64
import webbrowser
import os


SEND_BLOCK_SIZE = 8192
FILE_READ_BLOCK = 4096


def three_way_handshake(client_socket):
    client_seq = random.randint(0, 1000)
    data_to_send = {"SYN": 1, "SEQ": client_seq}
    client_socket.send(str(data_to_send).encode())
    client_seq += 1

    data = client_socket.recv(SEND_BLOCK_SIZE).decode()
    headers_and_data = json.loads(data.replace("'",'"'))

    server_ack = int(headers_and_data["ACK"])
    server_seq = int(headers_and_data["SEQ"])
    server_syn = int(headers_and_data["SYN"])

    client_ack = server_seq + server_syn

    data_to_send = {"ACK": client_ack, "SEQ": client_seq}
    
    client_socket.send(str(data_to_send).encode())
    return client_ack, client_seq


def recive_data_from_server(client_socket, client_ack, client_seq):
    html_data = ""

    data_to_send = {"ACK": client_ack, "SEQ": client_seq, "DATA": "Hi SpongeBob SquarePants it Patrick!"}
    client_socket.send(str(data_to_send).encode())

    client_seq += len(data_to_send["DATA"])

    data = client_socket.recv(SEND_BLOCK_SIZE).decode()
    data = client_socket.recv(SEND_BLOCK_SIZE).decode()
    headers_and_data = json.loads(data.replace("'", '"'))

    server_ack = int(headers_and_data["ACK"])
    server_seq = int(headers_and_data["SEQ"])
    server_data = headers_and_data["DATA"]
    
    client_ack += len(server_data)

    server_data = server_data.replace("START\n", "")
    
    while "\nEND" not in server_data:
        
        server_data = base64.b64decode(server_data).decode()
        html_data += server_data
        
        data_to_send = {"ACK": client_ack, "SEQ": client_seq}
        client_socket.send(str(data_to_send).encode())
        
        data = client_socket.recv(SEND_BLOCK_SIZE).decode()
        headers_and_data = json.loads(data.replace("'",'"'))

        server_ack = int(headers_and_data["ACK"])
        server_seq = int(headers_and_data["SEQ"])
        server_data = headers_and_data["DATA"]

        client_ack += len(server_data)

    server_data = server_data.replace("\nEND", "")
    server_data = base64.b64decode(server_data).decode()
    html_data += server_data
    
    data_to_send = {"ACK": client_ack, "SEQ": client_seq}
    client_socket.send(str(data_to_send).encode())

    return client_ack, client_seq, html_data


def fin_handshake(client_socket, client_ack, client_seq):
    data_to_send = {"ACK": client_ack, "SEQ": client_seq, "FIN": 1}
    client_seq += 1
    client_socket.send(str(data_to_send).encode())

    data = client_socket.recv(SEND_BLOCK_SIZE).decode()
    headers_and_data = json.loads(data.replace("'",'"'))
    server_ack = int(headers_and_data["ACK"])
    server_seq = int(headers_and_data["SEQ"])
    server_FIN = int(headers_and_data["FIN"])
    client_ack += server_FIN

    data_to_send = {"ACK": client_ack, "SEQ": client_seq}
    client_socket.send(str(data_to_send).encode())
    return client_ack, client_seq


def client_program():

    host = socket.gethostname()  # as both code is running on same pc
    port = 5000  # socket server port number

    client_socket = socket.socket()  # instantiate
    client_socket.connect((host, port))  # connect to the server
    client_ack, client_seq = three_way_handshake(client_socket)
    client_ack, client_seq, html_data = recive_data_from_server(client_socket, client_ack, client_seq)
    client_ack, client_seq = fin_handshake(client_socket, client_ack, client_seq)

    data = client_socket.recv(SEND_BLOCK_SIZE).decode()
    print(data)

    client_socket.close()

    html_file = open("data.html", "w")
    html_file.write(html_data)
    html_file.close()

    webbrowser.open('file://' + os.path.realpath("data.html"))


if __name__ == '__main__':
    client_program()
