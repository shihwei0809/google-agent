---
name: HTTPS 遠端網頁穿透中心
description: 穿透企業防火牆對遠端桌面與UDP協定的阻擋，透過純HTTPS (Port 443)邊緣網路提供跨裝置遠端操作、終端執行與檔案管理介面。
---

# HTTPS 遠端網頁穿透中心 (SKILL)

## 專案概述
本專案專為解決公司內部網路封鎖特定協定（如 STUN UDP 19302、Chrome Remote Desktop、AnyDesk）而設計。利用 Cloudflare HTTP/2 邊緣通道，將本機管理伺服器安全映射為全域 HTTPS 網址。

## 依賴環境
- Python 3.9+
- 套件：`fastapi`, `uvicorn`, `pydantic`, `python-multipart`
- 穿透核心：`d:\GOOGLE ANGET\cloudflared.exe` (使用 HTTP/2 純 TCP 443 協定)

## 常用操作指引
1. **環境檢查與初始化**:
   - 執行 `setup_env.ps1` 確保套件完整。
2. **啟動主服務**:
   - 執行 `python main.py` 或雙擊 `啟動HTTPS遠端穿透.bat`。
   - 讀取 `public_url.txt` 可取得最新的公網連線網址。
3. **安全防護**:
   - 預設存取密碼為 `c606admin`，可透過環境變數 `REMOTE_HUB_PWD` 自訂。
