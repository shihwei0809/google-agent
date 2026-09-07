// =====================================================================
// ⚠️ 重要架構區隔說明：
// 本檔案為【N系列現場作業檢點 - 入庫核對系統】(Receiving & Inspection)
// 負責：箱標籤效期檢驗、現場桶槽進廠檢點、AZ出貨地卡控、批號/效期一致性比對。
// 嚴格禁止：請勿將本檔案邏輯與「N系列出貨核對系統」(Shipping Verification) 混淆！
// =====================================================================

// ==========================================
// Google Apps Script v51.1 (相容20碼舊庫存與24碼新標籤雙軌版)
// ==========================================

function doGet(e) {
  if (e.parameter && e.parameter.page == 'query') {
    return HtmlService.createHtmlOutputFromFile('Query')
        .setTitle('N系列現場作業紀錄查詢系統(入庫檢點)')
        .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL)
        .addMetaTag('viewport', 'width=device-width, initial-scale=1');
  }
  return HtmlService.createHtmlOutputFromFile('Index')
      .setTitle('N系列BARCODE現場作業檢點-入庫 (v51.1)')
      .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL)
      .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

function getScriptUrl() { return ScriptApp.getService().getUrl(); }

// --- 輔助函式庫 ---
function toStr(val) { return (val === null || val === undefined) ? "" : val.toString(); }
function toHalfWidth(str) { return toStr(str).replace(/[\uff01-\uff5e]/g, function(ch) { return String.fromCharCode(ch.charCodeAt(0) - 0xfee0); }).replace(/\u3000/g, ' '); }
function normalizeBatch(str) { return toHalfWidth(str).replace(/[^a-zA-Z0-9]/g, ''); }
function extractRealBatch(fullString) { var s = toStr(fullString); if (s.indexOf('@') !== -1 && s.indexOf('+') !== -1) { var parts = s.split('@'); if (parts.length > 1) return parts[1]; } return s; }
function extractRealMat(fullString) { var s = toStr(fullString); if (s.indexOf('@') !== -1) { var parts = s.split('@'); return parts[0].length > 14 ? parts[0].substring(14) : parts[0]; } return s; }
function cleanMatMaster(str) { return toStr(str).trim().split(/\s+/)[0]; }
function isSameDay(d1, d2) { return d1.getFullYear() === d2.getFullYear() && d1.getMonth() === d2.getMonth() && d1.getDate() === d2.getDate(); }

// 日期處理與效期推算
function decodeBatchDate(batchStr) {
  var cleanBatch = normalizeBatch(batchStr); var currentYear = new Date().getFullYear();
  var tryParse = function(str) {
      if (str.length < 5) return null; var yy = parseInt(str.substring(0, 2), 10); var mChar = str.charAt(2).toUpperCase(); var dd = parseInt(str.substring(3, 5), 10); var mm = -1;
      if (/[0-9]/.test(mChar)) { mm = parseInt(mChar, 10); if (mm < 1) return null; } else { if (mChar === 'A') mm = 10; else if (mChar === 'B') mm = 11; else if (mChar === 'C') mm = 12; }
      if (isNaN(yy) || mm === -1 || isNaN(dd) || dd < 1 || dd > 31) return null;
      var fullYear = 2000 + yy; if (fullYear > currentYear + 5) return null;
      return new Date(fullYear, mm - 1, dd);
  };
  var d1 = tryParse(cleanBatch); var d2 = (cleanBatch.length > 5) ? tryParse(cleanBatch.substring(1)) : null; return (d1 && d2) ? (d2.getTime() > d1.getTime() ? d2 : d1) : (d1 || d2);
}
function calculateExpectedExpiry(prodDate) { if (!prodDate) return ""; var d = new Date(prodDate); d.setFullYear(d.getFullYear() + 1); d.setDate(d.getDate() - 1); return Utilities.formatDate(d, Session.getScriptTimeZone(), "yyyyMMdd"); }

