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
import webbrowser
from typing import Optional
from fastapi import FastAPI, HTTPException, Header, Query, Request
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
import uvicorn

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# --- 支援 PyInstaller 單一 EXE 免安裝封裝與一般開發模式 ---
IS_FROZEN = getattr(sys, "frozen", False)
# RUNTIME_DIR: .exe 執行檔所在的真實外部資料夾（用來存放每個使用者獨立的 security_config.json 與最新穿透網址）
RUNTIME_DIR = os.path.dirname(sys.executable) if IS_FROZEN else os.path.dirname(os.path.abspath(__file__))
# BUNDLE_DIR: PyInstaller 解壓縮內部資源的目錄 (_MEIPASS)，用來讀取封裝在內的 static/index.html 與 cloudflared.exe
BUNDLE_DIR = getattr(sys, "_MEIPASS", RUNTIME_DIR)

# --- 方案 B：GitHub 雲端熱更新 (main.py & static/index.html) ---
if IS_FROZEN and not globals().get("_HOT_RELOADED_"):
    def _run_hub_cloud_hot_reload():
        import urllib.request
        cache_dir = os.path.join(RUNTIME_DIR, ".cloud_cache")
        cached_py = os.path.join(cache_dir, "main_cloud.py")
        cached_static = os.path.join(cache_dir, "static", "index.html")
        local_py = os.path.join(RUNTIME_DIR, "main.py")
        base_raw = "https://raw.githubusercontent.com/shihwei0809/google-agent/main/HTTPS%E9%81%A0%E7%AB%AF%E7%B6%B2%E9%A0%81%E7%A9%BF%E9%80%8F%E4%B8%AD%E5%BF%83"
        try:
            # 1. 同步最新 static/index.html
            req_html = urllib.request.Request(f"{base_raw}/static/index.html", headers={"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"})
            with urllib.request.urlopen(req_html, timeout=2.5) as r_html:
                if r_html.status == 200:
                    html_bytes = r_html.read()
                    if len(html_bytes) > 1000:
                        os.makedirs(os.path.dirname(cached_static), exist_ok=True)
                        with open(cached_static, "wb") as hf:
                            hf.write(html_bytes)
            # 2. 同步最新 main.py
            req_py = urllib.request.Request(f"{base_raw}/main.py", headers={"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"})
            with urllib.request.urlopen(req_py, timeout=2.5) as r_py:
                if r_py.status == 200:
                    py_bytes = r_py.read()
                    if b"FastAPI" in py_bytes and len(py_bytes) > 5000:
                        os.makedirs(cache_dir, exist_ok=True)
                        with open(cached_py, "wb") as pf:
                            pf.write(py_bytes)
        except Exception:
            pass
        target_py = None
        if os.path.exists(local_py) and os.path.exists(cached_py):
            target_py = local_py if os.path.getmtime(local_py) > os.path.getmtime(cached_py) else cached_py
        elif os.path.exists(cached_py):
            target_py = cached_py
        elif os.path.exists(local_py):
            target_py = local_py
        if target_py:
            try:
                with open(target_py, "r", encoding="utf-8") as tf:
                    hot_code = tf.read()
                g_dict = dict(globals())
                g_dict["_HOT_RELOADED_"] = True
                g_dict["__name__"] = "__main__"
                g_dict["__file__"] = target_py
                exec(compile(hot_code, target_py, "exec"), g_dict)
                sys.exit(0)
            except SystemExit:
                raise
            except Exception as e:
                print(f"[HotReload Fallback] 改用內建封裝邏輯: {e}")
    _run_hub_cloud_hot_reload()

PROJECTS_ROOT = RUNTIME_DIR if IS_FROZEN else os.path.abspath(os.path.join(RUNTIME_DIR, ".."))

