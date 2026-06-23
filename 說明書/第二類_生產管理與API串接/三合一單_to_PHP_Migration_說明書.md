# 三合一單 to PHP Migration - 操作說明書

> 🔗 **GitHub 專案庫**：[shihwei0809/google-agent/tree/main/三合一單-to-PHP-Migration](https://github.com/shihwei0809/google-agent/tree/main/三合一單-to-PHP-Migration)


## 專案簡介
本指南與代碼用於將舊有的「三合一出貨確認單」系統（基於 Excel 巨集與 GAS），遷移至以 PHP + SQL 為架構的本地化工廠中央系統中。

## 主要功能特色
- **資料庫綱要遷移**：提供 Excel 資料庫化欄位對照表。
- **PHP 資料匯入 API**：一鍵將歷史 Excel 三合一單轉換為資料庫紀錄。

## 技術棧
- PHP 8, SQL Server / MySQL

## 遷移與操作步驟
1. 於資料庫建立資料表（使用 `schema.sql`）。
2. 將歷史 Excel 檔案放入 `import` 資料夾，並執行 `php import.php` 進行資料導入。
