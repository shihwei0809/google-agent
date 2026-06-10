# 雲端執行指引：使用 Google Apps Script 實現 24 小時免開機通報

如果您希望系統在**電腦關機時也能自動運作**，最完美且 **100% 免費** 的做法是將程式碼直接部署在您的 **Google 試算表雲端腳本 (Google Apps Script)** 中。

### 💡 雲端版的優勢：
1. **完全免開機**：程式託管在 Google 雲端伺服器，24 小時自動定時執行。
2. **一天僅通知一次（防打擾）**：系統會自動抓取**今日整天的預報溫度**，將所有超過 28°C 的時段整理在**同一封訊息**中發送。每天只會通報一次，人員不會因為頻繁通知而忽略。
3. **免 SMTP 與免密碼寄信**：直接調用 Google 官方郵件服務發信，安全且不需在設定檔中曝露您的信箱密碼。
4. **與試算表完美整合**：直接讀取您當前的 Google 試算表，完全不需將試算表「發布到網路 (CSV)」。
5. **自動產生當月紀錄分頁**：每次成功發送警報，系統會自動在您的 Google 試算表中尋找或新建名稱為「紀錄_年-月」的分頁（例如：`紀錄_2026-06`），並自動把通報時間、高溫明細等資訊追加進去，且具備精美格式美化，方便後續稽核與查詢。

---

## 🛠️ 第一步：貼上雲端程式碼

1. 開啟您在雲端硬碟建立的聯絡人試算表。
2. 點選上方選單的 **「擴充功能」 -> 「Apps Script」**。
3. 清除編輯器內的所有預設程式碼，並貼上以下程式碼：

