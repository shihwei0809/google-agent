# 出貨核對系統 - 資料庫版系統說明與操作手冊

本文件說明出貨核對系統（資料庫版）的架構、日常操作方法，以及未來若將資料庫或後端伺服器遷移至公司伺服器時的調整步驟。

---

## 🛠️ 系統架構簡介

本系統採用**行動端 (App) ➔ API 後端伺服器 (Server) ➔ 關係型資料庫 (Database)** 的三層式標準安全架構。

1. **Android App**：由現場人員持手機進行條碼掃描與本機防呆核對，核對成功後暫存在本機 SQLite。點選「連線同步」時，透過 Wi-Fi 發送 HTTP POST 請求將資料送往後端 API。
2. **Node.js Express API 伺服器**：安裝在電腦上，負責接收 App 傳來的 JSON 資料，解析欄位後安全地寫入 MySQL 資料庫。
3. **MySQL 資料庫 (XAMPP)**：儲存最終的所有核對同步紀錄。

---

## 📖 日常操作說明

### 1. 後端伺服器啟動與狀態確認
後端伺服器必須保持啟動，App 才能成功同步資料。
* **啟動方式**：
  1. 開啟命令提示字元 (cmd) 或 PowerShell。
  2. 切換到 `backend` 目錄：
     ```bash
     cd d:\GOOGLE ANGET\n系列GAS-轉-APK-離線核對上傳\BARCODEout-DB-Version\backend
     ```
  3. 執行啟動指令：
     ```bash
     npm start
     ```
  4. 當看見 `🚀 API 伺服器正在運行於 http://localhost:3000` 即代表運作正常。

### 2. 檢視與匯出資料 (phpMyAdmin)
1. 確保 XAMPP Control Panel 中的 **Apache** 與 **MySQL** 是 Start 狀態。
2. 開啟瀏覽器進入 `http://localhost/phpmyadmin`。
3. 點選左側選單的 **`barcode_db`** ➔ **`barcode_shipments`**。
4. 即可在「瀏覽」頁面看到所有同步進來的條碼紀錄。
5. 若需要匯出 Excel，可點選上方選單的「匯出」➔ 格式選擇「CSV」或「PDF/Excel」進行下載。

---

## 🌐 未來搬遷至公司伺服器的異動指南

當未來需要將系統正式佈署至公司伺服器（非個人電腦）時，主要有以下兩種情境與對應異動步驟：

### 情境 A：只將 MySQL 資料庫移至公司資料庫伺服器 (API 伺服器仍在原電腦)
如果您只希望將資料寫入公司現有的資料庫伺服器（例如公司的 MySQL、MariaDB 或 SQL Server）：
1. **修改 API 伺服器設定**：
   * 開啟 `BARCODEout-DB-Version/backend/.env` 檔案。
   * 將資料庫連接設定修改為公司伺服器的資訊：
     ```env
     DB_HOST=公司資料庫伺服器的IP (例如 10.1.2.3)
     DB_PORT=公司資料庫的Port (MySQL 預設 3306)
     DB_USER=公司資料庫帳號
     DB_PASSWORD=公司資料庫密碼
     DB_NAME=公司資料庫名稱 (例如 barcode_db)
     ```
   * 重新啟動後端伺服器 (`npm start`)，它將自動連線至新的伺服器並建立資料表。
2. **App 端無需任何修改**。

---

### 情境 B：後端 API 伺服器與資料庫全部移至公司伺服器 (推薦)
如果您希望將 Node.js 後端伺服器也部署在公司的伺服器上，以達到 24 小時不關機服務：

#### 1. 伺服器端部署
* 將整個 `backend` 資料夾複製到公司的伺服器上。
* 在伺服器上安裝 [Node.js](https://nodejs.org/)。
* 在 `backend` 目錄執行 `npm install`。
* 修改 `backend/.env` 檔案中的資料庫連線資訊 (如情境 A 所示)。
* 在伺服器上啟動服務：`npm start`（或使用 `pm2` 等工具讓它在背景永久執行）。

#### 2. Android App 程式碼異動
* 開啟 Android 專案中的 `app/src/main/java/com/example/barcode_out/NetworkHelper.kt`。
* 將 `DATABASE_API_URL` 修改為**公司伺服器的 IP 地址**（或網域名稱 Domain）：
  ```kotlin
  // 修改前：個人電腦 IP
  // private const val DATABASE_API_URL = "http://192.168.3.35:3000/api/shipments/sync"
  
  // 修改後：公司伺服器 IP (例如 10.10.1.50)
  private const val DATABASE_API_URL = "http://10.10.1.50:3000/api/shipments/sync"
  ```
* 修改完成後，在 Android Studio 中重新編譯產出新的 APK 並發布給現場人員安裝。

---

## ⚠️ 網路與防火牆注意事項 (IT 配合事項)
若要確保 App 能順利連上伺服器，請務必請公司 IT 協助檢查以下設定：
1. **內部網路相通**：現場手機連線的 Wi-Fi 必須與後端伺服器處於**同一個內部網路**，或者路由有開通相應路徑。
2. **防火牆連接埠 (Port) 開放**：伺服器作業系統（如 Windows Server）的防火牆必須**允許 Port 3000** 的輸入連線 (Inbound Rule)，否則手機的請求會被防火牆阻擋。
3. **固定 IP**：後端伺服器建議設定為**固定 IP**，以避免每次路由器重啟後電腦 IP 改變，導致 App 需要重新編譯。
