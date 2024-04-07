import socket
import threading
from datetime import datetime
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad

class ChatServer:
    def __init__(self):
        self.clients = {}
        self.client_count = 0
        self.server_socket = None
        self.running = False
        self.host = None
        self.port = None
        self.key = get_random_bytes(16)  # 生成16字节的随机密钥

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
                encrypted_message = client_socket.recv(1024)
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
        # Your message processing logic goes here
        self.broadcast(f"{username}: {message}", exclude_client=client_socket)

    def broadcast(self, message, exclude_client=None):
        for client_socket in list(self.clients.keys()):
            if client_socket != exclude_client:
                try:
                    encrypted_message = self.encrypt_message(message)
                    client_socket.send(encrypted_message)
                except ConnectionResetError:
                    pass

    def encrypt_message(self, message):
        cipher = AES.new(self.key, AES.MODE_CBC)
        ct_bytes = cipher.encrypt(pad(message.encode(), AES.block_size))
        iv = cipher.iv
        return iv + ct_bytes

    def decrypt_message(self, encrypted_message):
        iv = encrypted_message[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv=iv)
        pt = unpad(cipher.decrypt(encrypted_message[AES.block_size:]), AES.block_size)
        return pt.decode('utf-8')

def main():
    # 创建 ChatServer 实例
    server = ChatServer()
    server.start()

if __name__ == "__main__":
    main()
