# Level 2：試算表後端 - 使用說明書

> 🔗 **GitHub 專案庫**：[shihwei0809/google-agent/tree/main/互動式網站](https://github.com/shihwei0809/google-agent/tree/main/互動式網站)


---

## 📝 模組概述
本模組引入了「輕量級資料儲存」概念。學員完成測驗後，網頁會透過 HTTP POST 將學員的姓名、總分、以及詳細的答題選項傳送至 **Google Apps Script (GAS)**，並自動追加寫入到指定的 **Google 試算表**中。

*   **適用場景**：課後成績靜態回收、簡單的人員訓練簽到與考核記錄。
*   **解決的痛點**：克服 Level 1 關閉網頁即丟失數據的缺點，讓講師能在最熟悉的 Excel 介面中隨時統計成績。
*   **技術限制**：GAS / 試算表寫入會有約 1~2 秒的同步延遲，當多人同時點擊送出時，可能會因為併發冲突而卡死，因此不適合即時對戰。

---

## 🛠️ 技術實作與程式架構

### 檔案位置
*   **前端頁面**：`互動式網站/lv2-sheets.html`
*   **GAS 程式碼**：`互動式網站/gas-code.js`

### 後端 GAS 鎖定防護機制
為了避免多人同時寫入造成資料覆蓋，我們在 GAS 中加載了 `LockService`：
```javascript
function doPost(e) {
  var lock = LockService.getScriptLock();
  try {
    lock.waitLock(10000); // 鎖定 10 秒以進行排隊寫入
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
    var data = JSON.parse(e.postData.contents);
    sheet.appendRow([new Date(), data.nickname, data.score, ...data.answers]);
    return ContentService.createTextOutput(JSON.stringify({status: 'success'}));
  } finally {
    lock.releaseLock(); // 釋放鎖
  }
}
```

---

## 🚀 部署與操作步驟

### 第一步：部署雲端試算表 GAS 後端
1.  開啟您的 Google 雲端硬碟，建立一個新的 **Google 試算表**。
2.  點擊選單的「**擴充功能**」 $\rightarrow$ 「**Apps Script**」。
3.  將 `互動式網站/gas-code.js` 內容完整複製貼上。
4.  點擊右上方「**部署**」 $\rightarrow$ 「**新增部署**」。
5.  設定部署類型為「**網頁應用程式**」：
    *   **執行身分**：我 (您的 Google 帳號)
    *   **誰有權限存取**：任何人 (Anyone)
6.  點擊「部署」，授權 Google 帳戶後，**複製產生的網頁應用程式 URL**。

### 第二步：配置前端與測試
1.  在瀏覽器開啟 `互動式網站/lv2-sheets.html`。
2.  在頁面頂部的「**GAS 部署網頁應用程式 URL**」輸入框中貼上您剛剛複製的 URL（狀態會即時從模擬模式切換為連線模式）。
3.  輸入「姓名」，勾選測驗題，點擊「**送出測驗並存檔**」。
4.  回到你的雲端 Google 試算表，你將會看到一列全新的作答紀錄即時追加到最後一行！
