function setupEnvironment() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName("教材資料庫");
  if (!sheet) {
    sheet = ss.insertSheet("教材資料庫");
    sheet.appendRow(["教材名稱", "Markdown內容", "建立時間", "原檔連結"]);
  }
  // 建立存放圖片的資料夾
  var folders = DriveApp.getFoldersByName("教育訓練教材_圖片庫");
  var folder;
  if (folders.hasNext()) {
    folder = folders.next();
  } else {
    folder = DriveApp.createFolder("教育訓練教材_圖片庫");
    folder.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
  }
  Logger.log("✅ 設定完成！請在設定中填入您的 GEMINI_API_KEY。");
  Logger.log("📂 圖片資料夾 ID: " + folder.getId());
  // 將 ID 印出，讓使用者可以填到全域變數
}

// ----------------------------------------------------------------
// API 路由
// ----------------------------------------------------------------
function doPost(e) {
  // 處理 CORS 預檢請求
  if (!e.postData) {
    return makeResponse({status: "ok"});
  }
  
  try {
    var data = JSON.parse(e.postData.contents);
    var action = data.action;

    if (action === "upload") {
      return makeResponse(handleUpload(data));
    } else if (action === "list") {
      return makeResponse(handleList());
    } else if (action === "get") {
      return makeResponse(handleGet(data.filename));
    } else {
      return makeResponse({error: "Unknown action: " + action}, 400);
    }
  } catch (err) {
    return makeResponse({error: err.toString()}, 500);
  }
}

function makeResponse(data, code) {
  var output = ContentService.createTextOutput(JSON.stringify(data));
  output.setMimeType(ContentService.MimeType.JSON);
  return output;
}

// ----------------------------------------------------------------
// 上傳與轉檔邏輯
// ----------------------------------------------------------------
function handleUpload(data) {
  // data: { filename, mimeType, base64, geminiApiKey (optional) }
  var filename = data.filename;
  var mimeType = data.mimeType;
  var base64 = data.base64;
  
  // 1. 解碼並準備檔案
  var blob = Utilities.newBlob(Utilities.base64Decode(base64), mimeType, filename);
  
  // 2. 透過 Advanced Drive Service 強制轉換為 Google 文件 (執行 OCR 與圖片萃取)
  // 注意：需要到 GAS 編輯器的「服務」中開啟 Drive API
  var resource = {
    title: "AI暫存解析_" + filename,
    mimeType: MimeType.GOOGLE_DOCS
  };
  var convertedFile = Drive.Files.insert(resource, blob, {ocr: true});
  
  // 3. 讀取 Google 文件並抽出圖片
  var doc = DocumentApp.openById(convertedFile.id);
  var body = doc.getBody();
  var extractedText = body.getText() + "\n\n";
  
  // 取得資料夾
  var folders = DriveApp.getFoldersByName("教育訓練教材_圖片庫");
  var folder = folders.hasNext() ? folders.next() : DriveApp.createFolder("教育訓練教材_圖片庫");
  
  var images = body.getImages();
  for (var i = 0; i < images.length; i++) {
    var imgBlob = images[i].getBlob();
    var imgName = filename.split(".")[0] + "_img_" + (i+1) + ".jpg";
    imgBlob.setName(imgName);
    var imgFile = folder.createFile(imgBlob);
    
    // 取得圖片公開直連網址
    var imgUrl = "https://drive.google.com/uc?id=" + imgFile.getId();
    extractedText += "\n![圖片](" + imgUrl + ")\n\n";
  }
  
  // 4. 解析完成，刪除暫存的 Google 文件
  DriveApp.getFileById(convertedFile.id).setTrashed(true);
  
  // 5. 呼叫 Gemini API 進行精煉
  var geminiKey = data.geminiApiKey; // 前端傳入或使用全域
  var finalMarkdown = callGemini(extractedText, geminiKey);
  
  // 6. 存入試算表
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName("教材資料庫");
  var now = Utilities.formatDate(new Date(), "GMT+8", "yyyy-MM-dd HH:mm:ss");
  
  // 檢查是否已有同名教材，有則更新，無則新增
  var records = sheet.getDataRange().getValues();
  var updated = false;
  for (var r = 1; r < records.length; r++) {
    if (records[r][0] === filename) {
      sheet.getRange(r + 1, 2).setValue(finalMarkdown);
      sheet.getRange(r + 1, 3).setValue(now);
      updated = true;
      break;
    }
  }
  if (!updated) {
    sheet.appendRow([filename, finalMarkdown, now, ""]);
  }
  
  return { success: true, filename: filename, markdown: finalMarkdown };
}

// ----------------------------------------------------------------
// 呼叫 Gemini API 3.8
// ----------------------------------------------------------------
function callGemini(text, apiKey) {
  var url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key=" + apiKey;
  
  var prompt = "你是一個專業的教育訓練教材撰寫專家。\n" +
               "請將以下由系統萃取出的文字與圖片標籤，重新排版成結構清晰、適合閱讀的 Markdown 格式教材。\n" +
               "重要：請務必保留原文中所有的圖片標籤 `![圖片](...)` 不可刪除，將它們安插在適合的步驟段落中。\n\n" +
               "原始內容：\n" + text;
               
  var payload = {
    "contents": [{"parts": [{"text": prompt}]}]
  };
  
  var options = {
    "method": "post",
    "contentType": "application/json",
    "payload": JSON.stringify(payload),
    "muteHttpExceptions": true
  };
  
  var response = UrlFetchApp.fetch(url, options);
  var json = JSON.parse(response.getContentText());
  
  if (json.error) {
    throw new Error("Gemini API Error: " + json.error.message);
  }
  
  return json.candidates[0].content.parts[0].text;
}

// ----------------------------------------------------------------
// 取得列表與教材內容
// ----------------------------------------------------------------
function handleList() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("教材資料庫");
  var data = sheet.getDataRange().getValues();
  var list = [];
  for (var i = 1; i < data.length; i++) {
    if (data[i][0]) list.push(data[i][0]);
  }
  return { materials: list.reverse() };
}

function handleGet(filename) {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("教材資料庫");
  var data = sheet.getDataRange().getValues();
  for (var i = 1; i < data.length; i++) {
    if (data[i][0] === filename) {
      return { filename: filename, content: data[i][1] };
    }
  }
  return { error: "找不到教材" };
}
