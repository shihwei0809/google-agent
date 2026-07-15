# 出貨核對系統 - 資料庫同步版本 (BARCODEout-DB-Version)

本專案是從 GAS (Google Sheets) 版本升級為關係型資料庫 (MySQL) 版本的獨立專案。所有功能均已獨立分開，不會影響您原來的 GAS 版本。

---

## 📂 專案結構說明
* `app/`: Android 行動 App 原始碼（已將同步 API 從 GAS URL 調整為本地後端 API）。
* `backend/`: Node.js Express API 伺服器，負責接收 App 傳來的條碼資料並寫入 MySQL。
* `database/`: 包含建立 MySQL 資料表與資料庫的 SQL 腳本。

---

## 🛠️ 部署與使用步驟

### 步驟 1：建立 MySQL 資料庫 (使用 XAMPP)
1. 開啟您的 **XAMPP Control Panel**，確認 **MySQL** 與 **Apache** 模組已經啟動 (如您的螢幕截圖所示)。
2. 開啟瀏覽器，進入 `http://localhost/phpmyadmin` (或使用您的資料庫管理工具如 Navicat、HeidiSQL)。
3. 點選「SQL」分頁，複製並執行 `database/schema.sql` 裡面的內容，或者直接匯入該檔案。
   * 此動作將會自動建立 `barcode_db` 資料庫，並在其中建立 `barcode_shipments` 資料表。

---

### 步驟 2：啟動 Node.js API 後端伺服器
1. 請確認您的電腦已安裝 [Node.js](https://nodejs.org/) (建議 LTS 版本)。
2. 使用命令提示字元 (cmd) 或 PowerShell 進入 `BARCODEout-DB-Version/backend` 資料夾：
   ```bash
   cd d:\GOOGLE ANGET\n系列GAS-轉-APK-離線核對上傳\BARCODEout-DB-Version\backend
   ```
3. 安裝所需的依賴套件：
   ```bash
   npm install
   ```
4. 確認 `backend/.env` 中的資料庫連接設定（已預設為 XAMPP 的 localhost/root 無密碼設定）：
   ```env
   PORT=3000
   DB_HOST=127.0.0.1
   DB_PORT=3306
   DB_USER=root
   DB_PASSWORD=
   DB_NAME=barcode_db
   ```
5. 啟動伺服器：
   ```bash
   npm start
   ```
   * 畫面顯示 `✅ 成功連接到 MySQL 資料庫` 且 `🚀 API 伺服器正在運行於 http://localhost:3000` 即代表成功啟動！

---

### 步驟 3：設定 Android App 並進行編譯
1. 查詢您運行後端伺服器電腦的 **區域網路 IP 地址**：
   * 在電腦上開啟命令提示字元 (cmd)，輸入 `ipconfig`。
   * 尋找「IPv4 位址」（例如：`192.168.1.100` 或 `10.x.x.x`）。
2. 在 Android Studio 中開啟此新專案 `BARCODEout-DB-Version`。
3. 開啟 `app/src/main/java/com/example/barcode_out/NetworkHelper.kt`。
4. 修改第 13 行的 `DATABASE_API_URL`：
   ```kotlin
   // 請將 192.168.1.100 改為您的電腦區域網路 IP，埠號保持 3000
   private const val DATABASE_API_URL = "http://您的電腦IP:3000/api/shipments/sync"
   ```
5. **確保您的 Android 手機與此電腦連線至相同的 Wi-Fi 網路**，即可進行編譯並上機測試。

---

## 📊 資料庫欄位對照說明 (`barcode_shipments`)

當您在 App 中核對完成並按下「連線同步」後，資料會被解析並寫入 MySQL 的 `barcode_shipments` 中：

* `mode`: 出貨模式。
* `location`: 掃描場所（彰濱一廠 / 二廠）。
* `f0` ~ `f16`: 17 個條碼輸入欄位值。
* `created_at`: 寫入資料庫的日期與時間。
