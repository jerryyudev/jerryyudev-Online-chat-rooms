import socket
import threading

class ChatClient:
    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.is_connected = False

    def connect(self, server_host="127.0.0.1"):  # 添加默认的服务器主机名
        host = server_host
        port = 12345

        try:
            self.server_socket.connect((host, port))
            self.is_connected = True
            print("成功连接到服务器")
            threading.Thread(target=self.receive_messages).start()
        except Exception as e:
            print(f"连接失败: {e}")

    def receive_messages(self):
        while self.is_connected:
            try:
                message = self.server_socket.recv(1024).decode()
                print("收到服务器消息：", message)
            except Exception as e:
                print(f"接收消息时出错: {e}")
                break

    def send_message(self, message):
        try:
            self.server_socket.send(message.encode())
        except Exception as e:
            print(f"发送消息时出错: {e}")

def main():
    client = ChatClient()
    client.connect()  # 不传递参数，使用默认的服务器主机名 "127.0.0.1"

    while client.is_connected:
        try:
            message = input("输入消息：")
            client.send_message(message)
        except KeyboardInterrupt:
            print("键盘中断，关闭客户端连接")
            client.is_connected = False
            client.server_socket.close()
            break

if __name__ == "__main__":
    main()