```javascript
/**
 * 當試算表開啟時，自動建立頂端自訂選單，方便人員點選測試與重置
 */
function onOpen() {
  var ui = SpreadsheetApp.getUi();
  ui.createMenu('🌡️ 溫度通報系統')
      .addItem('🧪 測試即時通報 (強制發送)', 'testNotifyForce')
      .addItem('🔄 重置防重複鎖定', 'clearNotifiedState')
      .addItem('📏 重設欄寬為最佳預設', 'resetColumnWidths')
      .addToUi();
}

/**
 * CWA 環境溫度監控與 LINE/Email 自動通報系統 (Google Apps Script 雲端 CWA Open Data API 版)
 */
function checkWeatherAndNotify() {
  // 檢查本機最後執行時間，如果本機在 75 分鐘內有執行過，則雲端跳過本次排程 (本機優先)
  var properties = PropertiesService.getScriptProperties();
  var lastLocalHeartbeat = properties.getProperty("LAST_LOCAL_HEARTBEAT");
  if (lastLocalHeartbeat) {
    var lastTime = parseInt(lastLocalHeartbeat);
    var nowTime = new Date().getTime();
    var diffMinutes = (nowTime - lastTime) / (1000 * 60);
    if (diffMinutes < 75) {
      Logger.log("偵測到本機近期已執行（約 " + Math.round(diffMinutes) + " 分鐘前），雲端備援跳過本次排程。");
      return;
    }
  }

  // 檢查是否在監測時段 (08:00 - 24:00) 內，避免非工作時間打擾人員
  var today = new Date();
  var currentHour = parseInt(Utilities.formatDate(today, "GMT+8", "HH"));
  if (currentHour < 8 || currentHour >= 24) {
    Logger.log("目前時間為 " + currentHour + " 點，不在監測時段 (08:00 - 24:00) 內，跳過執行。");
    return;
  }
  
  // 取得第一個分頁 (聯絡人設定檔)，避免因為使用者點選其他分頁而讀錯資料
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheets()[0];
  var data = sheet.getDataRange().getValues();
  
  // 1. 從試算表讀取收件者與溫度設定
  var threshold = 28.0; // 預設 28 度
  var emails = [];
  var lineIds = [];
  
  // 欄位對應: Name (A), Email (B), LINE_ID (C), Enabled (D)
  for (var i = 1; i < data.length; i++) {
    var name = String(data[i][0]).trim();
    var email = String(data[i][1]).trim();
    var lineId = String(data[i][2]).trim();
    var enabled = String(data[i][3]).trim().toUpperCase();
    
    // 判斷是否為溫度閾值設定列
    if (name.toLowerCase().includes("threshold") || name.includes("溫度") || name.includes("閥值") || name.includes("閾值")) {
      var numMatch = email.match(/(\d+(?:\.\d+)?)/);
      if (numMatch) {
        threshold = parseFloat(numMatch[1]);
      }
      continue;
    }
    
    // 排除已停用的人員
    if (enabled !== "N" && enabled !== "NO" && enabled !== "FALSE") {
      if (email && email.includes("@")) {
        emails.push(email);
      }
      if (lineId) {
        var prefix = lineId.charAt(0).toUpperCase();
        if (prefix === "U" || prefix === "C" || prefix === "R") {
          lineIds.push(lineId);
        }
      }
    }
  }
  
  Logger.log("當前警報溫度閥值設定為: " + threshold + "°C");
  Logger.log("Email 收件人名單: " + emails);
  Logger.log("LINE 推播名單: " + lineIds);
  
  if (emails.length === 0 && lineIds.length === 0) {
    Logger.log("偵測不到任何有效的啟用收件者，停止執行。");
    return;
  }
  
  // 2. 透過 CWA Open Data API 獲取線西站即時環境溫度
  var apiKey = "CWA-718BCC42-A79F-4138-99BC-81D9C317BE28";
  var stationId = "C0G900"; // 線西站
  var apiUrl = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0001-001?Authorization=" + apiKey + "&StationId=" + stationId;
  
  var apiResponse = UrlFetchApp.fetch(apiUrl, {"muteHttpExceptions": true});
  if (apiResponse.getResponseCode() !== 200) {
    Logger.log("CWA API 請求失敗，狀態碼: " + apiResponse.getResponseCode());
    return;
  }
  var apiData = JSON.parse(apiResponse.getContentText("UTF-8"));
  var stations = apiData.records.Station;
  if (!stations || stations.length === 0) {
    Logger.log("CWA API 回傳空資料，StationId=" + stationId);
    return;
  }
  
  var s = stations[0];
  var we = s.WeatherElement;
  var rawObsTime = s.ObsTime.DateTime; // ISO 格式，例如 "2026-06-09T19:00:00+08:00"
  var displayTime = rawObsTime ? rawObsTime.replace("T", " ").substring(0, 19) : "";
  
  var currentTemp = parseFloat(we.AirTemperature);
  
  if (currentTemp === -99) {
    Logger.log("站點 " + stationId + " 觀測環境溫度異常（-99），停止執行。");
    return;
  }
  
  Logger.log("觀測時間: " + displayTime + "，環境溫度: " + currentTemp + "°C");
  
  // 3. 狀態機邏輯比對
  var properties = PropertiesService.getScriptProperties();
  var lastState = properties.getProperty("LAST_STATE"); // 前次狀態: "HOT" 或 "COOL"
  
  var shouldNotify = false;
  var isHot = currentTemp > threshold;
  var alertStateText = "";
  var notifySubject = "";
  var notifyBody = "";
  
  var today = new Date();
  var formattedTime = Utilities.formatDate(today, "GMT+8", "yyyy-MM-dd HH:mm:ss");
  
  if (isHot) {
    // 高溫狀態
    if (lastState !== "HOT") {
      shouldNotify = true;
      alertStateText = "高溫超標警報";
      notifySubject = "【高溫警報】彰化縣線西鄉目前環境溫度已達 " + currentTemp + "°C，超過設定閾值！";
      
      notifyBody = "【" + sheet.getName() + " 環境高溫警報】\n";
      notifyBody += "當前環境溫度：" + currentTemp + "°C ⚠️ (已超過設定閾值 " + threshold + "°C)\n";
      notifyBody += "氣象觀測時間：" + displayTime + "\n";
      notifyBody += "通報時間：" + formattedTime + "\n\n";
      notifyBody += "※ 請相關人員開啟灑水設備降溫循環過濾器。\n";
      notifyBody += "※ 請相關人員注意防暑、多補充水分，並採取防範措施。";
    } else {
      alertStateText = "高溫持續中";
      Logger.log("目前處於高溫超標狀態，但前次已通報過，跳過重複通知。");
    }
  } else {
    // 正常狀態
    if (lastState === "HOT") {
      // 從超標回落到正常，需要通知
      shouldNotify = true;
      alertStateText = "溫度回落正常";
      notifySubject = "【高溫解除】彰化縣線西鄉目前環境溫度已回落至 " + currentTemp + "°C，低於設定閾值。";
      
      notifyBody = "【" + sheet.getName() + " 環境溫度回落通知】\n";
      notifyBody += "當前環境溫度：" + currentTemp + "°C ✅ (已降至設定閾值 " + threshold + "°C 以下)\n";
      notifyBody += "氣象觀測時間：" + displayTime + "\n";
      notifyBody += "通報時間：" + formattedTime + "\n\n";
      notifyBody += "※ 目前高溫警報已解除，氣溫已回落至安全範圍。";
    } else {
      alertStateText = "正常 (未超標)";
      Logger.log("目前處於低於閾值狀態，且前次亦為正常，跳過通知。");
    }
  }
  
  // 4. 送出通知與記錄
  if (shouldNotify) {
    Logger.log("觸發通知：「" + notifySubject + "」");
    
    var lineSent = false;
    var emailSent = false;
    
    // A. 發送 LINE (多個個人 ID 採用 Multicast API，群組/聊天室採用 Push API)
    var lineToken = "5GyVAKorqM7GsTi5+OdJNtEMJZuvGXU4OXEHWeSS+gnhkpkV0ZFCEb7M2KdTopUKPELADU+xIMadPUytJO0g1XDpq2pnYj/70KNDBcL0pBLutivXV9P6Ff76ylrHQ0dbILQsPd7pCGLFXMcCrmgcEQdB04t89/1O/w1cDnyilFU=";
    var userIds = [];
    var groupIds = [];
    for (var m = 0; m < lineIds.length; m++) {
      var prefix = lineIds[m].charAt(0).toUpperCase();
      if (prefix === "U") userIds.push(lineIds[m]);
      else if (prefix === "C" || prefix === "R") groupIds.push(lineIds[m]);
    }
    
    if (userIds.length > 0) {
      var multicastUrl = "https://api.line.me/v2/bot/message/multicast";
      var options = {
        "method": "post",
        "headers": {
          "Content-Type": "application/json",
          "Authorization": "Bearer " + lineToken
        },
        "payload": JSON.stringify({
          "to": userIds,
          "messages": [{"type": "text", "text": notifyBody}]
        }),
        "muteHttpExceptions": true
      };
      var response = UrlFetchApp.fetch(multicastUrl, options);
      if (response.getResponseCode() === 200) {
        lineSent = true;
        Logger.log("LINE Multicast 推播成功！");
      } else {
        Logger.log("LINE Multicast 推播失敗: " + response.getContentText());
      }
    }
    
    for (var g = 0; g < groupIds.length; g++) {
      var pushUrl = "https://api.line.me/v2/bot/message/push";
      var options = {
        "method": "post",
        "headers": {
          "Content-Type": "application/json",
          "Authorization": "Bearer " + lineToken
        },
        "payload": JSON.stringify({
          "to": groupIds[g],
          "messages": [{"type": "text", "text": notifyBody}]
        }),
        "muteHttpExceptions": true
      };
      var response = UrlFetchApp.fetch(pushUrl, options);
      if (response.getResponseCode() === 200) {
        lineSent = true;
        Logger.log("LINE 群組/聊天室推播成功！(ID: " + groupIds[g] + ")");
      } else {
        Logger.log("LINE 群組/聊天室推播失敗: " + response.getContentText() + " (ID: " + groupIds[g] + ")");
      }
    }
    
    // B. 發送電子郵件
    if (emails.length > 0) {
      try {
        MailApp.sendEmail({
          to: emails.join(","),
          subject: notifySubject,
          body: notifyBody
        });
        emailSent = true;
        Logger.log("電子郵件寄送成功！");
      } catch (e) {
        Logger.log("電子郵件寄送失敗: " + e.message);
      }
    }
    
    // 成功發送後，更新狀態機狀態
    if (lineSent || emailSent) {
      properties.setProperty("LAST_STATE", isHot ? "HOT" : "COOL");
    }
  }
  
  // 5. 無論是否發送通報，皆將讀取到的值記錄到分頁（通知狀態標示發送情況），以利後續追查數據
  var statusText = "";
  if (shouldNotify) {
    var statusArr = [];
    if (lineSent) statusArr.push("LINE");
    if (emailSent) statusArr.push("Email");
    statusText = statusArr.length > 0 ? (statusArr.join(" & ") + " 已發送") : "發送失敗";
  } else {
    statusText = "未發送 (重複或正常)";
  }
  
  try {
    logNotificationToSheet(threshold, currentTemp, displayTime, alertStateText, statusText, "雲端備援");
  } catch (logErr) {
    Logger.log("寫入通報紀錄分頁失敗: " + logErr.message);
  }
}

/**
 * 將通報紀錄寫入當月分頁，若分頁不存在則自動建立
 */
function logNotificationToSheet(threshold, currentTemp, displayTime, alertStateText, statusText, senderType) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var today = new Date();
  
  // 取得台灣時間 (UTC+8) 的 YYYY-MM 和詳細時間
  var formattedMonth = Utilities.formatDate(today, "GMT+8", "yyyy-MM"); // 例如 "2026-06"
  var formattedTime = Utilities.formatDate(today, "GMT+8", "yyyy-MM-dd HH:mm:ss");
  
  var sheetName = "紀錄_" + formattedMonth;
  var logSheet = ss.getSheetByName(sheetName);
  
  var headers = [
    ["通報時間", "溫度閾值設定 (°C)", "通報環境溫度 (°C)", "氣象觀測時間", "警報狀態", "通知狀態"]
  ];
  
  // 如果當月分頁不存在，則建立它
  if (!logSheet) {
    logSheet = ss.insertSheet(sheetName);
    
    // 設定表頭
    logSheet.getRange(1, 1, 1, headers[0].length).setValues(headers);
    
    // 美化表頭：深藍底色 (#1F4E79)、白字、置中、粗體
    var headerRange = logSheet.getRange(1, 1, 1, headers[0].length);
    headerRange.setBackground("#1F4E79")
               .setFontColor("#FFFFFF")
               .setFontWeight("bold")
               .setHorizontalAlignment("center");
    
    // 凍結第一列
    logSheet.setFrozenRows(1);
    
    // 設定預設寬度 (只在新建分頁時執行，避免之後覆蓋使用者手動拉寬)
    logSheet.setColumnWidth(1, 170); // 通報時間
    logSheet.setColumnWidth(2, 140); // 溫度閾值設定 (°C)
    logSheet.setColumnWidth(3, 140); // 通報環境溫度 (°C)
    logSheet.setColumnWidth(4, 170); // 氣象觀測時間
    logSheet.setColumnWidth(5, 140); // 警報狀態
    logSheet.setColumnWidth(6, 200); // 通知狀態
  } else {
    // 檢查並自動將舊表頭更新為新的環境溫度表頭 (支援自動遷移舊資料庫)
    try {
      var currentHeaders = logSheet.getRange(1, 1, 1, headers[0].length).getValues()[0];
      if (currentHeaders[2] && (currentHeaders[2].indexOf("最高") !== -1 || currentHeaders[2].indexOf("體感") !== -1)) {
        logSheet.getRange(1, 3).setValue("通報環境溫度 (°C)");
      }
      if (currentHeaders[3] && currentHeaders[3].indexOf("時段") !== -1) {
        logSheet.getRange(1, 4).setValue("氣象觀測時間");
      }
      if (currentHeaders[4] && (currentHeaders[4].indexOf("超標") !== -1 || currentHeaders[4].indexOf("明細") !== -1)) {
        logSheet.getRange(1, 5).setValue("警報狀態");
      }
    } catch (err) {
      Logger.log("檢查並更新舊表頭失敗: " + err.message);
    }
  }
  
  var finalStatusText = statusText;
  if (senderType) {
    finalStatusText += " (" + senderType + ")";
  }
  
  // 新增紀錄列
  var rowData = [
    formattedTime, 
    threshold, 
    currentTemp, 
    displayTime, 
    alertStateText, 
    finalStatusText
  ];
  
  logSheet.appendRow(rowData);
  
  // 格式美化：資料列置中對齊
  var lastRow = logSheet.getLastRow();
  if (lastRow > 1) {
    logSheet.getRange(lastRow, 1, 1, headers[0].length).setHorizontalAlignment("center");
  }

  
  Logger.log("已將通報紀錄寫入分頁: " + sheetName);
}

/**
 * 測試即時通報 (強制發送，忽略工作時間與狀態鎖定)
 */
function testNotifyForce() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheets()[0];
  var data = sheet.getDataRange().getValues();
  
  var threshold = 28.0;
  var emails = [];
  var lineIds = [];
  
  for (var i = 1; i < data.length; i++) {
    var name = String(data[i][0]).trim();
    var email = String(data[i][1]).trim();
    var lineId = String(data[i][2]).trim();
    var enabled = String(data[i][3]).trim().toUpperCase();
    
    if (name.toLowerCase().includes("threshold") || name.includes("溫度") || name.includes("閥值") || name.includes("閾值")) {
      var numMatch = email.match(/(\d+(?:\.\d+)?)/);
      if (numMatch) {
        threshold = parseFloat(numMatch[1]);
      }
      continue;
    }
    
    if (enabled !== "N" && enabled !== "NO" && enabled !== "FALSE") {
      if (email && email.includes("@")) {
        emails.push(email);
      }
      if (lineId) {
        var prefix = lineId.charAt(0).toUpperCase();
        if (prefix === "U" || prefix === "C" || prefix === "R") {
          lineIds.push(lineId);
        }
      }
    }
  }
  
  var apiKey = "CWA-718BCC42-A79F-4138-99BC-81D9C317BE28";
  var stationId = "C0G900";
  var apiUrl = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0001-001?Authorization=" + apiKey + "&StationId=" + stationId;
  
  var apiResponse = UrlFetchApp.fetch(apiUrl, {"muteHttpExceptions": true});
  if (apiResponse.getResponseCode() !== 200) {
    SpreadsheetApp.getUi().alert("【錯誤】CWA API 請求失敗，狀態碼: " + apiResponse.getResponseCode());
    return;
  }
  var apiData = JSON.parse(apiResponse.getContentText("UTF-8"));
  var stations = apiData.records.Station;
  if (!stations || stations.length === 0) {
    SpreadsheetApp.getUi().alert("【錯誤】CWA API 回傳空資料，StationId=" + stationId);
    return;
  }
  
  var s = stations[0];
  var we = s.WeatherElement;
  var rawObsTime = s.ObsTime.DateTime;
  var displayTime = rawObsTime ? rawObsTime.replace("T", " ").substring(0, 19) : "";
  
  var currentTemp = parseFloat(we.AirTemperature);
  
  if (currentTemp === -99) {
    SpreadsheetApp.getUi().alert("【錯誤】站點 " + stationId + " 觀測資料異常（-99），無法進行測試。");
    return;
  }
  
  var today = new Date();
  var formattedTime = Utilities.formatDate(today, "GMT+8", "yyyy-MM-dd HH:mm:ss");
  
  var notifySubject = "【測試通報】發送測試：環境溫度為 " + currentTemp + "°C";
  var notifyBody = "【" + sheet.getName() + " 測試通報】\n";
  notifyBody += "當前環境溫度：" + currentTemp + "°C (設定閾值 " + threshold + "°C)\n";
  notifyBody += "氣象觀測時間：" + displayTime + "\n";
  notifyBody += "測試觸發時間：" + formattedTime + "\n\n";
  notifyBody += "※ 此為手動測試通報，目的為驗證 LINE 與 Email 通報通道是否暢通。";
  
  var lineSent = false;
  var emailSent = false;
  
  var lineToken = "5GyVAKorqM7GsTi5+OdJNtEMJZuvGXU4OXEHWeSS+gnhkpkV0ZFCEb7M2KdTopUKPELADU+xIMadPUytJO0g1XDpq2pnYj/70KNDBcL0pBLutivXV9P6Ff76ylrHQ0dbILQsPd7pCGLFXMcCrmgcEQdB04t89/1O/w1cDnyilFU=";
  var userIds = [];
  var groupIds = [];
  for (var m = 0; m < lineIds.length; m++) {
    var prefix = lineIds[m].charAt(0).toUpperCase();
    if (prefix === "U") userIds.push(lineIds[m]);
    else if (prefix === "C" || prefix === "R") groupIds.push(lineIds[m]);
  }
  
  if (userIds.length > 0) {
    var multicastUrl = "https://api.line.me/v2/bot/message/multicast";
    var options = {
      "method": "post",
      "headers": {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + lineToken
      },
      "payload": JSON.stringify({
        "to": userIds,
        "messages": [{"type": "text", "text": notifyBody}]
      }),
      "muteHttpExceptions": true
    };
    var response = UrlFetchApp.fetch(multicastUrl, options);
    if (response.getResponseCode() === 200) lineSent = true;
  }
  
  for (var g = 0; g < groupIds.length; g++) {
    var pushUrl = "https://api.line.me/v2/bot/message/push";
    var options = {
      "method": "post",
      "headers": {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + lineToken
      },
      "payload": JSON.stringify({
        "to": groupIds[g],
        "messages": [{"type": "text", "text": notifyBody}]
      }),
      "muteHttpExceptions": true
    };
    var response = UrlFetchApp.fetch(pushUrl, options);
    if (response.getResponseCode() === 200) lineSent = true;
  }
  
  if (emails.length > 0) {
    try {
      MailApp.sendEmail({
        to: emails.join(","),
        subject: notifySubject,
        body: notifyBody
      });
      emailSent = true;
    } catch (e) {
      Logger.log("測試信件發送失敗: " + e.message);
    }
  }
  
  var statusArr = [];
  if (lineSent) statusArr.push("LINE");
  if (emailSent) statusArr.push("Email");
  var statusText = statusArr.length > 0 ? (statusArr.join(" & ") + " 已發送") : "無成功通道";
  
  SpreadsheetApp.getUi().alert("【測試通報發送完成】\n目前觀測環境溫度：" + currentTemp + "°C\n發送通道：" + statusText + "\n\n請確認您的 LINE 或是信箱是否收到測試訊息。");
}

/**
 * 手動清除狀態（測試與重置用）
 */
function clearNotifiedState() {
  var props = PropertiesService.getScriptProperties();
  props.deleteProperty("LAST_STATE");
  props.deleteProperty("LAST_NOTIFIED_DATE"); // 相容舊版鎖定
  SpreadsheetApp.getUi().alert("【成功】防重複狀態已重置！\n系統目前的防重複通知鎖定已清除，下一小時如果溫度超標將會再次觸發通報。");
}

/**
 * 手動或自動重設當前月份紀錄分頁的欄寬為最佳預設值
 */
function resetColumnWidths() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var today = new Date();
  var formattedMonth = Utilities.formatDate(today, "GMT+8", "yyyy-MM");
  var sheetName = "紀錄_" + formattedMonth;
  var logSheet = ss.getSheetByName(sheetName);
  
  if (logSheet) {
    logSheet.setColumnWidth(1, 170); // 通報時間
    logSheet.setColumnWidth(2, 140); // 溫度閾值設定 (°C)
    logSheet.setColumnWidth(3, 140); // 通報環境溫度 (°C)
    logSheet.setColumnWidth(4, 170); // 氣象觀測時間
    logSheet.setColumnWidth(5, 140); // 警報狀態
    logSheet.setColumnWidth(6, 200); // 通知狀態
    
    try {
      SpreadsheetApp.getUi().alert("【成功】已將當月紀錄分頁（" + sheetName + "）的欄寬重設為最佳預設值！");
    } catch (e) {
      // 靜態呼叫時無視 ui 錯誤
    }
  } else {
    try {
      SpreadsheetApp.getUi().alert("【提示】找不到當月紀錄分頁（" + sheetName + "），請等候系統自動建立或手動執行一次測試。");
    } catch (e) {}
  }
}

/**
 * 接收 LINE Webhook 事件與本機心跳同步信號
 */
function doPost(e) {
  try {
    var postData = JSON.parse(e.postData.contents);
    
    // 處理本機與雲端的同步與心跳信號
    if (postData.action === "heartbeat") {
      var props = PropertiesService.getScriptProperties();
      // 更新本機最後心跳時間為當前時間戳
      props.setProperty("LAST_LOCAL_HEARTBEAT", new Date().getTime().toString());
      
      var syncType = postData.type || "heartbeat";
      var localState = postData.local_state;
      var cloudState = props.getProperty("LAST_STATE") || "COOL";
      
      if (syncType === "update" && localState) {
        // 本機發送了更新狀態，雲端同步更新狀態
        props.setProperty("LAST_STATE", localState);
        cloudState = localState;
      }
      
      // 如果本機傳來了觀測資料，則寫入試算表紀錄
      if (postData.current_temp !== undefined) {
        try {
          var senderType = "本機執行";
          if (syncType === "heartbeat") {
            senderType += " (心跳)";
          }
          logNotificationToSheet(
            postData.threshold || 28.0, 
            postData.current_temp, 
            postData.obs_time || "", 
            postData.alert_state || "", 
            postData.status_text || "", 
            senderType
          );
        } catch (logErr) {
          Logger.log("本機心跳寫入試算表失敗: " + logErr.message);
        }
      }
      
      var response = {
        "status": "success",
        "cloud_state": cloudState
      };
      return ContentService.createTextOutput(JSON.stringify(response))
                           .setMimeType(ContentService.MimeType.JSON);
    }
    var events = postData.events;
    
    if (events && events.length > 0) {
      for (var i = 0; i < events.length; i++) {
        var event = events[i];
        
        // 只有收到文字訊息才處理
        if (event.type === "message" && event.message.type === "text") {
          var userText = event.message.text.trim().toLowerCase();
          
          // 只有當使用者輸入查詢關鍵字時才紀錄，防止群組平時聊天洗板試算表
          if (userText === "id" || userText === "查詢id" || userText === "查詢 id" || userText === "group id") {
            var source = event.source || {};
            var targetId = "";
            var typeText = "";
            
            if (source.type === "group") {
              targetId = source.groupId;
              typeText = "群組 ID";
            } else if (source.type === "room") {
              targetId = source.roomId;
              typeText = "聊天室 ID";
            } else if (source.type === "user") {
              targetId = source.userId;
              typeText = "個人 ID";
            }
            
            if (targetId) {
              var ss = SpreadsheetApp.getActiveSpreadsheet();
              var sheet = ss.getSheets()[0]; // 取得第一個工作表
              var today = new Date();
              var formattedTime = Utilities.formatDate(today, "GMT+8", "yyyy-MM-dd HH:mm:ss");
              
              // 在工作表最下方新增一列紀錄
              sheet.appendRow(["【自動查詢】" + typeText, "請複製右邊的 ID：", targetId, "查詢時間: " + formattedTime]);
            }
          }
        }
      }
    }
  } catch (err) {
    // 確保不會報錯
  }
  return ContentService.createTextOutput("OK");
}
```

