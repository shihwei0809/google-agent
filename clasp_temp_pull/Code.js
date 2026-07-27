/**
 * 網頁伺服器入口
 */
function doGet() {
  var template = HtmlService.createTemplateFromFile('Index');
  try {
    template.skincareData = getSkincareData();
  } catch (e) {
    template.skincareData = { error: e.toString() };
  }
  return template.evaluate().setTitle('AI個人保養網站 V7 | 試算表與 Gemini 整合版').addMetaTag('viewport', 'width=device-width, initial-scale=1.0').setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

/**
 * 取得試算表中所有分頁的資料
 */
function getSkincareData() {
  var ss = SpreadsheetApp.openById("1Ee2l-BAw5BCc_WThJHuJN2cAtPS5f68m-k6Yrxi_lI0");
  
  // 如果試算表是空的，先進行初始化
  if (ss.getSheets().length === 1 && ss.getSheets()[0].getLastRow() === 0) {
    setupSheets();
  }
  
  var data = {
    summary: getSheetDataAsObjects(ss.getSheetByName("Summary")),
    products: getSheetDataAsObjects(ss.getSheetByName("Products")),
    instructions: getSheetDataAsObjects(ss.getSheetByName("Instructions")),
    routines: getSheetDataAsObjects(ss.getSheetByName("Routines")),
    sunscreens: getSheetDataAsObjects(ss.getSheetByName("Sunscreens")),
    avoidRules: getSheetDataAsObjects(ss.getSheetByName("AvoidRules")),
    dupes: getSheetDataAsObjects(ss.getSheetByName("Dupes"))
  };
  return data;
}

/**
 * 將指定的 Sheet 轉換為對象陣列 (第一列為 Key)
 */
function getSheetDataAsObjects(sheet) {
  if (!sheet) return [];
  var lastRow = sheet.getLastRow();
  var lastColumn = sheet.getLastColumn();
  if (lastRow < 2 || lastColumn < 1) return [];
  
  var range = sheet.getRange(1, 1, lastRow, lastColumn);
  var values = range.getValues();
  var headers = values[0];
  var objects = [];
  
  for (var i = 1; i < values.length; i++) {
    var obj = {};
    for (var j = 0; j < headers.length; j++) {
      obj[headers[j]] = values[i][j];
    }
    objects.push(obj);
  }
  return objects;
}

/**
 * 呼叫 Gemini API 進行諮詢
 */
function askGemini(userQuestion) {
  var ss = SpreadsheetApp.openById("1Ee2l-BAw5BCc_WThJHuJN2cAtPS5f68m-k6Yrxi_lI0");
  var configSheet = ss.getSheetByName("Config");
  var apiKey = "";
  var modelName = "gemini-2.5-flash";
  
  if (configSheet) {
    var data = getSheetDataAsObjects(configSheet);
    for (var i = 0; i < data.length; i++) {
      if (data[i].Key === "GEMINI_API_KEY") apiKey = data[i].Value;
      if (data[i].Key === "GEMINI_MODEL") modelName = data[i].Value || modelName;
    }
  }
  
  if (!apiKey || apiKey === "請輸入你的金鑰") {
    return "⚠️ 系統尚未設定 Gemini API 金鑰，請在試算表的 'Config' 工作表中填入您的 API 金鑰。";
  }
  
  // 彙整資料庫內容作為上下文
  var context = getSkincareContextSummary();
  var systemInstruction = "你是一位專業的個人皮膚保養顧問。你擁有用戶目前的保養品資料庫、使用方法、早晚流程以及防曬比較表。\n" +
                          "請根據以下資料庫內容，親切、專業、簡短地回答用戶的保養問題。\n" +
                          "當用戶的皮膚有紅腫、刺痛、脫皮等敏感情況時，必須依據避雷規則，主動警告他們暫停使用酸類、A醛、高濃度維C等功效型產品，並建議以修護為主的流程。\n\n" +
                          "【保養品資料庫內容如下】\n" + context;
  
  var url = "https://generativelanguage.googleapis.com/v1beta/models/" + modelName + ":generateContent?key=" + apiKey;
  
  var payload = {
    "contents": [
      {
        "role": "user",
        "parts": [{"text": userQuestion}]
      }
    ],
    "systemInstruction": {
      "parts": [{"text": systemInstruction}]
    },
    "generationConfig": {
      "temperature": 0.3,
      "maxOutputTokens": 1000
    }
  };
  
  var options = {
    "method": "post",
    "contentType": "application/json",
    "payload": JSON.stringify(payload),
    "muteHttpExceptions": true
  };
  
  try {
    var response = UrlFetchApp.fetch(url, options);
    var responseCode = response.getResponseCode();
    var responseText = response.getContentText();
    var json = JSON.parse(responseText);
    
    if (responseCode === 200) {
      if (json.candidates && json.candidates[0] && json.candidates[0].content && json.candidates[0].content.parts[0]) {
        return json.candidates[0].content.parts[0].text;
      }
      return "AI 沒有返回內容，請稍後再試。";
    } else {
      return "❌ AI 呼叫失敗，狀態碼: " + responseCode + "。錯誤原因: " + (json.error ? json.error.message : responseText);
    }
  } catch (e) {
    return "❌ 連線失敗: " + e.toString();
  }
}

/**
 * 彙整試算表資料為文字摘要
 */
function getSkincareContextSummary() {
  var ss = SpreadsheetApp.openById("1Ee2l-BAw5BCc_WThJHuJN2cAtPS5f68m-k6Yrxi_lI0");
  var summaryText = "";
  
  // 1. 總覽狀態
  var summarySheet = ss.getSheetByName("Summary");
  if (summarySheet) {
    var data = getSheetDataAsObjects(summarySheet);
    summaryText += "【目前皮膚狀態與主力組合】\n";
    data.forEach(function(row) {
      summaryText += "- " + row.Category + ": " + row.Content + "\n";
    });
    summaryText += "\n";
  }
  
  // 2. 全部產品
  var productsSheet = ss.getSheetByName("Products");
  if (productsSheet) {
    var data = getSheetDataAsObjects(productsSheet);
    summaryText += "【保養產品清單與適合度】\n";
    data.forEach(function(row) {
      summaryText += "- " + row.Product + " (" + row.Status + "): " + row.Description + "\n";
    });
    summaryText += "\n";
  }
  
  // 3. 避雷規則
  var avoidSheet = ss.getSheetByName("AvoidRules");
  if (avoidSheet) {
    var data = getSheetDataAsObjects(avoidSheet);
    summaryText += "【保養避雷規則】\n";
    data.forEach(function(row) {
      summaryText += "- 不要: " + row.DoNot + " | 原因: " + row.Reason + " | 正確做法: " + row.CorrectWay + "\n";
    });
    summaryText += "\n";
  }
  
  // 4. 早晚流程
  var routinesSheet = ss.getSheetByName("Routines");
  if (routinesSheet) {
    var data = getSheetDataAsObjects(routinesSheet);
    summaryText += "【早晚保養流程】\n";
    data.forEach(function(row) {
      summaryText += "- " + row.TimeOfDay + ": " + row.Flow + "\n";
    });
  }
  
  return summaryText;
}

/**
 * 初始化試算表資料 (將 V6 資料寫入)
 */
function setupSheets() {
  var ss = SpreadsheetApp.openById("1Ee2l-BAw5BCc_WThJHuJN2cAtPS5f68m-k6Yrxi_lI0");
  
  // 建立工作表
  createSheetWithData(ss, "Summary", [
    ["Category", "Content"],
    ["目前皮膚狀態", "外油內乾、醫生提醒臉太乾、皮秒術後需修護、防曬與降低刺激優先。"],
    ["緊急警告", "乾、刺、脫皮、泛紅時：白黃橘瓶、A醛、酸類、泥膜、水楊酸洗面膜全部暫停。"],
    ["主力步驟", "雅漾或SD噴霧 → 神經醯胺 → 玻尿酸 → SD能量霜 → 主力臉部防曬。"],
    ["功效型恢復順序", "白瓶G → 橘瓶PV / Celladix 131 → 黃瓶V / A醛 → 酸類與清潔面膜。"]
  ]);
  
  createSheetWithData(ss, "Products", [
    ["Product", "Status", "Description"],
    ["雅漾活泉水", "非常適合", "舒緩、降溫、降低緊繃，可取代SD噴霧。"],
    ["SD噴霧", "適合", "洗臉後、臉熱、緊繃時使用。"],
    ["SD舒緩精華", "適合", "主力修護精華。"],
    ["SD能量霜", "適合", "鎖水修護，T字薄擦。"],
    ["神經醯胺精華 1%", "非常適合", "屏障修護核心產品。"],
    ["1%玻尿酸", "適合但要鎖水", "後面一定要接乳霜。"],
    ["Celladix 131", "穩定後再用", "控油、毛孔、皮脂平衡。"],
    ["B5水楊酸洗面膜", "少用", "穩定後一週最多1次，只T字區。"],
    ["白瓶G", "14天後優先恢復", "穀胱甘肽亮白。"],
    ["橘瓶PV", "白瓶後再加入", "維C抗氧亮白。"],
    ["黃瓶V", "最後再用", "高濃維C，最容易刺、乾、脫皮。"],
    ["Medi-Peel A醛", "後期低頻率", "一週1次開始，避開眼周。"],
    ["TWG水楊酸/壬二酸", "14天後評估", "不要和A醛同晚。"],
    ["芷豆泥膜", "目前不建議", "臉乾時停用。"],
    ["SPF50+防曬", "每天必用", "皮秒後、防反黑、防老化。"]
  ]);
  
  createSheetWithData(ss, "Instructions", [
    ["Product", "Dosage", "UsageMethod", "Interval", "Attention"],
    ["雅漾/SD噴霧", "2～4下", "距離20公分噴，10～20秒後輕壓。", "半乾接精華", "不要自然乾到完全乾。"],
    ["SD舒緩精華", "1～2滴管", "輕壓，不用拍。", "30～60秒", "刺痛時可只用它＋乳霜。"],
    ["神經醯胺", "1～2滴管", "輕壓吸收。", "30～60秒", "早晚可用。"],
    ["玻尿酸", "2～4滴", "臉微濕時擦。", "30秒後接乳霜", "不可單擦。"],
    ["SD能量霜", "半～1顆黃豆", "全臉薄擦。", "最後一步", "T字少量。"],
    ["白瓶G", "2～3滴", "14天後少量局部。", "1～2分鐘", "一週2～3次開始。"],
    ["黃瓶V", "1～2滴局部", "完全穩定後才用。", "2～3分鐘", "乾燥期停用。"],
    ["Medi-Peel A醛", "豌豆大小", "晚上用，避開眼周鼻翼嘴角。", "5～10分後補霜", "一週1次開始。"],
    ["B5水楊酸洗面膜", "薄敷T字", "5～8分鐘沖掉。", "沖掉後立刻修護", "一週最多1次。"],
    ["防曬", "兩指長", "早上最後一步。", "保養後等3～5分", "戶外2～3小時補擦。"]
  ]);
  
  createSheetWithData(ss, "Routines", [
    ["TimeOfDay", "Flow"],
    ["早上", "清水/溫和洗臉 → 雅漾或SD噴霧 → 神經醯胺 → 玻尿酸 → SD能量霜薄擦 → 主力臉部防曬"],
    ["晚上", "溫和洗臉 → 雅漾或SD噴霧 → SD舒緩精華或神經醯胺 → 玻尿酸 → SD能量霜"],
    ["乾燥急救", "停用功效型產品 → 雅漾/SD噴霧 → 神經醯胺 → SD能量霜 → B5或CeraVe"]
  ]);
  
  createSheetWithData(ss, "Sunscreens", [
    ["Rank", "Product", "Score", "Position", "Recommendation"],
    ["🥇 No.1", "理膚寶水 UVMune 400", "9.5/10", "主力臉部防曬", "適合皮秒後、怕反黑、需要高UVA防護。"],
    ["🥈 No.2", "雅漾防曬系列", "9/10", "敏感肌/修護期", "適合臉乾、術後、敏感時期。"],
    ["🥉 No.3", "DR.WU 保濕防曬", "9/10", "保濕型防曬", "適合外油內乾、缺水。"],
    ["No.4", "OBgE 素顏霜防曬", "8.5/10", "潤色修飾", "建議當修飾，不完全取代足量防曬。"],
    ["No.5", "YIMIAOSI SPF50+", "7/10", "身體防曬優先", "臉部可用但非主力。"]
  ]);
  
  createSheetWithData(ss, "AvoidRules", [
    ["DoNot", "Reason", "CorrectWay"],
    ["噴霧後完全自然乾", "可能更緊繃。", "噴後10～20秒輕壓。"],
    ["用力拍打", "乾燥/術後易刺激。", "手掌輕壓。"],
    ["玻尿酸單擦", "可能越擦越乾。", "後接乳霜鎖水。"],
    ["A醛 + 酸類同晚", "太刺激。", "至少間隔2天。"],
    ["水楊酸洗面膜 + A醛同晚", "屏障容易受不了。", "分開不同天。"],
    ["臉乾還敷泥膜", "會更乾。", "穩定後只敷T字區。"]
  ]);
  
  createSheetWithData(ss, "Dupes", [
    ["OriginalProduct", "DupeProduct", "Category"],
    ["SD噴霧", "雅漾活泉水、理膚寶水B5噴霧、Curel噴霧", "噴霧"],
    ["SD舒緩精華", "DR.WU神經醯胺、理膚寶水B5精華、藝群神經醯胺", "精華液"],
    ["SD能量霜", "CeraVe修護乳霜、理膚寶水B5+、Curel乳霜", "乳霜"]
  ]);

  createSheetWithData(ss, "Config", [
    ["Key", "Value", "Description"],
    ["GEMINI_API_KEY", "請輸入你的金鑰", "Gemini API 金鑰，請向 Google AI Studio 申請"],
    ["GEMINI_MODEL", "gemini-2.5-flash", "使用之模型，建議為 gemini-2.5-flash"]
  ]);
  
  // 刪除預設的 Sheet1
  var defaultSheet = ss.getSheetByName("工作表1") || ss.getSheetByName("Sheet1");
  if (defaultSheet && ss.getSheets().length > 1) {
    ss.deleteSheet(defaultSheet);
  }
}

function createSheetWithData(ss, sheetName, data) {
  var sheet = ss.getSheetByName(sheetName);
  if (sheet) {
    ss.deleteSheet(sheet);
  }
  sheet = ss.insertSheet(sheetName);
  sheet.getRange(1, 1, data.length, data[0].length).setValues(data);
  sheet.getRange(1, 1, 1, data[0].length).setFontWeight("bold").setBackground("#e2e8f0");
  sheet.autoResizeColumns(1, data[0].length);
}
