---
name: ai-training-platform
description: AI 教育訓練平台專案開發與維護指引
---

# 🤖 AI 教育訓練平台技能指引 (SKILL)

## 專案概述
本專案為一個結合 React 前端與 FastAPI 後端的教育訓練平台。AI 代理在此專案中的主要任務是協助建置全端架構、串接 Gemini API 作為 AI 助教，並維護系統穩定性。

## 環境需求
*   **作業系統**: Windows (PowerShell)
*   **後端**: Python 3.10+, FastAPI, Uvicorn, google-generativeai
*   **前端**: Node.js 18+, React, Vite, Tailwind CSS

## 啟動與設定引導
當 AI 代理進入此專案時：
1. **檢查環境**：檢查 `backend/venv` 與 `frontend/node_modules` 是否存在。
2. **主動詢問**：若環境尚未建立，主動詢問使用者：「發現尚未安裝相關套件，是否要為您執行 `setup_env.ps1` 來一鍵配置環境？」
3. **啟動服務**：協助使用者啟動前後端服務，並確保 Port 不衝突。若預設 Port (8000/5173) 被佔用，應協助實作 Port Fallback 邏輯。

## 常見開發任務與指令
*   **安裝環境**: `.\setup_env.ps1`
*   **生成手冊**: `python build_manual_doc.py`
*   **後端啟動**: 進入 `backend` 目錄執行 `uvicorn main:app --reload --host 0.0.0.0 --port 8000`
*   **前端啟動**: 進入 `frontend` 目錄執行 `npm run dev`

## 注意事項
*   任何架構修改或新增 API，都必須同步更新此 `SKILL.md` 及 `README.md`。
*   使用者說「收工」時，必須嚴格遵守跨機 Git 分支邏輯進行備份與同步。
