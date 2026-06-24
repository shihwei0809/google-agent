# IPAHQ 槽車確認與掃描系統 - 操作說明書

> 🔗 **GitHub 專案庫**：[shihwei0809/google-agent/tree/main/IPAHQ槽車掃描系統代碼原始APP優化](https://github.com/shihwei0809/google-agent/tree/main/IPAHQ槽車掃描系統代碼原始APP優化)


## 專案簡介
本專案用於鴻勝化學的 IPAHQ 槽車進貨確認與掃描登記，透過條碼掃描防錯，確保卸料車號與採購單一致。

## 主要功能特色
- **GAS 雲端備份**：自動將槽車確認紀錄寫入 Google 試算表。
- **本機資料庫連線**：使用 PHP 讀寫 SQL Server / MySQL，將車牌號碼與品管報告（COA）進行防錯匹配。
- **行動裝置友善**：前端介面針對手持掃描槍與平板進行優化。

## 技術棧
- HTML5, Vanilla JS, PHP, Google Apps Script (GAS)

## 操作步驟
1. 確保本地 PHP 環境與 SQL 資料庫已啟動。
2. 使用平板或掃描槍開啟系統網頁。
3. 掃描槽車條碼，系統會即時綠燈過關或紅燈警告（代表車號或品名不符）。
