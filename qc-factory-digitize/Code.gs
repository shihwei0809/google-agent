const CONFIG = {
  sheetName: 'QC_Samples',
  configSheetName: 'System_Config', // 存放 QC_PIN 的工作表
  spreadsheetId: '1_4zrITMtrKCC9x_DmazqxYz63366ro-OpZOkNRTFhqo',
  // 已填入您的 Messaging API Channel Access Token
  LINE_TOKEN: 'DnDOO8qm91TN7WiOzEKKAVV8HC1vUUImhOH25rkHPt3WeozjQdP6pY+tv0lPym5GHZqHuUdiVKYPsI7BxhiHAnTVIaSGE+tukuSbNYJfcBcZ1yxNDnEH08lZbKFUL9YxmSCQiozhi1v22omQPy7bEAdB04t89/1O/w1cDnyilFU=', 
  headers: [
    'id', 'barcode', 'productName', 'tankNo', 'customer', 
    'quantity', 'flowType', 'dept', 'requester', 'grade', 
    'qcResult', 'createdAt', 'completedAt', 'status', 'qcNote'
  ]
};

function doGet() {
  return HtmlService.createHtmlOutputFromFile('Index')
    .setTitle('鴻勝化學 QC 檢驗即時看板系統')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

// 從 Excel 讀取品管授權碼
function getPinFromSheet_() {
  try {
    const ss = SpreadsheetApp.openById(CONFIG.spreadsheetId);
    const sheet = ss.getSheetByName(CONFIG.configSheetName);
    if (!sheet) return '8888'; 
    const data = sheet.getDataRange().getValues();
    for (let i = 1; i < data.length; i++) {
      if (data[i][0] === 'QC_PIN') return String(data[i][1]);
    }
    return '8888';
  } catch(e) { return '8888'; }
}

function getSamples() {
  try {
    const ss = SpreadsheetApp.openById(CONFIG.spreadsheetId);
    const sheet = ss.getSheetByName(CONFIG.sheetName);
    const data = sheet.getDataRange().getValues();
    if (data.length <= 1) return [];
    return data.slice(1).filter(row => row[0]).map(row => {
      let obj = {};
      CONFIG.headers.forEach((h, i) => {
        let val = row[i];
        if (val instanceof Date) { val = val.toISOString(); }
        obj[h] = val;
      });
      return obj;
    }).sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
  } catch(e) { return []; }
}

function createSample(payload) {
  const ss = SpreadsheetApp.openById(CONFIG.spreadsheetId);
  const sheet = ss.getSheetByName(CONFIG.sheetName);
  const rowData = CONFIG.headers.map(h => {
    if (h === 'id') return Utilities.getUuid();
    if (h === 'status') return 'pending';
    if (h === 'createdAt') return new Date().toISOString();
    return payload[h] || '';
  });
  sheet.appendRow(rowData);
  return { success: true };
}

function completeSample(id, result, note, pin) {
  const currentPin = getPinFromSheet_();
  if (pin !== currentPin) {
    return { success: false, error: '⛔ 授權失敗：品管專屬密碼錯誤！' };
  }

  const ss = SpreadsheetApp.openById(CONFIG.spreadsheetId);
  const sheet = ss.getSheetByName(CONFIG.sheetName);
  const data = sheet.getDataRange().getValues();
  const h = CONFIG.headers;
  
  for (let i = 1; i < data.length; i++) {
    if (data[i][h.indexOf('id')] === id) {
      const row = i + 1;
      sheet.getRange(row, h.indexOf('status') + 1).setValue('completed');
      sheet.getRange(row, h.indexOf('completedAt') + 1).setValue(new Date().toISOString());
      sheet.getRange(row, h.indexOf('qcResult') + 1).setValue(result);
      sheet.getRange(row, h.indexOf('qcNote') + 1).setValue(note);
      
      sendLineNotify(data[i][h.indexOf('barcode')], data[i][h.indexOf('productName')], data[i][h.indexOf('requester')], result, note);
      return { success: true };
    }
  }
  return { success: false, error: '找不到該筆資料' };
}

function sendLineNotify(barcode, productName, requester, result, note) {
  const msgText = `✅【品管檢驗放行通知】\n單號：${barcode}\n品名：${productName}\n送樣人：${requester}\n判定結果：${result}\n備註：${note}`;
  const payload = { "messages": [ { "type": "text", "text": msgText } ] };
  const options = {
    "method": "post",
    "headers": { "Authorization": "Bearer " + CONFIG.LINE_TOKEN, "Content-Type": "application/json" },
    "payload": JSON.stringify(payload)
  };
  UrlFetchApp.fetch("https://api.line.me/v2/bot/message/broadcast", options);
}
