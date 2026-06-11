/**
 * 當試算表開啟時，自動建立頂端自訂選單，方便人員點選測試與重置
 */
function onOpen() {
  var ui = SpreadsheetApp.getUi();
  ui.createMenu('🌡️ 溫度通報系統')
      .addItem('🧪 測試即時通報 (強制發送)', 'testNotifyForce')
      .addItem('⚙️ 套用設定並更新排程', 'applySettingsAndTriggers')
      .addItem('🔄 重置防重複鎖定', 'clearNotifiedState')
      .addItem('📏 重設欄寬為最佳預設', 'resetColumnWidths')
      .addToUi();
      
  // 開啟試算表時自動檢查並建立「系統設定」分頁
  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var configSheet = ss.getSheetByName("系統設定");
    if (!configSheet) {
      createDefaultConfigSheet(ss);
    }
  } catch (e) {}
}

/**
 * 網頁應用程式進入點：渲染 HMI 後台管理介面
 */
function doGet(e) {
  return HtmlService.createTemplateFromFile('Index')
      .evaluate()
      .setTitle('🌡️ 溫度通報系統 - 管理後台')
      .addMetaTag('viewport', 'width=device-width, initial-scale=1')
      .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

/**
 * 建立預設的「系統設定」分頁並美化排版
 */
function createDefaultConfigSheet(ss) {
  var configSheet = ss.insertSheet("系統設定");
  
  var headers = [["設定項目", "設定值", "說明"]];
  var data = [
    ["溫度警報閾值 (°C)", 28.0, "當環境溫度高於此溫度時發送高溫警報，回落低於此值時發送解除警報"],
    ["監測開始時間 (點)", 8, "每日開始監控的整點時間 (0-23)"],
    ["監測結束時間 (點)", 24, "每日結束監控的整點時間 (0-23，可跨夜如開始22、結束6)"],
    ["監測頻率 (分鐘)", 60, "監測執行間隔分鐘數，可設為 10, 15, 30, 60 等"],
    ["管理網頁密碼", "admin888", "進入 HMI 設定管理及聯絡人頁面所需的驗證密碼，預設為 admin888"]
  ];
  
  // 寫入標頭與資料
  configSheet.getRange(1, 1, 1, 3).setValues(headers);
  configSheet.getRange(2, 1, data.length, 3).setValues(data);
  
  // 美化表頭：深藍底色 (#1F4E79)、白字、粗體、置中
  configSheet.getRange(1, 1, 1, 3)
             .setBackground("#1F4E79")
             .setFontColor("#FFFFFF")
             .setFontWeight("bold")
             .setHorizontalAlignment("center");
             
  // 凍結第一列
  configSheet.setFrozenRows(1);
  
  // 資料列排版對齊
  configSheet.getRange(2, 1, data.length, 1).setHorizontalAlignment("center").setFontWeight("bold");
  configSheet.getRange(2, 2, data.length, 1).setHorizontalAlignment("center");
  configSheet.getRange(2, 3, data.length, 1).setHorizontalAlignment("left");
  
  // 設定適當欄寬
  configSheet.setColumnWidth(1, 160); // 設定項目
  configSheet.setColumnWidth(2, 100); // 設定值
  configSheet.setColumnWidth(3, 400); // 說明
  
  return configSheet;
}

/**
 * 讀取系統設定分頁中的配置參數 (具備自動建立與相容舊版之降級機制)
 */
function loadConfigFromSheet() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var configSheet = ss.getSheetByName("系統設定");
  
  // 如果找不到，自動建立預設設定分頁
  if (!configSheet) {
    try {
      configSheet = createDefaultConfigSheet(ss);
      Logger.log("「系統設定」分頁不存在，已自動建立並填入預設值。");
    } catch (e) {
      Logger.log("自動建立「系統設定」分頁失敗: " + e.message);
    }
  }
  
  var config = {
    threshold: 28.0,
    startHour: 8,
    endHour: 24,
    frequency: 60,
    password: "admin888"
  };
  
  if (!configSheet) {
    return config;
  }
  
  var data = configSheet.getDataRange().getValues();
  for (var i = 1; i < data.length; i++) {
    var key = String(data[i][0]).trim();
    var val = String(data[i][1]).trim();
    var key_lower = key.toLowerCase();
    
    if (key_lower.includes("threshold") || key.includes("溫度") || key.includes("閥值") || key.includes("閾值")) {
      var num = parseFloat(val);
      if (!isNaN(num)) config.threshold = num;
    } else if (key_lower.includes("start") || key.includes("開始") || key.includes("啟動")) {
      var num = parseInt(val);
      if (!isNaN(num)) config.startHour = num;
    } else if (key_lower.includes("end") || key.includes("結束") || key.includes("停止")) {
      var num = parseInt(val);
      if (!isNaN(num)) config.endHour = num;
    } else if (key_lower.includes("frequency") || key.includes("頻率") || key.includes("間隔")) {
      var num = parseInt(val);
      if (!isNaN(num)) config.frequency = num;
    } else if (key_lower.includes("password") || key.includes("密碼")) {
      config.password = val;
    }
  }
  
  return config;
}

