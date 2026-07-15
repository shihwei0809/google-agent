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
    
    // 1. Handle Image Upload Action
    if (parsed && parsed.action === "uploadImage") {
      if (!parsed.base64 || !parsed.fileName || !parsed.mimeType) {
        return ContentService.createTextOutput(JSON.stringify({ status: "error", message: "Missing image upload parameters" }))
          .setMimeType(ContentService.MimeType.JSON);
      }
      var fileUrl = saveUploadedFile(parsed.base64, parsed.fileName, parsed.mimeType);
      return ContentService.createTextOutput(JSON.stringify({ status: "success", url: fileUrl }))
        .setMimeType(ContentService.MimeType.JSON);
    }
    
    // 2. Handle New Board Sync Action with Log Details
    if (parsed && parsed.action === "syncData") {
      if (!parsed.boardData) {
        return ContentService.createTextOutput(JSON.stringify({ status: "error", message: "Missing boardData in syncData action" }))
          .setMimeType(ContentService.MimeType.JSON);
      }
      var boardDataString = JSON.stringify(parsed.boardData);
      saveBoardData(boardDataString);
      
      // Log to spreadsheet
      logToSpreadsheet(parsed.logAction, parsed.logTarget, parsed.logDetail);
      
      return ContentService.createTextOutput(JSON.stringify({ status: "success", message: "Data synchronized and logged successfully" }))
        .setMimeType(ContentService.MimeType.JSON);
    }
    
    // 3. Fallback: Handle Legacy Direct Sync Actions
    if (parsed && typeof parsed.boards === "object" && typeof parsed.activeDate === "string") {
      saveBoardData(rawData);
      logToSpreadsheet("系統資料同步", "看板資料庫", "手動/自動直接同步");
      return ContentService.createTextOutput(JSON.stringify({ status: "success", message: "Data synchronized successfully" }))
        .setMimeType(ContentService.MimeType.JSON);
    } else if (parsed && typeof parsed.boardTitle === "string" && Array.isArray(parsed.columns)) {
      saveBoardData(rawData);
      logToSpreadsheet("系統資料同步", "舊版看板資料庫", "手動/自動直接同步");
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
  // Ensure log spreadsheet is created and initialized
  var properties = PropertiesService.getScriptProperties();
  var spreadsheetId = properties.getProperty("log_spreadsheet_id");
  if (!spreadsheetId) {
    try {
      var ss = SpreadsheetApp.create("雲端留言板-操作日誌");
      spreadsheetId = ss.getId();
      properties.setProperty("log_spreadsheet_id", spreadsheetId);
      var sheet = ss.getSheets()[0];
      sheet.setName("操作紀錄");
      sheet.appendRow(["時間", "操作動作", "目標對象/標題", "詳細說明"]);
      sheet.getRange("A1:D1").setFontWeight("bold").setBackground("#e0e7ff");
      sheet.setFrozenRows(1);
    } catch (e) {
      Logger.log("Failed to create log spreadsheet on GET: " + e.toString());
    }
  }

  // 1. Read from script key-value property store (up to 9MB, fast, highly reliable)
  var data = properties.getProperty("board_data");
  if (data) {
    try {
      var parsed = JSON.parse(data);
      if (spreadsheetId) {
        parsed.logSpreadsheetUrl = "https://docs.google.com/spreadsheets/d/" + spreadsheetId + "/edit";
      }
      return JSON.stringify(parsed);
    } catch (e) {
      return data;
    }
  }
  
  // 2. Fallback: Read from Sheet named "DB" if a spreadsheet is linked
  try {
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("DB");
    if (sheet) {
      var cellVal = sheet.getRange("A1").getValue();
      if (cellVal) {
        try {
          var parsed = JSON.parse(cellVal);
          if (spreadsheetId) {
            parsed.logSpreadsheetUrl = "https://docs.google.com/spreadsheets/d/" + spreadsheetId + "/edit";
          }
          return JSON.stringify(parsed);
        } catch (e) {
          return cellVal;
        }
      }
    }
  } catch (e) {
    // Spreadsheet app might not be accessible if standalone
  }

  // 3. Fallback to empty default data if script is fresh
  var defaultVal = {
    boardTitle: "資材課工作交接與品質管理看板",
    boardDescription: "資材部公告、品質管理與工作交接、SOP規章、稽核巡檢與客訴改善追蹤看板 (雙擊空白處或點擊欄位下方 [+] 新增卡片)",
    bgType: "image",
    bgValue: "https://images.unsplash.com/photo-1531685250784-7569952593d2?q=80&w=1200",
    columns: [
      { id: "col-1", title: "最新公告與SOP規章", cards: [] },
      { id: "col-2", title: "品質異常通報", cards: [] },
      { id: "col-3", title: "稽核與日常巡檢", cards: [] },
      { id: "col-4", title: "客訴與改善追蹤 (CAR)", cards: [] },
      { id: "col-5", title: "回饋與建議", cards: [] }
    ]
  };
  
  if (spreadsheetId) {
    defaultVal.logSpreadsheetUrl = "https://docs.google.com/spreadsheets/d/" + spreadsheetId + "/edit";
  }
  
  return JSON.stringify(defaultVal);
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

// 3. Operation Log Spreadsheet Writer
function logToSpreadsheet(action, target, detail) {
  try {
    var properties = PropertiesService.getScriptProperties();
    var spreadsheetId = properties.getProperty("log_spreadsheet_id");
    var ss = null;

    if (spreadsheetId) {
      try {
        ss = SpreadsheetApp.openById(spreadsheetId);
      } catch (e) {
        ss = null;
      }
    }

    if (!ss) {
      // Create new Spreadsheet
      ss = SpreadsheetApp.create("雲端留言板-操作日誌");
      spreadsheetId = ss.getId();
      properties.setProperty("log_spreadsheet_id", spreadsheetId);
      
      var sheet = ss.getSheets()[0];
      sheet.setName("操作紀錄");
      sheet.appendRow(["時間", "操作動作", "目標對象/標題", "詳細說明"]);
      sheet.getRange("A1:D1").setFontWeight("bold").setBackground("#e0e7ff");
      sheet.setFrozenRows(1);
    } else {
      var sheet = ss.getSheetByName("操作紀錄");
      if (!sheet) {
        sheet = ss.insertSheet("操作紀錄");
        sheet.appendRow(["時間", "操作動作", "目標對象/標題", "詳細說明"]);
        sheet.getRange("A1:D1").setFontWeight("bold").setBackground("#e0e7ff");
        sheet.setFrozenRows(1);
      }
    }

    var now = new Date();
    var formattedDate = Utilities.formatDate(now, "GMT+8", "yyyy-MM-dd HH:mm:ss");
    sheet.appendRow([formattedDate, action || "同步資料", target || "", detail || ""]);
  } catch (err) {
    Logger.log("Failed to log operation: " + err.toString());
  }
}

// --------------------------------------------------------------------------
// Image Upload Helper (Google Drive Storage)
// --------------------------------------------------------------------------

function saveUploadedFile(base64Data, fileName, mimeType) {
  var folderName = "資材課留言板圖片";
  var folders = DriveApp.getFoldersByName(folderName);
  var folder;
  
  if (folders.hasNext()) {
    folder = folders.next();
  } else {
    folder = DriveApp.createFolder(folderName);
  }
  
  // Strip potential data URL prefix (e.g. "data:image/png;base64,")
  var base64Clean = base64Data;
  if (base64Data.indexOf(",") !== -1) {
    base64Clean = base64Data.split(",")[1];
  }
  
  var decoded = Utilities.base64Decode(base64Clean);
  var blob = Utilities.newBlob(decoded, mimeType, fileName);
  var file = folder.createFile(blob);
  
  // Set sharing permission so anyone with the link can view it (essential for <img> tag display)
  file.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
  
  // Construct a direct image display URL (using uc?export=view&id=FILE_ID)
  return "https://drive.google.com/uc?export=view&id=" + file.getId();
}

// Dummy function for administrator to trigger DriveApp authorization dialog in editor UI
function authorizeDrive() {
  var root = DriveApp.getRootFolder();
  Logger.log("Drive authorized. Root folder name: " + root.getName());
}
