/**
 * 網頁進入點
 */
function doGet() {
  return HtmlService.createTemplateFromFile('Index')
      .evaluate()
      .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL) 
      .addMetaTag('viewport', 'width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no')
      .setTitle('鴻勝包材管理系統 v13.5');
}

/**
 * 🔄 自動建立選單
 */
function onOpen() {
  var ui = SpreadsheetApp.getUi();
  ui.createMenu('🔄 系統管理')
      .addItem('手動發送低庫存警報', 'sendLowStockAlert')
      .addToUi();
}

/**
 * 📅 檢查今天是否為工作日
 */
function isWorkDay() {
  let today = new Date();
  let day = today.getDay();
  if (day === 0 || day === 6) return false;
  try {
    let twHolidayCalId = 'zh-tw.taiwan#holiday@group.v.calendar.google.com';
    let holidayCal = CalendarApp.getCalendarById(twHolidayCalId);
    if (holidayCal) {
      let events = holidayCal.getEventsForDay(today);
      return !events.some(e => e.getTitle().includes("放假") || e.getTitle().includes("節") || e.getTitle().includes("紀念"));
    }
  } catch (e) {
    console.error("日曆讀取略過: " + e.message);
  }
  return true;
}

/**
 * 🔐 驗證使用者登入
 */
function verifyUser(account, password) {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("User_List");
  if (!sheet) return { success: false, message: "找不到 User_List！" };
  const data = sheet.getDataRange().getValues();
  for (let i = 1; i < data.length; i++) {
    if (data[i][0].toString().trim() === account.toString().trim() && data[i][1].toString().trim() === password.toString().trim()) {
      return { success: true, name: data[i][2].toString().trim() };
    }
  }
  return { success: false, message: "❌ 帳號或密碼錯誤！" };
}

/**
 * 🧼 核心工具：極致清洗字串
 */