4. 點選上方的 **「儲存專案 (Save project)」** 圖示。

---

## 🔑 第二步：首次執行與授權

1. 在編輯器上方下拉選單選擇 **`checkWeatherAndNotify`**。
2. 點選 **「執行 (Run)」** 按鈕。
3. 系統會跳出「需要授權」視窗，點選 **「審查權限」**。

4. 選擇您的 Google 帳戶 -> **「進階 (Advanced)」 -> 「前往『未命名專案』(安全)」 -> 「允許 (Allow)」**。
5. 執行完成後，您可以在下方的「執行記錄」中看見輸出狀態！

---

## ⏰ 第三步：設定每小時自動排程 (狀態監控)

為了每小時自動比對即時溫度，且在超標或回落時第一時間通知人員，請如此設定：
1. 在 Apps Script 左側邊欄中，點擊 **「觸發條件 (Triggers)」**（時鐘圖示）。
2. 點選右下角的 **「新增觸發條件 (Add Trigger)」**。
3. 進行以下設定：
   * 選擇要執行的功能：**`checkWeatherAndNotify`**
   * 選擇應執行的部署作業：**`主要 (或您目前的部署版本)`**
   * 選取活動來源：**`時間驅動 (Time-driven)`**
   * 選取時間型觸發條件類型：**`小時定時器 (Hour timer)`**
   * 選取間隔時間：**`每小時 (Every hour)`**
