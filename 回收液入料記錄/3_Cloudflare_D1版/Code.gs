// Google Apps Script (GAS) 程式碼
// 部署方式：
// 1. 在 Google Drive 建立一個 Google Sheets (試算表)
// 2. 點擊「擴充功能」->「Apps Script」
// 3. 貼上此段程式碼
// 4. 點選「部署」->「新增部署作業」-> 類型選「網頁應用程式」
// 5. 權限設為「所有人 (任何人)」

const SHEET_NAME = "入料記錄總表"; // 請確認您的試算表分頁名稱

function setup() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME);
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(["ID", "日期", "車號", "狀態", "入料前照片URL", "車輛照片URL", "入料後照片URL", "建立時間"]);
  }
}

function formatDateStr(val) {
  if (!val) return "";
  if (val instanceof Date) {
    return Utilities.formatDate(val, "GMT+8", "yyyy-MM-dd");
  }
  return String(val).split("T")[0];
}

// 處理 GET 請求
function doGet(e) {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME);
  const data = sheet.getDataRange().getValues();
  
  const action = e.parameter.action; // 可透過網址參數決定要拿什麼資料
  
  if (action === "query") {
    // 查詢模式：回傳所有歷史紀錄 (越新的在越前面)
    let allRecords = [];
    for (let i = data.length - 1; i >= 1; i--) {
      allRecords.push({
        id: String(data[i][0]),
        date: formatDateStr(data[i][1]),
        license_plate: String(data[i][2]),
        status: String(data[i][3]),
        tBeforeUrl: data[i][4],
        vPhotoUrl: data[i][5],
        tAfterUrl: data[i][6],
        created_at: String(data[i][7])
      });
    }
    return ContentService.createTextOutput(JSON.stringify({ records: allRecords }))
      .setMimeType(ContentService.MimeType.JSON);
      
  } else {
    // 預設模式：只回傳 pending 列表
    let pendingRecords = [];
    for (let i = 1; i < data.length; i++) {
      if (data[i][3] === "pending") {
        pendingRecords.push({
          id: String(data[i][0]),
          date: formatDateStr(data[i][1]),
          license_plate: String(data[i][2]),
          created_at: String(data[i][7])
        });
      }
    }
    return ContentService.createTextOutput(JSON.stringify({ records: pendingRecords }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

// 處理 POST 請求 (新增或更新)
function doPost(e) {
  // 加入全域腳本鎖，防止手機並行送出兩次請求產生競態寫入重複列
  const lock = LockService.getScriptLock();
  try {
    lock.waitLock(30000); // 最多等待 30 秒排隊處理
    const params = JSON.parse(e.postData.contents);
    const action = params.action;
    
    if (action === "before_feed") {
      return handleBeforeFeed(params);
    } else if (action === "after_feed") {
      return handleAfterFeed(params);
    } else if (action === "complete_feed") {
      return handleCompleteFeed(params);
    }
    
    return jsonResponse({ success: false, detail: "未知的 action" }, 400);
  } catch (err) {
    return jsonResponse({ success: false, detail: err.toString() }, 500);
  } finally {
    lock.releaseLock();
  }
}

function handleBeforeFeed(params) {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME);
  const { id, date, license_plate, tank_level_before_b64, vehicle_photo_b64, t_name, v_name } = params;
  
  // 檢查是否重複 ID 或重複日期車號
  const data = sheet.getDataRange().getValues();
  for (let i = 1; i < data.length; i++) {
    const rowId = String(data[i][0]).trim();
    const rowDate = String(data[i][1]).trim();
    const rowPlate = String(data[i][2]).trim();

    if (rowId === String(id).trim()) {
      return jsonResponse({ success: true, message: "ID 已存在，略過新增" });
    }
    if (rowDate === String(date).trim() && rowPlate === String(license_plate).trim()) {
      return jsonResponse({ success: false, detail: "此日期與車號已登錄過！" }, 400);
    }
  }

  // 存檔到 Drive
  const t_url = saveBase64ToDrive(tank_level_before_b64, `before_${date}_${license_plate}_${t_name}`);
  const v_url = saveBase64ToDrive(vehicle_photo_b64, `vehicle_${date}_${license_plate}_${v_name}`);
  
  // 寫入 Sheets
  const timestamp = Utilities.formatDate(new Date(), "GMT+8", "yyyy-MM-dd HH:mm:ss");
  sheet.appendRow([String(id), date, license_plate, "pending", t_url, v_url, "", timestamp]);
  
  return jsonResponse({ success: true, message: "入料前資料已儲存至 Google 雲端" });
}

// 一次性寫入（針對離線時前、後都在手機完成的情況）
function handleCompleteFeed(params) {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME);
  const { id, date, license_plate, tank_level_before_b64, vehicle_photo_b64, tank_level_after_b64, t_name, v_name, a_name } = params;

  const data = sheet.getDataRange().getValues();
  for (let i = 1; i < data.length; i++) {
    const rowId = String(data[i][0]).trim();
    if (rowId === String(id).trim()) {
      // 若已經存在且已 completed，直接回傳成功
      return jsonResponse({ success: true, message: "紀錄已存在且完成" });
    }
  }

  const t_url = saveBase64ToDrive(tank_level_before_b64, `before_${date}_${license_plate}_${t_name}`);
  const v_url = saveBase64ToDrive(vehicle_photo_b64, `vehicle_${date}_${license_plate}_${v_name}`);
  const a_url = saveBase64ToDrive(tank_level_after_b64, `after_${date}_${license_plate}_${a_name}`);

  const timestamp = Utilities.formatDate(new Date(), "GMT+8", "yyyy-MM-dd HH:mm:ss");
  sheet.appendRow([String(id), date, license_plate, "completed", t_url, v_url, a_url, timestamp]);

  return jsonResponse({ success: true, message: "完整入料記錄已直接存入 Google 雲端" });
}

function handleAfterFeed(params) {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME);
  const { id, tank_level_after_b64, a_name } = params;
  
  const data = sheet.getDataRange().getValues();
  let rowIndex = -1;
  let date = "";
  let license_plate = "";
  
  for (let i = 1; i < data.length; i++) {
    const rowId = String(data[i][0]).trim();
    if (rowId === String(id).trim()) {
      if (data[i][3] === "pending") {
        rowIndex = i + 1;
        date = data[i][1];
        license_plate = data[i][2];
        break;
      } else if (data[i][3] === "completed") {
        return jsonResponse({ success: true, message: "已經是完成狀態" });
      }
    }
  }
  
  if (rowIndex === -1) {
    // 檢查是否已經 completed
    for (let i = 1; i < data.length; i++) {
      if (data[i][0] == id && data[i][3] === "completed") {
        return jsonResponse({ success: true, message: "已經更新過了" });
      }
    }
    return jsonResponse({ success: false, detail: "找不到該筆待入料紀錄" }, 404);
  }

  // 存檔到 Drive
  const a_url = saveBase64ToDrive(tank_level_after_b64, `after_${date}_${license_plate}_${a_name}`);
  
  // 更新 Sheets (狀態與第三張照片)
  sheet.getRange(rowIndex, 4).setValue("completed");
  sheet.getRange(rowIndex, 7).setValue(a_url);
  
  return jsonResponse({ success: true, message: "入料後記錄已更新至 Google 雲端" });
}

// 輔助函式：將 Base64 轉成檔案並存入 Drive 特定資料夾，回傳檔案網址
function saveBase64ToDrive(base64Str, filename) {
  if (!base64Str) return "";
  
  // 1. 尋找或建立「回收液照片歸檔」資料夾
  const folderName = "回收液照片歸檔";
  let folder;
  const folders = DriveApp.getFoldersByName(folderName);
  if (folders.hasNext()) {
    folder = folders.next();
  } else {
    folder = DriveApp.createFolder(folderName);
  }

  // 2. 轉換與存檔
  const base64Data = base64Str.split(",")[1] || base64Str; 
  const blob = Utilities.newBlob(Utilities.base64Decode(base64Data), MimeType.JPEG, filename);
  const file = folder.createFile(blob);
  
  // 3. 設定權限為知道連結者可檢視
  file.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
  return file.getUrl();
}

function jsonResponse(data, code=200) {
  return ContentService.createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
}
