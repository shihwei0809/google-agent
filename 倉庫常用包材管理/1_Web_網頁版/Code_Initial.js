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
 * 📝 接收表單並寫入 Log (★★★ 雙軌制：原料特例 vs 一般包材 ★★★)
 */
function writeInventoryLog(data) {
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const logSheet = ss.getSheetByName("Inventory_Log");
    const masterSheet = ss.getSheetByName("Inventory_Master");
    if (!logSheet || !masterSheet) throw new Error("找不到資料庫分頁");

    const now = new Date();
    let itemName = "", itemSpec = "", safeStock = 0;

    const masterData = masterSheet.getDataRange().getValues();
    const mHeaders = masterData[0];
    const colBc = mHeaders.indexOf('品號'), colNm = mHeaders.indexOf('品名'), colSp = mHeaders.indexOf('規格'), colSafe = mHeaders.indexOf('安全庫存');

    const targetClean = cleanString(data.barcode);

    for (let i = 1; i < masterData.length; i++) {
      if (cleanString(masterData[i][colBc]) === targetClean) {
        itemName = masterData[i][colNm] || "";
        itemSpec = masterData[i][colSp] || "";
        safeStock = parseFloat(masterData[i][colSafe]) || 0;
        break;
      }
    }

    let finalDept = (data.type === "收入" || data.type === "入庫") ? "資材組" : data.dept;
    let finalBatch = data.batch ? data.batch.toString().trim() : "無批號";
    if (finalBatch === "") finalBatch = "無批號";

    const safeBarcode = "'" + data.barcode.toString().trim().replace(/^'/, '');
    const safeBatch = "'" + finalBatch.toString().trim().replace(/^'/, '');

    const newRowId = "L" + Utilities.formatDate(now, "GMT+8", "yyyyMMddHHmmss");
    const finalDate = data.date || Utilities.formatDate(now, "GMT+8", "yyyy/MM/dd HH:mm:ss");

    // 1. 寫入總表 Log
    const rowData = [newRowId, finalDate, safeBarcode, itemName, itemSpec, data.type, safeBatch, data.qty, finalDept, data.remark, data.user];
    logSheet.appendRow(rowData);
    SpreadsheetApp.flush();

    const currentStock = calculateSingleItemStock(data.barcode);
    
    // ========================================================
    // 🆕 帳卡寫入邏輯
    const itemSheet = ss.getSheetByName(itemName);
    let alertMissingSheet = ""; 
    
    if (itemSheet) {
      // ★ 判斷是否為「特定原料」
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
             if (sheetData[i][2] !== "" || sheetData[i][3] !== "") { lastRow = i + 1; break; }
          }
          let targetRow = lastRow + 1;
          
          itemSheet.getRange(targetRow, 1).setValue(d.getMonth() + 1);
          itemSheet.getRange(targetRow, 2).setValue(d.getDate());
          itemSheet.getRange(targetRow, 3).setValue(safeBatch);
          itemSheet.getRange(targetRow, 4).setValue(data.qty);
          if (data.remark) itemSheet.getRange(targetRow, 5).setValue(data.remark);
          // ★ L 欄結存不寫入，保留公式！
          
        } else {
          // 出庫：尋找該批號並填入 1~5 數量
          let targetRow = -1;
          let targetIssueIndex = -1; // 0~4 代表 1~5次
          
          for (let i = 7; i < sheetData.length; i++) {
             let rowBatch = sheetData[i][2] ? sheetData[i][2].toString().trim().replace(/^'/, '') : "";
             if (rowBatch === finalBatch.replace(/^'/, '')) {
                // 檢查 F(5)~J(9) 是否有空位
                for (let slot = 0; slot < 5; slot++) {
                   if (sheetData[i][5 + slot] === "") {
                      targetRow = i + 1; targetIssueIndex = slot; break;
                   }
                }
                if (targetRow !== -1) break; // 找到了空位！
             }
          }
          
          if (targetRow === -1) return `❌ 寫入失敗：找不到批號「${finalBatch}」，或該批號的 5 次出貨已全滿！`;
          
          // 寫入數量到對應的 F~J 欄 (索引 6~10)
          itemSheet.getRange(targetRow, 6 + targetIssueIndex).setValue(data.qty);
          
          // 寫入出貨日期到對應的 N~R 欄 (索引 14~18)
          let dateStr = (d.getMonth() + 1) + "/" + d.getDate();
          itemSheet.getRange(targetRow, 14 + targetIssueIndex).setValue(dateStr);
          
          // 若有備註，附加到 E 欄 (入庫備註下方)
          if (data.remark) {
             let oldRemark = sheetData[targetRow - 1][4] ? sheetData[targetRow - 1][4].toString() : "";
             let newRemark = oldRemark ? (oldRemark + "\n" + data.remark) : data.remark;
             itemSheet.getRange(targetRow, 5).setValue(newRemark);
          }
        }
      } else {
        // 🌟🌟🌟【一般包材 自動對位/新增欄位邏輯】🌟🌟🌟
        let month = d.getMonth() + 1, day = d.getDate();        
        let summary = finalDept ? (data.type + "-" + finalDept) : data.type; 
        let isIssue = (data.type !== "入庫" && data.type !== "收入");
        
        let topHeaders = itemSheet.getRange(6, 1, 1, itemSheet.getLastColumn()).getValues()[0];
        let subHeaders = itemSheet.getRange(8, 1, 1, itemSheet.getLastColumn()).getValues()[0];
        let subHeadersClean = subHeaders.map(h => h.toString().trim());
        
        // 【自動新增欄位】
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
    // ========================================================

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
 * 🧮 計算最新庫存
 */
function calculateSingleItemStock(barcode) {
  const logSheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Inventory_Log");
  const data = logSheet.getDataRange().getValues();
  const headers = data[0];
  const cBc = headers.indexOf('品號'), cType = headers.indexOf('類型(進/出)'), cQty = headers.indexOf('數量');
  
  let targetClean = cleanString(barcode);
  let balance = 0;
  
  for (let i = 1; i < data.length; i++) {
    if (cleanString(data[i][cBc]) === targetClean) {
      let qty = parseFloat(data[i][cQty]) || 0;
      if (data[i][cType] === "收入" || data[i][cType] === "入庫") balance += qty;
      else balance -= qty;
    }
  }
  return balance;
}

/**
 * 🔍 獲取批號庫存 (★ 新增：計算已發出次數)
 */
function getItemBatches(barcode) { 
  if (!barcode) return []; 
  const logSheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Inventory_Log"); 
  if (!logSheet) return []; 
  const data = logSheet.getDataRange().getValues(), headers = data[0]; 
  const cBc = headers.indexOf('品號'), cType = headers.indexOf('類型(進/出)'), cBatch = headers.indexOf('批號'), cQty = headers.indexOf('數量'); 
  
  let batchesMap = {}; 
  let issueCountMap = {}; // 追蹤出庫次數

  for(let i = 1; i < data.length; i++) { 
    if (data[i][cBc] && cleanString(data[i][cBc]) === cleanString(barcode)) { 
      let b = data[i][cBatch] ? data[i][cBatch].toString().trim().replace(/^'/, '') : "無批號"; 
      let type = data[i][cType] ? data[i][cType].toString().trim() : "";
      let qty = parseFloat(data[i][cQty]) || 0; 
      
      if(!batchesMap[b]) { batchesMap[b] = 0; issueCountMap[b] = 0; }
      
      if(type === "入庫" || type === "收入") {
        batchesMap[b] += qty; 
      } else { 
        batchesMap[b] -= qty; 
        issueCountMap[b] += 1; // ★ 記錄該批號被發出的次數
      } 
    } 
  } 
  
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
 * 📊 查詢歷史帳卡核心
 */
function queryAccountCard(keyword, months) { 
  if (!keyword) return []; 
  const ss = SpreadsheetApp.getActiveSpreadsheet(); 
  const logSheet = ss.getSheetByName("Inventory_Log"); 
  if (!logSheet) return []; 
  
  const logs = logSheet.getDataRange().getValues();
  const headers = logs[0]; 
  const colDate = headers.indexOf('日期'), colItemCode = headers.indexOf('品號'), colType = headers.indexOf('類型(進/出)'), colBatch = headers.indexOf('批號'), colQty = headers.indexOf('數量'), colDept = headers.indexOf('領用單位'), colRemark = headers.indexOf('備註'); 
  
  let matchedItems = getMatchedItems(keyword); 
  if (matchedItems.length === 0) return []; 
  
  let cutoffDate = new Date(); 
  if (months > 0) { cutoffDate.setMonth(cutoffDate.getMonth() - parseInt(months)); cutoffDate.setHours(0, 0, 0, 0); } 
  else { cutoffDate = new Date(2000, 0, 1); } 
  
  let allResults = []; 
  for (let j = 0; j < matchedItems.length; j++) { 
    let item = matchedItems[j], history = [], balance = 0, carryForward = 0;
    let targetClean = cleanString(item.barcode); 
    
    for (let i = 1; i < logs.length; i++) { 
      if (colItemCode === -1 || !logs[i][colItemCode]) continue; 
      
      if (cleanString(logs[i][colItemCode]) === targetClean) { 
        let logDate = new Date(logs[i][colDate]), 
            type = logs[i][colType] ? logs[i][colType].toString().trim() : "", 
            batch = logs[i][colBatch] ? logs[i][colBatch].toString().trim().replace(/^'/, '') : "", 
            qty = parseFloat(logs[i][colQty]) || 0, 
            dept = logs[i][colDept] ? logs[i][colDept].toString().trim() : "", 
            remark = logs[i][colRemark] ? logs[i][colRemark].toString().trim() : "";        
        
        if (type === "入庫" || type === "收入") balance += qty; 
        else balance -= qty; 
        
        if (logDate < cutoffDate) { 
          carryForward = balance; 
        } else { 
          let in_qty = "", in_batch = "", out_mat = "", out_p1 = "", out_p2 = "", out_prod = "", out_batch = ""; 
          let summary = dept ? (type + "-" + dept) : type; 
          if (type === "入庫" || type === "收入") { in_qty = qty; in_batch = batch; } 
          else { 
            out_batch = batch; 
            if (dept.indexOf("資材") > -1) out_mat = qty; 
            else if (dept.indexOf("分一") > -1) out_p1 = qty; 
            else if (dept.indexOf("分二") > -1) out_p2 = qty; 
            else if (dept.indexOf("生產") > -1) out_prod = qty; 
            else out_mat = qty; 
          } 
          history.push({ 
            date: Utilities.formatDate(logDate, "GMT+8", "MM/dd"), 
            summary: summary, in_qty: in_qty, in_batch: in_batch, 
            out_mat: out_mat, out_p1: out_p1, out_p2: out_p2, out_prod: out_prod, 
            out_batch: out_batch, balance: balance, remark: remark 
          }); 
        } 
      } 
    } 
    if (months > 0) history.unshift({ date: "期初", summary: "上期轉入", in_qty: "", in_batch: "", out_mat: "", out_p1: "", out_p2: "", out_prod: "", out_batch: "", balance: carryForward, remark: "" }); 
    allResults.push({ details: item, history: history }); 
  } 
  return allResults; 
}

function getCategoryStockData() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const masterSheet = ss.getSheetByName("Inventory_Master");
  const logSheet = ss.getSheetByName("Inventory_Log");
  const logData = logSheet.getDataRange().getValues();
  const lHeaders = logData[0];
  const lColBc = lHeaders.indexOf('品號'), lColType = lHeaders.indexOf('類型(進/出)'), lColQty = lHeaders.indexOf('數量');

  let currentStockMap = {}; 
  for (let i = 1; i < logData.length; i++) {
    if (!logData[i][lColBc]) continue;
    let bc = cleanString(logData[i][lColBc]);
    let type = logData[i][lColType], qty = parseFloat(logData[i][lColQty]) || 0;
    if (!currentStockMap[bc]) currentStockMap[bc] = 0;
    if (type === "入庫" || type === "收入") currentStockMap[bc] += qty;
    else currentStockMap[bc] -= qty;
  }

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

  const customOrder = ["鴻勝新桶", "客供新桶", "特定原料", "回收桶", "其他包裝耗材"];
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