def resolve_cloudflared_path() -> str:
    candidates = [
        os.path.join(BUNDLE_DIR, "cloudflared.exe"),
        os.path.join(RUNTIME_DIR, "cloudflared.exe"),
        os.path.join(PROJECTS_ROOT, "cloudflared.exe"),
        os.path.join(PROJECTS_ROOT, "IPAHQ排程", "cloudflared.exe"),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return os.path.join(RUNTIME_DIR, "cloudflared.exe")

CLOUDFLARED_PATH = resolve_cloudflared_path()
CONFIG_FILE = os.path.join(RUNTIME_DIR, "security_config.json")
PUBLIC_URL_FILE = os.path.join(RUNTIME_DIR, "public_url.txt")

# 讀取安全配置 (若無則自動在執行檔旁為該位使用者產生專屬金鑰與 QR Code 設定頁)
def load_security_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f), False
        except Exception:
            pass
    comp_name = os.environ.get("COMPUTERNAME", "PC")
    user_name = os.environ.get("USERNAME", "User")
    secret = base64.b32encode(secrets.token_bytes(20)).decode("utf-8")
    issuer = f"RemoteHub-{comp_name}"
    totp_uri = f"otpauth://totp/{issuer}:{user_name}?secret={secret}&issuer={issuer}"
    cfg = {
        "password": os.environ.get("REMOTE_HUB_PWD", "c606admin"),
        "totp_secret": secret,
        "issuer": issuer,
        "account": user_name,
        "totp_uri": totp_uri
    }
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except Exception:
        pass
    return cfg, True

SEC_CONFIG, IS_FIRST_RUN = load_security_config()
ACCESS_PASSWORD = SEC_CONFIG["password"]
TOTP_SECRET = SEC_CONFIG["totp_secret"]
TOTP_URI = SEC_CONFIG.get("totp_uri", f"otpauth://totp/RemoteHub?secret={TOTP_SECRET}")

app = FastAPI(title="HTTPS Remote Web Penetration Hub with 2FA")
public_tunnel_url = ""
tunnel_process = None

ACTIVE_SESSIONS = {}
FAILED_ATTEMPTS = {}
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_SECONDS = 900  # 15 分鐘

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

def detect_google_drive_root() -> Optional[str]:
    import string
    for letter in string.ascii_uppercase:
        for folder in ["我的雲端硬碟", "My Drive"]:
            candidate = f"{letter}:\\{folder}"
            if os.path.exists(candidate):
                return candidate
    return None

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
                    print("\n" + "="*64)
                    print(f"[ONLINE] 2FA Cloudflare HTTPS Protected Portal Live!")
                    print(f"外網穿透網址 (Public URL) : {public_tunnel_url}")
                    print(f"區網連線網址 (Local URL)  : http://{get_local_ip()}:{local_port}")
                    print(f"預設管理密碼 (Password)   : {ACCESS_PASSWORD}")
                    print(f"手機 2FA 金鑰 (TOTP Key)  : {TOTP_SECRET}")
                    print("="*64 + "\n")
                except Exception:
                    pass
                publish_tunnel_url(public_tunnel_url)
                break

    t = threading.Thread(target=monitor_output, daemon=True)
    t.start()

