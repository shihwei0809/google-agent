# run_server.py - 智慧本機 Web 伺服器 (支援本機 IP 顯示與自動 Port 佔用切換)
import os
import sys
import socket
import webbrowser
import threading
import time
from http.server import SimpleHTTPRequestHandler, HTTPServer

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def find_available_port(start_port=8080, max_attempts=20):
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
    return start_port

class CustomHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # 允許跨域與 Service Worker 作用域控制
        self.send_header('Service-Worker-Allowed', '/')
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

def run_server():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)

    target_port = 8080
    available_port = find_available_port(target_port)
    local_ip = get_local_ip()

    if available_port != target_port:
        print(f"⚠️ 預設 Port {target_port} 已被佔用，已自動切換至可用 Port: {available_port}")

    server_address = ('0.0.0.0', available_port)
    httpd = HTTPServer(server_address, CustomHandler)

    local_url = f"http://localhost:{available_port}/index.html"
    lan_url = f"http://{local_ip}:{available_port}/index.html"

    print("=" * 60)
    print("🚀 三合一單與 COA 四重核對 PWA - 本機伺服器啟動成功！")
    print(f"📌 本機瀏覽網址: {local_url}")
    print(f"🌐 區網手機連線: {lan_url}")
    print("💡 提示：若手機需使用相機功能，請配合 Ngrok / Cloudflare Tunnel 使用 HTTPS！")
    print("=" * 60)

    # 延遲 2 秒後自動開啟瀏覽器
    def open_browser():
        time.sleep(1.5)
        webbrowser.open(local_url)

    threading.Thread(target=open_browser, daemon=True).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 伺服器已安全停止。")
        httpd.server_close()

if __name__ == '__main__':
    run_server()
