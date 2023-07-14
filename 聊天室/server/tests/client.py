# coding:utf-8
# user: 冷不丁
# @FILE_NAME: client
# @time: 2023/7/7 08:57
import socket

client = socket.socket()

try:
    client.connect(("localhost", 8080))
    while True:
        client.send('hello'.encode("utf-8"))
        recv_data = client.recv(1024)
        if not recv_data:
            break
        print(recv_data.decode('utf-8'))
except Exception:
    client.close()
