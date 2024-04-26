import socket
import threading
import sys
import base64
import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox

class ChatClient:
    def __init__(self):
        self.server_ip = "cn-hk-bgp-4.of-7af93c01.shop"
        self.server_port = 19384
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = False

        self.gui = tk.Tk()
        self.gui.title("Chat Room")
        self.chat_history = scrolledtext.ScrolledText(self.gui, width=40, height=20)
        self.chat_history.pack(padx=10, pady=10)
        self.message_entry = tk.Entry(self.gui, width=40)
        self.message_entry.pack(padx=10, pady=5)
        self.send_button = tk.Button(self.gui, text="Send", command=self.send_message)
        self.send_button.pack(padx=10, pady=5)

    def connect_to_server(self):
        try:
            self.client_socket.connect((self.server_ip, self.server_port))
            self.running = True
            threading.Thread(target=self.receive_messages).start()
            print("连接到服务器成功！")
            self.gui.protocol("WM_DELETE_WINDOW", self.leave)
            self.gui.mainloop()
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
                self.chat_history.insert(tk.END, message + '\n')
            except ConnectionResetError:
                print("与服务器的连接意外断开。")
                self.running = False
                break
            except ConnectionAbortedError:  # 忽略该错误
                pass

    def send_message(self):
        message = self.message_entry.get()
        if message:
            try:
                encrypted_message = base64.b64encode(message.encode()).decode()
                self.client_socket.send(encrypted_message.encode())
                self.chat_history.insert(tk.END, f"Me: {message}\n")  # 将自己发送的消息添加到聊天历史
                self.message_entry.delete(0, tk.END)
            except ConnectionAbortedError:
                print("与服务器的连接意外断开。")
                self.running = False

    def leave(self):
        self.running = False
        self.client_socket.close()
        self.gui.destroy()
        print("已离开聊天室。")
        sys.exit()

def main():
    client = ChatClient()
    client.connect_to_server()

if __name__ == "__main__":
    main()
