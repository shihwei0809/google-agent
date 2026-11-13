// ==========================================
// 1. 系統核心設定區 (請在此替換您的專屬三大金鑰)
// ==========================================
var LINE_ACCESS_TOKEN = '您的_LINE_CHANNEL_ACCESS_TOKEN';
var GEMINI_API_KEY = '您的_GOOGLE_GEMINI_API_KEY';
var SHEET_ID = '您的_GOOGLE_SPREADSHEET_ID'; 

// 核心大腦配置 (支援多模型自動降級備援)
var GEMINI_MODEL = "gemini-3.8-flash";
var GEMINI_FALLBACK_MODELS = [GEMINI_MODEL, "gemini-3.7-flash", "gemini-3.6-flash", "gemini-2.5-flash", "gemini-flash-latest"];

// 每日建議攝取量基準 (參考衛福部國健署成人每日參考值 2000 大卡基準，可依個人需求調整)
var DAILY_TARGETS = {
  calories:      { label: "熱量",       unit: "大卡", target: 2000, icon: "🔥", decimals: 0 },
  protein:       { label: "蛋白質",     unit: "g",    target: 60,   icon: "🥩", decimals: 1 },
  fat:           { label: "脂肪",       unit: "g",    target: 60,   icon: "🥑", decimals: 1 },
  saturated_fat: { label: "飽和脂肪",   unit: "g",    target: 18,   icon: "🧈", decimals: 1 },
  trans_fat:     { label: "反式脂肪",   unit: "g",    target: 2,    icon: "⚠️", decimals: 1 },
  carbs:         { label: "碳水化合物", unit: "g",    target: 300,  icon: "🍚", decimals: 1 },
  sugar:         { label: "糖",         unit: "g",    target: 50,   icon: "🍬", decimals: 1 },
  fiber:         { label: "膳食纖維",   unit: "g",    target: 25,   icon: "🥬", decimals: 1 },
  sodium:        { label: "鈉",         unit: "mg",   target: 2000, icon: "🧂", decimals: 0 }
};

function fetchGeminiWithFallback(payloadObj) {
  var lastErr = "";
  for (var i = 0; i < GEMINI_FALLBACK_MODELS.length; i++) {
    var m = GEMINI_FALLBACK_MODELS[i];
    if (!m) continue;
    var apiUrl = "https://generativelanguage.googleapis.com/v1beta/models/" + m + ":generateContent?key=" + GEMINI_API_KEY;
    try {
      var res = UrlFetchApp.fetch(apiUrl, {
        "method": "post",
        "contentType": "application/json",
        "payload": JSON.stringify(payloadObj),
        "muteHttpExceptions": true
      });
      if (res.getResponseCode() === 200) {
        return res;
      }
      lastErr = "HTTP " + res.getResponseCode() + ": " + res.getContentText();
    } catch (e) {
      lastErr = e.toString();
    }
  }
  throw new Error("所有 Gemini 備援模型皆呼叫失敗: " + lastErr);
}

// ==========================================
// 2. Webhook 主要入口門戶 (doPost)
// ==========================================
function doPost(e) {
  var replyToken = "";
  try {
    var contents = JSON.parse(e.postData.contents);
    var event = contents.events[0];
    replyToken = event.replyToken;
    var userId = event.source.userId;
    var userName = getUserProfile(userId);

    // 【文字訊息流處理】
    if (event.message.type === 'text') {
      var userMsg = event.message.text.trim();
      
      if (userMsg.includes("本月") || userMsg.includes("月統計")) {
        replyMessage(replyToken, queryMonthlyNutrition(userName));
      } 
      else if (userMsg.includes("今天") || userMsg.includes("統計") || userMsg.includes("今日")) {
        replyMessage(replyToken, queryTodayNutrition(userName));
      } 
      else if (userMsg.startsWith("設定目標")) {
        replyMessage(replyToken, handleSetTargets(userName, userMsg));
      }
      else if (userMsg.includes("修正") || userMsg.includes("不對") || userMsg.includes("改")) {
        handleAdvancedCorrection(replyToken, userName, userMsg);
      }
      else {
        replyMessage(replyToken, "🔍 " + userName + " 您好！\n• 直接傳食物照片：AI 自動辨識完整營養標示並累積今日進度\n• 輸入「今天統計」：看今日飲食清單與各營養素剩餘額度\n• 輸入「本月統計」：看本月累積營養報表\n• 輸入「修正第 X 餐：[修正內容]」：重算並覆蓋舊紀錄\n• 輸入「設定目標 熱量 1800 鈉 1500」：自訂每日建議攝取量");
      }
    }

    // 【影像訊息流處理】
    if (event.message.type === 'image') {
      var imageBlob = getLineImage(event.message.id);
      var base64Image = Utilities.base64Encode(imageBlob.getBytes());
      var nutritionData = analyzeFoodWithGemini(base64Image, imageBlob.getContentType());
      if (nutritionData) {
        writeToUserSheet(nutritionData, userName, -1);
        var todayTotals = getTodayTotals(userName);
        var userTargets = getUserTargets(userName);
        replyMessage(replyToken, "✅ 辨識完成並已記錄！\n" + formatNutritionText(nutritionData, todayTotals, userTargets));
      }
    }
  } catch (error) {
    if (replyToken) replyMessage(replyToken, "⚠️ 系統診斷報告：\n" + error.toString());
  }
  return ContentService.createTextOutput("OK");
}

