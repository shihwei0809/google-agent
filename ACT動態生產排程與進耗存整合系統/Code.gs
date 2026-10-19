/**
 * [ACT 動態生產排程與進耗存整合系統] Google Apps Script 雲端資料庫後端
 * 支援 Cloudflare Pages 跨網域 (CORS) 雙向讀寫與快照封存
 */

const SPREADSHEET_ID = '1aAkQzTlbtStVP27l_MYQwExkbZCRkk8npInIlhifz88'; // 預設試算表ID，可依需求調整
const MAIN_SHEET_NAME = 'ACT_DataStore';
const ARCHIVE_SHEET_NAME = 'ACT_ArchiveStore';

// 取得或自動建立工作表
function getSheet(sheetName) {
  let ss;
  try {
    ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  } catch (e) {
    ss = SpreadsheetApp.getActiveSpreadsheet();
  }
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

// 支援純網頁直接存取 (選用)
function doGet(e) {
  return ContentService.createTextOutput(JSON.stringify({
    status: "OK",
    service: "ACT Dynamic Production Schedule & Inventory API",
    time: new Date().toISOString()
  })).setMimeType(ContentService.MimeType.JSON);
}

// 🌟 核心：接收 Cloudflare Pages 發送的 JSON 請求
function doPost(e) {
  try {
    let contents = {};
    if (e && e.postData && e.postData.contents) {
      contents = JSON.parse(e.postData.contents);
    }

    const action = contents.action || 'load';

    // 1. 讀取最新資料
    if (action === 'load') {
      const data = loadCloudData();
      return buildJsonResponse({ status: "SUCCESS", data: data });
    }

    // 2. 寫入最新資料
    if (action === 'save') {
      const saveRes = saveCloudData(contents.payload || {});
      return buildJsonResponse({ status: "SUCCESS", message: saveRes });
    }

    // 3. 備份存檔
    if (action === 'archive') {
      const archRes = archiveData(contents.payload || {}, contents.archiveName || '未命名存檔');
      return buildJsonResponse({ status: "SUCCESS", message: archRes });
    }

    // 4. 讀取歷史備份清單
    if (action === 'get_archives') {
      const list = getArchiveList();
      return buildJsonResponse({ status: "SUCCESS", archives: list });
    }

    return buildJsonResponse({ status: "ERROR", message: "未知操作" });

  } catch (err) {
    return buildJsonResponse({ status: "ERROR", error: err.toString() });
  }
}

// 跨網域 JSON 封裝回應
function buildJsonResponse(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

// --- 讀取主資料 ---
function loadCloudData() {
  const sheet = getSheet(MAIN_SHEET_NAME);
  const data = sheet.getDataRange().getValues();
  const result = {};

  for (let i = 1; i < data.length; i++) {
    const key = String(data[i][0]).trim();
    if (!key) continue;

    let val = data[i][1];
    try {
      if (typeof val === 'string' && (val.startsWith('{') || val.startsWith('['))) {
        result[key] = JSON.parse(val);
      } else {
        result[key] = val;
      }
    } catch (e) {
      result[key] = val;
    }
  }
  return result;
}

// --- 寫入主資料 ---
function saveCloudData(payload) {
  const sheet = getSheet(MAIN_SHEET_NAME);
  const data = sheet.getDataRange().getValues();

  Object.keys(payload).forEach(key => {
    let value = payload[key];
    if (value === undefined || value === null) value = '';
    if (typeof value === 'number' && isNaN(value)) value = '';
    if (typeof value === 'object') value = JSON.stringify(value);

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

    targetCell.setValue(value);
  });

  SpreadsheetApp.flush();
  return "SUCCESS";
}

// --- 備份歷史 ---
function archiveData(payload, archiveName) {
  const sheet = getSheet(ARCHIVE_SHEET_NAME);
  const timestamp = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), "yyyy/MM/dd HH:mm:ss");
  const dataJSON = JSON.stringify(payload);

  sheet.appendRow([String(archiveName), "'" + timestamp, dataJSON]);
  SpreadsheetApp.flush();
  return "SUCCESS";
}

// --- 取得歷史清單 ---
function getArchiveList() {
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
}
