import socket
import threading
import sys

class ChatServer:
    def __init__(self):
        self.clients = {}
        self.client_count = 0
        self.server_socket = None
        self.running = False
        self.host = None
        self.port = None

    def start(self):
        self.host = "127.0.0.1"
        self.port = 12345

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"服务器已启动，监听 {self.host}:{self.port}")

        self.running = True

        while self.running:
            try:
                client_socket, client_address = self.server_socket.accept()
                if self.running:  # Only accept new connections when the server is running
                    self.client_count += 1
                    ip, port = client_address  # Get both IP and port
                    print(f"New user connected: {ip}:{port}")
                    threading.Thread(target=self.handle_client, args=(client_socket, ip, port)).start()
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

        # Close all client sockets
        for client_socket in self.clients.keys():
            try:
                client_socket.close()
            except AttributeError:
                pass

        # Close the server socket
        if isinstance(self.server_socket, socket.socket):
            self.server_socket.close()

        print("服务器已停止")

    def handle_client(self, client_socket, ip, port):
        username = f"{ip}:{port}"  # Use IP:Port as username
        self.clients[client_socket] = username

        # Broadcast a message to all clients about the new user
        self.broadcast(f"新用户加入聊天室：{username}")

        try:
            while True:
                encrypted_message = client_socket.recv(1024).decode()
                if not encrypted_message:
                    break
                decrypted_message = self.decrypt_message(encrypted_message)
                print(f"收到来自 {username} 的消息：{decrypted_message}")
                self.process_message(client_socket, username, decrypted_message)
        except ConnectionResetError:
            print(f"客户端 {username} 异常断开连接")
        finally:
            if client_socket in self.clients:
                del self.clients[client_socket]
            client_socket.close()

            # Broadcast a message to all clients about the user leaving
            self.broadcast(f"用户离开聊天室：{username}")
            return  # Ensure exiting the loop immediately in case of an exception

    def process_message(self, client_socket, username, message):
        if message.startswith("/ip"):
            ip_port_msg = f"您的IP地址和端口为：{username}"
            if username.startswith("127.0.0.1"):
                ip_port_msg += "（本机ip）"
            client_socket.send(ip_port_msg.encode())
        elif message.startswith("/stop"):
            parts = message.split(" ")
            if len(parts) >= 2:
                password = parts[1]
                if password == "1234":
                    self.stop()
                    client_socket.send("服务器已停止。".encode())
                    print("管理员停止了服务器")
                else:
                    client_socket.send("密码错误，请重新输入。".encode())
            else:
                client_socket.send("命令格式错误。".encode())
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

    def send_chat_history(self, client_socket):
        client_socket.send("聊天记录功能已被停用。".encode())

    def broadcast(self, message, exclude_client=None):
        for client_socket in list(self.clients.keys()):
            if client_socket != exclude_client:
                try:
                    client_socket.send(message.encode())
                except ConnectionResetError:
                    pass

    def decrypt_message(self, encrypted_message):
        decrypted_message = ""
        for char in encrypted_message:
            if char.isdigit():
                decrypted_message += str((int(char) - 1) % 10)  # 将数字减1并取余，实现简单解密
            elif char.isalpha():
                if char.islower():
                    decrypted_message += chr((ord(char) - ord('a') - 1) % 26 + ord('a'))  # 小写字母减1并取余，实现简单解密
                else:
                    decrypted_message += chr((ord(char) - ord('A') - 1) % 26 + ord('A'))  # 大写字母减1并取余，实现简单解密
            else:
                decrypted_message += char  # 其他字符保持不变
        return decrypted_message

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

def main():
    # 创建 ChatServer 实例
    server = ChatServer()
    server.start()

if __name__ == "__main__":
    main()
