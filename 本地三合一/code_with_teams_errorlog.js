// ==========================================
// 備份時間: 2026-10-11
// 說明: 整合 Error_Log 試算表寫入 + Teams (Power Automate) 自動錯誤推播版本
// ==========================================

// ==========================================
// 系統設定區 (自動化動態讀取版)
// ==========================================
var DEFAULT_USAGE_LIMIT = 900; 
var BACKUP_FOLDER_ID = "16lBdHf67N3QVfBEbnU2O5fgFa_6H1j4v"; 
var TEAMS_WEBHOOK_URL = "https://defaulta46d9e33ad01451aaec52ee61979c6.d0.environment.api.powerplatform.com:443/powerautomate/automations/direct/cu/22/workflows/91b9b15b99a64990bf3f7116c031dea4/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=huhEyZ8m-m8EKJ7JXRmhR-CtuVI83kTLRADHB12g-7k";

// ==========================================
// 0. 動態設定管理機制
// ==========================================
function setupConfigSheet() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName("設定");
  
  if (!sheet) {
    sheet = ss.insertSheet("設定");
    sheet.appendRow(["設定項目", "設定值", "說明"]);
    sheet.getRange("A1:C1").setFontWeight("bold").setBackground("#f3f4f6");
    
    var defaults = [
      ["VISION_API_KEY", "填入你的_Google_Vision_金鑰_1", "主力 OCR 金鑰 (每月前 1000 次)"],
      ["VISION_API_KEY", "填入你的_Google_Vision_金鑰_2", "備用 OCR 金鑰"],
      ["GEMINI_API_KEY", "填入你的_Gemini_專用金鑰_1", "Gemini 主力備援金鑰"],
      ["GEMINI_API_KEY", "填入你的_Gemini_專用金鑰_2", "Gemini 第二把備援金鑰"],
      ["GEMINI_MODEL", "gemini-3.6-flash", "第 1 順位 (每日 20 次)"],
      ["GEMINI_MODEL", "gemini-3.5-flash", "第 2 順位 (每日 20 次)"],
      ["GEMINI_MODEL", "gemini-3.5-flash-lite", "第 3 順位 (每日 500 次)"],
      ["GEMINI_MODEL", "gemini-3.1-flash-lite", "第 4 順位 (每日 500 次)"],
      ["USAGE_LIMIT", "900", "Vision Key 切換閥值"]
    ];
    
    sheet.getRange(2, 1, defaults.length, 3).setValues(defaults);
    sheet.setColumnWidth(1, 150);
    sheet.setColumnWidth(2, 350);
    sheet.setColumnWidth(3, 250);
  }

  // 初始化 API_Log 分頁
  var logSheet = ss.getSheetByName("API_Log");
  if (!logSheet) {
    logSheet = ss.insertSheet("API_Log");
    logSheet.appendRow(["呼叫時間 (Time)", "API 類型 (Type)", "使用模型 (Model)", "使用金鑰 (Key)", "執行狀態 (Status)", "備註說明 (Note)"]);
    logSheet.getRange("A1:F1").setFontWeight("bold").setBackground("#e2e8f0");
    logSheet.setColumnWidth(1, 150);
    logSheet.setColumnWidth(4, 250);
    logSheet.setColumnWidth(6, 300);
  }

  // 初始化 Error_Log 分頁
  var errSheet = ss.getSheetByName("Error_Log");
  if (!errSheet) {
    errSheet = ss.insertSheet("Error_Log");
    errSheet.appendRow(["時間", "料號", "供應商", "批號", "地點/槽號", "失敗原因", "地磅辨識全文", "COA辨識全文"]);
    errSheet.getRange("A1:H1").setFontWeight("bold").setBackground("#fee2e2");
  }
  
  return "✅『設定』分頁、『API_Log』與『Error_Log』已成功建立！";
}

function getSystemConfig() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName("設定");
  var config = {
    visionKeys: [],
    geminiKeys: [],
    geminiModels: [],
    usageLimit: DEFAULT_USAGE_LIMIT
  };
  
  if (!sheet) return config;
  
  var data = sheet.getDataRange().getValues();
  for (var i = 1; i < data.length; i++) {
    var key = data[i][0] ? String(data[i][0]).trim() : "";
    var val = data[i][1] ? String(data[i][1]).trim() : "";
    if (!key || !val) continue;
    
    if (key === "VISION_API_KEY") config.visionKeys.push(val);
    else if (key === "GEMINI_API_KEY") config.geminiKeys.push(val);
    else if (key === "GEMINI_MODEL") config.geminiModels.push(val);
    else if (key === "USAGE_LIMIT") config.usageLimit = parseInt(val) || DEFAULT_USAGE_LIMIT;
  }
  
  return config;
}

