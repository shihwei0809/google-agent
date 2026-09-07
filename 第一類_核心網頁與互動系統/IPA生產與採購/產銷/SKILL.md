---
name: sales-plan-pwa-system
description: 勝一化工產銷計畫 Web/PWA 雙軌系統操作與維護技能
---

# 勝一化工 產銷計畫 Web/PWA 雙軌系統

## 1. 專案位置
`d:\GOOGLE ANGET\第一類_核心網頁與互動系統\IPA生產與採購\產銷`

## 2. 核心架構
- `1_Web_網頁版/index.html`：純前端 React 18 + Tailwind CSS，支援離線單檔執行與 CSV 匯出。
- `2_PWA_App版/`：具備 `manifest.json`、`sw.js`、`icons/`，支援桌面安裝 (Chrome/Edge) 與手機主畫面 (Android/iOS)。
- `2_PWA_App版/run_server.py`：具備動態 Port 搜尋與區域網路實體 IP 提示之本機伺服器。
- `2_PWA_App版/build_manual_doc.py`：自動產出 Word (.docx) 與 PDF (.pdf) 操作手冊。

## 3. 核心公式
- 8/31 預估結存 = 08/24期初庫存 + 8月生產總量 - 08/24~08/31銷
- 9/30 預估結存 = 8/31庫存 + 9月生產總量 - 09/30銷
- 10/31 預估結存 = 9/30庫存 + 10月生產總量 - 10/31銷
- 11/30 預估結存 = 10/31庫存 + 11月生產總量 - 11/30銷

## 4. 啟動與測試指令
```powershell
# 啟動 PWA 本機測試伺服器
cd "d:\GOOGLE ANGET\第一類_核心網頁與互動系統\IPA生產與採購\產銷\2_PWA_App版"
python run_server.py

# 重新產出圖文手冊
python build_manual_doc.py
```
