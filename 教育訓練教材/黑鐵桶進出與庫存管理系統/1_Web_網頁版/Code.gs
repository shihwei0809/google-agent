function doGet() {
  return HtmlService.createTemplateFromFile('index')
    .evaluate()
    .setTitle('黑鐵桶進出與庫存管理系統')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

// --- 讀取類功能 ---

function getInventoryStats() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const summarySheet = ss.getSheetByName('庫存統計');
  
  // 初始化統計結構
  let stats = {
    in: { total: 0, visera: 0, tok: 0, other: 0 }, // 進場: 總數, 采鈺, 東應化, 其他
    out: { total: 0, visera: 0, tok: 0, other: 0 } // 出場: 總數, 采鈺, 東應化, 其他
  };

  if (!summarySheet) return stats;

  const data = summarySheet.getDataRange().getValues();
  
  // 從第1列開始 (避開標題)
  for (let i = 1; i < data.length; i++) {
    const drumId = String(data[i][0]).toUpperCase();
    const status = data[i][2]; 
    
    // 1. 判斷廠商類別
    let type = 'other';
    if (drumId.includes('2ACT  1')) {
      type = 'visera'; // 采鈺
    } else if (drumId.includes('2ACT  2')) {
      type = 'tok';    // 東應化
    }

    // 2. 判斷進出狀態並累加
    if (status === '進場') {
      stats.in.total++;
      stats.in[type]++;
    } else if (status === '出場') {
      stats.out.total++;
      stats.out[type]++;
    }
  }
  
  return stats;
}

function getHighUsageDrums() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('庫存統計');
  if (!sheet) return [];
  const data = sheet.getDataRange().getValues();
  let list = [];
  for (let i = 1; i < data.length; i++) {
    let count = parseInt(data[i][1]) || 0;
    if (count >= 7) {
      list.push({ drumId: data[i][0], count: count, status: data[i][2], lastDate: data[i][3] });
    }
  }
  return list;
}

// --- 查詢功能 (新增) ---

function queryDrumHistoryAdvanced(params) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const drumIdUpper = params.drumId ? params.drumId.toUpperCase() : '';
  let history = [];
  
  // 要搜尋的工作表列表，新增了分開存放的三個紀錄工作表
  const sheetsToSearch = ['紀錄_采鈺', '紀錄_東應化', '紀錄_其他', '紀錄', '報廢紀錄'];
  
  // 處理日期範圍
  let startObj = params.startDate ? new Date(params.startDate + 'T00:00:00') : null;
  let endObj = params.endDate ? new Date(params.endDate + 'T23:59:59') : null;
  
  sheetsToSearch.forEach(sheetName => {
    const sheet = ss.getSheetByName(sheetName);
    if (sheet) {
      const data = sheet.getDataRange().getValues();
      for (let i = 1; i < data.length; i++) { // 假設第一列是標題
        const row = data[i];
        
        let dateVal = row[0];
        let actionVal = row[1];
        let idVal = String(row[2] || '').toUpperCase();
        
        // 報廢紀錄格式可能不同：[時間, 桶號, 次數, 狀態]
        if (sheetName === '報廢紀錄') {
           idVal = String(row[1]).toUpperCase();
           actionVal = '報廢';
        }

        // 篩選桶號 (若有輸入)
        if (drumIdUpper && !idVal.includes(drumIdUpper)) continue;
        
        // 篩選動作 (若有選擇)
        if (params.action && actionVal !== params.action) continue;
        
        // 篩選日期
        let rowDate = dateVal instanceof Date ? dateVal : new Date(dateVal);
        if (startObj && rowDate < startObj) continue;
        if (endObj && rowDate > endObj) continue;

        let dateStr = String(dateVal);
        if (rowDate instanceof Date && !isNaN(rowDate)) {
           dateStr = Utilities.formatDate(rowDate, Session.getScriptTimeZone(), "yyyy/MM/dd HH:mm:ss");
        }

        history.push({
          date: dateStr,
          action: actionVal,
          id: idVal,
          sheet: sheetName
        });
      }
    }
  });
  
  // 依時間排序 (越新越上面)
  history.sort((a, b) => new Date(b.date) - new Date(a.date));
  
  return history;
}

// --- 寫入/更新類功能 ---