// ==========================================
// 3. 高階 AI 修正與統計報表核心邏輯
// ==========================================

// 進階修正模組：智慧比對今日特定餐點並強制重置數值
function handleAdvancedCorrection(replyToken, userName, userMsg) {
  var ss = SpreadsheetApp.openById(SHEET_ID);
  var sheet = ss.getSheetByName(userName);
  if (!sheet || sheet.getLastRow() < 2) { replyMessage(replyToken, "尚未有任何歷史紀錄，無法執行修正。"); return; }

  var targetNum = 0;
  var numMatch = userMsg.match(/第\s*(\d+)\s*餐/);
  if (numMatch) targetNum = parseInt(numMatch[1]);

  var rows = sheet.getDataRange().getValues();
  var today = new Date(); today.setHours(0,0,0,0);
  var todayRowIndices = [];
  for (var i = 1; i < rows.length; i++) {
    var d = new Date(rows[i][0]); d.setHours(0,0,0,0);
    if (d.getTime() === today.getTime()) todayRowIndices.push(i + 1);
  }

  // 若未指定第幾餐，預設為今日最後一餐
  var targetRowIndex = (targetNum > 0 && targetNum <= todayRowIndices.length) 
                       ? todayRowIndices[targetNum - 1] 
                       : todayRowIndices[todayRowIndices.length - 1];

  if (!targetRowIndex) { replyMessage(replyToken, "找不到該序號的紀錄，請先傳送「今天統計」核對編號。"); return; }

  var oldText = sheet.getRange(targetRowIndex, 2).getValue();
  var prompt = "你是專業營養師。請修正以下餐點。原本內容：「" + oldText + "」。使用者提出的修正指令：「" + userMsg + "」。請重新估算每項食物熱量與完整營養標示，以 JSON 格式回傳，熱量與主要營養素嚴禁無故設為 0。格式：{\"items\": [{\"name\": \"食物名\", \"calories\": 數值}], \"total_calories\": 數值, \"total_carbs\": 數值, \"total_protein\": 數值, \"total_fat\": 數值, \"total_saturated_fat\": 數值, \"total_trans_fat\": 數值, \"total_sugar\": 數值, \"total_fiber\": 數值, \"total_sodium\": 數值}";
  
  var response = fetchGeminiWithFallback({
    "contents": [{"parts": [{"text": prompt}]}],
    "generationConfig": {"responseMimeType": "application/json"}
  });
  
  var rawText = JSON.parse(response.getContentText()).candidates[0].content.parts[0].text;
  var correctedData = JSON.parse(rawText.replace(/```json/g, "").replace(/```/g, "").trim());

  writeToUserSheet(correctedData, userName, targetRowIndex);
  var todayTotals = getTodayTotals(userName);
  var userTargets = getUserTargets(userName);
  replyMessage(replyToken, "🛠️ 修正成功！已同步重算營養標示與今日累積：\n" + formatNutritionText(correctedData, todayTotals, userTargets));
}

// 取得使用者每日建議目標 (含個人化覆寫)
function getUserTargets(userName) {
  var targets = JSON.parse(JSON.stringify(DAILY_TARGETS));
  try {
    var saved = PropertiesService.getScriptProperties().getProperty("TARGETS_" + userName);
    if (saved) {
      var overrides = JSON.parse(saved);
      for (var k in overrides) {
        if (targets[k]) targets[k].target = Number(overrides[k]);
      }
    }
  } catch (e) {}
  return targets;
}