/**
 * 手動或選單觸發：套用設定並更新雲端時間觸發器頻率
 */
function applySettingsAndTriggers() {
  var config = loadConfigFromSheet();
  updateTriggerFrequency(config.frequency);
  
  try {
    SpreadsheetApp.getUi().alert(
      "【設定套用成功】\n\n" +
      "系統已成功套用新參數：\n" +
      "1. 溫度警報閾值：" + config.threshold + "°C\n" +
      "2. 監測時段：" + config.startHour + ":00 - " + config.endHour + ":00\n" +
      "3. 監測頻率：" + config.frequency + " 分鐘\n\n" +
      "※ 雲端 Apps Script 定時觸發器已重新建立並開始生效！"
    );
  } catch (e) {
    Logger.log("更新觸發器成功，頻率：" + config.frequency + " 分鐘");
  }
}

/**
 * 動態重建指定分鐘數的定時觸發器
 */
function updateTriggerFrequency(minutes) {
  var triggers = ScriptApp.getProjectTriggers();
  for (var i = 0; i < triggers.length; i++) {
    if (triggers[i].getHandlerFunction() === 'checkWeatherAndNotify') {
      ScriptApp.deleteTrigger(triggers[i]);
    }
  }
  
  // 建立新時間型觸發條件，根據分鐘數對應至 Apps Script 支援的間隔
  if (minutes === 10) {
    ScriptApp.newTrigger('checkWeatherAndNotify').timeBased().everyMinutes(10).create();
  } else if (minutes === 15) {
    ScriptApp.newTrigger('checkWeatherAndNotify').timeBased().everyMinutes(15).create();
  } else if (minutes === 30) {
    ScriptApp.newTrigger('checkWeatherAndNotify').timeBased().everyMinutes(30).create();
  } else if (minutes === 60) {
    ScriptApp.newTrigger('checkWeatherAndNotify').timeBased().everyHours(1).create();
  } else if (minutes === 120) {
    ScriptApp.newTrigger('checkWeatherAndNotify').timeBased().everyHours(2).create();
  } else {
    // 預設一小時
    ScriptApp.newTrigger('checkWeatherAndNotify').timeBased().everyHours(1).create();
  }
}

/**
 * RPC 函數群：獲取密碼認證結果
 */
function verifyPassword(enteredPassword) {
  var config = loadConfigFromSheet();
  if (config.password === enteredPassword) {
    return { success: true };
  } else {
    return { success: false, message: "管理驗證密碼錯誤，請重新輸入！" };
  }
}

/**
 * RPC 函數群：獲取儀表板綜合資訊
 */
