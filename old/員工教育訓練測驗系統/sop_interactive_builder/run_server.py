import socket
import webbrowser
import uvicorn
import time
import threading

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

def open_browser(port):
    time.sleep(2)
    webbrowser.open(f"http://localhost:{port}")

if __name__ == "__main__":
    base_port = 8000
    port = find_available_port(base_port)
    local_ip = get_local_ip()

    print("===============================================================================")
    print(" SOP Interactive Builder is starting...")
    print(" The browser will open automatically in 2 seconds.")
    print(" Keep this window open to run the server.")
    print("===============================================================================")
    print("📱 員工教育訓練互動簡報產生器 - 本機伺服器已啟動")
    print("===============================================================================")
    print("\n💡 請將此視窗保持開啟，關閉後服務將中斷。\n")
    
    if port != base_port:
        print(f"⚠️ 預設 Port {base_port} 已被佔用，已自動切換至可用 Port: {port}")

    print("📢 請在瀏覽器輸入以下網址開啟產生器：")
    print(f"👉 本機使用: http://localhost:{port}")
    if local_ip != "127.0.0.1":
        print(f"👉 區網分享: http://{local_ip}:{port}  (傳給其他同事)")
    print("===============================================================================")

    # Start browser in a background thread
    threading.Thread(target=open_browser, args=(port,), daemon=True).start()

    # Start uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=port, log_level="info")
