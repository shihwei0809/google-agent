import socket
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pathlib import Path

app = FastAPI(title="勝一小包barcode對刷核對")

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
                if port != start_port:
                    print(f"\n[提醒] 預設 Port {start_port} 已被佔用，已自動切換至可用 Port: {port}\n")
                return port
            except OSError:
                continue
    raise RuntimeError("找不到可用的 Port")

@app.get("/", response_class=HTMLResponse)
async def read_index():
    index_path = Path(__file__).parent / "index.html"
    return index_path.read_text(encoding="utf-8")

if __name__ == "__main__":
    port = find_available_port(8002)
    ip = get_local_ip()
    print(f"======================================================")
    print(f"啟動成功! 請開啟瀏覽器訪問: http://{ip}:{port}")
    print(f"======================================================")
    # 將 host 綁定為 ip，避免 uvicorn 在主控台印出 0.0.0.0
    uvicorn.run("main:app", host=ip, port=port, reload=True)
