import threading
import socket
import json
import random
import argparse
import base64


SEND_BLOCK_SIZE = 8192
FILE_READ_BLOCK = int(SEND_BLOCK_SIZE / 2)


# Check if the client established a connection correctly.
def check_syn_ack(conn):
    data = conn.recv(SEND_BLOCK_SIZE).decode()  # recv the input from the server

    # In any case of error print the error and return 0, 0 to signle to close the connection
    try:
        # When dict int python use ' insted of " so in order that the json will work you need to change it to "
        headers_and_data = json.loads(data.replace("'", '"'))

        # Get the values of the flags in the packet the client had sent
        syn_client = int(headers_and_data["SYN"])
        seq_client = int(headers_and_data["SEQ"])
        
        # If true then client had sent worng input so will close the connection
        if not syn_client == 1:
            raise Exception("SYN must be 1")

        # If true then client had sent worng input so will close the connection
        if seq_client < 0:
            raise Exception("SEQ cant be negative")

        seq_server = random.randint(0, 1000)  # Initialize the SEQ value for the server (in real life it can go up to 2.1B+)

        server_ack = seq_client + syn_client  # Update the server ack value

        data_to_send = {"SYN": 1, "SEQ": seq_server, "ACK": server_ack}  # Create dictionry with the values to send

        conn.send(str(data_to_send).encode())  # Send the encoded data to server
        seq_server += 1

        data = conn.recv(SEND_BLOCK_SIZE).decode()  # recv the input from the server

         # When dict int python use ' insted of " so in order that the json will work you need to change it to "
        headers_and_data = json.loads(data.replace("'",'"'))

        # Get the values of the flags in the packet the client had sent
        ack_client = int(headers_and_data["ACK"])
        seq_client = int(headers_and_data["SEQ"])

        # If true then client had sent worng input so will close the connection
        if not ack_client == seq_server:
            raise Exception("ACK must be the same as server SEQ")

        return seq_server, server_ack
        
    except Exception as err:
        print(err)
        print("data is corrupt")
        return 0
    

# Get the client request
def get_client_request(conn, seq_server, server_ack):
    data = conn.recv(SEND_BLOCK_SIZE).decode()  # recv the input from the server
    # In any case of error print the error and return 0, 0 to signle to close the connection
    try:
        # When dict int python use ' insted of " so in order that the json will work you need to change it to "
        headers_and_data = json.loads(data.replace("'", '"'))
        
        # Get the values of the flags in the packet the client had sent
        seq_client = int(headers_and_data["SEQ"])
        ack_client = int(headers_and_data["ACK"])

        payload = headers_and_data["DATA"]  # Get the data part of the packet

        # If true then client had sent worng input so will close the connection
        if not seq_client == server_ack:
            raise Exception("client SEQ must be the same as server ACK")

        # If true then client had sent worng input so will close the connection
        if not seq_server == ack_client:
            raise Exception("client ACK must be the same as server SEQ")

        server_ack += len(payload)  # Update the server ack value

        data_to_send = {"SEQ": seq_server, "ACK": server_ack}  # Create dictionry with the values to send
        conn.send(str(data_to_send).encode())  # Send the packet to the client

        # Check if the request from the client was correct and if not send him what the request should include,
        # Use recursion call to recive agian the request from the client.
        if "Hi SpongeBob SquarePants it Patrick!" not in payload:
            data_to_send["DATA"] = "ERROR bad request!\nRequest must inculde 'Hi SpongeBob SquarePants it Patrick!'!"
            seq_server += len(data_to_send["DATA"])  # Update the server ack value
            
            conn.send(str(data_to_send).encode())
            # Use recursion call to recive agian the request from the client.
            seq_server, server_ack = get_client_request(conn, seq_server, server_ack)
             
        return seq_server, server_ack
        
    except Exception as err:
        print(err)
        print("data is corrupt")
        return 0, 0