4. 點選 **「儲存」**。

大功告成！Google 伺服器每小時會自動抓取氣象署最新環境溫度觀測資料，當發現溫度「首次破閾值」或「首次回落至閾值以下」時，會自動發送通知，並隨時寫入事件紀錄分頁！

---

## 🕹️ 第四步：使用頂端自訂選單或圖形按鈕（免進程式碼測試）

貼上新版程式碼並儲存後，重新整理 Google 試算表網頁，您可以使用以下兩種方式執行測試與重置：

### 方法 A：使用頂端自訂選單
1. 重新整理試算表後，頂端選單列將會自動出現：**`🌡️ 溫度通報系統`**。
2. 點選它會展開三個子項目：
   * **`🧪 測試即時通報 (強制發送)`**：直接抓取目前的彰化縣線西鄉環境溫度，並強制發送通知（會忽略工作時間限制與前次狀態機鎖定）。發送完成後會自動彈出提示視窗。
   * **`🔄 重置防重複鎖定`**：一鍵清除防重複通知鎖定，下一小時如果溫度超標將會再次觸發通報。
   * **`📏 重設欄寬為最佳預設`**：一鍵將當前月份的紀錄分頁欄位寬度重設為最美觀的預設寬度（通報時間 170px, 欄位各 140-200px），避免欄位擠壓或跑掉。

