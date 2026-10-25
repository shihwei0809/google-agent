import subprocess
import time
import re
import os
import sys

# Ensure utf-8 output
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

base_dir = os.path.dirname(os.path.abspath(__file__))
cf_exe = os.path.join(base_dir, "cloudflared.exe")
if not os.path.exists(cf_exe):
    cf_exe = "cloudflared.exe"

print("============================================================")
print("  正在啟動 Cloudflare HTTPS 443 專屬穿透 (微軟原生 RDP 模式)")
print("============================================================")
print("")
print("[*] 正在建立安全加密隧道 (連線埠 3389)...")

p = subprocess.Popen([cf_exe, "tunnel", "--url", "rdp://localhost:3389"], stderr=subprocess.PIPE, text=True, bufsize=1, encoding="utf-8", errors="ignore")

url = None
while True:
    line = p.stderr.readline()
    if not line:
        break
    if "trycloudflare.com" in line:
        m = re.search(r"https://([a-zA-Z0-9-]+\.trycloudflare\.com)", line)
        if m:
            host = m.group(1)
            print("")
            print("============================================================")
            print("  [OK] RDP 穿透連線已成功建立！(完全偽裝為 443 HTTPS，絕不被擋)")
            print("============================================================")
            print("")
            print("【筆電端連線指令】請在筆電複製並執行以下指令：")
            print(f"cloudflared.exe access rdp --hostname {host} --url localhost:3389")
            print("")
            print("【筆電遠端桌面開啟】")
            print("1. 按 Win + R 輸入 mstsc 並按 Enter")
            print("2. 電腦名稱填寫: localhost:3389")
            print("3. 輸入本機的 Windows 帳號密碼即可進入原生桌面！")
            print("============================================================")
            print("(請保持此視窗開啟，關閉即斷線)")
            print("")

            # 儲存筆電一鍵連線腳本
            bat_content = f"@echo off\r\nchcp 65001 >nul\r\necho 正在連線公司電腦 RDP...\r\nstart mstsc /v:localhost:3389\r\ncloudflared.exe access rdp --hostname {host} --url localhost:3389\r\n"
            with open(os.path.join(base_dir, "筆電端一鍵連線.bat"), "w", encoding="utf-8") as bf:
                bf.write(bat_content)
            with open(os.path.join(base_dir, "最新RDP穿透網址.txt"), "w", encoding="utf-8") as uf:
                uf.write(f"主機: {host}\n指令: cloudflared.exe access rdp --hostname {host} --url localhost:3389\n")
            break

# 保持進程運作
p.wait()