// 透過 LINE 指令設定個人每日建議目標 (例：設定目標 熱量 1800 鈉 1500)
function handleSetTargets(userName, userMsg) {
  var aliasMap = {
    "熱量": "calories", "卡路里": "calories",
    "蛋白": "protein", "蛋白質": "protein",
    "脂肪": "fat",
    "飽和脂肪": "saturated_fat",
    "反式脂肪": "trans_fat",
    "碳水": "carbs", "碳水化合物": "carbs",
    "糖": "sugar",
    "纖維": "fiber", "膳食纖維": "fiber",
    "鈉": "sodium"
  };
  var props = PropertiesService.getScriptProperties();
  var saved = {};
  try {
    var existing = props.getProperty("TARGETS_" + userName);
    if (existing) saved = JSON.parse(existing);
  } catch (e) {}

  var updated = [];
  var regex = /(熱量|卡路里|蛋白質|蛋白|飽和脂肪|反式脂肪|脂肪|碳水化合物|碳水|膳食纖維|纖維|糖|鈉)\s*[:：]?\s*(\d+(?:\.\d+)?)/g;
  var match;
  while ((match = regex.exec(userMsg)) !== null) {
    var key = aliasMap[match[1]];
    var val = Number(match[2]);
    if (key && val > 0) {
      saved[key] = val;
      updated.push(DAILY_TARGETS[key].label + " → " + val + " " + DAILY_TARGETS[key].unit);
    }
  }
  if (updated.length === 0) {
    return "⚙️ 自訂每日建議量格式：\n請輸入「設定目標 熱量 1800 蛋白質 70 鈉 1500」\n支援項目：熱量、蛋白質、脂肪、飽和脂肪、反式脂肪、碳水化合物、糖、膳食纖維、鈉";
  }
  props.setProperty("TARGETS_" + userName, JSON.stringify(saved));
  return "✅ 已為 " + userName + " 更新每日建議目標：\n• " + updated.join("\n• ");
}

// 計算今日各項營養素累積總和
function getTodayTotals(userName) {
  var totals = { calories: 0, carbs: 0, protein: 0, fat: 0, saturated_fat: 0, trans_fat: 0, sugar: 0, fiber: 0, sodium: 0 };
  var ss = SpreadsheetApp.openById(SHEET_ID);
  var sheet = ss.getSheetByName(userName);
  if (!sheet || sheet.getLastRow() < 2) return totals;
  var rows = sheet.getDataRange().getValues();
  var today = new Date(); today.setHours(0,0,0,0);
  for (var i = 1; i < rows.length; i++) {
    var d = new Date(rows[i][0]); d.setHours(0,0,0,0);
    if (d.getTime() === today.getTime()) {
      totals.calories      += Number(rows[i][2]  || 0);
      totals.carbs         += Number(rows[i][3]  || 0);
      totals.protein       += Number(rows[i][4]  || 0);
      totals.fat           += Number(rows[i][5]  || 0);
      totals.saturated_fat += Number(rows[i][6]  || 0);
      totals.trans_fat     += Number(rows[i][7]  || 0);
      totals.sugar         += Number(rows[i][8]  || 0);
      totals.fiber         += Number(rows[i][9]  || 0);
      totals.sodium        += Number(rows[i][10] || 0);
    }
  }
  return totals;
}

// 產生「已吸收 / 每日建議（剩餘 / 超標）」對照文字
function formatDailyProgress(totals, targets) {
  var keys = ["calories", "protein", "fat", "saturated_fat", "trans_fat", "carbs", "sugar", "fiber", "sodium"];
  var lines = [];
  for (var i = 0; i < keys.length; i++) {
    var k = keys[i];
    var cfg = targets[k];
    var absorbed = Number(totals[k] || 0);
    var target = Number(cfg.target || 0);
    var diff = target - absorbed;
    var dec = cfg.decimals;
    var statusText = diff >= 0
      ? "剩餘 " + diff.toFixed(dec) + " " + cfg.unit
      : "⚠️ 超標 +" + Math.abs(diff).toFixed(dec) + " " + cfg.unit;
    lines.push(cfg.icon + " " + cfg.label + "：" + absorbed.toFixed(dec) + " / " + target.toFixed(dec) + " " + cfg.unit + "（" + statusText + "）");
  }
  return lines.join("\n");
}

