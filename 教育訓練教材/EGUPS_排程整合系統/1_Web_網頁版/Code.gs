const SPREADSHEET_ID = '1aAkQzTlbtStVP27l_MYQwExkbZCRkk8npInIlhifz88';
const MAIN_SHEET_NAME = 'DataStore';
const ARCHIVE_SHEET_NAME = 'ArchiveStore'; 

function doGet() {
  return HtmlService.createTemplateFromFile('Index')
    .evaluate()
    .setTitle('EGUPS動態整合系統 (GAS 備份版)')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

// 取得或建立工作表
function getSheet(sheetName) {
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  let sheet = ss.getSheetByName(sheetName);
  if (!sheet) {
    sheet = ss.insertSheet(sheetName);
    if (sheetName === MAIN_SHEET_NAME) {
      sheet.getRange(1, 1, 1, 2).setValues([['Key', 'Value']]);
    } else if (sheetName === ARCHIVE_SHEET_NAME) {
      sheet.getRange(1, 1, 1, 3).setValues([['ArchiveID', 'Timestamp', 'DataJSON']]);
    }
  }
  return sheet;
}

// --- 主要資料讀寫 ---
function loadCloudData() {
  try {
    const sheet = getSheet(MAIN_SHEET_NAME);
    const data = sheet.getDataRange().getValues();
    const result = {};
    
    for (let i = 0; i < data.length; i++) {
      const key = String(data[i][0]).trim();
      if (!key || key === 'Key') continue; 
      
      let val = data[i][1];
      if (key === 'startDateTime' || key === 'scheduleStartDateTime') {
        result[key] = val;
        continue;
      }
      try {
        if (typeof val === 'string' && (val.startsWith('{') || val.startsWith('['))) {
          result[key] = JSON.parse(val);
        } else {
          result[key] = val;
        }
      } catch (e) { result[key] = val; }
    }
    return result;
  } catch (err) { 
    return { _error: err.toString() }; 
  }
}

function saveCloudData(payload) {
  try {
    const sheet = getSheet(MAIN_SHEET_NAME);
    const data = sheet.getDataRange().getValues();

    Object.keys(payload).forEach(key => {
      let value = payload[key];
      if (value === undefined || value === null) value = '';
      if (typeof value === 'number' && isNaN(value)) value = '';
      if (typeof value === 'object') value = JSON.stringify(value);
      
      if ((key === 'startDateTime' || key === 'scheduleStartDateTime') && value !== '') value = "'" + value; 

      let rowIndex = -1;
      for (let i = 0; i < data.length; i++) {
        if (String(data[i][0]).trim() === key) {
          rowIndex = i + 1;
          break;
        }
      }

      let targetCell;
      if (rowIndex !== -1) {
        targetCell = sheet.getRange(rowIndex, 2);
      } else {
        sheet.appendRow([key, '']);
        targetCell = sheet.getRange(sheet.getLastRow(), 2);
      }

      if (key === 'startDateTime' || key === 'scheduleStartDateTime') targetCell.setNumberFormat('@');
      targetCell.setValue(value);
    });
    
    SpreadsheetApp.flush();
    return "SUCCESS";
  } catch (err) {
    return "ERROR: " + err.toString();
  }
}

// --- 歷史紀錄備份與讀取功能 ---

// 1. 備份當下資料
function archiveData(payload, archiveName) {
  try {
    const sheet = getSheet(ARCHIVE_SHEET_NAME);
    const timestamp = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), "yyyy/MM/dd HH:mm:ss");
    const dataJSON = JSON.stringify(payload);
    
    sheet.appendRow([String(archiveName), "'" + timestamp, dataJSON]);
    SpreadsheetApp.flush();
    return "SUCCESS";
  } catch (err) {
    return "ERROR: " + err.toString();
  }
}

// 2. 取得歷史紀錄清單
function getArchiveList() {
  try {
    const sheet = getSheet(ARCHIVE_SHEET_NAME);
    const data = sheet.getDataRange().getValues();
    const list = [];
    
    for (let i = 1; i < data.length; i++) {
      if (data[i][0]) {
        list.push({
          id: String(data[i][0]),
          time: String(data[i][1]),
          dataStr: String(data[i][2])  
        });
      }
    }
    return list.reverse();
  } catch (err) {
    return [];
  }
}
