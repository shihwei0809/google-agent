// ============================================================
// 📋 Google Apps Script — 員工教育訓練測驗成績收集系統 (進出貨作業與安全防護標準作業程序)
// ============================================================
// 
// 操作步驟：
// 1. 前往 https://sheets.new 建立一個新的試算表，命名為「員工測驗紀錄」
// 2. 點選上方選單的「擴充功能」->「Apps Script」
// 3. 將此編輯器內原有的內容清空，並貼上下方所有的程式碼後存檔。
// 4. 點選右上角的「部署」->「新增部署作業」
//    - 選取類型：網頁應用程式 (Web App)
//    - 說明：教育訓練成績回收
//    - 執行身分：我 (Me)
//    - 誰可以存取：所有人 (Anyone)
// 5. 點擊「部署」，授權存取 Google 帳號後，複製產生的「網頁應用程式 URL」。
// 6. 將複製的網址，貼入測驗網頁右上角「⚙️ 系統設定」的雲端同步欄位中即可。

const SHEET_NAME = '作答紀錄';

function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    let sheet = ss.getSheetByName(SHEET_NAME);
    if (!sheet) { sheet = ss.insertSheet(SHEET_NAME); }
    const name = data.name || '未知';
    const score = data.score !== undefined ? data.score : 0;
    const correctCount = data.correctCount !== undefined ? data.correctCount : 0;
    const total = data.total !== undefined ? data.total : 0;
    const timestamp = data.timestamp || new Date().toLocaleString('zh-TW', { timeZone: 'Asia/Taipei' });
    const qAnswers = [];
    let qIndex = 1;
    while (data['q' + qIndex] !== undefined) {
      qAnswers.push(data['q' + qIndex]);
      qIndex++;
    }
    if (sheet.getLastRow() === 0) {
      const headers = ['時間戳記', '姓名', '對題數', '得分'];
      for (let i = 1; i < qIndex; i++) { headers.push('第 ' + i + ' 題作答'); }
      sheet.appendRow(headers);
      const range = sheet.getRange(1, 1, 1, headers.length);
      range.setBackground('#4F46E5');
      range.setFontColor('#FFFFFF');
      range.setFontWeight('bold');
    }
    const rowData = [timestamp, name, correctCount + ' / ' + total, score + ' 分'];
    qAnswers.forEach(ans => rowData.push(ans));
    sheet.appendRow(rowData);
    return ContentService.createTextOutput(JSON.stringify({ status: 'ok', message: '已成功存入雲端試算表！' })).setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({ status: 'error', message: err.toString() })).setMimeType(ContentService.MimeType.JSON);
  }
}