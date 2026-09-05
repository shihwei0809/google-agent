import os
import sys
import socket
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def find_available_port(start_port=8080):
    port = start_port
    while port < 65535:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
            port += 1
    return start_port

def main():
    # Set console encoding
    if sys.platform == "win32":
        os.system("chcp 65001 >nul")
        
    title = os.path.basename(os.getcwd())
    port = find_available_port(8085)
    local_ip = get_local_ip()
    
    print("=" * 60)
    print(f"   🚀 {title} - PWA 本機測試伺服器")
    print("=" * 60)
    print(f"[✓] 電腦本機網址:   http://localhost:{port}")
    print(f"[✓] 手機/PDA網址:   http://{local_ip}:{port}")
    print("-" * 60)
    print("【📱 如何安裝為桌面 / 手機 App】:")
    print("  1. 電腦瀏覽器 (Chrome/Edge): 點擊網址列右側的「安裝」圖示")
    print("  2. Android 手機: 點擊頁面上方「立即安裝」或「新增至主畫面」")
    print("  3. iPhone (Safari): 點擊底部「分享」按鈕 ->「加入主畫面」")
    print("=" * 60)
    print(f"正在為您開啟瀏覽器: http://localhost:{port} ...\n")
    
    webbrowser.open(f"http://localhost:{port}")
    
    print("伺服器運行中 (按 Ctrl+C 可停止)...")
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n伺服器已停止。")

if __name__ == '__main__':
    main()