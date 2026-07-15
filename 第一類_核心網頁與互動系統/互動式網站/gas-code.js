/**
 * Google Apps Script (GAS) Backend Code
 * 
 * 部署說明：
 * 1. 開啟一個 Google 試算表。
 * 2. 點擊「擴充功能」 -> 「Apps Script」。
 * 3. 清空原本的程式碼，將此檔案的內容完整複製貼上。
 * 4. 點擊「部署」 -> 「新增部署」。
 * 5. 選取類型為「網頁應用程式」。
 * 6. 設定：
 *    - 說明：互動式測驗接收端
 *    - 執行身分：我 (您的 Google 帳號)
 *    - 誰有權限存取：任何人 (Anyone)
 * 7. 點擊部署，授予必要權限後，複製產生的「網頁應用程式 URL」並填入前端頁面。
 */

function doGet(e) {
  // 用於前端驗證與連結獲取
  var sheet = SpreadsheetApp.getActiveSpreadsheet();
  var sheetUrl = sheet.getUrl();
  
  return ContentService.createTextOutput(JSON.stringify({
    status: 'success',
    sheetUrl: sheetUrl
  })).setMimeType(ContentService.MimeType.JSON);
}

function doPost(e) {
  var lock = LockService.getScriptLock();
  try {
    // 鎖定 10 秒以避免併發寫入衝突
    lock.waitLock(10000);
    
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
    var postData = JSON.parse(e.postData.contents);
    
    var nickname = postData.nickname;
    var score = postData.score;
    var answers = postData.answers; // 陣列格式
    
    // 組合要寫入的資料列
    var timestamp = new Date();
    var rowData = [timestamp, nickname, score];
    
    // 將所有答案依序加入 rowData
    if (Array.isArray(answers)) {
      for (var i = 0; i < answers.length; i++) {
        rowData.push(answers[i]);
      }
    }
    
    // 寫入試算表最後一列
    sheet.appendRow(rowData);
    
    return ContentService.createTextOutput(JSON.stringify({
      status: 'success',
      message: 'Data successfully written to sheet.'
    })).setMimeType(ContentService.MimeType.JSON);
    
  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({
      status: 'error',
      message: error.toString()
    })).setMimeType(ContentService.MimeType.JSON);
    
  } finally {
    lock.releaseLock();
  }
}
