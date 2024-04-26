import requests

def test_proxy(proxy):
    try:
        response = requests.get("http://httpbin.org/ip", proxies={"http": proxy, "https": proxy}, timeout=5)
        if response.status_code == 200:
            return True
        else:
            return False
    except Exception as e:
        print("Error:", e)
        return False

def main():
    proxies = [
        "http://127.0.0.1:10809",
        "http://127.0.0.1:10809",  # Replace with your proxy addresses
        # Add more proxy addresses as needed
    ]

    for proxy in proxies:
        if test_proxy(proxy):
            print(f"Proxy {proxy} is working")
        else:
            print(f"Proxy {proxy} is not working")

if __name__ == "__main__":
    main()
