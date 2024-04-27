import socket

def dns_lookup(domain_name, dns_server):
    # 创建一个UDP套接字
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # DNS服务器地址和端口
    server_address = (dns_server, 53)
    
    try:
        # 构造DNS查询报文
        query_message = bytearray()
        query_message.extend(b'\xAA\xAA')  # 标识字段
        query_message.extend(b'\x01\x00')  # 查询报文格式：标准查询
        query_message.extend(b'\x00\x01')  # 查询数：1个
        query_message.extend(b'\x00\x00')  # 回答数：0个
        query_message.extend(b'\x00\x00')  # 权威资源记录数：0个
        query_message.extend(b'\x00\x00')  # 额外资源记录数：0个
        # 分割域名并编码
        for part in domain_name.split('.'):
            query_message.append(len(part))
            query_message.extend(part.encode())
        query_message.extend(b'\x00')  # 域名结束
        query_message.extend(b'\x00\x01')  # 查询类型：A记录
        query_message.extend(b'\x00\x01')  # 查询类：IN（Internet）
        
        # 发送DNS查询请求
        sock.sendto(query_message, server_address)
        
        # 接收DNS响应
        response, _ = sock.recvfrom(4096)
        
        # 解析响应获取IP地址
        ip_address = '.'.join(str(byte) for byte in response[-4:])
        
        return ip_address
    finally:
        sock.close()

if __name__ == "__main__":
    domain = input("请输入域名：")
    dns_server = "1.1.1.1"  # 这里是你的DNS服务器地址
    ip = dns_lookup(domain, dns_server)
    print(f"{domain} 的IP地址是：{ip}")
    a = input("按回车键退出程序")