// ==========================================
// 1. 路由控制
// ==========================================
function doGet(e) {
  return HtmlService.createTemplateFromFile('Index')
      .evaluate()
      .setTitle('台積三合一單與COA 雙重核對系統')
      .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

// ==========================================
// 2. 查詢系統資料取得邏輯
// ==========================================
function getLogData(page, searchText, startDate, endDate) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var allSheets = ss.getSheets();
  var allData = [];

  for (var i = 0; i < allSheets.length; i++) {
    var sheet = allSheets[i];
    var sheetName = sheet.getName();
    if (sheetName === "Data" || sheetName.startsWith("Data_")) {
      var lastRow = sheet.getLastRow();
      if (lastRow > 1) {
        var sheetData = sheet.getRange(2, 1, lastRow - 1, sheet.getLastColumn()).getValues();
        allData = allData.concat(sheetData);
      }
    }
  }

  allData.sort(function(a, b) { return new Date(b[0]) - new Date(a[0]); });

  var filteredData = allData.filter(function(row) {
    var rowBatch = row[3] ? String(row[3]).toLowerCase() : ""; 
    var rowMaterial = row[1] ? String(row[1]).toLowerCase() : "";
    var rowSourceOrder = row[11] ? String(row[11]).toLowerCase() : ""; 
    var rowDocOrder = row[12] ? String(row[12]).toLowerCase() : "";  

    var isMatch = true;
    if (searchText) {
      var q = searchText.toLowerCase();
      if (!rowBatch.includes(q) && !rowMaterial.includes(q) && !rowSourceOrder.includes(q) && !rowDocOrder.includes(q)) {
        isMatch = false;
      }
    }
    if (isMatch && (startDate || endDate)) {
      var dateStr = Utilities.formatDate(new Date(row[0]), "Asia/Taipei", "yyyy-MM-dd");
      if (startDate && dateStr < startDate) isMatch = false;
      if (endDate && dateStr > endDate) isMatch = false;
    }
    return isMatch;
  });

  var itemsPerPage = 15; 
  var totalRecords = filteredData.length;
  var totalPages = Math.ceil(totalRecords / itemsPerPage);
  if (page < 1) page = 1;
  if (page > totalPages && totalPages > 0) page = totalPages;

  var startIndex = (page - 1) * itemsPerPage;
  var endIndex = startIndex + itemsPerPage;
  var pagedData = filteredData.slice(startIndex, endIndex);

  var resultData = pagedData.map(function(row) {
    return formatRowData(row);
  });

  return { records: resultData, total: totalRecords, totalPages: totalPages, currentPage: page };
}

function getExportData(searchText, startDate, endDate) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var allSheets = ss.getSheets();
  var allData = [];

  for (var i = 0; i < allSheets.length; i++) {
    var sheet = allSheets[i];
    var sheetName = sheet.getName();
    if (sheetName === "Data" || sheetName.startsWith("Data_")) {
      var lastRow = sheet.getLastRow();
      if (lastRow > 1) {
        var sheetData = sheet.getRange(2, 1, lastRow - 1, sheet.getLastColumn()).getValues();
        allData = allData.concat(sheetData);
      }
    }
  }
  allData.sort(function(a, b) { return new Date(b[0]) - new Date(a[0]); });

  var filteredData = allData.filter(function(row) {
    var rowBatch = row[3] ? String(row[3]).toLowerCase() : ""; 
    var rowMaterial = row[1] ? String(row[1]).toLowerCase() : "";
    var rowSourceOrder = row[11] ? String(row[11]).toLowerCase() : ""; 
    var rowDocOrder = row[12] ? String(row[12]).toLowerCase() : "";  

    var isMatch = true;
    if (searchText) {
      var q = searchText.toLowerCase();
      if (!rowBatch.includes(q) && !rowMaterial.includes(q) && !rowSourceOrder.includes(q) && !rowDocOrder.includes(q)) {
        isMatch = false;
      }
    }
    if (isMatch && (startDate || endDate)) {
      var dateStr = Utilities.formatDate(new Date(row[0]), "Asia/Taipei", "yyyy-MM-dd");
      if (startDate && dateStr < startDate) isMatch = false;
      if (endDate && dateStr > endDate) isMatch = false;
    }
    return isMatch;
  });

  return filteredData.map(function(row) { return formatRowData(row); });
}

