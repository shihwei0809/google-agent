---
name: IPA專用動態生產排程GAS專案
description: |
  這是一個 Google Apps Script (GAS) 專案，用於 IPA 生產排程與進耗存追蹤，並包含船隻位置查詢功能。
  請使用 clasp 來拉取 (clone) 與推送 (push) 程式碼。
---

# IPA 專用動態生產排程 GAS 專案

## 技能與環境設定指南

這個專案是在 Google Apps Script 環境中執行的。為了要在本機進行開發與版本控制，我們使用 `@google/clasp`。

### 依賴環境
*   **Node.js** (建議 LTS 版本)
*   **npm套件**: `@google/clasp`

### 首次設定步驟
1. 執行 `setup_env.ps1` 自動安裝 Node.js 與 clasp。
2. 開啟 PowerShell，輸入 `clasp login` 完成 Google 帳號授權。
3. 取得專案的 Script ID 後，在 `src` 目錄下執行 `clasp clone <Script_ID>`。

### 日常開發指令
*   **上傳/推送程式碼**: `clasp push`
*   **下載/拉取最新程式碼**: `clasp pull`
*   **在瀏覽器中開啟專案**: `clasp open`
