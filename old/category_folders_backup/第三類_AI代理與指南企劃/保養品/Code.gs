/**
 * 網頁伺服器入口
 */
function doGet(e) {
  if (e && e.parameter && e.parameter.migrate === "true") {
    try {
      var result = runMigrations();
      return ContentService.createTextOutput(JSON.stringify(result)).setMimeType(ContentService.MimeType.JSON);
    } catch(err) {
      return ContentService.createTextOutput(JSON.stringify({ success: false, error: err.toString() })).setMimeType(ContentService.MimeType.JSON);
    }
  }
  var template = HtmlService.createTemplateFromFile("Index");
  var htmlOutput = template.evaluate();
  htmlOutput.setTitle("AI Skincare Website V7");
  htmlOutput.addMetaTag("viewport", "width=device-width, initial-scale=1.0");
  htmlOutput.setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
  return htmlOutput;
}

/**
 * 執行試算表多使用者遷移與初始化
 */
function runMigrations() {
  var ss = SpreadsheetApp.openById("1Ee2l-BAw5BCc_WThJHuJN2cAtPS5f68m-k6Yrxi_lI0");
  
  // 1. 建立 Users 工作表（如果不存在）
  var usersSheet = ss.getSheetByName("Users");
  if (!usersSheet) {
    usersSheet = ss.insertSheet("Users");
    usersSheet.getRange(1, 1, 1, 3).setValues([["Username", "Pin", "SpreadsheetId"]]);
    usersSheet.getRange(1, 1, 1, 3).setFontWeight("bold").setBackground("#e2e8f0");
  }
  
  // 預設新增使用者 shihwei / 1234
  var usersData = getSheetDataAsObjects(usersSheet);
  var hasShihwei = usersData.some(function(row) {
    return row.Username && row.Username.toString().trim() === "shihwei";
  });
  if (!hasShihwei) {
    usersSheet.appendRow(["shihwei", "1234", ""]);
  }
  
  // 2. 在需要分區的工作表加上 Username 欄位
  var partitionedSheets = ["Summary", "Products", "Instructions", "Routines", "ChecklistState"];
  partitionedSheets.forEach(function(name) {
    var sheet = ss.getSheetByName(name);
    if (!sheet) return;
    
    var lastRow = sheet.getLastRow();
    var lastColumn = sheet.getLastColumn();
    if (lastColumn < 1) return;
    
    var headers = sheet.getRange(1, 1, 1, lastColumn).getValues()[0];
    var userColIdx = headers.indexOf("Username");
    
    if (userColIdx === -1) {
      // Username 欄位不存在，直接在最後一行追加
      sheet.getRange(1, lastColumn + 1).setValue("Username").setFontWeight("bold").setBackground("#e2e8f0");
      if (lastRow >= 2) {
        var fillValues = [];
        for (var i = 2; i <= lastRow; i++) {
          fillValues.push(["shihwei"]);
        }
        sheet.getRange(2, lastColumn + 1, lastRow - 1, 1).setValues(fillValues);
      }
      sheet.autoResizeColumn(lastColumn + 1);
    }
  });
  
  return { success: true, message: "資料遷移完成！已建立 Users 且所有相關分頁已加上 Username 分區。" };
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
  var values = range.getDisplayValues();
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
 * 驗證 PIN 碼登入並回傳該使用者的資料
 */
function loginAndFetchData(username, pin) {
  if (!username || !pin) {
    throw new Error("請輸入使用者名稱與 PIN 碼");
  }
  
  var ss = SpreadsheetApp.openById("1Ee2l-BAw5BCc_WThJHuJN2cAtPS5f68m-k6Yrxi_lI0");
  
  // 驗證 Users
  var usersSheet = ss.getSheetByName("Users");
  if (!usersSheet) {
    runMigrations();
    usersSheet = ss.getSheetByName("Users");
  }
  
  var users = getSheetDataAsObjects(usersSheet);
  var validUser = null;
  for (var i = 0; i < users.length; i++) {
    if (users[i].Username.toString().toLowerCase().trim() === username.toString().toLowerCase().trim() &&
        users[i].Pin.toString().trim() === pin.toString().trim()) {
      validUser = users[i];
      break;
    }
  }
  
  if (!validUser) {
    throw new Error("帳號或 PIN 碼錯誤");
  }
  
  var summaryRaw = getSheetDataAsObjects(ss.getSheetByName("Summary"));
  var productsRaw = getSheetDataAsObjects(ss.getSheetByName("Products"));
  var instructionsRaw = getSheetDataAsObjects(ss.getSheetByName("Instructions"));
  var routinesRaw = getSheetDataAsObjects(ss.getSheetByName("Routines"));
  var sunscreens = getSheetDataAsObjects(ss.getSheetByName("Sunscreens"));
  var avoidRules = getSheetDataAsObjects(ss.getSheetByName("AvoidRules"));
  var dupes = getSheetDataAsObjects(ss.getSheetByName("Dupes"));
  
  var filterUser = function(row) {
    return row.Username && row.Username.toString().toLowerCase().trim() === username.toString().toLowerCase().trim();
  };
  
  var summary = summaryRaw.filter(filterUser);
  var products = productsRaw.filter(filterUser);
  var instructions = instructionsRaw.filter(filterUser);
  var routines = routinesRaw.filter(filterUser);
  var checklistState = getChecklistStateForUser(username);
  
  return {
    summary: summary,
    products: products,
    instructions: instructions,
    routines: routines,
    sunscreens: sunscreens,
    avoidRules: avoidRules,
    dupes: dupes,
    checklistState: checklistState
  };
}

/**
 * 呼叫 Gemini API 進行諮詢（限定當前登入使用者的資料 Context）
 */
function askGemini(username, userQuestion) {
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
  
  var context = getSkincareContextSummaryForUser(username);
  var systemInstruction = "你是一位專業的個人皮膚保養顧問。你擁有用戶目前的保養品資料庫、使用方法、早晚流程以及防曬比較表。\n" +
                          "請根據以下資料庫內容，親切、專業、簡短地回答用戶的保養問題。\n" +
                          "當用戶的皮膚有紅腫、刺痛、脫皮等敏感情況時，必須依據避雷規則，主動警告他們暫停使用酸類、A醛、高濃度維C等功效型產品，並建議以修護為主的流程。\n" +
                          "【重要功能一：新產品評估判定】\n" +
                          "當用戶詢問資料庫以外的任何「新產品」或「往後的產品」是否適合他們，你必須建立一個動態評估標準，比對該新產品的成分/功能與用戶當前的皮膚狀態（如外油內乾、皮秒術後需修護）和避雷規則。根據這些比對結果，明確判定出該新產品的適合度等級（「非常適合」、「穩定後再用」、「目前不建議」）並詳細說明原因。\n" +
                          "【重要功能二：協助登錄資料庫】\n" +
                          "若用戶明確要求「幫我新增這個產品」、「加到我的資料庫」或類似意圖時，在用文字親切回覆完畢後，你必須在回覆的最尾端附加上一個特定的指令 JSON 格式，以便系統自動將其登錄至試算表。格式必須為：\n" +
                          "[[ADD_PRODUCT_JSON: {\"Product\":\"產品名稱\",\"Status\":\"適合度\",\"Description\":\"用途說明\",\"Dosage\":\"用量\",\"UsageMethod\":\"使用方法\",\"Interval\":\"間隔\",\"Attention\":\"注意事項\"}]]\n" +
                          "請務必填寫你評估出來的各項屬性，未提及的屬性可保留空字串，但不可省略該 JSON 格式。\n\n" +
                          "【當前使用者：" + username + " 的保養品資料庫內容如下】\n" + context;
  
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
      "temperature": 0.7,
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
 * 彙整特定使用者的試算表資料為文字摘要
 */
function getSkincareContextSummaryForUser(username) {
  var ss = SpreadsheetApp.openById("1Ee2l-BAw5BCc_WThJHuJN2cAtPS5f68m-k6Yrxi_lI0");
  var summaryText = "";
  
  var filterUser = function(row) {
    return row.Username && row.Username.toString().toLowerCase().trim() === username.toString().toLowerCase().trim();
  };
  
  // 1. 總覽狀態
  var summarySheet = ss.getSheetByName("Summary");
  if (summarySheet) {
    var data = getSheetDataAsObjects(summarySheet).filter(filterUser);
    summaryText += "【目前皮膚狀態與主力組合】\n";
    data.forEach(function(row) {
      summaryText += "- " + row.Category + ": " + row.Content + "\n";
    });
    summaryText += "\n";
  }
  
  // 2. 全部產品
  var productsSheet = ss.getSheetByName("Products");
  if (productsSheet) {
    var data = getSheetDataAsObjects(productsSheet).filter(filterUser);
    summaryText += "【保養產品清單與適合度】\n";
    data.forEach(function(row) {
      summaryText += "- " + row.Product + " (" + row.Status + "): " + row.Description + "\n";
    });
    summaryText += "\n";
  }
  
  // 3. 避雷規則 (全域)
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
    var data = getSheetDataAsObjects(routinesSheet).filter(filterUser);
    summaryText += "【早晚保養流程】\n";
    data.forEach(function(row) {
      summaryText += "- " + row.TimeOfDay + ": " + row.Flow + "\n";
    });
  }
  
  return summaryText;
}

/**
 * 快速新增產品到該使用者的試算表分區
 */
function addNewProductToSheets(username, productData) {
  var ss = SpreadsheetApp.openById("1Ee2l-BAw5BCc_WThJHuJN2cAtPS5f68m-k6Yrxi_lI0");
  
  var productName = productData.Product || productData.productName || "";
  if (!productName) return { success: false, message: "產品名稱不能為空" };
  
  // 1. 寫入 Products 工作表
  var productsSheet = ss.getSheetByName("Products");
  if (productsSheet) {
    productsSheet.appendRow([
      productName,
      productData.Status || "適合",
      productData.Description || "",
      username
    ]);
  }
  
  // 2. 寫入 Instructions 工作表
  var instructionsSheet = ss.getSheetByName("Instructions");
  if (instructionsSheet) {
    instructionsSheet.appendRow([
      productName,
      productData.Dosage || "",
      productData.UsageMethod || "",
      productData.Interval || "",
      productData.Attention || "",
      username
    ]);
  }
  
  return { success: true, message: "成功新增產品：" + productName };
}

/**
 * 取得特定使用者的雲端勾選清單狀態
 */
function getChecklistStateForUser(username) {
  var ss = SpreadsheetApp.openById("1Ee2l-BAw5BCc_WThJHuJN2cAtPS5f68m-k6Yrxi_lI0");
  var sheet = ss.getSheetByName("ChecklistState");
  if (!sheet) {
    sheet = ss.insertSheet("ChecklistState");
    sheet.getRange(1, 1, 1, 4).setValues([["Key", "Value", "LastUpdated", "Username"]]);
    sheet.getRange(1, 1, 1, 4).setFontWeight("bold").setBackground("#e2e8f0");
  }
  
  var data = getSheetDataAsObjects(sheet);
  var state = {};
  data.forEach(function(row) {
    if (row.Username && row.Username.toString().toLowerCase().trim() === username.toString().toLowerCase().trim()) {
      state[row.Key] = (row.Value === "true" || row.Value === true);
    }
  });
  return state;
}

/**
 * 儲存單個勾選狀態至雲端（隔離使用者）
 */
function saveChecklistState(username, key, value) {
  var ss = SpreadsheetApp.openById("1Ee2l-BAw5BCc_WThJHuJN2cAtPS5f68m-k6Yrxi_lI0");
  var sheet = ss.getSheetByName("ChecklistState");
  if (!sheet) {
    sheet = ss.insertSheet("ChecklistState");
    sheet.getRange(1, 1, 1, 4).setValues([["Key", "Value", "LastUpdated", "Username"]]);
    sheet.getRange(1, 1, 1, 4).setFontWeight("bold").setBackground("#e2e8f0");
  }
  
  var lastRow = sheet.getLastRow();
  var found = false;
  
  if (lastRow >= 2) {
    var range = sheet.getRange(2, 1, lastRow - 1, 4);
    var values = range.getValues();
    for (var i = 0; i < values.length; i++) {
      var rowKey = values[i][0];
      var rowUser = values[i][3];
      if (rowKey === key && rowUser.toString().toLowerCase().trim() === username.toString().toLowerCase().trim()) {
        sheet.getRange(i + 2, 2, 1, 2).setValues([[value.toString(), new Date()]]);
        found = true;
        break;
      }
    }
  }
  
  if (!found) {
    sheet.appendRow([key, value.toString(), new Date(), username]);
  }
  
  return { success: true };
}

/**
 * 清除特定使用者在雲端的所有勾選狀態
 */
function clearChecklistState(username) {
  var ss = SpreadsheetApp.openById("1Ee2l-BAw5BCc_WThJHuJN2cAtPS5f68m-k6Yrxi_lI0");
  var sheet = ss.getSheetByName("ChecklistState");
  if (sheet) {
    var lastRow = sheet.getLastRow();
    if (lastRow >= 2) {
      var range = sheet.getRange(2, 1, lastRow - 1, 4);
      var values = range.getValues();
      for (var i = values.length - 1; i >= 0; i--) {
        var rowUser = values[i][3];
        if (rowUser.toString().toLowerCase().trim() === username.toString().toLowerCase().trim()) {
          sheet.deleteRow(i + 2);
        }
      }
    }
  }
  return { success: true };
}

/**
 * 初始化全新試算表資料的函數（供初次安裝使用）
 */
function setupSheets() {
  var ss = SpreadsheetApp.openById("1Ee2l-BAw5BCc_WThJHuJN2cAtPS5f68m-k6Yrxi_lI0");
  
  createSheetWithData(ss, "Users", [
    ["Username", "Pin", "SpreadsheetId"],
    ["shihwei", "1234", ""]
  ]);

  createSheetWithData(ss, "Summary", [
    ["Category", "Content", "Username"],
    ["目前皮膚狀態", "外油內乾、醫生提醒臉太乾、皮秒術後需修護、防曬與降低刺激優先。", "shihwei"],
    ["緊急警告", "乾、刺、脫皮、泛紅時：白黃橘瓶、A醛、酸類、泥膜、水楊酸洗面膜全部暫停。", "shihwei"],
    ["主力步驟", "雅漾或SD噴霧 → 神經醯胺 → 玻尿酸 → SD能量霜 → 主力臉部防曬。", "shihwei"],
    ["功效型恢復順序", "白瓶G → 橘瓶PV / Celladix 131 → 黃瓶V / A醛 → 酸類與清潔面膜。", "shihwei"]
  ]);
  
  createSheetWithData(ss, "Products", [
    ["Product", "Status", "Description", "Username"],
    ["雅漾活泉水", "非常適合", "舒緩、降溫、降低緊繃，可取代SD噴霧。", "shihwei"],
    ["SD噴霧", "適合", "洗臉後、臉熱、緊繃時使用。", "shihwei"],
    ["SD舒緩精華", "適合", "主力修護精華。", "shihwei"],
    ["SD能量霜", "適合", "鎖水修護，T字薄擦。", "shihwei"],
    ["神經醯胺精華 1%", "非常適合", "屏障修護核心產品。", "shihwei"],
    ["1%玻尿酸", "適合但要鎖水", "後面一定要接乳霜。", "shihwei"],
    ["Celladix 131", "穩定後再用", "控油、毛孔、皮脂平衡。", "shihwei"],
    ["B5水楊酸洗面膜", "少用", "穩定後一週最多1次，只T字區。", "shihwei"],
    ["白瓶G", "14天後優先恢復", "穀胱甘肽亮白。", "shihwei"],
    ["橘瓶PV", "白瓶後再加入", "維C抗氧亮白。", "shihwei"],
    ["黃瓶V", "最後再用", "高濃維C，最容易刺、乾、脫皮。", "shihwei"],
    ["Medi-Peel A醛", "後期低頻率", "一週1次開始，避開眼周。", "shihwei"],
    ["TWG水楊酸/壬二酸", "14天後評估", "不要和A醛同晚。", "shihwei"],
    ["芷豆泥膜", "目前不建議", "臉乾時停用。", "shihwei"],
    ["SPF50+防曬", "每天必用", "皮秒後、防反黑、防老化。", "shihwei"]
  ]);
  
  createSheetWithData(ss, "Instructions", [
    ["Product", "Dosage", "UsageMethod", "Interval", "Attention", "Username"],
    ["雅漾/SD噴霧", "2～4下", "距離20公分噴，10～20秒後輕壓。", "半乾接精華", "不要自然乾到完全乾。", "shihwei"],
    ["SD舒緩精華", "1～2滴管", "輕壓，不用拍。", "30～60秒", "刺痛時可只用它＋乳霜。", "shihwei"],
    ["神經醯胺", "1～2滴管", "輕壓吸收。", "30～60秒", "早晚可用。", "shihwei"],
    ["玻尿酸", "2～4滴", "臉微濕時擦。", "30秒後接乳霜", "不可單擦。", "shihwei"],
    ["SD能量霜", "半～1顆黃豆", "全臉薄擦。", "最後一步", "T字少量。", "shihwei"],
    ["白瓶G", "2～3滴", "14天後少量局部。", "1～2分鐘", "一週2～3次開始。", "shihwei"],
    ["黃瓶V", "1～2滴局部", "完全穩定後才用。", "2～3分鐘", "乾燥期停用。", "shihwei"],
    ["Medi-Peel A醛", "豌豆大小", "晚上用，避開眼周鼻翼嘴角。", "5～10分後補霜", "一週1次開始。", "shihwei"],
    ["B5水楊酸洗面膜", "薄敷T字", "5～8分鐘沖掉。", "沖掉後立刻修護", "一週最多1次。", "shihwei"],
    ["防曬", "兩指長", "早上最後一步。", "保養後等3～5分", "戶外2～3小時補擦。", "shihwei"]
  ]);
  
  createSheetWithData(ss, "Routines", [
    ["TimeOfDay", "Flow", "Username"],
    ["早上", "清水/溫和洗臉 → 雅漾或SD噴霧 → 神經醯胺 → 玻尿酸 → SD能量霜薄擦 → 主力臉部防曬", "shihwei"],
    ["晚上", "溫和洗臉 → 雅漾或SD噴霧 → SD舒緩精華或神經醯胺 → 玻尿酸 → SD能量霜", "shihwei"],
    ["乾燥急救", "停用功效型產品 → 雅漾/SD噴霧 → 神經醯胺 → SD能量霜 → B5或CeraVe", "shihwei"]
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
  
  createSheetWithData(ss, "ChecklistState", [
    ["Key", "Value", "LastUpdated", "Username"]
  ]);
  
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
