// ==========================================
// 設定區 (V37 地點寬容判讀版)
// ==========================================
var API_KEY_1 = "AIzaSyCxpDwmsFfKtYkz-_rnqPJW_iVh5j-wQd4"; // 請填入 shihwei0809
var API_KEY_2 = "AIzaSyCdl7WZKnyUtYL0mubKslz7Cvq2wqStS_8"; // 請填入 syhm10150

var USAGE_LIMIT = 900; 
var BACKUP_FOLDER_ID = "16lBdHf67N3QVfBEbnU2O5fgFa_6H1j4v"; 

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
// 3. 掃描核對邏輯
// ==========================================
function processFormAndVerify_V10(formObject) {
  try {
    var rawQrBatch = formObject.batchNo ? formObject.batchNo.toString().trim() : ""; 
    var rawPlace   = formObject.deliveryPlace ? formObject.deliveryPlace.toString().trim() : "";
    var rawTank    = formObject.tankNo ? formObject.tankNo.toString().trim() : ""; 
    var photoDataBatch = formObject.photoDataBatch; 
    var photoDataLoc   = formObject.photoDataLoc;   

    if (!photoDataBatch || !photoDataLoc) throw new Error("缺少照片資料");

    var ocrTextBatch = "", ocrTextLoc = "";
    try {
      ocrTextBatch = callVisionAPI(photoDataBatch); 
      ocrTextLoc   = callVisionAPI(photoDataLoc);   
    } catch (e) {
      return { success: false, message: "OCR 錯誤: " + e.message };
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

    // 核對邏輯 (targetPlace 不再預先去頭去尾，改由 smartLocationCheck 統一處理)
    var targetBatch = rawQrBatch.length >= 11 ? rawQrBatch.substring(1, 11) : rawQrBatch;
    var targetTank  = rawTank; 
    var targetPlace = rawPlace; 

    var check1 = advancedFuzzyCheck(ocrTextBatch, targetBatch);
    var check2 = smartLocationCheck(ocrTextLoc, targetPlace); // ★ 使用新的地點比對邏輯
    
    var tempOcrForTank = ocrTextLoc;
    if (targetBatch.length > 5) {
        tempOcrForTank = ocrTextLoc.toUpperCase().split(targetBatch.toUpperCase()).join(""); 
    }
    var check3 = advancedFuzzyCheck(tempOcrForTank, targetTank);
    var check4 = advancedFuzzyCheck(ocrTextLoc, targetBatch);

    var isSuccess = check1.pass && check2.pass && check3.pass && check4.pass;
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
      msg += "\n1. COA 批號：OK\n2. 地磅 地點：OK\n3. 地磅 槽號：OK\n4. 地磅 批號：OK";
      return { success: true, message: msg };

    } else {
      msg = "❌ 核對失敗 (未存檔)，請檢查：\n";
      if (!check1.pass) msg += "⚠️ COA照片：找不到批號 (" + targetBatch + ")\n";
      if (!check2.pass) msg += "⚠️ 地磅照片：地點不符 (" + targetPlace + ")\n";
      if (!check3.pass) msg += "⚠️ 地磅照片：找不到槽號 (" + targetTank + ")\n";
      if (!check4.pass) msg += "⚠️ 地磅照片：畫面批號錯誤 (" + targetBatch + ")\n";
      return { success: false, message: msg };
    }
  } catch (e) { return { success: false, message: "錯誤: " + e.toString() }; }
}

// ==========================================
// 4. 工具函式
// ==========================================
function getSmartApiKey() {
  var props = PropertiesService.getScriptProperties();
  var currentMonth = Utilities.formatDate(new Date(), "Asia/Taipei", "yyyy-MM");
  var lastResetMonth = props.getProperty("LAST_RESET_MONTH");
  if (lastResetMonth !== currentMonth) {
    props.setProperty("USAGE_COUNT", "0");
    props.setProperty("LAST_RESET_MONTH", currentMonth);
  }
  var usage = parseInt(props.getProperty("USAGE_COUNT") || "0");
  return (usage < USAGE_LIMIT) ? API_KEY_1 : API_KEY_2;
}