// --- 入庫檢點核心寫入邏輯 (相容 20 碼與 24 碼) ---
function processAndSave(data) {
  var f = data.fields; var mode = data.mode; var location = data.location || ""; var errorList = [];
  var boxBarcode = toStr(f[0]).trim(); var boxMat = ""; var boxExpiry = ""; 

  // ========================================================
  // 1. 料號與保存期限條碼檢核 (外箱標籤)
  //    - 首碼 1：相容 20 碼(舊庫存) 與 24 碼(新規格)
  //    - 首碼 7：長度 29 碼，需包含 -T0
  // ========================================================
  if (boxBarcode !== "") {
    var len = boxBarcode.length, prefix = boxBarcode.charAt(0), suffix = boxBarcode.slice(-2).toUpperCase(); 
    
    // 結尾代碼卡控 (同時相容 TSMC 常見的 TS 與 Email 規範的 TW)
    if (suffix !== "TS" && suffix !== "TW") {
      errorList.push('❌ [料號與保存期限條碼] 格式錯誤！結尾必須是 TS 或 TW (目前: ' + suffix + ')。');
    }
    else if (prefix === "1") { 
      // ========================================================
      // 【精準儲槽卡控】：偵測當前批號是否屬於 M76 儲槽
      // ========================================================
      var isM76 = false;
      for (var k = 0; k < f.length; k++) {
        if (toStr(f[k]).toUpperCase().indexOf("M76") !== -1) {
          isM76 = true;
          break;
        }
      }

      var lengthValid = false;
      if (isM76) {
        // 【M76 儲槽】：嚴格只能是 24 碼！不得為 20 碼或其他長度
        if (len === 24) {
          lengthValid = true;
        } else {
          errorList.push('❌ [料號與保存期限條碼] 長度錯誤！<br>👉 M76 儲槽只能是 24 碼 (目前長度: ' + len + ')。');
        }
      } else {
        // 【其他儲槽】：非 M76 儲槽嚴格只能是 20 碼！不得為 24 碼或其他長度
        if (len === 20) {
          lengthValid = true;
        } else {
          errorList.push('❌ [料號與保存期限條碼] 長度錯誤！<br>👉 一般儲槽(非 M76)應為 20 碼 (目前長度: ' + len + ')。');
        }
      }

      if (lengthValid) { 
        // 依據儲槽長度精準截取料號與效期
        var rD   = (len === 24) ? boxBarcode.substring(14, 22) : boxBarcode.substring(10, 18); 
        var mStr = (len === 24) ? boxBarcode.substring(1, 14).trim() : boxBarcode.substring(1, 10).trim();

        if (/^\d{8}$/.test(rD)) { 
          boxExpiry = rD; 
          boxMat = mStr; 
        } else {
          errorList.push('❌ 日期解析失敗！(抓取到的日期碼: ' + rD + ')'); 
        }
      } 
    } 
    else if (prefix === "7") { 
      if (len !== 29) {
        errorList.push('❌ [料號與保存期限條碼] 長度錯誤！首碼7應為29碼。<br>目前長度: ' + len); 
      } else if (boxBarcode.indexOf("-T0") === -1) {
        errorList.push('❌ 格式錯誤！首碼為7時，必須包含 "-T0"'); 
      } else { 
        var rD = boxBarcode.substring(19, 27); 
        if (/^\d{8}$/.test(rD)) { 
          boxExpiry = rD; 
          boxMat = boxBarcode.substring(0, 19).trim(); 
        } else {
          errorList.push('❌ 日期解析失敗！(抓取到的日期碼: ' + rD + ')'); 
        }
      } 
    } 
    else {
      errorList.push('❌ 首碼須為 1 或 7');
    }
  }

  var headers = [];
  if (mode === 'field_az') headers = ["日期時間", "作業場所", "料號與保存期限條碼", "桶1批號", "桶1出貨地", "桶1料號", "桶2批號", "桶2出貨地", "桶2料號", "桶3批號", "桶3出貨地", "桶3料號", "桶4批號", "桶4出貨地", "桶4料號", "四合一料號", "4in1批1", "4in1批2", "4in1批3", "4in1批4", "判定結果"];
  else headers = ["日期時間", "作業場所", "料號與保存期限條碼", "桶1批號", "桶1料號", "桶2批號", "桶2料號", "桶3批號", "桶3料號", "桶4批號", "桶4料號", "四合一料號", "4in1批1", "4in1批2", "4in1批3", "4in1批4", "判定結果"];

  var tankMap = [{b:1,d:2,m:3,mb:14,n:'第一桶'},{b:4,d:5,m:6,mb:15,n:'第二桶'},{b:7,d:8,m:9,mb:16,n:'第三桶'},{b:10,d:11,m:12,mb:17,n:'第四桶'}];
  var idxMasterMat = 13; var masterMaterial = cleanMatMaster(f[idxMasterMat]); var seenMasterBatches = [];
  if (mode === 'field_full' && !masterMaterial) return { status: 'error', message: '❌ [四合一料號] 為必填項目！' };
  
  var activeTankCount = 0; var seenTankBatches = [];

  for (var i = 0; i < tankMap.length; i++) {
    var item = tankMap[i]; var rawB = toStr(f[item.b]).trim(); var rawM = toStr(f[item.m]).trim(); var rawD = toStr(f[item.d]).trim(); var rawMB = toStr(f[item.mb]).trim();
    if (mode === 'field_az' && (rawB!==""||rawM!=="")) { if (rawD === "") errorList.push('❌ [' + item.n + '] 漏掃出貨地！'); else if (rawD !== "310651601") errorList.push('❌ [' + item.n + '] 出貨地錯誤！(應為310651601)'); }
    if (mode === 'field_full' && rawMB !== "") { var nm = normalizeBatch(rawMB); if (seenMasterBatches.some(function(b){return normalizeBatch(b)===nm})) errorList.push('❌ [四合一] 批號重複'); else seenMasterBatches.push(rawMB); }
    if (rawB !== "" || rawM !== "") {
      activeTankCount++;
      if (rawM === "" && rawB !== "") errorList.push('❌ [' + item.n + '] 漏掃料號！');
      if (rawM !== "" && rawB === "") errorList.push('❌ [' + item.n + '] 漏掃批號！');
      if (rawB !== "") {
        var rb = extractRealBatch(rawB); var nrb = normalizeBatch(rb);
        if (seenTankBatches.some(function(b){return normalizeBatch(extractRealBatch(b))===nrb})) errorList.push('❌ [' + item.n + '] 重複掃描！'); else seenTankBatches.push(rawB);
        if (boxMat!=="" && boxExpiry!=="") {
           if (rawM!==boxMat && rawM.substring(1)!==boxMat) errorList.push('❌ [' + item.n + '] 料號不符！');
           var pd = decodeBatchDate(rb); if (pd) { var ee = calculateExpectedExpiry(pd); if (ee!==boxExpiry) errorList.push('❌ [' + item.n + '] 效期異常！(推算:'+ee+')'); }
        }
      }
      if (mode === 'field_full' && rawM!=="" && rawM!==masterMaterial) errorList.push('❌ [' + item.n + '] 4in1料號不符！');
      if ((mode==='field_full'||mode==='field_az') && rawB.indexOf('@')!==-1 && rawM!=="") { var qm = extractRealMat(rawB); if (qm!==rawM && qm!==rawM.substring(1)) errorList.push('❌ [' + item.n + '] 貼紙錯誤！'); }
      if (mode==='field_full' && rawB!=="") {
         if (rawMB==="") errorList.push('❌ [' + item.n + '] 缺4in1批號！');
         else { var rb2 = extractRealBatch(rawB); var sc = normalizeBatch(rb2).toUpperCase(); var mc = normalizeBatch(rawMB).toUpperCase(); var im = false; if (sc===mc) im=true; else if (mc.length>1 && sc===mc.substring(1)) im=true; if (!im) errorList.push('❌ [' + item.n + '] 批號不一致！'); }
      }
    }
  }

  if (activeTankCount === 0) return { status: 'error', message: '⚠️ 無資料！' };
  if (mode === 'field_full') { var amc = 0; for (var m=14; m<=17; m++) if (toStr(f[m]).trim()!=="") amc++; if (activeTankCount!==amc) errorList.push('❌ 數量異常！'); if (activeTankCount<4) errorList.push('❌ [整板] 需掃滿4桶！'); }
  if (mode === 'field_az' && activeTankCount < 4) errorList.push('❌ [AZ] 需掃滿4桶！');
  if (mode === 'field_loose' && activeTankCount > 3) errorList.push('❌ [散桶] 最多3桶！');
  if (errorList.length > 0) return { status: 'error', message: errorList.join('\n') };

  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet(); var now = new Date(); var year = now.getFullYear(); var month = now.getMonth(); 
    var startM = Math.floor(month / 2) * 2 + 1; var endM = startM + 1; var pad = function(n) { return (n < 10 ? '0' : '') + n; };
    var dateSuffix = "_" + year + "-" + pad(startM) + "~" + pad(endM);
    var baseName = mode === 'field_full' ? "現場整板紀錄" : (mode === 'field_az' ? "現場AZ紀錄" : "現場散桶紀錄");
    var targetSheetName = baseName + dateSuffix;
    var sheet = ss.getSheetByName(targetSheetName);
    if (!sheet) { sheet = ss.insertSheet(targetSheetName); sheet.appendRow(headers); sheet.setFrozenRows(1); }
    var dataToWrite = [toStr(f[0])];
    for(var i=0; i<4; i++) {
       var idxBase = i*3 + 1; dataToWrite.push(toStr(f[idxBase])); 
       if (mode === 'field_az') dataToWrite.push(toStr(f[idxBase+1])); 
       dataToWrite.push(toStr(f[idxBase+2])); 
    }
    for(var i=13; i<=17; i++) dataToWrite.push(toStr(f[i]));
    var resultText = mode === 'field_full' ? '批號/效期一致 合格' : (mode === 'field_az' ? 'AZ檢查 合格' : '散桶紀錄完成');
    sheet.appendRow([now, location].concat(dataToWrite).concat([resultText]));
    var lastRow = sheet.getLastRow(); var dailyCount = 1;
    if (lastRow > 1) { var dts = sheet.getRange(Math.max(2, lastRow-200), 1, Math.min(lastRow-1, 201), 1).getValues(); var tc=0; for(var i=0;i<dts.length;i++) if(dts[i][0] instanceof Date && isSameDay(dts[i][0], now)) tc++; if(tc>0) dailyCount=tc; }
    return { status: 'success', message: '✅ [' + targetSheetName + '] 成功！<br>(本日第 ' + dailyCount + ' 筆)', count: dailyCount };
  } catch (e) { return { status: 'error', message: '寫入錯誤: ' + e.toString() }; }
}

