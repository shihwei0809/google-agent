---
name: tsmc-lorry-barcode-server
description: 台積電槽車 Barcode 三合一單與運輸通知表架機專用伺服器
---

# 台積電槽車 Barcode 三合一單網頁架機伺服器 AI 維護指南

## 專案概述
本專案為 FastAPI 架機伺服器，託管在 C:\GOOGLE ANGET\三合一單網頁架機伺服器\。
前端透過 SPA (static/index.html) 提供使用者操作介面，後端 server.py 負責處理 Excel 生成、QR Code 繪製、COA 裁切與 ZIP 打包。

## 依賴環境與套件
- Python 3.8+
- 必要套件：astapi, uvicorn, openpyxl, qrcode, pillow
- 前端 CDN：SheetJS (xlsx.full.min.js), Tesseract.js (	esseract.min.js)

## AI 行為與修改維護守則
1. **OCR 方案限制**：目標環境封鎖本地 	esseract.exe，因此 OCR 辨識完全在前端瀏覽器透過 Tesseract.js 執行，後端 server.py 僅接收座標 (ocr_data) 進行純 Pillow 影像裁切，切勿擅自在後端引入需要本地 binary 的 OCR 套件。
2. **COA 裁切原則**：
   - 必須裁切出：上方【單行表頭】+【該批號專屬數據列】。
   - 表頭底線必須位於第一筆批號上方。
   - 裁切後圖片等比例縮放嵌入三合一單 F5 儲存格，不可失真或破壞解析度。
3. **Port 佔用與 IP 顯示**：
   - 啟動時必須調用 ind_available_port(8002) 自動切換可用 Port。
   - 必須透過 get_local_ip() 顯示實體區網 IP 供現場連線。
4. **啟動指令**：
   - PowerShell / CMD：python server.py 或執行 架設伺服器_一鍵啟動.bat。
