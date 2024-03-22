import socket
import threading

class ChatServer:
    def __init__(self):
        self.clients = {}
        self.messages = []
        self.client_count = 0

    def start(self):
        # 创建一个TCP/IP socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # 获取本地主机地址和端口号
        host = "127.0.0.1"
        port = 12345

        # 绑定地址和端口号
        self.server_socket.bind((host, port))

        # 设置最大连接数，超过后排队
        self.server_socket.listen(5)
        print(f"服务器已启动，监听 {host}:{port}")

        while True:
            # 建立客户端连接
            client_socket, client_address = self.server_socket.accept()
            self.client_count += 1
            self.clients[self.client_count] = client_socket
            print(f"连接来自 {client_address} 的客户端 {self.client_count}")

            # 发送客户端编号
            client_socket.send(f"你是客户端{self.client_count}".encode())

            # 发送新客户端加入消息给所有客户端
            self.broadcast(f"客户端{self.client_count} 加入了聊天室")

            # 为每个客户端创建一个线程来处理消息
            threading.Thread(target=self.handle_client, args=(client_socket, self.client_count)).start()

    def handle_client(self, client_socket, client_id):
        while True:
            # 接收客户端消息
            try:
                message = client_socket.recv(1024).decode()
            except Exception as e:
                print(f"客户端 {client_id} 断开连接")
                del self.clients[client_id]
                self.broadcast(f"客户端{client_id} 退出了聊天室")
                break

            if not message:
                print(f"客户端 {client_id} 断开连接")
                del self.clients[client_id]
                self.broadcast(f"客户端{client_id} 退出了聊天室")
                break

            print(f"客户端 {client_id} 发送的消息：{message}")

            # 将消息发送给其他所有客户端
            self.broadcast(f"客户端{client_id}: {message}", exclude_id=client_id)

    def broadcast(self, message, exclude_id=None):
        for cid, sock in self.clients.items():
            if cid != exclude_id:
                try:
                    sock.send(message.encode())
                except Exception as e:
                    print(f"发送消息给客户端 {cid} 失败: {e}")

def main():
    server = ChatServer()

    # 启动服务器
    server.start()

if __name__ == "__main__":
    main()
