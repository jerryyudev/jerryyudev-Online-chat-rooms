import socket
import http.client
import os
import threading
import logging
from datetime import datetime

class ChatClient:
    def __init__(self, server_host='82.153.65.180', server_port=20486, proxy_host='127.0.0.1', proxy_port=10809):
        self.server_host = server_host
        self.server_port = server_port
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.client_socket = None
        self.connected = False
        self.download_dir = "downloads"
        self.buffer_size = 4096  # increased buffer size

        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)

        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

    def log(self, message):
        logging.info(message)

    def connect_to_server(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.proxy_host, self.proxy_port))

            connect_command = f"CONNECT {self.server_host}:{self.server_port} HTTP/1.1\r\n\r\n"
            self.client_socket.sendall(connect_command.encode('utf-8'))
            
            response = self.client_socket.recv(4096).decode('utf-8')
            if "200 Connection established" not in response:
                raise Exception(f"代理服务器连接失败: {response}")

            self.connected = True
            self.log(f"通过代理 {self.proxy_host}:{self.proxy_port} 连接到服务器 {self.server_host}:{self.server_port} 成功！")
        except Exception as e:
            self.log(f"无法连接到服务器: {e}")
            self.connected = False

    def receive_message(self):
        while self.connected:
            try:
                message = self.client_socket.recv(self.buffer_size).decode('utf-8', errors='ignore')
                if not message:
                    break
                if message.startswith("/file "):
                    filename = message[6:]
                    self.receive_file(filename)
                elif message.startswith("你已被踢出聊天室，原因："):
                    self.log(message)
                    self.connected = False
                    self.client_socket.close()
                    break
                elif message == "服务器即将停止":
                    self.log(message)
                    self.connected = False
                    self.client_socket.close()
                    break
                elif "文件" in message and "成功上传并分配了序号" in message:
                    self.log(message)
                else:
                    self.log(message)
            except UnicodeDecodeError as e:
                self.log(f"接收消息时出错: {e}")
                self.connected = False
                break
            except Exception as e:
                self.log(f"接收消息时出错: {e}")
                self.connected = False
                break

    def receive_file(self, filename):
        try:
            file_path = os.path.join(self.download_dir, filename)
            with open(file_path, "wb") as file:
                while True:
                    data = self.client_socket.recv(self.buffer_size)
                    if b"FILE_TRANSFER_COMPLETE" in data:
                        data = data.replace(b"FILE_TRANSFER_COMPLETE", b"")
                        if data:
                            file.write(data)
                        break
                    file.write(data)
            self.log(f"文件 {filename} 已成功接收并保存到 {file_path}")
        except Exception as e:
            self.log(f"接收文件时出错: {e}")

    def send_message(self, message):
        try:
            self.client_socket.send(message.encode('utf-8'))
        except Exception as e:
            self.log(f"发送消息时出错: {e}")

    def send_file(self, file_path):
        try:
            with open(file_path, "rb") as file:
                filename = os.path.basename(file_path)
                self.client_socket.send(f"/file {filename}".encode('utf-8'))
                while True:
                    data = file.read(self.buffer_size)
                    if not data:
                        break
                    self.client_socket.send(data)
                self.client_socket.send(b"FILE_TRANSFER_COMPLETE")
            self.log(f"文件 {filename} 已成功发送")
        except Exception as e:
            self.log(f"发送文件时出错: {e}")

    def reconnect(self):
        self.client_socket.close()
        self.connect_to_server()
        threading.Thread(target=self.receive_message).start()

    def start(self):
        self.connect_to_server()
        threading.Thread(target=self.receive_message).start()
        while True:
            message = input()
            if message == "/leave":
                self.connected = False
                self.client_socket.close()
                break
            elif message == "/reconnect":
                self.connected = False
                self.reconnect()
            elif message.startswith("/file "):
                file_path = message[6:]
                self.send_file(file_path)
            elif message.startswith("/download "):
                self.send_message(message)
            else:
                self.send_message(message)

if __name__ == "__main__":
    client = ChatClient()
    client.start()