function formatRowData(row) {
    var status = row[8];     
    var photoBatch = row[9]; 
    var photoLoc = row[10];
    var sourceOrder = row[11] || "";
    var docOrder = row[12] || ""; 

    var foundLinks = [];
    for (var i = 7; i < row.length; i++) {
      if (String(row[i]).startsWith("http")) foundLinks.push(String(row[i]));
    }
    if (!photoBatch || !String(photoBatch).startsWith("http")) { if (foundLinks.length > 0) photoBatch = foundLinks[0]; }
    if (!photoLoc || !String(photoLoc).startsWith("http")) { if (foundLinks.length > 1) photoLoc = foundLinks[1]; }
    if (String(status).startsWith("http") || status === "") { if (row[7] && !String(row[7]).startsWith("http")) status = row[7]; }

    return {
      time: Utilities.formatDate(new Date(row[0]), "Asia/Taipei", "yyyy-MM-dd HH:mm:ss"),
      material: row[1], tank: row[2], batch: row[3], supplier: row[4], location: row[5], 
      status: status, photoBatch: photoBatch, photoLoc: photoLoc, 
      sourceOrder: sourceOrder, docOrder: docOrder 
    };
}

// ==========================================
// 2.5 Teams (Power Automate) 專用通知模組
// ==========================================
function sendTeamsNotification(details) {
  if (!TEAMS_WEBHOOK_URL || TEAMS_WEBHOOK_URL.indexOf("http") !== 0) return;

  var user = details.user || "現場作業員";
  var location = details.location || "未提供";
  var tank = details.tank || "未提供";
  var time = details.time || Utilities.formatDate(new Date(), "Asia/Taipei", "yyyy-MM-dd HH:mm:ss");
  var errorDetail = details.errorDetail || "";

  // 格式完全還原 Teams 卡片截圖需求，同時涵蓋多種欄位命名相容性
  var payload = {
    // 欄位對應方式 1: 繁體中文欄位名稱
    "人員": user,
    "位置": location,
    "槽號": tank,
    "時間": time,
    "異常狀況詳細說明": errorDetail,
    
    // 欄位對應方式 2: 英文字軌命名相容
    "user": user,
    "location": location,
    "tank": tank,
    "time": time,
    "reason": errorDetail,
    "message": errorDetail,
    "title": "三合一單核對錯誤提醒",

    // 欄位對應方式 3: 內嵌 Adaptive Card (若流程直接發送卡片)
    "type": "message",
    "attachments": [
      {
        "contentType": "application/vnd.microsoft.card.adaptive",
        "content": {
          "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
          "type": "AdaptiveCard",
          "version": "1.4",
          "body": [
            {
              "type": "TextBlock",
              "text": "⚠️ 三合一單核對錯誤提醒",
              "weight": "Bolder",
              "size": "Medium",
              "color": "Warning"
            },
            {
              "type": "FactSet",
              "facts": [
                { "title": "人員：", "value": user },
                { "title": "位置：", "value": location },
                { "title": "槽號：", "value": tank },
                { "title": "時間：", "value": time }
              ]
            },
            {
              "type": "TextBlock",
              "text": "**異常狀況詳細說明：**",
              "weight": "Bolder",
              "spacing": "Medium"
            },
            {
              "type": "TextBlock",
              "text": errorDetail,
              "wrap": true
            }
          ]
        }
      }
    ]
  };

  try {
    UrlFetchApp.fetch(TEAMS_WEBHOOK_URL, {
      method: "post",
      contentType: "application/json",
      payload: JSON.stringify(payload),
      muteHttpExceptions: true
    });
  } catch (err) {
    Logger.log("Teams 推送失敗: " + err.message);
  }
}

