# N系列BARCODE出貨核對

**Date**: May 10, 2026 at 07:48 PM
**Turns**: 11
**Source**: [Gemini Chat](https://gemini.google.com/u/1/app/aa11848dddedaf08)

---

## Turn 1

### 👤 User

將出貨排程與查詢介面 做交叉核對即可，不需要在掃描介面做核對

### 🤖 Assistant

這個思路非常正確！將防呆與查核分開，**「掃描介面只負責紀錄與基礎驗證，不要阻擋現場作業；查詢介面再來做排程的交叉比對」**，這樣不僅能維持現場人員的工作流暢度，管理人員也能在後台一目了然地看到有沒有人「掃了不在排程上的貨」。
我已經幫您把系統邏輯重新改寫為 **v34.0 (查詢端排程核對版)**：

1. **掃描介面 (Index.html)**：移除「更新排程」按鈕與核對開關，恢復純粹、無阻擋的掃描儲存。
2. **後端 (Code.gs)**：掃描時不再阻擋；但在讀取查詢資料時，自動去比對「出貨排程」分頁，並給資料標上是否吻合的標籤。
3. **查詢介面 (Query.html)**：
  - 將「📅 更新排程」的功能**移動到這裡**，由管理人員來維護。
  - 表格的「判定結果」欄位下方，會自動顯示 **「📅 排程相符」** 或是 **「⚠️ 不在排程」** 的標籤。
請將專案中的三個檔案 **完全清空後，再複製貼上** 以下程式碼。

---

### 檔案一：`Code.gs` (後端主程式)

```javascript
// ==========================================
// 1. 網頁入口 (路由控制)
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
        .setTitle('出貨核對系統 (v34.0)')
        .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL)
        .addMetaTag('viewport', 'width=device-width, initial-scale=1');
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
    if (s.toUpperCase().indexOf("T-0") === -1) return "❌ 格式錯誤！\n👉 [7開頭] 需包含 'T-0'";
  }
  if (s.toUpperCase().indexOf("T-0") !== -1 && !s.startsWith("7")) {
    return "❌ 格式錯誤！\n👉 含有 'T-0' 必須以 '7' 開頭";
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
// 3. 主程式 Logic (掃描儲存：移除排程阻擋)
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

        var fCheck1 = check1SeriesFormat(rawBatch);
        if (fCheck1 !== "OK") allErrors.push('❌ [' + item.name + '] ' + fCheck1);
        var fCheck7 = check7SeriesFormat(rawBatch);
        if (fCheck7 !== "OK") allErrors.push('❌ [' + item.name + '] ' + fCheck7);

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

    var masterMaterial = cleanMatMaster(f[8]); 
    if (!masterMaterial) return { status: 'error', message: '❌ [四合一料號] 為必填項目！' };

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

        var fCheck1 = check1SeriesFormat(tankRawBatch);
        if (fCheck1 !== "OK") allErrors.push('❌ [' + item.name + '] ' + fCheck1);
        var fCheck7 = check7SeriesFormat(tankRawBatch);
        if (fCheck7 !== "OK") allErrors.push('❌ [' + item.name + '] ' + fCheck7);

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

    var cleanWhMat = cleanMatMaster(f[13]); 
    if (cleanWhMat !== masterMaterial) allErrors.push('❌ [繳庫單] 料號異常！');
    
    var whBatch1 = f[14].trim(); 
    var whBatch2 = f[15].trim();
    var whBatch3 = f[16].trim();

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

  if (allErrors.length > 0) return { status: 'error', message: allErrors.join('\n\n') };

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
    return { status: 'error', message: '寫入錯誤: ' + e.toString() };
  }
}

// ==========================================
// 4. 查詢功能 (包含後端排程交叉比對)
// ==========================================
function searchRecords(dateStart, dateEnd, keyword) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheets = ss.getSheets();
  var allData = [];
  
  var dStart = new Date(dateStart); dStart.setHours(0,0,0,0);
  var dEnd = new Date(dateEnd); dEnd.setHours(23,59,59,999);
  var hasKeyword = (keyword && keyword.toString().trim() !== "");
  var keyUpper = hasKeyword ? keyword.toString().toUpperCase().trim() : "";

  // 【預載】出貨排程，轉換為陣列以供快速比對
  var scheduleSheet = ss.getSheetByName("出貨排程");
  var scheduleBatches = [];
  if (scheduleSheet && scheduleSheet.getLastRow() > 0) {
    var sData = scheduleSheet.getDataRange().getDisplayValues();
    for (var sr = 0; sr < sData.length; sr++) {
      for (var sc = 0; sc < sData[sr].length; sc++) {
        var val = normalizeBatch(sData[sr][sc]);
        if (val !== "") scheduleBatches.push(val);
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
            mainBatch = extractBatchForWarehouse(row[2] || ""); // 取第一桶批號
        } else {
            record.master = { mat: row[10], batches: [row[11], row[12], row[13], row[14]] };
            record.wh = { mat: row[15], batches: [row[16], row[17], row[18]] };
            record.result = row[19] || "未知";
            var whB = row[16] ? row[16].toString().trim() : "";
            mainBatch = extractBatchForWarehouse(whB !== "" ? whB : (row[2] || "")); // 取繳庫或第一桶批號
        }

        // 進行排程交叉比對
        var inSch = false;
        if (mainBatch !== "") {
            var target = normalizeBatch(mainBatch);
            if (target.startsWith("2") && target.length > 8) target = target.substring(1);
            for (var sb = 0; sb < scheduleBatches.length; sb++) {
                if (scheduleBatches[sb] === target || scheduleBatches[sb].indexOf(target) !== -1) {
                    inSch = true; break;
                }
            }
        }
        record.inSchedule = inSch; // 將排程比對結果存入 record

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
// 6. 排程更新功能 (接收查詢前端貼上的 Excel)
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

```

---

### 檔案二：`Index.html` (純淨掃描介面)

```html
<!DOCTYPE html>
<html>
  <head>
    <base target="_top">
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="https://unpkg.com/html5-qrcode" type="text/javascript"></script>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700&display=swap" rel="stylesheet">
    <style>
      body { font-family: 'Noto Sans TC', sans-serif; background-color: #f0f2f5; padding: 10px; margin: 0; color: #444; }
      .container { max-width: 600px; margin: 0 auto; padding-bottom: 120px; }
      
      h3 { 
        text-align: center; color: #1a73e8; margin-bottom: 15px; font-weight: 700; font-size: 20px; 
        display: flex; flex-direction: column; justify-content: center; align-items: center; gap: 10px; position: relative; 
      }
      
      .query-link { 
        font-size: 14px; text-decoration: none; color: #555; font-weight: bold; 
        background: #fff; border: 1px solid #ddd; padding: 6px 15px; border-radius: 15px; white-space: nowrap; box-shadow: 0 1px 2px rgba(0,0,0,0.1);
      }
      .query-link:hover { background: #f8f9fa; }

      @media (min-width: 600px) {
        h3 { flex-direction: row; gap: 0; }
        .query-link { position: absolute; right: 0; top: 50%; transform: translateY(-50%); }
      }
      
      .top-control-bar { margin-bottom: 10px; display: flex; flex-direction: column; gap: 10px; }
      .mode-switch { display: flex; gap: 5px; width: 100%; justify-content: space-between; }
      .sub-control-bar { display: flex; gap: 5px; width: 100%; align-items: center; }

      .mode-option {
        background: white; padding: 10px 2px; border: 1px solid #dadce0; border-radius: 8px; cursor: pointer;
        font-size: 13px; font-weight: bold; color: #5f6368; transition: all 0.2s ease;
        display: flex; flex-direction: column; align-items: center; justify-content: center; flex: 1; text-align: center; height: 50px; box-shadow: 0 1px 2px rgba(0,0,0,0.05);
      }
      .mode-option:hover { border-color: #1a73e8; color: #1a73e8; }
      .mode-option.active { border: 2px solid #1a73e8; background: #e8f0fe; color: #1a73e8; box-shadow: 0 2px 5px rgba(26, 115, 232, 0.2); }
      
      input[type="radio"] { display: none; }
      
      .select-wrapper { flex: 1; display: flex; align-items: center; padding: 8px 12px; background: white; border: 1px solid #dadce0; border-radius: 8px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); height: 40px; box-sizing: border-box; }
      .select-wrapper label { font-size: 14px; font-weight: bold; color: #333; margin-right: 8px; white-space: nowrap; }
      .custom-select { border: none; background: transparent; font-size: 15px; font-weight: bold; color: #1a73e8; outline: none; width: 100%; cursor: pointer; }
      .qty-wrapper { display: none; background: #fff8e1; border-color: #fbbc04; } 

      .card { background: white; border-radius: 12px; padding: 15px; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.08); border-left: 5px solid #ccc; }
      .card-title { font-size: 16px; font-weight: 700; margin-bottom: 12px; display: flex; align-items: center; justify-content: space-between; color: #202124; }
      .c-blue { border-left-color: #4285f4; } .c-green { border-left-color: #34a853; } .c-orange { border-left-color: #fbbc04; }
      
      .input-group { display: flex; flex-direction: column; width: 100%; margin-bottom: 12px; }
      .input-group label { font-size: 13px; color: #5f6368; margin-bottom: 5px; font-weight: 600; margin-left: 2px; }
      .input-wrapper { position: relative; display: flex; align-items: center; width: 100%; }
      .input-wrapper input { width: 100%; padding: 12px 75px 12px 12px; border: 1px solid #dadce0; border-radius: 8px; font-size: 16px; box-sizing: border-box; background: #fff; transition: border 0.2s; height: 48px; }
      .input-wrapper input:focus { border-color: #4285f4; border-width: 2px; outline: none; padding-left: 11px; }
      .action-icons { position: absolute; right: 6px; top: 50%; transform: translateY(-50%); display: flex; gap: 6px; }
      .icon-btn { cursor: pointer; border-radius: 6px; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; font-size: 18px; }
      .scan-btn { background-color: #e8f0fe; color: #1a73e8; }
      .clear-btn { background-color: #fce8e6; color: #d93025; }
      
      .hidden-force { display: none !important; }
      .toggle-btn { font-size: 13px; color: #1a73e8; cursor: pointer; background: #e8f0fe; padding: 4px 10px; border-radius: 12px; text-decoration: none; display: inline-block; }
      
      #reader-modal { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.9); z-index: 9999; display: none; flex-direction: column; align-items: center; justify-content: center; }
      #reader { width: 90%; max-width: 500px; background: #000; border-radius: 12px; overflow: hidden; }
      #close-reader { margin-top: 20px; padding: 12px 30px; background: white; color: black; border: none; border-radius: 30px; font-weight: bold; font-size: 16px; cursor: pointer; }
      
      .btn-check { width: 100%; padding: 15px; background: #1a73e8; color: white; font-size: 18px; font-weight: bold; border: none; border-radius: 8px; margin-top: 10px; cursor: pointer; box-shadow: 0 4px 6px rgba(26, 115, 232, 0.3); }
      .btn-check:active { transform: scale(0.98); background: #185abc; }
      .btn-clear { background: none; color: #5f6368; margin-top: 20px; width: 100%; border: none; text-decoration: underline; cursor: pointer; font-size: 14px; padding: 10px; }
      
      #result { position: fixed; bottom: 20px; left: 5%; right: 5%; width: 90%; padding: 15px; text-align: left; font-weight: bold; border-radius: 12px; display: none; z-index: 999; box-shadow: 0 4px 15px rgba(0,0,0,0.3); box-sizing: border-box; cursor: pointer; }
      .success { background-color: #e6f4ea; color: #137333; border: 1px solid #ceead6; text-align: center !important; } 
      .error { background-color: #fce8e6; color: #c5221f; border: 1px solid #fad2cf; }
    </style>
  </head>
  <body onload="initPage()">
    <div id="reader-modal"><div id="reader"></div><button id="close-reader" onclick="stopScanner()">關閉鏡頭</button></div>

    <div class="container">
      <h3>
          <span>🔍 N系列BARCODE現場作業檢點</span>
          <a href="<?= ScriptApp.getService().getUrl() ?>?page=query" target="_blank" class="query-link">📊 查詢出貨紀錄</a>
      </h3>
      
      <div class="top-control-bar">
        <div class="mode-switch">
          <label class="mode-option active" id="opt-full"><input type="radio" name="checkMode" value="ship_full" checked><span>整板出貨</span></label>
          <label class="mode-option" id="opt-mixed"><input type="radio" name="checkMode" value="ship_mixed"><span>混板出貨</span></label>
          <label class="mode-option" id="opt-loose"><input type="radio" name="checkMode" value="ship_loose"><span>散桶</span></label>
          <label class="mode-option" id="opt-az"><input type="radio" name="checkMode" value="ship_az"><span>AZ檢查</span></label>
        </div>

        <div class="sub-control-bar">
            <div class="select-wrapper">
                <label>場所:</label>
                <select id="workLocation" class="custom-select">
                    <option value="崙尾一廠" selected>崙尾一廠</option>
                    <option value="本廠">本廠</option>
                </select>
            </div>
            <div class="select-wrapper qty-wrapper" id="qty-wrapper">
                <label>數量:</label>
                <select id="barrelCount" class="custom-select" onchange="updateLayout()">
                    <option value="1">1 桶</option>
                    <option value="2">2 桶</option>
                    <option value="3">3 桶</option>
                </select>
            </div>
        </div>
      </div>

      <script>
        function createInput(label, id, placeholder, wrapperId) {
          var wrapAttr = wrapperId ? `id="${wrapperId}"` : '';
          return `<div class="input-group" ${wrapAttr}><label>${label}</label><div class="input-wrapper"><input type="text" id="${id}" placeholder="${placeholder}"><div class="action-icons"><div class="icon-btn scan-btn" onclick="startScanner('${id}')">📷</div><div class="icon-btn clear-btn" onclick="clearOne('${id}')">✕</div></div></div></div>`;
        }
      </script>

      <div class="card c-blue">
        <div class="card-title">📦 1. 現場作業桶槽</div>
        <script>document.write(createInput('桶1 批號','f0','掃描批號QR'));</script>
        <script>document.write(createInput('桶1 料號','f1','掃描料號貼紙'));</script>
        <div id="row-tank-2">
          <script>document.write(createInput('桶2 批號','f2','掃描批號QR'));</script>
          <script>document.write(createInput('桶2 料號','f3','掃描料號貼紙'));</script>
        </div>
        <div id="row-tank-3">
          <script>document.write(createInput('桶3 批號','f4','掃描批號QR'));</script>
          <script>document.write(createInput('桶3 料號','f5','掃描料號貼紙'));</script>
        </div>
        <div id="row-tank-4">
          <script>document.write(createInput('桶4 批號','f6','掃描批號QR'));</script>
          <script>document.write(createInput('桶4 料號','f7','掃描料號貼紙'));</script>
        </div>
      </div>

      <div class="card c-green" id="card-master">
        <div class="card-title">🧩 2. 四合一標籤</div>
        <script>document.write(createInput('四合一 料號 (必填)','f8','掃描'));</script>
        <script>document.write(createInput('4in1 批號1 (對應桶1)','f9','掃描'));</script>
        <div id="wrap-batch-2"><script>document.write(createInput('4in1 批號2 (對應桶2)','f10','掃描'));</script></div>
        <div id="wrap-batch-3"><script>document.write(createInput('4in1 批號3 (對應桶3)','f11','掃描'));</script></div>
        <div id="wrap-batch-4"><script>document.write(createInput('4in1 批號4 (對應桶4)','f12','掃描'));</script></div>
      </div>
      
      <div class="card c-orange" id="card-wh">
        <div class="card-title">
            📄 3. 繳庫單
            <span class="toggle-btn" onclick="toggleThirdBatch()" id="btn-toggle-3">+ 新增第3批</span>
        </div>
        <script>document.write(createInput('繳庫 料號','f13','掃描'));</script>
        <script>document.write(createInput('繳庫 批號1','f14','掃描'));</script>
        <script>document.write(createInput('繳庫 批號2','f15','掃描'));</script>
        <div class="hidden-force" id="row-wh-3">
            <script>document.write(createInput('繳庫 批號3 (選填)','f16','極少數混3批時使用'));</script>
        </div>
      </div>

      <button class="btn-check" onclick="handleSubmit()">🚀 巡檢核對並存檔</button>
      <button class="btn-clear" onclick="manualClear()">清空重掃</button>
    </div>
    
    <div id="result"></div>

    <script>
      var currentMode = 'ship_full';
      var html5QrCode;
      var currentInputId = '';
      var inputTimer = null;

      function initPage() { 
        setupAutoHide();
        $('input[name="checkMode"]').change(function() { setMode(this.value); });
        setMode('ship_full'); 

        var savedLoc = localStorage.getItem('s_workLocation');
        if(savedLoc) $('#workLocation').val(savedLoc);
        $('#workLocation').change(function() { localStorage.setItem('s_workLocation', $(this).val()); });

        setupSmartJump(); 
        setTimeout(function() { var f = document.getElementById('f0'); if(f) f.focus(); }, 300);
      }

      function toggleThirdBatch() {
          var row = document.getElementById('row-wh-3');
          var btn = document.getElementById('btn-toggle-3');
          if (row.classList.contains('hidden-force')) {
              row.classList.remove('hidden-force');
              btn.innerText = "- 隱藏第3批";
              document.getElementById('f16').focus();
          } else {
              row.classList.add('hidden-force');
              btn.innerText = "+ 新增第3批";
              document.getElementById('f16').value = ""; 
          }
      }

      function setupAutoHide() {
         $(document).ready(function() {
             $(document).on('click touchstart', function(e) {
                 if (!$(e.target).closest('#result, .btn-check').length) {
                     if ($('#result').is(':visible') && $('#result').hasClass('error')) {
                         $('#result').fadeOut(300);
                     }
                 }
             });
             $('input, select').on('focus click', function() { $('#result').fadeOut(300); });
         });
      }

      function highlightField(id) {
          var el = document.getElementById(id);
          if(el) {
            el.style.backgroundColor = "#e8f0fe";
            setTimeout(function(){ el.style.backgroundColor = "#fff"; }, 500);
          }
      }

      function setupSmartJump() {
        document.addEventListener('input', function(e) {
          if (e.target.tagName === 'INPUT' && e.target.type === 'text') {
            if (inputTimer) clearTimeout(inputTimer);
            inputTimer = setTimeout(function() {
              if (e.target.value.trim() !== "") handleInputComplete(e.target.id, e.target.value.trim());
            }, 250);
          }
        });
        document.addEventListener('keydown', function(e) {
          if (e.target.tagName === 'INPUT' && e.target.type === 'text') {
            if (e.keyCode === 13 || e.key === 'Enter' || e.keyCode === 9) {
              e.preventDefault();
              if (inputTimer) clearTimeout(inputTimer);
              handleInputComplete(e.target.id, e.target.value.trim());
            }
          }
        });
      }

      function handleInputComplete(inputId, value) {
         document.getElementById(inputId).value = value;
         jumpToNext(inputId); 
      }

      function setMode(mode) {
        currentMode = mode;
        $('.mode-option').removeClass('active');
        if (mode === 'ship_full') $('#opt-full').addClass('active');
        else if (mode === 'ship_mixed') $('#opt-mixed').addClass('active');
        else if (mode === 'ship_az') $('#opt-az').addClass('active');
        else $('#opt-loose').addClass('active');
        
        var radios = document.getElementsByName('checkMode');
        for(var i=0; i<radios.length; i++) { if(radios[i].value === mode) radios[i].checked = true; }
        updateLayout();
      }

      function updateLayout() {
        var qtyWrapper = document.getElementById('qty-wrapper');
        var qtySelect = document.getElementById('barrelCount');
        var masterCard = document.getElementById('card-master');
        var whCard = document.getElementById('card-wh');
        var barrelCount = 4;

        qtyWrapper.style.display = 'none'; 
        masterCard.style.display = 'block'; 
        whCard.style.display = 'block';

        if (currentMode === 'ship_full' || currentMode === 'ship_mixed') {
          barrelCount = 4;
        } else if (currentMode === 'ship_az') {
          masterCard.style.display = 'none'; 
          whCard.style.display = 'none';
          barrelCount = 4;
        } else {
          qtyWrapper.style.display = 'flex';
          barrelCount = parseInt(qtySelect.value);
        }

        toggleVisibility('row-tank-2', barrelCount >= 2);
        toggleVisibility('wrap-batch-2', barrelCount >= 2);
        toggleVisibility('row-tank-3', barrelCount >= 3);
        toggleVisibility('wrap-batch-3', barrelCount >= 3);
        toggleVisibility('row-tank-4', barrelCount >= 4);
        toggleVisibility('wrap-batch-4', barrelCount >= 4);
      }

      function toggleVisibility(elementId, isVisible) {
        var el = document.getElementById(elementId);
        if (el) {
          if (isVisible) el.classList.remove('hidden-force');
          else el.classList.add('hidden-force');
        }
      }

      function startScanner(inputId) {
        currentInputId = inputId;
        document.getElementById('reader-modal').style.display = 'flex';
        html5QrCode = new Html5Qrcode("reader");
        html5QrCode.start(
          { facingMode: "environment" }, { fps: 10, qrbox: { width: 250, height: 250 } },
          (decodedText) => {
            document.getElementById(currentInputId).value = decodedText;
            stopScanner();
            handleInputComplete(currentInputId, decodedText);
          }, () => {}
        ).catch(err => { alert("無法啟動相機。"); document.getElementById('reader-modal').style.display = 'none'; });
      }

      function stopScanner() {
        if(html5QrCode) {
          html5QrCode.stop().then(() => { html5QrCode.clear(); document.getElementById('reader-modal').style.display = 'none'; });
        } else { document.getElementById('reader-modal').style.display = 'none'; }
      }

      function jumpToNext(currentId) {
        var inputs = Array.from(document.querySelectorAll('input[type=text]'));
        var visibleInputs = inputs.filter(input => input.offsetParent !== null);
        var currentIndex = visibleInputs.findIndex(input => input.id === currentId);
        if (currentIndex !== -1 && currentIndex < visibleInputs.length - 1) {
          var nextInput = visibleInputs[currentIndex + 1];
          nextInput.focus();
        }
      }

      function clearOne(id) { var el = document.getElementById(id); if (el) { el.value = ""; el.focus(); } }

      function handleSubmit() {
        var inputs = document.querySelectorAll('input[type=text]');
        inputs.forEach(function(input) { if (input.offsetParent === null) input.value = ""; });
        var fields = []; for(var i=0; i<17; i++) fields.push(document.getElementById('f'+i).value);
        var loc = $('#workLocation').val();

        if (currentMode !== 'ship_az' && fields[8].trim() === "") { alert("四合一料號必填!"); return; }
        if(!fields[1] && !fields[3] && !fields[5] && !fields[7]){ alert("請至少掃描一桶!"); return; }
        
        $('#result').hide();
        google.script.run.withSuccessHandler(onSuccess).withFailureHandler(onFailure).processAndSave({ 
            fields: fields, 
            mode: currentMode,
            location: loc
        });
      }

      function onSuccess(response) {
        var resDiv = document.getElementById('result');
        $(resDiv).removeClass('success error').show();
        if (response.status === 'success') {
          resDiv.className = 'success'; resDiv.innerHTML = response.message + '<br>(欄位已自動清空)';
          clearInputsOnly(); 
          setTimeout(function(){ document.getElementById('f0').focus(); }, 100);
          setTimeout(function(){ $(resDiv).fadeOut(500); }, 3000); 
        } else {
          resDiv.className = 'error'; resDiv.innerHTML = response.message.replace(/\n/g, '<br>');
        }
      }
      function onFailure(error) { alert("程式錯誤: "+error); }
      function clearInputsOnly() { for(var i=0; i<17; i++) document.getElementById('f'+i).value = ""; }
      function manualClear() { clearInputsOnly(); $('#result').hide(); document.getElementById('f0').focus(); }
    </script>
  </body>
</html>

```

---

### 檔案三：`Query.html` (查詢與排程管理介面)

```html
<!DOCTYPE html>
<html>
  <head>
    <base target="_top">
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
      body { font-family: 'Noto Sans TC', sans-serif; background-color: #f8f9fa; margin: 0; padding: 15px; color: #333; }
      .container { width: fit-content; min-width: 100%; margin: 0 auto; background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 1px 5px rgba(0,0,0,0.05); }
      
      .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 1px solid #eee; position: relative; }
      h3 { color: #1a73e8; margin: 0; font-size: 20px; font-weight: 700; display: flex; flex-direction: column; justify-content: center; align-items: center; gap: 10px; width: 100%; text-align: center; }
      
      .top-links { display: flex; gap: 10px; }
      .action-link { font-size: 13px; text-decoration: none; color: #555; font-weight: bold; background: #fff; padding: 8px 15px; border-radius: 20px; white-space: nowrap; border: 1px solid #ddd; cursor: pointer; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
      .action-link:hover { background: #f8f9fa; }
      .link-blue { color: #1a73e8; border-color: #d2e3fc; background: #e8f0fe; }

      @media (min-width: 600px) {
        h3 { flex-direction: row; justify-content: flex-start; text-align: left; width: auto; gap: 10px; }
        .top-links { margin-left: auto; }
      }

      .search-bar { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; background: #fff; padding: 0 0 15px 0; }
      .search-label { font-weight: bold; color: #444; font-size: 13px; margin-right: 2px; }
      .date-input { padding: 5px 8px; border: 1px solid #ccc; border-radius: 4px; font-size: 13px; color: #333; }
      .text-input { flex: 1; padding: 5px 8px; border: 1px solid #ccc; border-radius: 4px; font-size: 13px; min-width: 200px; }
      .btn-search { background-color: #1a73e8; color: white; border: none; padding: 6px 20px; border-radius: 4px; font-size: 13px; font-weight: bold; cursor: pointer; }
      .btn-search:hover { background-color: #1557b0; }

      .table-responsive { border: 1px solid #eee; border-radius: 6px; overflow-x: auto; }
      .data-table { width: auto; border-collapse: collapse; font-size: 12px; }
      .data-table th { background-color: #f1f3f4; color: #5f6368; font-weight: bold; text-align: left; padding: 10px 12px; border-bottom: 2px solid #ddd; white-space: nowrap; }
      .data-table td { padding: 8px 12px; border-bottom: 1px solid #f1f3f4; vertical-align: top; color: #3c4043; line-height: 1.4; white-space: nowrap; }
      .data-table tr:hover { background-color: #f8fbff; }

      .col-id    { width: 40px; color: #999; font-weight: bold; text-align: center; }
      .col-info  { width: 100px; } 
      .col-mode  { width: 60px; text-align: center; }
      .col-tanks { width: auto; min-width: 250px; } 
      .col-4in1  { width: auto; min-width: 150px; }   
      .col-wh    { width: auto; min-width: 150px; }   
      .col-res   { width: 140px; text-align: center; } 

      .data-table th.col-id, .data-table th.col-mode, .data-table th.col-res { text-align: center; }

      .loc-text { font-weight: bold; font-size: 13px; color: #202124; display: block; margin-bottom: 2px; }
      .date-text { font-size: 11px; color: #888; }
      .mode-badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; color: #1a73e8; background: #e8f0fe; }
      .mode-badge.az { color: #c5221f; background: #fce8e6; }
      
      .data-list { display: flex; flex-direction: column; gap: 4px; }
      .data-item { font-family: 'Roboto Mono', monospace; font-size: 11.5px; border-bottom: 1px dashed #eee; padding-bottom: 2px; white-space: nowrap; }
      .data-item:last-child { border-bottom: none; }
      
      .lbl { color: #5f6368; font-weight: bold; margin-right: 5px; font-size: 11px; }
      .txt-blue { color: #1a73e8; font-weight: bold; }
      .txt-green { color: #137333; font-weight: bold; }
      .txt-orange { color: #e37400; font-weight: bold; }

      .res-tag { display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; white-space: normal; line-height: 1.2; }
      .res-ok { background-color: #e6f4ea; color: #137333; border: 1px solid #ceead6; }
      .res-err { background-color: #fce8e6; color: #c5221f; border: 1px solid #fad2cf; }
      
      .sch-ok { margin-top:6px; font-size:11px; color:#137333; background:#e6f4ea; padding:3px 6px; border-radius:4px; display:inline-block; border:1px solid #ceead6; width: max-content; }
      .sch-err { margin-top:6px; font-size:11px; color:#c5221f; background:#fce8e6; padding:3px 6px; border-radius:4px; display:inline-block; border:1px solid #fad2cf; width: max-content; }

      #loading { text-align: center; padding: 30px; color: #5f6368; font-size: 14px; display: none; }
      .pagination { display: flex; justify-content: flex-end; align-items: center; gap: 10px; margin-top: 15px; }
      .page-btn { padding: 5px 12px; border: 1px solid #ddd; background: white; border-radius: 4px; cursor: pointer; color: #555; font-size: 12px; }
      .page-btn:disabled { background: #f5f5f5; color: #ccc; cursor: not-allowed; }

      /* --- 更新排程 Modal --- */
      #schedule-modal { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); z-index: 8888; display: none; justify-content: center; align-items: center; }
      .schedule-box { background: white; padding: 20px; border-radius: 12px; width: 90%; max-width: 500px; box-shadow: 0 4px 20px rgba(0,0,0,0.2); white-space: normal; }
      .schedule-box h4 { margin: 0 0 10px 0; color: #1a73e8; }
      .schedule-box p { font-size: 13px; color: #555; margin-bottom: 15px; line-height: 1.5; }
      .schedule-box textarea { width: 100%; height: 200px; border: 2px dashed #ccc; border-radius: 8px; padding: 10px; font-size: 12px; box-sizing: border-box; resize: none; }
      .schedule-box textarea:focus { border-color: #1a73e8; outline: none; }
      .modal-btns { display: flex; justify-content: flex-end; gap: 10px; margin-top: 15px; }
      .btn-cancel { padding: 8px 15px; border: none; background: #eee; color: #333; border-radius: 6px; cursor: pointer; font-weight: bold; }
      .btn-save { padding: 8px 20px; border: none; background: #1a73e8; color: white; border-radius: 6px; cursor: pointer; font-weight: bold; }
      .btn-save:hover { background: #1557b0; }
    </style>
  </head>
  <body>
    <div id="schedule-modal">
        <div class="schedule-box">
            <h4>📅 一鍵更新出貨排程</h4>
            <p>請前往 T100 匯出<b>「今日與近期」</b>的排程 Excel，將資料全選複製 (Ctrl+C)，然後在下方方塊中貼上 (Ctrl+V)。</p>
            <textarea id="schedule-data" placeholder="請在此貼上 Excel 資料..."></textarea>
            <div class="modal-btns">
                <button class="btn-cancel" onclick="closeScheduleModal()">取消</button>
                <button class="btn-save" onclick="submitSchedule()" id="btn-submit-schedule">💾 覆蓋儲存</button>
            </div>
        </div>
    </div>

    <div class="container">
      <div class="header">
        <h3>
          <span>📊 出貨紀錄查詢</span>
          <div class="top-links">
             <button class="action-link link-blue" onclick="openScheduleModal()">📅 更新排程</button>
             <button class="action-link" onclick="goHome()">← 返回掃描頁</button>
          </div>
        </h3>
      </div>

      <div class="search-bar">
        <span class="search-label">日期範圍 :</span>
        <input type="date" id="dateStart" class="date-input">
        <span style="color:#999">~</span>
        <input type="date" id="dateEnd" class="date-input">
        <span class="search-label" style="margin-left: 15px;">搜尋 :</span>
        <input type="text" id="batchInput" class="text-input" placeholder="輸入外箱條碼或批號...">
        <button class="btn-search" onclick="doSearch()">查詢</button>
      </div>

      <div id="loading">⏳ 資料搜尋中...</div>
      
      <div class="table-responsive">
        <table class="data-table">
          <thead>
            <tr>
              <th class="col-id">ID</th>
              <th class="col-info">時間 / 場所</th>
              <th class="col-mode">模式</th>
              <th class="col-tanks">桶槽作業紀錄 (1~4)</th>
              <th class="col-4in1">4合1 紀錄</th>
              <th class="col-wh">外箱條碼 / 料號</th> 
              <th class="col-res">判定結果</th>
            </tr>
          </thead>
          <tbody id="tableBody"></tbody>
        </table>
      </div>

      <div class="pagination" id="paginationControl" style="visibility:hidden;">
        <button class="page-btn" id="btnPrev" onclick="changePage(-1)">上一頁</button>
        <span id="pageInfo" style="font-size:13px; font-weight:bold; color:#5f6368;">第 1 頁</span>
        <button class="page-btn" id="btnNext" onclick="changePage(1)">下一頁</button>
      </div>
    </div>

    <script>
      var allData = [];
      var currentPage = 1;
      var pageSize = 20;

      window.onload = function() {
        var today = new Date().toISOString().split('T')[0];
        var lastWeek = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
        document.getElementById('dateStart').value = lastWeek;
        document.getElementById('dateEnd').value = today;
      };

      function goHome() {
         google.script.run.withSuccessHandler(function(url){
             window.top.location.href = url.split('?')[0]; 
         }).getScriptUrl();
      }

      function openScheduleModal() {
          document.getElementById('schedule-modal').style.display = 'flex';
          document.getElementById('schedule-data').value = ""; 
          document.getElementById('schedule-data').focus();
      }

      function closeScheduleModal() {
          document.getElementById('schedule-modal').style.display = 'none';
      }

      function submitSchedule() {
          var tsvData = document.getElementById('schedule-data').value.trim();
          if(tsvData === "") {
              alert("請先貼上資料！"); return;
          }
          
          var btn = document.getElementById('btn-submit-schedule');
          btn.innerText = "⏳ 儲存中...";
          btn.disabled = true;

          google.script.run
            .withSuccessHandler(function(res) {
                alert(res.msg);
                if(res.success) {
                   closeScheduleModal();
                   doSearch(); // 儲存後自動重新查詢
                }
                btn.innerText = "💾 覆蓋儲存";
                btn.disabled = false;
            })
            .withFailureHandler(function(err) {
                alert("伺服器錯誤：" + err);
                btn.innerText = "💾 覆蓋儲存";
                btn.disabled = false;
            })
            .updateScheduleData(tsvData);
      }

      function doSearch() {
        var ds = document.getElementById('dateStart').value;
        var de = document.getElementById('dateEnd').value;
        var kw = document.getElementById('batchInput').value.trim();
        
        document.getElementById('loading').style.display = 'block';
        document.getElementById('tableBody').innerHTML = '';
        document.getElementById('paginationControl').style.visibility = 'hidden';

        google.script.run
          .withSuccessHandler(function(data) {
             allData = data;
             currentPage = 1;
             renderTable();
             document.getElementById('loading').style.display = 'none';
             document.getElementById('paginationControl').style.visibility = (allData.length > 0) ? 'visible' : 'hidden';
          })
          .withFailureHandler(function(e){ 
             alert("查詢錯誤: " + e); 
             document.getElementById('loading').style.display = 'none'; 
          })
          .searchRecords(ds, de, kw);
      }

      function renderTable() {
        var tbody = document.getElementById('tableBody');
        tbody.innerHTML = "";
        
        if (!allData || allData.length === 0) {
          tbody.innerHTML = "<tr><td colspan='7' style='text-align:center; padding:30px; color:#888;'>查無資料</td></tr>";
          return;
        }

        var startIdx = (currentPage - 1) * pageSize;
        var endIdx = Math.min(startIdx + pageSize, allData.length);
        var pageData = allData.slice(startIdx, endIdx);

        document.getElementById('pageInfo').innerText = "第 " + currentPage + " 頁 / 共 " + Math.ceil(allData.length / pageSize) + " 頁";
        document.getElementById('btnPrev').disabled = (currentPage === 1);
        document.getElementById('btnNext').disabled = (endIdx >= allData.length);

        var html = "";
        pageData.forEach(function(row, index) {
           var globalIdx = allData.length - (startIdx + index); 
           var badgeClass = (row.mode.indexOf("AZ") !== -1) ? "az" : "";

           var whHtml = "<div class='data-list'>";
           if(row.wh.mat) whHtml += `<div class='data-item txt-orange'>Mat: ${row.wh.mat}</div>`;
           if(row.wh.batches) {
               row.wh.batches.forEach((b, k) => {
                   if(b) whHtml += `<div class='data-item'><span class='lbl'>W${k+1}:</span>${b}</div>`;
               });
           }
           whHtml += "</div>";

           var tankHtml = "<div class='data-list'>";
           for(var i=0; i<4; i++) {
               if(row.tanks[i].batch || row.tanks[i].mat) {
                   tankHtml += `<div class='data-item'><span class='lbl'>T${i+1}:</span>${row.tanks[i].batch} <span class='lbl' style='margin-left:5px;color:#1a73e8'>${row.tanks[i].mat}</span></div>`;
               }
           }
           tankHtml += "</div>";

           var masterHtml = "<div class='data-list'>";
           if(row.master.mat) masterHtml += `<div class='data-item txt-green'>Mat: ${row.master.mat}</div>`;
           if(row.master.batches) {
               row.master.batches.forEach((b, k) => {
                   if(b) masterHtml += `<div class='data-item'><span class='lbl'>B${k+1}:</span>${b}</div>`;
               });
           }
           masterHtml += "</div>";

           var resText = row.result || ""; 
           var resClass = (resText.indexOf("合格") !== -1) ? "res-ok" : "res-err";
           
           // 【排程狀態標籤】
           var schTag = row.inSchedule 
               ? `<div class="sch-ok">📅 排程相符</div>` 
               : `<div class="sch-err">⚠️ 不在排程</div>`;

           html += `<tr>
             <td class="col-id">#${globalIdx}</td>
             <td class="col-info">
                <span class="loc-text">${row.location}</span>
                <span class="date-text">${row.date}<br>${row.time}</span>
             </td>
             <td class="col-mode"><span class="mode-badge ${badgeClass}">${row.mode}</span></td>
             
             <td class="col-tanks">${tankHtml}</td>
             <td class="col-4in1">${masterHtml}</td>
             <td class="col-wh">${whHtml}</td>
             
             <td class="col-res">
                <span class="res-tag ${resClass}">${resText}</span><br>
                ${schTag}
             </td>
           </tr>`;
        });
        tbody.innerHTML = html;
      }

      function changePage(delta) { currentPage += delta; renderTable(); }
    </script>
  </body>
</html>

```

### 最後提醒：
請務必執行 **部署**$\rightarrow$**管理部署作業**$\rightarrow$**編輯 (✏️)**$\rightarrow$ 選擇 **建立新版本**$\rightarrow$ 點擊 **部署**。

## Turn 2

### 👤 User

可否製作排程核對關閉的開關

### 🤖 Assistant

這是一個非常貼心的設計！確實，有時候管理人員只是想單純「查閱歷史紀錄」，或者當天還沒匯入排程時，如果不關閉核對功能，畫面上會一直出現「⚠️ 不在排程」的紅字，視覺上會很干擾。
我幫您在 **查詢介面 (Query.html)** 增加了一個 **「🛡️ 啟用排程核對」的開關** (預設開啟)。

- **開啟時**：會去比對排程，並顯示「📅 排程相符」或「⚠️ 不在排程」。
- **關閉時**：不會去讀取排程資料，畫面乾乾淨淨，只顯示原本的「合格 / 異常」。
由於這只影響後台查詢，您的 `Index.html` (掃描介面) 完全不用改。請將以下兩個檔案 **清空並覆蓋** 即可：

---

### 第一步：覆蓋 `Code.gs` (後端加入開關接收)
請將您的 `Code.gs` 全選並替換為以下內容 (v34.1)：

```javascript
// ==========================================
// 1. 網頁入口 (路由控制)
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
        .setTitle('出貨核對系統 (v34.1)')
        .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL)
        .addMetaTag('viewport', 'width=device-width, initial-scale=1');
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
    if (s.toUpperCase().indexOf("T-0") === -1) return "❌ 格式錯誤！\n👉 [7開頭] 需包含 'T-0'";
  }
  if (s.toUpperCase().indexOf("T-0") !== -1 && !s.startsWith("7")) {
    return "❌ 格式錯誤！\n👉 含有 'T-0' 必須以 '7' 開頭";
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
// 3. 主程式 Logic (掃描端完全無排程阻擋)
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

        var fCheck1 = check1SeriesFormat(rawBatch);
        if (fCheck1 !== "OK") allErrors.push('❌ [' + item.name + '] ' + fCheck1);
        var fCheck7 = check7SeriesFormat(rawBatch);
        if (fCheck7 !== "OK") allErrors.push('❌ [' + item.name + '] ' + fCheck7);

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

    var masterMaterial = cleanMatMaster(f[8]); 
    if (!masterMaterial) return { status: 'error', message: '❌ [四合一料號] 為必填項目！' };

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

        var fCheck1 = check1SeriesFormat(tankRawBatch);
        if (fCheck1 !== "OK") allErrors.push('❌ [' + item.name + '] ' + fCheck1);
        var fCheck7 = check7SeriesFormat(tankRawBatch);
        if (fCheck7 !== "OK") allErrors.push('❌ [' + item.name + '] ' + fCheck7);

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

    var cleanWhMat = cleanMatMaster(f[13]); 
    if (cleanWhMat !== masterMaterial) allErrors.push('❌ [繳庫單] 料號異常！');
    
    var whBatch1 = f[14].trim(); 
    var whBatch2 = f[15].trim();
    var whBatch3 = f[16].trim();

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

  if (allErrors.length > 0) return { status: 'error', message: allErrors.join('\n\n') };

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
    return { status: 'error', message: '寫入錯誤: ' + e.toString() };
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

  // 根據前端傳來的 useScheduleCheck 決定要不要載入排程表
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

        // 如果開關啟用，才進行比對，否則預設給 null
        var inSch = null;
        if (useScheduleCheck === true && mainBatch !== "") {
            inSch = false; // 預設找不到
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
// 6. 排程更新功能
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

```

---

### 第二步：覆蓋 `Query.html` (加入排程開關按鈕)
請將您的 `Query.html` 全選並替換為以下內容：

```html
<!DOCTYPE html>
<html>
  <head>
    <base target="_top">
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
      body { font-family: 'Noto Sans TC', sans-serif; background-color: #f8f9fa; margin: 0; padding: 15px; color: #333; }
      .container { width: fit-content; min-width: 100%; margin: 0 auto; background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 1px 5px rgba(0,0,0,0.05); }
      
      .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 1px solid #eee; position: relative; }
      h3 { color: #1a73e8; margin: 0; font-size: 20px; font-weight: 700; display: flex; flex-direction: column; justify-content: center; align-items: center; gap: 10px; width: 100%; text-align: center; }
      
      .top-links { display: flex; gap: 10px; }
      .action-link { font-size: 13px; text-decoration: none; color: #555; font-weight: bold; background: #fff; padding: 8px 15px; border-radius: 20px; white-space: nowrap; border: 1px solid #ddd; cursor: pointer; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
      .action-link:hover { background: #f8f9fa; }
      .link-blue { color: #1a73e8; border-color: #d2e3fc; background: #e8f0fe; }

      @media (min-width: 600px) {
        h3 { flex-direction: row; justify-content: flex-start; text-align: left; width: auto; gap: 10px; }
        .top-links { margin-left: auto; }
      }

      .search-bar { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; background: #fff; padding: 0 0 15px 0; }
      .search-label { font-weight: bold; color: #444; font-size: 13px; margin-right: 2px; }
      .date-input { padding: 5px 8px; border: 1px solid #ccc; border-radius: 4px; font-size: 13px; color: #333; }
      .text-input { flex: 1; padding: 5px 8px; border: 1px solid #ccc; border-radius: 4px; font-size: 13px; min-width: 200px; }
      .btn-search { background-color: #1a73e8; color: white; border: none; padding: 6px 20px; border-radius: 4px; font-size: 13px; font-weight: bold; cursor: pointer; margin-left: auto; }
      .btn-search:hover { background-color: #1557b0; }

      /* 開關樣式 */
      .toggle-switch { display: flex; align-items: center; background: #e8f0fe; padding: 5px 10px; border-radius: 6px; border: 1px solid #d2e3fc; margin-left: 10px; cursor: pointer; }
      .toggle-switch input { margin: 0 5px 0 0; cursor: pointer; width: 14px; height: 14px; }
      .toggle-switch span { font-size: 13px; font-weight: bold; color: #1a73e8; }

      .table-responsive { border: 1px solid #eee; border-radius: 6px; overflow-x: auto; }
      .data-table { width: auto; border-collapse: collapse; font-size: 12px; }
      .data-table th { background-color: #f1f3f4; color: #5f6368; font-weight: bold; text-align: left; padding: 10px 12px; border-bottom: 2px solid #ddd; white-space: nowrap; }
      .data-table td { padding: 8px 12px; border-bottom: 1px solid #f1f3f4; vertical-align: top; color: #3c4043; line-height: 1.4; white-space: nowrap; }
      .data-table tr:hover { background-color: #f8fbff; }

      .col-id    { width: 40px; color: #999; font-weight: bold; text-align: center; }
      .col-info  { width: 100px; } 
      .col-mode  { width: 60px; text-align: center; }
      .col-tanks { width: auto; min-width: 250px; } 
      .col-4in1  { width: auto; min-width: 150px; }   
      .col-wh    { width: auto; min-width: 150px; }   
      .col-res   { width: 140px; text-align: center; } 

      .data-table th.col-id, .data-table th.col-mode, .data-table th.col-res { text-align: center; }

      .loc-text { font-weight: bold; font-size: 13px; color: #202124; display: block; margin-bottom: 2px; }
      .date-text { font-size: 11px; color: #888; }
      .mode-badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; color: #1a73e8; background: #e8f0fe; }
      .mode-badge.az { color: #c5221f; background: #fce8e6; }
      
      .data-list { display: flex; flex-direction: column; gap: 4px; }
      .data-item { font-family: 'Roboto Mono', monospace; font-size: 11.5px; border-bottom: 1px dashed #eee; padding-bottom: 2px; white-space: nowrap; }
      .data-item:last-child { border-bottom: none; }
      
      .lbl { color: #5f6368; font-weight: bold; margin-right: 5px; font-size: 11px; }
      .txt-blue { color: #1a73e8; font-weight: bold; }
      .txt-green { color: #137333; font-weight: bold; }
      .txt-orange { color: #e37400; font-weight: bold; }

      .res-tag { display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; white-space: normal; line-height: 1.2; }
      .res-ok { background-color: #e6f4ea; color: #137333; border: 1px solid #ceead6; }
      .res-err { background-color: #fce8e6; color: #c5221f; border: 1px solid #fad2cf; }
      
      .sch-ok { margin-top:6px; font-size:11px; color:#137333; background:#e6f4ea; padding:3px 6px; border-radius:4px; display:inline-block; border:1px solid #ceead6; width: max-content; }
      .sch-err { margin-top:6px; font-size:11px; color:#c5221f; background:#fce8e6; padding:3px 6px; border-radius:4px; display:inline-block; border:1px solid #fad2cf; width: max-content; }

      #loading { text-align: center; padding: 30px; color: #5f6368; font-size: 14px; display: none; }
      .pagination { display: flex; justify-content: flex-end; align-items: center; gap: 10px; margin-top: 15px; }
      .page-btn { padding: 5px 12px; border: 1px solid #ddd; background: white; border-radius: 4px; cursor: pointer; color: #555; font-size: 12px; }
      .page-btn:disabled { background: #f5f5f5; color: #ccc; cursor: not-allowed; }

      /* --- 更新排程 Modal --- */
      #schedule-modal { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); z-index: 8888; display: none; justify-content: center; align-items: center; }
      .schedule-box { background: white; padding: 20px; border-radius: 12px; width: 90%; max-width: 500px; box-shadow: 0 4px 20px rgba(0,0,0,0.2); white-space: normal; }
      .schedule-box h4 { margin: 0 0 10px 0; color: #1a73e8; }
      .schedule-box p { font-size: 13px; color: #555; margin-bottom: 15px; line-height: 1.5; }
      .schedule-box textarea { width: 100%; height: 200px; border: 2px dashed #ccc; border-radius: 8px; padding: 10px; font-size: 12px; box-sizing: border-box; resize: none; }
      .schedule-box textarea:focus { border-color: #1a73e8; outline: none; }
      .modal-btns { display: flex; justify-content: flex-end; gap: 10px; margin-top: 15px; }
      .btn-cancel { padding: 8px 15px; border: none; background: #eee; color: #333; border-radius: 6px; cursor: pointer; font-weight: bold; }
      .btn-save { padding: 8px 20px; border: none; background: #1a73e8; color: white; border-radius: 6px; cursor: pointer; font-weight: bold; }
      .btn-save:hover { background: #1557b0; }
    </style>
  </head>
  <body>
    <div id="schedule-modal">
        <div class="schedule-box">
            <h4>📅 一鍵更新出貨排程</h4>
            <p>請前往 T100 匯出<b>「近期與今日」</b>的排程 Excel，將資料全選複製 (Ctrl+C)，然後在下方方塊中貼上 (Ctrl+V)。</p>
            <textarea id="schedule-data" placeholder="請在此貼上 Excel 資料..."></textarea>
            <div class="modal-btns">
                <button class="btn-cancel" onclick="closeScheduleModal()">取消</button>
                <button class="btn-save" onclick="submitSchedule()" id="btn-submit-schedule">💾 覆蓋儲存</button>
            </div>
        </div>
    </div>

    <div class="container">
      <div class="header">
        <h3>
          <span>📊 出貨紀錄查詢</span>
          <div class="top-links">
             <button class="action-link link-blue" onclick="openScheduleModal()">📅 更新排程</button>
             <button class="action-link" onclick="goHome()">← 返回掃描頁</button>
          </div>
        </h3>
      </div>

      <div class="search-bar">
        <span class="search-label">日期範圍 :</span>
        <input type="date" id="dateStart" class="date-input">
        <span style="color:#999">~</span>
        <input type="date" id="dateEnd" class="date-input">
        <span class="search-label" style="margin-left: 15px;">搜尋 :</span>
        <input type="text" id="batchInput" class="text-input" placeholder="輸入外箱條碼或批號...">
        
        <label class="toggle-switch">
          <input type="checkbox" id="checkScheduleToggle" checked>
          <span>🛡️ 啟用排程核對</span>
        </label>

        <button class="btn-search" onclick="doSearch()">查詢</button>
      </div>

      <div id="loading">⏳ 資料搜尋中...</div>
      
      <div class="table-responsive">
        <table class="data-table">
          <thead>
            <tr>
              <th class="col-id">ID</th>
              <th class="col-info">時間 / 場所</th>
              <th class="col-mode">模式</th>
              <th class="col-tanks">桶槽作業紀錄 (1~4)</th>
              <th class="col-4in1">4合1 紀錄</th>
              <th class="col-wh">外箱條碼 / 料號</th> 
              <th class="col-res">判定結果</th>
            </tr>
          </thead>
          <tbody id="tableBody"></tbody>
        </table>
      </div>

      <div class="pagination" id="paginationControl" style="visibility:hidden;">
        <button class="page-btn" id="btnPrev" onclick="changePage(-1)">上一頁</button>
        <span id="pageInfo" style="font-size:13px; font-weight:bold; color:#5f6368;">第 1 頁</span>
        <button class="page-btn" id="btnNext" onclick="changePage(1)">下一頁</button>
      </div>
    </div>

    <script>
      var allData = [];
      var currentPage = 1;
      var pageSize = 20;

      window.onload = function() {
        var today = new Date().toISOString().split('T')[0];
        var lastWeek = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
        document.getElementById('dateStart').value = lastWeek;
        document.getElementById('dateEnd').value = today;
      };

      function goHome() {
         google.script.run.withSuccessHandler(function(url){
             window.top.location.href = url.split('?')[0]; 
         }).getScriptUrl();
      }

      function openScheduleModal() {
          document.getElementById('schedule-modal').style.display = 'flex';
          document.getElementById('schedule-data').value = ""; 
          document.getElementById('schedule-data').focus();
      }

      function closeScheduleModal() {
          document.getElementById('schedule-modal').style.display = 'none';
      }

      function submitSchedule() {
          var tsvData = document.getElementById('schedule-data').value.trim();
          if(tsvData === "") {
              alert("請先貼上資料！"); return;
          }
          
          var btn = document.getElementById('btn-submit-schedule');
          btn.innerText = "⏳ 儲存中...";
          btn.disabled = true;

          google.script.run
            .withSuccessHandler(function(res) {
                alert(res.msg);
                if(res.success) {
                   closeScheduleModal();
                   doSearch(); // 儲存後自動重新查詢
                }
                btn.innerText = "💾 覆蓋儲存";
                btn.disabled = false;
            })
            .withFailureHandler(function(err) {
                alert("伺服器錯誤：" + err);
                btn.innerText = "💾 覆蓋儲存";
                btn.disabled = false;
            })
            .updateScheduleData(tsvData);
      }

      function doSearch() {
        var ds = document.getElementById('dateStart').value;
        var de = document.getElementById('dateEnd').value;
        var kw = document.getElementById('batchInput').value.trim();
        var useSchedule = document.getElementById('checkScheduleToggle').checked; // 讀取開關狀態
        
        document.getElementById('loading').style.display = 'block';
        document.getElementById('tableBody').innerHTML = '';
        document.getElementById('paginationControl').style.visibility = 'hidden';

        google.script.run
          .withSuccessHandler(function(data) {
             allData = data;
             currentPage = 1;
             renderTable();
             document.getElementById('loading').style.display = 'none';
             document.getElementById('paginationControl').style.visibility = (allData.length > 0) ? 'visible' : 'hidden';
          })
          .withFailureHandler(function(e){ 
             alert("查詢錯誤: " + e); 
             document.getElementById('loading').style.display = 'none'; 
          })
          .searchRecords(ds, de, kw, useSchedule); // 將開關狀態傳給後端
      }

      function renderTable() {
        var tbody = document.getElementById('tableBody');
        tbody.innerHTML = "";
        
        if (!allData || allData.length === 0) {
          tbody.innerHTML = "<tr><td colspan='7' style='text-align:center; padding:30px; color:#888;'>查無資料</td></tr>";
          return;
        }

        var startIdx = (currentPage - 1) * pageSize;
        var endIdx = Math.min(startIdx + pageSize, allData.length);
        var pageData = allData.slice(startIdx, endIdx);

        document.getElementById('pageInfo').innerText = "第 " + currentPage + " 頁 / 共 " + Math.ceil(allData.length / pageSize) + " 頁";
        document.getElementById('btnPrev').disabled = (currentPage === 1);
        document.getElementById('btnNext').disabled = (endIdx >= allData.length);

        var html = "";
        pageData.forEach(function(row, index) {
           var globalIdx = allData.length - (startIdx + index); 
           var badgeClass = (row.mode.indexOf("AZ") !== -1) ? "az" : "";

           var whHtml = "<div class='data-list'>";
           if(row.wh.mat) whHtml += `<div class='data-item txt-orange'>Mat: ${row.wh.mat}</div>`;
           if(row.wh.batches) {
               row.wh.batches.forEach((b, k) => {
                   if(b) whHtml += `<div class='data-item'><span class='lbl'>W${k+1}:</span>${b}</div>`;
               });
           }
           whHtml += "</div>";

           var tankHtml = "<div class='data-list'>";
           for(var i=0; i<4; i++) {
               if(row.tanks[i].batch || row.tanks[i].mat) {
                   tankHtml += `<div class='data-item'><span class='lbl'>T${i+1}:</span>${row.tanks[i].batch} <span class='lbl' style='margin-left:5px;color:#1a73e8'>${row.tanks[i].mat}</span></div>`;
               }
           }
           tankHtml += "</div>";

           var masterHtml = "<div class='data-list'>";
           if(row.master.mat) masterHtml += `<div class='data-item txt-green'>Mat: ${row.master.mat}</div>`;
           if(row.master.batches) {
               row.master.batches.forEach((b, k) => {
                   if(b) masterHtml += `<div class='data-item'><span class='lbl'>B${k+1}:</span>${b}</div>`;
               });
           }
           masterHtml += "</div>";

           var resText = row.result || ""; 
           var resClass = (resText.indexOf("合格") !== -1) ? "res-ok" : "res-err";
           
           // 【排程狀態標籤】：只有開關啟用且判斷過，才會顯示
           var schTag = "";
           if (row.inSchedule === true) {
               schTag = `<div class="sch-ok">📅 排程相符</div>`;
           } else if (row.inSchedule === false) {
               schTag = `<div class="sch-err">⚠️ 不在排程</div>`;
           }

           html += `<tr>
             <td class="col-id">#${globalIdx}</td>
             <td class="col-info">
                <span class="loc-text">${row.location}</span>
                <span class="date-text">${row.date}<br>${row.time}</span>
             </td>
             <td class="col-mode"><span class="mode-badge ${badgeClass}">${row.mode}</span></td>
             
             <td class="col-tanks">${tankHtml}</td>
             <td class="col-4in1">${masterHtml}</td>
             <td class="col-wh">${whHtml}</td>
             
             <td class="col-res">
                <span class="res-tag ${resClass}">${resText}</span><br>
                ${schTag}
             </td>
           </tr>`;
        });
        tbody.innerHTML = html;
      }

      function changePage(delta) { currentPage += delta; renderTable(); }
    </script>
  </body>
</html>

```
**更新完成後，記得一定要點擊「部署 → 建立新版本」！**
如果這幾天排程沒有更新，您隨時可以把開關關掉，就可以舒適地看歷史紀錄了。

## Turn 3

### 👤 User

*[This turn includes uploaded images]*

![上傳圖片預覽](https://lh3.googleusercontent.com/gg/AEir0wJ1Q_T1I69wV7klDCWTQ67tSibOlehiPVkzkdeVUX8SvCykyAcrTv3WxYjhf4GjRqDyJ-4BLDZaGvJ6_elZWyxTCioQzQtKNNDISaHurGKAL6nzk3RpRJs2FiD1HWYQOBdScWZD6MIjLbuE0gqneTgydtyvOaD401zlF2PHoKoKX0iwej4wVfPOYhv_yOJ7T4D13a6hocHSvuFHkQtvpeFd8ohSVluaJVM5kLUZzndv-3Rl92ZM-ptuBOOTkCXoqI62kiTclyTa7DXulzA97xBf03QSCu7tmQ?authuser=1)

關閉排程核對 還是有顯示不在排程的提醒

### 🤖 Assistant

發現問題了！從您提供的截圖來看，這是因為您把開關「取消勾選」後，**沒有再次點擊右邊的【查詢】按鈕**。
在原本的設計中，系統還保留著「上一次勾選時查詢的舊資料」，所以標籤沒有消失。
為了讓操作更直覺、不需人員多按一個按鈕，我幫您做了一個小升級：

1. **開關連動**：現在只要您一扳動開關（打勾或取消），系統就會**自動重新整理表格**，不用再手動按查詢。
2. **強制隱藏**：在前端顯示時多加一層保護，只要開關是「關」的，就絕對不顯示任何排程標籤。
您只需要重新覆蓋 **Query.html** 這個檔案即可（`Code.gs` 和 `Index.html` 不用動）。

---

### 請將 `Query.html` 全選並替換為以下內容：

```html
<!DOCTYPE html>
<html>
  <head>
    <base target="_top">
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
      body { font-family: 'Noto Sans TC', sans-serif; background-color: #f8f9fa; margin: 0; padding: 15px; color: #333; }
      .container { width: fit-content; min-width: 100%; margin: 0 auto; background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 1px 5px rgba(0,0,0,0.05); }
      
      .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 1px solid #eee; position: relative; }
      h3 { color: #1a73e8; margin: 0; font-size: 20px; font-weight: 700; display: flex; flex-direction: column; justify-content: center; align-items: center; gap: 10px; width: 100%; text-align: center; }
      
      .top-links { display: flex; gap: 10px; }
      .action-link { font-size: 13px; text-decoration: none; color: #555; font-weight: bold; background: #fff; padding: 8px 15px; border-radius: 20px; white-space: nowrap; border: 1px solid #ddd; cursor: pointer; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
      .action-link:hover { background: #f8f9fa; }
      .link-blue { color: #1a73e8; border-color: #d2e3fc; background: #e8f0fe; }

      @media (min-width: 600px) {
        h3 { flex-direction: row; justify-content: flex-start; text-align: left; width: auto; gap: 10px; }
        .top-links { margin-left: auto; }
      }

      .search-bar { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; background: #fff; padding: 0 0 15px 0; }
      .search-label { font-weight: bold; color: #444; font-size: 13px; margin-right: 2px; }
      .date-input { padding: 5px 8px; border: 1px solid #ccc; border-radius: 4px; font-size: 13px; color: #333; }
      .text-input { flex: 1; padding: 5px 8px; border: 1px solid #ccc; border-radius: 4px; font-size: 13px; min-width: 200px; }
      .btn-search { background-color: #1a73e8; color: white; border: none; padding: 6px 20px; border-radius: 4px; font-size: 13px; font-weight: bold; cursor: pointer; margin-left: auto; }
      .btn-search:hover { background-color: #1557b0; }

      /* 開關樣式 */
      .toggle-switch { display: flex; align-items: center; background: #e8f0fe; padding: 5px 10px; border-radius: 6px; border: 1px solid #d2e3fc; margin-left: 10px; cursor: pointer; }
      .toggle-switch input { margin: 0 5px 0 0; cursor: pointer; width: 14px; height: 14px; }
      .toggle-switch span { font-size: 13px; font-weight: bold; color: #1a73e8; }

      .table-responsive { border: 1px solid #eee; border-radius: 6px; overflow-x: auto; }
      .data-table { width: auto; border-collapse: collapse; font-size: 12px; }
      .data-table th { background-color: #f1f3f4; color: #5f6368; font-weight: bold; text-align: left; padding: 10px 12px; border-bottom: 2px solid #ddd; white-space: nowrap; }
      .data-table td { padding: 8px 12px; border-bottom: 1px solid #f1f3f4; vertical-align: top; color: #3c4043; line-height: 1.4; white-space: nowrap; }
      .data-table tr:hover { background-color: #f8fbff; }

      .col-id    { width: 40px; color: #999; font-weight: bold; text-align: center; }
      .col-info  { width: 100px; } 
      .col-mode  { width: 60px; text-align: center; }
      .col-tanks { width: auto; min-width: 250px; } 
      .col-4in1  { width: auto; min-width: 150px; }   
      .col-wh    { width: auto; min-width: 150px; }   
      .col-res   { width: 140px; text-align: center; } 

      .data-table th.col-id, .data-table th.col-mode, .data-table th.col-res { text-align: center; }

      .loc-text { font-weight: bold; font-size: 13px; color: #202124; display: block; margin-bottom: 2px; }
      .date-text { font-size: 11px; color: #888; }
      .mode-badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; color: #1a73e8; background: #e8f0fe; }
      .mode-badge.az { color: #c5221f; background: #fce8e6; }
      
      .data-list { display: flex; flex-direction: column; gap: 4px; }
      .data-item { font-family: 'Roboto Mono', monospace; font-size: 11.5px; border-bottom: 1px dashed #eee; padding-bottom: 2px; white-space: nowrap; }
      .data-item:last-child { border-bottom: none; }
      
      .lbl { color: #5f6368; font-weight: bold; margin-right: 5px; font-size: 11px; }
      .txt-blue { color: #1a73e8; font-weight: bold; }
      .txt-green { color: #137333; font-weight: bold; }
      .txt-orange { color: #e37400; font-weight: bold; }

      .res-tag { display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; white-space: normal; line-height: 1.2; }
      .res-ok { background-color: #e6f4ea; color: #137333; border: 1px solid #ceead6; }
      .res-err { background-color: #fce8e6; color: #c5221f; border: 1px solid #fad2cf; }
      
      .sch-ok { margin-top:6px; font-size:11px; color:#137333; background:#e6f4ea; padding:3px 6px; border-radius:4px; display:inline-block; border:1px solid #ceead6; width: max-content; }
      .sch-err { margin-top:6px; font-size:11px; color:#c5221f; background:#fce8e6; padding:3px 6px; border-radius:4px; display:inline-block; border:1px solid #fad2cf; width: max-content; }

      #loading { text-align: center; padding: 30px; color: #5f6368; font-size: 14px; display: none; }
      .pagination { display: flex; justify-content: flex-end; align-items: center; gap: 10px; margin-top: 15px; }
      .page-btn { padding: 5px 12px; border: 1px solid #ddd; background: white; border-radius: 4px; cursor: pointer; color: #555; font-size: 12px; }
      .page-btn:disabled { background: #f5f5f5; color: #ccc; cursor: not-allowed; }

      /* --- 更新排程 Modal --- */
      #schedule-modal { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); z-index: 8888; display: none; justify-content: center; align-items: center; }
      .schedule-box { background: white; padding: 20px; border-radius: 12px; width: 90%; max-width: 500px; box-shadow: 0 4px 20px rgba(0,0,0,0.2); white-space: normal; }
      .schedule-box h4 { margin: 0 0 10px 0; color: #1a73e8; }
      .schedule-box p { font-size: 13px; color: #555; margin-bottom: 15px; line-height: 1.5; }
      .schedule-box textarea { width: 100%; height: 200px; border: 2px dashed #ccc; border-radius: 8px; padding: 10px; font-size: 12px; box-sizing: border-box; resize: none; }
      .schedule-box textarea:focus { border-color: #1a73e8; outline: none; }
      .modal-btns { display: flex; justify-content: flex-end; gap: 10px; margin-top: 15px; }
      .btn-cancel { padding: 8px 15px; border: none; background: #eee; color: #333; border-radius: 6px; cursor: pointer; font-weight: bold; }
      .btn-save { padding: 8px 20px; border: none; background: #1a73e8; color: white; border-radius: 6px; cursor: pointer; font-weight: bold; }
      .btn-save:hover { background: #1557b0; }
    </style>
  </head>
  <body>
    <div id="schedule-modal">
        <div class="schedule-box">
            <h4>📅 一鍵更新出貨排程</h4>
            <p>請前往 T100 匯出<b>「近期與今日」</b>的排程 Excel，將資料全選複製 (Ctrl+C)，然後在下方方塊中貼上 (Ctrl+V)。</p>
            <textarea id="schedule-data" placeholder="請在此貼上 Excel 資料..."></textarea>
            <div class="modal-btns">
                <button class="btn-cancel" onclick="closeScheduleModal()">取消</button>
                <button class="btn-save" onclick="submitSchedule()" id="btn-submit-schedule">💾 覆蓋儲存</button>
            </div>
        </div>
    </div>

    <div class="container">
      <div class="header">
        <h3>
          <span>📊 出貨紀錄查詢</span>
          <div class="top-links">
             <button class="action-link link-blue" onclick="openScheduleModal()">📅 更新排程</button>
             <button class="action-link" onclick="goHome()">← 返回掃描頁</button>
          </div>
        </h3>
      </div>

      <div class="search-bar">
        <span class="search-label">日期範圍 :</span>
        <input type="date" id="dateStart" class="date-input">
        <span style="color:#999">~</span>
        <input type="date" id="dateEnd" class="date-input">
        <span class="search-label" style="margin-left: 15px;">搜尋 :</span>
        <input type="text" id="batchInput" class="text-input" placeholder="輸入外箱條碼或批號...">
        
        <label class="toggle-switch">
          <input type="checkbox" id="checkScheduleToggle" checked onchange="doSearch()">
          <span>🛡️ 啟用排程核對</span>
        </label>

        <button class="btn-search" onclick="doSearch()">查詢</button>
      </div>

      <div id="loading">⏳ 資料搜尋中...</div>
      
      <div class="table-responsive">
        <table class="data-table">
          <thead>
            <tr>
              <th class="col-id">ID</th>
              <th class="col-info">時間 / 場所</th>
              <th class="col-mode">模式</th>
              <th class="col-tanks">桶槽作業紀錄 (1~4)</th>
              <th class="col-4in1">4合1 紀錄</th>
              <th class="col-wh">外箱條碼 / 料號</th> 
              <th class="col-res">判定結果</th>
            </tr>
          </thead>
          <tbody id="tableBody"></tbody>
        </table>
      </div>

      <div class="pagination" id="paginationControl" style="visibility:hidden;">
        <button class="page-btn" id="btnPrev" onclick="changePage(-1)">上一頁</button>
        <span id="pageInfo" style="font-size:13px; font-weight:bold; color:#5f6368;">第 1 頁</span>
        <button class="page-btn" id="btnNext" onclick="changePage(1)">下一頁</button>
      </div>
    </div>

    <script>
      var allData = [];
      var currentPage = 1;
      var pageSize = 20;

      window.onload = function() {
        var today = new Date().toISOString().split('T')[0];
        var lastWeek = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
        document.getElementById('dateStart').value = lastWeek;
        document.getElementById('dateEnd').value = today;
      };

      function goHome() {
         google.script.run.withSuccessHandler(function(url){
             window.top.location.href = url.split('?')[0]; 
         }).getScriptUrl();
      }

      function openScheduleModal() {
          document.getElementById('schedule-modal').style.display = 'flex';
          document.getElementById('schedule-data').value = ""; 
          document.getElementById('schedule-data').focus();
      }

      function closeScheduleModal() {
          document.getElementById('schedule-modal').style.display = 'none';
      }

      function submitSchedule() {
          var tsvData = document.getElementById('schedule-data').value.trim();
          if(tsvData === "") {
              alert("請先貼上資料！"); return;
          }
          
          var btn = document.getElementById('btn-submit-schedule');
          btn.innerText = "⏳ 儲存中...";
          btn.disabled = true;

          google.script.run
            .withSuccessHandler(function(res) {
                alert(res.msg);
                if(res.success) {
                   closeScheduleModal();
                   doSearch(); // 儲存後自動重新查詢
                }
                btn.innerText = "💾 覆蓋儲存";
                btn.disabled = false;
            })
            .withFailureHandler(function(err) {
                alert("伺服器錯誤：" + err);
                btn.innerText = "💾 覆蓋儲存";
                btn.disabled = false;
            })
            .updateScheduleData(tsvData);
      }

      function doSearch() {
        var ds = document.getElementById('dateStart').value;
        var de = document.getElementById('dateEnd').value;
        var kw = document.getElementById('batchInput').value.trim();
        var useSchedule = document.getElementById('checkScheduleToggle').checked; 
        
        document.getElementById('loading').style.display = 'block';
        document.getElementById('tableBody').innerHTML = '';
        document.getElementById('paginationControl').style.visibility = 'hidden';

        google.script.run
          .withSuccessHandler(function(data) {
             allData = data;
             currentPage = 1;
             renderTable();
             document.getElementById('loading').style.display = 'none';
             document.getElementById('paginationControl').style.visibility = (allData.length > 0) ? 'visible' : 'hidden';
          })
          .withFailureHandler(function(e){ 
             alert("查詢錯誤: " + e); 
             document.getElementById('loading').style.display = 'none'; 
          })
          .searchRecords(ds, de, kw, useSchedule); 
      }

      function renderTable() {
        var tbody = document.getElementById('tableBody');
        tbody.innerHTML = "";
        
        if (!allData || allData.length === 0) {
          tbody.innerHTML = "<tr><td colspan='7' style='text-align:center; padding:30px; color:#888;'>查無資料</td></tr>";
          return;
        }

        var startIdx = (currentPage - 1) * pageSize;
        var endIdx = Math.min(startIdx + pageSize, allData.length);
        var pageData = allData.slice(startIdx, endIdx);

        document.getElementById('pageInfo').innerText = "第 " + currentPage + " 頁 / 共 " + Math.ceil(allData.length / pageSize) + " 頁";
        document.getElementById('btnPrev').disabled = (currentPage === 1);
        document.getElementById('btnNext').disabled = (endIdx >= allData.length);

        // 【關鍵修改】：即時讀取開關狀態，做二次保護
        var useSchedule = document.getElementById('checkScheduleToggle').checked;

        var html = "";
        pageData.forEach(function(row, index) {
           var globalIdx = allData.length - (startIdx + index); 
           var badgeClass = (row.mode.indexOf("AZ") !== -1) ? "az" : "";

           var whHtml = "<div class='data-list'>";
           if(row.wh.mat) whHtml += `<div class='data-item txt-orange'>Mat: ${row.wh.mat}</div>`;
           if(row.wh.batches) {
               row.wh.batches.forEach((b, k) => {
                   if(b) whHtml += `<div class='data-item'><span class='lbl'>W${k+1}:</span>${b}</div>`;
               });
           }
           whHtml += "</div>";

           var tankHtml = "<div class='data-list'>";
           for(var i=0; i<4; i++) {
               if(row.tanks[i].batch || row.tanks[i].mat) {
                   tankHtml += `<div class='data-item'><span class='lbl'>T${i+1}:</span>${row.tanks[i].batch} <span class='lbl' style='margin-left:5px;color:#1a73e8'>${row.tanks[i].mat}</span></div>`;
               }
           }
           tankHtml += "</div>";

           var masterHtml = "<div class='data-list'>";
           if(row.master.mat) masterHtml += `<div class='data-item txt-green'>Mat: ${row.master.mat}</div>`;
           if(row.master.batches) {
               row.master.batches.forEach((b, k) => {
                   if(b) masterHtml += `<div class='data-item'><span class='lbl'>B${k+1}:</span>${b}</div>`;
               });
           }
           masterHtml += "</div>";

           var resText = row.result || ""; 
           var resClass = (resText.indexOf("合格") !== -1) ? "res-ok" : "res-err";
           
           // 【關鍵修改】：只有在 useSchedule 為 true 時才顯示標籤
           var schTag = "";
           if (useSchedule) {
               if (row.inSchedule === true) {
                   schTag = `<div class="sch-ok">📅 排程相符</div>`;
               } else if (row.inSchedule === false) {
                   schTag = `<div class="sch-err">⚠️ 不在排程</div>`;
               }
           }

           html += `<tr>
             <td class="col-id">#${globalIdx}</td>
             <td class="col-info">
                <span class="loc-text">${row.location}</span>
                <span class="date-text">${row.date}<br>${row.time}</span>
             </td>
             <td class="col-mode"><span class="mode-badge ${badgeClass}">${row.mode}</span></td>
             
             <td class="col-tanks">${tankHtml}</td>
             <td class="col-4in1">${masterHtml}</td>
             <td class="col-wh">${whHtml}</td>
             
             <td class="col-res">
                <span class="res-tag ${resClass}">${resText}</span><br>
                ${schTag}
             </td>
           </tr>`;
        });
        tbody.innerHTML = html;
      }

      function changePage(delta) { currentPage += delta; renderTable(); }
    </script>
  </body>
</html>

```
覆蓋儲存後，記得點擊 **「部署 → 建立新版本 → 部署」**。
更新後，只要一按開關，它就會瞬間幫您刷新畫面，紅色的「不在排程」警告就會馬上消失！

## Turn 4

### 👤 User

*[This turn includes uploaded images]*

![上傳圖片預覽](https://lh3.googleusercontent.com/gg/AEir0wIrkmGfHU_1hskZppf6gEPJ0MOjqT8Q90WGREaIU_IFTNsl5I-8gHzNWE1CazUIDRLykk7HSQIDAbyE2B4_158DeErdrVLoqEkV3aq2uYR-ikzptSdR7gjDF-Rk76WGhuGnYHL-ad7EoxrqF_Dw8eHSQfhrvgQUIRafQJ98XX2WfxnDpZC3JdDZz82RVrnu0QEGcCYzQ7m6w3FPxPoCF_gCqUNwgartuJkzrtQOJIp2vgvQksfNOAZZooBs2RYa6j4F0yOEOxoQFiP7EK3Omf-SE1pBjWnT0Xg?authuser=1)

可以讓目前的排程顯示出來，然後做一個清除鍵給人員使用，這樣人員再核對排程批號比較清楚是否有無貼錯出貨日期批號

### 🤖 Assistant

這是一個非常棒的防呆優化！
將目前的排程顯示出來，能讓人員明確知道「現在系統認定要出的是哪些貨」，並且加上「清空」功能，可以避免舊資料殘留導致誤判。
為了讓顯示出來的 Excel 資料更易讀，我特別將文字輸入框設定為 **「不換行且保留對齊（保留 Tab 縮排）」**，這樣它看起來就會像一個小型的表格。
請將您的 **Code.gs** 與 **Query.html** 這兩個檔案完全清空後，貼上以下最新代碼（`Index.html` 維持原樣不需要動）。

---

### 第一步：覆蓋 `Code.gs` (後端新增讀取與清空功能)
請全選並覆蓋 `Code.gs`，我在最下方加入了 `getScheduleRawText` 與 `clearScheduleData` 兩個新函式：

```javascript
// ==========================================
// 1. 網頁入口 (路由控制)
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
        .setTitle('出貨核對系統 (v34.2)')
        .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL)
        .addMetaTag('viewport', 'width=device-width, initial-scale=1');
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
    if (s.toUpperCase().indexOf("T-0") === -1) return "❌ 格式錯誤！\n👉 [7開頭] 需包含 'T-0'";
  }
  if (s.toUpperCase().indexOf("T-0") !== -1 && !s.startsWith("7")) {
    return "❌ 格式錯誤！\n👉 含有 'T-0' 必須以 '7' 開頭";
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
// 3. 主程式 Logic (掃描端完全無排程阻擋)
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

        var fCheck1 = check1SeriesFormat(rawBatch);
        if (fCheck1 !== "OK") allErrors.push('❌ [' + item.name + '] ' + fCheck1);
        var fCheck7 = check7SeriesFormat(rawBatch);
        if (fCheck7 !== "OK") allErrors.push('❌ [' + item.name + '] ' + fCheck7);

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

    var masterMaterial = cleanMatMaster(f[8]); 
    if (!masterMaterial) return { status: 'error', message: '❌ [四合一料號] 為必填項目！' };

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

        var fCheck1 = check1SeriesFormat(tankRawBatch);
        if (fCheck1 !== "OK") allErrors.push('❌ [' + item.name + '] ' + fCheck1);
        var fCheck7 = check7SeriesFormat(tankRawBatch);
        if (fCheck7 !== "OK") allErrors.push('❌ [' + item.name + '] ' + fCheck7);

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

    var cleanWhMat = cleanMatMaster(f[13]); 
    if (cleanWhMat !== masterMaterial) allErrors.push('❌ [繳庫單] 料號異常！');
    
    var whBatch1 = f[14].trim(); 
    var whBatch2 = f[15].trim();
    var whBatch3 = f[16].trim();

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

  if (allErrors.length > 0) return { status: 'error', message: allErrors.join('\n\n') };

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
    return { status: 'error', message: '寫入錯誤: ' + e.toString() };
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
// 6. 排程更新與讀取功能 (包含清空)
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

// 【新增】取得目前的排程文字，顯示在輸入框內
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

// 【新增】清空排程
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

```

---

### 第二步：覆蓋 `Query.html` (查詢介面加入顯示排程與清空按鈕)
請全選並覆蓋 `Query.html`。
這個版本讓輸入框排版更像 Excel (保留欄位對齊)，並加入紅色「清空目前排程」按鈕：

```html
<!DOCTYPE html>
<html>
  <head>
    <base target="_top">
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
      body { font-family: 'Noto Sans TC', sans-serif; background-color: #f8f9fa; margin: 0; padding: 15px; color: #333; }
      .container { width: fit-content; min-width: 100%; margin: 0 auto; background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 1px 5px rgba(0,0,0,0.05); }
      
      .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 1px solid #eee; position: relative; }
      h3 { color: #1a73e8; margin: 0; font-size: 20px; font-weight: 700; display: flex; flex-direction: column; justify-content: center; align-items: center; gap: 10px; width: 100%; text-align: center; }
      
      .top-links { display: flex; gap: 10px; }
      .action-link { font-size: 13px; text-decoration: none; color: #555; font-weight: bold; background: #fff; padding: 8px 15px; border-radius: 20px; white-space: nowrap; border: 1px solid #ddd; cursor: pointer; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
      .action-link:hover { background: #f8f9fa; }
      .link-blue { color: #1a73e8; border-color: #d2e3fc; background: #e8f0fe; }

      @media (min-width: 600px) {
        h3 { flex-direction: row; justify-content: flex-start; text-align: left; width: auto; gap: 10px; }
        .top-links { margin-left: auto; }
      }

      .search-bar { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; background: #fff; padding: 0 0 15px 0; }
      .search-label { font-weight: bold; color: #444; font-size: 13px; margin-right: 2px; }
      .date-input { padding: 5px 8px; border: 1px solid #ccc; border-radius: 4px; font-size: 13px; color: #333; }
      .text-input { flex: 1; padding: 5px 8px; border: 1px solid #ccc; border-radius: 4px; font-size: 13px; min-width: 200px; }
      .btn-search { background-color: #1a73e8; color: white; border: none; padding: 6px 20px; border-radius: 4px; font-size: 13px; font-weight: bold; cursor: pointer; margin-left: auto; }
      .btn-search:hover { background-color: #1557b0; }

      .toggle-switch { display: flex; align-items: center; background: #e8f0fe; padding: 5px 10px; border-radius: 6px; border: 1px solid #d2e3fc; margin-left: 10px; cursor: pointer; }
      .toggle-switch input { margin: 0 5px 0 0; cursor: pointer; width: 14px; height: 14px; }
      .toggle-switch span { font-size: 13px; font-weight: bold; color: #1a73e8; }

      .table-responsive { border: 1px solid #eee; border-radius: 6px; overflow-x: auto; }
      .data-table { width: auto; border-collapse: collapse; font-size: 12px; }
      .data-table th { background-color: #f1f3f4; color: #5f6368; font-weight: bold; text-align: left; padding: 10px 12px; border-bottom: 2px solid #ddd; white-space: nowrap; }
      .data-table td { padding: 8px 12px; border-bottom: 1px solid #f1f3f4; vertical-align: top; color: #3c4043; line-height: 1.4; white-space: nowrap; }
      .data-table tr:hover { background-color: #f8fbff; }

      .col-id    { width: 40px; color: #999; font-weight: bold; text-align: center; }
      .col-info  { width: 100px; } 
      .col-mode  { width: 60px; text-align: center; }
      .col-tanks { width: auto; min-width: 250px; } 
      .col-4in1  { width: auto; min-width: 150px; }   
      .col-wh    { width: auto; min-width: 150px; }   
      .col-res   { width: 140px; text-align: center; } 

      .data-table th.col-id, .data-table th.col-mode, .data-table th.col-res { text-align: center; }

      .loc-text { font-weight: bold; font-size: 13px; color: #202124; display: block; margin-bottom: 2px; }
      .date-text { font-size: 11px; color: #888; }
      .mode-badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; color: #1a73e8; background: #e8f0fe; }
      .mode-badge.az { color: #c5221f; background: #fce8e6; }
      
      .data-list { display: flex; flex-direction: column; gap: 4px; }
      .data-item { font-family: 'Roboto Mono', monospace; font-size: 11.5px; border-bottom: 1px dashed #eee; padding-bottom: 2px; white-space: nowrap; }
      .data-item:last-child { border-bottom: none; }
      
      .lbl { color: #5f6368; font-weight: bold; margin-right: 5px; font-size: 11px; }
      .txt-blue { color: #1a73e8; font-weight: bold; }
      .txt-green { color: #137333; font-weight: bold; }
      .txt-orange { color: #e37400; font-weight: bold; }

      .res-tag { display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; white-space: normal; line-height: 1.2; }
      .res-ok { background-color: #e6f4ea; color: #137333; border: 1px solid #ceead6; }
      .res-err { background-color: #fce8e6; color: #c5221f; border: 1px solid #fad2cf; }
      
      .sch-ok { margin-top:6px; font-size:11px; color:#137333; background:#e6f4ea; padding:3px 6px; border-radius:4px; display:inline-block; border:1px solid #ceead6; width: max-content; }
      .sch-err { margin-top:6px; font-size:11px; color:#c5221f; background:#fce8e6; padding:3px 6px; border-radius:4px; display:inline-block; border:1px solid #fad2cf; width: max-content; }

      #loading { text-align: center; padding: 30px; color: #5f6368; font-size: 14px; display: none; }
      .pagination { display: flex; justify-content: flex-end; align-items: center; gap: 10px; margin-top: 15px; }
      .page-btn { padding: 5px 12px; border: 1px solid #ddd; background: white; border-radius: 4px; cursor: pointer; color: #555; font-size: 12px; }
      .page-btn:disabled { background: #f5f5f5; color: #ccc; cursor: not-allowed; }

      /* --- 更新排程 Modal --- */
      #schedule-modal { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); z-index: 8888; display: none; justify-content: center; align-items: center; }
      .schedule-box { background: white; padding: 20px; border-radius: 12px; width: 95%; max-width: 700px; box-shadow: 0 4px 20px rgba(0,0,0,0.2); white-space: normal; }
      .schedule-box h4 { margin: 0 0 10px 0; color: #1a73e8; }
      .schedule-box p { font-size: 13px; color: #555; margin-bottom: 10px; line-height: 1.5; }
      
      /* 設定讓 Excel 貼上後依然保留排版 */
      .schedule-box textarea { 
        width: 100%; height: 350px; border: 2px dashed #ccc; border-radius: 8px; 
        padding: 10px; font-size: 12px; box-sizing: border-box; resize: none; 
        white-space: pre; overflow-wrap: normal; overflow-x: auto; font-family: monospace;
      }
      .schedule-box textarea:focus { border-color: #1a73e8; outline: none; }
      
      .modal-btns { display: flex; justify-content: space-between; align-items: center; margin-top: 15px; }
      .btn-cancel { padding: 8px 15px; border: none; background: #eee; color: #333; border-radius: 6px; cursor: pointer; font-weight: bold; }
      .btn-save { padding: 8px 20px; border: none; background: #1a73e8; color: white; border-radius: 6px; cursor: pointer; font-weight: bold; }
      .btn-save:hover { background: #1557b0; }
      .btn-clear-data { padding: 8px 15px; border: none; background: #fce8e6; color: #c5221f; border-radius: 6px; cursor: pointer; font-weight: bold; }
      .btn-clear-data:hover { background: #fad2cf; }
    </style>
  </head>
  <body>
    <div id="schedule-modal">
        <div class="schedule-box">
            <h4>📅 出貨排程管理</h4>
            <p>目前系統內的排程資料如下。您可以核對是否正確，或直接「全選並貼上」新的 Excel 資料來覆蓋它。</p>
            <textarea id="schedule-data" placeholder="載入中...或請在此貼上 Excel 資料..."></textarea>
            
            <div class="modal-btns">
                <button class="btn-clear-data" onclick="clearSchedule()" id="btn-clear-schedule">🗑️ 清空目前排程</button>
                
                <div style="display: flex; gap: 10px;">
                    <button class="btn-cancel" onclick="closeScheduleModal()">取消</button>
                    <button class="btn-save" onclick="submitSchedule()" id="btn-submit-schedule">💾 覆蓋儲存</button>
                </div>
            </div>
        </div>
    </div>

    <div class="container">
      <div class="header">
        <h3>
          <span>📊 出貨紀錄查詢</span>
          <div class="top-links">
             <button class="action-link link-blue" onclick="openScheduleModal()">📅 更新排程</button>
             <button class="action-link" onclick="goHome()">← 返回掃描頁</button>
          </div>
        </h3>
      </div>

      <div class="search-bar">
        <span class="search-label">日期範圍 :</span>
        <input type="date" id="dateStart" class="date-input">
        <span style="color:#999">~</span>
        <input type="date" id="dateEnd" class="date-input">
        <span class="search-label" style="margin-left: 15px;">搜尋 :</span>
        <input type="text" id="batchInput" class="text-input" placeholder="輸入外箱條碼或批號...">
        
        <label class="toggle-switch">
          <input type="checkbox" id="checkScheduleToggle" checked onchange="doSearch()">
          <span>🛡️ 啟用排程核對</span>
        </label>

        <button class="btn-search" onclick="doSearch()">查詢</button>
      </div>

      <div id="loading">⏳ 資料搜尋中...</div>
      
      <div class="table-responsive">
        <table class="data-table">
          <thead>
            <tr>
              <th class="col-id">ID</th>
              <th class="col-info">時間 / 場所</th>
              <th class="col-mode">模式</th>
              <th class="col-tanks">桶槽作業紀錄 (1~4)</th>
              <th class="col-4in1">4合1 紀錄</th>
              <th class="col-wh">外箱條碼 / 料號</th> 
              <th class="col-res">判定結果</th>
            </tr>
          </thead>
          <tbody id="tableBody"></tbody>
        </table>
      </div>

      <div class="pagination" id="paginationControl" style="visibility:hidden;">
        <button class="page-btn" id="btnPrev" onclick="changePage(-1)">上一頁</button>
        <span id="pageInfo" style="font-size:13px; font-weight:bold; color:#5f6368;">第 1 頁</span>
        <button class="page-btn" id="btnNext" onclick="changePage(1)">下一頁</button>
      </div>
    </div>

    <script>
      var allData = [];
      var currentPage = 1;
      var pageSize = 20;

      window.onload = function() {
        var today = new Date().toISOString().split('T')[0];
        var lastWeek = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
        document.getElementById('dateStart').value = lastWeek;
        document.getElementById('dateEnd').value = today;
      };

      function goHome() {
         google.script.run.withSuccessHandler(function(url){
             window.top.location.href = url.split('?')[0]; 
         }).getScriptUrl();
      }

      // 打開視窗時：讀取目前排程顯示出來
      function openScheduleModal() {
          document.getElementById('schedule-modal').style.display = 'flex';
          var ta = document.getElementById('schedule-data');
          ta.value = "⏳ 正在讀取目前的排程資料，請稍候...";
          ta.disabled = true;

          google.script.run
            .withSuccessHandler(function(text) {
                ta.disabled = false;
                ta.value = text;
                ta.focus();
            })
            .withFailureHandler(function(err) {
                ta.disabled = false;
                ta.value = "";
                alert("讀取排程失敗：" + err);
            })
            .getScheduleRawText();
      }

      function closeScheduleModal() {
          document.getElementById('schedule-modal').style.display = 'none';
      }

      function submitSchedule() {
          var tsvData = document.getElementById('schedule-data').value.trim();
          if(tsvData === "") {
              alert("請先貼上資料！如果想清空排程，請使用左下角的「清空目前排程」按鈕。"); 
              return;
          }
          
          var btn = document.getElementById('btn-submit-schedule');
          btn.innerText = "⏳ 儲存中...";
          btn.disabled = true;

          google.script.run
            .withSuccessHandler(function(res) {
                alert(res.msg);
                if(res.success) {
                   closeScheduleModal();
                   doSearch(); 
                }
                btn.innerText = "💾 覆蓋儲存";
                btn.disabled = false;
            })
            .withFailureHandler(function(err) {
                alert("伺服器錯誤：" + err);
                btn.innerText = "💾 覆蓋儲存";
                btn.disabled = false;
            })
            .updateScheduleData(tsvData);
      }

      // 新增：清空排程邏輯
      function clearSchedule() {
          if(!confirm("確定要清空目前的排程資料嗎？\n(清空後，所有啟用了核對的歷史紀錄都會顯示「不在排程」)")) return;
          
          var btn = document.getElementById('btn-clear-schedule');
          btn.innerText = "⏳ 清空中...";
          btn.disabled = true;

          google.script.run
            .withSuccessHandler(function(res) {
                alert(res.msg);
                if(res.success) {
                   document.getElementById('schedule-data').value = "";
                   closeScheduleModal();
                   doSearch(); 
                }
                btn.innerText = "🗑️ 清空目前排程";
                btn.disabled = false;
            })
            .withFailureHandler(function(err) {
                alert("伺服器錯誤：" + err);
                btn.innerText = "🗑️ 清空目前排程";
                btn.disabled = false;
            })
            .clearScheduleData();
      }

      function doSearch() {
        var ds = document.getElementById('dateStart').value;
        var de = document.getElementById('dateEnd').value;
        var kw = document.getElementById('batchInput').value.trim();
        var useSchedule = document.getElementById('checkScheduleToggle').checked; 
        
        document.getElementById('loading').style.display = 'block';
        document.getElementById('tableBody').innerHTML = '';
        document.getElementById('paginationControl').style.visibility = 'hidden';

        google.script.run
          .withSuccessHandler(function(data) {
             allData = data;
             currentPage = 1;
             renderTable();
             document.getElementById('loading').style.display = 'none';
             document.getElementById('paginationControl').style.visibility = (allData.length > 0) ? 'visible' : 'hidden';
          })
          .withFailureHandler(function(e){ 
             alert("查詢錯誤: " + e); 
             document.getElementById('loading').style.display = 'none'; 
          })
          .searchRecords(ds, de, kw, useSchedule); 
      }

      function renderTable() {
        var tbody = document.getElementById('tableBody');
        tbody.innerHTML = "";
        
        if (!allData || allData.length === 0) {
          tbody.innerHTML = "<tr><td colspan='7' style='text-align:center; padding:30px; color:#888;'>查無資料</td></tr>";
          return;
        }

        var startIdx = (currentPage - 1) * pageSize;
        var endIdx = Math.min(startIdx + pageSize, allData.length);
        var pageData = allData.slice(startIdx, endIdx);

        document.getElementById('pageInfo').innerText = "第 " + currentPage + " 頁 / 共 " + Math.ceil(allData.length / pageSize) + " 頁";
        document.getElementById('btnPrev').disabled = (currentPage === 1);
        document.getElementById('btnNext').disabled = (endIdx >= allData.length);

        var useSchedule = document.getElementById('checkScheduleToggle').checked;

        var html = "";
        pageData.forEach(function(row, index) {
           var globalIdx = allData.length - (startIdx + index); 
           var badgeClass = (row.mode.indexOf("AZ") !== -1) ? "az" : "";

           var whHtml = "<div class='data-list'>";
           if(row.wh.mat) whHtml += `<div class='data-item txt-orange'>Mat: ${row.wh.mat}</div>`;
           if(row.wh.batches) {
               row.wh.batches.forEach((b, k) => {
                   if(b) whHtml += `<div class='data-item'><span class='lbl'>W${k+1}:</span>${b}</div>`;
               });
           }
           whHtml += "</div>";

           var tankHtml = "<div class='data-list'>";
           for(var i=0; i<4; i++) {
               if(row.tanks[i].batch || row.tanks[i].mat) {
                   tankHtml += `<div class='data-item'><span class='lbl'>T${i+1}:</span>${row.tanks[i].batch} <span class='lbl' style='margin-left:5px;color:#1a73e8'>${row.tanks[i].mat}</span></div>`;
               }
           }
           tankHtml += "</div>";

           var masterHtml = "<div class='data-list'>";
           if(row.master.mat) masterHtml += `<div class='data-item txt-green'>Mat: ${row.master.mat}</div>`;
           if(row.master.batches) {
               row.master.batches.forEach((b, k) => {
                   if(b) masterHtml += `<div class='data-item'><span class='lbl'>B${k+1}:</span>${b}</div>`;
               });
           }
           masterHtml += "</div>";

           var resText = row.result || ""; 
           var resClass = (resText.indexOf("合格") !== -1) ? "res-ok" : "res-err";
           
           var schTag = "";
           if (useSchedule) {
               if (row.inSchedule === true) {
                   schTag = `<div class="sch-ok">📅 排程相符</div>`;
               } else if (row.inSchedule === false) {
                   schTag = `<div class="sch-err">⚠️ 不在排程</div>`;
               }
           }

           html += `<tr>
             <td class="col-id">#${globalIdx}</td>
             <td class="col-info">
                <span class="loc-text">${row.location}</span>
                <span class="date-text">${row.date}<br>${row.time}</span>
             </td>
             <td class="col-mode"><span class="mode-badge ${badgeClass}">${row.mode}</span></td>
             
             <td class="col-tanks">${tankHtml}</td>
             <td class="col-4in1">${masterHtml}</td>
             <td class="col-wh">${whHtml}</td>
             
             <td class="col-res">
                <span class="res-tag ${resClass}">${resText}</span><br>
                ${schTag}
             </td>
           </tr>`;
        });
        tbody.innerHTML = html;
      }

      function changePage(delta) { currentPage += delta; renderTable(); }
    </script>
  </body>
</html>

```
修改完畢後，請記得點擊右上方藍色按鈕：**「部署」 →「管理部署作業」 → 點擊「編輯（✏️）」 → 版本選擇「建立新版本」 →「部署」**。
現在點開「更新排程」，它會自動去試算表中抓取目前的資料，並且對齊整齊呈現，人員可以一眼看出是不是有貼錯，要重來也只要點一下紅色垃圾桶就可以了！

## Turn 5

### 👤 User

*[This turn includes uploaded images]*

![上傳圖片預覽](https://lh3.googleusercontent.com/gg/AEir0wITGCSCr-6xQRg8R88agKQ-tjrN7dPLNcPR2uEIXIuHebLkrs-3HM_nSjfh2Ze5qx15yPi2nq8xMaI9f3MFjuiGkxm30ZUH8R3TXc4DCF4fmOmokwC7TqxjfE9krocfz97-l0pEHXOlQBg8QLkvFmCLcxld9CJIF-BTinGs8eyK7gvmDiuGLnNuZt2kB_WxA0a8uKVCuC7YwaEu_RKqoSm_Qli5KnylqKi0gQD4iI_LZUV2oLTwYEyxd-0s5emwwNwIcLZqL71mSsRbRd3egsUaRHBTZ2dJNFo?authuser=1)

7L1400241-T02 00000000TS ，此四合一料號 7開頭應為29碼但我故意少於29碼系統還是沒檢查出來

### 🤖 Assistant

我完全了解問題出在哪裡了！
您點出了一個非常關鍵的漏洞：目前的系統邏輯中，`1開頭需20碼` 與 `7開頭需29碼` 的嚴格格式檢查，**只被套用在「現場作業桶槽的批號」上**，而**漏掉了「四合一料號」以及「繳庫料號」等欄位**。
因此，當您在「四合一料號」掃描了長度只有 24 碼的 `7L1400241-T02 00000000TS` 時，系統並沒有執行長度攔截，直接讓它過關了。
為了一勞永逸地解決這個問題，我寫了一個統一的檢查機制 `validate17Series`，並**強制套用到所有會被掃描的欄位**（包含桶槽料號、四合一料號、四合一批號、繳庫單等）。只要有任何一格掃出來的條碼是 1 或 7 開頭，就必須絕對服從長度規定！
請將您的 **Code.gs** 全選並覆蓋為下方的 **v34.3 (全面防呆升級版)**（`Index.html` 和 `Query.html` 維持原樣即可）：

### Code.gs (v34.3 全面欄位格式防呆版)

```javascript
// ==========================================
// 1. 網頁入口 (路由控制)
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
        .setTitle('出貨核對系統 (v34.3)')
        .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL)
        .addMetaTag('viewport', 'width=device-width, initial-scale=1');
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
    if (s.toUpperCase().indexOf("T-0") === -1) return "❌ 格式錯誤！\n👉 [7開頭] 需包含 'T-0'";
  }
  if (s.toUpperCase().indexOf("T-0") !== -1 && !s.startsWith("7")) {
    return "❌ 格式錯誤！\n👉 含有 'T-0' 必須以 '7' 開頭";
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

// 【新增】統一驗證輔助函式：確保任何欄位只要有值，就套用 1/7 系列檢查
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
// 3. 主程式 Logic (全面格式防呆)
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

        // 【修改】使用統一驗證函式檢查批號與料號
        validate17Series(rawBatch, item.name + ' 批號', allErrors);
        validate17Series(rawMat, item.name + ' 料號', allErrors);

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
    if (!masterMaterial) {
        return { status: 'error', message: '❌ [四合一料號] 為必填項目！' };
    }
    
    // 【關鍵新增】對「四合一料號」執行 1/7 系列長度檢查
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

        // 【修改】全面檢查現場輸入的批號與料號
        validate17Series(tankRawBatch, item.name + ' 批號', allErrors);
        validate17Series(tankInputMat, item.name + ' 料號', allErrors);
        validate17Series(masterBatchVal, '四合一單據 (對應' + item.name + ')', allErrors);

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
    
    // 【新增】檢查繳庫單料號
    validate17Series(rawWhMat, '繳庫單料號', allErrors);
    if (cleanWhMat !== masterMaterial) allErrors.push('❌ [繳庫單] 料號異常！');
    
    var whBatch1 = f[14].trim(); 
    var whBatch2 = f[15].trim();
    var whBatch3 = f[16].trim();

    // 【新增】檢查繳庫單批號
    validate17Series(whBatch1, '繳庫批號1', allErrors);
    validate17Series(whBatch2, '繳庫批號2', allErrors);
    validate17Series(whBatch3, '繳庫批號3', allErrors);

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

  if (allErrors.length > 0) return { status: 'error', message: allErrors.join('\n\n') };

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
    return { status: 'error', message: '寫入錯誤: ' + e.toString() };
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

```
修改完畢後，請記得點擊 **「部署」 →「管理部署作業」 → 點擊「編輯（✏️）」 → 建立新版本 →「部署」**。這樣一來，不管人員將 `7L...` 或 `1L...` 掃描到哪個欄位，只要長度不對，系統都會立刻無情地彈出紅字阻擋！

## Turn 6

### 👤 User

*[This turn includes uploaded images]*

![上傳圖片預覽](https://lh3.googleusercontent.com/gg/AEir0wIzhvHjj69hRedqAXLGa0HzUvOzj_vtezay0QTF13AI4hZpLNoI2f7c67d9Fx51W-yNqJwxTfR672tkP4md14HkpyBhnowX5wPuU21IQ1AXTD9de-iZrsWNlVR8S11D2_rYJ01eZkR3yO1oFElH-pP6MDojh3kopooWdBMn1C2Tp9EYF3126T1sMBoaemybcqOx1KSkECjlgbVLyHZ0c6I9s9KbBvHWD5_yuhG1GDieV7BulW0cGdHiAQeTB8UKoi9xL3oN32JwpOUIFDuHwq0i8nKEzw2w6g?authuser=1)

只有四合一那個欄位需29碼 ，桶子上的料號目前沒有特別限定長度規則，但可以幫我標註起來讓我之後可以自行增設

### 🤖 Assistant

完全明白！從您提供的截圖可以看到，因為 `7L1400241-T02` 這個「桶子料號」只有 13 碼，卻被系統誤認為是 7 開頭必須 29 碼，導致全部亮紅燈報錯。
這確實是我的疏忽，防呆機制開得太廣了。我們現在把規則精確調整為：

1. **「四合一料號」**：嚴格執行 1 字頭 20 碼 / 7 字頭 29 碼的檢查（如您所願，少一碼都不行）。
2. **「桶槽批號」**：維持原有的嚴格檢查。
3. **「桶槽料號」與其他欄位**：**暫不檢查長度**。
4. **未來擴充標註**：我已經在程式碼中為您設立了 **// 【未來擴充區】** 的標記。如果您之後想把桶子料號也納入長度管制，只要把前方的 `//` 刪掉就可以了，非常方便！
請將您的 **Code.gs** 全選並覆蓋為以下版本 (v34.4)。
*(註：Index.html 與 Query.html 維持原樣，不需修改)*

### Code.gs (v34.4 精準防呆與未來擴充版)

```javascript
// ==========================================
// 1. 網頁入口 (路由控制)
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
        .setTitle('出貨核對系統 (v34.4)')
        .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL)
        .addMetaTag('viewport', 'width=device-width, initial-scale=1');
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
    if (s.toUpperCase().indexOf("T-0") === -1) return "❌ 格式錯誤！\n👉 [7開頭] 需包含 'T-0'";
  }
  if (s.toUpperCase().indexOf("T-0") !== -1 && !s.startsWith("7")) {
    return "❌ 格式錯誤！\n👉 含有 'T-0' 必須以 '7' 開頭";
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

// 【共用驗證函式】
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
        
        // 【未來擴充區】若未來「AZ 桶料號」也需要檢查 1/7 系列長度，請把下方這行的「//」刪除：
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
        
        // 【未來擴充區】若未來「現場桶槽料號」需要檢查長度，請把下方這行的「//」刪除：
        // validate17Series(tankInputMat, item.name + ' 料號', allErrors);

        // 【未來擴充區】若未來「四合一對應的批號」需要檢查長度，請把下方這行的「//」刪除：
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
    
    // 【未來擴充區】若未來「繳庫單料號」需要檢查長度，請把下方這行的「//」刪除：
    // validate17Series(rawWhMat, '繳庫單料號', allErrors);
    
    if (cleanWhMat !== masterMaterial) allErrors.push('❌ [繳庫單] 料號異常！');
    
    var whBatch1 = f[14].trim(); 
    var whBatch2 = f[15].trim();
    var whBatch3 = f[16].trim();

    // 【未來擴充區】若未來「繳庫單批號」需要檢查長度，請把下方這幾行的「//」刪除：
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

  if (allErrors.length > 0) return { status: 'error', message: allErrors.join('\n\n') };

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
    return { status: 'error', message: '寫入錯誤: ' + e.toString() };
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

```

## Turn 7

### 👤 User

幫我重新調整未來擴充區 程式後面要備註是怎麼檢查未來我在修改比較了解

### 🤖 Assistant

沒問題！為了讓您未來在維護與修改時能一目了然，我把 `Code.gs` 裡面的 **【未來擴充區】** 註解寫得更詳細了。
現在每一塊擴充區上面，都會清楚寫明：

1. **這個檢查是針對什麼欄位**。
2. **它的檢查邏輯是什麼**（例如：1開頭限制20碼、7開頭限制29碼）。
3. **未來要怎麼啟用它**（刪除 `//` 即可）。
請將您的 **Code.gs** 全選並覆蓋為下方的 **v34.5 (註解優化版)**（前端的 `Index.html` 和 `Query.html` 維持原樣不需要動）：

### Code.gs (v34.5 註解優化版)

```javascript
// ==========================================
// 1. 網頁入口 (路由控制)
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
        .setTitle('出貨核對系統 (v34.5)')
        .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL)
        .addMetaTag('viewport', 'width=device-width, initial-scale=1');
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
    if (s.toUpperCase().indexOf("T-0") === -1) return "❌ 格式錯誤！\n👉 [7開頭] 需包含 'T-0'";
  }
  if (s.toUpperCase().indexOf("T-0") !== -1 && !s.startsWith("7")) {
    return "❌ 格式錯誤！\n👉 含有 'T-0' 必須以 '7' 開頭";
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
        //          若值為「7開頭」，強制要求 29 碼且包含 T-0。
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
    
    // 【重點】四合一料號：已強制啟用 1/7 系列長度檢查
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
        //          若值為「7開頭」，強制要求 29 碼且包含 T-0。
        // 啟用方法：刪除下方這行最前面的「//」符號。
        // ==========================================
        // validate17Series(tankInputMat, item.name + ' 料號', allErrors);

        // ==========================================
        // 【未來擴充區：四合一對應批號 檢查】
        // 檢查邏輯：針對「四合一單據上對應各桶的批號」
        //          若值為「1開頭」，強制要求 20 碼且結尾為 TS。
        //          若值為「7開頭」，強制要求 29 碼且包含 T-0。
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
    //          若值為「7開頭」，強制要求 29 碼且包含 T-0。
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
    //          若值為「7開頭」，強制要求 29 碼且包含 T-0。
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

  if (allErrors.length > 0) return { status: 'error', message: allErrors.join('\n\n') };

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
    return { status: 'error', message: '寫入錯誤: ' + e.toString() };
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

```

## Turn 8

### 👤 User

T-0 這個我當初打錯了 是-T0 檢查才對

### 🤖 Assistant

沒問題！這是一個很重要的小細節，我已經將檢查邏輯從 `T-0` 修正為 **-T0**，同時也把未來擴充區的註解文字一併更新了。
請將您的 **Code.gs** 全選並覆蓋為下方的 **v34.6 (-T0 修正版)**（前端的 `Index.html` 和 `Query.html` 維持原樣即可）：

### Code.gs (v34.6)

```javascript
// ==========================================
// 1. 網頁入口 (路由控制)
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

  if (allErrors.length > 0) return { status: 'error', message: allErrors.join('\n\n') };

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
    return { status: 'error', message: '寫入錯誤: ' + e.toString() };
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

```

## Turn 9

### 👤 User

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
這段與
/ 【共用驗證函式：專門用來執行 1/7 開頭的長度檢查】
function validate17Series(val, label, errors) {
if (!val || String(val).trim() === "") return;
var c1 = check1SeriesFormat(val);
if (c1 !== "OK") errors.push('❌ [' + label + '] ' + c1);
var c7 = check7SeriesFormat(val);
if (c7 !== "OK") errors.push('❌ [' + label + '] ' + c7);
}
差異在那

### 🤖 Assistant

這兩段程式碼其實是「分工合作」**的關係，可以把它們想像成**「制定規則的法官」**與**「執行臨檢的警察」。
它們的差異與各自的功用如下：

### 1. `check7SeriesFormat` 與 `check1SeriesFormat` (底層規則 / 法官)
這兩個函式是**純粹的判斷邏輯**。它們不關心這個條碼是從「桶槽」掃來的還是從「四合一單據」掃來的，它們只做一件事：**檢驗字串是否符合硬性規定**。

- **輸入**：只吃一段字串 (`code`)。
- **輸出**：如果正確，回傳 `"OK"`；如果錯誤，回傳一段單純的錯誤原因（例如 `"❌ 格式錯誤！👉 [1開頭] 長度需 20 碼..."`）。
- **特點**：因為它們很單純，所以非常好維護。未來如果 T100 系統改了規定（例如 1 開頭變成要 22 碼），只要改這裡就好。

### 2. `validate17Series` (共用驗證函式 / 警察)
這個函式是**整合執行器**。因為我們的系統有很多欄位（桶1、桶2、四合一、繳庫單...）都需要做這兩項檢查，如果每個欄位都要寫兩次 `if...else`，程式碼會變得超級長又容易出錯。

- **輸入**：
  1. `val`: 掃描到的值（例如 `1L1400241`）。
  2. `label`: 欄位名稱（例如 `'四合一料號'`），用來告訴使用者是哪裡掃錯了。
  3. `errors`: 收集所有錯誤的大陣列。
- **運作流程**：
  1. **過濾空白**：如果欄位沒填東西，直接跳過 (`return`)，不檢查。
  2. **呼叫法官 A**：把值丟給 `check1SeriesFormat`。如果法官說不合格，它就把「欄位名稱 + 錯誤原因」打包起來，丟進系統的錯誤清單 (`errors.push`)。
  3. **呼叫法官 B**：把值丟給 `check7SeriesFormat`，做一樣的動作。

---

### 💡 舉個實際的例子
假設人員在「四合一料號」掃描了長度只有 13 碼的 `1L1400241-T02`：

1. 主程式呼叫：`validate17Series('1L1400241-T02', '四合一料號', allErrors)`
2. `validate17Series` 拿著這個值去問 `check1SeriesFormat`。
3. `check1SeriesFormat` 發現它開頭是 1，但長度不對，也沒有 TS 結尾，於是退回字串：`"❌ 格式錯誤！👉 [1開頭] 長度需 20 碼..."`
4. `validate17Series` 收到退件，幫它掛上名牌，塞進錯誤清單：
`"❌ [四合一料號] ❌ 格式錯誤！👉 [1開頭] 長度需 20 碼..."`
**總結來說：**`check...` 是定義「什麼是錯的」；而 `validate17Series` 是為了讓主程式變乾淨，幫您自動把值丟去檢查，並清楚標示「是哪個欄位發生了這個錯誤」。這是一種「模組化」的寫法，未來若要增加「9開頭」的規則，只要再寫一個 `check9`，然後加進 `validate17Series` 裡就全部套用了！

## Turn 10

### 👤 User

幫我把所有檢查核對相關的列個清單，讓我後續修bag比較清梵楚

### 🤖 Assistant

為了方便您後續進行維護或除錯（Debug），我將系統目前（v34.6 版本）所有核心的檢查與核對邏輯整理成這份清單。您可以將其視為系統的「邏輯藍圖」。

---

### 一、 條碼格式硬性規定 (底層規則)
這是系統最基礎的檢查，定義在 `check...Format` 函式中。

1. **7 字頭條碼規則**：
  - 開頭若為 `7`，長度必須**剛好 29 碼**。
  - 開頭若為 `7`，內容必須包含 **-T0**。
  - 若內容包含 `-T0`，開頭必須是 `7`。
2. **1 字頭條碼規則**：
  - 開頭若為 `1`，長度必須**剛好 20 碼**。
  - 開頭若為 `1`，結尾必須是 **TS**。
3. **通用驗證執行器 (validate17Series)**：
  - 負責將上述 1/7 規則套用到指定欄位，並加上「[欄位名稱]」作為標籤，以便在畫面上顯示是哪一格出錯。

---

### 二、 欄位與格式檢查清單 (掃描存檔時)
當人員按下「🚀 巡檢核對並存檔」時，系統會依序檢查以下項目：

#### 1. 所有模式共通檢查

- **1/7 系列長度檢查**：
  - **桶槽批號**：強制檢查 (1開頭20碼 / 7開頭29碼)。
  - **四合一料號**：強制檢查 (1開頭20碼 / 7開頭29碼)。
- **重複掃描檢查**：確保「桶1」到「桶4」掃描到的批號不重複。
- **料號一致性**：確保所有現場桶子的「料號」都與「第一桶」或「四合一單據」一致。
- **QR 內碼核對**：若批號是 QR Code（含 `@`），系統會提取裡面的料號，檢查是否與人員手動掃描的料號貼紙相符。

#### 2. 一般模式 (整板 / 混板 / 散桶) 專屬檢查

- **四合一料號必填**：沒掃四合一料號不能存檔。
- **四合一與現場批號比對**：
  - 使用 `verifyPairStrict` 進行深度比對。
  - 處理 QR Code 標籤的特殊去碼邏輯（去首碼、去 `+` 號、去空白）。
- **數量異常檢查**：檢查「現場桶數」是否與「四合一單據上的批號筆數」相等。
- **整板模式限制**：檢查 4 桶批號的「主體（Base）」是否完全相同（不准混批）。
- **繳庫單核對**：
  - 繳庫單料號需與四合一一致。
  - 繳庫單批號必須包含在現場掃描的桶子中（支援 `2` 字頭補位比對）。
  - 檢查是否有漏打：現場掃到的所有批號都必須出現在繳庫單上。

#### 3. AZ 模式專屬檢查

- **長度異常檢查**：
  - 比較各桶條碼的原始長度。
  - 若第一桶與其他桶長度落差大於 10 碼（例如重複掃描導致長度加倍），系統會攔截報錯。

---

### 三、 查詢端：排程交叉核對 (查詢紀錄時)
當人員在查詢頁面啟用「🛡️ 啟用排程核對」時：

1. **排程資料載入**：系統讀取「出貨排程」分頁所有內容，並清理出批號清單。
2. **批號比對**：
  - **AZ 模式**：取第一桶批號。
  - **一般模式**：取「繳庫批號1」（若無則取桶1）。
3. **模糊搜尋**：
  - 處理 `2` 字頭差異。
  - 檢查該批號是否存在於排程 Excel 貼上的任何一格中。
4. **結果標籤**：吻合顯示「📅 排程相符」；找不到則顯示「⚠️ 不在排程」。

---

### 四、 未來擴充區 (Code.gs 內部備註)
為了讓您之後方便修改，我在代碼中標記了幾個區域：

- **AZ 桶料號 檢查**：目前未啟用長度限制。若要規範，刪除前方的 `//`。
- **現場桶槽料號 檢查**：一般模式下的桶子料號，目前未啟用 1/7 系列長度限制。
- **四合一對應批號 檢查**：針對單據上的批號欄位，目前未啟用 1/7 系列長度限制。
- **繳庫單料號/批號 檢查**：目前未啟用長度限制，僅做內容一致性比對。

---

### 五、 除錯建議 (Troubleshooting Tips)

- **如果長度對卻報格式錯誤**：檢查條碼中是否含有隱形的換行符號或空格（系統已做 `.trim()` 處理，但若在中間則會失敗）。
- **如果排程比對不到**：請檢查「出貨排程」分頁是否正確貼上，且該批號在 Excel 裡沒有被系統截斷（例如變成科學記號 `2.6E+10`）。
- **如果標籤不消失**：確保 `Query.html` 已更新至具有 `onchange="doSearch()"` 連動功能的版本。
這份清單可以幫助您在未來需要調整規則（例如更改長度、新增開關）時，快速找到對應的程式碼區段。

## Turn 11

### 👤 User

整理成md檔

### 🤖 Assistant

```python
markdown_content = """# N系列BARCODE出貨作業檢點系統 (v34.6) 規格說明書

## 摘要
本系統是一款基於 **Google Apps Script (GAS)** 開發的行動化 Web App，專為現場出貨作業設計。系統核心目標是透過條碼掃描與自動化邏輯，即時核對「現場桶槽」、「四合一單據」與「繳庫單」三者資訊的一致性，並結合「出貨排程」進行雙重驗證，將人為疏失（如拿錯批號、掃錯欄位）降至最低。

## 內容

### 1. 核心驗證規則 (底層法官)
系統對特定字頭條碼執行硬性格式檢查：
* **7 系列條碼**：
    * 開頭字元：必須為 `7`。
    * 總長度：必須剛好為 **29 碼**。
    * 必要字串：內容必須包含 **`-T0`**。
* **1 系列條碼**：
    * 開頭字元：必須為 `1`。
    * 總長度：必須剛好為 **20 碼**。
    * 結尾字元：必須以 **`TS`** 結尾。

### 2. 作業模式說明
* **整板出貨**：強制檢查 4 桶批號是否為主體一致（不准混批）。
* **混板出貨**：允許 4 桶批號不同，但須與單據一一對應。
* **散桶模式**：可自由選擇 1~3 桶數量進行核對。
* **AZ 檢查**：簡化模式，不核對單據，僅檢查 4 桶間的批號一致性與條碼長度異常（防重複掃描）。

### 3. 主要功能模組
* **掃描介面 (Index)**：
    * 響應式設計，支援手機與 PC 瀏覽。
    * 場所記憶：預設「崙尾一廠」，並自動記憶使用者最後選擇。
    * 智能跳格：掃描完成後自動聚焦下一個輸入框。
* **查詢中心 (Query)**：
    * 資料密度優化：表格採用不換行（No Wrap）設計。
    * 排程管理：提供管理人員直接貼上 T100 Excel 資料的功能。
    * 交叉核對：查詢時自動將歷史紀錄與目前排程比對，標註「📅 排程相符」或「⚠️ 不在排程」。
    * 核對開關：可隨時關閉排程比對標籤，僅看原始合格狀態。

## 重點整理
* **模組化驗證**：採用 `validate17Series` 函式統一管理所有欄位的格式檢查。
* **高精準度防呆**：針對「四合一料號」執行最嚴格的 29 碼/20 碼過濾。
* **排程靈活性**：支援貼上「近期排程」（含明日資料），解決提前備貨的核對問題。
* **自動化儲存**：資料依雙月（如 2026-05~06）自動分流至不同的 Google Sheet 工作表，方便管理。

## TODO
* **擴充桶槽料號檢查**：目前桶槽料號未限制 1/7 系列長度，未來可於 `Code.gs` 擴充區啟用。
* **四合一對應批號驗證**：若需對單據上的批號欄位也執行長度管制，已有預留區塊。
* **繳庫單細節強化**：未來可考慮將繳庫單的批號也納入 1/7 系列長度限制。

## 結論
目前系統已更新至 **v34.6 穩定版**，解決了 AZ 模式欄位錯位、查詢頁標記殘留、四合一料號長度漏查以及 -T0 關鍵字誤植等 Bug。系統具備高度的防呆性能，並能適應現場提前備貨的作業流程。
"""

with open("2026-05-10-Barcode-Shipment-Verification-System.md", "w", encoding="utf-8") as f:
    f.write(markdown_content)

```
為您整理的 Markdown 檔案已經準備好了！![「MD」圖示](assets/img-001.png) 2026-05-10...ion-System MD
這份文件記錄了目前 v34.6 版本的核心功能、規則、重點與未來可以擴充的 TODO 事項，方便您後續維護或交接時參考。如果有需要調整標題或內容的地方，請隨時告訴我！

---

*Exported from [Gemini Voyager](https://github.com/Nagi-ovo/gemini-voyager)*  
*Generated on May 10, 2026 at 07:48 PM*