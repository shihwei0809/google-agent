// ==========================================
// 設定區 (V43 本地 OCR + 雲端驗證存檔版)
// ==========================================
var BACKUP_FOLDER_ID = "16lBdHf67N3QVfBEbnU2O5fgFa_6H1j4v"; // 請填入備份雲端資料夾 ID

// ==========================================
// 1. 路由控制 (當透過 Google Apps Script 連接時，自動回傳網頁)
// ==========================================
function doGet(e) {
  return HtmlService.createTemplateFromFile('Index')
      .evaluate()
      .setTitle('台積三合一單與COA 雙重核對系統')
      .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

// ==========================================
// 2. 本地辨識後的驗證與核對存檔邏輯 (供手機/網頁呼叫)
// ==========================================
function processFormAndVerify_LocalOCR(formObject) {
  try {
    var rawQrBatch = formObject.batchNo ? formObject.batchNo.toString().trim() : ""; 
    var rawPlace   = formObject.deliveryPlace ? formObject.deliveryPlace.toString().trim() : "";
    var rawTank    = formObject.tankNo ? formObject.tankNo.toString().trim() : ""; 
    var photoDataBatch = formObject.photoDataBatch; 
    var photoDataLoc   = formObject.photoDataLoc;   
    var ocrTextBatch   = formObject.ocrTextBatch || ""; // 接收前端已從本機辨識出的文字
    var ocrTextLoc     = formObject.ocrTextLoc || "";   // 接收前端已從本機辨識出的文字

    if (!photoDataBatch || !photoDataLoc) throw new Error("缺少照片資料");

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

    // 核對邏輯
    var targetBatch = rawQrBatch.length >= 11 ? rawQrBatch.substring(1, 11) : rawQrBatch;
    var targetTank  = rawTank; 
    var targetPlace = rawPlace; 

    var check1 = advancedFuzzyCheck(ocrTextBatch, targetBatch);
    var check2 = smartLocationCheck(ocrTextLoc, targetPlace); 
    
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
// 3. 查詢系統資料取得邏輯
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
// 4. 比對與防呆工具函式
// ==========================================
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
