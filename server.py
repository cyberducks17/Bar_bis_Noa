import threading
import socket
import json
import random
import argparse
import base64


SEND_BLOCK_SIZE = 8192
FILE_READ_BLOCK = 4096


def check_syn_ack(conn):
    data = conn.recv(SEND_BLOCK_SIZE).decode()

    try:
        headers_and_data = json.loads(data.replace("'",'"'))

        syn_client = headers_and_data["SYN"]
        seq_client = headers_and_data["SEQ"]

        syn_client = int(syn_client)
        seq_client = int(seq_client)
        
        if not syn_client == 1:
            raise Exception("SYN must be 1")

        if seq_client < 0:
            raise Exception("SEQ cant be negative")

        seq_server = random.randint(0, 1000)

        server_ack = seq_client + syn_client

        data_to_send = {"SYN": 1, "SEQ": seq_server, "ACK": server_ack}

        conn.send(str(data_to_send).encode())
        seq_server += 1

        data = conn.recv(SEND_BLOCK_SIZE).decode()

        headers_and_data = json.loads(data.replace("'",'"'))

        ack_client = headers_and_data["ACK"]
        seq_client = headers_and_data["SEQ"]
        
        ack_client = int(ack_client)
        seq_client = int(seq_client)

        if not ack_client == seq_server:
            raise Exception("ACK must be the same as server SEQ")

        return seq_server, server_ack
        
    except Exception as err:
        print(err)
        print("data is corrupt")
        return 0
    

def get_client_request(conn, seq_server, server_ack):
    data = conn.recv(SEND_BLOCK_SIZE).decode()
    
    try:
        headers_and_data = json.loads(data.replace("'",'"'))
        
        seq_client = headers_and_data["SEQ"]
        ack_client = headers_and_data["ACK"]

        ack_client = int(ack_client)
        seq_client = int(seq_client)
        
        payload = headers_and_data["DATA"]

        if not seq_client == server_ack:
            raise Exception("client SEQ must be the same as server ACK")

        if not seq_server == ack_client:
            raise Exception("client ACK must be the same as server SEQ")

        server_ack += len(payload)

        data_to_send = {"SEQ": seq_server, "ACK": server_ack}
        conn.send(str(data_to_send).encode())

        if "Hi SpongeBob SquarePants it Patrick!" not in payload:
            data_to_send["DATA"] = "ERROR bad request!\nRequest must inculde 'Hi SpongeBob SquarePants it Patrick!'!"
            seq_server += len(data_to_send["DATA"])
            
            conn.send(str(data_to_send).encode())
            seq_server, server_ack = get_client_request(conn, seq_server, server_ack)
             
        return seq_server, server_ack
        
    except Exception as err:
        print(err)
        print("data is corrupt")
        return 0, 0


def send_data_to_client(conn, seq_server, server_ack, html_path):
    try:
        data_to_send = {"SEQ": seq_server, "ACK": server_ack, "DATA": "START\n"}

        html_file = open(html_path, "r")
        html_data = html_file.read(FILE_READ_BLOCK)
        while html_data:
            
            data_to_send["DATA"] = "{}{}".format(data_to_send["DATA"], base64.b64encode(html_data.encode()).decode())

            if len(html_data) < FILE_READ_BLOCK:
                data_to_send["DATA"] = "{}\nEND".format(data_to_send["DATA"])
            
            conn.send(str(data_to_send).encode())

            seq_server += len(data_to_send["DATA"])

            data = conn.recv(SEND_BLOCK_SIZE).decode()
            headers_and_data = json.loads(data.replace("'",'"'))

            seq_client = headers_and_data["SEQ"]
            ack_client = headers_and_data["ACK"]

            ack_client = int(ack_client)
            seq_client = int(seq_client)

            if not seq_client == server_ack:
                raise Exception("client SEQ must be the same as server ACK")

            if not seq_server == ack_client:
                raise Exception("client ACK must be the same as server SEQ")

            html_data = html_file.read(FILE_READ_BLOCK)
            data_to_send = {"SEQ": seq_server, "ACK": server_ack, "DATA": ""}

        data = conn.recv(SEND_BLOCK_SIZE).decode()
        
        headers_and_data = json.loads(data.replace("'",'"'))

        fin_client = headers_and_data["FIN"]
        ack_client = headers_and_data["ACK"]

        if not fin_client == 1:
            raise Exception("client must set FIN flag to 1")

        if not seq_server == ack_client:
            raise Exception("client ACK must be the same as server SEQ")
        
        server_ack += fin_client
        data_to_send = {"SEQ": seq_server, "ACK": server_ack, "FIN": 1}
        conn.send(str(data_to_send).encode())

        seq_server += 1

        data = conn.recv(SEND_BLOCK_SIZE).decode()
        
        headers_and_data = json.loads(data.replace("'",'"'))

        ack_client = headers_and_data["ACK"]

        if not seq_server == ack_client:
            raise Exception("client ACK must be the same as server SEQ")

        return seq_server, server_ack
        
    except Exception as err:
        print(err)
        print("data is corrupt")
        return 0


def serve(conn, html_file_path):
    seq_server, server_ack = check_syn_ack(conn)
        
    if not seq_server:
        conn.close()
        return

    seq_server, server_ack = get_client_request(conn, seq_server, server_ack)
    if not seq_server:
        conn.close()
        return

    seq_server, server_ack = send_data_to_client(conn, seq_server, server_ack, html_file_path)
    if not seq_server:
        conn.close()
        return

    conn.send("Well done agent Patrick you have passed layer 4 exercise".encode())

    conn.close()  # close the connection

    
def server_program():

    parser = argparse.ArgumentParser(description='server for ex bis')
    parser.add_argument('-f','--html_file_path', help='path to html file', required=True)
    args = parser.parse_args()

    html_file_path = args.html_file_path
    
    # get the hostname
    host = socket.gethostname()
    port = 5000  # initiate port no above SEND_BLOCK_SIZE

    server_socket = socket.socket()  # get instance
    # look closely. The bind() function takes tuple as argument
    server_socket.bind((host, port))  # bind host address and port together

    # configure how many client the server can listen simultaneously
    server_socket.listen(1)

    while True:
        try:
            conn, address = server_socket.accept()  # accept new connection
            print("Connection from: " + str(address))

            thread = threading.Thread(target=serve, args=(conn, html_file_path))
            thread.start()
        except Exception as err:
            print(err)


if __name__ == '__main__':
    server_program()
