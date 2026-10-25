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
from fastapi.responses import HTMLResponse, FileResponse, Response
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


# ==========================================
# 即時遠端桌面畫面串流與滑鼠鍵盤操控 API (純 HTTPS 443)
# ==========================================
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

class MouseEventRequest(BaseModel):
    action: str  # click, dblclick, rightclick, mousedown, mouseup, move, wheel
    x_ratio: float = 0.5
    y_ratio: float = 0.5
    delta: int = 0
    all_screens: bool = False

class KeyEventRequest(BaseModel):
    action: str  # key, text, combo
    key: str = ""
    text: str = ""

_thread_desktop_local = threading.local()
_virtual_cursor = [960, 540]
_promoted_hwnd = 0
_minimized_in_lock = set()

def _attach_to_input_desktop(force_default: bool = False):
    """確保當前執行緒已掛載至使用者互動桌面 (Default Desktop)，支援鎖定畫面下直通底層桌面"""
    try:
        u32 = ctypes.windll.user32
        GENERIC_ALL = 0x10000000
        hdesk = 0
        if not force_default:
            hdesk = u32.OpenInputDesktop(0, False, GENERIC_ALL)
        if not hdesk:
            hdesk = u32.OpenDesktopW("Default", 0, False, GENERIC_ALL)
        if hdesk:
            u32.SetThreadDesktop(hdesk)
            old = getattr(_thread_desktop_local, "hdesk", None)
            if old and old != hdesk:
                u32.CloseDesktop(old)
            _thread_desktop_local.hdesk = hdesk
    except Exception:
        pass

class _POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

class _RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long), ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

def _is_workstation_locked() -> bool:
    try:
        u32 = ctypes.windll.user32
        GENERIC_ALL = 0x10000000
        hin = u32.OpenInputDesktop(0, False, GENERIC_ALL)
        if not hin:
            return True
        buf = ctypes.create_unicode_buffer(64)
        u32.GetUserObjectInformationW(hin, 2, buf, 128, None)
        u32.CloseDesktop(hin)
        return buf.value.lower() != "default"
    except Exception:
        return False

def _get_ordered_desktop_windows(screen_w: int = 1920, screen_h: int = 1080):
    """列舉 Default 桌面所有可見視窗 (自動過濾 Windows 鎖定畫面遮罩，並支援鎖定下視窗切換排序)"""
    global _promoted_hwnd
    _attach_to_input_desktop(force_default=True)
    u32 = ctypes.windll.user32
    dwm = getattr(ctypes.windll, "dwmapi", None)

    raw_hwnds = []
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def _cb(hwnd, _lparam):
        if hwnd and u32.IsWindowVisible(hwnd) and not u32.IsIconic(hwnd):
            raw_hwnds.append(int(hwnd))
        return True
    u32.EnumWindows(WNDENUMPROC(_cb), 0)

    app_windows = []
    taskbar_win = None
    progman_win = None

    SKIP_CLASSES = {
        "LockScreenBackstopFrame", "Windows.UI.Core.CoreWindow",
        "IME", "MSCTFIME UI", "DummyDWMListenerWindow",
        "EdgeUiInputTopWndClass", "EdgeUiInputWndClass", " WorkerW"
    }
    SKIP_TITLES = {
        "Windows 預設鎖定畫面", "Windows Default Lock Screen",
        "Backstop Window", "Windows 輸入體驗", "Windows Input Experience"
    }

    for hwnd in raw_hwnds:
        if hwnd in _minimized_in_lock:
            continue
        if dwm:
            cloaked = ctypes.c_int(0)
            if dwm.DwmGetWindowAttribute(hwnd, 14, ctypes.byref(cloaked), 4) == 0 and cloaked.value != 0:
                continue
        cls_buf = ctypes.create_unicode_buffer(128)
        txt_buf = ctypes.create_unicode_buffer(256)
        u32.GetClassNameW(hwnd, cls_buf, 128)
        u32.GetWindowTextW(hwnd, txt_buf, 256)
        cls = cls_buf.value
        txt = txt_buf.value

        if cls in SKIP_CLASSES or txt in SKIP_TITLES:
            continue
        if cls == "ApplicationFrameWindow" and ("鎖定畫面" in txt or "Lock Screen" in txt or not txt.strip()):
            continue

        rc = _RECT()
        u32.GetWindowRect(hwnd, ctypes.byref(rc))
        w = rc.right - rc.left
        h = rc.bottom - rc.top
        if w < 30 or h < 20 or rc.right <= 0 or rc.bottom <= 0 or rc.left >= screen_w or rc.top >= screen_h:
            continue

        info = {"hwnd": hwnd, "cls": cls, "title": txt, "rect": (rc.left, rc.top, rc.right, rc.bottom), "w": w, "h": h}
        if cls == "Shell_TrayWnd":
            taskbar_win = info
        elif cls in ("Progman", "WorkerW"):
            if not progman_win and w >= screen_w and h >= screen_h:
                progman_win = info
        else:
            if not txt.strip() and cls not in ("Chrome_WidgetWin_1", "CabinetWClass"):
                continue
            app_windows.append(info)

    if _promoted_hwnd:
        for i, item in enumerate(app_windows):
            if item["hwnd"] == _promoted_hwnd:
                promoted = app_windows.pop(i)
                app_windows.insert(0, promoted)
                break

    return app_windows, taskbar_win, progman_win

