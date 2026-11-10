---
name: ocr-to-excel-manager
description: 協助使用者初始化與運行「AI 圖片/PDF 雙重 OCR 智慧判讀轉 Excel 系統」環境
---

# AI 圖片/PDF 雙重 OCR 智慧判讀轉 Excel 系統 專案管理技能

本專案提供雙重架構的高精度圖片與 PDF 表格 OCR 判讀服務：
1. **Google Gemini 雲端高精準度引擎**（優先）：當有 Google API Key 時優先調用，支援手寫、旋轉與複雜表格還原。
2. **本機 EasyOCR 雙語引擎**（自動備援）：當無金鑰、離線或雲端繁忙時自動無縫接手，完全不依賴外網。

## 🛠️ 環境依賴需求
1. **Python 3.9+**：核心運算與 FastAPI 伺服器。
2. **依賴套件**：
   - `google-genai` (Google Gemini 雲端多模態 OCR)
   - `easyocr` (繁體中文 + 英文離線模型)
   - `openpyxl` (商務 Excel 報表生成)
   - `Pillow` (影像讀取與標註圖繪製)
   - `pymupdf` (PDF 轉影像與逐頁解析)
   - `fastapi`, `uvicorn`, `python-multipart`

## 🚀 AI 助理執行指引
1. **環境檢查與初始化**：
   - 若人員環境缺少套件，可執行 `powershell -ExecutionPolicy Bypass -File setup_env.ps1`。
2. **服務啟動**：
   - 啟動主服務：執行 `run_web_app.bat`。
   - 伺服器啟動後會在 `http://localhost:8000`（或自動 Fallback 之 Port）自動開啟瀏覽器。
3. **雙重金鑰機制**：
   - 系統後端支援讀取專案 `.env` 中的 `GEMINI_API_KEY`。
   - 前端網頁支援動態輸入金鑰並儲存至瀏覽器 `localStorage`。