// 今日明細與完整營養累積統計
function queryTodayNutrition(userName) {
  var ss = SpreadsheetApp.openById(SHEET_ID);
  var sheet = ss.getSheetByName(userName);
  if (!sheet) return "🔍 尚未找到您的飲食資料庫。";
  var rows = sheet.getDataRange().getValues();
  var today = new Date(); today.setHours(0,0,0,0);
  var count = 0, list = "";
  for (var i = 1; i < rows.length; i++) {
    var d = new Date(rows[i][0]); d.setHours(0,0,0,0);
    if (d.getTime() === today.getTime()) {
      count++;
      list += "\n🍴 填報編號 [" + count + "]：\n" + rows[i][1] + "\n";
    }
  }
  if (count === 0) return "📅 您今天尚未上傳任何食物照片喔！";
  var totals = getTodayTotals(userName);
  var targets = getUserTargets(userName);
  return "📅 " + userName + " 的今日飲食清單：\n" + list +
         "\n------------------\n" +
         "📊 【今日累積 vs 每日建議 (剩餘)】\n" +
         formatDailyProgress(totals, targets);
}

// 本月加總趨勢與天數均值計算
function queryMonthlyNutrition(userName) {
  var ss = SpreadsheetApp.openById(SHEET_ID);
  var sheet = ss.getSheetByName(userName);
  if (!sheet) return "🔍 尚未找到您的飲食資料庫。";
  var rows = sheet.getDataRange().getValues();
  var now = new Date();
  var tCal = 0, tCarb = 0, tProt = 0, tFat = 0, tSat = 0, tTrans = 0, tSugar = 0, tFiber = 0, tSodium = 0;
  var count = 0, days = {};
  for (var i = 1; i < rows.length; i++) {
    var d = new Date(rows[i][0]);
    if (d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear()) {
      count++;
      tCal    += Number(rows[i][2]  || 0);
      tCarb   += Number(rows[i][3]  || 0);
      tProt   += Number(rows[i][4]  || 0);
      tFat    += Number(rows[i][5]  || 0);
      tSat    += Number(rows[i][6]  || 0);
      tTrans  += Number(rows[i][7]  || 0);
      tSugar  += Number(rows[i][8]  || 0);
      tFiber  += Number(rows[i][9]  || 0);
      tSodium += Number(rows[i][10] || 0);
      days[d.toDateString()] = true;
    }
  }
  if (count === 0) return "📅 您本月份尚未有任何紀錄。";
  var dCount = Object.keys(days).length;
  return "📊 " + userName + " 本月營養累積報表\n" +
         "📅 統計月份：" + (now.getMonth() + 1) + "月\n" +
         "--------------------------\n" +
         "🔥 總熱量：" + tCal.toFixed(0) + " 大卡\n" +
         "🥩 總蛋白質：" + tProt.toFixed(1) + " g\n" +
         "🥑 總脂肪：" + tFat.toFixed(1) + " g（飽和 " + tSat.toFixed(1) + " g / 反式 " + tTrans.toFixed(1) + " g）\n" +
         "🍚 總碳水：" + tCarb.toFixed(1) + " g（糖 " + tSugar.toFixed(1) + " g）\n" +
         "🥬 總膳食纖維：" + tFiber.toFixed(1) + " g\n" +
         "🧂 總鈉：" + tSodium.toFixed(0) + " mg\n" +
         "--------------------------\n" +
         "📈 週期平均數據：\n" +
         "• 有紀錄的天數：" + dCount + " 天\n" +
         "• 每日平均熱量：" + (tCal/dCount).toFixed(0) + " 大卡\n" +
         "• 每日平均鈉：" + (tSodium/dCount).toFixed(0) + " mg";
}

// ==========================================
// 4. 底層基礎工具箱 (資料庫寫入、API 請求)
// ==========================================

function writeToUserSheet(data, userName, rowIndex) {
  var ss = SpreadsheetApp.openById(SHEET_ID);
  var sheet = ss.getSheetByName(userName) || ss.insertSheet(userName);
  var headers = ["時間戳記", "食物明細", "總熱量", "碳水(g)", "蛋白(g)", "脂肪(g)", "飽和脂肪(g)", "反式脂肪(g)", "糖(g)", "膳食纖維(g)", "鈉(mg)"];
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(headers);
    sheet.getRange(1, 1, 1, headers.length).setFontWeight("bold");
  } else if (sheet.getLastColumn() < headers.length) {
    // 舊版試算表自動補齊新營養標示欄位標題，保留歷史紀錄
    sheet.getRange(1, 1, 1, headers.length).setValues([headers]).setFontWeight("bold");
  }
  
  var detail = (data.items && Array.isArray(data.items)) 
    ? data.items.map(function(i){return i.name + " (" + (i.calories || 0) + "大卡)"}).join("\n") 
    : "無明細數據";

  var rowData = [
    new Date(), 
    detail.toString(), 
    Number(data.total_calories || 0), 
    Number(data.total_carbs || 0), 
    Number(data.total_protein || 0), 
    Number(data.total_fat || 0),
    Number(data.total_saturated_fat || 0),
    Number(data.total_trans_fat || 0),
    Number(data.total_sugar || 0),
    Number(data.total_fiber || 0),
    Number(data.total_sodium || 0)
  ];

  if (rowIndex > 1) {
    sheet.getRange(rowIndex, 1, 1, headers.length).setValues([rowData]);
  } else {
    sheet.appendRow(rowData);
  }
}

