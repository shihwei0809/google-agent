---
name: shinychem-ipahq-scheduler
description: 勝一化工槽車出貨排程管理、即時推播與台積電三合一單生成系統之 AI 代理指南
---

# AI 代理作業指南 (shinychem-ipahq-scheduler)

## 專案概述
- **專案名稱**：勝一出貨排程管理系統 (IPA HQ 槽車派車・技服・業務三方協同平台)
- **專案目錄**：c:\GOOGLE ANGET\IPAHQ排程
- **技術架構**：
  - **後端**：Node.js (Express), Web Push (VAPID), Server-Sent Events (SSE), localtunnel
  - **前端**：Vanilla JS (ES6+), PWA (Service Worker + Manifest), SSE 即時連動
  - **資料層**：database.json + 帳號密碼管理.xlsx 雙向鏡像同步
  - **單據產生器**：Python (generate_3in1.py + openpyxl + qrcode)
- **雲端部署目標**：Render (Dockerfile) + Cloudflare Tunnel (cloudflared.exe)

## 核心功能清單
1. **多角色登入與權限卡控**：
   - 系統管理員 (dmin, shihwei)、業務人員 (sales)、技服主管 (	ech_mgr)、運輸公司 (	ransporter)、技服人員 (29位姓名帳號)
2. **技服個人化排程查詢與即時已讀**：
   - 技服同仁登入後自動鎖定姓名，預設呈現「當天與明天」排程，可切換「之前歷史排程」與「全部日程」。
   - 開啟訂單即時標記已讀，後端 SSE 即時推播廣播給所有螢幕，桌機大表 0.1 秒內自動切換「🟢 已讀 (時間/姓名)」。
3. **推播通知 (Web Push)**：
   - 支援出車時間/地點/充填手變更自動推播通知，點擊直接聚焦單筆確認彈窗。
4. **台積電三合一條碼單一鍵下載**：
   - 自動查驗 9 碼地點代號，自動產出含 Barcode 之 Excel 派車單。

## 指令與維護指南
- **環境設定**：powershell -File setup_env.ps1
- **本機啟動**：執行 一鍵啟動系統.bat 或 
ode server.js
- **手冊產出**：執行 python build_manual_doc.py
