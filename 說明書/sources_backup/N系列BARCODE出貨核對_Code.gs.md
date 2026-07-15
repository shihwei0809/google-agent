# Source Code Backup - N系列BARCODE出貨核對 - Code.gs

> [!NOTE]
> *   **原始本機路徑**: [Code.gs](file:///D:/GOOGLE%20ANGET/N系列BARCODE出貨核對/Code.gs)
> *   **自動備份時間**: `2026-07-15 13:39:13`
> *   **語言類型**: `javascript`

``` javascript
// ==========================================
// 1. 網頁入口 (路由控制)
// ==========================================
// ==========================================
// 1. 網頁開啟與查詢介面 (GET 請求)
// ==========================================
function doGet(e) {
  var page = e.parameter.page;
  if (page === 'query') {
    return HtmlService.createTemplateFromFile('Query').evaluate()
        .setTitle('出貨核對-歷史查詢')
        .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL)
        .addMetaTag('viewport', 'width=device-width, initial-scale=1');
  } else {
    return HtmlService.createTemplateFromFile('Index').evaluate()
        .setTitle('出貨核對系統 (v34.6)')
        .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL)
        .addMetaTag('viewport', 'width=device-width, initial-scale=1');
  }
}

// ==========================================
// 2. 接收手機 App 背景同步 (POST 請求)
// ==========================================
function doPost(e) {
  try {
    // 1. 取得 POST 請求的 Body 內容
    var rawData = e.postData.contents;
    if (!rawData) {
      return ContentService.createTextOutput(JSON.stringify({ 
        status: "error", 
        message: "❌ 未接收到任何資料" 
      })).setMimeType(ContentService.MimeType.JSON);
    }
    
    // 2. 解析 JSON
    var json = JSON.parse(rawData);
    var recordData = JSON.parse(json.barcode);
    
    // 3. 呼叫現有的核心存檔法官邏輯 processAndSave(data)
    var result = processAndSave(recordData);
    
    // 4. 回傳執行結果給手機 App
    return ContentService.createTextOutput(JSON.stringify(result))
      .setMimeType(ContentService.MimeType.JSON);
      
  } catch (err) {
    try {
      var errLoc = (typeof recordData !== 'undefined' && recordData && recordData.location) ? recordData.location : "API 串接";
      var errMode = (typeof recordData !== 'undefined' && recordData && recordData.mode) ? recordData.mode : "API 串接";
      var errFields = (typeof recordData !== 'undefined' && recordData && recordData.fields) ? recordData.fields : [];
      sendTeamsErrorNotification("❌ API 雲端執行錯誤: " + err.toString(), errLoc, errMode, errFields);
    } catch (errTeams) {
      Logger.log("API 發送 Teams 通知錯誤: " + errTeams.toString());
    }
    return ContentService.createTextOutput(JSON.stringify({ 
      status: "error", 
      message: "❌ 雲端執行錯誤: " + err.toString() 
    })).setMimeType(ContentService.MimeType.JSON);
  }
}


// ==========================================
// 2. 輔助函式庫
// ==========================================
function toHalfWidth(str) {
  if (!str) return "";
  return str.toString().replace(/[\uff01-\uff5e]/g, function(ch) {
    return String.fromCharCode(ch.charCodeAt(0) - 0xfee0);
  }).replace(/\u3000/g, ' ');
}

function normalizeBatch(str) {
  if (!str) return "";
  var half = toHalfWidth(str); 
  return half.replace(/[^a-zA-Z0-9]/g, ''); 
}

function extractRealBatch(fullString) {
  if (!fullString) return "";
  var s = fullString.toString().trim();
  if (s.indexOf('@') !== -1 && s.indexOf('+') !== -1) {
    var parts = s.split('@');
    if (parts.length > 1) return parts[1]; 
  }
  return s;
}

function extractBatchForWarehouse(fullString) {
  var s = extractRealBatch(fullString);
  if (s.indexOf('+') !== -1) s = s.split('+')[0];
  if (s.indexOf(' ') !== -1) s = s.split(/\s+/)[0];
  return s;
}

function cleanMatMaster(str) {
  if (!str) return "";
  var s = str.toString().trim().toUpperCase(); 
  if (s.indexOf(' ') > -1) s = s.split(' ')[0];
  s = s.replace(/^\d+L/, 'L');
  return s;
}

function extractRealMat(fullString) {
  if (!fullString) return "";
  var s = fullString.toString().trim();
  if (s.indexOf('@') !== -1) {
    var parts = s.split('@');
    var part1 = parts[0];
    if (part1.length > 14) return part1.substring(14); 
    return part1;
  }
  return cleanMatMaster(s);
}

function isSameDay(d1, d2) {
  return d1.getFullYear() === d2.getFullYear() &&
         d1.getMonth() === d2.getMonth() &&
         d1.getDate() === d2.getDate();
}

function getBatchBase(str) {
  var s = String(str).trim();
  if (s.indexOf("+") !== -1) {
    return s.split("+")[0];
  } else if (s.indexOf(" ") !== -1) {
    return s.split(" ")[0];
  }
  return s;
}

function check7SeriesFormat(code) {
  var s = String(code).trim();
  if (s.startsWith("7")) {
    if (s.length !== 29) return "❌ 格式錯誤！\n👉 [7開頭] 長度需 29 碼 (目前 " + s.length + ")";
    if (s.toUpperCase().indexOf("-T0") === -1) return "❌ 格式錯誤！\n👉 [7開頭] 需包含 '-T0'";
  }
  if (s.toUpperCase().indexOf("-T0") !== -1 && !s.startsWith("7")) {
    return "❌ 格式錯誤！\n👉 含有 '-T0' 必須以 '7' 開頭";
  }
  return "OK";
}

function check1SeriesFormat(code) {
  var s = String(code).trim();
  if (s.startsWith("1")) {
    if (s.length !== 20) return "❌ 格式錯誤！\n👉 [1開頭] 長度需 20 碼 (目前 " + s.length + ")";
    if (!s.endsWith("TS")) return "❌ 格式錯誤！\n👉 [1開頭] 必須以 'TS' 結尾";
  }
  return "OK";
}

// 【共用驗證函式：專門用來執行 1/7 開頭的長度檢查】
function validate17Series(val, label, errors) {
  if (!val || String(val).trim() === "") return;
  var c1 = check1SeriesFormat(val);
  if (c1 !== "OK") errors.push('❌ [' + label + '] ' + c1);
  var c7 = check7SeriesFormat(val);
  if (c7 !== "OK") errors.push('❌ [' + label + '] ' + c7);
}

function verifyPairStrict(scanVal, masterVal) {
  var scan = String(scanVal).trim();
  var master = String(masterVal).trim();
  if (scan === "" || master === "") return { pass: false, msg: "資料空白" };

  if (scan.startsWith("1") && scan.length === 20 && scan.endsWith("TS")) {
      if (scan === master) return { pass: true, msg: "OK" };
      if (scan.indexOf(master) !== -1 && master.length > 5) return { pass: true, msg: "OK" };
      return { pass: false, msg: "1字頭比對失敗\n現場: " + scan + "\n單據: " + master };
  }

  var isQr = (scan.indexOf("@") !== -1);
  if (isQr) {
    var processedScan = "";
    var parts = scan.split('@');
    if (parts.length > 1) processedScan = parts[1];
    else processedScan = scan;
    processedScan = processedScan.replace(/\+/g, '').replace(/\s+/g, '');
    
    var processedMaster = master;
    if (processedMaster.length > 0) processedMaster = processedMaster.substring(1);
    processedMaster = processedMaster.replace(/\s+/g, '');

    if (processedScan === processedMaster) return { pass: true, msg: "OK" };
    else return { pass: false, msg: "QR比對失敗\n現場(去+): " + processedScan + "\n單據(去首碼): " + processedMaster };
  }

  if (scan === master) return { pass: true, msg: "OK" };
  if (scan.replace(/\s+/g, '') === master.replace(/\s+/g, '')) return { pass: true, msg: "OK" };
  return { pass: false, msg: "數值不一致\n現場: " + scan + "\n單據: " + master };
}

function getBiMonthlySuffix() {
  var now = new Date();
  var year = now.getFullYear();
  var month = now.getMonth(); 
  var startMonthIdx = Math.floor(month / 2) * 2;
  var m1 = startMonthIdx + 1;
  var m2 = startMonthIdx + 2;
  var pad = function(n) { return (n < 10 ? '0' : '') + n; };
  return "_" + year + "-" + pad(m1) + "~" + pad(m2);
}

// ==========================================
// 3. 主程式 Logic
// ==========================================
function processAndSave(data) {
  var f = data.fields; 
  var mode = data.mode; 
  var location = data.location; 
  var allErrors = []; 
  var headers = [];
  var writeData = []; 

  var tankMap = [
    { batch: 0, mat: 1, name: '第一桶', masterBatchIdx: 9 },
    { batch: 2, mat: 3, name: '第二桶', masterBatchIdx: 10 },
    { batch: 4, mat: 5, name: '第三桶', masterBatchIdx: 11 },
    { batch: 6, mat: 7, name: '第四桶', masterBatchIdx: 12 }
  ];

  if (mode === 'ship_az') {
    headers = ["日期時間", "作業場所", "桶1批號", "桶1料號", "桶2批號", "桶2料號", "桶3批號", "桶3料號", "桶4批號", "桶4料號", "判定結果"];
    var activeTankCount = 0;
    var firstTankMaterial = ""; 
    var rawBatches = [];
    var seenAz = {}; 

    for (var i = 0; i < tankMap.length; i++) {
      var item = tankMap[i];
      var rawBatch = f[item.batch].toString().trim();
      var rawMat = f[item.mat].toString().trim(); 
      
      if (rawBatch !== "" || rawMat !== "") {
        activeTankCount++;
        rawBatches.push(rawBatch);

        // 確保桶批號格式正確
        validate17Series(rawBatch, item.name + ' 批號', allErrors);
        
        // ==========================================
        // 【未來擴充區：AZ 模式桶槽料號 檢查】
        // 檢查邏輯：針對「AZ模式下掃描的料號」
        //          若值為「1開頭」，強制要求 20 碼且結尾為 TS。
        //          若值為「7開頭」，強制要求 29 碼且包含 -T0。
        // 啟用方法：刪除下方這行最前面的「//」符號。
        // ==========================================
        // validate17Series(rawMat, item.name + ' 料號', allErrors);

        var norm = normalizeBatch(rawBatch);
        if (norm !== "") {
            if (seenAz[norm]) allErrors.push('❌ [' + item.name + '] 重複掃描！(與 ' + seenAz[norm] + ' 相同)');
            else seenAz[norm] = item.name;
        }

        var cleanMat = cleanMatMaster(rawMat); 
        if (firstTankMaterial === "") firstTankMaterial = cleanMat;
        if (cleanMat !== firstTankMaterial) allErrors.push('❌ [' + item.name + '] 料號異常！與第一桶不同。');
        
        if (rawBatch.indexOf('@') !== -1) {
           var qrMat = extractRealMat(rawBatch);
           if (qrMat !== "" && qrMat !== cleanMat) allErrors.push('❌ [' + item.name + '] 貼紙錯誤！QR料號與掃描料號不符');
        }
      }
    }

    if (activeTankCount === 0) return { status: 'error', message: '⚠️ 未偵測到任何資料' };
    
    if (rawBatches.length > 1) {
       var base1 = getBatchBase(rawBatches[0]);
       var len1 = rawBatches[0].length; 

       for (var k=1; k<rawBatches.length; k++) {
          if (getBatchBase(rawBatches[k]) !== base1) {
             allErrors.push('❌ AZ批號不一致！第' + (k+1) + '桶與第1桶批號主體不同。');
          }
          var lenK = rawBatches[k].length;
          if (Math.abs(len1 - lenK) > 10) {
             allErrors.push('❌ AZ長度異常！\n👉 第1桶長度: ' + len1 + '\n👉 第' + (k+1) + '桶長度: ' + lenK + '\n(可能發生重複掃描或殘留字元)');
          }
       }
    }
    writeData = f.slice(0, 8); 

  } 
  else {
    headers = ["日期時間", "作業場所", "桶1批號", "桶1料號", "桶2批號", "桶2料號", "桶3批號", "桶3料號", "桶4批號", "桶4料號", "四合一料號", "4in1批1", "4in1批2", "4in1批3", "4in1批4", "繳庫料號", "繳庫批1", "繳庫批2", "繳庫批3", "判定結果"];

    var rawMasterMat = f[8].toString().trim();
    var masterMaterial = cleanMatMaster(rawMasterMat); 
    if (!masterMaterial) return { status: 'error', message: '❌ [四合一料號] 為必填項目！' };
    
    // 【重點】四合一料號強制檢查長度
    validate17Series(rawMasterMat, '四合一料號', allErrors);

    var activeTankCount = 0; 
    var activeBatchesShort = []; 
    var collectedBatchBases = []; 
    var seenDrumbatches = {}; 

    for (var i = 0; i < tankMap.length; i++) {
      var item = tankMap[i];
      var tankRawBatch = f[item.batch].toString().trim();
      var tankInputMat = f[item.mat].toString().trim();
      var masterBatchVal = f[item.masterBatchIdx].toString().trim();

      if (tankRawBatch !== "" || tankInputMat !== "") {
        activeTankCount++;

        // 確保桶批號格式正確
        validate17Series(tankRawBatch, item.name + ' 批號', allErrors);
        
        // ==========================================
        // 【未來擴充區：現場桶槽料號 檢查】
        // 檢查邏輯：針對「現場單獨桶槽掃描的料號」
        //          若值為「1開頭」，強制要求 20 碼且結尾為 TS。
        //          若值為「7開頭」，強制要求 29 碼且包含 -T0。
        // 啟用方法：刪除下方這行最前面的「//」符號。
        // ==========================================
        // validate17Series(tankInputMat, item.name + ' 料號', allErrors);

        // ==========================================
        // 【未來擴充區：四合一對應批號 檢查】
        // 檢查邏輯：針對「四合一單據上對應各桶的批號」
        //          若值為「1開頭」，強制要求 20 碼且結尾為 TS。
        //          若值為「7開頭」，強制要求 29 碼且包含 -T0。
        // 啟用方法：刪除下方這行最前面的「//」符號。
        // ==========================================
        // validate17Series(masterBatchVal, '四合一單據 (對應' + item.name + ')', allErrors);

        var normBatch = normalizeBatch(tankRawBatch);
        if (normBatch !== "") {
            if (seenDrumbatches[normBatch]) {
                allErrors.push('❌ [' + item.name + '] 重複掃描！(與' + seenDrumbatches[normBatch] + '相同)');
            } else {
                seenDrumbatches[normBatch] = item.name;
            }
        }

        var tankCleanMat = cleanMatMaster(tankInputMat);
        if (tankCleanMat !== masterMaterial) allErrors.push('❌ [' + item.name + '] 料號異常！\n👉 現場: ' + tankCleanMat + '\n👉 單據: ' + masterMaterial);

        if (tankRawBatch.indexOf('@') !== -1) {
           var qrMat = extractRealMat(tankRawBatch);
           if (qrMat !== "" && qrMat !== tankCleanMat) allErrors.push('❌ [' + item.name + '] 貼紙錯誤！\nQR內碼: ' + qrMat + '\n與掃描不符。');
        }

        if (masterBatchVal === "") {
           allErrors.push('❌ [' + item.name + '] 對應的「四合一單據批號」未輸入！');
        } else {
           var verifyResult = verifyPairStrict(tankRawBatch, masterBatchVal);
           if (!verifyResult.pass) {
              var detailedMsg = '❌ [' + item.name + '] 與四合一單據不符！\n👉 現場: ' + tankRawBatch + '\n👉 單據: ' + masterBatchVal;
              allErrors.push(detailedMsg);
           }
        }
        collectedBatchBases.push({ name: item.name, base: getBatchBase(tankRawBatch), raw: tankRawBatch });
        activeBatchesShort.push(extractBatchForWarehouse(tankRawBatch));
      }
    }

    if (activeTankCount === 0) return { status: 'error', message: '⚠️ 未偵測到任何現場桶槽資料！' };

    if (mode === 'ship_full' && collectedBatchBases.length > 1) {
       var standardBase = collectedBatchBases[0].base;
       for (var k = 1; k < collectedBatchBases.length; k++) {
          if (collectedBatchBases[k].base !== standardBase) allErrors.push('❌ 整板批號異常！不同批號不可混在同板');
       }
    }

    var activeMasterCount = 0;
    for (var m = 9; m <= 12; m++) if (f[m].toString().trim() !== "") activeMasterCount++;
    if (activeTankCount !== activeMasterCount) allErrors.push('❌ 數量異常！現場 ' + activeTankCount + ' 桶 vs 四合一 ' + activeMasterCount + ' 筆');

    var rawWhMat = f[13].toString().trim();
    var cleanWhMat = cleanMatMaster(rawWhMat); 
    
    // ==========================================
    // 【未來擴充區：繳庫單料號 檢查】
    // 檢查邏輯：針對「繳庫單掃描的料號」
    //          若值為「1開頭」，強制要求 20 碼且結尾為 TS。
    //          若值為「7開頭」，強制要求 29 碼且包含 -T0。
    // 啟用方法：刪除下方這行最前面的「//」符號。
    // ==========================================
    // validate17Series(rawWhMat, '繳庫單料號', allErrors);
    
    if (cleanWhMat !== masterMaterial) allErrors.push('❌ [繳庫單] 料號異常！');
    
    var whBatch1 = f[14].trim(); 
    var whBatch2 = f[15].trim();
    var whBatch3 = f[16].trim();

    // ==========================================
    // 【未來擴充區：繳庫單批號 檢查】
    // 檢查邏輯：針對「繳庫單掃描的各項批號」
    //          若值為「1開頭」，強制要求 20 碼且結尾為 TS。
    //          若值為「7開頭」，強制要求 29 碼且包含 -T0。
    // 啟用方法：刪除下方對應行數最前面的「//」符號。
    // ==========================================
    // validate17Series(whBatch1, '繳庫批號1', allErrors);
    // validate17Series(whBatch2, '繳庫批號2', allErrors);
    // validate17Series(whBatch3, '繳庫批號3', allErrors);

    if (whBatch1 === "" && whBatch2 === "" && whBatch3 === "") {
       allErrors.push('❌ [繳庫單] 未掃描任何批號！');
    } else {
      var tempBatches = activeBatchesShort.slice();
      var checkAndRemove = function(val) {
        if (val === "") return true;
        var whNorm = normalizeBatch(extractBatchForWarehouse(val)); 
        for (var i = 0; i < tempBatches.length; i++) {
           var fieldNorm = normalizeBatch(tempBatches[i]); 
           if (fieldNorm === whNorm || fieldNorm === "2"+whNorm || whNorm === "2"+fieldNorm) {
              tempBatches.splice(i, 1); return true; 
           }
        }
        return false;
      };
      
      if (!checkAndRemove(whBatch1)) allErrors.push('❌ [繳庫單批號1] 異常！現場沒掃到。');
      if (!checkAndRemove(whBatch2)) allErrors.push('❌ [繳庫單批號2] 異常！現場沒掃到。');
      if (!checkAndRemove(whBatch3)) allErrors.push('❌ [繳庫單批號3] 異常！現場沒掃到。');

      var whInputs = [];
      if (whBatch1 !== "") whInputs.push(normalizeBatch(extractBatchForWarehouse(whBatch1)));
      if (whBatch2 !== "") whInputs.push(normalizeBatch(extractBatchForWarehouse(whBatch2)));
      if (whBatch3 !== "") whInputs.push(normalizeBatch(extractBatchForWarehouse(whBatch3)));

      var uniqueScannedBatches = [];
      for (var b=0; b<activeBatchesShort.length; b++) {
         var bNorm = normalizeBatch(activeBatchesShort[b]);
         if (uniqueScannedBatches.indexOf(bNorm) === -1) uniqueScannedBatches.push(bNorm);
      }

      for (var u=0; u<uniqueScannedBatches.length; u++) {
         var needed = uniqueScannedBatches[u];
         var foundInWh = false;
         for (var w=0; w<whInputs.length; w++) {
            var input = whInputs[w];
            if (input === needed || input === "2"+needed || needed === "2"+input) {
               foundInWh = true; break;
            }
         }
         if (!foundInWh) allErrors.push('❌ 繳庫單漏打！現場有但繳庫單沒填。');
      }
    }
    writeData = f;
  }

  if (allErrors.length > 0) {
    var errorMsg = allErrors.join('\n\n');
    try {
      sendTeamsErrorNotification(errorMsg, location, mode, f);
    } catch (errTeams) {
      Logger.log("發送 Teams 通知錯誤: " + errTeams.toString());
    }
    return { status: 'error', message: errorMsg };
  }

  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var baseSheetName = "";
    if (mode === 'ship_full') baseSheetName = "整板出貨紀錄";
    else if (mode === 'ship_mixed') baseSheetName = "混板出貨紀錄";
    else if (mode === 'ship_az') baseSheetName = "AZ出貨紀錄";
    else baseSheetName = "散桶出貨紀錄";

    var targetSheetName = baseSheetName + getBiMonthlySuffix();
    var sheet = ss.getSheetByName(targetSheetName);
    
    if (!sheet) {
      sheet = ss.insertSheet(targetSheetName);
      sheet.appendRow(headers);
      sheet.setFrozenRows(1);
    }

    var now = new Date();
    sheet.appendRow([now, location].concat(writeData, ["批號一致 合格"]));
    
    var lastRow = sheet.getLastRow();
    var dailyCount = 0;
    if (lastRow > 1) {
      var dates = sheet.getRange(2, 1, lastRow - 1, 1).getValues();
      for (var i = 0; i < dates.length; i++) {
        if (dates[i][0] instanceof Date && isSameDay(dates[i][0], now)) dailyCount++;
      }
    }
    if (dailyCount === 0) dailyCount = 1;

    return { status: 'success', message: '✅ 紀錄成功！<br>已寫入: [' + targetSheetName + ']<br>(本日第 ' + dailyCount + ' 筆)', count: dailyCount };

  } catch (e) {
    var writeErrorMsg = '寫入錯誤: ' + e.toString();
    try {
      sendTeamsErrorNotification(writeErrorMsg, location, mode, f);
    } catch (errTeams) {
      Logger.log("發送 Teams 通知錯誤: " + errTeams.toString());
    }
    return { status: 'error', message: writeErrorMsg };
  }
}

// ==========================================
// 4. 查詢功能 (支援排程開關參數)
// ==========================================
function searchRecords(dateStart, dateEnd, keyword, useScheduleCheck) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheets = ss.getSheets();
  var allData = [];
  
  var dStart = new Date(dateStart); dStart.setHours(0,0,0,0);
  var dEnd = new Date(dateEnd); dEnd.setHours(23,59,59,999);
  var hasKeyword = (keyword && keyword.toString().trim() !== "");
  var keyUpper = hasKeyword ? keyword.toString().toUpperCase().trim() : "";

  var scheduleBatches = [];
  if (useScheduleCheck === true) {
    var scheduleSheet = ss.getSheetByName("出貨排程");
    if (scheduleSheet && scheduleSheet.getLastRow() > 0) {
      var sData = scheduleSheet.getDataRange().getDisplayValues();
      for (var sr = 0; sr < sData.length; sr++) {
        for (var sc = 0; sc < sData[sr].length; sc++) {
          var val = normalizeBatch(sData[sr][sc]);
          if (val !== "") scheduleBatches.push(val);
        }
      }
    }
  }

  for (var i = 0; i < sheets.length; i++) {
    var sheet = sheets[i];
    var sName = sheet.getName();
    
    if (sName.indexOf("出貨紀錄") !== -1) {
      var isAZ = (sName.indexOf("AZ") !== -1);
      var modeLabel = "散桶";
      if (sName.indexOf("整板") !== -1) modeLabel = "整板";
      else if (sName.indexOf("混板") !== -1) modeLabel = "混板";
      else if (isAZ) modeLabel = "AZ";

      var lastRow = sheet.getLastRow();
      if (lastRow < 2) continue;

      var rangeData = sheet.getRange(2, 1, lastRow - 1, 21).getValues();

      for (var r = rangeData.length - 1; r >= 0; r--) {
        var row = rangeData[r];
        var rowDate = new Date(row[0]);
        if (rowDate < dStart || rowDate > dEnd) continue;

        var record = {};
        record.date = Utilities.formatDate(rowDate, Session.getScriptTimeZone(), "yyyy-MM-dd");
        record.time = Utilities.formatDate(rowDate, Session.getScriptTimeZone(), "HH:mm");
        record.location = row[1] || "-";
        record.mode = modeLabel;
        record.tanks = [
            { batch: row[2], mat: row[3] },
            { batch: row[4], mat: row[5] },
            { batch: row[6], mat: row[7] },
            { batch: row[8], mat: row[9] }
        ];

        var mainBatch = "";

        if (isAZ) {
            record.master = { mat: "", batches: [] }; 
            record.wh = { mat: "", batches: [] };
            record.result = row[10] || "未知"; 
            mainBatch = extractBatchForWarehouse(row[2] || ""); 
        } else {
            record.master = { mat: row[10], batches: [row[11], row[12], row[13], row[14]] };
            record.wh = { mat: row[15], batches: [row[16], row[17], row[18]] };
            record.result = row[19] || "未知";
            var whB = row[16] ? row[16].toString().trim() : "";
            mainBatch = extractBatchForWarehouse(whB !== "" ? whB : (row[2] || "")); 
        }

        var inSch = null;
        if (useScheduleCheck === true && mainBatch !== "") {
            inSch = false; 
            var target = normalizeBatch(mainBatch);
            if (target.startsWith("2") && target.length > 8) target = target.substring(1);
            for (var sb = 0; sb < scheduleBatches.length; sb++) {
                if (scheduleBatches[sb] === target || scheduleBatches[sb].indexOf(target) !== -1) {
                    inSch = true; break;
                }
            }
        }
        record.inSchedule = inSch; 

        if (hasKeyword) {
          var rowString = JSON.stringify(record).toUpperCase();
          if (rowString.indexOf(keyUpper) === -1) continue;
        }
        allData.push(record);
      }
    }
  }
  return allData;
}

// ==========================================
// 5. 系統功能
// ==========================================
function getScriptUrl() {
  return ScriptApp.getService().getUrl();
}

// ==========================================
// 6. 排程更新與讀取功能
// ==========================================
function updateScheduleData(tsvData) {
  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = ss.getSheetByName("出貨排程");
    
    if (!sheet) {
      sheet = ss.insertSheet("出貨排程");
    }

    var rows = tsvData.split('\n');
    var dataToWrite = [];
    var maxCols = 0;

    for (var i = 0; i < rows.length; i++) {
      var cols = rows[i].split('\t');
      for(var j=0; j<cols.length; j++) {
         cols[j] = cols[j].replace(/\r/g, '').trim();
      }
      
      if (cols.join('').trim() !== '') {
         dataToWrite.push(cols);
         if (cols.length > maxCols) maxCols = cols.length;
      }
    }

    if (dataToWrite.length === 0) {
      return { success: false, msg: "資料空白，請確認是否有複製到內容！" };
    }

    for (var k = 0; k < dataToWrite.length; k++) {
      while (dataToWrite[k].length < maxCols) {
        dataToWrite[k].push("");
      }
    }

    sheet.clearContents();
    sheet.getRange(1, 1, dataToWrite.length, maxCols).setValues(dataToWrite);

    return { success: true, msg: "✅ 排程更新成功！\n共寫入 " + dataToWrite.length + " 筆最新資料。" };
    
  } catch (e) {
    return { success: false, msg: "更新失敗發生錯誤: " + e.toString() };
  }
}

function getScheduleRawText() {
  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = ss.getSheetByName("出貨排程");
    if (!sheet || sheet.getLastRow() === 0) return "";
    
    var data = sheet.getDataRange().getDisplayValues();
    var text = "";
    for (var i = 0; i < data.length; i++) {
      text += data[i].join('\t') + "\n";
    }
    return text.trim();
  } catch(e) {
    return "";
  }
}

function clearScheduleData() {
  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = ss.getSheetByName("出貨排程");
    if (sheet) {
      sheet.clearContents();
    }
    return { success: true, msg: "🗑️ 排程資料已完全清空！" };
  } catch(e) {
     return { success: false, msg: "清空失敗: " + e.toString() };
  }
}

// ==========================================
// 7. Teams Webhook 異常通知功能
// ==========================================
function sendTeamsErrorNotification(errorsText, location, mode, fields) {
  var url = PropertiesService.getScriptProperties().getProperty("TEAMS_WEBHOOK_URL");
  if (!url) {
    try {
      var ss = SpreadsheetApp.getActiveSpreadsheet();
      var sheet = ss.getSheetByName("系統設定");
      if (sheet) {
        var data = sheet.getDataRange().getValues();
        for (var i = 0; i < data.length; i++) {
          var key = String(data[i][0]).trim();
          var val = String(data[i][1]).trim();
          if (key.toLowerCase().indexOf("teams") > -1 || key.toLowerCase().indexOf("webhook") > -1) {
            url = val;
            break;
          }
        }
      }
    } catch(e) {
      Logger.log("讀取系統設定失敗: " + e.toString());
    }
  }

  if (!url || url.indexOf("http") !== 0) {
    Logger.log("未設定 Teams Webhook URL 或格式不正確。");
    return;
  }

  var notifySubject = "⚠️ 出貨核對異常";
  var header = "";
  if (errorsText.indexOf("寫入錯誤") > -1 || errorsText.indexOf("雲端執行錯誤") > -1) {
    header = "系統執行錯誤 (場所: " + (location || "未指定") + ", 模式: " + (mode || "未知") + ")";
  } else {
    header = "巡檢核對失敗 (場所: " + (location || "未指定") + ", 模式: " + (mode || "未知") + ")";
  }
  
  var textMessage = header + "\n\n" + errorsText;

  try {
    var payload = {
      "@type": "MessageCard",
      "@context": "http://schema.org/extensions",
      "themeColor": "D9534F",
      "summary": notifySubject,
      "title": notifySubject,
      "text": textMessage
    };
    var options = {
      "method": "post",
      "contentType": "application/json",
      "payload": JSON.stringify(payload),
      "muteHttpExceptions": true
    };
    var response = UrlFetchApp.fetch(url, options);
    Logger.log("Teams Webhook 發送成功！狀態碼: " + response.getResponseCode());
  } catch(e) {
    Logger.log("Teams Webhook 發送異常: " + e.toString());
  }
}

// 測試 Teams Webhook 功能
function testTeamsNotification() {
  var testErrors = "❌ [桶2] 與四合一單據不符！\n現場: 720260707-T001\n單據: 720260707-T002";
  var testFields = [
    "720260707-T001", "L12345", // 桶1
    "720260707-T001", "L12345", // 桶2
    "", "", // 桶3
    "", "", // 桶4
    "L12345", "720260707-T001", "720260707-T002", "", "", // 四合一料號/批1~4
    "L12345", "720260707-T001", "", "" // 繳庫料號/批1~3
  ];
  sendTeamsErrorNotification(testErrors, "崙尾一廠", "ship_full", testFields);
}
```
