---
name: 軟管對刷-T100QC串接中間件備案
description: 鼎新 T100 ERP 品管檢驗單 (QC301/ESQC301) 與軟管對刷系統銜接的中間件 API 獨立備案。
---

# 🤖 AI 助理技能與維護說明

## 專案範疇
本專案為完全獨立之備案，專門負責提供 T100 QC 檢驗結果查詢 RESTful API。

## 核心檔案說明
- `t100_qc_middleware.php`：包含完整的 Oracle / SQL Server 連線敘述與動態彈性設定。

## 維護指南
- 若未來 T100 檢驗單欄位名或單別有異動，只需修改 `t100_qc_middleware.php` 中 `$T100_CONFIG` 陣列與 `queryT100Database` 內的 SQL 敘述。
