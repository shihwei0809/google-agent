---
name: hr-rules-training-manager
description: 協助使用者初始化與部署「員工工作規則教育訓練與測驗系統」
---

# 員工工作規則教育訓練與測驗系統 (hr_quiz_v2) 管理技能

本專案是新進員工的工作規則教育訓練與測驗系統，支援投影片朗讀播放、自動配音與測驗結果回寫。

## 🛠️ 環境依賴需求
1. **Python 3**：用於執行 `update_project_files.py` 以繪製投影片圖片及生成 edge-tts 語音旁白。
   - 依賴套件：`Pillow`、`edge-tts`
2. **Node.js (npm)**：用於安裝 `netlify-cli` 進行線上網址部署。
   - 部署工具：`netlify-cli`（全域安裝）

## 🚀 AI 助理執行指引
1. **環境檢查**：
   - 檢查系統中是否已安裝 Python，若有，請確認是否安裝了 `Pillow` 與 `edge-tts`。
   - 檢查是否已安裝 Node.js，以及是否全域安裝了 `netlify` 部署指令。
   - 若環境不全，請建議使用者執行 `powershell -ExecutionPolicy Bypass -File setup_env.ps1`。
2. **生成資源與語音**：
   - 執行 `update_project_files.py` 重新生成圖片與旁白 MP3 檔：
     ```powershell
     $env:PYTHONIOENCODING="utf-8"; python update_project_files.py
     ```
3. **線上發佈與部署**：
   - 本專案已整合於傳送門大廳中。要更新發佈，回到最外層 `C:\GOOGLE ANGET` 目錄，執行 `python build_portal.py` 後再部署大廳：
     ```powershell
     npx netlify deploy --site=20de222c-ed8e-4fa9-8ab3-84682b0efb41 --dir=說明書 --prod
     ```
