---
name: 倉儲儲位 PWA 記錄系統
description: 手機 PWA 選擇儲位、批號與數量，即時無損回寫 崙尾倉儲儲位表.xlsm 與 鴻勝儲位表.xlsm，並統計每日板數與各批號核對量。
---

# 倉儲儲位 PWA 記錄系統 - AI 助理指南

## 環境與依賴
- **Python 3.9+**
- **套件**：`fastapi`, `uvicorn`, `pydantic`, `openpyxl`, `lxml`, `python-docx`
- **一鍵初始化**：`powershell -ExecutionPolicy Bypass -File setup_env.ps1`

## 啟動與測試指令
- **一鍵啟動（建議）**：雙擊或執行 `2_PWA_App版\啟動PWA儲位系統.bat`
- **手動啟動**：
  ```powershell
  cd "c:\GOOGLE ANGET\儲位記錄\2_PWA_App版"
  python run_server.py
  ```
- **產出操作手冊**：
  ```powershell
  python build_manual_doc.py
  ```

## 核心架構重點（維護必讀）
1. **絕對不可用 `openpyxl.load_workbook(..., keep_vba=True)` 直接覆寫 `鴻勝儲位表.xlsm`**：該檔 drawing XML 的 `pitchFamily` 屬性會觸發 `openpyxl` `Max value is 52` 驗證錯誤，且 `openpyxl` 會移除 `x14:dataValidations`。
2. **請維持 `2_PWA_App版/excel_engine.py` 的 Surgical XML/ZIP 寫入機制**：僅修改總表（`崙尾倉儲儲位表_總表202208` / `倉庫總表`）的 C~H 欄儲存格，保留 C 欄 VLOOKUP `<f>` 公式與所有巨集、圖表、分區儲位表，並開啟 `fullCalcOnLoad="1"`。
3. **每日對帳統計**：儲存於 `2_PWA_App版/data/daily_logs.json`，API 支援依日期查詢總板數與依批號彙整核對，並可匯出 UTF-8 BOM CSV。