// 錯誤日誌寫入與 Teams 觸發整合
function logVerificationError(formObject, errorReason, ocrLoc, ocrBatch) {
  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var errSheet = ss.getSheetByName("Error_Log");
    if (!errSheet) {
      errSheet = ss.insertSheet("Error_Log");
      errSheet.appendRow(["時間", "料號", "供應商", "批號", "地點/槽號", "失敗原因", "地磅辨識全文", "COA辨識全文"]);
      errSheet.getRange("A1:H1").setFontWeight("bold").setBackground("#fee2e2");
    }
    
    var timeStr = Utilities.formatDate(new Date(), "Asia/Taipei", "yyyy-MM-dd HH:mm:ss");
    var material = formObject && formObject.materialNo ? String(formObject.materialNo) : "";
    var supplier = formObject && formObject.supplier ? String(formObject.supplier) : "";
    var batch = formObject && formObject.batchNo ? String(formObject.batchNo) : "";
    var location = formObject && formObject.deliveryPlace ? String(formObject.deliveryPlace) : "";
    var tank = formObject && formObject.tankNo ? String(formObject.tankNo) : "";
    var placeTank = location + (tank ? (" / " + tank) : "");
    var user = formObject && formObject.userName ? String(formObject.userName) : "現場作業員";
    
    // 1. 寫入 Error_Log 試算表 (與截圖結構 100% 一致)
    errSheet.appendRow([
      timeStr,
      "'" + material,
      "'" + supplier,
      "'" + batch,
      placeTank,
      errorReason,
      ocrLoc || "",
      ocrBatch || ""
    ]);

    // 2. 觸發 Power Automate Teams 通知
    sendTeamsNotification({
      user: user,
      location: location,
      tank: tank,
      time: timeStr,
      errorDetail: errorReason
    });

  } catch (e) {
    Logger.log("寫入 Error_Log 或發送 Teams 失敗: " + e.message);
  }
}