function getDashboardData() {
  var config = loadConfigFromSheet();
  var props = PropertiesService.getScriptProperties();
  var lastLocalHeartbeat = props.getProperty("LAST_LOCAL_HEARTBEAT") || "";
  var lastState = props.getProperty("LAST_STATE") || "COOL";
  
  var currentTemp = -99;
  var displayTime = "";
  try {
    var apiKey = "CWA-718BCC42-A79F-4138-99BC-81D9C317BE28";
    var stationId = "C2G870"; // 伸港站
    var apiUrl = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001?Authorization=" + apiKey + "&StationId=" + stationId;
    var apiResponse = UrlFetchApp.fetch(apiUrl, {"muteHttpExceptions": true});
    if (apiResponse.getResponseCode() === 200) {
      var apiData = JSON.parse(apiResponse.getContentText("UTF-8"));
      var stations = apiData.records.Station;
      if (stations && stations.length > 0) {
        var s = stations[0];
        currentTemp = parseFloat(s.WeatherElement.AirTemperature);
        var rawTime = s.ObsTime.DateTime;
        displayTime = rawTime ? rawTime.replace("T", " ").substring(0, 19) : "";
      }
    }
  } catch (err) {}
  
  return {
    currentTemp: currentTemp,
    obsTime: displayTime,
    threshold: config.threshold,
    startHour: config.startHour,
    endHour: config.endHour,
    frequency: config.frequency,
    lastState: lastState,
    lastLocalHeartbeat: lastLocalHeartbeat,
    nowTime: new Date().getTime().toString()
  };
}

/**
 * RPC 函數群：儲存系統參數並重建定時排程
 */
function saveSystemSettings(settings, password) {
  var config = loadConfigFromSheet();
  if (config.password !== password) {
    throw new Error("管理權限驗證失敗，無法修改設定！");
  }
  
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var configSheet = ss.getSheetByName("系統設定");
  if (!configSheet) {
    configSheet = createDefaultConfigSheet(ss);
  }
  
  var data = [
    ["溫度警報閾值 (°C)", parseFloat(settings.threshold), "當環境溫度高於此溫度時發送高溫警報，回落低於此值時發送解除警報"],
    ["監測開始時間 (點)", parseInt(settings.startHour), "每日開始監控的整點時間 (0-23)"],
    ["監測結束時間 (點)", parseInt(settings.endHour), "每日結束監控的整點時間 (0-23，可跨夜如開始22、結束6)"],
    ["監測頻率 (分鐘)", parseInt(settings.frequency), "監測執行間隔分鐘數，可設為 10, 15, 30, 60 等"],
    ["管理網頁密碼", settings.password || config.password, "進入 HMI 設定管理及聯絡人頁面所需的驗證密碼，預設為 admin888"]
  ];
  
  configSheet.getRange(2, 1, data.length, 3).setValues(data);
  updateTriggerFrequency(parseInt(settings.frequency));
  return {status: "success"};
}

/**
 * RPC 函數群：獲取聯絡人名冊
 */
function getContactsData() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheets()[0];
  var values = sheet.getDataRange().getValues();
  var contacts = [];
  for (var i = 1; i < values.length; i++) {
    var name = String(values[i][0]).trim();
    var name_lower = name.toLowerCase();
    var email = String(values[i][1]).trim();
    var lineId = String(values[i][2]).trim();
    var enabled = String(values[i][3]).trim().toUpperCase();
    
    if (name_lower.includes("threshold") || name.includes("溫度") || name.includes("閥值") || name.includes("閾值") ||
        name_lower.includes("start") || name.includes("開始") || name.includes("啟動") ||
        name_lower.includes("end") || name.includes("結束") || name.includes("停止") ||
        name_lower.includes("frequency") || name.includes("頻率") || name.includes("間隔") ||
        name_lower.includes("password") || name.includes("密碼")) {
      continue;
    }
    
    if (name === "" && email === "" && lineId === "") continue;
    
    contacts.push({
      name: name,
      email: email,
      lineId: lineId,
      enabled: (enabled !== "N" && enabled !== "NO" && enabled !== "FALSE")
    });
  }
  return contacts;
}