function cleanString(str) {
  if (str === null || str === undefined) return "";
  let s = str.toString().trim();
  s = s.replace(/^['`’“]+/, "");
  return s.toLowerCase();
}

/**
 * 📝 接收表單並寫入 Log (★★★ 自動分流 NSE_Log 或 Inventory_Log ★★★)
 */
function writeInventoryLog(data) {
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const masterSheet = ss.getSheetByName("Inventory_Master");
    if (!masterSheet) throw new Error("找不到 Inventory_Master 資料庫分頁");

    const now = new Date();
    let itemName = "", itemSpec = "", safeStock = 0, itemCat = "";

    const masterData = masterSheet.getDataRange().getValues();
    const mHeaders = masterData[0];
    const colBc = mHeaders.indexOf('品號'), colNm = mHeaders.indexOf('品名'), colSp = mHeaders.indexOf('規格'), colSafe = mHeaders.indexOf('安全庫存'), colCat = mHeaders.indexOf('類別');

    const targetClean = cleanString(data.barcode);

    for (let i = 1; i < masterData.length; i++) {
      if (cleanString(masterData[i][colBc]) === targetClean) {
        if (colCat !== -1) itemCat = masterData[i][colCat].toString().trim();
        itemName = masterData[i][colNm] || "";
        itemSpec = masterData[i][colSp] || "";
        safeStock = parseFloat(masterData[i][colSafe]) || 0;
        break;
      }
    }

    // 🌟【自動分流邏輯】判斷是否為成品/NSE
    let isNSE = itemCat.includes("成品") || itemName.toUpperCase().includes("NSE") || itemName.includes("台積成品");
    let targetLogName = isNSE ? "NSE_Log" : "Inventory_Log";
    
    const logSheet = ss.getSheetByName(targetLogName);
    if (!logSheet) throw new Error(`找不到總表分頁：「${targetLogName}」，請先在試算表中建立！`);

    let finalDept = (data.type === "收入" || data.type === "入庫") ? "資材組" : data.dept;
    let finalBatch = data.batch ? data.batch.toString().trim() : "無批號";
    if (finalBatch === "") finalBatch = "無批號";

    const safeBarcode = "'" + data.barcode.toString().trim().replace(/^'/, '');
    const safeBatch = "'" + finalBatch.toString().trim().replace(/^'/, '');

    const newRowId = "L" + Utilities.formatDate(now, "GMT+8", "yyyyMMddHHmmss");
    const finalDate = data.date || Utilities.formatDate(now, "GMT+8", "yyyy/MM/dd HH:mm:ss");

    // 1. 寫入總表 Log (會依照條件分流寫入 NSE_Log 或 Inventory_Log)
    const rowData = [newRowId, finalDate, safeBarcode, itemName, itemSpec, data.type, safeBatch, data.qty, finalDept, data.remark, data.user];
    logSheet.appendRow(rowData);
    SpreadsheetApp.flush();

    const currentStock = calculateSingleItemStock(data.barcode);
    
    // ========================================================
    // 🆕 帳卡寫入邏輯
    const itemSheet = ss.getSheetByName(itemName);
    let alertMissingSheet = ""; 
    
    if (itemSheet) {
      // ★ 判斷是否為「特定原料」 (如果 NSE 也要用格子帳卡，請自行補上品名)
      const rawMaterials = ["MEA", "PG", "TMAH", "TMAHLT", "GLC250", "RSK718"];
      let isRawMaterial = rawMaterials.includes(itemName.toUpperCase().replace(/-/g, ""));
      let d = new Date(finalDate);
      
      if (isRawMaterial) {
        // 🌟🌟🌟【特定原料 專屬寫入邏輯】🌟🌟🌟
        let sheetData = itemSheet.getDataRange().getValues();
        
        if (data.type === "收入" || data.type === "入庫") {
          // 入庫：尋找最後一行新增
          let lastRow = 7; 
          for (let i = sheetData.length - 1; i >= 7; i--) {
             if (sheetData[i][3] !== "" || sheetData[i][4] !== "") { lastRow = i + 1; break; }
          }
          let targetRow = lastRow + 1;
          
          itemSheet.getRange(targetRow, 1).setValue(d.getMonth() + 1); // A: 月
          itemSheet.getRange(targetRow, 2).setValue(d.getDate());      // B: 日
          itemSheet.getRange(targetRow, 4).setValue(safeBatch);        // D: 批號
          itemSheet.getRange(targetRow, 5).setValue(data.qty);         // E: 數量
          if (data.remark) itemSheet.getRange(targetRow, 6).setValue(data.remark); // F: 備註
          
        } else {
          // 🌟【進階升級版】出庫跨列自動拆分
          let remainingQty = parseFloat(data.qty) || 0;
          let dateStr = (d.getMonth() + 1) + "/" + d.getDate();
          let isBatchFound = false;
          let writtenToAtLeastOneRow = false;
          
          for (let i = 7; i < sheetData.length; i++) {
             if (remainingQty <= 0) break; // 發貨完畢
             
             let rowBatch = sheetData[i][3] ? sheetData[i][3].toString().trim().replace(/^'/, '') : "";
             if (rowBatch === finalBatch.replace(/^'/, '')) {
                isBatchFound = true;
                
                let incomeQty = parseFloat(sheetData[i][4]) || 0;
                let issueSum = 0;
                for (let s = 0; s < 5; s++) {
                   issueSum += parseFloat(sheetData[i][7 + s]) || 0;
                }
                
                let rowAvailable = 0;
                if (incomeQty > 0) {
                   rowAvailable = incomeQty - issueSum;
                   if (rowAvailable <= 0) continue; // 已無庫存，跳下一列
                }
                
                let targetIssueIndex = -1;
                for (let slot = 0; slot < 5; slot++) {
                   if (sheetData[i][7 + slot] === "") {
                      targetIssueIndex = slot; break;
                   }
                }
                
                if (targetIssueIndex !== -1) {
                   let qtyToDeduct = remainingQty;
                   if (incomeQty > 0) {
                      qtyToDeduct = Math.min(rowAvailable, remainingQty);
                   }
                   
                   let targetRow = i + 1;
                   itemSheet.getRange(targetRow, 8 + targetIssueIndex).setValue(qtyToDeduct);
                   itemSheet.getRange(targetRow, 17 + targetIssueIndex).setValue(dateStr); // Q~U欄
                   
                   if (data.remark) {
                      let oldRemark = sheetData[targetRow - 1][5] ? sheetData[targetRow - 1][5].toString() : "";
                      let newRemark = oldRemark ? (oldRemark + "\n" + data.remark) : data.remark;
                      itemSheet.getRange(targetRow, 6).setValue(newRemark);
                   }
                   
                   remainingQty -= qtyToDeduct;
                   writtenToAtLeastOneRow = true;
                   sheetData[i][7 + targetIssueIndex] = qtyToDeduct; 
                }
             }
          }
          
          if (!isBatchFound) {
             return `❌ 寫入失敗：帳卡上找不到批號「${finalBatch}」，請檢查 D 欄！`;
          }
          if (remainingQty > 0) {
             if (writtenToAtLeastOneRow) {
                return `⚠️ 已扣除部分數量！但剩餘空間或庫存不足，還有 ${remainingQty} 未能扣除。`;
             } else {
                return `❌ 寫入失敗：批號「${finalBatch}」沒有空位或已無庫存！`;
             }
          }
        }
      } else {
        // 🌟🌟🌟【一般包材/成品 自動對位新增欄位】🌟🌟🌟
        let month = d.getMonth() + 1, day = d.getDate();        
        let summary = finalDept ? (data.type + "-" + finalDept) : data.type; 
        let isIssue = (data.type !== "入庫" && data.type !== "收入");
        
        let topHeaders = itemSheet.getRange(6, 1, 1, itemSheet.getLastColumn()).getValues()[0];
        let subHeaders = itemSheet.getRange(8, 1, 1, itemSheet.getLastColumn()).getValues()[0];
        let subHeadersClean = subHeaders.map(h => h.toString().trim());
        
        if (isIssue && subHeadersClean.indexOf(finalDept) === -1) {
          let insertTarget = -1;
          let lastLoc = subHeadersClean.lastIndexOf("批號");
          if (lastLoc === -1) lastLoc = subHeadersClean.lastIndexOf("備註"); 
          
          let balanceIndex = -1;
          for (let j = 0; j < topHeaders.length; j++) { if (topHeaders[j].toString().trim() === "結存") { balanceIndex = j; break; } }
          
          if (lastLoc !== -1 && lastLoc > 6) insertTarget = lastLoc + 1;
          else if (balanceIndex !== -1) insertTarget = balanceIndex + 1;
          
          if (insertTarget !== -1) {
            itemSheet.insertColumnBefore(insertTarget);
            itemSheet.getRange(8, insertTarget).setValue(finalDept);
            topHeaders = itemSheet.getRange(6, 1, 1, itemSheet.getLastColumn()).getValues()[0];
            subHeaders = itemSheet.getRange(8, 1, 1, itemSheet.getLastColumn()).getValues()[0];
            subHeadersClean = subHeaders.map(h => h.toString().trim());
          } else { return `❌ 寫入失敗：分頁格式異常，找不到位置自動新增欄位！`; }
        }
        
        let finalRowData = [];
        for (let i = 0; i < topHeaders.length; i++) {
          let topCol = topHeaders[i].toString().trim(), subCol = subHeadersClean[i];
          
          if (topCol === "結存") { finalRowData.push(currentStock); break; }
          
          if (i === 0) finalRowData.push(month);
          else if (i === 1) finalRowData.push(day);
          else if (i === 2) finalRowData.push(summary);
          else if (subCol === "倉庫" || subCol === "數量" || subCol === "收入數量") finalRowData.push(!isIssue ? data.qty : "");
          else if (subCol === "批號") { 
            if (i < 6 && !isIssue) finalRowData.push(safeBatch);
            else if (i >= 6 && isIssue) finalRowData.push(safeBatch);
            else finalRowData.push("");
          }
          else if (subCol === "備註") finalRowData.push(data.remark || "");
          else if (isIssue && subCol === finalDept) finalRowData.push(data.qty);
          else finalRowData.push(""); 
        }
        
        let columnAData = itemSheet.getRange("A1:A" + itemSheet.getMaxRows()).getValues();
        let lastRowInColumnA = 0;
        for (let i = columnAData.length - 1; i >= 0; i--) {
          if (columnAData[i][0] !== "") { lastRowInColumnA = i + 1; break; }
        }
        itemSheet.getRange(lastRowInColumnA + 1, 1, 1, finalRowData.length).setValues([finalRowData]);
      }
    } else {
      alertMissingSheet = `\n⚠️ 提醒：找不到名為「${itemName}」的專屬分頁，已跳過帳卡寫入。`;
    }

    try {
      if (isWorkDay() && safeStock > 0 && currentStock < safeStock) {
        let alertMsg = `⚠️【低庫存警報】⚠️\n品項：${itemName}\n結存：${currentStock}\n🛑 安全水位：${safeStock}`;
        sendLineBotMessage(alertMsg); sendEmailAlert(alertMsg, itemName);
      }
    } catch (e) {}

    return `✅ 成功寫入！當前庫存：${currentStock}${alertMissingSheet}`;
  } catch (err) {
    return `❌ 寫入失敗：${err.message}`;
  }
}

/**
 * 🧮 雙核心計算最新庫存
 */
function calculateSingleItemStock(barcode) {
  const logSheetNames = ["Inventory_Log", "NSE_Log"];
  let targetClean = cleanString(barcode);
  let balance = 0;
  
  logSheetNames.forEach(sheetName => {
    const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(sheetName);
    if (!sheet) return;
    const data = sheet.getDataRange().getValues();
    if (data.length <= 1) return;
    const headers = data[0];
    const cBc = headers.indexOf('品號'), cType = headers.indexOf('類型(進/出)'), cQty = headers.indexOf('數量');
    if (cBc === -1) return;
    
    for (let i = 1; i < data.length; i++) {
      if (cleanString(data[i][cBc]) === targetClean) {
        let qty = parseFloat(data[i][cQty]) || 0;
        if (data[i][cType] === "收入" || data[i][cType] === "入庫") balance += qty;
        else balance -= qty;
      }
    }
  });
  return balance;
}

/**
 * 🔍 雙核心獲取批號庫存
 */
function getItemBatches(barcode) { 
  if (!barcode) return []; 
  const logSheetNames = ["Inventory_Log", "NSE_Log"];
  let batchesMap = {}; 
  let issueCountMap = {}; 

  logSheetNames.forEach(sheetName => {
    const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(sheetName);
    if (!sheet) return;
    const data = sheet.getDataRange().getValues();
    if (data.length <= 1) return;
    const headers = data[0]; 
    const cBc = headers.indexOf('品號'), cType = headers.indexOf('類型(進/出)'), cBatch = headers.indexOf('批號'), cQty = headers.indexOf('數量'); 
    if (cBc === -1) return;

    for(let i = 1; i < data.length; i++) { 
      if (data[i][cBc] && cleanString(data[i][cBc]) === cleanString(barcode)) { 
        let b = data[i][cBatch] ? data[i][cBatch].toString().trim().replace(/^'/, '') : "無批號"; 
        let type = data[i][cType] ? data[i][cType].toString().trim() : "";
        let qty = parseFloat(data[i][cQty]) || 0; 
        
        if(!batchesMap[b]) { batchesMap[b] = 0; issueCountMap[b] = 0; }
        
        if(type === "入庫" || type === "收入") batchesMap[b] += qty; 
        else { batchesMap[b] -= qty; issueCountMap[b] += 1; } 
      } 
    } 
  });
  
  let result = []; 
  for(let key in batchesMap) { 
    if(batchesMap[key] > 0) result.push({ batch: key, stock: batchesMap[key], issueCount: issueCountMap[key] }); 
  } 
  return result; 
}

/**
 * 🔍 關鍵字搜尋品項
 */
function getMatchedItems(keyword) { 
  if (!keyword) return []; 
  let k = keyword.toString().trim().toLowerCase(); 
  const masterSheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Inventory_Master"); 
  if (!masterSheet) return []; 
  
  const data = masterSheet.getDataRange().getValues(); 
  const headers = data[0]; 
  const colBc = headers.indexOf('品號'), colNm = headers.indexOf('品名'), colSp = headers.indexOf('規格'); 
  let matches = []; 
  
  for (let i = 1; i < data.length; i++) { 
    let rawBc = data[i][colBc] ? data[i][colBc].toString().trim() : "";
    let cleanBc = rawBc.replace(/^'/, '');
    let nm = data[i][colNm] ? data[i][colNm].toString().trim() : ""; 
    let sp = data[i][colSp] ? data[i][colSp].toString().trim() : "-"; 
    
    if (cleanBc.toLowerCase().indexOf(k) > -1 || nm.toLowerCase().indexOf(k) > -1 || sp.toLowerCase().indexOf(k) > -1) { 
      matches.push({ barcode: cleanBc, name: nm, spec: sp }); 
      if(matches.length >= 15) break; 
    } 
  } 
  return matches; 
}

/**
 * 📊 雙核心查詢歷史帳卡 (自動按日期排序合併)
 */
function queryAccountCard(keyword, months) { 
  if (!keyword) return []; 
  const ss = SpreadsheetApp.getActiveSpreadsheet(); 
  
  let matchedItems = getMatchedItems(keyword); 
  if (matchedItems.length === 0) return []; 
  
  let cutoffDate = new Date(); 
  if (months > 0) { cutoffDate.setMonth(cutoffDate.getMonth() - parseInt(months)); cutoffDate.setHours(0, 0, 0, 0); } 
  else { cutoffDate = new Date(2000, 0, 1); } 
  
  const logSheetNames = ["Inventory_Log", "NSE_Log"];
  let allLogs = [];
  
  logSheetNames.forEach(sheetName => {
    const sheet = ss.getSheetByName(sheetName);
    if (!sheet) return;
    const data = sheet.getDataRange().getValues();
    if(data.length <= 1) return;
    const headers = data[0];
    const cDate = headers.indexOf('日期'), cBc = headers.indexOf('品號'), cType = headers.indexOf('類型(進/出)'), cBatch = headers.indexOf('批號'), cQty = headers.indexOf('數量'), cDept = headers.indexOf('領用單位'), cRemark = headers.indexOf('備註');
    if (cBc === -1) return;
    
    for(let i = 1; i < data.length; i++) {
       if(!data[i][cBc]) continue;
       allLogs.push({
          date: new Date(data[i][cDate]),
          bcClean: cleanString(data[i][cBc]),
          type: data[i][cType] ? data[i][cType].toString().trim() : "",
          batch: data[i][cBatch] ? data[i][cBatch].toString().trim().replace(/^'/, '') : "",
          qty: parseFloat(data[i][cQty]) || 0,
          dept: data[i][cDept] ? data[i][cDept].toString().trim() : "",
          remark: data[i][cRemark] ? data[i][cRemark].toString().trim() : ""
       });
    }
  });

  // 按日期精準排序
  allLogs.sort((a, b) => a.date - b.date);
  
  let allResults = []; 
  for (let j = 0; j < matchedItems.length; j++) { 
    let item = matchedItems[j], history = [], balance = 0, carryForward = 0;
    let targetClean = cleanString(item.barcode); 
    
    for (let i = 0; i < allLogs.length; i++) { 
      let log = allLogs[i];
      if (log.bcClean === targetClean) { 
        if (log.type === "入庫" || log.type === "收入") balance += log.qty; 
        else balance -= log.qty; 
        
        if (log.date < cutoffDate) { 
          carryForward = balance; 
        } else { 
          let in_qty = "", in_batch = "", out_mat = "", out_p1 = "", out_p2 = "", out_prod = "", out_batch = ""; 
          let summary = log.dept ? (log.type + "-" + log.dept) : log.type; 
          if (log.type === "入庫" || log.type === "收入") { in_qty = log.qty; in_batch = log.batch; } 
          else { 
            out_batch = log.batch; 
            if (log.dept.indexOf("資材") > -1) out_mat = log.qty; 
            else if (log.dept.indexOf("分一") > -1) out_p1 = log.qty; 
            else if (log.dept.indexOf("分二") > -1) out_p2 = log.qty; 
            else if (log.dept.indexOf("生產") > -1) out_prod = log.qty; 
            else out_mat = log.qty; 
          } 
          history.push({ 
            date: Utilities.formatDate(log.date, "GMT+8", "MM/dd"), 
            summary: summary, in_qty: in_qty, in_batch: in_batch, 
            out_mat: out_mat, out_p1: out_p1, out_p2: out_p2, out_prod: out_prod, 
            out_batch: out_batch, balance: balance, remark: log.remark 
          }); 
        } 
      } 
    } 
    if (months > 0) history.unshift({ date: "期初", summary: "上期轉入", in_qty: "", in_batch: "", out_mat: "", out_p1: "", out_p2: "", out_prod: "", out_batch: "", balance: carryForward, remark: "" }); 
    allResults.push({ details: item, history: history }); 
  } 
  return allResults; 
}

/**
 * 📊 雙核心抓取分類庫存資料
 */
function getCategoryStockData() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const masterSheet = ss.getSheetByName("Inventory_Master");
  
  let currentStockMap = {}; 
  const logSheetNames = ["Inventory_Log", "NSE_Log"];
  
  logSheetNames.forEach(sheetName => {
    const logSheet = ss.getSheetByName(sheetName);
    if (!logSheet) return;
    const logData = logSheet.getDataRange().getValues();
    if(logData.length <= 1) return;
    const lHeaders = logData[0];
    const lColBc = lHeaders.indexOf('品號'), lColType = lHeaders.indexOf('類型(進/出)'), lColQty = lHeaders.indexOf('數量');
    if(lColBc === -1) return;

    for (let i = 1; i < logData.length; i++) {
      if (!logData[i][lColBc]) continue;
      let bc = cleanString(logData[i][lColBc]);
      let type = logData[i][lColType], qty = parseFloat(logData[i][lColQty]) || 0;
      if (!currentStockMap[bc]) currentStockMap[bc] = 0;
      if (type === "入庫" || type === "收入") currentStockMap[bc] += qty;
      else currentStockMap[bc] -= qty;
    }
  });

  const masterData = masterSheet.getDataRange().getValues();
  const mHeaders = masterData[0];
  const colCat = mHeaders.indexOf('類別'), colBc = mHeaders.indexOf('品號'), colNm = mHeaders.indexOf('品名'), colSafe = mHeaders.indexOf('安全庫存');

  let rawCategories = {};
  for (let i = 1; i < masterData.length; i++) {
    let cat = masterData[i][colCat];
    if (cat) {
      let bc = masterData[i][colBc].toString().trim().replace(/^'/, '');
      let safe = parseFloat(masterData[i][colSafe]) || 0;
      let dynamicStock = currentStockMap[cleanString(bc)] || 0;
      if (!rawCategories[cat]) rawCategories[cat] = [];
      rawCategories[cat].push({ barcode: bc, name: masterData[i][colNm].toString().trim(), stock: dynamicStock, safe: safe });
    }
  }

  const customOrder = ["鴻勝新桶", "客供新桶", "特定原料", "回收桶", "成品", "其他包裝耗材"];
  let sortedArray = [];
  customOrder.forEach(cat => { if (rawCategories[cat]) { sortedArray.push({ title: cat, items: rawCategories[cat] }); delete rawCategories[cat]; } });
  for (let cat in rawCategories) { sortedArray.push({ title: cat, items: rawCategories[cat] }); }
  return sortedArray;
}

function getFormDropdownData() { 
  const masterSheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Inventory_Master"); 
  if (!masterSheet) return []; 
  const data = masterSheet.getDataRange().getValues(), headers = data[0]; 
  const colBc = headers.indexOf('品號'), colNm = headers.indexOf('品名'), colSp = headers.indexOf('規格'); 
  let items = []; 
  for (let i = 1; i < data.length; i++) { 
    if (data[i][colBc]) items.push({ barcode: data[i][colBc].toString().trim().replace(/^'/, ''), name: data[i][colNm].toString().trim(), spec: data[i][colSp] ? data[i][colSp].toString().trim() : "" }); 
  } 
  return items; 
}

function getSystemConfig() { 
  try { 
    const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("User_List"); 
    if (!sheet) return null; 
    return { emails: sheet.getRange("E2").getValue().toString().trim(), lineToken: sheet.getRange("F2").getValue().toString().trim(), lineUserId: sheet.getRange("G2").getValue().toString().trim() }; 
  } catch(e) { return null; } 
}

function sendLineBotMessage(message) { 
  const config = getSystemConfig(); 
  if (!config || !config.lineToken || !config.lineUserId) return; 
  const url = "https://api.line.me/v2/bot/message/push"; 
  const options = { "method": "post", "headers": { "Content-Type": "application/json", "Authorization": "Bearer " + config.lineToken }, "payload": JSON.stringify({ "to": config.lineUserId, "messages": [{ "type": "text", "text": message }] }), "muteHttpExceptions": true }; 
  try { UrlFetchApp.fetch(url, options); } catch (e) {} 
}

function sendEmailAlert(message, itemName) { 
  const config = getSystemConfig(); 
  if (!config || !config.emails) return; 
  const subject = `【鴻勝包材低庫存通知】品項：${itemName}`; 
  try { MailApp.sendEmail(config.emails, subject, message); } catch (e) {} 
}

function sendLowStockAlert() { 
  if (!isWorkDay()) return; 
  const currentStocks = getCategoryStockData(); 
  let alertList = []; 
  currentStocks.forEach(group => { group.items.forEach(item => { if (item.safe > 0 && item.stock < item.safe) alertList.push(`🔴 ${item.name} (剩餘: ${item.stock}, 安全: ${item.safe})`); }); }); 
  if (alertList.length > 0) { 
    let msg = "\n⚠️ 鴻勝低庫存巡檢警報：\n" + alertList.join("\n"); 
    sendLineBotMessage(msg); sendEmailAlert(msg, "全品項巡檢"); 
  } 
}

/**
 * 🤖 一鍵自動開帳機器人 (抓取所有成品分頁中，剩餘大於 0 的批號寫入 NSE_Log)
 */
function autoImportInitialStock() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const logSheet = ss.getSheetByName("NSE_Log");
  const masterSheet = ss.getSheetByName("Inventory_Master");
  
  if (!logSheet || !masterSheet) {
    SpreadsheetApp.getUi().alert("找不到 NSE_Log 或 Inventory_Master");
    return;
  }
  
  // 取得總目錄，用來對照 品名 -> 品號/規格
  const masterData = masterSheet.getDataRange().getValues();
  const mHeaders = masterData[0];
  const cBc = mHeaders.indexOf("品號"), cNm = mHeaders.indexOf("品名"), cSp = mHeaders.indexOf("規格");
  let masterMap = {};
  for(let i=1; i<masterData.length; i++) {
    if(masterData[i][cNm]) {
      masterMap[masterData[i][cNm].toString().trim()] = {
         bc: masterData[i][cBc].toString().trim().replace(/^'/, ''),
         sp: masterData[i][cSp] ? masterData[i][cSp].toString().trim() : ""
      };
    }
  }

  // 找出所有成品的分頁 (名稱包含 NSE 或 台積)
  const allSheets = ss.getSheets();
  let importCount = 0;
  let logsToAdd = [];
  
  for (let s = 0; s < allSheets.length; s++) {
    let sheet = allSheets[s];
    let sheetName = sheet.getName();
    
    // 如果分頁名稱包含 NSE 或 台積，就進行掃描
    if (sheetName.toUpperCase().includes("NSE") || sheetName.includes("台積")) {
      let data = sheet.getDataRange().getValues();
      if(data.length < 8) continue; 
      
      let itemInfo = masterMap[sheetName] || { bc: "未知", sp: "" };
      
      // 動態尋找 1數量~6數量 的欄位位置 (相容您不同格式的帳卡)
      let subHeaders = data[7]; // 第 8 列標題
      let inBatchCol = 3; // 預設 D 欄是入庫批號
      let inQtyCol = 4;   // 預設 E 欄是入庫數量
      let outQtyCols = [];
      
      for(let c = 6; c < subHeaders.length; c++) {
         let header = subHeaders[c] ? subHeaders[c].toString().trim() : "";
         if(header.includes("數量") && header.match(/\d/)) {
            outQtyCols.push(c);
         }
      }
      // 防呆：如果沒抓到標題，預設抓 H ~ M 欄
      if(outQtyCols.length === 0) outQtyCols = [7, 8, 9, 10, 11, 12]; 
      
      // 掃描第 9 列開始的所有明細
      for (let i = 8; i < data.length; i++) {
        let batch = data[i][inBatchCol] ? data[i][inBatchCol].toString().trim().replace(/^'/, '') : "";
        let income = parseFloat(data[i][inQtyCol]) || 0;
        if (!batch || income <= 0) continue; 
        
        let issueSum = 0;
        for (let idx of outQtyCols) {
           issueSum += parseFloat(data[i][idx]) || 0;
        }
        
        let remain = income - issueSum;
        // 如果這個批號還有庫存，做成期初開帳
        if (remain > 0) {
           let now = new Date();
           let newRowId = "L" + Utilities.formatDate(now, "GMT+8", "yyyyMMddHHmmss") + importCount;
           let dateStr = Utilities.formatDate(now, "GMT+8", "yyyy/MM/dd");
           
           logsToAdd.push([
             newRowId, dateStr, "'" + itemInfo.bc, sheetName, itemInfo.sp,
             "入庫", "'" + batch, remain, "資材組", "系統自動抓取期初開帳", "System"
           ]);
           importCount++;
        }
      }
    }
  }
  
  // 一次性寫入 NSE_Log
  if (logsToAdd.length > 0) {
     logSheet.getRange(logSheet.getLastRow() + 1, 1, logsToAdd.length, 11).setValues(logsToAdd);
     SpreadsheetApp.getUi().alert("✅ 太棒了！開帳完成！\n共幫您把 " + importCount + " 筆尚有庫存的批號，自動寫入 NSE_Log 囉！");
  } else {
     SpreadsheetApp.getUi().alert("⚠️ 沒有找到任何大於 0 的庫存可以匯入。");
  }
}

/**
 * 🌐 支援外部 PWA / API 呼叫 (JSON 接口)
 */
function doPost(e) {
  try {
    let req;
    if (e.postData && e.postData.contents) {
      req = JSON.parse(e.postData.contents);
    } else if (e.parameter) {
      req = e.parameter;
    } else {
      throw new Error("無效的請求資料");
    }

    const action = req.action;
    let result = null;

    if (action === 'verifyUser') {
      result = verifyUser(req.account, req.password);
    } else if (action === 'getCategoryStockData') {
      result = getCategoryStockData();
    } else if (action === 'getFormDropdownData') {
      result = getFormDropdownData();
    } else if (action === 'getItemBatches') {
      result = getItemBatches(req.barcode);
    } else if (action === 'queryAccountCard') {
      result = queryAccountCard(req.keyword, req.months);
    } else if (action === 'writeInventoryLog') {
      result = writeInventoryLog(req.data);
    } else {
      result = { error: "未知操作指令: " + action };
    }

    return ContentService.createTextOutput(JSON.stringify(result))
      .setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({ error: err.message }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}
