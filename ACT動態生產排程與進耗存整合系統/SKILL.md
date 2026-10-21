---
name: act-production-planner
description: ACT 動態生產排程與進耗存整合系統 (Cloudflare 邊緣版 + Google Sheets 雲端資料庫)
---

# ACT 動態生產排程與進耗存整合系統 AI 指南

## 專案概要
- **前端平台**：Cloudflare Pages (`https://act-planner-pwa.pages.dev`)
- **後端資料庫**：Google Sheets (透過 Google Apps Script `doPost` 提供跨網域 JSON API)
- **實體路徑**：`C:\GOOGLE ANGET\ACT動態生產排程與進耗存整合系統`

## 常用操作與功能亮點
1. **重新部署網頁**：執行 `C:\GOOGLE ANGET\ACT動態生產排程與進耗存整合系統\一鍵部署至Cloudflare.bat`。
2. **更換 Google 試算表連線**：修改 `public/index.html` 中的 `GAS_API_URL` 常數。
3. **儲槽容量上限與總滿位計算**：各儲槽獨立顯示與自訂容量上限（如 TK623 125T），頂部即時統計「儲槽滿位 + 槽車滿位 = 總滿位」。
4. **槽車存量納入期初總成品**：支援「槽車存量」與「其他庫存量」輸入，100% 正確計入「總計期初成品」並作為進耗存首日推演基礎。
5. **雙階庫存容量預警**：超過實體儲槽時黃底警示（需調用槽車），超過儲槽與槽車總滿位時紅底高亮警示。
