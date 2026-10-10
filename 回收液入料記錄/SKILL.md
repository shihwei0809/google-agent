---
name: 回收液入料記錄系統
description: 提供回收液入料前後的拍照與車號記錄，支援暫存與避免重複功能
---

# 回收液入料記錄系統 - SKILL

## 系統架構
本系統主要採用 FastAPI 作為後端，SQLite 作為本地暫存資料庫，並透過純 HTML/JS 實作前端 PWA 介面。

## 環境需求
- Python 3.9+
- FastAPI
- Uvicorn
- SQLite (內建)

## 啟動與部署
使用者若需要啟動系統，請引導執行 `2_PWA_App版` 內的 `啟動系統.bat` 或使用以下指令：
```bash
cd 2_PWA_App版
pip install -r requirements.txt
python main.py
```

## 功能邏輯說明
1. **入料前**：前端傳送車號、日期、入料前液位照片、車輛照片至 `/api/before_feed`，建立一筆 `status='pending'` 的紀錄。
2. **入料後**：前端從 `/api/pending_records` 取得清單，使用者選擇後，傳送入料後液位照片至 `/api/after_feed/{id}`，將該紀錄更新為 `status='completed'`。
