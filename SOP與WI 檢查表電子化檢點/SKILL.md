---
name: sop-wi-checklist-system
description: 鴻勝化學 C50110-INV-02-01 (6.1~6.5) SOP/WI 電子化檢點與模板改版系統（三軌架構：Web / PWA / Cloudflare D1）
---

# AI 助理操作指引

- **專案名稱**：SOP / WI 檢查表電子化檢點系統（v1.0.0）
- **來源文件**：`C50110-INV-02-01 儲槽進出貨作業方法(3.1版).doc`（附件 6.1～6.5）
- **環境需求**：
  - Python 3.9+（本機 PWA 測試伺服器與 `build_manual_doc.py` 需 `python-docx`、`pillow`）
  - Node.js + `wrangler` CLI（僅部署 `3_Cloudflare_D1版` 時需要）
- **執行指令**：
  - 初始化環境：`powershell -ExecutionPolicy Bypass -File setup_env.ps1`
  - 啟動本機 PWA 測試：`2_PWA_App版\啟動PWA本機測試.bat`
  - 生成操作手冊：`python build_manual_doc.py`
  - 部署雲端 D1：`3_Cloudflare_D1版\一鍵自動部署上雲端.bat`
- **開發注意事項**：
  - 修改前端邏輯時，請先更新 `1_Web_網頁版/` 後同步至 `2_PWA_App版/` 與 `3_Cloudflare_D1版/public/`。
  - D1 API 嚴禁整表 `DELETE + INSERT`，必須維持單列原子 UPSERT 與 `Asia/Taipei` 時間戳。