def _print_window_to_image(hwnd: int, w: int, h: int):
    from PIL import Image
    u32 = ctypes.windll.user32
    gdi = ctypes.windll.gdi32
    hdc_screen = u32.GetDC(0)
    hdc_mem = gdi.CreateCompatibleDC(hdc_screen)
    bmi = ctypes.create_string_buffer(40)
    struct.pack_into("IiiHHIIiiII", bmi, 0, 40, w, -h, 1, 32, 0, 0, 0, 0, 0, 0)
    ppv = ctypes.c_void_p()
    hbm = gdi.CreateDIBSection(hdc_screen, bmi, 0, ctypes.byref(ppv), None, 0)
    old_bm = gdi.SelectObject(hdc_mem, hbm)
    try:
        ret = u32.PrintWindow(hwnd, hdc_mem, 2)
        if not ret:
            u32.PrintWindow(hwnd, hdc_mem, 0)
        buf = (ctypes.c_ubyte * (w * h * 4)).from_address(ppv.value)
        img = Image.frombuffer("RGBA", (w, h), buf, "raw", "BGRA", 0, 1).convert("RGB")
        return img
    finally:
        gdi.SelectObject(hdc_mem, old_bm)
        gdi.DeleteObject(hbm)
        gdi.DeleteDC(hdc_mem)
        u32.ReleaseDC(0, hdc_screen)

def _grab_desktop_composited(left: int, top: int, w: int, h: int):
    """當 Windows 處於鎖定畫面時，直接穿透鎖定遮罩並合成使用者底層桌面視窗與工作列"""
    from PIL import Image
    canvas = Image.new("RGB", (w, h), (15, 23, 42))
    app_windows, taskbar_win, progman_win = _get_ordered_desktop_windows(w, h)

    render_stack = []
    covered_fullscreen = False
    for item in app_windows:
        render_stack.append(item)
        l, t, r, b = item["rect"]
        if l <= 0 and t <= 0 and r >= w and b >= h - 60:
            covered_fullscreen = True
            break

    if not covered_fullscreen and progman_win:
        render_stack.append(progman_win)

    for item in reversed(render_stack):
        try:
            win_img = _print_window_to_image(item["hwnd"], item["w"], item["h"])
            l, t, _, _ = item["rect"]
            canvas.paste(win_img, (l - left, t - top))
        except Exception:
            pass

    if taskbar_win:
        try:
            tb_img = _print_window_to_image(taskbar_win["hwnd"], taskbar_win["w"], taskbar_win["h"])
            l, t, _, _ = taskbar_win["rect"]
            canvas.paste(tb_img, (l - left, t - top))
        except Exception:
            pass

    return canvas

def _get_screen_bounds(all_screens: bool = False):
    _attach_to_input_desktop(force_default=True)
    u32 = ctypes.windll.user32
    if all_screens:
        left = u32.GetSystemMetrics(76)   # SM_XVIRTUALSCREEN
        top = u32.GetSystemMetrics(77)    # SM_YVIRTUALSCREEN
        width = u32.GetSystemMetrics(78)  # SM_CXVIRTUALSCREEN
        height = u32.GetSystemMetrics(79) # SM_CYVIRTUALSCREEN
    else:
        left, top = 0, 0
        width = u32.GetSystemMetrics(0)   # SM_CXSCREEN
        height = u32.GetSystemMetrics(1)  # SM_CYSCREEN
    return left, top, max(1, width), max(1, height)