// ==========================================
// 3. 掃描核對邏輯
// ==========================================
function processFormAndVerify_V10(formObject) {
  var ocrTextBatch = "", ocrTextLoc = "";
  try {
    var rawQrBatch = formObject.batchNo ? formObject.batchNo.toString().trim() : ""; 
    var rawPlace   = formObject.deliveryPlace ? formObject.deliveryPlace.toString().trim() : "";
    var rawTank    = formObject.tankNo ? formObject.tankNo.toString().trim() : ""; 
    var photoDataBatch = formObject.photoDataBatch; 
    var photoDataLoc   = formObject.photoDataLoc;   

    if (!photoDataBatch || !photoDataLoc) throw new Error("缺少照片資料");

    try {
      var config = getSystemConfig();
      ocrTextBatch = callVisionAPI(photoDataBatch, config); 
      ocrTextLoc   = callVisionAPI(photoDataLoc, config);   
    } catch (e) {
      var errMsg = "辨識錯誤: " + e.message;
      logVerificationError(formObject, errMsg, "", "");
      return { success: false, message: errMsg };
    }

    var extractedSourceOrder = "";
    var extractedDocOrder = "";
    var fixedOcr = ocrTextLoc.replace(/E\s+S\s+X\s+M/gi, "ESXM").replace(/ESXM\s+/gi, "ESXM");

    var matchSrc = fixedOcr.match(/\b(ESXM1[A-Z0-9\-]+)/i);
    if (matchSrc) extractedSourceOrder = matchSrc[1];

    var matchDoc = fixedOcr.match(/\b(ESXM2[A-Z0-9\-]+)/i);
    if (matchDoc) extractedDocOrder = matchDoc[1];

    if (!extractedDocOrder) {
        var matchBackup = ocrTextLoc.match(/(?:單據編號|單據)[^\w\d]*([A-Z0-9\-]+)/i);
        if (matchBackup) extractedDocOrder = matchBackup[1];
    }

    // 比對專用純淨值 (去除第一碼前綴: 批號6, 槽號5, 料號4，畫面與存檔仍保留完整值)
    var targetBatch = rawQrBatch;
    if (targetBatch.startsWith("6") && targetBatch.length > 1) {
        targetBatch = targetBatch.substring(1);
    } else if (targetBatch.length >= 11) {
        targetBatch = targetBatch.substring(1, 11);
    }

    var targetTank = rawTank; 
    if (targetTank.startsWith("5") && targetTank.length > 1) {
        targetTank = targetTank.substring(1);
    }

    var targetPlace = rawPlace; 

    var rawMaterial = formObject.materialNo ? formObject.materialNo.toString().trim() : "";
    var targetMaterial = rawMaterial;
    if (targetMaterial.startsWith("4") && targetMaterial.length > 1) {
        targetMaterial = targetMaterial.substring(1);
    }

    var check1 = advancedFuzzyCheck(ocrTextBatch, targetBatch);
    var check2 = smartLocationCheck(ocrTextLoc, targetPlace); 
    
    // 槽號比對：先嘗試排除批號以避免誤判
    var tempOcrForTank = ocrTextLoc;
    if (targetBatch.length > 5) {
        tempOcrForTank = ocrTextLoc.toUpperCase().split(targetBatch.toUpperCase()).join(""); 
    }
    var check3 = advancedFuzzyCheck(tempOcrForTank, targetTank);
    // 防呆備援：若批號本身內嵌槽號（如 26A11E3181 內含 E318）導致排除後找不到，且全文確實包含槽號，則視為通過
    if (!check3.pass) {
        var fallbackCheckTank = advancedFuzzyCheck(ocrTextLoc, targetTank);
        if (fallbackCheckTank.pass) {
            check3 = fallbackCheckTank;
        }
    }

    var check4 = advancedFuzzyCheck(ocrTextLoc, targetBatch);
    var check5 = advancedFuzzyCheck(ocrTextLoc, targetMaterial);

    var isSuccess = check1.pass && check2.pass && check3.pass && check4.pass && check5.pass;
    var msg = "";

    if (isSuccess) {
      var urlBatch = "上傳失敗", urlLoc = "上傳失敗";
      try {
        urlBatch = saveImageToDrive(photoDataBatch, "Batch_" + rawQrBatch);
        urlLoc   = saveImageToDrive(photoDataLoc,   "Loc_" + rawPlace);
      } catch(e) {}

      var ss = SpreadsheetApp.getActiveSpreadsheet();
      var targetSheetName = getTargetSheetName();
      var ws = ss.getSheetByName(targetSheetName);
      if(!ws) { 
          ws = ss.insertSheet(targetSheetName); 
          try { ss.setActiveSheet(ws); ss.moveActiveSheet(2); } catch(e){} 
          ws.appendRow(["時間","料號","槽號","批號","供應商","原始地點","比對用地點","原始QR","狀態","COA照片","地點照片", "來源單號", "磅單編號"]); 
      }
      ws.appendRow([
        new Date(), "'" + (formObject.materialNo||""), "'" + (formObject.tankNo||""), "'" + (formObject.batchNo||""), 
        formObject.supplier, formObject.deliveryPlace, targetPlace, "'" + (formObject.rawQr||""), 
        "核對成功", urlBatch, urlLoc, extractedSourceOrder, extractedDocOrder      
      ]);

      msg = "✅ 完美！全數核對成功\n--------------------\n";
      if(extractedSourceOrder) msg += "📄 來源單號：" + extractedSourceOrder + "\n";
      if(extractedDocOrder)    msg += "🎫 磅單編號：" + extractedDocOrder + "\n"; 
      msg += "\n1. COA 批號：OK\n2. 地磅 地點：OK\n3. 地磅 槽號：OK\n4. 地磅 批號：OK\n5. 地磅 料號：OK";
      return { success: true, message: msg };

    } else {
      msg = "❌ 核對失敗 (未存檔)，請檢查：\n";
      if (!check1.pass) msg += "⚠️ COA照片：找不到批號 (" + targetBatch + ")\n";
      if (!check2.pass) msg += "⚠️ 地磅照片：地點不符 (" + targetPlace + ")\n";
      if (!check3.pass) msg += "⚠️ 地磅照片：找不到槽號 (" + targetTank + ")\n";
      if (!check4.pass) msg += "⚠️ 地磅照片：畫面批號錯誤 (" + targetBatch + ")\n";
      if (!check5.pass) msg += "⚠️ 地磅照片：找不到料號 (" + targetMaterial + ")\n";

      // ★ 核心修復：寫入 Error_Log 試算表，並自動發送 Teams 通知
      logVerificationError(formObject, msg, ocrTextLoc, ocrTextBatch);

      return { success: false, message: msg };
    }
  } catch (e) { 
    var exMsg = "錯誤: " + e.toString();
    logVerificationError(formObject, exMsg, ocrTextLoc, ocrTextBatch);
    return { success: false, message: exMsg }; 
  }
}

