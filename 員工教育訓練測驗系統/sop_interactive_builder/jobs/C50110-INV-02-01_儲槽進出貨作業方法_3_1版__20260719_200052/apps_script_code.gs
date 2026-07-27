// ============================================================
// 📋 Google Apps Script — 員工教育訓練測驗成績收集系統
// SOP：C50110-INV-02-01 儲槽進出貨作業方法 3 1版 
// ============================================================

const SHEET_NAME = '作答紀錄';

function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    let sheet = ss.getSheetByName(SHEET_NAME);
    if (!sheet) { sheet = ss.insertSheet(SHEET_NAME); }
    const name         = data.name || '未知';
    const score        = data.score !== undefined ? data.score : 0;
    const correctCount = data.correctCount !== undefined ? data.correctCount : 0;
    const total        = data.total !== undefined ? data.total : 0;
    const timestamp    = data.timestamp || new Date().toLocaleString('zh-TW', { timeZone: 'Asia/Taipei' });
    const qAnswers = [];
    let qIndex = 1;
    while (data['q' + qIndex + '_answer'] !== undefined) {
      qAnswers.push(data['q' + qIndex + '_answer']);
      qIndex++;
    }
    if (sheet.getLastRow() === 0) {
      const headers = ['時間戳記', '姓名', '對題數', '得分'];
      for (let i = 1; i < qIndex; i++) {
        const q = data['q' + i + '_question'] || ('第 ' + i + ' 題');
        headers.push(q);
      }
      sheet.appendRow(headers);
      const range = sheet.getRange(1, 1, 1, headers.length);
      range.setBackground('#4F46E5');
      range.setFontColor('#FFFFFF');
      range.setFontWeight('bold');
    }
    const rowData = [timestamp, name, correctCount + ' / ' + total, score + ' 分'];
    qAnswers.forEach(ans => rowData.push(ans));
    sheet.appendRow(rowData);
    return ContentService
      .createTextOutput(JSON.stringify({ status: 'ok', message: '已成功存入雲端試算表！' }))
      .setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService
      .createTextOutput(JSON.stringify({ status: 'error', message: err.toString() }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}
