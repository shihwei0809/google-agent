---
name: act-production-planner
description: ACT 動態生產排程與進耗存整合系統 (Cloudflare 邊緣版 + Google Sheets 雲端資料庫)
---

# ACT 動態生產排程與進耗存整合系統 AI 指南

## 專案概要
- **前端平台**：Cloudflare Pages (`https://act-planner-pwa.pages.dev`)
- **後端資料庫**：Google Sheets (透過 Google Apps Script `doPost` 提供跨網域 JSON API)
- **實體路徑**：`C:\GOOGLE ANGET\ACT動態生產排程與進耗存整合系統`

## 常用操作
1. **重新部署網頁**：執行 `C:\GOOGLE ANGET\ACT動態生產排程與進耗存整合系統\一鍵部署至Cloudflare.bat`。
2. **更換 Google 試算表連線**：修改 `public/index.html` 中的 `GAS_API_URL` 常數。
