# -*- coding: utf-8 -*-
"""
鴻勝化學 QC 看板本機 Web 伺服器
遵循 Rule 6 規範：自動抓取實體 IP、自動 Port 佔用切換
"""
import http.server
import socketserver
import socket
import os
import sys
import webbrowser

sys.stdout.reconfigure(encoding='utf-8')

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def find_available_port(start_port: int = 8010, max_attempts: int = 50) -> int:
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", port))
                return port
            except OSError:
                continue
    return start_port

def run():
    web_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(web_dir)
    
    preferred_port = 8010
    port = find_available_port(preferred_port)
    local_ip = get_local_ip()
    
    Handler = http.server.SimpleHTTPRequestHandler
    Handler.extensions_map.update({
        '.manifest': 'text/cache-manifest',
        '.json': 'application/json',
        '.js': 'application/javascript; charset=utf-8',
        '.html': 'text/html; charset=utf-8',
        '.css': 'text/css; charset=utf-8',
    })
    
    with socketserver.TCPServer(("", port), Handler) as httpd:
        print("=" * 65)
        print("   🧪 鴻勝化學 QC 檢驗即時看板系統 (PWA 雙軌獨立版本)")
        print("=" * 65)
        if port != preferred_port:
            print(f"⚠️ 預設 Port {preferred_port} 已被佔用，已自動切換至可用 Port: {port}")
        print(f"💻 電腦本機網址:  http://localhost:{port}")
        print(f"📱 區域網路手機:  http://{local_ip}:{port}")
        print("-" * 65)
        print("💡 提示：手機連上廠內同個 Wi-Fi，打開上述手機網址即可瀏覽或「安裝為 PWA App」！")
        print("💡 伺服器運作中... 請勿關閉此視窗 (按 Ctrl+C 可停止伺服器)")
        print("=" * 65)
        
        try:
            webbrowser.open(f"http://localhost:{port}")
        except Exception:
            pass
            
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n伺服器已正常停止。")

if __name__ == '__main__':
    run()
