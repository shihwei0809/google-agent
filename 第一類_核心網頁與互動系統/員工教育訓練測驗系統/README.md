# 📝 員工教育訓練測驗系統 模組群 (Employee Training & Quiz System Hub)

> 🔗 **GitHub 路徑**：[google-agent / 第一類\_核心網頁與互動系統 / 員工教育訓練測驗系統](https://github.com/shihwei0809/google-agent/tree/main/%E7%AC%AC%E4%B8%80%E9%A1%9E_%E6%A0%B8%E5%BF%83%E7%B6%B2%E9%A0%81%E8%88%87%E4%BA%92%E5%8B%95%E7%B3%BB%E7%B5%B1/%E5%93%A1%E5%B7%A5%E6%95%99%E8%82%B2%E8%A8%93%E7%B7%B4%E6%B8%AC%E9%A9%97%E7%B3%BB%E7%B5%B1)

本資料夾匯集所有與**「廠區 SOP 教育訓練、互動式簡報生成、測驗試題與成績自動紀錄」**相關的系統模組。

---

## 📁 子專案一覽

| 專案名稱 | 說明簡述 | 主要技術 |
|---|---|---|
| 📝 [hr_quiz_v2](./hr_quiz_v2/) | 通用型 SOP 員工教育訓練與測驗系統（本機優先版）。支援圖形化題庫管理、微軟 TTS 語音朗讀、作答結果寫入 CSV 與成績防刷機制。 | HTML5, CSS3, JS, 微軟 TTS, Apps Script |
| 🎈 [nitrogen_quiz](./nitrogen_quiz/) | 氮封閥與安全防爆專題教育訓練測驗系統。結合 P&ID 互動式簡報與測驗。 | HTML5, Web Audio, JS, SVG |
| 🛠️ [sop_generator](./sop_generator/) | 廠區標準作業程序 (SOP) 試題與測驗自動生成器。 | Python, Jinja2, HTML5 |
| 🎨 [sop_interactive_builder](./sop_interactive_builder/) | 互動式 SOP 簡報與題目建置工具。支援 PPTX 解析與範本導出。 | Python, python-pptx, WebUI |
| 📦 [倉庫原料、物料及桶裝製成品作業管理辦法_教育訓練測驗套件](./倉庫原料、物料及桶裝製成品作業管理辦法_教育訓練測驗套件/) | 倉庫物流與原料管理辦法專屬 SOP 教育訓練講義與評量測驗套件。 | HTML5, CSS3, JS |

---

## 🚀 啟動方式

- ⚡ **雙擊執行**：資料夾內的 `點我啟動教育訓練產生器.bat`
- 📖 各專案單獨說明書可參考各子資料夾內的 `README.md` 或 `操作說明書.md`。
