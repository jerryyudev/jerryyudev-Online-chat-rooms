import socket
import threading
import sys

class ChatClient:
    def __init__(self):
        self.server_ip = "127.0.0.1"
        self.server_port = 12345
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
                # Filter out the port from server messages
                if "新用户加入聊天室：" in message:
                    message = message.split(":")[0]  # Remove the port part
                print(message)
            except ConnectionResetError:
                print("与服务器的连接意外断开。")
                self.running = False
                break

    def send_message(self, message):
        try:
            self.client_socket.send(message.encode())
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
