import socket
import threading

class ChatClient:
    def __init__(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = False

    def connect(self, host, port):
        try:
            self.client_socket.connect((host, port))
            self.running = True
            threading.Thread(target=self.receive_messages).start()
            print("成功连接到服务器")
        except Exception as e:
            print(f"连接失败: {e}")

    def receive_messages(self):
        while self.running:
            try:
                message = self.client_socket.recv(1024).decode()
                if message:
                    print(message)
            except ConnectionResetError:
                print("与服务器的连接已断开")
                self.running = False
                break

    def send_message(self, message):
        try:
            self.client_socket.send(message.encode())
        except ConnectionResetError:
            print("与服务器的连接已断开")

    def stop(self):
        self.running = False
        self.client_socket.close()

def main():
    client = ChatClient()
    host = "127.0.0.1"
    port = 12345

    client.connect(host, port)

    while client.running:
        message = input()
        client.send_message(message)

if __name__ == "__main__":
    main()