### 方法 B：插入圖形按鈕（直接放在工作表內）
1. 在您的工作表點選 **「插入」 -> 「繪圖」**。
2. 畫三個按鈕形狀（例如矩形），加上文字「🧪 測試通報」、「🔄 重置重複鎖定」與「📏 重設欄寬」。
3. 右鍵點擊按鈕圖示，再點選圖示右上角的 **「三個點 (更多動作)」 -> 「指派指令碼 (Assign script)」**。
   * 「測試通報」按鈕指派：**`testNotifyForce`**
   * 「重置重複鎖定」按鈕指派：**`clearNotifiedState`**
   * 「重設欄寬」按鈕指派：**`resetColumnWidths`**
4. 指派完成後，任何人員只要在試算表中直接點擊按鈕，就能直接觸發對應功能！

---

## 📝 版本更新與修改紀錄 (Changelog)

1. **全面改用一般環境溫度**：
   - 根據現場人員反饋，監控指標已從「體感溫度」改為中央氣象署觀測站的「一般環境溫度 (AirTemperature)」。
2. **每小時持續寫入紀錄**：
   - 無論是否發送通報（如重複跳過或氣溫正常），系統每小時執行皆會將觀測值寫入 `紀錄_YYYY-MM` 分頁。
   - 新增本機執行時的「心跳寫入」機制：本機觀測完畢後會發送數據至雲端 Web App，由 Web App 代為寫入試算表，確保本機/雲端不論誰執行都有完整溫度觀測紀錄。