/**
 * RPC 函數群：更新聯絡人名冊 (會保留舊設定行)
 */
function saveContactsData(contactsList, password) {
  var config = loadConfigFromSheet();
  if (config.password !== password) {
    throw new Error("管理權限驗證失敗，無法修改聯絡人名單！");
  }

  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheets()[0];
  var oldValues = sheet.getDataRange().getValues();
  var newValues = [];
  newValues.push(oldValues[0]); // Header
  
  // 濾出舊設定行並加入
  for (var i = 1; i < oldValues.length; i++) {
    var name = String(oldValues[i][0]).trim();
    var name_lower = name.toLowerCase();
    if (name_lower.includes("threshold") || name.includes("溫度") || name.includes("閥值") || name.includes("閾值") ||
        name_lower.includes("start") || name.includes("開始") || name.includes("啟動") ||
        name_lower.includes("end") || name.includes("結束") || name.includes("停止") ||
        name_lower.includes("frequency") || name.includes("頻率") || name.includes("間隔") ||
        name_lower.includes("password") || name.includes("密碼")) {
      newValues.push(oldValues[i]);
    }
  }
  
  // 加入新聯絡人
  for (var j = 0; j < contactsList.length; j++) {
    var c = contactsList[j];
    newValues.push([
      c.name || "",
      c.email || "",
      c.lineId || "",
      c.enabled ? "Y" : "N"
    ]);
  }
  
  sheet.clearContents();
  sheet.getRange(1, 1, newValues.length, 4).setValues(newValues);
  return {status: "success"};
}

/**
 * RPC 函數群：載入當月通報歷史明細
 */
function getHistoryLogs() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var today = new Date();
  var formattedMonth = Utilities.formatDate(today, "GMT+8", "yyyy-MM");
  var sheetName = "紀錄_" + formattedMonth;
  var logSheet = ss.getSheetByName(sheetName);
  if (!logSheet) {
    return [];
  }
  
  var values = logSheet.getDataRange().getValues();
  var logs = [];
  for (var i = values.length - 1; i >= 1; i--) {
    logs.push({
      time: String(values[i][0]),
      threshold: parseFloat(values[i][1]),
      temp: parseFloat(values[i][2]),
      obsTime: String(values[i][3]),
      alertState: String(values[i][4]),
      statusText: String(values[i][5])
    });
  }
  return logs;
}

/**
 * CWA 環境溫度監控與 LINE/Email 自動通報系統 (Google Apps Script 雲端 CWA Open Data API 版)
 */
