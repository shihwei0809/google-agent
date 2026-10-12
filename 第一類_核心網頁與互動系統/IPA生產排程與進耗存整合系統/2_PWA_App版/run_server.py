import http.server
import socketserver
import socket
import os
import sys

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def start_server(port=8002):
    Handler = http.server.SimpleHTTPRequestHandler
    
    while port < 8020:
        try:
            with socketserver.TCPServer(("", port), Handler) as httpd:
                ip = get_ip()
                print(f"🚀 IPA PWA Server is running!")
                print(f"👉 Local: http://localhost:{port}")
                print(f"👉 Network: http://{ip}:{port}")
                print("Press Ctrl+C to stop.")
                httpd.serve_forever()
        except OSError as e:
            if e.errno == 98 or e.errno == 10048:
                print(f"Port {port} is in use, trying {port+1}...")
                port += 1
            else:
                raise

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    start_server()
