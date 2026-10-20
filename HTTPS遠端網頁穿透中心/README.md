# 🌐 HTTPS 遠端網頁穿透中心 (HTTPS Remote Web Penetration Hub)

專為應對企業硬體防火牆阻擋（如封鎖 UDP 19302 STUN 協定、阻擋遠端桌面連線）而設計的**免安裝、純 HTTPS (Port 443) 網頁穿透管理系統**。

## 🌟 核心功能亮點
1. **純 443 埠 HTTPS 出口穿透**：透過 Cloudflare 專用 HTTP/2 邊緣通道直連，100% 避開公司防火牆對 UDP / STUN 的攔截，任何外網環境皆可順暢連入。
2. **免安裝用戶端 (跨裝置)**：手機、平板、家用電腦無需安裝任何軟體，直接以瀏覽器開啟專屬 HTTPS 網址即可登入操作。
3. **安全金鑰防護 (Token Auth)**：預設密碼驗證機制，防止公網未授權存取。
4. **線上即時終端 (Interactive Web Terminal)**：提供標準 PowerShell / CMD 執行介面，支援即時指令、Git 開工/收工同步、服務管理。
5. **視覺化專案檔案總管 (File Explorer & Editor)**：支援跨專案瀏覽、程式碼線上預覽、檔案下載與即時編輯儲存。
6. **Windows 原生 RDP 穿透支援**：完整保留 Port 3389 連線指引，支援透過 Cloudflare Access 直接連入完整 Windows GUI 桌面。

---

## 📁 完整檔案結構 (File Tree)
```text
HTTPS遠端網頁穿透中心/
├── main.py                  # FastAPI 核心伺服器與 Cloudflare Tunnel 自動封裝
├── requirements.txt         # 依賴套件清單 (fastapi, uvicorn, pydantic, multipart)
├── README.md                # 本說明書 (人類閱讀)
├── SKILL.md                 # AI 代理標準技能說明書
├── setup_env.ps1            # 一鍵安裝與依賴檢查腳本
├── 啟動HTTPS遠端穿透.bat     # 一鍵自動啟動器 (自動偵測可用 Port 與公網網址)
└── static/
    └── index.html           # 科技感響應式 Web 控制中心前端介面
```

---

## ⚡ 啟動與執行方式

### 方式一：一鍵啟動（最推薦）
雙擊執行 `啟動HTTPS遠端穿透.bat`，系統將自動：
1. 檢查 Python 與必要套件
2. 自動尋找可用 Port (8800+)
3. 建立 Cloudflare HTTPS 穿透通道
4. 自動複製專屬公網網址並開啟瀏覽器

### 方式二：手動指令啟動
```powershell
python main.py
```
啟動後終端機將顯示：
```text
🚀 Cloudflare HTTPS 線上專屬入口已成功生成！
🌐 公網專屬網址: https://xxxx-xxxx-xxxx.trycloudflare.com
🔑 預設登入密碼: c606admin
```
