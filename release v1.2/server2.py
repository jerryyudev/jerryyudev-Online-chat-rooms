import socket
import threading
from datetime import datetime
import os

class ChatServer:
    def __init__(self):
        self.clients = {}
        self.usernames = {}
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
            client_socket, client_address = self.server_socket.accept()
            self.client_count += 1
            self.clients[self.client_count] = client_socket

            threading.Thread(target=self.handle_client, args=(client_socket, client_address)).start()

    def stop(self):
        self.running = False
        self.server_socket.close()
        self.log("服务器已停止")

    def handle_client(self, client_socket, client_address):
        username = client_address[0]
        self.usernames[client_socket] = username
        self.log(f"客户端 {username} 已连接")

        while True:
            try:
                message = client_socket.recv(1024).decode().strip()
                self.log(f"收到来自 {username} 的消息：{message}")

                if message == "/stop":
                    self.stop()
                    self.broadcast(f"服务器已停止", exclude_client=client_socket)
                    del self.usernames[client_socket]
                    client_socket.close()
                    break
                elif message == "/list":
                    self.send_user_list(client_socket)
                else:
                    self.broadcast(f"{username}: {message}", exclude_client=client_socket)
            except ConnectionResetError:
                self.log(f"客户端 {username} 异常断开连接")
                if client_socket in self.clients:
                    del self.clients[client_socket]
                del self.usernames[client_socket]
                break

    def send_user_list(self, client_socket):
        user_list = "\n".join(self.usernames.values())
        client_socket.send(f"在线用户列表：\n{user_list}".encode())

    def broadcast(self, message, exclude_client=None):
        for client_socket in list(self.clients.values()):
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

    def log(self, message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        log_message = f"{timestamp} - {message}"
        print(log_message)
        with open(self.log_filename, "a") as logfile:
            logfile.write(log_message + "\n")

def main():
    server = ChatServer()
    server.start()

if __name__ == "__main__":
    main()