// ==========================================
// 4. API 呼叫與瀑布流備援邏輯
// ==========================================
function getSmartApiKey(visionKeys, usageLimit) {
  if (!visionKeys || visionKeys.length === 0) return "";
  
  var props = PropertiesService.getScriptProperties();
  var currentMonth = Utilities.formatDate(new Date(), "Asia/Taipei", "yyyy-MM");
  var lastResetMonth = props.getProperty("LAST_RESET_MONTH");
  if (lastResetMonth !== currentMonth) {
    props.setProperty("USAGE_COUNT", "0");
    props.setProperty("LAST_RESET_MONTH", currentMonth);
  }
  
  var usage = parseInt(props.getProperty("USAGE_COUNT") || "0");
  var keyIndex = Math.floor(usage / usageLimit);
  
  if (keyIndex >= visionKeys.length) {
    keyIndex = visionKeys.length - 1;
  }
  
  return visionKeys[keyIndex];
}

function incrementApiUsage() {
  var props = PropertiesService.getScriptProperties();
  var usage = parseInt(props.getProperty("USAGE_COUNT") || "0");
  props.setProperty("USAGE_COUNT", String(usage + 1));
}

function logApiUsage(apiType, modelName, keyString, status, note) {
  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var logSheet = ss.getSheetByName("API_Log");
    if (!logSheet) return; 
    
    var maskedKey = "N/A";
    if (keyString && keyString.length > 12) {
      maskedKey = keyString.substring(0, 8) + "..." + keyString.substring(keyString.length - 4);
    } else if (keyString) {
      maskedKey = keyString;
    }
    
    var timeStr = Utilities.formatDate(new Date(), "Asia/Taipei", "yyyy-MM-dd HH:mm:ss");
    logSheet.appendRow([timeStr, apiType, modelName, maskedKey, status, note || ""]);
  } catch (e) {
    Logger.log("寫入日誌失敗: " + e.message);
  }
}

function callVisionAPI(base64Data, config) {
  if (!config) config = getSystemConfig();
  
  if (config.visionKeys && config.visionKeys.length > 0) {
    var currentKey = getSmartApiKey(config.visionKeys, config.usageLimit);
    var url = "https://vision.googleapis.com/v1/images:annotate?key=" + currentKey;
    var payload = { "requests": [{ "image": { "content": base64Data.split(',')[1] }, "features": [{ "type": "TEXT_DETECTION" }] }] };
    
    try {
      var response = UrlFetchApp.fetch(url, { "method": "post", "contentType": "application/json", "payload": JSON.stringify(payload), "muteHttpExceptions": true });
      var json = JSON.parse(response.getContentText());
      
      if (!json.error) {
        incrementApiUsage(); 
        logApiUsage("Google Vision", "default", currentKey, "✅ 成功", "");
        return (json.responses && json.responses[0].fullTextAnnotation) ? json.responses[0].fullTextAnnotation.text : "";
      } else {
        Logger.log("Google Vision API 失敗或額度耗盡: " + json.error.message);
        logApiUsage("Google Vision", "default", currentKey, "❌ 失敗", json.error.message);
      }
    } catch (e) {
      Logger.log("Google Vision API 連線失敗: " + e.message);
      logApiUsage("Google Vision", "default", currentKey, "❌ 連線失敗", e.message);
    }
  }

  if (config.geminiKeys && config.geminiKeys.length > 0 && config.geminiModels && config.geminiModels.length > 0) {
    for (var i = 0; i < config.geminiModels.length; i++) {
      var modelName = config.geminiModels[i];
      for (var k = 0; k < config.geminiKeys.length; k++) {
        var geminiKey = config.geminiKeys[k];
        Logger.log("嘗試呼叫備援模型: " + modelName + " (使用第 " + (k + 1) + " 把金鑰)");
        
        var geminiResult = callSpecificGeminiModel(base64Data, geminiKey, modelName);
        if (geminiResult !== null) {
          logApiUsage("Gemini Fallback", modelName, geminiKey, "✅ 成功", "備援接手成功");
          return geminiResult;
        }
      }
    }
  }
  
  throw new Error("所有辨識 API 皆已用盡或發生錯誤！請檢查試算表設定金鑰。");
}

