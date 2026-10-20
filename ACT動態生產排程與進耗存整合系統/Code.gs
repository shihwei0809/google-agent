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
    if (sheetName.startsWith('ArchiveStore') || sheetName === ARCHIVE_SHEET_NAME) {
      sheet.getRange(1, 1, 1, 4).setValues([['ArchiveID', 'Product', 'Timestamp', 'DataJSON']]);
    } else {
      // 包含 DataStore 或各產品工作表
      sheet.getRange(1, 1, 1, 2).setValues([['Key', 'Value']]);
    }
  }
  return sheet;
}

// 支援純網頁直接存取 (選用)
function doGet(e) {
  return ContentService.createTextOutput(JSON.stringify({
    status: "OK",
    service: "Dynamic Production Schedule & Inventory API",
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
    const product = contents.product || contents.payload?.currentProduct || 'ACT';
    const sheetName = 'DataStore_' + product.replace(/[/\\?*:[\]]/g, '_');

    // 1. 讀取特定產品最新資料
    if (action === 'load') {
      const data = loadCloudData(sheetName);
      return buildJsonResponse({ status: "SUCCESS", product: product, data: data });
    }

    // 2. 寫入特定產品最新資料至獨立分頁
    if (action === 'save') {
      const saveRes = saveCloudData(sheetName, contents.payload || {});
      return buildJsonResponse({ status: "SUCCESS", product: product, message: saveRes });
    }

    // 3. 備份存檔 (自動在開頭帶入產品名稱)
    if (action === 'archive') {
      const archRes = archiveData(contents.payload || {}, contents.archiveName || '未命名存檔', product);
      return buildJsonResponse({ status: "SUCCESS", product: product, message: archRes });
    }

    // 4. 讀取歷史備份清單
    if (action === 'get_archives') {
      const list = getArchiveList(product);
      return buildJsonResponse({ status: "SUCCESS", product: product, archives: list });
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

// --- 讀取主資料 (支援分產品分頁，向下相容舊 ACT_DataStore) ---
function loadCloudData(sheetName) {
  let sheet = getSheet(sheetName);
  let data = sheet.getDataRange().getValues();

  // 若該產品專屬分頁為空且是 ACT，則嘗試回退讀取舊的 MAIN_SHEET_NAME
  if (data.length <= 1 && sheetName.includes('ACT')) {
    const oldSheet = getSheet(MAIN_SHEET_NAME);
    const oldData = oldSheet.getDataRange().getValues();
    if (oldData.length > 1) {
      data = oldData;
    }
  }

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

// --- 寫入主資料 (寫入各產品專屬分頁，如 DataStore_ACT, DataStore_IPA) ---
function saveCloudData(sheetName, payload) {
  const sheet = getSheet(sheetName);
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

// --- 備份歷史 (自動前綴 [產品名] 開頭，以利後續讀取區分) ---
function archiveData(payload, archiveName, product) {
  const sheet = getSheet(ARCHIVE_SHEET_NAME);
  const timestamp = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), "yyyy/MM/dd HH:mm:ss");
  const dataJSON = JSON.stringify(payload);

  // 防呆：若使用者輸入的名稱尚未包含產品名稱，自動在開頭補上 [產品名]
  const prodTag = `[${product || 'ACT'}]`;
  let finalName = String(archiveName).trim();
  if (!finalName.startsWith(prodTag)) {
    finalName = `${prodTag} ${finalName}`;
  }

  sheet.appendRow([finalName, product || 'ACT', "'" + timestamp, dataJSON]);
  SpreadsheetApp.flush();
  return "SUCCESS";
}

// --- 取得歷史清單 (可依產品篩選或全列出) ---
function getArchiveList(filterProduct) {
  const sheet = getSheet(ARCHIVE_SHEET_NAME);
  const data = sheet.getDataRange().getValues();
  const list = [];

  for (let i = 1; i < data.length; i++) {
    if (data[i][0]) {
      const rowProd = String(data[i][1] || '');
      const rowId = String(data[i][0]);
      
      // 若有指定產品過濾，且有填 product 欄位或開頭帶有 [產品名]
      if (filterProduct && rowProd && rowProd !== filterProduct) {
        continue;
      }

      list.push({
        id: rowId,
        product: rowProd,
        time: String(data[i][2] || ''),
        dataStr: String(data[i][3] || data[i][2] || '')
      });
    }
  }
  return list.reverse();
}