function incrementApiUsage() {
  var props = PropertiesService.getScriptProperties();
  var usage = parseInt(props.getProperty("USAGE_COUNT") || "0");
  props.setProperty("USAGE_COUNT", String(usage + 1));
}

function callVisionAPI(base64Data) {
  var currentKey = getSmartApiKey(); 
  var url = "https://vision.googleapis.com/v1/images:annotate?key=" + currentKey;
  var payload = { "requests": [{ "image": { "content": base64Data.split(',')[1] }, "features": [{ "type": "TEXT_DETECTION" }] }] };
  var response = UrlFetchApp.fetch(url, { "method": "post", "contentType": "application/json", "payload": JSON.stringify(payload), "muteHttpExceptions": true });
  incrementApiUsage(); 
  var json = JSON.parse(response.getContentText());
  return (json.responses && json.responses[0].fullTextAnnotation) ? json.responses[0].fullTextAnnotation.text : "";
}

function analyzeLabelPhoto(photoData) {
  try {
    var ocrText = callVisionAPI(photoData);
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

// ★ V43 修正：嚴格移除 E 並拆分 8 碼（前四廠別、後四廠區）雙重相符判定
function smartLocationCheck(ocrText, target) {
  if (!ocrText || !target) return { pass: false };
  var cleanOCR = ocrText.toUpperCase().replace(/[\s-]/g, ""); 
  var cleanTarget = target.toUpperCase().replace(/[\s-]/g, "");

  // 1. 完全命中 (基本防呆)
  if (cleanOCR.includes(cleanTarget)) return { pass: true };

  // 2. 移除開頭的 E
  var processedTarget = cleanTarget;
  if (processedTarget.startsWith("E")) {
      processedTarget = processedTarget.substring(1);
  }

  // 3. 核心邏輯：將剩下的 8 碼拆分為前四與後四
  if (processedTarget.length === 8) {
      var part1 = processedTarget.substring(0, 4); // 前四碼：廠別 (如 F180 或 0070)
      var part2 = processedTarget.substring(4);    // 後四碼：廠區 (如 183B 或 0001)
      
      // 廠別跟廠區都必須同時相符才算通過
      if (cleanOCR.includes(part1) && cleanOCR.includes(part2)) {
          return { pass: true };
      }
  }

  // 4. 螢幕反光 2 與 3 的 OCR 雙向容錯處理 (維持原有的防誤判機制)
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
  var cleanOCR = ocrText.toUpperCase().replace(/[\s-]/g, ""); var cleanTarget = target.toUpperCase().replace(/[\s-]/g, "");
  if (cleanTarget.length === 0) return { pass: false };
  if (cleanOCR.includes(cleanTarget)) return { pass: true };
  if (cleanTarget.match(/^\d/)) { var noPrefix = cleanTarget.substring(1); if (noPrefix.length >= 3 && cleanOCR.includes(noPrefix)) { return { pass: true }; } }
  var variant1 = cleanTarget.replace(/3/g, "5").replace(/8/g, "B"); if (cleanOCR.includes(variant1)) return { pass: true };
  var variant2 = cleanTarget.replace(/5/g, "3").replace(/B/g, "8"); if (cleanOCR.includes(variant2)) return { pass: true };
  var fO = cleanOCR.replace(/[OIZS]/g, function(m){return {'O':'0','I':'1','Z':'2','S':'5'}[m]});
  var fT = cleanTarget.replace(/[OIZS]/g, function(m){return {'O':'0','I':'1','Z':'2','S':'5'}[m]});
  if (fO.includes(fT)) return { pass: true };
  return { pass: false };
}

function saveImageToDrive(base64Data, prefix) {
  if (!BACKUP_FOLDER_ID) return "";
  var blob = Utilities.newBlob(Utilities.base64Decode(base64Data.split(',')[1]), base64Data.split(';')[0].split(':')[1], prefix + "_" + Utilities.formatDate(new Date(), "GMT+8", "HHmmss") + ".jpg");
  var file = DriveApp.getFolderById(BACKUP_FOLDER_ID).createFile(blob);
  file.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
  return file.getUrl();
}