function callSpecificGeminiModel(base64Data, apiKey, modelName) {
  var url = "https://generativelanguage.googleapis.com/v1beta/models/" + modelName + ":generateContent?key=" + apiKey;
  var rawBase64 = base64Data.split(',')[1];
  
  var payload = {
    "contents": [
      {
        "parts": [
          { "text": "請將這張圖片裡的所有文字完整讀取出來，不要加上任何額外的說明或引號。" },
          {
            "inlineData": {
              "mimeType": "image/jpeg",
              "data": rawBase64
            }
          }
        ]
      }
    ]
  };
  
  try {
    var response = UrlFetchApp.fetch(url, {
      "method": "post",
      "contentType": "application/json",
      "payload": JSON.stringify(payload),
      "muteHttpExceptions": true
    });
    
    var json = JSON.parse(response.getContentText());
    if (json.error) {
      Logger.log("Gemini " + modelName + " 失敗：" + json.error.message);
      logApiUsage("Gemini Fallback", modelName, apiKey, "❌ 失敗", json.error.message);
      return null;
    }
    
    if (json.candidates && json.candidates.length > 0 && json.candidates[0].content && json.candidates[0].content.parts) {
      return json.candidates[0].content.parts[0].text;
    }
  } catch (e) {
    Logger.log("Gemini 連線異常：" + e.message);
  }
  
  return null;
}

function analyzeLabelPhoto(photoData) {
  try {
    var config = getSystemConfig();
    var ocrText = callVisionAPI(photoData, config);
    if (!ocrText) throw new Error("照片中未發現文字");
    var result = { material: "", tank: "", batch: "", supplier: "", place: "" };

    var matchMat = ocrText.match(/(?:料號|TSMC料號)[^\w\d]*([A-Z0-9\-_]{4,})/i);
    if (matchMat) { result.material = matchMat[1]; } 
    else { var fallback = ocrText.match(/\b([4L][A-Z0-9]{8,12})\b/); if (fallback) result.material = fallback[1]; }

    var matchTank = ocrText.match(/槽號[^\w\d]*([A-Z0-9\s]+)/i);
    if (matchTank) {
        var cleanTank = matchTank[1].replace(/\s/g, "");
        if (cleanTank.length >= 3) result.tank = cleanTank;
    }
    if (!result.tank) {
        var fallbackTank = ocrText.match(/\b(\d?E\d{2,4})\b/);
        if (fallbackTank) result.tank = fallbackTank[1];
    }

    var matchBatch = ocrText.match(/批號[^\w\d]*([A-Z0-9]+)/i);
    if (matchBatch) result.batch = matchBatch[1];

    var matchSup = ocrText.match(/供應商[^\w\d]*(\d{8,})/i); 
    if (matchSup) { result.supplier = matchSup[1]; }
    if (!result.supplier && ocrText.toUpperCase().includes("SHINY")) { result.supplier = "Shiny"; }

    var matchPlace = ocrText.match(/(?:送達地點|地點|廠區)[^\w\d]*([A-Z0-9]+)/i);
    if (matchPlace) { result.place = matchPlace[1]; } 
    else { var matchTSMC = ocrText.match(/(F\d+[A-Z]?)/i); if (matchTSMC) result.place = matchTSMC[1]; }

    return { success: true, data: result };
  } catch (e) { return { success: false, message: e.toString() }; }
}

function getTargetSheetName() {
  var now = new Date(); var year = now.getFullYear(); var month = now.getMonth() + 1; 
  var startMonth = Math.floor((month - 1) / 2) * 2 + 1; var endMonth = startMonth + 1;
  var pad = function(n) { return n < 10 ? '0' + n : n; };
  return "Data_" + year + "_" + pad(startMonth) + "-" + pad(endMonth);
}

