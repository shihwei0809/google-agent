import socket
import subprocess
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

if __name__ == "__main__":
    default_port = 8788
    port = find_available_port(default_port)
    if port != default_port:
        print(f"Default port {default_port} is in use, fallback to port: {port}")
    
    ip = get_local_ip()
    print(f"=========================================")
    print(f" ChemFlow Pro Local Server Running")
    print(f"=========================================")
    print(f" [Local URL] http://localhost:{port}")
    print(f" [Network URL] http://{ip}:{port}")
    print(f"=========================================")
    
    # 加入 --ip 0.0.0.0 讓同網段的手機或其他電腦也能訪問
    try:
        subprocess.run(f"npx wrangler pages dev public --ip 0.0.0.0 --port {port} --local", shell=True)
    except KeyboardInterrupt:
        print("Server stopped.")
