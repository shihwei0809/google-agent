import http.server
import socketserver
import socket
import os
import webbrowser

PORT = 8002

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def find_available_port(start_port: int, max_attempts: int = 50) -> int:
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", port))
                return port
            except OSError:
                continue
    return start_port

class Handler(http.server.SimpleHTTPRequestHandler):
    pass

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    actual_port = find_available_port(PORT)
    ip = get_local_ip()
    
    print("==================================================")
    if actual_port != PORT:
        print(f"預設 Port {PORT} 已被佔用，已自動切換至可用 Port: {actual_port}")
        
    print(f"黑鐵桶 PWA 本機測試伺服器啟動中...")
    print(f"本機網址: http://localhost:{actual_port}")
    print(f"手機網址: http://{ip}:{actual_port}  <-- 請將手機連上同一個 Wi-Fi 後輸入此網址")
    print("==================================================")
    
    webbrowser.open(f"http://localhost:{actual_port}")
    
    with socketserver.TCPServer(("0.0.0.0", actual_port), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n伺服器已關閉")

if __name__ == "__main__":
    main()
