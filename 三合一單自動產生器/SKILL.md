---
name: 三合一單自動產生器
description: 提供生成台積電槽車Barcode三合一單與運輸通知表的桌面自動化工具。包含高畫質 COA 截圖 AI 裁切辨識、雙引擎多檔匯入功能。
---

# 三合一單自動產生器與運輸通知表

## 環境依賴
- **Python 套件**: openpyxl, qrcode, Pillow, pytesseract, python-docx
- **外部系統依賴**: [Tesseract OCR Windows 64-bit](https://github.com/UB-Mannheim/tesseract/wiki) (預設安裝路徑 C:\Program Files\Tesseract-OCR\tesseract.exe)
- **啟動腳本**: 啟動_三合一單產生器.bat 具備自動安裝上述 pip 套件之功能。

## 開發與修改規範 (AI 注意事項)
- **OCR 裁切邊距**: 若使用者反應 COA 圖片裁切有殘影或被切到，請調整 main.py 內的 header_bottom, 
ow_top, 
ow_bottom 像素增減值。目前系統採用 LANCZOS 2x 放大技術處理，請注意座標換算。
- **匯入邏輯**: import_from_excel 已實作雙引擎 (橫向表格與直向 Key-Value CSV)，若遇到無法匯入的格式，請優先檢查該迴圈內的 is_vertical_csv 判定邏輯。
- **文檔同步**: 若修改了核心功能，請務必同時更新 README.md，以符合專案開發規範。
