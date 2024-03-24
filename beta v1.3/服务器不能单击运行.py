import os
import socket
import threading
import datetime
from concurrent.futures import ThreadPoolExecutor

class ChatServer:
    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = "127.0.0.1"
        self.port = 12345
        self.clients = {}
        self.running = False
        self.log_filename = None
        self.executor = ThreadPoolExecutor(max_workers=10)  # 使用线程池管理客户端连接

    def start(self):
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True
            self.create_log_file()
            print(f"服务器已启动，监听 {self.host}:{self.port}")
            threading.Thread(target=self.accept_clients).start()
        except Exception as e:
            print(f"启动服务器失败: {e}")

    def remove_client(self, client_socket):  
        # 从self.clients中移除指定的client_socket  
        if client_socket in self.clients:  
            del self.clients[client_socket]  
        # 关闭client_socket连接  
        client_socket.close()

    def accept_clients(self):
        while self.running:
            try:
                client_socket, client_address = self.server_socket.accept()
                print(f"连接来自 {client_address}")
                threading.Thread(target=self.handle_client, args=(client_socket, client_address)).start()
                self.broadcast_message(f"用户 {client_address[0]} 已加入服务器")

            except OSError as e:
                if self.running:
                    print(f"服务器已停止接受新的客户端连接：{e}")
                break

    def handle_client(self, client_socket, client_address):
        username = client_address[0]
        self.clients[client_socket] = username
        try:
            while True:
                message = client_socket.recv(1024).decode()
                if not message:
                    break  # 客户端断开连接时退出循环
                print(f"收到来自 {username} 的消息：{message}")
                self.log_message(f"收到来自 {username} 的消息：{message}")  # 记录用户消息
                if message.startswith("/stop"):
                    parts = message.split(" ")
                    if len(parts) >= 2:
                        password = parts[1]
                        self.prompt_password_and_stop(client_socket, password)
                        break
                    else:
                        client_socket.send("密码错误，请重新输入。".encode())
                elif message.startswith("/list"):
                    self.send_user_list(client_socket)
                    self.output_user_list()
                elif message.startswith("/kick"):
                    self.prompt_password_and_kick(client_socket, message)
                elif message.startswith("/history"):
                    self.send_chat_history(client_socket)
                else:
                    
                    self.broadcast_message(f"{username}: {message}", sender=client_socket)

        except ConnectionResetError:
            print(f"客户端 {username} 异常断开连接")
        finally:
            if client_socket in self.clients:
                del self.clients[client_socket]
            client_socket.close()

    def prompt_password_and_stop(self, client_socket, password):
        if password == "1234":
            self.stop()
            client_socket.send("服务器已停止。".encode())
            self.log_message("管理员停止了服务器")  # 记录管理员操作
        else:
            client_socket.send("密码错误，请重新输入。".encode())
            # 在这里可以添加逻辑，等待客户端发送新密码

    def output_user_list(self):
        print("在线用户列表：")
        for user in self.clients.values():
            print(user)

    def broadcast_message(self, message, sender=None):  
        # 将消息写入日志文件  
        self.log_message(message)  
        
        # 广播消息给所有客户端，除了发送者  
        for client_socket, username in list(self.clients.items()):  
            if client_socket != sender:  # 排除发送者  
                try:  
                    client_socket.send(message.encode())  
                except (ConnectionResetError, socket.error) as e:  
                    print(f"与客户端 {username} 的连接意外断开：{e}")  
                    self.remove_client(client_socket)


    def log_message(self, message):
        with open(self.log_filename, "a") as f:
            f.write(f"{datetime.datetime.now()} - {message}\n")

    def stop(self):
        self.running = False
        self.server_socket.close()

    def send_user_list(self, client_socket):
        user_list = "在线用户：\n"
        for user in self.clients.values():
            user_list += f"- {user}\n"
        client_socket.send(user_list.encode())

    def prompt_password_and_kick(self, client_socket, message):
        parts = message.split(" ")
        if len(parts) >= 4 and parts[-1] == "1234":  # Check if password is correct
            target_username = parts[1]
            kick_reason = " ".join(parts[2:-1])
            for sock, username in list(self.clients.items()):
                if username == target_username:
                    sock.send(f"您已被管理员踢出服务器，原因：{kick_reason}".encode())
                    del self.clients[sock]
                    sock.close()
                    print(f"用户 {target_username} 已被踢出服务器。")
                    self.log_message(f"管理员踢出用户 {target_username}，原因：{kick_reason}")  # 记录管理员操作
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

    def create_log_file(self):
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_filename = os.path.join(log_dir, f"server_log_{timestamp}.txt")

def main():
    server = ChatServer()
    server.start()

if __name__ == "__main__":
    main()
