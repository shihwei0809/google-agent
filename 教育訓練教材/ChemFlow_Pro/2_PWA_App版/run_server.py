import http.server
import socketserver
import socket
import os

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

PORT = find_available_port(8000)
IP = get_local_ip()

Handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print("========================================")
    print(f"ChemFlow Pro 伺服器啟動成功！")
    print(f"本機測試網址: http://localhost:{PORT}")
    print(f"區網分享網址: http://{IP}:{PORT}")
    print("========================================")
    print("請使用瀏覽器開啟上述網址。若要停止伺服器，請按 Ctrl+C")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n伺服器已關閉。")