def _draw_cursor_on_image(img, offset_left=0, offset_top=0, use_virtual=False):
    try:
        from PIL import ImageDraw
        pt = _POINT()
        if ctypes.windll.user32.GetCursorPos(ctypes.byref(pt)):
            _virtual_cursor[0] = pt.x
            _virtual_cursor[1] = pt.y
        cx = _virtual_cursor[0] - offset_left
        cy = _virtual_cursor[1] - offset_top
        if 0 <= cx <= img.width and 0 <= cy <= img.height:
            draw = ImageDraw.Draw(img)
            r = 7
            draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline="#ffffff", width=2)
            draw.ellipse((cx - 4, cy - 4, cx + 4, cy + 4), fill="#ef4444")
    except Exception:
        pass

@app.get("/api/screen/frame")
def get_screen_frame(
    quality: int = 65,
    scale: float = 0.75,
    all_screens: bool = False,
    x_auth_token: Optional[str] = Query(None),
    header_token: Optional[str] = Header(None, alias="x-auth-token")
):
    token = header_token or x_auth_token
    verify_token(token)
    try:
        from PIL import Image
        from io import BytesIO
        left, top, w, h = _get_screen_bounds(all_screens)
        img = None
        if not _is_workstation_locked():
            try:
                _attach_to_input_desktop(force_default=False)
                from PIL import ImageGrab
                img = ImageGrab.grab(all_screens=all_screens)
            except Exception:
                img = None
        if img is None:
            _attach_to_input_desktop(force_default=True)
            img = _grab_desktop_composited(left, top, w, h)
        _draw_cursor_on_image(img, left, top)
        if 0.2 <= scale < 0.99:
            new_w = max(320, int(img.width * scale))
            new_h = max(200, int(img.height * scale))
            img = img.resize((new_w, new_h), Image.Resampling.BILINEAR)
        buf = BytesIO()
        q = max(20, min(95, int(quality)))
        img.convert("RGB").save(buf, format="JPEG", quality=q, optimize=False)
        return Response(
            content=buf.getvalue(),
            media_type="image/jpeg",
            headers={"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"擷取螢幕失敗: {e}")

def _find_deepest_child_at(root_hwnd: int, sx: int, sy: int) -> int:
    u32 = ctypes.windll.user32
    best_hwnd = root_hwnd
    best_area = 1 << 60
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def _cb(hwnd, _lparam):
        nonlocal best_hwnd, best_area
        if hwnd and u32.IsWindowVisible(hwnd):
            rc = _RECT()
            if u32.GetWindowRect(hwnd, ctypes.byref(rc)):
                if rc.left <= sx < rc.right and rc.top <= sy < rc.bottom:
                    area = max(1, (rc.right - rc.left) * (rc.bottom - rc.top))
                    if area <= best_area:
                        best_area = area
                        best_hwnd = int(hwnd)
        return True
    try:
        u32.EnumChildWindows(root_hwnd, WNDENUMPROC(_cb), 0)
    except Exception:
        pass
    return best_hwnd

@app.post("/api/screen/mouse")
def handle_screen_mouse(req: MouseEventRequest, x_auth_token: Optional[str] = Header(None)):
    global _promoted_hwnd
    verify_token(x_auth_token)
    u32 = ctypes.windll.user32
    left, top, w, h = _get_screen_bounds(req.all_screens)
    tx = int(left + max(0.0, min(1.0, req.x_ratio)) * w)
    ty = int(top + max(0.0, min(1.0, req.y_ratio)) * h)
    _virtual_cursor[0] = tx
    _virtual_cursor[1] = ty

    act = req.action.lower()

    # 1. 確保掛載至互動桌面並將滑鼠物理移動至座標
    _attach_to_input_desktop(force_default=False)
    u32.SetCursorPos(tx, ty)

    # 2. 發送真實 OS 硬體級滑鼠事件 (移除干擾雙擊的 Alt 鍵干擾，確保 Windows 100% 辨識連點開檔)
    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004
    MOUSEEVENTF_RIGHTDOWN = 0x0008
    MOUSEEVENTF_RIGHTUP = 0x0010
    MOUSEEVENTF_MIDDLEDOWN = 0x0020
    MOUSEEVENTF_MIDDLEUP = 0x0040
    MOUSEEVENTF_WHEEL = 0x0800

    if act == "click":
        u32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(0.02)
        u32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    elif act == "dblclick":
        # 嚴格遵循 Windows 雙擊開檔標準時序 (Click 1 -> 70ms 最適間隔 -> Click 2)
        u32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(0.02)
        u32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        time.sleep(0.07)
        u32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(0.02)
        u32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    elif act == "rightclick":
        u32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
        time.sleep(0.02)
        u32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
    elif act == "middleclick":
        u32.mouse_event(MOUSEEVENTF_MIDDLEDOWN, 0, 0, 0, 0)
        time.sleep(0.02)
        u32.mouse_event(MOUSEEVENTF_MIDDLEUP, 0, 0, 0, 0)
    elif act == "mousedown":
        u32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    elif act == "mouseup":
        u32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    elif act == "wheel":
        d = int(req.delta)
        if d == 0:
            d = 120
        u32.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, d, 0)

    return {"status": "ok", "x": tx, "y": ty, "mode": "hardware_direct"}

VK_MAP = {
    "enter": 0x0D, "return": 0x0D, "backspace": 0x08, "tab": 0x09,
    "escape": 0x1B, "esc": 0x1B, "space": 0x20, "delete": 0x2E, "del": 0x2E,
    "up": 0x26, "arrowup": 0x26, "down": 0x28, "arrowdown": 0x28,
    "left": 0x25, "arrowleft": 0x25, "right": 0x27, "arrowright": 0x27,
    "home": 0x24, "end": 0x23, "pageup": 0x21, "pagedown": 0x22,
    "win": 0x5B, "f1": 0x70, "f2": 0x71, "f3": 0x72, "f4": 0x73,
    "f5": 0x74, "f6": 0x75, "f7": 0x76, "f8": 0x77, "f9": 0x78,
    "f10": 0x79, "f11": 0x7A, "f12": 0x7B,
}

def _tap_vk(vk: int):
    u32 = ctypes.windll.user32
    u32.keybd_event(vk, 0, 0, 0)
    time.sleep(0.02)
    u32.keybd_event(vk, 0, 2, 0)

def _combo_vk(mod_vk: int, key_vk: int):
    u32 = ctypes.windll.user32
    u32.keybd_event(mod_vk, 0, 0, 0)
    time.sleep(0.02)
    u32.keybd_event(key_vk, 0, 0, 0)
    time.sleep(0.02)
    u32.keybd_event(key_vk, 0, 2, 0)
    time.sleep(0.02)
    u32.keybd_event(mod_vk, 0, 2, 0)

ULONG_PTR = ctypes.c_ulonglong

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ('dx', ctypes.c_long), ('dy', ctypes.c_long),
        ('mouseData', ctypes.c_ulong), ('dwFlags', ctypes.c_ulong),
        ('time', ctypes.c_ulong), ('dwExtraInfo', ULONG_PTR)
    ]

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ('wVk', ctypes.c_ushort), ('wScan', ctypes.c_ushort),
        ('dwFlags', ctypes.c_ulong), ('time', ctypes.c_ulong),
        ('dwExtraInfo', ULONG_PTR)
    ]

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [('uMsg', ctypes.c_ulong), ('wParamL', ctypes.c_short), ('wParamH', ctypes.c_ushort)]

