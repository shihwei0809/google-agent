# ⏰ QC 檢驗超時 24/7 背景排程 Worker (Cloudflare Workers Cron Trigger)

本專案為「鴻勝化學 QC 樣品即時管理系統」的雲端定時排程服務，部署於 Cloudflare Workers，具備 24/7/365 全天候自動觸發機制。

---

## 核心功能亮點

- **全天候 24/7 自動排程**：透過 Cloudflare Workers 原生 Cron Trigger，每 5 分鐘自動執行一次，完全不依賴任何瀏覽器或使用者打開網頁。
- **即時超時偵測**：自動呼叫 `https://qc-samples.pages.dev/api?action=checkOverdue`，精準計算樣品等待時間。
  - **滿 2 小時**：推送第 1 階段警告至 Teams（主管群與送樣單位）。
  - **滿 4 小時**：推送第 2 階段嚴重超時警告至 Teams。
- **手動測試支援**：同時開放 HTTPS 存取端點（`https://qc-overdue-cron.shihwei0809.workers.dev`），點擊即可立即手動觸發一次檢查。

---

## 完整檔案結構說明

```text
cron_worker/
├── README.md                          # 本說明書
├── SKILL.md                           # AI 助理操作規範與環境指導
├── setup_env.ps1                      # 環境檢查與部署腳本
├── worker.js                          # Cloudflare Worker 程式碼 (Fetch + Scheduled)
├── deploy_cron.py                     # 透過 Cloudflare REST API 自動部署排程腳本
└── 一鍵部署定時排程Worker.bat           # Windows 一鍵部署與更新批次檔
```

---

## 一鍵部署與執行步驟

雙擊執行 `一鍵部署定時排程Worker.bat`，即可自動將最新 Worker 與排程規則部署至 Cloudflare。