function checkWeatherAndNotify() {
  var config = loadConfigFromSheet();
  var threshold = config.threshold;
  var startHour = config.startHour;
  var endHour = config.endHour;
  var frequency = config.frequency;

  var heartbeatTimeoutMinutes = Math.max(25, frequency * 2.5);
  var properties = PropertiesService.getScriptProperties();
  var lastLocalHeartbeat = properties.getProperty("LAST_LOCAL_HEARTBEAT");
  if (lastLocalHeartbeat) {
    var lastTime = parseInt(lastLocalHeartbeat);
    var nowTime = new Date().getTime();
    var diffMinutes = (nowTime - lastTime) / (1000 * 60);
    if (diffMinutes < heartbeatTimeoutMinutes) {
      Logger.log("偵測到本機近期已執行（約 " + Math.round(diffMinutes) + " 分鐘前），雲端備援跳過本次排程。");
      return;
    }
  }

  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheets()[0];
  var data = sheet.getDataRange().getValues();
  
  var emails = [];
  var lineIds = [];
  
  for (var i = 1; i < data.length; i++) {
    var name = String(data[i][0]).trim();
    var name_lower = name.toLowerCase();
    var email = String(data[i][1]).trim();
    var lineId = String(data[i][2]).trim();
    var enabled = String(data[i][3]).trim().toUpperCase();
    
    if (name_lower.includes("threshold") || name.includes("溫度") || name.includes("閥值") || name.includes("閾值") ||
        name_lower.includes("start") || name.includes("開始") || name.includes("啟動") ||
        name_lower.includes("end") || name.includes("結束") || name.includes("停止") ||
        name_lower.includes("frequency") || name.includes("頻率") || name.includes("間隔") ||
        name_lower.includes("password") || name.includes("密碼")) {
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
  
  var today = new Date();
  var currentHour = parseInt(Utilities.formatDate(today, "GMT+8", "HH"));
  var isInTimeWindow = false;
  if (startHour < endHour) {
    isInTimeWindow = (currentHour >= startHour && currentHour < endHour);
  } else {
    isInTimeWindow = (currentHour >= startHour || currentHour < endHour);
  }
  
  if (!isInTimeWindow) {
    Logger.log("目前時間為 " + currentHour + " 點，不在監測時段 (" + startHour + ":00 - " + endHour + ":00) 內，跳過執行。");
    return;
  }
  
  Logger.log("當前警報溫度閥值設定為: " + threshold + "°C");
  Logger.log("Email 收件人名單: " + emails);
  Logger.log("LINE 推播名單: " + lineIds);
  
  if (emails.length === 0 && lineIds.length === 0) {
    Logger.log("偵測不到任何有效的啟用收件者，停止執行。");
    return;
  }
  
  var apiKey = "CWA-718BCC42-A79F-4138-99BC-81D9C317BE28";
  var stationId = "C2G870"; // 伸港站
  var apiUrl = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001?Authorization=" + apiKey + "&StationId=" + stationId;
  
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
  var rawObsTime = s.ObsTime.DateTime;
  var displayTime = rawObsTime ? rawObsTime.replace("T", " ").substring(0, 19) : "";
  var currentTemp = parseFloat(we.AirTemperature);
  
  if (currentTemp === -99) {
    Logger.log("站點 " + stationId + " 觀測環境溫度異常（-99），停止執行。");
    return;
  }
  
  Logger.log("觀測時間: " + displayTime + "，環境溫度: " + currentTemp + "°C");
  
  var lastState = properties.getProperty("LAST_STATE");
  var shouldNotify = false;
  var isHot = currentTemp > threshold;
  var alertStateText = "";
  var notifySubject = "";
  var notifyBody = "";
  var formattedTime = Utilities.formatDate(today, "GMT+8", "yyyy-MM-dd HH:mm:ss");
  
  if (isHot) {
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
    if (lastState === "HOT") {
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
  
  if (shouldNotify) {
    Logger.log("觸發通知：「" + notifySubject + "」");
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
        Logger.log("電子郵件寄送失敗: " + e.message);
      }
    }
    
    if (lineSent || emailSent) {
      properties.setProperty("LAST_STATE", isHot ? "HOT" : "COOL");
    }
  }
  
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
  
  var formattedMonth = Utilities.formatDate(today, "GMT+8", "yyyy-MM"); 
  var formattedTime = Utilities.formatDate(today, "GMT+8", "yyyy-MM-dd HH:mm:ss");
  
  var sheetName = "紀錄_" + formattedMonth;
  var logSheet = ss.getSheetByName(sheetName);
  
  var headers = [
    ["通報時間", "溫度閾值設定 (°C)", "通報環境溫度 (°C)", "氣象觀測時間", "警報狀態", "通知狀態"]
  ];
  
  if (!logSheet) {
    logSheet = ss.insertSheet(sheetName);
    logSheet.getRange(1, 1, 1, headers[0].length).setValues(headers);
    
    var headerRange = logSheet.getRange(1, 1, 1, headers[0].length);
    headerRange.setBackground("#1F4E79")
               .setFontColor("#FFFFFF")
               .setFontWeight("bold")
               .setHorizontalAlignment("center");
    
    logSheet.setFrozenRows(1);
    
    logSheet.setColumnWidth(1, 170); // 通報時間
    logSheet.setColumnWidth(2, 140); // 溫度閾值設定 (°C)
    logSheet.setColumnWidth(3, 140); // 通報環境溫度 (°C)
    logSheet.setColumnWidth(4, 170); // 氣象觀測時間
    logSheet.setColumnWidth(5, 140); // 警報狀態
    logSheet.setColumnWidth(6, 200); // 通知狀態
  } else {
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
  
  var rowData = [
    formattedTime, 
    threshold, 
    currentTemp, 
    displayTime, 
    alertStateText, 
    finalStatusText
  ];
  
  logSheet.appendRow(rowData);
  
  var lastRow = logSheet.getLastRow();
  if (lastRow > 1) {
    logSheet.getRange(lastRow, 1, 1, headers[0].length).setHorizontalAlignment("center");
  }
  Logger.log("已將通報紀錄寫入分頁: " + sheetName);
}

/**
 * 測試即時通報 (強制發送，忽略工作時間與狀態鎖定)
 */
function testNotifyForce(password) {
  var config = loadConfigFromSheet();
  var isSpreadsheetUI = false;
  try {
    SpreadsheetApp.getUi();
    isSpreadsheetUI = true;
  } catch (e) {}
  
  if (!isSpreadsheetUI) {
    if (config.password !== password) {
      throw new Error("管理權限驗證失敗，無法發送測試通報！");
    }
  }

  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheets()[0];
  var data = sheet.getDataRange().getValues();
  var threshold = config.threshold;
  
  var emails = [];
  var lineIds = [];
  
  for (var i = 1; i < data.length; i++) {
    var name = String(data[i][0]).trim();
    var name_lower = name.toLowerCase();
    var email = String(data[i][1]).trim();
    var lineId = String(data[i][2]).trim();
    var enabled = String(data[i][3]).trim().toUpperCase();
    
    if (name_lower.includes("threshold") || name.includes("溫度") || name.includes("閥值") || name.includes("閾值") ||
        name_lower.includes("start") || name.includes("開始") || name.includes("啟動") ||
        name_lower.includes("end") || name.includes("結束") || name.includes("停止") ||
        name_lower.includes("frequency") || name.includes("頻率") || name.includes("間隔") ||
        name_lower.includes("password") || name.includes("密碼")) {
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
  var stationId = "C2G870"; // 伸港站
  var apiUrl = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001?Authorization=" + apiKey + "&StationId=" + stationId;
  
  var apiResponse = UrlFetchApp.fetch(apiUrl, {"muteHttpExceptions": true});
  if (apiResponse.getResponseCode() !== 200) {
    if (isSpreadsheetUI) {
      SpreadsheetApp.getUi().alert("【錯誤】CWA API 請求失敗，狀態碼: " + apiResponse.getResponseCode());
    } else {
      throw new Error("CWA API 請求失敗，狀態碼: " + apiResponse.getResponseCode());
    }
    return;
  }
  var apiData = JSON.parse(apiResponse.getContentText("UTF-8"));
  var stations = apiData.records.Station;
  if (!stations || stations.length === 0) {
    if (isSpreadsheetUI) {
      SpreadsheetApp.getUi().alert("【錯誤】CWA API 回傳空資料，StationId=" + stationId);
    } else {
      throw new Error("CWA API 回傳空資料");
    }
    return;
  }
  
  var s = stations[0];
  var we = s.WeatherElement;
  var rawObsTime = s.ObsTime.DateTime;
  var displayTime = rawObsTime ? rawObsTime.replace("T", " ").substring(0, 19) : "";
  var currentTemp = parseFloat(we.AirTemperature);
  
  if (currentTemp === -99) {
    if (isSpreadsheetUI) {
      SpreadsheetApp.getUi().alert("【錯誤】站點 " + stationId + " 觀測資料異常（-99），無法進行測試。");
    } else {
      throw new Error("站點氣溫觀測值異常");
    }
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
  
  if (isSpreadsheetUI) {
    SpreadsheetApp.getUi().alert("【測試通報發送完成】\n目前觀測環境溫度：" + currentTemp + "°C\n發送通道：" + statusText + "\n\n請確認您的 LINE 或是信箱是否收到測試訊息。");
  } else {
    return { status: "success", temp: currentTemp, channels: statusText };
  }
}

/**
 * 手動清除狀態（測試與重置用）
 */
function clearNotifiedState(password) {
  var config = loadConfigFromSheet();
  var isSpreadsheetUI = false;
  try {
    SpreadsheetApp.getUi();
    isSpreadsheetUI = true;
  } catch (e) {}
  
  if (!isSpreadsheetUI) {
    if (config.password !== password) {
      throw new Error("管理權限驗證失敗，無法清除重複狀態鎖定！");
    }
  }

  var props = PropertiesService.getScriptProperties();
  props.deleteProperty("LAST_STATE");
  props.deleteProperty("LAST_NOTIFIED_DATE"); 
  
  if (isSpreadsheetUI) {
    SpreadsheetApp.getUi().alert("【成功】防重複狀態已重置！\n系統目前的防重複通知鎖定已清除，下一小時如果溫度超標將會再次觸發通報。");
  } else {
    return { status: "success" };
  }
}

/**
 * 手動或自動重設當前月份紀錄分頁的欄寬為最佳預設值
 */
function resetColumnWidths(password) {
  var config = loadConfigFromSheet();
  var isSpreadsheetUI = false;
  try {
    SpreadsheetApp.getUi();
    isSpreadsheetUI = true;
  } catch (e) {}
  
  if (!isSpreadsheetUI) {
    if (config.password !== password) {
      throw new Error("管理權限驗證失敗，無法重設紀錄欄寬！");
    }
  }

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
    
    if (isSpreadsheetUI) {
      SpreadsheetApp.getUi().alert("【成功】已將當月紀錄分頁（" + sheetName + "）的欄寬重設為最佳預設值！");
    } else {
      return { status: "success" };
    }
  } else {
    if (isSpreadsheetUI) {
      SpreadsheetApp.getUi().alert("【提示】找不到當月紀錄分頁（" + sheetName + "），請等候系統自動建立或手動執行一次測試。");
    } else {
      throw new Error("找不到當月紀錄分頁（" + sheetName + "）");
    }
  }
}

/**
 * 接收 LINE Webhook 事件與本機心跳同步信號
 */
function doPost(e) {
  try {
    var postData = JSON.parse(e.postData.contents);
    
    if (postData.action === "heartbeat") {
      var props = PropertiesService.getScriptProperties();
      props.setProperty("LAST_LOCAL_HEARTBEAT", new Date().getTime().toString());
      
      var syncType = postData.type || "heartbeat";
      var localState = postData.local_state;
      var cloudState = props.getProperty("LAST_STATE") || "COOL";
      
      if (syncType === "update" && localState) {
        props.setProperty("LAST_STATE", localState);
        cloudState = localState;
      }
      
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
        
        if (event.type === "message" && event.message.type === "text") {
          var userText = event.message.text.trim().toLowerCase();
          
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
              var sheet = ss.getSheets()[0]; 
              var today = new Date();
              var formattedTime = Utilities.formatDate(today, "GMT+8", "yyyy-MM-dd HH:mm:ss");
              sheet.appendRow(["【自動查詢】" + typeText, "請複製右邊的 ID：", targetId, "查詢時間: " + formattedTime]);
            }
          }
        }
      }
    }
  } catch (err) {}
  return ContentService.createTextOutput("OK");
}