def publish_tunnel_url(url: str):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    comp_name = os.environ.get("COMPUTERNAME", "PC")

    # 1. 寫入本地 public_url.txt
    try:
        with open(PUBLIC_URL_FILE, "w", encoding="utf-8") as f:
            f.write(url)
    except Exception as e:
        print(f"[!] 寫入 {PUBLIC_URL_FILE} 失敗: {e}")

    # 2. 產生 HTML 自動導向與本機 2FA 綁定說明頁面 (僅存於本機與個人雲端硬碟，方便初次使用者掃描 QR Code)
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=180x180&data={requests.utils.quote(TOTP_URI) if 'requests' in sys.modules else TOTP_URI}"
    import urllib.parse
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=180x180&data={urllib.parse.quote(TOTP_URI)}"

    html_content = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>連線至 {comp_name} 遠端穿透中心</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #f8fafc; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; padding: 20px; box-sizing: border-box; }}
  .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 16px; padding: 28px; max-width: 500px; width: 100%; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.5); text-align: center; }}
  .badge {{ display: inline-block; background: #059669; color: #ecfdf5; font-size: 13px; font-weight: 600; padding: 4px 12px; border-radius: 9999px; margin-bottom: 12px; }}
  h1 {{ font-size: 20px; margin: 0 0 8px; color: #ffffff; }}
  p {{ font-size: 13px; color: #94a3b8; margin: 0 0 20px; line-height: 1.6; }}
  .btn {{ display: block; background: #2563eb; color: #ffffff; text-decoration: none; font-size: 16px; font-weight: 600; padding: 14px 20px; border-radius: 10px; transition: background 0.2s; word-break: break-all; }}
  .btn:hover {{ background: #1d4ed8; }}
  .info-box {{ margin-top: 20px; background: #0f172a; border-radius: 10px; padding: 16px; text-align: left; font-size: 13px; color: #cbd5e1; }}
  .info-row {{ display: flex; justify-content: space-between; margin-bottom: 8px; gap: 10px; }}
  .info-row:last-child {{ margin-bottom: 0; }}
  .label {{ color: #64748b; white-space: nowrap; }}
  .val {{ font-family: monospace; color: #38bdf8; font-weight: 600; word-break: break-all; text-align: right; }}
  .qr-box {{ margin-top: 16px; background: #0f172a; border: 1px dashed #334155; border-radius: 10px; padding: 14px; text-align: center; }}
  .qr-box img {{ background: #fff; padding: 8px; border-radius: 8px; margin-top: 8px; }}
</style>
</head>
<body>
<div class="card">
  <div class="badge">● 主機連線就緒 (HTTPS 安全穿透)</div>
  <h1>{comp_name} 遠端穿透中心</h1>
  <p>請點擊下方按鈕開啟遠端 Web 控制台（可將此網址傳至手機隨時連線）：</p>
  <a class="btn" href="{url}" target="_blank">🚀 立即開啟遠端控制台</a>
  <div class="info-box">
    <div class="info-row"><span class="label">公網穿透網址:</span><span class="val">{url}</span></div>
    <div class="info-row"><span class="label">更新時間:</span><span class="val">{timestamp}</span></div>
    <div class="info-row"><span class="label">本機名稱:</span><span class="val">{comp_name}</span></div>
    <div class="info-row"><span class="label">綁定 Google 帳號:</span><span class="val">{SEC_CONFIG.get('account', comp_name)}</span></div>
    <div class="info-row"><span class="label">1. 登入密碼:</span><span class="val">{ACCESS_PASSWORD}</span></div>
    <div class="info-row"><span class="label">2. 手機 2FA 金鑰:</span><span class="val">{TOTP_SECRET}</span></div>
  </div>
  <div class="qr-box">
    <div style="font-size:12px; color:#94a3b8;">📱 首次使用請用手機 <b>Google Authenticator</b> 掃描下方 QR Code 綁定 6 位數動態碼（登入控制台後可於右上角「⚙️ 帳號設定」隨時改為您個人的 Google 帳號與密碼）：</div>
    <img src="{qr_url}" width="150" height="150" alt="2FA QR Code">
  </div>
</div>
</body>
</html>"""

    # 3. 寫入執行檔所在目錄與上層目錄
    local_targets = [
        os.path.join(RUNTIME_DIR, "最新遠端穿透網址.html"),
        os.path.join(RUNTIME_DIR, "最新遠端穿透網址.txt"),
    ]
    if PROJECTS_ROOT != RUNTIME_DIR:
        local_targets.extend([
            os.path.join(PROJECTS_ROOT, "最新遠端穿透網址.html"),
            os.path.join(PROJECTS_ROOT, "最新遠端穿透網址.txt"),
        ])

    for target in local_targets:
        try:
            with open(target, "w", encoding="utf-8") as f:
                f.write(html_content if target.endswith(".html") else f"最新穿透網址: {url}\n更新時間: {timestamp}\n登入密碼: {ACCESS_PASSWORD}\n2FA金鑰: {TOTP_SECRET}\n")
        except Exception:
            pass

    # 若為單一 EXE 模式或首次執行，自動為使用者在瀏覽器打開本機引導頁（含網址與 2FA QR Code）
    if IS_FROZEN or IS_FIRST_RUN:
        try:
            webbrowser.open(os.path.join(RUNTIME_DIR, "最新遠端穿透網址.html"))
        except Exception:
            pass

    # 4. 動態偵測 Google 雲端硬碟並同步
    gdrive_root = detect_google_drive_root()
    if gdrive_root and os.path.exists(gdrive_root):
        gdrive_targets = [
            os.path.join(gdrive_root, "最新遠端穿透網址.html"),
            os.path.join(gdrive_root, "最新遠端穿透網址.txt"),
        ]
        ga_dir = os.path.join(gdrive_root, "GOOGLE ANGET")
        if os.path.exists(ga_dir):
            gdrive_targets.extend([
                os.path.join(ga_dir, "最新遠端穿透網址.html"),
                os.path.join(ga_dir, "最新遠端穿透網址.txt"),
            ])
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
    expire_time = ACTIVE_SESSIONS.get(x_auth_token)
    if not expire_time or expire_time < time.time():
        raise HTTPException(status_code=401, detail="驗證已過期或無效，請重新進行 2FA 登入")
    return True

# --- API 定義 ---

class Auth2FARequest(BaseModel):
    password: str
    totp_code: str

class AccountSetupRequest(BaseModel):
    account: str
    password: str
    regenerate_secret: bool = False

class CommandRequest(BaseModel):
    command: str
    shell: str = "powershell"
    cwd: Optional[str] = None

class FileSaveRequest(BaseModel):
    path: str
    content: str

def is_local_request(req: Request) -> bool:
    ip = get_client_ip(req)
    return ip in ("127.0.0.1", "::1", "localhost") and not req.headers.get("cf-connecting-ip")

@app.get("/api/account/info")
def get_account_info(request: Request, x_auth_token: Optional[str] = Header(None)):
    # 允許本機 (127.0.0.1) 直接檢視，或外網已通過 2FA 登入之使用者檢視
    if not is_local_request(request):
        verify_token(x_auth_token)
    import urllib.parse
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={urllib.parse.quote(TOTP_URI)}"
    return {
        "account": SEC_CONFIG.get("account", ""),
        "issuer": SEC_CONFIG.get("issuer", ""),
        "totp_secret": TOTP_SECRET,
        "totp_uri": TOTP_URI,
        "qr_url": qr_url,
        "is_local": is_local_request(request)
    }

@app.post("/api/account/setup")
def setup_account(req: AccountSetupRequest, request: Request, x_auth_token: Optional[str] = Header(None)):
    global SEC_CONFIG, ACCESS_PASSWORD, TOTP_SECRET, TOTP_URI
    if not is_local_request(request):
        verify_token(x_auth_token)

    clean_account = req.account.strip() or os.environ.get("USERNAME", "User")
    clean_pwd = req.password.strip()
    if len(clean_pwd) < 4:
        raise HTTPException(status_code=400, detail="密碼長度請至少輸入 4 碼以上！")

    comp_name = os.environ.get("COMPUTERNAME", "PC")
    issuer = f"RemoteHub-{comp_name}"
    new_secret = base64.b32encode(secrets.token_bytes(20)).decode("utf-8") if req.regenerate_secret else TOTP_SECRET
    new_uri = f"otpauth://totp/{issuer}:{clean_account}?secret={new_secret}&issuer={issuer}"

    SEC_CONFIG = {
        "password": clean_pwd,
        "totp_secret": new_secret,
        "issuer": issuer,
        "account": clean_account,
        "totp_uri": new_uri
    }
    ACCESS_PASSWORD = clean_pwd
    TOTP_SECRET = new_secret
    TOTP_URI = new_uri

    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(SEC_CONFIG, f, indent=2, ensure_ascii=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"寫入設定失敗: {e}")

    if public_tunnel_url:
        publish_tunnel_url(public_tunnel_url)

    import urllib.parse
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={urllib.parse.quote(TOTP_URI)}"
    return {
        "status": "ok",
        "message": "個人 Google 帳號與密碼已更新儲存！",
        "account": clean_account,
        "totp_secret": TOTP_SECRET,
        "qr_url": qr_url
    }

@app.post("/api/auth")
def auth(req: Auth2FARequest, request: Request):
    ip = get_client_ip(request)
    check_rate_limit(ip)

    if req.password != ACCESS_PASSWORD:
        record_failed_attempt(ip)
        raise HTTPException(status_code=401, detail="密碼錯誤，請重新確認！")

    if not verify_totp(TOTP_SECRET, req.totp_code):
        record_failed_attempt(ip)
        raise HTTPException(status_code=401, detail="2FA 動態驗證碼錯誤或已過期，請確認手機 Authenticator 時間與數字！")

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
    user_home = os.path.expanduser("~")
    shortcuts = [
        {"name": f"💻 程式工作目錄 ({PROJECTS_ROOT})", "path": PROJECTS_ROOT.replace("\\", "/")},
        {"name": "🖥️ 桌面 (Desktop)", "path": os.path.join(user_home, "Desktop").replace("\\", "/")},
        {"name": "📥 下載 (Downloads)", "path": os.path.join(user_home, "Downloads").replace("\\", "/")},
        {"name": "📄 文件 (Documents)", "path": os.path.join(user_home, "Documents").replace("\\", "/")},
    ]
    gdrive = detect_google_drive_root()
    if gdrive:
        shortcuts.insert(1, {"name": f"☁️ Google 雲端硬碟 ({gdrive[:2]})", "path": gdrive.replace("\\", "/")})
    return {"drives": drives, "shortcuts": shortcuts}

@app.get("/api/drives")
def get_drives(x_auth_token: Optional[str] = Header(None)):
    verify_token(x_auth_token)
    return get_system_drives()

@app.get("/api/status")
def get_status(x_auth_token: Optional[str] = Header(None)):
    verify_token(x_auth_token)

    try:
        total, used, free = shutil.disk_usage(PROJECTS_ROOT)
    except Exception:
        total, used, free = shutil.disk_usage("C:\\")

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

def resolve_static_dir() -> str:
    local = os.path.join(RUNTIME_DIR, "static")
    if os.path.exists(os.path.join(local, "index.html")):
        return local
    cloud_cached = os.path.join(RUNTIME_DIR, ".cloud_cache", "static")
    if os.path.exists(os.path.join(cloud_cached, "index.html")):
        return cloud_cached
    bundled = os.path.join(BUNDLE_DIR, "static")
    if os.path.exists(os.path.join(bundled, "index.html")):
        return bundled
    os.makedirs(local, exist_ok=True)
    return local

STATIC_DIR = resolve_static_dir()

@app.get("/", response_class=HTMLResponse)
def index():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>HTTPS 遠端網頁穿透中心建置中...</h1>"

if __name__ == "__main__":
    local_port = find_available_port(8800)
    local_ip = get_local_ip()
    print(f"[*] 啟動本機伺服器於: http://localhost:{local_port} (區網 IP: http://{local_ip}:{local_port})")

    start_cloudflared_tunnel(local_port)
    uvicorn.run(app, host="0.0.0.0", port=local_port, log_level="info")
