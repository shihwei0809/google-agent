# -*- coding: utf-8 -*-
import os
import sys
import socket
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler

class UTF8Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        if self.path.endswith(".html") or self.path == "/" or self.path == "":
            self.send_header("Content-Type", "text/html; charset=utf-8")
        elif self.path.endswith(".json"):
            self.send_header("Content-Type", "application/json; charset=utf-8")
        elif self.path.endswith(".js"):
            self.send_header("Content-Type", "application/javascript; charset=utf-8")
        super().end_headers()

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def find_available_port(start_port: int = 8088, max_attempts: int = 50) -> int:
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", port))
                return port
            except OSError:
                print(f"[提示] 預設 Port {port} 已被佔用，正在嘗試下一個可用 Port...")
                continue
    return start_port

def main():
    if sys.platform == "win32":
        os.system("chcp 65001 >nul")
        
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    start_port = 8088
    port = find_available_port(start_port)
    local_ip = get_local_ip()
    
    print("=" * 65)
    print("   🛢️ IPA 生產排程與進耗存整合系統 v3.1 - PWA 獨立 App 測試伺服器")
    print("=" * 65)
    if port != start_port:
        print(f"[切換提示] 預設 Port {start_port} 已被佔用，已自動切換至可用 Port: {port}")
    print(f"[✓] 電腦本機網址:   http://localhost:{port}")
    print(f"[✓] 手機/區域網路:  http://{local_ip}:{port}")
    print("-" * 65)
    print("【📱 三端 PWA 獨立 App 安裝指引】:")
    print("  1. 電腦 (Chrome / Edge): 點擊網址列右側「安裝」或頂部橫幅「立即安裝」")
    print("  2. Android 手機 / 平板: 點擊頁面上方「立即安裝」或選單「新增至主畫面」")
    print("  3. iPhone / iPad (Safari): 點擊底部「分享」圖示 -> 選擇「加入主畫面」")
    print("=" * 65)
    print(f"正在為您開啟瀏覽器: http://localhost:{port} ...\n")
    
    webbrowser.open(f"http://localhost:{port}")
    
    print("伺服器持續運作中 (按 Ctrl+C 可停止伺服器)...")
    server = HTTPServer(('0.0.0.0', port), UTF8Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n伺服器已正常停止。")

if __name__ == '__main__':
    main()
