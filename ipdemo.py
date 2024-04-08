import requests

def get_ip_info(ip_address):
    url = f"http://ip-api.com/json/{ip_address}"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print("Error:", response.status_code)
        return None

def main():
    ip_address = input("请输入要查询的IP地址：")
    ip_info = get_ip_info(ip_address)
    
    if ip_info and ip_info["status"] == "success":
        print("查询结果：")
        print("IP地址:", ip_info["query"])
        print("国家:", ip_info["country"])
        print("地区:", ip_info["regionName"])
        print("城市:", ip_info["city"])
        print("经纬度:", ip_info["lat"], ",", ip_info["lon"])
    else:
        print("查询失败，请检查输入的IP地址是否正确。")

    input("按任意键退出程序")

if __name__ == "__main__":
    main()
