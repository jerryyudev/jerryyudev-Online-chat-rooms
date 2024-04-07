import socket
import threading
import sys
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad

class ChatClient:
    def __init__(self):
        self.server_ip = "191.96.240.164"
        self.server_port = 19384
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = False
        self.key = get_random_bytes(16)  # 生成16字节的随机密钥

    def connect_to_server(self):
        try:
            self.client_socket.connect((self.server_ip, self.server_port))
            self.running = True
            threading.Thread(target=self.receive_messages).start()
            print("连接到服务器成功！")
        except ConnectionRefusedError:
            print("连接被拒绝。服务器可能未启动或者无法连接。")

    def receive_messages(self):
        while self.running:
            try:
                encrypted_message = self.client_socket.recv(1024)
                if not encrypted_message:
                    print("与服务器的连接已断开。")
                    self.running = False
                    break  # 服务器关闭连接时退出循环
                decrypted_message = self.decrypt_message(encrypted_message)
                # Filter out the port from server messages
                if "新用户加入聊天室：" in decrypted_message:
                    decrypted_message = decrypted_message.split(":")[0]  # Remove the port part
                print(decrypted_message)
            except ConnectionResetError:
                print("与服务器的连接意外断开。")
                self.running = False
                break

    def send_message(self, message):
        try:
            encrypted_message = self.encrypt_message(message)
            self.client_socket.send(encrypted_message)
        except ConnectionAbortedError:
            print("与服务器的连接意外断开。")
            self.running = False

    def reconnect(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect_to_server()

    def leave(self):
        self.running = False
        self.client_socket.close()
        print("已离开聊天室。")

    def encrypt_message(self, message):
        cipher = AES.new(self.key, AES.MODE_CBC)
        ct_bytes = cipher.encrypt(pad(message.encode(), AES.block_size))
        iv = cipher.iv
        return iv + ct_bytes

    def decrypt_message(self, encrypted_message):
        iv = encrypted_message[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv=iv)
        decrypted_message = unpad(cipher.decrypt(encrypted_message[AES.block_size:]), AES.block_size)
        return decrypted_message.decode('utf-8')

def main():
    client = ChatClient()
    client.connect_to_server()
    while client.running:
        message = input()
        if message == "/leave":
            client.leave()
            sys.exit()
        elif message == "/reconnect":
            client.reconnect()
        else:
            client.send_message(message)

if __name__ == "__main__":
    main()
