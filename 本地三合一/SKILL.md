---
name: tsmc-3in1-coa-verifier
description: 專門維護與部署「台積三合一單與 COA 雙重核對系統」之 AI 代理指南
---

# AI 代理作業指南 (tsmc-3in1-coa-verifier)

## 專案概述
- **專案名稱**：台積三合一單與 COA 雙重核對系統 (GAS 雲端智慧辨識版)
- **專案目錄**：`c:\GOOGLE ANGET\本地三合一`
- **技術棧**：Google Apps Script (JavaScript), HTML5, Tailwind CSS, html5-qrcode, Google Cloud Vision API, Google Gemini API, python-docx, pywin32

## 核心核對邏輯重點
1. **輸入三要素**：QR Code 資訊、COA 照片、地磅照片。
2. **四大關卡卡控**：
   - 關卡 1 (COA 批號)：`advancedFuzzyCheck(ocrTextBatch, targetBatch)`
   - 關卡 2 (地點)：`smartLocationCheck(ocrTextLoc, targetPlace)` 拆分前 4 碼與後 4 碼同時相符
   - 關卡 3 (槽號)：先自文字抽離批號避免干擾，再比對槽號
   - 關卡 4 (地磅批號)：地磅畫面顯示之批號比對
3. **手冊生成指令**：
   - 執行 `python build_manual_doc.py` 產出 Word (.docx) 與 PDF (.pdf)。
