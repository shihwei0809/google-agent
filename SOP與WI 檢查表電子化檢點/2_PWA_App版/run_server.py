import http.server
import socket
import socketserver
import threading
import time
import webbrowser
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_PORT = 8085


def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def find_available_port(start_port: int) -> int:
    port = start_port
    while port < start_port + 50:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
        port += 1
    return start_port


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)


def main():
    port = find_available_port(DEFAULT_PORT)
    if port != DEFAULT_PORT:
        print(f"⚠️ 預設 Port {DEFAULT_PORT} 已被佔用，已自動切換至可用 Port: {port}")

    local_ip = get_local_ip()
    url_local = f"http://localhost:{port}"
    url_lan = f"http://{local_ip}:{port}"
    print("=" * 60)
    print("🚀 SOP / WI 電子化檢點系統 (PWA App 本機伺服器) 已啟動")
    print(f"💻 本機網址：{url_local}")
    print(f"📱 區網平板/手機連線網址：{url_lan}")
    print("=" * 60)

    threading.Timer(1.5, lambda: webbrowser.open(url_local)).start()
    with socketserver.TCPServer(("0.0.0.0", port), QuietHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n已停止伺服器。")


if __name__ == "__main__":
    main()
