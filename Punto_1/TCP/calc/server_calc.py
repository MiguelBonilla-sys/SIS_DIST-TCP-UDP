import socket
import sys

def read_number(sock):
    a = ''
    while True:
        msg =  sock.recv(1)
        if (msg == b'\n'):
            break
        a += msg.decode()
    return (int(a,10))

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_address = ('localhost', 10009)
sock.bind(server_address)

sock.listen(5)

while True:
    print('waiting for a connection')
    connection, client_address = sock.accept()
    try:
        print('connection from', client_address)
        a = read_number(connection)
        b = read_number(connection)
        op = read_number(connection)
        if (op == 0):
            res = a + b
        else:
            res = a - b
        message = str(res) + "\0"
        message = message + "\0"
        connection.sendall(message.encode())
    finally:
        connection.close()