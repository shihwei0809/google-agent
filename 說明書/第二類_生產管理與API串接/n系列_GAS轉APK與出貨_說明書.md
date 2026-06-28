# n系列 GAS 轉 APK 與出貨系統 - 操作說明書

> 🔗 **GitHub 專案庫**：[shihwei0809/google-agent/tree/main/n系列GAS-轉-APK-離線核對上傳](https://github.com/shihwei0809/google-agent/tree/main/n系列GAS-轉-APK-離線核對上傳)

---

## 專案簡介
本專案為將原有 Google 試算表（GAS）出貨登錄功能遷移至手持式 Android 條碼掃描裝置的**原生 Android 應用程式** (Native Android App)。
專為現場包裝核對人員設計，支援 SQLite 離線暫存、格式驗證、防斷電/休眠失憶機制，並在網路連通時自動或手動同步至 Google Apps Script 雲端試算表。

---

## 主要功能特色
1. **離線 SQLite 暫存**：在廠區無 Wi-Fi 訊號之盲區（如庫房深處或貨櫃內）掃描時，自動將出貨紀錄暫存於手機本地資料庫，待重獲訊號後同步。
2. **ZXing 穩定掃描**：整合官方 `zxing-android-embedded` 掃描器，相容多種手持掃描槍硬體，具備高效率、防閃退特性。
3. **欄位自動聚焦**：條碼掃描成功後，系統自動判定目前模式並自動聚焦下一個未填寫欄位，減少人工點擊次數。
4. **防失憶回復機制**：實作 `onSaveInstanceState`，當相機掃描器開啟時若發生系統記憶體回收，返回後仍可自動找回當前輸入欄位，確保資料不丟失。
5. **客製化 UI 與文字加黑**：針對現場強光環境，將輸入框、提示字與 Spinner 下拉選單（場所、數量）調整為黑體、放大、粗體，方便現場人員辨識。
6. **背景非同步同步與自動重試**：實作 `ConnectivityManager` 監聽器，網路恢復時自動觸發背景執行緒非同步同步，防止 UI 卡死並有效避開 Android NetworkOnMainThread 閃退問題。

---

## 技術棧
- **開發語言**：Kotlin
- **建置工具**：Android Gradle Plugin (AGP), Kotlin DSL (`.gradle.kts`)
- **資料庫**：SQLite (本機暫存)
- **網路通訊**：OkHttp 4 (JSON 傳輸與 Line Notify 連線)
- **掃描套件**：`com.journeyapps:zxing-android-embedded`
- **雲端整合**：Google Apps Script (GAS) Web App, Line Notify API (異常回報)

---

## 本地 SQLite 結構
暫存資料表 `pending_shipments`：
```sql
CREATE TABLE pending_shipments (
    id INTEGER PRIMARY KEY AUTOINCREMENT, 
    barcode TEXT, 
    timestamp TEXT
)
```

---

## 部署與使用說明
1. **設定金鑰與伺服器網址**：
   - 開啟 `app/src/main/java/com/example/barcode_out/NetworkHelper.kt`，填入正式的 `LINE_TOKEN` 與 `GAS_URL`。
2. **編譯產出 APK**：
   - 在 Android Studio 中開啟此專案目錄 `BARCODEout-20260601`，執行 `Build > Build Bundle(s) / APK(s) > Build APK(s)`，或在終端機執行 `.\gradlew.bat assembleDebug`。
3. **手機安裝與設定**：
   - 將產出的 `app-debug.apk` 安裝至實體 Android 手機或掃描槍。
   - 第一次使用需於系統提示時，核准相機 (Camera) 與網路 (Internet) 權限。
4. **現場操作**：
   - 選擇出貨模式（整板、混板、散桶、AZ），並設定場所與數量。
   - 點擊欄位旁的「📷」按鈕啟動掃描。
   - 點擊「🚀 巡檢核對並存檔」儲存至手機資料庫。
   - 點擊「🔄 同步暫存資料」或靜待網路自動恢復，系統即會將資料批次上傳至 GAS。