class INPUT_UNION(ctypes.Union):
    _fields_ = [('mi', MOUSEINPUT), ('ki', KEYBDINPUT), ('hi', HARDWAREINPUT)]

class INPUT(ctypes.Structure):
    _fields_ = [('type', ctypes.c_ulong), ('u', INPUT_UNION)]

def _set_clipboard_text(text: str) -> bool:
    try:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        kernel32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
        kernel32.GlobalAlloc.restype = ctypes.c_void_p
        kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
        kernel32.GlobalLock.restype = ctypes.c_void_p
        kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
        user32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]
        user32.SetClipboardData.restype = ctypes.c_void_p

        CF_UNICODETEXT = 13
        GMEM_MOVEABLE = 0x0002
        if not user32.OpenClipboard(0):
            return False
        user32.EmptyClipboard()
        encoded = text.encode("utf-16le") + b"\x00\x00"
        h_mem = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(encoded))
        if not h_mem:
            user32.CloseClipboard()
            return False
        p_mem = kernel32.GlobalLock(h_mem)
        if p_mem:
            ctypes.memmove(p_mem, encoded, len(encoded))
            kernel32.GlobalUnlock(h_mem)
            user32.SetClipboardData(CF_UNICODETEXT, h_mem)
        user32.CloseClipboard()
        return True
    except Exception:
        try:
            ctypes.windll.user32.CloseClipboard()
        except Exception:
            pass
        return False

