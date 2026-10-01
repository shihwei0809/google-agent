# 製程流程圖 HANDOVER.md — 跨電腦交接日誌

## 最後更新：2026-09-30

---

## 本次進度摘要（2026-09-30）

### ✅ 完成項目

1. **備註卡片多行顯示修復**
   - SVG `<text>` 改用 `<tspan dy>` 逐行渲染
   - 背景 `<rect>` 自動依照行數與中英文混排寬度撐開
   - 換行符號由 `split('\\n')` 改為 `split(/\r?\n/)` 正確識別 Enter 換行

2. **AI 聊天（製程 AI 助手）全面升級**
   - 移除後端路由依賴，改為前端直接呼叫 Google Gemini API
   - 動態 ListModels 偵測可用模型，依版本號排序優先使用最新 Flash
   - 實作完整降級 Fallback（3.8→3.7→3.6→3.5→2.5→1.5）
   - 錯誤訊息直接顯示於對話框

3. **AI 設備建圖功能移除**
   - Gemini 圖像模型（Nano Banana 2 等）已不提供免費額度
   - 已徹底移除：工具列按鈕、Modal HTML、所有 JS 事件監聽

4. **中央大腦規則更新（INSTRUCTIONS.md）**
   - 新增第 10 條：Gemini Flash 模型版本規範（3.8→3.7→3.6 往下降）
   - Push 至 GitHub my-ai-brain

5. **安全性修復**
   - 將 `.wrangler/` 加入 `.gitignore`，避免 SQLite 中的 API Key 洩漏到 GitHub
   - 移除所有 `patch*.py`, `fix_*.js`, `temp*.js` 等暫存腳本的 Git 追蹤

---

## 目前系統架構

- **部署平台**：Cloudflare Pages（`製程流程圖/` 子目錄）
- **AI 功能**：純前端呼叫 Google Gemini API（不需要後端中轉）
- **API Key 儲存**：localStorage `chemflow_gemini_key`
- **目前分支**：`feat/20260930`（開發中，尚未合併 main）

## 下次開工待辦

- [ ] 測試備註卡片換行顯示是否正常（F12 清快取後）
- [ ] 測試 AI 聊天助手是否能正常回覆（需要 API Key）
- [ ] 確認 Service Worker 快取是否有自動更新
