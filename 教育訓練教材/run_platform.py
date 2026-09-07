import os
import sys
import time
import socket
import subprocess
import webbrowser
import atexit
import signal

# 設定 Windows 主控台 UTF-8 編碼
if sys.platform == "win32":
    os.system("chcp 65001 >nul")
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
PYTHON_EXE = os.path.join(BACKEND_DIR, "venv", "Scripts", "python.exe")

processes = []

def get_local_ip():
    """取得本機區域網路實體 IP"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def kill_port_processes(port):
    """清理佔用指定 Port 的舊程序，防止重複啟動"""
    if sys.platform != "win32":
        return
    try:
        cmd = f'netstat -ano | findstr ":{port} "'
        output = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL)
        pids = set()
        for line in output.strip().split("\n"):
            parts = line.strip().split()
            if len(parts) >= 5 and "LISTENING" in line:
                pid = parts[-1]
                if pid.isdigit() and int(pid) > 4:
                    pids.add(pid)
        for pid in pids:
            subprocess.run(f"taskkill /F /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def cleanup():
    """安全關閉所有背景子程序"""
    print("\n[系統關閉中] 正在終止前後端服務...")
    for p in processes:
        try:
            p.terminate()
            p.kill()
        except Exception:
            pass
    # 再次清理 Port 8000 與 5173
    kill_port_processes(8000)
    kill_port_processes(5173)
    print("[系統已安全停止]")

atexit.register(cleanup)

def main():
    print("=" * 60)
    print("   [*] AI 教育訓練平台 - 整合管理控制台")
    print("=" * 60)

    # 1. 自動檢查並清理舊程序
    print("\n[1/3] 正在檢查並清理舊程序殘留 (Port 8000, 5173)...")
    kill_port_processes(8000)
    kill_port_processes(5173)
    time.sleep(1)

    # 2. 檢查 .env API Key
    env_file = os.path.join(BACKEND_DIR, ".env")
    has_key = False
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("GEMINI_API_KEY=") and len(line.split("=", 1)[1].strip()) > 5:
                    has_key = True
                    break
    if not has_key:
        print("[提示] 尚未設定 GEMINI_API_KEY，請至 backend/.env 填入金鑰。")

    # 3. 啟動 FastAPI 後端 (Port 8000)
    print("[2/3] 正在啟動 FastAPI 後端服務 (Port: 8000)...")
    backend_cmd = [PYTHON_EXE, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
    p_backend = subprocess.Popen(
        backend_cmd,
        cwd=BACKEND_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    processes.append(p_backend)

    # 4. 啟動 React 前端 (Port 5173)
    print("[3/3] 正在啟動 React 前端服務 (Port: 5173)...")
    frontend_cmd = "npm run dev -- --host --port 5173"
    p_frontend = subprocess.Popen(
        frontend_cmd,
        cwd=FRONTEND_DIR,
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    processes.append(p_frontend)

    # 等待伺服器就緒
    time.sleep(3)
    local_ip = get_local_ip()

    print("\n" + "=" * 60)
    print("   [OK] 平台啟動成功！前後端均在背後安靜運作")
    print("=" * 60)
    print(f"   本機網址:   http://localhost:5173")
    print(f"   區域網路:   http://{local_ip}:5173")
    print(f"   API 後端:   http://localhost:8000")
    print("-" * 60)
    print("   提示: 本視窗為「單一控制台」，請保持開啟。")
    print("   停止: 若要停止系統，請在此視窗按下 Ctrl + C 或直接關閉本視窗。")
    print("=" * 60)
    print("\n正在為您開啟瀏覽器...\n")

    webbrowser.open("http://localhost:5173")

    # 監聽持續運作
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
