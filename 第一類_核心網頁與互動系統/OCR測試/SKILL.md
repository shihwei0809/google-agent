---
name: ocr-to-excel-manager
description: 協助使用者初始化與運行「AI 圖片智慧判讀轉 Excel 系統」環境
---

# AI 圖片智慧判讀轉 Excel 系統 (OCR to Excel) 專案管理技能

本專案提供高精度的本機圖片 OCR 判讀與自動轉 Excel 報表服務。

## 🛠️ 環境依賴需求
1. **Python 3.9+**：核心運算與 FastAPI 伺服器。
2. **依賴套件**：
   - `fastapi`, `uvicorn`, `python-multipart`
   - `easyocr` (繁體中文 + 英文離線模型)
   - `openpyxl` (商務 Excel 報表生成)
   - `Pillow` (影像讀取與標註圖繪製)
   - `pymupdf` (PDF 轉影像)
   - `opencv-python` (圖像處理)

## 🚀 AI 助理執行指引
1. **環境檢查與初始化**：
   - 若人員環境缺少套件，可執行 `powershell -ExecutionPolicy Bypass -File setup_env.ps1`。
2. **服務啟動**：
   - 啟動主服務：執行 `run_web_app.bat` 或在終端機執行 `python ocr_web_app.py`。
   - 伺服器啟動後會在 `http://localhost:8000`（或自動 Fallback 之 Port）提供服務。
3. **功能更新規範**：
   - 當修改表格聚類演算法或 Excel 樣式時，同步確認 `web_index.html` 之互動式預覽功能。
