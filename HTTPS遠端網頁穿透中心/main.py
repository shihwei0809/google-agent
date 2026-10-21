import os
import sys
import socket
import shutil
import subprocess
import threading
import time
import datetime
import re
import json
import ctypes
import base64
import struct
import hmac
import hashlib
import secrets
from typing import Optional
from fastapi import FastAPI, HTTPException, Header, Query, Request
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
import uvicorn

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

# --- 全域設定 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECTS_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
CLOUDFLARED_PATH = os.path.join(PROJECTS_ROOT, "cloudflared.exe")
CONFIG_FILE = os.path.join(BASE_DIR, "security_config.json")
PUBLIC_URL_FILE = os.path.join(BASE_DIR, "public_url.txt")

# 讀取安全配置 (若無則自動產生)
def load_security_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    secret = base64.b32encode(secrets.token_bytes(20)).decode("utf-8")
    cfg = {
        "password": os.environ.get("REMOTE_HUB_PWD", "c606admin"),
        "totp_secret": secret,
        "issuer": "GoogleAgent-C606",
        "account": "shihwei0809@gmail.com",
        "totp_uri": f"otpauth://totp/GoogleAgent:shihwei0809@gmail.com?secret={secret}&issuer=GoogleAgent-C606"
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
    return cfg

SEC_CONFIG = load_security_config()
ACCESS_PASSWORD = SEC_CONFIG["password"]
TOTP_SECRET = SEC_CONFIG["totp_secret"]

app = FastAPI(title="HTTPS Remote Web Penetration Hub with 2FA")
public_tunnel_url = ""
tunnel_process = None

# 安全工作階段管理 (Session Tokens)
# token -> expire_timestamp
ACTIVE_SESSIONS = {}

# 防暴力破解 (Rate Limiting)
# ip -> {"count": int, "blocked_until": float}
FAILED_ATTEMPTS = {}
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_SECONDS = 900 # 15 分鐘

def verify_totp(secret: str, code: str, window: int = 1) -> bool:
    curr = int(time.time()) // 30
    code = str(code).strip()
    try:
        key = base64.b32decode(secret, True)
    except Exception:
        return False

    for i in range(-window, window + 1):
        msg = struct.pack(">Q", curr + i)
        h = hmac.new(key, msg, hashlib.sha1).digest()
        o = h[19] & 15
        calc = f"{(struct.unpack('>I', h[o:o+4])[0] & 0x7fffffff) % 1000000:06d}"
        if calc == code:
            return True
    return False

def get_client_ip(req: Request) -> str:
    forwarded = req.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return req.client.host if req.client else "unknown"

def check_rate_limit(ip: str):
    now = time.time()
    record = FAILED_ATTEMPTS.get(ip)
    if record:
        if record.get("blocked_until", 0) > now:
            remaining = int(record["blocked_until"] - now)
            raise HTTPException(status_code=429, detail=f"安全鎖定中：連續錯誤多次，請等待 {remaining} 秒後再試！")
        elif record.get("blocked_until", 0) <= now and record.get("count", 0) >= MAX_FAILED_ATTEMPTS:
            FAILED_ATTEMPTS[ip] = {"count": 0, "blocked_until": 0}

def record_failed_attempt(ip: str):
    now = time.time()
    record = FAILED_ATTEMPTS.get(ip, {"count": 0, "blocked_until": 0})
    record["count"] += 1
    if record["count"] >= MAX_FAILED_ATTEMPTS:
        record["blocked_until"] = now + LOCKOUT_SECONDS
        print(f"[SECURITY ALERT] IP {ip} 已被鎖定 15 分鐘 (連續 {MAX_FAILED_ATTEMPTS} 次登入失敗)")
    FAILED_ATTEMPTS[ip] = record

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def find_available_port(start_port: int = 8800, max_attempts: int = 50) -> int:
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", port))
                return port
            except OSError:
                continue
    return start_port

def start_cloudflared_tunnel(local_port: int):
    global public_tunnel_url, tunnel_process
    if not os.path.exists(CLOUDFLARED_PATH):
        print(f"[!] 找不到 cloudflared.exe: {CLOUDFLARED_PATH}")
        return

    cmd = [
        CLOUDFLARED_PATH,
        "tunnel",
        "--protocol", "http2",
        "--url", f"http://127.0.0.1:{local_port}"
    ]
    print(f"[*] 正在建立 Cloudflare HTTPS 安全穿透隧道 (Port {local_port})...")
    
    tunnel_process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    def monitor_output():
        global public_tunnel_url
        for line in tunnel_process.stdout:
            m = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
            if m:
                public_tunnel_url = m.group(0)
                try:
                    print("\n" + "="*60)
                    print(f"[ONLINE] 2FA Cloudflare HTTPS Protected Portal Live!")
                    print(f"URL: {public_tunnel_url}")
                    print(f"Password: {ACCESS_PASSWORD}")
                    print(f"2FA Secret: {TOTP_SECRET}")
                    print("="*60 + "\n")
                except Exception:
                    pass
                publish_tunnel_url(public_tunnel_url)
                break

    t = threading.Thread(target=monitor_output, daemon=True)
    t.start()

def publish_tunnel_url(url: str):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # 1. 寫入本地 public_url.txt
    try:
        with open(PUBLIC_URL_FILE, "w", encoding="utf-8") as f:
            f.write(url)
    except Exception as e:
        print(f"[!] 寫入 {PUBLIC_URL_FILE} 失敗: {e}")

    # 2. 產生 HTML 自動導向頁面
    html_content = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="refresh" content="2; url={url}">
<title>連線至 GOOGLE本機 (C606-PC1) 遠端穿透中心</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #f8fafc; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; padding: 20px; box-sizing: border-box; }}
  .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 16px; padding: 32px; max-width: 480px; width: 100%; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.5); text-align: center; }}
  .badge {{ display: inline-block; background: #059669; color: #ecfdf5; font-size: 13px; font-weight: 600; padding: 4px 12px; border-radius: 9999px; margin-bottom: 16px; }}
  h1 {{ font-size: 20px; margin: 0 0 12px; color: #ffffff; }}
  p {{ font-size: 14px; color: #94a3b8; margin: 0 0 24px; line-height: 1.6; }}
  .btn {{ display: block; background: #2563eb; color: #ffffff; text-decoration: none; font-size: 16px; font-weight: 600; padding: 14px 20px; border-radius: 10px; transition: background 0.2s; word-break: break-all; }}
  .btn:hover {{ background: #1d4ed8; }}
  .info-box {{ margin-top: 24px; background: #0f172a; border-radius: 8px; padding: 16px; text-align: left; font-size: 13px; color: #cbd5e1; }}
  .info-row {{ display: flex; justify-content: space-between; margin-bottom: 8px; }}
  .info-row:last-child {{ margin-bottom: 0; }}
  .label {{ color: #64748b; }}
  .val {{ font-family: monospace; color: #38bdf8; font-weight: 600; }}
</style>
</head>
<body>
<div class="card">
  <div class="badge">● 主機連線中 (在線)</div>
  <h1>GOOGLE 本機 (C606-PC1) 遠端穿透中心</h1>
  <p>系統將在 2 秒內自動為您導向至安全穿透入口，或直接點擊下方按鈕前往：</p>
  <a class="btn" href="{url}" target="_blank">🚀 立即開啟遠端控制台</a>
  <div class="info-box">
    <div class="info-row"><span class="label">穿透網址:</span><span class="val" style="word-break: break-all;">{url}</span></div>
    <div class="info-row"><span class="label">更新時間:</span><span class="val">{timestamp}</span></div>
    <div class="info-row"><span class="label">本機名稱:</span><span class="val">C606-PC1 (Windows)</span></div>
    <div class="info-row"><span class="label">登入密碼:</span><span class="val">c606admin</span></div>
    <div class="info-row"><span class="label">動態雙重認證:</span><span class="val">Google Authenticator (6位數)</span></div>
  </div>
</div>
</body>
</html>"""

    # 3. 寫入本機專案與根目錄
    local_targets = [
        os.path.join(PROJECTS_ROOT, "最新遠端穿透網址.html"),
        os.path.join(PROJECTS_ROOT, "最新遠端穿透網址.txt"),
    ]
    for target in local_targets:
        try:
            with open(target, "w", encoding="utf-8") as f:
                f.write(html_content if target.endswith(".html") else f"最新穿透網址: {url}\n更新時間: {timestamp}\n")
        except Exception:
            pass

    # 4. 同步寫入 Google 雲端硬碟 (G:\我的雲端硬碟)
    gdrive_root = r"G:\我的雲端硬碟"
    if os.path.exists(gdrive_root):
        gdrive_targets = [
            os.path.join(gdrive_root, "最新遠端穿透網址.html"),
            os.path.join(gdrive_root, "最新遠端穿透網址.txt"),
            os.path.join(gdrive_root, "GOOGLE ANGET", "最新遠端穿透網址.html"),
            os.path.join(gdrive_root, "GOOGLE ANGET", "最新遠端穿透網址.txt"),
        ]
        for target in gdrive_targets:
            try:
                os.makedirs(os.path.dirname(target), exist_ok=True)
                with open(target, "w", encoding="utf-8") as f:
                    f.write(html_content if target.endswith(".html") else f"最新穿透網址: {url}\n更新時間: {timestamp}\n")
                print(f"[GDrive Sync] 已成功同步最新穿透網址至: {target}")
            except Exception as ge:
                print(f"[!] 同步至 Google 雲端硬碟失敗 ({target}): {ge}")

def verify_token(x_auth_token: Optional[str] = Header(None)):
    if not x_auth_token:
        raise HTTPException(status_code=401, detail="未提供安全驗證 Token")
    # 檢查是否為合法有效之 Session Token
    expire_time = ACTIVE_SESSIONS.get(x_auth_token)
    if not expire_time or expire_time < time.time():
        raise HTTPException(status_code=401, detail="驗證已過期或無效，請重新進行 2FA 登入")
    return True

# --- API 定義 ---

class Auth2FARequest(BaseModel):
    password: str
    totp_code: str

class CommandRequest(BaseModel):
    command: str
    shell: str = "powershell"
    cwd: Optional[str] = None

class FileSaveRequest(BaseModel):
    path: str
    content: str



@app.post("/api/auth")
def auth(req: Auth2FARequest, request: Request):
    ip = get_client_ip(request)
    check_rate_limit(ip)

    # 1. 密碼驗證
    if req.password != ACCESS_PASSWORD:
        record_failed_attempt(ip)
        raise HTTPException(status_code=401, detail="密碼錯誤，請重新確認！")

    # 2. 2FA 動態驗證碼 (TOTP 6位數)
    if not verify_totp(TOTP_SECRET, req.totp_code):
        record_failed_attempt(ip)
        raise HTTPException(status_code=401, detail="2FA 動態驗證碼錯誤或已過期，請確認手機 Authenticator 時間與數字！")

    # 登入成功：清除失敗紀錄，生成高強度 Session Token (有效期限 8 小時)
    if ip in FAILED_ATTEMPTS:
        FAILED_ATTEMPTS[ip]["count"] = 0

    session_token = secrets.token_hex(32)
    ACTIVE_SESSIONS[session_token] = time.time() + (8 * 3600)
    print(f"[SECURITY] 2FA 認證成功: IP {ip} 已簽發安全 Session")

    return {
        "status": "ok",
        "token": session_token,
        "expires_in": 28800
    }

@app.post("/api/shutdown")
def shutdown(x_auth_token: Optional[str] = Header(None)):
    verify_token(x_auth_token)
    print("[SECURITY] 使用者要求立即關閉穿透通道與伺服器...")
    
    def kill_soon():
        time.sleep(1)
        global tunnel_process
        if tunnel_process:
            tunnel_process.terminate()
        os._exit(0)

    threading.Thread(target=kill_soon, daemon=True).start()
    return {"status": "ok", "message": "穿透中心正在關閉，外網入口已即時切斷！"}

def get_system_drives():
    import string
    drives = []
    for letter in string.ascii_uppercase:
        drive_path = f"{letter}:\\"
        if os.path.exists(drive_path):
            try:
                total, used, free = shutil.disk_usage(drive_path)
                drives.append({
                    "name": f"{letter}: 磁碟",
                    "path": f"{letter}:/",
                    "total_gb": round(total / (1024**3), 1),
                    "free_gb": round(free / (1024**3), 1),
                    "is_drive": True
                })
            except Exception:
                drives.append({
                    "name": f"{letter}: 磁碟",
                    "path": f"{letter}:/",
                    "total_gb": 0,
                    "free_gb": 0,
                    "is_drive": True
                })
    # 常見捷徑
    user_home = os.path.expanduser("~")
    shortcuts = [
        {"name": "💻 本機專案庫 (D:\\GOOGLE ANGET)", "path": PROJECTS_ROOT.replace("\\", "/")},
        {"name": "🖥️ 桌面 (Desktop)", "path": os.path.join(user_home, "Desktop").replace("\\", "/")},
        {"name": "📥 下載 (Downloads)", "path": os.path.join(user_home, "Downloads").replace("\\", "/")},
        {"name": "📄 文件 (Documents)", "path": os.path.join(user_home, "Documents").replace("\\", "/")},
    ]
    if os.path.exists("G:\\我的雲端硬碟"):
        shortcuts.insert(1, {"name": "☁️ Google 雲端硬碟 (G:)", "path": "G:/我的雲端硬碟"})
    return {"drives": drives, "shortcuts": shortcuts}

@app.get("/api/drives")
def get_drives(x_auth_token: Optional[str] = Header(None)):
    verify_token(x_auth_token)
    return get_system_drives()

@app.get("/api/status")
def get_status(x_auth_token: Optional[str] = Header(None)):
    verify_token(x_auth_token)
    
    total, used, free = shutil.disk_usage(PROJECTS_ROOT)
    
    class MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [
            ("dwLength", ctypes.c_ulong),
            ("dwMemoryLoad", ctypes.c_ulong),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]
    mem_stat = MEMORYSTATUSEX()
    mem_stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(mem_stat))
    
    rdp_active = False
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1.0)
        if s.connect_ex(("127.0.0.1", 3389)) == 0:
            rdp_active = True

    return {
        "local_ip": get_local_ip(),
        "public_url": public_tunnel_url,
        "computer_name": os.environ.get("COMPUTERNAME", "PC"),
        "user_name": os.environ.get("USERNAME", "User"),
        "rdp_port_3389": rdp_active,
        "disk": {
            "total_gb": round(total / (1024**3), 1),
            "free_gb": round(free / (1024**3), 1),
            "used_percent": round((used / total) * 100, 1)
        },
        "memory": {
            "load_percent": mem_stat.dwMemoryLoad,
            "total_gb": round(mem_stat.ullTotalPhys / (1024**3), 1),
            "free_gb": round(mem_stat.ullAvailPhys / (1024**3), 1)
        }
    }

@app.post("/api/terminal/run")
def run_command(req: CommandRequest, x_auth_token: Optional[str] = Header(None)):
    verify_token(x_auth_token)
    work_dir = req.cwd or PROJECTS_ROOT
    if not os.path.exists(work_dir):
        work_dir = PROJECTS_ROOT

    if req.shell == "cmd":
        cmd_args = ["cmd.exe", "/c", req.command]
    else:
        cmd_args = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", req.command]

    try:
        res = subprocess.run(
            cmd_args,
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=60
        )
        return {
            "exit_code": res.returncode,
            "stdout": res.stdout,
            "stderr": res.stderr
        }
    except subprocess.TimeoutExpired:
        return {
            "exit_code": -1,
            "stdout": "",
            "stderr": "執行超時（超過 60 秒）"
        }
    except Exception as e:
        return {
            "exit_code": -1,
            "stdout": "",
            "stderr": str(e)
        }

@app.get("/api/files/list")
def list_files(path: str = "", x_auth_token: Optional[str] = Header(None)):
    verify_token(x_auth_token)
    
    if not path or path == "root":
        data = get_system_drives()
        items = []
        for s in data["shortcuts"]:
            items.append({
                "name": s["name"],
                "path": s["path"],
                "is_dir": True,
                "is_shortcut": True,
                "size": 0,
                "modified": ""
            })
        for d in data["drives"]:
            items.append({
                "name": f"{d['name']} (剩餘 {d['free_gb']} GB / 總共 {d['total_gb']} GB)",
                "path": d["path"],
                "is_dir": True,
                "is_drive": True,
                "size": 0,
                "modified": ""
            })
        return {
            "current_path": "",
            "is_root": True,
            "items": items
        }

    target_dir = os.path.abspath(path.replace("/", "\\"))
    if not os.path.exists(target_dir):
        raise HTTPException(status_code=404, detail="資料夾不存在")

    items = []
    try:
        for entry in os.scandir(target_dir):
            try:
                stat = entry.stat()
                items.append({
                    "name": entry.name,
                    "path": os.path.join(target_dir, entry.name).replace("\\", "/"),
                    "is_dir": entry.is_dir(),
                    "size": stat.st_size if not entry.is_dir() else 0,
                    "modified": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime))
                })
            except Exception:
                continue
    except PermissionError:
        raise HTTPException(status_code=403, detail="存取被拒 (此系統資料夾需要更高權限)")

    items.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
    
    parent = os.path.dirname(target_dir)
    if parent == target_dir:
        parent = ""

    return {
        "current_path": target_dir.replace("\\", "/"),
        "parent_path": parent.replace("\\", "/") if parent else "",
        "is_root": False,
        "items": items
    }

@app.get("/api/files/read")
def read_file(path: str, x_auth_token: Optional[str] = Header(None)):
    verify_token(x_auth_token)
    target_file = os.path.abspath(path.replace("/", "\\"))
    if not os.path.isfile(target_file):
        raise HTTPException(status_code=404, detail="檔案不存在")

    try:
        with open(target_file, "r", encoding="utf-8", errors="replace") as f:
            content = f.read(1000000)
        return {"path": target_file.replace("\\", "/"), "content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/files/download")
def download_file(path: str, x_auth_token: Optional[str] = Query(None)):
    verify_token(x_auth_token)
    target_file = os.path.abspath(path.replace("/", "\\"))
    if not os.path.isfile(target_file):
        raise HTTPException(status_code=404, detail="檔案不存在")
    return FileResponse(target_file, filename=os.path.basename(target_file))

@app.post("/api/files/save")
def save_file(req: FileSaveRequest, x_auth_token: Optional[str] = Header(None)):
    verify_token(x_auth_token)
    target_file = os.path.abspath(req.path.replace("/", "\\"))
    try:
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(req.content)
        return {"status": "ok", "message": "檔案儲存成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

STATIC_DIR = os.path.join(BASE_DIR, "static")
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR, exist_ok=True)

@app.get("/", response_class=HTMLResponse)
def index():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>HTTPS 遠端網頁穿透中心建置中...</h1>"

if __name__ == "__main__":
    local_port = find_available_port(8800)
    print(f"[*] 啟動本機伺服器於: http://127.0.0.1:{local_port}")
    
    start_cloudflared_tunnel(local_port)
    uvicorn.run(app, host="0.0.0.0", port=local_port, log_level="info")
