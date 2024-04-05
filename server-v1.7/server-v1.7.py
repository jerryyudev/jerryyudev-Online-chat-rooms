import socket
import threading
from datetime import datetime
import os

class ChatServer:
    def __init__(self):
        self.clients = {}
        self.client_count = 0
        self.server_socket = None
        self.running = False
        self.log_filename = None

    def start(self):
        host = "127.0.0.1"
        port = 12345

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((host, port))
        self.server_socket.listen(5)
        print(f"服务器已启动，监听 {host}:{port}")

        self.initialize_logging()
        self.running = True

        while self.running:
            try:
                client_socket, client_address = self.server_socket.accept()
                if self.running:  # Only accept new connections when the server is running
                    self.client_count += 1
                    ip, port = client_address
                    print(f"New user connected: {ip}:{port}")
                    threading.Thread(target=self.handle_client, args=(client_socket, client_address)).start()
                else:
                    if isinstance(client_socket, socket.socket):  # Check if client_socket is a socket object
                        client_socket.close()  # Close the socket if it's still valid
            except OSError as e:
                if self.running:
                    print(f"Server stopped accepting new client connections: {e}")
                break

        # Close all client sockets
        for client_socket in self.clients.values():
            if isinstance(client_socket, socket.socket):  # Check if client_socket is a socket object
                client_socket.close()

        # Close the server socket
        if isinstance(self.server_socket, socket.socket):  # Check if self.server_socket is a socket object
            self.server_socket.close()


    def stop(self):
        self.running = False

        # 关闭所有客户端套接字
        for client_socket in self.clients.keys():
            try:
                client_socket.close()
            except AttributeError:
                pass

        # 关闭服务器套接字
        if isinstance(self.server_socket, socket.socket):
            self.server_socket.close()

        self.log("服务器已停止")


    
    def handle_client(self, client_socket, client_address):
        ip, port = client_address  # 获取客户端的IP地址和端口
        username = f"{ip}:{port}"
        self.clients[client_socket] = username

        # 向所有客户端广播新用户加入的消息
        self.broadcast(f"新用户加入聊天室：{username}")

        try:
            while True:
                message = client_socket.recv(1024).decode()
                if not message:
                    break
                print(f"收到来自 {username} 的消息：{message}")
                self.log_message(f"收到来自 {username} 的消息：{message}")
                self.process_message(client_socket, username, message)
        except ConnectionResetError:
            print(f"客户端 {username} 异常断开连接")
        finally:
            if client_socket in self.clients:
                del self.clients[client_socket]
            client_socket.close()

            # 向所有客户端广播用户离开的消息
            self.broadcast(f"用户离开聊天室：{username}")
            return  # 添加此行，确保在异常发生时直接退出循环

    def process_message(self, client_socket, username, message):
        if message.startswith("/ip"):
            ip_port_msg = f"您的IP地址和端口为：{client_socket.getpeername()[0]}:{client_socket.getpeername()[1]}"
            client_socket.send(ip_port_msg.encode())
        elif message.startswith("/stop"):
            parts = message.split(" ")
            if len(parts) >= 2:
                password = parts[1]
                self.prompt_password_and_stop(client_socket, password)
            else:
                client_socket.send("密码错误，请重新输入。".encode())
        elif message.startswith("/list"):
            self.send_user_list(client_socket)
        elif message.startswith("/kick"):
            self.prompt_password_and_kick(client_socket, message)
        elif message.startswith("/history"):
            self.send_chat_history(client_socket)
        else:
            self.broadcast(f"{username}: {message}", exclude_client=client_socket)

    def send_user_list(self, client_socket):
        user_list = "\n".join(self.clients.values())
        client_socket.send(f"在线用户列表：\n{user_list}".encode())

    def broadcast(self, message, exclude_client=None):
        for client_socket in list(self.clients.keys()):
            if client_socket != exclude_client:
                try:
                    client_socket.send(message.encode())
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
            client_socket.send("服务器已停止。".encode())
            self.log("管理员停止了服务器")
        else:
            client_socket.send("密码错误，请重新输入。".encode())

    def prompt_password_and_kick(self, client_socket, message):
        parts = message.split(" ")
        if len(parts) >= 4 and parts[-1] == "1234":
            target_username = parts[1]
            kick_reason = " ".join(parts[2:-1])
            for sock, username in list(self.clients.items()):
                if username == target_username:
                    sock.send(f"您已被管理员踢出服务器，原因：{kick_reason}".encode())
                    del self.clients[sock]
                    sock.close()
                    print(f"用户 {target_username} 已被踢出服务器。")
                    self.log(f"管理员踢出用户 {target_username}，原因：{kick_reason}")
                    return
                    break
            client_socket.send(f"未找到用户 {target_username}。".encode())
        else:
            client_socket.send("命令格式错误或密码错误。".encode())

    def send_chat_history(self, client_socket):
        try:
            with open(self.log_filename, "r") as f:
                chat_history = f.read()
            client_socket.send(chat_history.encode())
        except FileNotFoundError:
            client_socket.send("聊天记录不存在。".encode())

def main():
    # 创建 ChatServer 实例
    server = ChatServer()
    server.start()

if __name__ == "__main__":
    main()
