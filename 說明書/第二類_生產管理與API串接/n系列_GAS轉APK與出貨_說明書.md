# n系列 GAS 轉 APK 與出貨系統 - 操作說明書

> 🔗 **GitHub 專案庫**：[shihwei0809/google-agent/tree/main/n系列GAS-轉-APK-離線核對上傳](https://github.com/shihwei0809/google-agent/tree/main/n系列GAS-轉-APK-離線核對上傳)


## 專案簡介
本專案將原本運行於 Google 試算表（GAS）的出貨登錄系統，封裝並轉換為 Android APK 安裝檔，供現場人員配戴手持 Android 掃描器使用，支援離線暫存與批次上傳。

## 主要功能特色
- **離線工作模式**：在廠區無 Wi-Fi 訊號處可先將掃描資料暫存於本地 SQLite 中。
- **自動回傳雲端**：當偵測到網路連線時，自動將暫存出貨紀錄批次上傳至 Google Sheets。

## 技術棧
- Android SDK, Cordova/WebView, SQLite, Google Apps Script (GAS)

## 安裝與操作
1. 將產出的 `n-series-scanner.apk` 安裝至 Android 掃描槍。
2. 開啟 App，設定 GAS Web App URL。
3. 開始掃描出貨，確認完成後點選「批次同步」即可。