// ==========================================
// 4. v51.1 結構化查詢邏輯 (AZ欄位順序自動修正版 + 20/24碼相容)
// ==========================================
function searchRecords(params) {
  var ss = SpreadsheetApp.getActiveSpreadsheet(); var sheets = ss.getSheets(); var results = [];
  var searchType = params.type; var targetSheets = [];
  sheets.forEach(function(sheet) { if (sheet.getName().indexOf("現場") !== -1 && sheet.getName().indexOf("紀錄") !== -1) targetSheets.push(sheet); });

  for (var i = 0; i < targetSheets.length; i++) {
    var sheet = targetSheets[i]; var lastRow = sheet.getLastRow(); if (lastRow < 2) continue; 
    var sheetName = sheet.getName();
    
    var modeBadge = "field_loose"; var modeLabel = "散桶";
    if (sheetName.indexOf("整板") !== -1) { modeBadge = "field_full"; modeLabel = "整板"; }
    else if (sheetName.indexOf("AZ") !== -1) { modeBadge = "field_az"; modeLabel = "AZ"; }

    // --- 【關鍵修正】智慧判斷欄位順序 ---
    var header = sheet.getRange(1, 1, 1, 25).getValues()[0];
    
    var hasLoc = (header[1] && toStr(header[1]).indexOf("場所") !== -1);
    var idxLoc = hasLoc ? 1 : -1;
    var idxBox = hasLoc ? 2 : -1;

    // 判斷是否為 AZ 模式 (有無出貨地?)
    var hE = toStr(header[4]); // 第 5 欄
    var hF = toStr(header[5]); // 第 6 欄
    var hasDest = (hE.indexOf("出貨地") !== -1 || hF.indexOf("出貨地") !== -1);

    var step = (hasDest) ? 3 : 2;
    var offsetDest = 1; 
    var offsetMat = 2;  
    
    if (hasDest) {
       // 如果 F 欄是出貨地，代表是模式 B (Excel實際狀況)
       if (hF.indexOf("出貨地") !== -1) {
          offsetMat = 1;
          offsetDest = 2;
       } 
    }

    var data = sheet.getRange(2, 1, lastRow - 1, 30).getValues(); 

    for (var r = 0; r < data.length; r++) {
      var row = data[r]; var rawDate = row[0]; var rowDate = null;
      if (rawDate instanceof Date) rowDate = rawDate;
      else if (typeof rawDate === 'string') rowDate = new Date(rawDate.replace("上午","AM").replace("下午","PM"));
      if (!rowDate || isNaN(rowDate.getTime())) continue;

      var isMatch = false; var qStr = toStr(params.batch).trim().toUpperCase();
      if (searchType === 'date') {
        var qDateStart = new Date(params.dateStart); var qDateEnd = new Date(params.dateEnd);
        qDateStart.setHours(0,0,0,0); qDateEnd.setHours(23,59,59,999);
        if (rowDate >= qDateStart && rowDate <= qDateEnd) isMatch = true;
      }
      if (searchType === 'batch') {
        var rowStr = row.join(" ").toUpperCase();
        if (rowStr.indexOf(qStr) !== -1) isMatch = true;
      }

      if (isMatch) {
        var dateStr = Utilities.formatDate(rowDate, Session.getScriptTimeZone(), "yyyy/MM/dd HH:mm:ss");
        var locStr = (idxLoc !== -1) ? toStr(row[idxLoc]) : "未紀錄";
        var boxStr = (idxBox !== -1) ? toStr(row[idxBox]) : "";
        var boxMat = "";
        
        // 【關鍵修改】：歷史查詢保留 20 碼與 24 碼雙向解析相容，確保舊資料料號不失真
        if (boxStr.startsWith("1")) {
          boxMat = (boxStr.length === 24) ? boxStr.substring(1, 14).trim() : boxStr.substring(1, 10).trim();
        } else if (boxStr.startsWith("7") && boxStr.length >= 19) {
          boxMat = boxStr.substring(0, 19).trim();
        }

        var tanks = [];
        for (var t=0; t<4; t++) {
           var startOffset = hasLoc ? 3 : 1; 
           var base = startOffset + (t * step);
           
           var bVal = toStr(row[base]); 
           if (!bVal) continue;
           
           var dVal = ""; var mVal = "";
           if (hasDest) { 
             dVal = toStr(row[base + offsetDest]); 
             mVal = toStr(row[base + offsetMat]); 
           } else { 
             mVal = toStr(row[base + 1]); 
           }
           tanks.push({ id: t+1, batch: bVal, dest: dVal, mat: mVal });
        }

        var master = null;
        if (modeBadge === "field_full") {
           var mmIdx = (hasDest) ? 15 : 11; 
           if (row[mmIdx]) {
              var mMat = toStr(row[mmIdx]); var mBatches = [];
              for(var k=1; k<=4; k++) if(row[mmIdx+k]) mBatches.push(toStr(row[mmIdx+k]));
              master = { mat: mMat, batches: mBatches };
           }
        }
        var resultStr = toStr(row[row.length-1]); 

        results.push({ id: i, date: dateStr, location: locStr, mode: modeBadge, modeLabel: modeLabel, box: boxStr, boxMat: boxMat, tanks: tanks, master: master, result: resultStr });
      }
    }
  }
  results.sort(function(a, b) { return b.date.localeCompare(a.date); });
  return results;
}
