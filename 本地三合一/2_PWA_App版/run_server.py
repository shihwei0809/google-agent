import http.server
import socketserver
import socket

PORT = 8000
Handler = http.server.SimpleHTTPRequestHandler

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

while True:
    try:
        with socketserver.TCPServer(('', PORT), Handler) as httpd:
            ip = get_ip()
            print(f"\n[✅] 伺服器已啟動！")
            print(f"👉 電腦本機請訪問: http://localhost:{PORT}")
            print(f"👉 手機測試請訪問: http://{ip}:{PORT}")
            print(f"\n請確保手機與電腦連線至同一個 Wi-Fi 網路。")
            httpd.serve_forever()
    except OSError:
        PORT += 1