def _send_unicode_text(text: str):
    u32 = ctypes.windll.user32
    u32.SendInput.argtypes = [ctypes.c_uint, ctypes.POINTER(INPUT), ctypes.c_int]
    u32.SendInput.restype = ctypes.c_uint
    KEYEVENTF_KEYUP = 0x0002
    KEYEVENTF_UNICODE = 0x0004
    for ch in text:
        code = ord(ch)
        if code in (10, 13):
            d = INPUT(type=1, u=INPUT_UNION(ki=KEYBDINPUT(wVk=0x0D, wScan=0, dwFlags=0, time=0, dwExtraInfo=0)))
            u = INPUT(type=1, u=INPUT_UNION(ki=KEYBDINPUT(wVk=0x0D, wScan=0, dwFlags=KEYEVENTF_KEYUP, time=0, dwExtraInfo=0)))
        else:
            d = INPUT(type=1, u=INPUT_UNION(ki=KEYBDINPUT(wVk=0, wScan=code, dwFlags=KEYEVENTF_UNICODE, time=0, dwExtraInfo=0)))
            u = INPUT(type=1, u=INPUT_UNION(ki=KEYBDINPUT(wVk=0, wScan=code, dwFlags=KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, time=0, dwExtraInfo=0)))
        u32.SendInput(1, ctypes.byref(d), ctypes.sizeof(INPUT))
        time.sleep(0.005)
        u32.SendInput(1, ctypes.byref(u), ctypes.sizeof(INPUT))
        time.sleep(0.005)

@app.post("/api/screen/key")
def handle_screen_key(req: KeyEventRequest, x_auth_token: Optional[str] = Header(None)):
    global _promoted_hwnd
    verify_token(x_auth_token)
    u32 = ctypes.windll.user32
    act = req.action.lower()

    _attach_to_input_desktop(force_default=False)

    if act == "text" and req.text:
        # 雙軌並行超高可靠度文字注入：
        # 1. 優先透過 Win32 64-bit 原生剪貼簿注入 + Ctrl+V (完美支援任意中英文長字串、標點符號與多行內容)
        pasted = False
        try:
            if _set_clipboard_text(req.text):
                time.sleep(0.03)
                _combo_vk(0x11, 0x56)  # Ctrl + V
                pasted = True
        except Exception:
            pasted = False

        # 2. 若剪貼簿失敗則無縫降級為 SendInput KEYEVENTF_UNICODE 保底
        if not pasted:
            _send_unicode_text(req.text)
        return {"status": "ok", "typed": req.text, "mode": "clipboard" if pasted else "sendinput"}

    elif act == "combo":
        c = req.key.lower()
        if c == "ctrl+c": _combo_vk(0x11, 0x43)
        elif c == "ctrl+v": _combo_vk(0x11, 0x56)
        elif c == "ctrl+a": _combo_vk(0x11, 0x41)
        elif c == "ctrl+z": _combo_vk(0x11, 0x5A)
        elif c == "ctrl+s": _combo_vk(0x11, 0x53)
        elif c == "ctrl+w": _combo_vk(0x11, 0x57)
        elif c == "alt+tab": _combo_vk(0x12, 0x09)
        elif c == "win+d": _combo_vk(0x5B, 0x44)
        elif c == "alt+f4": _combo_vk(0x12, 0x73)
        return {"status": "ok", "combo": c}

    else:
        k = req.key.lower()
        if k in VK_MAP:
            _tap_vk(VK_MAP[k])
        elif len(k) == 1:
            _send_unicode_text(req.key)
        return {"status": "ok", "key": req.key}

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