function processForm(formObject) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const summarySheet = ss.getSheetByName('庫存統計');
  
  if (!summarySheet) return { status: 'error', message: '找不到庫存統計工作表' };

  const timestamp = new Date();
  const actionType = formObject.actionType;
  
  let entries = [];
  for (let key in formObject) {
    if (key.startsWith('drum_')) {
      let val = formObject[key];
      if (val && val.toString().trim() !== "") entries.push(val.toString().trim().toUpperCase());
    }
  }

  if (entries.length === 0) return { status: 'warning', message: '未輸入資料' };

  let alertList = [];
  entries.forEach(drumId => {
    // 判斷分類，以寫入對應工作表
    let category = '其他';
    if (drumId.includes('2ACT  1')) {
      category = '采鈺';
    } else if (drumId.includes('2ACT  2')) {
      category = '東應化';
    }
    
    // 取得或建立對應的紀錄工作表
    let sheetName = '紀錄_' + category;
    let logSheet = ss.getSheetByName(sheetName);
    if (!logSheet) {
      logSheet = ss.insertSheet(sheetName);
      logSheet.appendRow(['時間', '動作', '桶號']); // 建立標題列
    }

    logSheet.appendRow([timestamp, actionType, drumId]);
    
    let result = updateUsageAndStatus(summarySheet, drumId, actionType, timestamp);
    if (result.count >= 7) alertList.push(`${drumId} (${result.count}次)`);
  });

  return { 
    status: 'success', 
    message: `成功儲存 ${entries.length} 筆 (已分類至對應工作表)`,
    stats: getInventoryStats(),
    alerts: alertList 
  };
}

function updateUsageAndStatus(sheet, drumId, action, time) {
  const data = sheet.getDataRange().getValues();
  let rowIndex = -1, currentCount = 0;
  
  for (let i = 1; i < data.length; i++) {
    if (data[i][0] == drumId) {
      rowIndex = i + 1;
      currentCount = parseInt(data[i][1]) || 0;
      break;
    }
  }
  
  let newCount = currentCount;
  if (rowIndex > 0) {
    if (action === '出場') newCount = currentCount + 1;
    sheet.getRange(rowIndex, 2).setValue(newCount);
    sheet.getRange(rowIndex, 3).setValue(action);
    sheet.getRange(rowIndex, 4).setValue(time);
  } else {
    newCount = (action === '出場') ? 1 : 0;
    sheet.appendRow([drumId, newCount, action, time]);
  }
  return { count: newCount };
}

function processArchiveForm(formObject) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const summarySheet = ss.getSheetByName('庫存統計');
  let archiveSheet = ss.getSheetByName('報廢紀錄');

  if (!summarySheet) return { status: 'error', message: '找不到庫存統計工作表' };
  if (!archiveSheet) {
    archiveSheet = ss.insertSheet('報廢紀錄');
    archiveSheet.appendRow(['時間', '桶號', '次數', '狀態']);
  }

  let drumIds = [];
  for (let key in formObject) {
    if (key.startsWith('archive_drum_')) {
      let val = formObject[key];
      if (val && val.toString().trim() !== "") drumIds.push(val.toString().trim().toUpperCase());
    }
  }

  if (drumIds.length === 0) return { status: 'warning', message: '未輸入任何桶號' };

  let successCount = 0;
  let notFoundList = [];

  drumIds.forEach(targetId => {
    const data = summarySheet.getDataRange().getValues();
    let rowIndex = -1;
    let rowData = [];

    for (let i = 1; i < data.length; i++) {
      if (data[i][0] == targetId) {
        rowIndex = i + 1;
        rowData = data[i];
        break;
      }
    }

    if (rowIndex > 0) {
      archiveSheet.appendRow([new Date(), rowData[0], rowData[1], rowData[2]]);
      summarySheet.deleteRow(rowIndex);
      successCount++;
    } else {
      notFoundList.push(targetId);
    }
  });

  let message = `共封存 ${successCount} 筆桶號。`;
  if (notFoundList.length > 0) {
    message += `\n⚠️ 有 ${notFoundList.length} 筆找不到:\n${notFoundList.join(', ')}`;
  }

  return { 
    status: 'success', 
    message: message,
    stats: getInventoryStats() 
  };
}

// --- PWA API �䴩 ---

function doPost(e) {
  try {
    const params = JSON.parse(e.postData.contents);
    const action = params.action;
    let result = {};

    if (action === 'getInventoryStats') {
      result = getInventoryStats();
    } else if (action === 'getHighUsageDrums') {
      result = getHighUsageDrums();
    } else if (action === 'queryDrumHistoryAdvanced') {
      result = queryDrumHistoryAdvanced(params.data);
    } else if (action === 'processForm') {
      result = processForm(params.data);
    } else if (action === 'processArchiveForm') {
      result = processArchiveForm(params.data);
    }

    return ContentService.createTextOutput(JSON.stringify(result))
      .setMimeType(ContentService.MimeType.JSON);
  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({ status: 'error', message: error.toString() }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

function doOptions(e) {
  return ContentService.createTextOutput("")
    .setMimeType(ContentService.MimeType.TEXT);
}
