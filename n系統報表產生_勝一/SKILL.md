---
name: n-series-report-generator-shengyi
description: N系列報表輸出系統 (勝一專用版) - 生產履歷與 COA 自動化報表產出系統
---

# 🤖 N系列報表輸出系統 (勝一專用版) - AI 代理指引

## 專案定位
本專案為「N系列報表輸出系統」的**勝一專用獨立版本**，從原系統獨立複製建立，後續勝一之專屬操作流程、排程欄位、對照表結構與輸出格式在此目錄進行客製化修改，**嚴禁影響原鴻勝版 (`c:\GOOGLE ANGET\n系統報表產生\`)**。

## 環境依賴
- **Python**: 3.9+
- **必要套件**:
  - `openpyxl`
  - `Pillow`
  - `qrcode`
  - `pytesseract`
  - `python-docx` (手冊生成專用)

## 啟動與維護指令
1. **啟動主程式**：
   ```powershell
   python main.py
   ```
   或直接執行 `啟動本機視窗版.bat`。

2. **環境初始化**：
   ```powershell
   .\setup_env.ps1
   ```

3. **語法編譯檢查**：
   ```powershell
   python -m py_compile main.py
   ```

## 開發維護注意事項
- **獨立更新網址**：`一鍵更新系統程式.bat` 下載點必須指向 `shihwei0809/google-agent/main/n%E7%B3%BB%E7%B5%B1%E5%A0%B1%E8%A1%A8%E7%94%A2%E7%94%9F_%E5%8B%9D%E4%B8%80/main.py`。
- **認列不認批號**：維持每筆排程獨立建單與檔案序號防覆蓋機制。
- **對照表依賴**：本地依賴 `N系料小包-地點代號對照表.xlsx`，若勝一有專屬廠區或料號對照，需於此 Excel 中維護。
