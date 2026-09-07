# 出貨核對系統 (GAS純雲端版) 程式碼完整註解說明書

這份文件為系統的核心 GAS 程式碼加上了**逐段、逐行的詳細中文註解**。您可以直接將以下程式碼**全選複製**，貼上並覆蓋您原本的 `程式碼.gs`。這不僅不會影響原本的功能，還能讓未來接手維護的工程師或您自己，一眼看懂每段程式碼在做什麼！

```javascript
// ==========================================
// 1. 網頁開啟與查詢介面 (GET 請求)
// 作用：當使用者透過瀏覽器打開這個 GAS 網址時會執行的入口。
// 邏輯：根據網址後面的參數 (page=query)，決定要顯示「歷史查詢畫面」還是「首頁畫面」。
// ==========================================
function doGet(e) {
  var page = e.parameter.page;
  if (page === 'query') {
    return HtmlService.createTemplateFromFile('Query').evaluate()
        .setTitle('出貨核對-歷史查詢')
        .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL) // 允許被其他網頁嵌入 (如 iframe)
        .addMetaTag('viewport', 'width=device-width, initial-scale=1'); // 適應手機螢幕大小
  } else {
    return HtmlService.createTemplateFromFile('Index').evaluate()
        .setTitle('出貨核對系統 (v34.6)')
        .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL)
        .addMetaTag('viewport', 'width=device-width, initial-scale=1');
  }
}

// ==========================================
// 2. 接收手機 App 背景同步 (POST 請求)
// 作用：提供給手機 APP (或 API) 呼叫的入口。當手機掃描完成按下「上傳」時，資料會送到這裡。
// ==========================================
function doPost(e) {
  try {
    // 1. 取得 POST 請求的 Body 內容 (手機傳來的 JSON 字串)
    var rawData = e.postData.contents;
    if (!rawData) {
      // 沒收到資料時的防呆回傳
      return ContentService.createTextOutput(JSON.stringify({ 
        status: "error", 
        message: "❌ 未接收到任何資料" 
      })).setMimeType(ContentService.MimeType.JSON);
    }
    
    // 2. 解析 JSON：將純文字轉換回物件結構
    var json = JSON.parse(rawData);
    var recordData = JSON.parse(json.barcode);
    
    // 3. 呼叫現有的核心存檔法官邏輯 (判斷是否合格、是否可寫入試算表)
    var result = processAndSave(recordData);
    
    // 4. 將檢查與存檔結果回傳給手機 App，讓手機顯示成功或報錯畫面
    return ContentService.createTextOutput(JSON.stringify(result))
      .setMimeType(ContentService.MimeType.JSON);
      
  } catch (err) {
    // 萬一程式執行發生不可預期的崩潰，觸發 Teams 警報
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
// 3. 輔助函式庫 (資料清洗與格式轉換)
// 作用：提供給主程式呼叫的小工具，專門處理字串清理、防呆轉換。
// ==========================================

// 將全形字元轉換為半形字元 (防止現場人員不小心切換到全形輸入導致比對失敗)
function toHalfWidth(str) {
  if (!str) return "";
  return str.toString().replace(/[\uff01-\uff5e]/g, function(ch) {
    return String.fromCharCode(ch.charCodeAt(0) - 0xfee0);
  }).replace(/\u3000/g, ' ');
}

// 正規化批號：轉半形後，只保留英文字母和數字 (過濾掉特殊符號如 - 或空白)
function normalizeBatch(str) {
  if (!str) return "";
  var half = toHalfWidth(str); 
  return half.replace(/[^a-zA-Z0-9]/g, ''); 
}

// 從 QR Code 中萃取出真實的「批號」
// 邏輯：找 @ 與 +，抓取它們中間的那段 (例如 L14@7L14-T04+2027 會抽出 7L14-T04+2027)
function extractRealBatch(fullString) {
  if (!fullString) return "";
  var s = fullString.toString().trim();
  if (s.indexOf('@') !== -1 && s.indexOf('+') !== -1) {
    var parts = s.split('@');
    if (parts.length > 1) return parts[1]; 
  }
  return s;
}

// 專門為「繳庫單比對」設計的批號萃取器
// 邏輯：不只要解開 QR code，還要強制切除 '+' 後面的日期與空白
function extractBatchForWarehouse(fullString) {
  var s = extractRealBatch(fullString);
  if (s.indexOf('+') !== -1) s = s.split('+')[0];
  if (s.indexOf(' ') !== -1) s = s.split(/\s+/)[0];
  return s;
}

// 清理料號主檔 (單據上的料號)
// 邏輯：去掉空白，並將開頭的「數字+L」(如 1L, 2L) 統一還原為「L」，以利後續與現場比對
function cleanMatMaster(str) {
  if (!str) return "";
  var s = str.toString().trim().toUpperCase(); 
  if (s.indexOf(' ') > -1) s = s.split(' ')[0];
  s = s.replace(/^\d+L/, 'L');
  return s;
}

// 從 QR Code 中萃取出真實的「料號」
// 邏輯：抓取 @ 前面的部分。如果前面超過 14 碼，取後面的部分。
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

// 判斷兩個日期是否為同一天 (用來計算本日第幾筆)
function isSameDay(d1, d2) {
  return d1.getFullYear() === d2.getFullYear() &&
         d1.getMonth() === d2.getMonth() &&
         d1.getDate() === d2.getDate();
}

// 取得批號的主體 (去除 + 號或空白後面的雜訊)
function getBatchBase(str) {
  var s = String(str).trim();
  if (s.indexOf("+") !== -1) {
    return s.split("+")[0];
  } else if (s.indexOf(" ") !== -1) {
    return s.split(" ")[0];
  }
  return s;
}

// ==========================================
// 格式驗證器 (檢查長度與特殊規則)
// ==========================================

// 檢查 7 系列 (含 AZ 短批號) 的格式規則
function check7SeriesFormat(code) {
  var s = String(code).trim();
  // 規則 A：7 開頭的批號，長度必須是 29 碼(傳統) 或 13 碼(AZ)，且必須包含 -T0
  if (s.startsWith("7")) {
    if (s.length !== 29 && s.length !== 13) {
      return "❌ 格式錯誤！\n👉 [7開頭] 長度需 29 碼或 13 碼 (目前 " + s.length + " 碼)";
    }
    if (s.toUpperCase().indexOf("-T0") === -1) {
      return "❌ 格式錯誤！\n👉 [7開頭] 需包含 '-T0'";
    }
  }
  // 規則 B：若包含 -T0 但開頭卻不是 7，代表刷錯條碼
  if (s.toUpperCase().indexOf("-T0") !== -1 && !s.startsWith("7")) {
    return "❌ 格式錯誤！\n👉 含有 '-T0' 必須以 '7' 開頭";
  }
  return "OK";
}

// 檢查 1 系列的格式規則
function check1SeriesFormat(code) {
  var s = String(code).trim();
  // 1 開頭的必須是 20 碼，且以 TS 結尾
  if (s.startsWith("1")) {
    if (s.length !== 20) return "❌ 格式錯誤！\n👉 [1開頭] 長度需 20 碼 (目前 " + s.length + ")";
    if (!s.endsWith("TS")) return "❌ 格式錯誤！\n👉 [1開頭] 必須以 'TS' 結尾";
  }
  return "OK";
}

// 總驗證器 (會被出貨邏輯呼叫)
function validate17Series(val, label, errors) {
  if (!val || String(val).trim() === "") return;
  // 先把 QR Code 脫殼，抽出真正的批號
  var realVal = extractRealBatch(val);
  // 去除尾部的日期 (+號之後) 以利精準計算長度
  if (realVal.indexOf('+') !== -1) {
    realVal = realVal.split('+')[0];
  }
  var c1 = check1SeriesFormat(realVal);
  if (c1 !== "OK") errors.push('❌ [' + label + '] ' + c1);
  var c7 = check7SeriesFormat(realVal);
  if (c7 !== "OK") errors.push('❌ [' + label + '] ' + c7);
}

// 嚴格比對器：比較「現場掃描值」與「單據值」是否一致
function verifyPairStrict(scanVal, masterVal) {
  var scan = String(scanVal).trim();
  var master = String(masterVal).trim();
  if (scan === "" || master === "") return { pass: false, msg: "資料空白" };

  // 1字頭特殊放寬比對邏輯 (允許單據批號只輸入後半段)
  if (scan.startsWith("1") && scan.length === 20 && scan.endsWith("TS")) {
      if (scan === master) return { pass: true, msg: "OK" };
      if (scan.indexOf(master) !== -1 && master.length > 5) return { pass: true, msg: "OK" };
      return { pass: false, msg: "1字頭比對失敗\n現場: " + scan + "\n單據: " + master };
  }

  // QR Code 脫殼比對邏輯
  var isQr = (scan.indexOf("@") !== -1);
  if (isQr) {
    var processedScan = "";
    var parts = scan.split('@');
    if (parts.length > 1) processedScan = parts[1];
    else processedScan = scan;
    processedScan = processedScan.replace(/\+/g, '').replace(/\s+/g, ''); // 現場去除 + 號
    
    var processedMaster = master;
    if (processedMaster.length > 0) processedMaster = processedMaster.substring(1); // 單據預設去除第一碼
    processedMaster = processedMaster.replace(/\s+/g, '');

    if (processedScan === processedMaster) return { pass: true, msg: "OK" };
    else return { pass: false, msg: "QR比對失敗\n現場(去+): " + processedScan + "\n單據(去首碼): " + processedMaster };
  }

  // 一般全文字比對
  if (scan === master) return { pass: true, msg: "OK" };
  // 去除空白後再次比對
  if (scan.replace(/\s+/g, '') === master.replace(/\s+/g, '')) return { pass: true, msg: "OK" };
  
  return { pass: false, msg: "數值不一致\n現場: " + scan + "\n單據: " + master };
}

// 產生雙月結算的 Sheet 頁籤名稱尾綴 (例如 _2026-07~08)
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

// 安全解析試算表上的日期，支援中英混雜
function parseSheetDate(val) {
  if (!val) return null;
  if (val instanceof Date) return val;
  var str = val.toString().trim();
  str = str.replace("上午", "AM").replace("下午", "PM");
  var d = new Date(str);
  return isNaN(d.getTime()) ? null : d;
}

// ==========================================
// 4. 主程式核心大腦 (巡檢核對與寫入)
// 作用：接收手機送來的各欄位資料，依據不同模式進行各項業務邏輯檢查。
// 若有錯誤則阻擋寫入並回傳錯誤訊息；若全部通過，則寫入對應的 Sheet。
// ==========================================
function processAndSave(data) {
  var f = data.fields; // 陣列，包含畫面上所有的輸入框內容
  var mode = data.mode; // 出貨模式 (AZ, 整板, 散桶等)
  var location = data.location; // 作業廠區
  var allErrors = []; // 用來收集所有發生的錯誤
  var headers = [];
  var writeData = []; 

  // 定義現場最多 4 桶的位置對應
  var tankMap = [
    { batch: 0, mat: 1, name: '第一桶', masterBatchIdx: 9 },
    { batch: 2, mat: 3, name: '第二桶', masterBatchIdx: 10 },
    { batch: 4, mat: 5, name: '第三桶', masterBatchIdx: 11 },
    { batch: 6, mat: 7, name: '第四桶', masterBatchIdx: 12 }
  ];

  // ----------------------------------------
  // 【模式 A】AZ 出貨核對專用邏輯
  // ----------------------------------------
  if (mode === 'ship_az') {
    headers = ["日期時間", "作業場所", "桶1批號", "桶1料號", "桶2批號", "桶2料號", "桶3批號", "桶3料號", "桶4批號", "桶4料號", "判定結果"];
    var activeTankCount = 0;
    var firstTankMaterial = ""; 
    var rawBatches = [];
    var seenAz = {}; 

    // 逐桶檢查
    for (var i = 0; i < tankMap.length; i++) {
      var item = tankMap[i];
      var rawBatch = f[item.batch].toString().trim();
      var rawMat = f[item.mat].toString().trim(); 
      
      if (rawBatch !== "" || rawMat !== "") {
        activeTankCount++;
        rawBatches.push(rawBatch);

        // 1. 執行 1/7 系列基本格式驗證
        validate17Series(rawBatch, item.name + ' 批號', allErrors);
        
        // 2. 檢查是否重複掃描 (掃到同一桶)
        var norm = normalizeBatch(rawBatch);
        if (norm !== "") {
            if (seenAz[norm]) allErrors.push('❌ [' + item.name + '] 重複掃描！(與 ' + seenAz[norm] + ' 相同)');
            else seenAz[norm] = item.name;
        }

        // 3. 確保 1~4 桶料號必須全部相同
        var cleanMat = cleanMatMaster(rawMat); 
        if (firstTankMaterial === "") firstTankMaterial = cleanMat;
        if (cleanMat !== firstTankMaterial) allErrors.push('❌ [' + item.name + '] 料號異常！與第一桶不同。');
        
        // 4. 驗證 QR Code 內建料號是否等於畫面輸入的料號
        if (rawBatch.indexOf('@') !== -1) {
           var qrMat = extractRealMat(rawBatch);
           if (qrMat !== "" && qrMat !== cleanMat) allErrors.push('❌ [' + item.name + '] 貼紙錯誤！QR料號與掃描料號不符');
        }
      }
    }

    if (activeTankCount === 0) return { status: 'error', message: '⚠️ 未偵測到任何資料' };
    
    // 5. 確保多桶間的 AZ 批號主體與長度必須一致
    if (rawBatches.length > 1) {
       var base1 = getBatchBase(rawBatches[0]);
       var len1 = rawBatches[0].length; 

       for (var k=1; k<rawBatches.length; k++) {
          if (getBatchBase(rawBatches[k]) !== base1) {
             allErrors.push('❌ AZ批號不一致！第' + (k+1) + '桶與第1桶批號主體不同。');
          }
          var lenK = rawBatches[k].length;
          // 長度落差大於 10 碼，代表可能有人掃了短碼有人掃了 QR
          if (Math.abs(len1 - lenK) > 10) {
             allErrors.push('❌ AZ長度異常！\n👉 第1桶長度: ' + len1 + '\n👉 第' + (k+1) + '桶長度: ' + lenK + '\n(可能發生重複掃描或殘留字元)');
          }
       }
    }
    writeData = f.slice(0, 8); // 準備寫入資料

  } 
  // ----------------------------------------
  // 【模式 B】一般散桶/整板/混板核對邏輯
  // ----------------------------------------
  else {
    headers = ["日期時間", "作業場所", "桶1批號", "桶1料號", "桶2批號", "桶2料號", "桶3批號", "桶3料號", "桶4批號", "桶4料號", "四合一料號", "4in1批1", "4in1批2", "4in1批3", "4in1批4", "繳庫料號", "繳庫批1", "繳庫批2", "繳庫批3", "判定結果"];

    // 檢查四合一單據欄位是否有填
    var rawMasterMat = f[8].toString().trim();
    var masterMaterial = cleanMatMaster(rawMasterMat); 
    if (!masterMaterial) return { status: 'error', message: '❌ [四合一料號] 為必填項目！' };
    
    validate17Series(rawMasterMat, '四合一料號', allErrors);

    var activeTankCount = 0; 
    var activeBatchesShort = []; 
    var collectedBatchBases = []; 
    var seenDrumbatches = {}; 

    // 逐桶檢查並比對單據
    for (var i = 0; i < tankMap.length; i++) {
      var item = tankMap[i];
      var tankRawBatch = f[item.batch].toString().trim();
      var tankInputMat = f[item.mat].toString().trim();
      var masterBatchVal = f[item.masterBatchIdx].toString().trim();

      if (tankRawBatch !== "" || tankInputMat !== "") {
        activeTankCount++;

        validate17Series(tankRawBatch, item.name + ' 批號', allErrors);

        // 重複掃描檢查
        var normBatch = normalizeBatch(tankRawBatch);
        if (normBatch !== "") {
            if (seenDrumbatches[normBatch]) {
                allErrors.push('❌ [' + item.name + '] 重複掃描！(與' + seenDrumbatches[normBatch] + '相同)');
            } else {
                seenDrumbatches[normBatch] = item.name;
            }
        }

        // 料號一致性比對 (現場 vs 四合一單據)
        var tankCleanMat = cleanMatMaster(tankInputMat);
        if (tankCleanMat !== masterMaterial) allErrors.push('❌ [' + item.name + '] 料號異常！\n👉 現場: ' + tankCleanMat + '\n👉 單據: ' + masterMaterial);

        if (tankRawBatch.indexOf('@') !== -1) {
           var qrMat = extractRealMat(tankRawBatch);
           if (qrMat !== "" && qrMat !== tankCleanMat) allErrors.push('❌ [' + item.name + '] 貼紙錯誤！\nQR內碼: ' + qrMat + '\n與掃描不符。');
        }

        // 嚴格比對：現場批號 vs 單據批號
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

    // 【整板出貨防呆】若為整板出貨，現場的批號必須完全一致不可混裝
    if (mode === 'ship_full' && collectedBatchBases.length > 1) {
       var standardBase = collectedBatchBases[0].base;
       for (var k = 1; k < collectedBatchBases.length; k++) {
          if (collectedBatchBases[k].base !== standardBase) allErrors.push('❌ 整板批號異常！不同批號不可混在同板');
       }
    }

    // 防呆：現場桶數必須等於單據輸入的筆數
    var activeMasterCount = 0;
    for (var m = 9; m <= 12; m++) if (f[m].toString().trim() !== "") activeMasterCount++;
    if (activeTankCount !== activeMasterCount) allErrors.push('❌ 數量異常！現場 ' + activeTankCount + ' 桶 vs 四合一 ' + activeMasterCount + ' 筆');

    // ----------------------------------------
    // 【繳庫單比對邏輯】
    // ----------------------------------------
    var rawWhMat = f[13].toString().trim();
    var cleanWhMat = cleanMatMaster(rawWhMat); 
    
    if (cleanWhMat !== masterMaterial) allErrors.push('❌ [繳庫單] 料號異常！');
    
    var whBatch1 = f[14].trim(); 
    var whBatch2 = f[15].trim();
    var whBatch3 = f[16].trim();

    if (whBatch1 === "" && whBatch2 === "" && whBatch3 === "") {
       allErrors.push('❌ [繳庫單] 未掃描任何批號！');
    } else {
      var tempBatches = activeBatchesShort.slice();
      // 確保繳庫單打的批號，現場都有掃到
      var checkAndRemove = function(val) {
        if (val === "") return true;
        var whNorm = normalizeBatch(extractBatchForWarehouse(val)); 
        for (var i = 0; i < tempBatches.length; i++) {
           var fieldNorm = normalizeBatch(tempBatches[i]); 
           // 支援開頭補 2 的特殊規則
           if (fieldNorm === whNorm || fieldNorm === "2"+whNorm || whNorm === "2"+fieldNorm) {
              tempBatches.splice(i, 1); return true; 
           }
        }
        return false;
      };
      
      if (!checkAndRemove(whBatch1)) allErrors.push('❌ [繳庫單批號1] 異常！現場沒掃到。');
      if (!checkAndRemove(whBatch2)) allErrors.push('❌ [繳庫單批號2] 異常！現場沒掃到。');
      if (!checkAndRemove(whBatch3)) allErrors.push('❌ [繳庫單批號3] 異常！現場沒掃到。');

      // 反向防呆：確保現場掃到的所有「不重複批號」，繳庫單上都有填
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

  // ----------------------------------------
  // 【錯誤攔截與回報】
  // ----------------------------------------
  if (allErrors.length > 0) {
    var errorMsg = allErrors.join('\n\n');
    try {
      sendTeamsErrorNotification(errorMsg, location, mode, f); // 觸發 Teams 警告
    } catch (errTeams) {
      Logger.log("發送 Teams 通知錯誤: " + errTeams.toString());
    }
    return { status: 'error', message: errorMsg };
  }

  // ----------------------------------------
  // 【資料寫入試算表】
  // ----------------------------------------
  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var baseSheetName = "";
    if (mode === 'ship_full') baseSheetName = "整板出貨紀錄";
    else if (mode === 'ship_mixed') baseSheetName = "混板出貨紀錄";
    else if (mode === 'ship_az') baseSheetName = "AZ出貨紀錄";
    else baseSheetName = "散桶出貨紀錄";

    // 使用雙月自動建頁籤機制 (例如: 散桶出貨紀錄_2026-07~08)
    var targetSheetName = baseSheetName + getBiMonthlySuffix();
    var sheet = ss.getSheetByName(targetSheetName);
    
    if (!sheet) {
      sheet = ss.insertSheet(targetSheetName);
      sheet.appendRow(headers);
      sheet.setFrozenRows(1);
    }

    var now = new Date();
    // 寫入當下時間、廠區、填寫資料，以及最後補上「合格」標記
    sheet.appendRow([now, location].concat(writeData, ["批號一致 合格"]));
    
    // 計算今日是第幾筆
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
// 5. 查詢功能 (供網頁介面使用)
// 作用：讀取各個「出貨紀錄」頁籤，並過濾日期與關鍵字，打包回傳給網頁前端
// ==========================================
function searchRecords(dateStart, dateEnd, keyword, useScheduleCheck) {
  // ... (保留原本邏輯，主要進行跨頁籤搜尋並支援排程比對過濾)
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
      var isAZSheet = (sName.indexOf("AZ") !== -1);
      var modeLabel = "散桶";
      if (sName.indexOf("整板") !== -1) modeLabel = "整板";
      else if (sName.indexOf("混板") !== -1) modeLabel = "混板";
      else if (isAZSheet) modeLabel = "AZ";

      var lastRow = sheet.getLastRow();
      if (lastRow < 2) continue;

      var rangeData = sheet.getDataRange().getValues();

      for (var r = rangeData.length - 1; r >= 1; r--) {
        var row = rangeData[r];
        var rowDate = parseSheetDate(row[0]);
        
        if (!rowDate || rowDate < dStart || rowDate > dEnd) continue;

        var isAZRow = isAZSheet || (row.length <= 11) || (row[10] && String(row[10]).indexOf("合格") !== -1 && !row[19]);

        var record = {};
        record.date = Utilities.formatDate(rowDate, Session.getScriptTimeZone(), "yyyy-MM-dd");
        record.time = Utilities.formatDate(rowDate, Session.getScriptTimeZone(), "HH:mm");
        record.location = row[1] || "-";
        record.mode = isAZRow ? "AZ" : modeLabel;
        record.tanks = [
            { batch: row[2] || "", mat: row[3] || "" },
            { batch: row[4] || "", mat: row[5] || "" },
            { batch: row[6] || "", mat: row[7] || "" },
            { batch: row[8] || "", mat: row[9] || "" }
        ];

        var mainBatch = "";

        if (isAZRow) {
            record.master = { mat: "", batches: [] }; 
            record.wh = { mat: "", batches: [] };
            record.result = row[10] || "未知"; 
            mainBatch = extractBatchForWarehouse(row[2] || ""); 
        } else {
            record.master = { mat: row[10] || "", batches: [row[11]||"", row[12]||"", row[13]||"", row[14]||""] };
            record.wh = { mat: row[15] || "", batches: [row[16]||"", row[17]||"", row[18]||""] };
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
// 6. 系統功能
// ==========================================
function getScriptUrl() {
  return ScriptApp.getService().getUrl();
}

// ==========================================
// 7. 排程更新與讀取功能
// 作用：提供網頁端上傳排程 (通常由業務或生管複製 Excel 上傳)
// ==========================================
function updateScheduleData(tsvData) {
  // ... (寫入試算表 [出貨排程] 頁籤)
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
// 8. Teams Webhook 異常通知功能
// 作用：當防呆報錯或系統崩潰時，自動發送 JSON 給 Teams Webhook 機器人，通知群組。
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

function testTeamsNotification() {
  var testErrors = "❌ [桶2] 與四合一單據不符！\n現場: 720260707-T001\n單據: 720260707-T002";
  var testFields = [
    "720260707-T001", "L12345", 
    "720260707-T001", "L12345", 
    "", "", 
    "", "", 
    "L12345", "720260707-T001", "720260707-T002", "", "", 
    "L12345", "720260707-T001", "", "" 
  ];
  sendTeamsErrorNotification(testErrors, "崙尾一廠", "ship_full", testFields);
}
```
