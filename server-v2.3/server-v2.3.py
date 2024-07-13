import socket
import threading
import os
import logging
from datetime import datetime

class ChatServer:
    def __init__(self, host='127.0.0.1', port=12345):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.clients = {}
        self.client_usernames = {}
        self.upload_dir = "uploads"
        self.password = "1234"
        self.history = []

        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)

        log_dir = "server_logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        logging.basicConfig(filename=os.path.join(log_dir, "server.log"), level=logging.INFO)

    def log(self, message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"{timestamp} - {message}"
        print(log_message)
        logging.info(log_message)
        self.history.append(log_message)

    def broadcast(self, message, exclude_client=None):
        for client_socket in self.clients.values():
            if client_socket != exclude_client:
                try:
                    client_socket.send(message.encode())
                except Exception as e:
                    self.log(f"发送消息时出错: {e}")

    def handle_client(self, client_socket, address):
        username = f"{address[0]}:{address[1]}"
        self.clients[username] = client_socket
        self.client_usernames[client_socket] = username
        self.log(f"新用户加入: {username}")
        self.broadcast(f"新用户加入聊天室: {username}")

        try:
            while True:
                message = client_socket.recv(1024).decode()
                if not message:
                    break
                self.process_message(client_socket, username, message)
        except OSError as e:
            self.log(f"处理来自 {username} 的消息时出错: {e}")
        finally:
            if username in self.clients:
                del self.clients[username]
            if client_socket in self.client_usernames:
                del self.client_usernames[client_socket]
            self.log(f"用户断开连接: {username}")
            self.broadcast(f"用户离开聊天室: {username}")
            client_socket.close()

    def process_message(self, client_socket, username, message):
        if message.startswith("/file "):
            self.receive_file(client_socket, message[6:])
        elif message == "/filelist":
            self.send_file_list(client_socket)
        elif message.startswith("/download "):
            self.send_file(client_socket, message[10:])
        elif message == "/history":
            self.send_history(client_socket)
        elif message.startswith("/ip"):
            client_socket.send(f"你的IP地址和端口是: {username}".encode())
        elif message.startswith("/stop "):
            self.stop_server(message[6:])
        elif message == "/list":
            self.send_user_list(client_socket)
        elif message.startswith("/kick "):
            self.kick_user(client_socket, message[6:])
        else:
            self.log(f"{username}: {message}")
            self.broadcast(f"{username}: {message}", exclude_client=client_socket)

    def receive_file(self, client_socket, filename):
        try:
            file_path = os.path.join(self.upload_dir, filename)
            with open(file_path, "wb") as file:
                while True:
                    data = client_socket.recv(1024)
                    if data == b"FILE_END":
                        break
                    file.write(data)
            self.log(f"文件 {filename} 已成功上传并保存到 {file_path}")
            client_socket.send(f"文件 {filename} 已成功上传并分配了序号 {len(os.listdir(self.upload_dir))}".encode())
            self.broadcast(f"文件 {filename} 已上传", exclude_client=client_socket)
        except Exception as e:
            self.log(f"接收文件时出错: {e}")
            client_socket.send(f"接收文件时出错: {e}".encode())

    def send_file_list(self, client_socket):
        file_list = os.listdir(self.upload_dir)
        if not file_list:
            client_socket.send("服务器上的文件列表为空".encode())
        else:
            response = "服务器上的文件列表：\n"
            for idx, filename in enumerate(file_list, start=1):
                response += f"{idx}: {filename}\n"
            client_socket.send(response.encode())

    def send_file(self, client_socket, file_index):
        try:
            file_index = int(file_index) - 1
            file_list = os.listdir(self.upload_dir)
            if 0 <= file_index < len(file_list):
                filename = file_list[file_index]
                file_path = os.path.join(self.upload_dir, filename)
                with open(file_path, "rb") as file:
                    while True:
                        data = file.read(1024)
                        if not data:
                            break
                        client_socket.send(data)
                client_socket.send(b"FILE_END")
            else:
                client_socket.send("无效的文件序号".encode())
        except Exception as e:
            self.log(f"发送文件时出错: {e}")
            client_socket.send(f"发送文件时出错: {e}".encode())

    def send_history(self, client_socket):
        history = "\n".join(self.history)
        client_socket.send(history.encode())

    def send_user_list(self, client_socket):
        user_list = "\n".join(self.clients.keys())
        client_socket.send(user_list.encode())

    def stop_server(self, password):
        if password == self.password:
            self.log("服务器即将停止")
            self.broadcast("服务器即将停止")
            for client_socket in self.clients.values():
                client_socket.close()
            self.server_socket.close()
            exit()
        else:
            self.log("停止服务器的密码错误")

    def kick_user(self, client_socket, command):
        try:
            parts = command.split()
            if len(parts) < 3:
                client_socket.send("命令格式不正确。使用 /kick [username] [reason] [password]".encode())
                return
            username, reason, password = parts[0], " ".join(parts[1:-1]), parts[-1]
            if password != self.password:
                client_socket.send("踢人命令的密码错误".encode())
                return
            if username in self.clients:
                kicked_client_socket = self.clients[username]
                kicked_client_socket.send(f"你已被踢出聊天室，原因：{reason}".encode())
                kicked_client_socket.close()
                del self.clients[username]
                del self.client_usernames[kicked_client_socket]
                self.log(f"{username} 已被踢出聊天室，原因：{reason}")
                self.broadcast(f"{username} 已被踢出聊天室，原因：{reason}")
            else:
                client_socket.send("指定的用户名不存在".encode())
        except Exception as e:
            self.log(f"踢人时出错: {e}")
            client_socket.send(f"踢人时出错: {e}".encode())

    def start(self):
        self.log(f"服务器已启动，监听 {self.host}:{self.port}")
        while True:
            client_socket, address = self.server_socket.accept()
            threading.Thread(target=self.handle_client, args=(client_socket, address)).start()

if __name__ == "__main__":
    server = ChatServer()
    server.start()
