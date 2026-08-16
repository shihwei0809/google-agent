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
<!DOCTYPE html>
<html>
  <head>
    <base target="_top">
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/html5-qrcode" type="text/javascript"></script>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Noto+Sans+TC:wght@400;700&display=swap" rel="stylesheet">
    <style>
      body { font-family: 'Inter', 'Noto Sans TC', sans-serif; padding: 20px; background-color: #f8fafc; color: #1e293b; padding-bottom: 80px; }
      input[type="text"], input[type="date"] { width: 100%; padding: 10px 12px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 0.9rem; transition: all 0.2s; background-color: #fff; }
      input[type="text"]:focus, input[type="date"]:focus { border-color: #3b82f6; outline: none; ring: 3px solid rgba(59, 130, 246, 0.1); }
      input[readonly] { background-color: #f1f5f9; color: #475569; cursor: default; }
      
      .btn { padding: 12px; border-radius: 8px; font-weight: 600; transition: all 0.2s; display: flex; align-items: center; justify-content: center; gap: 6px; width: 100%; font-size: 0.95rem; }
      .btn:active { transform: scale(0.98); }
      .btn-scan { background: linear-gradient(135deg, #2563eb, #1d4ed8); color: white; box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2); }
      .btn-ai { background: linear-gradient(135deg, #8b5cf6, #6d28d9); color: white; box-shadow: 0 4px 6px -1px rgba(139, 92, 246, 0.2); }
      .btn-submit { background: linear-gradient(135deg, #10b981, #059669); color: white; box-shadow: 0 4px 6px -1px rgba(16, 185, 129, 0.2); font-size: 1.05rem; }
      .btn-disabled { background: #94a3b8; cursor: not-allowed; transform: none !important; }
      .btn-action { padding: 8px 16px; border-radius: 8px; font-size: 0.85rem; font-weight: 600; background: white; border: 1px solid #e2e8f0; color: #475569; cursor: pointer; display: inline-flex; align-items: center; gap: 5px; }
      /* 匯出按鈕專用樣式 */
      .btn-export { background: #10b981; color: white; border: none; }
      .btn-export:hover { background: #059669; }
      
      #reader, #camera-container { width: 100%; border-radius: 12px; overflow: hidden; background: #000; margin-bottom: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.2); display: none; }
      #live-video { width: 100%; height: auto; display: block; }
      .camera-controls { position: absolute; bottom: 20px; left: 0; width: 100%; display: flex; justify-content: center; gap: 20px; z-index: 10; }
      .btn-shutter { width: 60px; height: 60px; border-radius: 50%; background: white; border: 4px solid rgba(255,255,255,0.5); cursor: pointer; box-shadow: 0 2px 10px rgba(0,0,0,0.3); }
      
      .photo-box { border: 2px dashed #cbd5e1; padding: 16px; text-align: center; border-radius: 12px; background: #f8fafc; margin-bottom: 16px; cursor: pointer; transition: all 0.2s; }
      .preview-img { width: 100%; border-radius: 8px; margin-top: 10px; display: none; filter: grayscale(100%) contrast(120%); }
      .hidden-section { display: none !important; }
      
      .header-icon { width: 40px; height: 40px; background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); border-radius: 10px; display: flex; align-items: center; justify-content: center; color: white; }
      
      /* 表格 */
      .custom-table { width: 100%; border-collapse: separate; border-spacing: 0; }
      .custom-table thead th { background: #f8fafc; color: #64748b; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; padding: 12px 16px; text-align: left; border-bottom: 1px solid #e2e8f0; }
      .custom-table thead th:last-child { text-align: right; }
      .custom-table tbody td { padding: 14px 16px; border-bottom: 1px solid #f1f5f9; font-size: 0.875rem; vertical-align: middle; }
      .custom-table tbody td:last-child { text-align: right; }
      .badge-success { background: #dcfce7; color: #166534; padding: 4px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 700; }
      .badge-fail { background: #fee2e2; color: #991b1b; padding: 4px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 700; }
      .btn-photo { padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; background: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe; text-decoration: none; display: inline-flex; margin-left: 6px; }
    </style>
  </head>
  <body>

    <div id="view-scan" class="max-w-md mx-auto">
      <div class="bg-white rounded-2xl shadow-xl border border-white/60 overflow-hidden">
        <div class="p-6 border-b border-slate-100 flex justify-between items-center bg-white">
            <div class="flex items-center gap-3">
                <div class="header-icon"><svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-6 h-6"><path stroke-linecap="round" stroke-linejoin="round" d="M3.75 4.875c0-.621.504-1.125 1.125-1.125h4.5c.621 0 1.125.504 1.125 1.125v4.5c0 .621-.504 1.125-1.125 1.125h-4.5A1.125 1.125 0 013.75 9.375v-4.5zM3.75 14.625c0-.621.504-1.125 1.125-1.125h4.5c.621 0 1.125.504 1.125 1.125v4.5c0 .621-.504 1.125-1.125 1.125h-4.5a1.125 1.125 0 01-1.125-1.125v-4.5zM13.5 4.875c0-.621.504-1.125 1.125-1.125h4.5c.621 0 1.125.504 1.125 1.125v4.5c0 .621-.504 1.125-1.125 1.125h-4.5a1.125 1.125 0 01-1.125-1.125v-4.5zM13.5 4.875c0-.621.504-1.125 1.125-1.125h4.5c.621 0 1.125.504 1.125 1.125v4.5c0 .621-.504 1.125-1.125 1.125h-4.5A1.125 1.125 0 0113.5 9.375v-4.5z" /></svg></div>
                <div><h1 class="text-lg font-bold text-slate-800">三合一單核對系統</h1><p class="text-xs text-slate-500 font-medium">COA與T100交叉核對</p></div>
            </div>
            <button onclick="showQuery()" class="btn-action">查詢紀錄</button>
        </div>

        <div class="p-6 pt-4">
            <div class="grid grid-cols-2 gap-3 mb-4">
                <button type="button" onclick="openQrScanner()" class="btn btn-scan"><svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-5 h-5"><path stroke-linecap="round" stroke-linejoin="round" d="M3.75 4.875c0-.621.504-1.125 1.125-1.125h4.5c.621 0 1.125.504 1.125 1.125v4.5c0 .621-.504 1.125-1.125 1.125h-4.5A1.125 1.125 0 013.75 9.375v-4.5zM3.75 14.625c0-.621.504-1.125 1.125-1.125h4.5c.621 0 1.125.504 1.125 1.125v4.5c0 .621-.504 1.125-1.125 1.125h-4.5a1.125 1.125 0 01-1.125-1.125v-4.5zM13.5 4.875c0-.621.504-1.125 1.125-1.125h4.5c.621 0 1.125.504 1.125 1.125v4.5c0 .621-.504 1.125-1.125 1.125h-4.5a1.125 1.125 0 01-1.125-1.125v-4.5zM13.5 4.875c0-.621.504-1.125 1.125-1.125h4.5c.621 0 1.125.504 1.125 1.125v4.5c0 .621-.504 1.125-1.125 1.125h-4.5A1.125 1.125 0 0113.5 9.375v-4.5z" /></svg>掃描 QR</button>
                <button type="button" onclick="openAiCamera()" id="btnAi" class="btn btn-ai"><svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-5 h-5"><path stroke-linecap="round" stroke-linejoin="round" d="M6.827 6.175A2.31 2.31 0 015.186 7.23c-.38.054-.757.112-1.134.175C2.999 7.58 2.25 8.507 2.25 9.574V18a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9.574c0-1.067-.75-1.994-1.802-2.169a47.865 47.865 0 00-1.134-.175 2.31 2.31 0 01-1.64-1.055l-.822-1.316a2.192 2.192 0 00-1.736-1.039 48.774 48.774 0 00-5.232 0 2.192 2.192 0 00-1.736 1.039l-.821 1.316z" /></svg>AI 讀單</button>
            </div>

            <div id="reader"></div>
            <div id="camera-container">
                <video id="live-video" autoplay playsinline></video>
                <div class="camera-controls">
                    <button style="background:rgba(0,0,0,0.5);color:white;padding:8px;border-radius:20px;" onclick="closeAiCamera()">取消</button>
                    <button class="btn-shutter" onclick="captureAiPhoto()"></button>
                    <div style="width:50px;"></div>
                </div>
            </div>
            
            <img id="imgLabel" class="preview-img mb-4">
            <div id="msgLabel" class="text-center text-xs text-slate-400 mt-2 hidden"></div>

            <form id="myForm" onsubmit="handleFormSubmit(event)">
                <div class="bg-slate-50 p-4 rounded-xl border border-slate-200 mb-6">
                    <div class="mb-3">
                        <label class="text-xs font-bold text-slate-400 uppercase mb-1 block">QR 內容 / AI 寫入</label>
                        <input type="text" name="rawQr" id="rawQr" placeholder="請操作上方按鈕" required oninput="parseInputData(this.value)" class="font-mono text-sm text-slate-600">
                    </div>
                    <div class="grid grid-cols-2 gap-3">
                        <div><label class="text-xs font-bold text-slate-500 mb-1 block">料號</label><input type="text" name="materialNo" id="materialNo"></div>
                        <div><label class="text-xs font-bold text-slate-500 mb-1 block">槽號</label><input type="text" name="tankNo" id="tankNo"></div>
                        <div><label class="text-xs font-bold text-red-500 mb-1 block">批號 (目標)</label><input type="text" name="batchNo" id="batchNo" class="font-bold text-red-600 bg-red-50 border-red-100"></div>
                        <div><label class="text-xs font-bold text-blue-500 mb-1 block">送達地點</label><input type="text" name="deliveryPlace" id="deliveryPlace" class="font-bold text-blue-600 bg-blue-50 border-blue-100"></div>
                    </div>
                    <div class="mt-3"><label class="text-xs font-bold text-slate-500 mb-1 block">供應商</label><input type="text" name="supplier" id="supplier"></div>
                </div>

                <div class="photo-box" onclick="document.getElementById('inputBatch').click()">
                    <label class="text-blue-600 font-bold block mb-1">📦 2. 拍攝 COA (批號)</label>
                    <input type="file" id="inputBatch" accept="image/*" capture="environment" class="hidden" onchange="handleImageUpload(event, 'Batch')" required>
                    <div id="statusBatch" class="text-orange-500 text-xs font-bold mt-2 hidden">⚡ 處理中...</div>
                    <img id="previewBatch" class="preview-img">
                    <input type="hidden" name="photoDataBatch" id="photoDataBatch">
                </div>

                <div class="photo-box" onclick="document.getElementById('inputLoc').click()">
                    <label class="text-blue-600 font-bold block mb-1">🏭 3. 拍攝 T100 地磅畫面</label>
                    <input type="file" id="inputLoc" accept="image/*" capture="environment" class="hidden" onchange="handleImageUpload(event, 'Loc')" required>
                    <div id="statusLoc" class="text-orange-500 text-xs font-bold mt-2 hidden">⚡ 處理中...</div>
                    <img id="previewLoc" class="preview-img">
                    <input type="hidden" name="photoDataLoc" id="photoDataLoc">
                </div>

                <button type="submit" id="submitBtn" class="btn btn-submit mt-2">🚀 4. 智能驗證並上傳</button>
            </form>
        </div>
      </div>
    </div>

    <div id="view-query" class="w-full max-w-7xl mx-auto hidden-section">
      <div class="bg-white rounded-2xl shadow-xl border border-white/60 overflow-hidden">
         <div class="p-6 border-b border-slate-100 bg-white">
             <div class="flex flex-col lg:flex-row justify-between lg:items-center gap-4 mb-4">
                 <div class="flex items-center gap-3">
                    <div class="header-icon bg-slate-800"><svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-6 h-6"><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" /></svg></div>
                    <div><h1 class="text-xl font-bold text-slate-800">歷史紀錄</h1><p class="text-xs text-slate-500">共 <span id="total-badge">0</span> 筆資料</p></div>
                 </div>
                 <button onclick="showScan()" class="btn-action">回掃描頁</button>
             </div>
             
             <div class="flex flex-col md:flex-row gap-3 mb-4">
                 <div class="flex items-center gap-2 w-full md:w-auto">
                     <input type="date" id="startDate" class="bg-slate-50 shadow-sm border p-2 rounded">
                     <span class="text-slate-400">~</span>
                     <input type="date" id="endDate" class="bg-slate-50 shadow-sm border p-2 rounded">
                 </div>
                 <div class="flex gap-2 flex-1">
                     <input type="text" id="searchInput" placeholder="搜尋批號 / 單號 / 料號..." class="bg-slate-50 shadow-sm">
                     <button onclick="searchData()" class="btn bg-blue-600 text-white hover:bg-blue-700 px-6 shadow-sm w-auto">搜尋</button>
                     <button onclick="exportExcel()" class="btn btn-export shadow-sm w-auto whitespace-nowrap">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-5 h-5"><path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" /></svg>
                        匯出 Excel
                     </button>
                 </div>
             </div>
         </div>
         
         <div class="overflow-x-auto min-h-[400px]">
             <table class="custom-table">
                 <thead>
                     <tr>
                         <th class="w-32">時間 / 狀態</th>
                         <th class="text-blue-700">批號 (BATCH)</th>
                         <th class="text-slate-600">單號資訊</th>
                         <th>供應商</th>
                         <th>料號</th>
                         <th>槽號</th>
                         <th>地點</th>
                         <th>照片</th>
                     </tr>
                 </thead>
                 <tbody id="tableBody"></tbody>
             </table>
             <div id="loadingOverlay" class="hidden-section p-10 text-center text-slate-400">讀取資料中...</div>
         </div>
         <div id="pagination" class="hidden-section p-4 border-t border-slate-100 flex justify-between items-center bg-slate-50">
             <button id="prevBtn" onclick="changePage(-1)" class="btn-action">« 上一頁</button><span id="pageInfo" class="text-sm font-bold">1/1</span><button id="nextBtn" onclick="changePage(1)" class="btn-action">下一頁 »</button>
         </div>
      </div>
    </div>

    <script>
      function showQuery() { document.getElementById('view-scan').classList.add('hidden-section'); document.getElementById('view-query').classList.remove('hidden-section'); fetchData(); }
      function showScan() { document.getElementById('view-query').classList.add('hidden-section'); document.getElementById('view-scan').classList.remove('hidden-section'); }

      // ★ V36 新增：匯出 Excel 功能
      function exportExcel() {
          const btn = document.querySelector('.btn-export');
          const originalText = btn.innerHTML;
          btn.innerHTML = '處理中...'; btn.disabled = true;

          const search = document.getElementById('searchInput').value;
          const start = document.getElementById('startDate').value;
          const end = document.getElementById('endDate').value;

          google.script.run.withSuccessHandler(function(data) {
              if(!data || data.length === 0) { alert("沒有資料可匯出"); btn.innerHTML = originalText; btn.disabled = false; return; }
              
              // 製作 CSV 內容 (加入 BOM 以支援中文)
              let csvContent = "\uFEFF";
              csvContent += "時間,狀態,批號,來源單號,磅單編號,供應商,料號,槽號,地點,照片連結1,照片連結2\n";
              
              data.forEach(function(row) {
                  let rowStr = [
                      row.time,
                      row.status,
                      row.batch,
                      row.sourceOrder,
                      row.docOrder,
                      row.supplier,
                      row.material,
                      row.tank,
                      row.location,
                      row.photoBatch,
                      row.photoLoc
                  ].map(e => `"${String(e).replace(/"/g, '""')}"`).join(","); // 處理逗號與引號
                  csvContent += rowStr + "\n";
              });

              // 下載檔案
              const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
              const url = URL.createObjectURL(blob);
              const link = document.createElement("a");
              link.setAttribute("href", url);
              link.setAttribute("download", `核對紀錄_${new Date().toISOString().slice(0,10)}.csv`);
              document.body.appendChild(link);
              link.click();
              document.body.removeChild(link);

              btn.innerHTML = originalText; btn.disabled = false;
          }).withFailureHandler(function(err) {
              alert("匯出失敗: " + err);
              btn.innerHTML = originalText; btn.disabled = false;
          }).getExportData(search, start, end); // 呼叫後端新的匯出函式
      }

      // 以下為原有函式 (掃描/拍照/查詢)
      let html5QrcodeScanner;
      let videoStream;

      function openQrScanner() {
        closeAiCamera(); document.getElementById('reader').style.display = 'block'; document.getElementById('imgLabel').style.display = 'none';
        html5QrcodeScanner = new Html5Qrcode("reader");
        html5QrcodeScanner.start({ facingMode: "environment" }, { fps: 10, qrbox: { width: 250, height: 250 } }, (decodedText) => {
           document.getElementById('rawQr').value = decodedText; parseInputData(decodedText); 
           html5QrcodeScanner.stop().then(() => { document.getElementById('reader').style.display = 'none'; });
        }).catch(err => alert("相機啟動失敗，請確認權限"));
      }

      async function openAiCamera() {
        if(html5QrcodeScanner) { try{ await html5QrcodeScanner.stop(); }catch(e){} document.getElementById('reader').style.display = 'none'; }
        document.getElementById('imgLabel').style.display = 'none'; document.getElementById('camera-container').style.display = 'block';
        const video = document.getElementById('live-video');
        try { videoStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment", width: { ideal: 4096 }, height: { ideal: 2160 } } }); video.srcObject = videoStream; } catch (err) { alert("無法啟動相機"); closeAiCamera(); }
      }

      function closeAiCamera() {
        document.getElementById('camera-container').style.display = 'none';
        if (videoStream) { videoStream.getTracks().forEach(track => track.stop()); videoStream = null; }
      }

      function captureAiPhoto() {
        const video = document.getElementById('live-video'); const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth; canvas.height = video.videoHeight;
        const ctx = canvas.getContext('2d'); ctx.filter = "grayscale(100%) contrast(150%)"; ctx.drawImage(video, 0, 0);
        const dataUrl = canvas.toDataURL('image/jpeg', 0.85);
        const img = document.getElementById('imgLabel'); img.src = dataUrl; img.style.display = 'block';
        closeAiCamera(); analyzeCapturedImage(dataUrl);
      }

      function analyzeCapturedImage(base64Data) {
        const btn = document.getElementById('btnAi'); const msg = document.getElementById('msgLabel'); const originalText = btn.innerHTML;
        btn.innerHTML = `AI 讀取中...`; btn.classList.add('opacity-75', 'pointer-events-none'); msg.classList.remove('hidden'); msg.innerText = '正在雲端分析...';
        google.script.run.withSuccessHandler(function(res) {
              btn.innerHTML = originalText; btn.classList.remove('opacity-75', 'pointer-events-none');
              if(res.success) {
                  const d = res.data;
                  if(d.material) document.getElementById('materialNo').value = d.material;
                  if(d.tank) document.getElementById('tankNo').value = d.tank;
                  if(d.batch) document.getElementById('batchNo').value = d.batch;
                  if(d.place) document.getElementById('deliveryPlace').value = d.place;
                  if(d.supplier) document.getElementById('supplier').value = d.supplier;
                  document.getElementById('rawQr').value = "AI_CAMERA_CAPTURE";
                  msg.innerHTML = `<span class="text-green-600 font-bold">✅ 讀取成功！請檢查資料</span>`;
              } else { msg.innerText = "❌ 讀取失敗"; alert("AI 讀取失敗: " + res.message); }
          }).withFailureHandler(function(err){ btn.innerHTML = originalText; alert("系統錯誤: "+err); }).analyzeLabelPhoto(base64Data);
      }

      function parseInputData(text) {
        if (!text || !text.includes("||")) return;
        const parts = text.trim().split("||");
        document.getElementById('materialNo').value = parts[1] || ""; document.getElementById('tankNo').value = parts[2] || "";
        document.getElementById('batchNo').value = parts[3] || ""; document.getElementById('supplier').value = parts[4] || ""; document.getElementById('deliveryPlace').value = parts[5] || "";
      }

      function handleImageUpload(event, type) {
        const file = event.target.files[0]; if (!file) return;
        const statusEl = document.getElementById('status' + type); const previewEl = document.getElementById('preview' + type); const hiddenEl = document.getElementById('photoData' + type);
        statusEl.style.display = 'block'; statusEl.classList.remove('hidden');
        const reader = new FileReader(); reader.readAsDataURL(file);
        reader.onload = function(e) {
            const img = new Image(); img.src = e.target.result;
            img.onload = function() {
                const canvas = document.createElement('canvas'); const ctx = canvas.getContext('2d');
                const MAX = 1600; let w = img.width; let h = img.height; if (w > MAX) { h *= MAX / w; w = MAX; } canvas.width = w; canvas.height = h;
                ctx.filter = "grayscale(100%) contrast(150%) brightness(110%)"; ctx.drawImage(img, 0, 0, w, h);
                const data = canvas.toDataURL('image/jpeg', 0.85); previewEl.src = data; previewEl.style.display = 'block'; hiddenEl.value = data;
                statusEl.innerText = '✅ 優化完成'; statusEl.classList.replace('text-orange-500','text-green-600');
            }
        }
      }

      function handleFormSubmit(event) {
        event.preventDefault();
        const batchNo = document.getElementById('batchNo').value; const photoBatch = document.getElementById('photoDataBatch').value; const photoLoc = document.getElementById('photoDataLoc').value;
        if(!batchNo || !photoBatch || !photoLoc) { alert("⚠️ 資料不完整"); return; }
        const btn = document.getElementById('submitBtn'); const txt = btn.innerText; btn.disabled = true; btn.innerText = "⏳ 驗證中..."; btn.classList.add('btn-disabled');
        google.script.run.withSuccessHandler(function(res) {
            if(res.success) { alert(res.message); document.getElementById("myForm").reset(); document.getElementById('previewBatch').style.display='none'; document.getElementById('previewLoc').style.display='none'; document.getElementById('imgLabel').style.display='none'; document.getElementById('statusBatch').classList.add('hidden'); document.getElementById('statusLoc').classList.add('hidden'); document.getElementById('msgLabel').classList.add('hidden'); } 
            else { alert(res.message + "\n\n❌ 未存檔。"); }
            btn.disabled = false; btn.innerText = txt; btn.classList.remove('btn-disabled');
        }).processFormAndVerify_V10({
             batchNo: batchNo, deliveryPlace: document.getElementById('deliveryPlace').value, supplier: document.getElementById('supplier').value, tankNo: document.getElementById('tankNo').value, materialNo: document.getElementById('materialNo').value, rawQr: document.getElementById('rawQr').value, photoDataBatch: photoBatch, photoDataLoc: photoLoc
        });
      }

      let currentPage = 1;
      function searchData() { currentPage = 1; fetchData(); }
      function changePage(d) { currentPage += d; fetchData(); }
      function fetchData() { document.getElementById('loadingOverlay').classList.remove('hidden-section'); document.getElementById('tableBody').innerHTML = ''; google.script.run.withSuccessHandler(renderTable).getLogData(currentPage, document.getElementById('searchInput').value, document.getElementById('startDate').value, document.getElementById('endDate').value); }
      function renderTable(data) {
         document.getElementById('loadingOverlay').classList.add('hidden-section'); const tbody = document.getElementById('tableBody');
         document.getElementById('total-badge').innerText = data.total;
         if(data.records.length === 0) { tbody.innerHTML = '<tr><td colspan="8" class="p-10 text-center text-slate-400">📭 查無資料</td></tr>'; return; }
         let html = '';
         data.records.forEach(r => {
            const success = r.status.includes('成功');
            const statusBadge = `<span class="${success ? 'badge badge-success' : 'badge badge-fail'}">${success ? '✅' : '❌'}</span>`;
            let photoBtns = '';
            if(r.photoBatch && r.photoBatch.startsWith('http')) photoBtns += `<a href="${r.photoBatch}" target="_blank" class="btn-photo">📦COA批號</a>`;
            if(r.photoLoc && r.photoLoc.startsWith('http')) photoBtns += `<a href="${r.photoLoc}" target="_blank" class="btn-photo">🏭槽號、批號、廠區和廠別</a>`;
            
            let orderHtml = '-';
            if(r.sourceOrder || r.docOrder) {
                orderHtml = '<div class="flex flex-col gap-1">';
                if(r.sourceOrder) orderHtml += `<span class="text-xs bg-slate-100 p-1 rounded text-slate-600 font-mono" title="來源單號">來源單號: ${r.sourceOrder}</span>`;
                if(r.docOrder)    orderHtml += `<span class="text-xs bg-blue-50 p-1 rounded text-blue-600 font-mono" title="磅單編號">磅單編號: ${r.docOrder}</span>`;
                orderHtml += '</div>';
            }

            html += `<tr><td><div class="text-xs text-slate-400 mb-1 font-mono">${r.time}</div>${statusBadge}</td><td class="font-bold text-blue-700 font-mono text-sm">${r.batch}</td><td>${orderHtml}</td><td class="text-slate-500 text-xs">${r.supplier||'-'}</td><td class="text-slate-600 font-mono text-xs">${r.material}</td><td class="text-slate-600 font-mono text-xs">${r.tank}</td><td class="text-slate-600 text-xs">${r.location}</td><td>${photoBtns||'-'}</td></tr>`;
         });
         tbody.innerHTML = html;
         document.getElementById('pagination').classList.remove('hidden-section'); document.getElementById('pageInfo').innerText = currentPage + " / " + data.totalPages;
         document.getElementById('prevBtn').disabled = currentPage <= 1; document.getElementById('nextBtn').disabled = currentPage >= data.totalPages;
      }
    </script>
  </body>
</html>
