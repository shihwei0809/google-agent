---
name: agilent-gc-lc-viewer
description: Agilent GC/LC chromatography data (.ch/.D) binary parser, web interactive viewer, peak area calculator, and CSV/Excel exporter.
---

# Agilent GC/LC Data Viewer Agent Guide

## 專案簡介
本子專案提供跨電腦無原廠授權環境下解析與檢視 Agilent 氣相/液相層析儀 (`.ch` / `.D`) 數據的完整解決方案。

## 依賴環境
- Python 3.8+
- FastAPI, uvicorn
- numpy, pandas, openpyxl

## 核心指令
- 一鍵啟動：`.\點我啟動Agilent數據解析器.bat`
- 手動啟動：`python main.py`
- 環境建置：`powershell -ExecutionPolicy Bypass -File .\setup_env.ps1`