# send the client the correct info
def send_data_to_client(conn, seq_server, server_ack, html_path):
    # In any case of error print the error and return 0, 0 to signle to close the connection
    try:
        data_to_send = {"SEQ": seq_server, "ACK": server_ack, "DATA": "START\n"}  # Create dictionry with the values to send
        
        # Read the input html file to send it in segmants to the client
        html_file = open(html_path, "r")
        
        html_data = html_file.read(FILE_READ_BLOCK)  # Read the file in blocks
        # Run while there is still data to read

        while html_data:
            # Encode the data to send with base64
            data_to_send["DATA"] = "{}{}".format(data_to_send["DATA"], base64.b64encode(html_data.encode()).decode())
            # When reach the last block of the file add END to the data so the client will now to send FIN
            if len(html_data) < FILE_READ_BLOCK:
                data_to_send["DATA"] = "{}\nEND".format(data_to_send["DATA"])
            
            conn.send(str(data_to_send).encode())

            seq_server += len(data_to_send["DATA"])  # Update the server seq value

            data = conn.recv(SEND_BLOCK_SIZE).decode()  # recv the input from the server
            # When dict int python use ' insted of " so in order that the json will work you need to change it to "
            headers_and_data = json.loads(data.replace("'", '"'))

            seq_client = int(headers_and_data["SEQ"])
            ack_client = int(headers_and_data["ACK"])
            # If true then client had sent worng input so will close the connection
            if not seq_client == server_ack:
                raise Exception("client SEQ must be the same as server ACK")

            # If true then client had sent worng input so will close the connection
            if not seq_server == ack_client:
                raise Exception("client ACK must be the same as server SEQ")

            html_data = html_file.read(FILE_READ_BLOCK)  # Read the file in blocks
            data_to_send = {"SEQ": seq_server, "ACK": server_ack, "DATA": ""}  # Create dictionry with the values to send

        html_file.close()

        data = conn.recv(SEND_BLOCK_SIZE).decode()  # recv the input from the server
        
        # When dict int python use ' insted of " so in order that the json will work you need to change it to "
        headers_and_data = json.loads(data.replace("'", '"'))

        fin_client = int(headers_and_data["FIN"])
        ack_client = int(headers_and_data["ACK"])
        
        # If true then client had sent worng input so will close the connection
        if not fin_client == 1:
            raise Exception("client must set FIN flag to 1")

        # If true then client had sent worng input so will close the connection
        if not seq_server == ack_client:
            raise Exception("client ACK must be the same as server SEQ")
        
        server_ack += fin_client
        data_to_send = {"SEQ": seq_server, "ACK": server_ack, "FIN": 1}  # Create dictionry with the values to send
        conn.send(str(data_to_send).encode())

        seq_server += 1

        data = conn.recv(SEND_BLOCK_SIZE).decode()  # recv the input from the server
        
        # When dict int python use ' insted of " so in order that the json will work you need to change it to "
        headers_and_data = json.loads(data.replace("'", '"'))

        ack_client = headers_and_data["ACK"]

        # If true then client had sent worng input so will close the connection
        if not seq_server == ack_client:
            raise Exception("client ACK must be the same as server SEQ")

        return seq_server, server_ack
        
    except Exception as err:
        print(err)
        print("data is corrupt")
        return 0


def serve(conn, html_file_path):
    seq_server, server_ack = check_syn_ack(conn)
    
    # If true then a error occured so will close the connection and exit
    if not seq_server:
        conn.close()  # close the connection
        return

    # If true then a error occured so will close the connection and exit
    seq_server, server_ack = get_client_request(conn, seq_server, server_ack)
    if not seq_server:
        conn.close()  # close the connection
        return

    # If true then a error occured so will close the connection and exit
    seq_server, server_ack = send_data_to_client(conn, seq_server, server_ack, html_file_path)
    if not seq_server:
        conn.close()  # close the connection
        return

    # If the client recved this masseage then he manged to send all packets with the correct falgs value and finshed layer 4
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
            conn, address = server_socket.accept()  # Accept new connection
            print("Connection from: " + str(address))  # Print new connection

            thread = threading.Thread(target=serve, args=(conn, html_file_path))  # Let a thread handle the new connection
            thread.start()
        except Exception as err:
            print(err)


if __name__ == '__main__':
    server_program()
