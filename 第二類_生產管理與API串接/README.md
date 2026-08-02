# ⚙️ 第二類：生產管理與 API 串接 (Production Management & API Integration)

> 🔗 **GitHub 路徑**：[google-agent / 第二類\_生產管理與API串接](https://github.com/shihwei0809/google-agent/tree/main/%E7%AC%AC%E4%BA%8C%E9%A1%9E_%E7%94%9F%E7%94%A2%E7%AE%17%E7%90%86%E8%88%87API%E4%B8%B2%E6%8E%A5)

本分類匯集所有**化工廠生產排程優化、儲槽與槽車條碼核對、QC 品質管制看板、GAS 遷移至 PHP/SQL 資料庫、以及設備溫度警報通報**等核心生產管理模組。

---

## 📁 專案目錄與簡述

| 專案名稱 | 說明簡述 | 主要技術 |
|---|---|---|
| 🧪 [IPA-生產排程雙儲槽優化](./IPA-生產排程雙儲槽優化/) | IPA 高純度化學品雙儲槽產能分配優化與排程演算工具 | Python, SciPy, Matplotlib, PHP |
| 🚛 [IPAHQ-槽車確認-GAS-to-PHPSQL](./IPAHQ-槽車確認-GAS-to-PHPSQL/) | IPAHQ 槽車出貨確認系統（由 Google Apps Script 成功遷移至 PHP/MySQL） | PHP, MySQL, GAS API |
| 📱 [IPAHQ槽車掃描系統代碼原始APP優化](./IPAHQ槽車掃描系統代碼原始APP優化/) | IPAHQ 槽車現場條碼掃描 Android App 原始碼與 Cordova 打包模組 | Cordova, Android, JavaScript |
| 📦 [N系列BARCODE出貨核對](./N系列BARCODE出貨核對/) | N 系列產品現場出貨條碼防呆核對系統 | PHP, MySQL, HTML5 Barcode Reader |
| 📲 [n系列GAS-轉-APK-離線核對上傳](./n系列GAS-轉-APK-離線核對上傳/) | N 系列條碼離線掃描核對與網路連線時自動回傳至 GAS/PHP 之 Android APK | Cordova, Ionic, LocalStorage |
| 🔗 [N系列PHP-條碼掃描-API-串接](./N系列PHP-條碼掃描-API-串接/) | N 系列條碼掃描與出貨驗證 RESTful API 服務 | PHP, REST API, JSON |
| 🚚 [n系列出貨-轉-PHP](./n系列出貨-轉-PHP/) | N 系列出貨單據格式轉換與 PHP 入庫處理腳本 | PHP, MySQL |
| 🔬 [QC-系統客製化電子化工廠](./QC-系統客製化電子化工廠/) | 電子級高純度化學品 QC 品質分析數據自動登錄與檢驗看板 | PHP, MySQL, Chart.js |
| 📑 [三合一單-to-PHP-Migration](./三合一單-to-PHP-Migration/) | 廠區「三合一單據」批量 Excel/GAS 數據遷移至本機/雲端 SQL 腳本 | PHP, PDO, Spreadsheet Parser |
| 🌡️ [溫度通報](./溫度通報/) | 廠區儲槽與反應釜溫度實時監控與 LINE / Email 異常自動警報通報系統 | Python, GAS, Line Notify API |
| 🔑 [軟管對刷](./軟管對刷/) | 鴻勝化學軟管對刷稽核 Android APK (v3.4)，支援一/二/三廠選單、00前綴保護與QC授權放行 | Android SDK, Kotlin, Retrofit, GAS API |
| 🛡️ [軟管對刷-T100QC串接中間件備案](./軟管對刷-T100QC串接中間件備案/) | 鼎新 T100 ERP 品管單 (QC301/ESQC301) 判定中間件備案（獨立資料夾，高彈性設定） | PHP, Oracle OCI, REST API |

---

## 🚀 一鍵環境初始化

若要為此分類下的所有 Python/PHP/Cordova 工具安裝軟體與套件，可執行：
```powershell
.\setup_env.ps1
```
