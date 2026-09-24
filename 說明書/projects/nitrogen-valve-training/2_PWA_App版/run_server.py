import http.server
import socketserver
import socket
import os

PORT = 8000
DIRECTORY = "."

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

ip = get_ip()

# Port Fallback
while True:
    try:
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            print(f"\n✅ 伺服器啟動成功！")
            print(f"👉 本機測試網址: http://localhost:{PORT}")
            print(f"👉 手機測試網址: http://{ip}:{PORT} (請確保手機與電腦在同一 WiFi 下)\n")
            httpd.serve_forever()
    except OSError as e:
        if e.errno == 10048:
            print(f"⚠️ Port {PORT} 已被佔用，自動嘗試 {PORT+1}...")
            PORT += 1
        else:
            raise
