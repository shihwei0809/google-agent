# Clasp + Netlify 部署指南 - 操作說明書

> 🔗 **GitHub 專案庫**：[mathruffian-dot/clasp-netlify-mcp-guide](https://github.com/mathruffian-dot/clasp-netlify-mcp-guide)


## 專案簡介
本專案提供標準安裝與部署指南，指導 AI Agent 如何將網頁前端自動部署至 Netlify，並將後端 Apps Script 透過 Google clasp 工具同步，實現無縫的雲端備份與部署。

## 主要功能特色
- **自動化 clasp 設定**：包含 `.clasp.json` 設定範例，防範 AI 部署權限錯誤。
- **Netlify CLI 自動發布**：提供一鍵建置前端並發布至 Netlify 託管空間的腳本。

## 技術棧
- Node.js, @google/clasp, Netlify CLI

## 操作步驟
1. 參考說明書中的命令，安裝並登入 clasp：
   ```bash
   npm install -g @google/clasp
   clasp login
   ```
2. 執行 `clasp push` 將 GAS 代碼推送到雲端試算表。
3. 執行 `netlify deploy --prod` 發布前端網頁。
