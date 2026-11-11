# QC 檢驗超時排程服務 (QC Overdue Cron Trigger)

## 專案概要
- **名稱**：QC Overdue Cron Trigger
- **用途**：透過 Cloudflare Workers 原生 Cron 觸發器每 5 分鐘主動檢查一次 QC 樣品超時狀況，自動發送 Teams 警報卡片。
- **目標端點**：`https://qc-samples.pages.dev/api?action=checkOverdue`

## 依賴環境與憑證
- Python 3.10+
- 根目錄 `.env` 中的 `CLOUDFLARE_API_TOKEN` 與 `CLOUDFLARE_ACCOUNT_ID`

## 執行與部署指令
```powershell
python deploy_cron.py
```
