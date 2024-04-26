import socket
import threading
import sys
import base64

class ChatClient:
    def __init__(self, proxy_host=None, proxy_port=None):
        self.server_ip = "cn-hk-bgp-4.of-7af93c01.shop"
        self.server_port = 19384
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = False

    def connect_to_server(self):
        try:
            if self.proxy_host and self.proxy_port:
                self.client_socket.connect((self.proxy_host, self.proxy_port))
                # Send CONNECT request to proxy server
                connect_request = f"CONNECT {self.server_ip}:{self.server_port} HTTP/1.1\r\nHost: {self.server_ip}:{self.server_port}\r\n\r\n"
                self.client_socket.sendall(connect_request.encode())
                response = self.client_socket.recv(1024).decode()
                if "200 Connection established" not in response:
                    print("连接失败：", response)
                    return
            else:
                self.client_socket.connect((self.server_ip, self.server_port))

            self.running = True
            threading.Thread(target=self.receive_messages).start()
            print("连接到服务器成功！")
        except ConnectionRefusedError:
            print("连接被拒绝。服务器可能未启动或者无法连接。")

    def receive_messages(self):
        while self.running:
            try:
                encrypted_message = self.client_socket.recv(1024).decode()
                if not encrypted_message:
                    print("与服务器的连接已断开。")
                    self.running = False
                    break  # 服务器关闭连接时退出循环
                message = base64.b64decode(encrypted_message.encode()).decode()
                print(message)
            except ConnectionResetError:
                print("与服务器的连接意外断开。")
                self.running = False
                break
            except ConnectionAbortedError:  # 忽略该错误
                pass

    def send_message(self, message):
        try:
            encrypted_message = base64.b64encode(message.encode()).decode()
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

def main():
    proxy_host = "127.0.0.1"  # 设置HTTP代理服务器地址
    proxy_port = 10809  # 设置HTTP代理服务器端口
    client = ChatClient(proxy_host, proxy_port)
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
