import socket
import threading
import sys

class ChatClient:
    def __init__(self):
        self.server_ip = "191.96.240.164"
        self.server_port = 19384
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = False

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
                message = self.client_socket.recv(1024).decode()
                if not message:
                    print("与服务器的连接已断开。")
                    self.running = False
                    break  # 服务器关闭连接时退出循环
                print(message)
            except ConnectionResetError:
                print("与服务器的连接意外断开。")
                self.running = False
                break
            except ConnectionAbortedError:  # 忽略该错误
                pass

    def send_message(self, message):
        encrypted_message = self.encrypt_message(message)
        try:
            self.client_socket.send(encrypted_message.encode())
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
        encrypted_message = ""
        for char in message:
            if char.isdigit():
                encrypted_message += str((int(char) + 1) % 10)  # 将数字加1并取余，实现简单替换
            elif char.isalpha():
                if char.islower():
                    encrypted_message += chr((ord(char) - ord('a') + 1) % 26 + ord('a'))  # 小写字母加1并取余，实现简单替换
                else:
                    encrypted_message += chr((ord(char) - ord('A') + 1) % 26 + ord('A'))  # 大写字母加1并取余，实现简单替换
            else:
                encrypted_message += char  # 其他字符保持不变
        return encrypted_message

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
