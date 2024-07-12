import socket
import threading
import base64
import os

class ChatClient:
    def __init__(self, server_host='127.0.0.1', server_port=12345):
        self.server_host = server_host
        self.server_port = server_port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.download_dir = "downloads"
        self.connected = False
        
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)

    def connect_to_server(self):
        try:
            self.client_socket.connect((self.server_host, self.server_port))
            self.connected = True
            print(f"连接到服务器 {self.server_host}:{self.server_port} 成功！")
            self.send_message("新用户加入聊天室")
        except Exception as e:
            print(f"连接到服务器失败: {e}")

    def send_message(self, message):
        try:
            self.client_socket.send(message.encode())
        except Exception as e:
            print(f"发送消息时出错: {e}")

    def receive_message(self):
        while self.connected:
            try:
                message = self.client_socket.recv(1024).decode()
                if not message:
                    break
                if message.startswith("/file "):
                    self.save_file(message[6:])
                elif message.startswith("你已被踢出聊天室，原因："):
                    print(message)
                    self.connected = False
                    self.client_socket.close()
                    break
                else:
                    print(message)
            except OSError as e:
                print(f"接收消息时出错: {e}")
                break

    def send_file(self, file_path):
        try:
            filename = os.path.basename(file_path)
            with open(file_path, "rb") as file:
                file_data = base64.b64encode(file.read()).decode()
            self.send_message(f"/file {filename}:{file_data}")
        except Exception as e:
            print(f"发送文件时出错: {e}")

    def save_file(self, file_info):
        try:
            filename, file_data_base64 = file_info.split(":", 1)
            file_data = base64.b64decode(file_data_base64.encode())
            file_path = os.path.join(self.download_dir, filename)
            with open(file_path, "wb") as file:
                file.write(file_data)
            print(f"文件 {filename} 已成功保存到 {file_path}")
        except Exception as e:
            print(f"保存文件时出错: {e}")

    def reconnect(self):
        try:
            self.client_socket.close()
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connect_to_server()
            threading.Thread(target=self.receive_message).start()
        except Exception as e:
            print(f"重新连接时出错: {e}")

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
            else:
                self.send_message(message)

if __name__ == "__main__":
    client = ChatClient()
    client.start()
