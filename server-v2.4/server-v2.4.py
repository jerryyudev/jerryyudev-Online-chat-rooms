import socket
import threading
import os
import logging

class ChatServer:
    def __init__(self, host='127.0.0.1', port=12345, upload_dir="uploads"):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.clients = {}
        self.client_usernames = {}
        self.history = []
        self.upload_dir = upload_dir
        self.password = "1234"  # 默认密码为1234
        self.buffer_size = 4096  # increased buffer size

        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)

        # 初始化日志记录
        log_dir = "server_logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_file = os.path.join(log_dir, 'server.log')

        # 配置日志记录器
        self.logger = logging.getLogger('ChatServer')
        self.logger.setLevel(logging.INFO)

        # 创建文件处理器并设置日志级别为INFO
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)

        # 创建控制台处理器并设置日志级别为INFO
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # 创建格式化器并将其添加到处理器
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # 将处理器添加到日志记录器
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

        self.log(f"服务器已启动，监听 {self.host}:{self.port}")

    def log(self, message):
        self.logger.info(message)

    def broadcast(self, message):
        self.history.append(message)
        for client_socket in self.clients.values():
            try:
                client_socket.send(message.encode('utf-8'))
            except:
                continue

    def handle_client(self, client_socket, address):
        username = f"{address[0]}:{address[1]}"
        self.log(f"新用户加入: {username}")
        self.clients[username] = client_socket
        self.client_usernames[client_socket] = username
        self.broadcast(f"{username} 加入了聊天室")

        while True:
            try:
                message = client_socket.recv(self.buffer_size).decode('utf-8')
                if message.startswith("/file "):
                    filename = message[6:]
                    self.receive_file(client_socket, filename)
                elif message.startswith("/download "):
                    file_index = int(message.split()[1])
                    self.send_file(client_socket, file_index)
                elif message == "/filelist":
                    self.send_file_list(client_socket)
                elif message == "/userlist":
                    self.send_user_list(client_socket)
                elif message == "/history":
                    self.send_history(client_socket)
                elif message.startswith("/kick "):
                    parts = message.split(' ', 3)
                    if len(parts) == 4:
                        self.kick_user(client_socket, parts[1], parts[2], parts[3])
                elif message.startswith("/stop "):
                    self.stop_server(message.split(' ', 1)[1])
                elif message == "/ip":
                    self.send_client_ip(client_socket, address)
                else:
                    self.log(f"{username}: {message}")
                    self.broadcast(f"{username}: {message}")
            except Exception as e:
                self.log(f"处理来自 {username} 的消息时出错: {e}")
                break
        self.remove_client(client_socket, username)

    def send_client_ip(self, client_socket, address):
        client_ip = f"您的ip地址为 {address[0]}:{address[1]}"
        client_socket.send(client_ip.encode('utf-8'))

    def remove_client(self, client_socket, username):
        try:
            client_socket.close()
        except Exception as e:
            self.log(f"关闭套接字时出错: {e}")
        finally:
            if username in self.clients:
                del self.clients[username]
            if client_socket in self.client_usernames:
                del self.client_usernames[client_socket]
            self.broadcast(f"{username} 离开了聊天室")

    def receive_file(self, client_socket, filename):
        try:
            file_path = os.path.join(self.upload_dir, filename)
            self.log(f"开始接收文件: {filename}")
            with open(file_path, "wb") as file:
                while True:
                    data = client_socket.recv(self.buffer_size)
                    if b"FILE_TRANSFER_COMPLETE" in data:
                        data = data.replace(b"FILE_TRANSFER_COMPLETE", b"")
                        if data:
                            file.write(data)
                        break
                    file.write(data)
            self.log(f"文件 {filename} 已成功上传并保存到 {file_path}")
            self.broadcast(f"文件 {filename} 已成功上传并分配了序号 {len(os.listdir(self.upload_dir))}")
        except Exception as e:
            self.log(f"接收文件时出错: {e}")
            client_socket.send(f"接收文件时出错: {e}".encode('utf-8'))

    def send_file(self, client_socket, file_index):
        try:
            files = os.listdir(self.upload_dir)
            if 0 < file_index <= len(files):
                filename = files[file_index - 1]
                file_path = os.path.join(self.upload_dir, filename)
                client_socket.send(f"/file {filename}".encode('utf-8'))
                self.log(f"开始发送文件: {filename}")
                with open(file_path, "rb") as file:
                    while True:
                        data = file.read(self.buffer_size)
                        if not data:
                            break
                        client_socket.send(data)
                client_socket.send(b"FILE_TRANSFER_COMPLETE")
                self.log(f"文件 {filename} 已成功发送")
            else:
                client_socket.send("无效的文件序号".encode('utf-8'))
        except Exception as e:
            self.log(f"发送文件时出错: {e}")
            client_socket.send(f"发送文件时出错: {e}".encode('utf-8'))

    def send_file_list(self, client_socket):
        files = os.listdir(self.upload_dir)
        file_list = "\n".join([f"{i+1}: {file}" for i, file in enumerate(files)])
        client_socket.send(file_list.encode('utf-8'))

    def send_history(self, client_socket):
        history = "\n".join(self.history)
        client_socket.send(history.encode('utf-8'))

    def send_user_list(self, client_socket):
        user_list = "\n".join(self.clients.keys())
        client_socket.send(user_list.encode('utf-8'))

    def stop_server(self, password):
        if password == self.password:
            self.broadcast("服务器即将停止")
            self.log("服务器正在停止...")
            for client_socket in self.clients.values():
                client_socket.close()
            self.server_socket.close()
            os._exit(0)
        else:
            self.broadcast("停止服务器失败：密码错误")

    def kick_user(self, client_socket, target_username, reason, password):
        if password != self.password:
            client_socket.send("踢出用户失败：密码错误".encode('utf-8'))
            return
        for username, target_socket in self.clients.items():
            if username == target_username:
                target_socket.send(f"你已被踢出聊天室，原因：{reason}".encode('utf-8'))
                self.remove_client(target_socket, username)
                self.broadcast(f"{username} 被踢出聊天室，原因：{reason}")
                break

    def start(self):
        while True:
            client_socket, address = self.server_socket.accept()
            threading.Thread(target=self.handle_client, args=(client_socket, address)).start()

if __name__ == "__main__":
    server = ChatServer()
    server.start()
