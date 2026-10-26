@echo off
chcp 65001 >nul
echo 正在連線公司電腦 RDP...
start mstsc /v:localhost:3389
cloudflared.exe access rdp --hostname arthur-artistic-enrolled-fee.trycloudflare.com --url localhost:3389
