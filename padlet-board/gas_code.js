// ==========================================================================
// Google Apps Script Backend (gas_code.js)
// Message Board Backend Database Storage API
// ==========================================================================

function doGet(e) {
  var output = getBoardData();
  return ContentService.createTextOutput(output)
    .setMimeType(ContentService.MimeType.JSON);
}

function doPost(e) {
  try {
    var rawData = e.postData.contents;
    if (!rawData) {
      return ContentService.createTextOutput(JSON.stringify({ status: "error", message: "No post data found" }))
        .setMimeType(ContentService.MimeType.JSON);
    }
    
    // Parse to validate JSON formatting
    var parsed = JSON.parse(rawData);
    if (parsed && typeof parsed.boards === "object" && typeof parsed.activeDate === "string") {
      saveBoardData(rawData);
      return ContentService.createTextOutput(JSON.stringify({ status: "success", message: "Data synchronized successfully" }))
        .setMimeType(ContentService.MimeType.JSON);
    } else if (parsed && typeof parsed.boardTitle === "string" && Array.isArray(parsed.columns)) {
      saveBoardData(rawData);
      return ContentService.createTextOutput(JSON.stringify({ status: "success", message: "Legacy data synchronized successfully" }))
        .setMimeType(ContentService.MimeType.JSON);
    } else {
      return ContentService.createTextOutput(JSON.stringify({ status: "error", message: "Invalid JSON schema for board data" }))
        .setMimeType(ContentService.MimeType.JSON);
    }
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({ status: "error", message: err.toString() }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

// --------------------------------------------------------------------------
// Core Storage Helpers
// --------------------------------------------------------------------------

function getBoardData() {
  // 1. Read from script key-value property store (up to 9MB, fast, highly reliable)
  var data = PropertiesService.getScriptProperties().getProperty("board_data");
  if (data) {
    return data;
  }
  
  // 2. Fallback: Read from Sheet named "DB" if a spreadsheet is linked
  try {
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("DB");
    if (sheet) {
      var cellVal = sheet.getRange("A1").getValue();
      if (cellVal) {
        return cellVal;
      }
    }
  } catch (e) {
    // Spreadsheet app might not be accessible if standalone
  }

  // 3. Fallback to empty default data if script is fresh
  return JSON.stringify({
    boardTitle: "品保課協作與品質管理看板",
    boardDescription: "品保部公告、品質異常通報、SOP規章、稽核巡檢與客訴改善追蹤看板 (雙擊空白處或點擊欄位下方 [+] 新增卡片)",
    bgType: "image",
    bgValue: "https://images.unsplash.com/photo-1531685250784-7569952593d2?q=80&w=1200",
    columns: [
      { id: "col-1", title: "最新公告與SOP規章", cards: [] },
      { id: "col-2", title: "品質異常通報", cards: [] },
      { id: "col-3", title: "稽核與日常巡檢", cards: [] },
      { id: "col-4", title: "客訴與改善追蹤 (CAR)", cards: [] },
      { id: "col-5", title: "回饋與建議", cards: [] }
    ]
  });
}

function saveBoardData(jsonString) {
  // 1. Save to Apps Script Properties Store
  PropertiesService.getScriptProperties().setProperty("board_data", jsonString);
  
  // 2. Save to sheet named "DB" as cell A1 backup
  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    if (ss) {
      var sheet = ss.getSheetByName("DB");
      if (!sheet) {
        sheet = ss.insertSheet("DB");
      }
      sheet.getRange("A1").setValue(jsonString);
    }
  } catch (e) {
    // If running as standalone script, active spreadsheet might not exist, which is fine
  }
}
