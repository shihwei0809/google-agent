# AI 面試語音特質與資材適性分析系統 (interview_analyzer)

## 專案簡介
本專案為針對 HR 人資與資材主管設計的 AI 語音特質分析系統，具備以下核心能力：
1. **長面試背景自動備份 (Chunked Auto-Save)**：預設每 5 分鐘背景分段備份，防止斷電失誤與面試結束等待。
2. **資材部黃金 DISC 比對**：針對現場助理工程師、資材工程師與資材行政自動做 CS/SC 型特質評估。
3. **多 Key 自動輪替與 Cascade 降階**：支援貼入多組 Gemini API Key，自動切換 Gemini 3.6-flash -> 3.5-flash。
4. **一鍵導出 Word (.docx) 評估報告**：內含排版表格、DISC 對照表與 Big Five 量化圖表。

## 執行與安裝方法
- **一鍵啟動**：雙擊執行 `雙擊點我啟動面試語音AI分析系統.bat` 或在 Powershell 執行 `./setup_env.ps1`。
- **網址**：`http://localhost:8000`
