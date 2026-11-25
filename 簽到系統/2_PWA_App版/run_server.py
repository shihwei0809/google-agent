import http.server
import socket
import socketserver
import sys
import webbrowser
import threading
import time

DEFAULT_PORT = 8080


def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def find_available_port(start_port: int = DEFAULT_PORT, max_tries: int = 50) -> int:
    for port in range(start_port, start_port + max_tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise RuntimeError("找不到可用的 Port")


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()


def main():
    req_port = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT
    port = find_available_port(req_port)
    if port != req_port:
        print(f"[提醒] 預設 Port {req_port} 已被佔用，已自動切換至可用 Port: {port}")

    local_ip = get_local_ip()
    print("=" * 52)
    print("  企業活動簽到系統 - PWA 本機測試伺服器")
    print("=" * 52)
    print(f"  本機網址: http://localhost:{port}")
    print(f"  區網網址: http://{local_ip}:{port}  (手機同 Wi-Fi 可掃描/開啟)")
    print("  按 Ctrl+C 停止服務")
    print("=" * 52)

    def open_browser():
        time.sleep(1.2)
        webbrowser.open(f"http://localhost:{port}")

    threading.Thread(target=open_browser, daemon=True).start()

    with socketserver.TCPServer(("0.0.0.0", port), QuietHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n伺服器已停止。")


if __name__ == "__main__":
    main()