function analyzeFoodWithGemini(base64Image, mimeType) {
  var prompt = "你是一位頂尖的營養師。請用視覺精準分析照片。獨立拆解菜色（必須使用純繁體中文），並根據份量合理估計熱量與完整台灣營養標示（熱量、碳水化合物、蛋白質、脂肪、飽和脂肪、反式脂肪、糖、膳食纖維、鈉，嚴禁將熱量或主要營養素隨意回傳 0）。請絕對以完整 JSON 回傳：{\"items\": [{\"name\": \"食物名\", \"calories\": 數值}], \"total_calories\": 數值, \"total_carbs\": 數值, \"total_protein\": 數值, \"total_fat\": 數值, \"total_saturated_fat\": 數值, \"total_trans_fat\": 數值, \"total_sugar\": 數值, \"total_fiber\": 數值, \"total_sodium\": 數值}";
  var response = fetchGeminiWithFallback({
    "contents": [{"parts": [{"text": prompt}, {"inline_data": {"mime_type": mimeType, "data": base64Image}}]}],
    "generationConfig": {"responseMimeType": "application/json"}
  });
  var rawText = JSON.parse(response.getContentText()).candidates[0].content.parts[0].text;
  return JSON.parse(rawText.replace(/```json/g, "").replace(/```/g, "").trim());
}

function formatNutritionText(data, todayTotals, userTargets) {
  var itemsText = (data.items && Array.isArray(data.items)) 
    ? data.items.map(function(i){return "🔸 " + i.name + "：" + (i.calories || 0) + " 大卡"}).join("\n") 
    : "無細節";
  var mealText = "------------------\n" + itemsText +
         "\n------------------\n" +
         "📋 【本餐營養標示】\n" +
         "🔥 熱量：" + Number(data.total_calories || 0).toFixed(0) + " 大卡\n" +
         "🥩 蛋白質：" + Number(data.total_protein || 0).toFixed(1) + " g\n" +
         "🥑 脂肪：" + Number(data.total_fat || 0).toFixed(1) + " g（飽和 " + Number(data.total_saturated_fat || 0).toFixed(1) + " g / 反式 " + Number(data.total_trans_fat || 0).toFixed(1) + " g）\n" +
         "🍚 碳水化合物：" + Number(data.total_carbs || 0).toFixed(1) + " g（糖 " + Number(data.total_sugar || 0).toFixed(1) + " g）\n" +
         "🥬 膳食纖維：" + Number(data.total_fiber || 0).toFixed(1) + " g\n" +
         "🧂 鈉：" + Number(data.total_sodium || 0).toFixed(0) + " mg";
  if (todayTotals && userTargets) {
    mealText += "\n------------------\n📊 【今日累積 vs 每日建議 (剩餘)】\n" + formatDailyProgress(todayTotals, userTargets);
  }
  return mealText;
}

function getUserProfile(userId) {
  try { 
    var response = UrlFetchApp.fetch("https://api.line.me/v2/bot/profile/" + userId, {"headers": {"Authorization": "Bearer " + LINE_ACCESS_TOKEN}});
    return JSON.parse(response.getContentText()).displayName; 
  } catch (e) { return "外部使用者"; }
}

function getLineImage(messageId) {
  return UrlFetchApp.fetch('https://api-data.line.me/v2/bot/message/' + messageId + '/content', {"headers": {"Authorization": "Bearer " + LINE_ACCESS_TOKEN}}).getBlob();
}

function replyMessage(replyToken, text) {
  UrlFetchApp.fetch('https://api.line.me/v2/bot/message/reply', {
    "method": "post", "headers": {"Authorization": "Bearer " + LINE_ACCESS_TOKEN}, "contentType": "application/json",
    "payload": JSON.stringify({"replyToken": replyToken, "messages": [{"type": "text", "text": text}]})
  });
}