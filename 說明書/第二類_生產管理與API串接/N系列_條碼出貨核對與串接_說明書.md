# N系列 條碼出貨核對與串接 - 操作說明書

> 🔗 **GitHub 專案庫**：[shihwei0809/google-agent/tree/main/n系列GAS-轉-APK-離線核對上傳](https://github.com/shihwei0809/google-agent/tree/main/n系列GAS-轉-APK-離線核對上傳)


## 專案簡介
本系統專為 N 系列產品出貨設計，現場包裝員透過條碼槍掃描產品條碼，系統自動進行型號與出貨單核對，防止出錯貨。

## 主要功能特色
- **實時核對**：掃描後立即在畫面比對出貨型號與數量。
- **API 自動同步**：核對完成後，自動調用 PHP API 將資料回傳至 ERP/MES 系統。

## 技術棧
- PHP, JavaScript, SQL Database

## 操作步驟
1. 打開出貨核對網頁。
2. 掃描出貨單條碼以載入預計出貨清單。
3. 依序掃描棧板或外箱上的產品條碼，確認完成後按「確認出貨」自動同步後台。
