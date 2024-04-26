import socket
import threading
from datetime import datetime
import os
import base64

class ChatServer:
    def __init__(self):
        self.clients = {}
        self.client_count = 0
        self.server_socket = None
        self.running = False
        self.log_filename = None
        self.host = None
        self.port = None

    def start(self):
        self.host = "127.0.0.1"
        self.port = 12345

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"服务器已启动，监听 {self.host}:{self.port}")

        self.initialize_logging()
        self.running = True

        while self.running:
            try:
                client_socket, client_address = self.server_socket.accept()
                if self.running:
                    self.client_count += 1
                    ip, port = client_address
                    print(f"New user connected: {ip}:{port}")
                    threading.Thread(target=self.handle_client, args=(client_socket, ip, port)).start()
                else:
                    if isinstance(client_socket, socket.socket):
                        client_socket.close()
            except OSError as e:
                if self.running:
                    print(f"Server stopped accepting new client connections: {e}")
                break

        for client_socket in self.clients.values():
            if isinstance(client_socket, socket.socket):
                client_socket.close()

        if isinstance(self.server_socket, socket.socket):
            self.server_socket.close()


    def stop(self):
        self.running = False

        for client_socket in self.clients.keys():
            try:
                client_socket.close()
            except AttributeError:
                pass

        if isinstance(self.server_socket, socket.socket):
            self.server_socket.close()

        self.log("服务器已停止")


    
    def handle_client(self, client_socket, ip, port):
        username = f"{ip}:{port}"  
        self.clients[client_socket] = username

        self.broadcast(base64.b64encode(f"新用户加入聊天室：{username}".encode()).decode().encode())

        try:
            while True:
                encrypted_message = client_socket.recv(1024).decode()
                if not encrypted_message:
                    break
                message = base64.b64decode(encrypted_message.encode()).decode()
                print(f"收到来自 {username} 的消息：{message}")
                self.log_message(f"收到来自 {username} 的消息：{message}")
                self.process_message(client_socket, username, message)
        except ConnectionResetError:
            print(f"客户端 {username} 异常断开连接")
        finally:
            if client_socket in self.clients:
                del self.clients[client_socket]
            client_socket.close()

            self.broadcast(base64.b64encode(f"用户离开聊天室：{username}".encode()).decode().encode())
            return 

    def process_message(self, client_socket, username, message):
        if message.startswith("/ip"):
            ip_port_msg = f"您的IP地址和端口为：{username}"
            client_socket.send(base64.b64encode(ip_port_msg.encode()).decode().encode())
        elif message.startswith("/stop"):
            parts = message.split(" ")
            if len(parts) >= 2:
                password = parts[1]
                self.prompt_password_and_stop(client_socket, password)
            else:
                client_socket.send(base64.b64encode("密码错误，请重新输入。".encode()).decode().encode())
        elif message.startswith("/list"):
            self.send_user_list(client_socket)
        elif message.startswith("/kick"):
            self.prompt_password_and_kick(client_socket, message)
        elif message.startswith("/history"):
            self.send_history_disabled_message(client_socket)  # 添加这一行
        else:
            self.broadcast(base64.b64encode(f"{username}: {message}".encode()).decode().encode(), exclude_client=client_socket)

    def send_user_list(self, client_socket):
        user_list = "\n".join(self.clients.values())
        client_socket.send(base64.b64encode(f"在线用户列表：\n{user_list}".encode()).decode().encode())

    def send_chat_history(self, client_socket):
        try:
            with open(self.log_filename, "r") as f:
                chat_history = f.read()
            client_socket.send(chat_history.encode())
        except FileNotFoundError:
            client_socket.send("聊天记录不存在。".encode())

    def broadcast(self, message, exclude_client=None):
        for client_socket in list(self.clients.keys()):
            if client_socket != exclude_client:
                try:
                    client_socket.send(message)
                except ConnectionResetError:
                    pass

    def initialize_logging(self):
        logs_dir = "logs"
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)

        now = datetime.now()
        self.log_filename = os.path.join(logs_dir, f"server_log_{now.strftime('%Y%m%d_%H%M%S')}.txt")
        self.log("服务器已启动")

    def log_message(self, message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        log_message = f"{timestamp} - {message}"
        print(log_message)
        with open(self.log_filename, "a") as logfile:
            logfile.write(log_message + "\n")

    def log(self, message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        log_message = f"{timestamp} - {message}"
        print(log_message)
        with open(self.log_filename, "a") as logfile:
            logfile.write(log_message + "\n")

    def prompt_password_and_stop(self, client_socket, password):
        if password == "1234":
            self.stop()
            client_socket.send(base64.b64encode("服务器已停止。".encode()).decode().encode())
            self.log("管理员停止了服务器")
        else:
            client_socket.send(base64.b64encode("密码错误，请重新输入。".encode()).decode().encode())

    def prompt_password_and_kick(self, client_socket, message):
        parts = message.split(" ")
        if len(parts) >= 4 and parts[-1] == "1234":
            target_username = parts[1]
            kick_reason = " ".join(parts[2:-1])
            for sock, username in list(self.clients.items()):
                if username == target_username:
                    sock.send(base64.b64encode(f"您已被管理员踢出服务器，原因：{kick_reason}".encode()).decode().encode())
                    del self.clients[sock]
                    sock.close()
                    print(f"用户 {target_username} 已被踢出服务器。")
                    self.log(f"管理员踢出用户 {target_username}，原因：{kick_reason}")
                    return
                    break
            client_socket.send(base64.b64encode(f"未找到用户 {target_username}。".encode()).decode().encode())
        else:
            client_socket.send(base64.b64encode("命令格式错误或密码错误。".encode()).decode().encode())

    def send_history_disabled_message(self, client_socket):  # 添加该方法
        client_socket.send(base64.b64encode("历史消息功能已禁用。".encode()).decode().encode())

def main():
    server = ChatServer()
    server.start()

if __name__ == "__main__":
    main()