function smartLocationCheck(ocrText, target) {
  if (!ocrText || !target) return { pass: false };
  var cleanOCR = ocrText.toUpperCase().replace(/[\s-]/g, ""); 
  var cleanTarget = target.toUpperCase().replace(/[\s-]/g, "");

  if (cleanOCR.includes(cleanTarget)) return { pass: true };

  var processedTarget = cleanTarget;
  if (processedTarget.startsWith("E")) {
      processedTarget = processedTarget.substring(1);
  }

  if (processedTarget.length === 8) {
      var part1 = processedTarget.substring(0, 4);
      var part2 = processedTarget.substring(4);
      
      if (cleanOCR.includes(part1) && cleanOCR.includes(part2)) {
          return { pass: true };
      }
  }

  var fuzzyOCR = cleanOCR.replace(/2/g, "3");
  var fuzzyTarget = processedTarget.replace(/2/g, "3");
  
  if (fuzzyTarget.length === 8) {
      var fPart1 = fuzzyTarget.substring(0, 4);
      var fPart2 = fuzzyTarget.substring(4);
      if (fuzzyOCR.includes(fPart1) && fuzzyOCR.includes(fPart2)) {
          return { pass: true };
      }
  }

  return { pass: false };
}

function advancedFuzzyCheck(ocrText, target) {
  if (!ocrText || !target) return { pass: false };
  var cleanOCR = ocrText.toUpperCase().replace(/[\s-]/g, ""); 
  var cleanTarget = target.toUpperCase().replace(/[\s-]/g, "");
  if (cleanTarget.length === 0) return { pass: false };

  function testMatch(t) {
    if (!t || t.length === 0) return false;
    if (cleanOCR.includes(t)) return true;
    if (cleanOCR.includes(t.replace(/8/g, "B"))) return true;
    if (cleanOCR.includes(t.replace(/B/g, "8"))) return true;
    if (cleanOCR.includes(t.replace(/3/g, "5"))) return true;
    if (cleanOCR.includes(t.replace(/5/g, "3"))) return true;
    var variant1 = t.replace(/3/g, "5").replace(/8/g, "B");
    if (cleanOCR.includes(variant1)) return true;
    var variant2 = t.replace(/5/g, "3").replace(/B/g, "8");
    if (cleanOCR.includes(variant2)) return true;
    var fO = cleanOCR.replace(/[OIZS]/g, function(m){return {'O':'0','I':'1','Z':'2','S':'5'}[m]});
    var fT = t.replace(/[OIZS]/g, function(m){return {'O':'0','I':'1','Z':'2','S':'5'}[m]});
    if (fO.includes(fT)) return true;
    return false;
  }

  // 1. 完全或容錯比對 cleanTarget
  if (testMatch(cleanTarget)) return { pass: true };

  // 2. 自動去除第一碼前綴比對 (若開頭為數字且長度 >= 3)
  if (cleanTarget.match(/^\d/)) {
    var noPrefix = cleanTarget.substring(1);
    if (noPrefix.length >= 3 && testMatch(noPrefix)) {
      return { pass: true };
    }
  }

  return { pass: false };
}

function saveImageToDrive(base64Data, prefix) {
  if (!BACKUP_FOLDER_ID) return "";
  var blob = Utilities.newBlob(Utilities.base64Decode(base64Data.split(',')[1]), base64Data.split(';')[0].split(':')[1], prefix + "_" + Utilities.formatDate(new Date(), "GMT+8", "HHmmss") + ".jpg");
  var file = DriveApp.getFolderById(BACKUP_FOLDER_ID).createFile(blob);
  file.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
  return file.getUrl();
}

// ==========================================
// 5. PWA 專用 API 接口 (支援外部 fetch 呼叫)
// ==========================================
function doPost(e) {
  if (typeof e === 'undefined') {
    return ContentService.createTextOutput(JSON.stringify({ error: 'No data' })).setMimeType(ContentService.MimeType.JSON);
  }

  try {
    var requestData = JSON.parse(e.postData.contents);
    var action = requestData.action;
    var result = {};

    if (action === "analyzeLabelPhoto") {
      result = analyzeLabelPhoto(requestData.base64Data);
    } 
    else if (action === "processFormAndVerify") {
      result = processFormAndVerify_V10(requestData.formObject);
    } 
    else if (action === "getLogData") {
      result = getLogData(requestData.page, requestData.searchText, requestData.startDate, requestData.endDate);
    } 
    else if (action === "getExportData") {
      result = getExportData(requestData.searchText, requestData.startDate, requestData.endDate);
    } 
    else {
      result = { success: false, message: "未知的 API 動作: " + action };
    }

    return ContentService.createTextOutput(JSON.stringify(result))
      .setMimeType(ContentService.MimeType.JSON);

  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({ success: false, message: error.toString() }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}