3. **設備降溫提醒**：
   - 高溫超標警報訊息內重新加入設備提示語：`※ 請相關人員開啟灑水設備降溫循環過濾器。`
4. **Bug 修復**：
   - 修復雲端程式碼 `testNotifyForce` 內誤用未定義變數 `currentAT` 的問題。
   - 修復雲端程式碼 `doPost` 內誤用未定義變數 `props` 的問題。
5. **紀錄表頭與分頁優化**：
   - 自動按月建立 `紀錄_YYYY-MM` 分頁。
   - 表頭採用全新欄位：`["通報時間", "溫度閾值設定 (°C)", "通報環境溫度 (°C)", "氣象觀測時間", "警報狀態", "通知狀態"]`。
   - 具備表頭自動平滑遷移功能，舊的紀錄分頁會在首次執行時自動轉換為新欄位名稱。
6. **群組 ID 查詢功能 (doPost Webhook)**：
   - 內建 `doPost(e)` Webhook 處理程式。
   - 防洗板機制：只有當使用者在 LINE 中傳送 `id` 或 `查詢id` 時，才會將取得的群組/個人 ID 自動寫入試算表第一個分頁最底端。
7. **LINE 推播相容性優化**：
   - LINE ID 大小寫字母自動容錯，支援個人 ID (Multicast) 與群組/聊天室 ID (Push)。
