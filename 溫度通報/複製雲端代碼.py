#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自動在本地生成 Code.gs 與 Index.html，並提供複製到剪貼簿功能 (v4.0 HMI 人機介面版)
"""

import os
import sys
import subprocess

# Google Apps Script 門面/後端程式碼 (Code.gs)
GAS_CODE = r"""/**
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
    ["監測頻率 (分鐘)", 60, "監測執行間隔分鐘數，可設為 10, 15, 30, 60 等"]
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
    frequency: 60
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
function saveSystemSettings(settings) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var configSheet = ss.getSheetByName("系統設定");
  if (!configSheet) {
    configSheet = createDefaultConfigSheet(ss);
  }
  
  var data = [
    ["溫度警報閾值 (°C)", parseFloat(settings.threshold), "當環境溫度高於此溫度時發送高溫警報，回落低於此值時發送解除警報"],
    ["監測開始時間 (點)", parseInt(settings.startHour), "每日開始監控的整點時間 (0-23)"],
    ["監測結束時間 (點)", parseInt(settings.endHour), "每日結束監控的整點時間 (0-23，可跨夜如開始22、結束6)"],
    ["監測頻率 (分鐘)", parseInt(settings.frequency), "監測執行間隔分鐘數，可設為 10, 15, 30, 60 等"]
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
        name_lower.includes("frequency") || name.includes("頻率") || name.includes("間隔")) {
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
function saveContactsData(contactsList) {
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
        name_lower.includes("frequency") || name.includes("頻率") || name.includes("間隔")) {
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
        name_lower.includes("frequency") || name.includes("頻率") || name.includes("間隔")) {
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
function testNotifyForce() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheets()[0];
  var data = sheet.getDataRange().getValues();
  
  var config = loadConfigFromSheet();
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
        name_lower.includes("frequency") || name.includes("頻率") || name.includes("間隔")) {
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
  props.deleteProperty("LAST_NOTIFIED_DATE"); 
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
    } catch (e) {}
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
              sheet.appendRow(["【自動查詢】" + typeText, "請複製右邊 of ID：", targetId, "查詢時間: " + formattedTime]);
            }
          }
        }
      }
    }
  } catch (err) {}
  return ContentService.createTextOutput("OK");
}
"""

# Google Apps Script 前端網頁程式碼 (Index.html)
HTML_CODE = r"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>🌡️ 溫度通報系統 - 管理人機介面</title>
  <!-- Google Fonts: Outfit & Inter -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
  <!-- FontAwesome Icons -->
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  
  <style>
    /* CSS Variables & Design System */
    :root {
      --bg-main: #0b0f19;
      --bg-card: rgba(22, 28, 45, 0.65);
      --bg-card-hover: rgba(30, 41, 59, 0.8);
      --border-color: rgba(255, 255, 255, 0.08);
      --border-glow: rgba(59, 130, 246, 0.15);
      --primary: #3b82f6;
      --primary-hover: #2563eb;
      --primary-glow: rgba(59, 130, 246, 0.35);
      --success: #10b981;
      --success-glow: rgba(16, 185, 129, 0.2);
      --warning: #f59e0b;
      --warning-glow: rgba(245, 158, 11, 0.2);
      --danger: #ef4444;
      --danger-glow: rgba(239, 68, 68, 0.35);
      --text-main: #f3f4f6;
      --text-muted: #9ca3af;
      --font-outfit: 'Outfit', 'Inter', -apple-system, sans-serif;
      --font-inter: 'Inter', -apple-system, sans-serif;
      --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    body {
      font-family: var(--font-inter);
      background-color: var(--bg-main);
      background-image: 
        radial-gradient(at 0% 0%, rgba(17, 24, 39, 1) 0px, transparent 50%),
        radial-gradient(at 50% 0%, rgba(30, 58, 138, 0.15) 0px, transparent 50%),
        radial-gradient(at 100% 100%, rgba(15, 23, 42, 1) 0px, transparent 50%);
      background-attachment: fixed;
      color: var(--text-main);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      overflow-x: hidden;
    }

    /* Main Container Layout */
    .app-container {
      display: flex;
      flex: 1;
      position: relative;
    }

    /* Sidebar Navigation */
    aside {
      width: 260px;
      background: rgba(17, 24, 39, 0.7);
      backdrop-filter: blur(20px);
      border-right: 1px solid var(--border-color);
      display: flex;
      flex-direction: column;
      padding: 2rem 1.5rem;
      position: fixed;
      top: 0;
      bottom: 0;
      left: 0;
      z-index: 100;
      transition: var(--transition);
    }

    .brand-section {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      margin-bottom: 2.5rem;
      padding-left: 0.5rem;
    }

    .brand-logo {
      font-size: 1.75rem;
      filter: drop-shadow(0 0 8px var(--primary-glow));
    }

    .brand-title {
      font-family: var(--font-outfit);
      font-weight: 700;
      font-size: 1.2rem;
      letter-spacing: 0.5px;
      background: linear-gradient(135deg, #ffffff 30%, #9ca3af 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    .nav-menu {
      list-style: none;
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .nav-item {
      width: 100%;
    }

    .nav-link {
      display: flex;
      align-items: center;
      gap: 1rem;
      padding: 0.85rem 1rem;
      color: var(--text-muted);
      text-decoration: none;
      font-weight: 500;
      border-radius: 12px;
      transition: var(--transition);
      cursor: pointer;
      border: 1px solid transparent;
    }

    .nav-link:hover {
      color: var(--text-main);
      background: rgba(255, 255, 255, 0.03);
      border-color: rgba(255, 255, 255, 0.05);
    }

    .nav-link.active {
      color: #ffffff;
      background: rgba(59, 130, 246, 0.15);
      border-color: rgba(59, 130, 246, 0.25);
      box-shadow: 0 4px 15px rgba(59, 130, 246, 0.1);
      text-shadow: 0 0 10px rgba(59, 130, 246, 0.3);
    }

    .nav-link i {
      font-size: 1.1rem;
      width: 20px;
      text-align: center;
      transition: var(--transition);
    }

    .nav-link.active i {
      color: var(--primary);
      filter: drop-shadow(0 0 5px var(--primary-glow));
    }

    /* Main Content Area */
    main {
      flex: 1;
      margin-left: 260px;
      padding: 2rem 3rem;
      min-width: 0; /* Prevents flex items from overflowing */
      transition: var(--transition);
    }

    /* Header Panel */
    header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 2rem;
      border-bottom: 1px solid var(--border-color);
      padding-bottom: 1.5rem;
    }

    .header-title h1 {
      font-family: var(--font-outfit);
      font-weight: 700;
      font-size: 1.8rem;
      margin-bottom: 0.25rem;
    }

    .header-title p {
      color: var(--text-muted);
      font-size: 0.9rem;
    }

    /* Status Indicator Badge */
    .system-status-indicator {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      background: rgba(17, 24, 39, 0.5);
      border: 1px solid var(--border-color);
      padding: 0.5rem 1rem;
      border-radius: 99px;
      font-size: 0.85rem;
      font-weight: 500;
    }

    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background-color: var(--text-muted);
      display: inline-block;
    }

    .status-dot.online {
      background-color: var(--success);
      box-shadow: 0 0 10px var(--success-glow);
      animation: pulse-green 2s infinite;
    }

    .status-dot.offline {
      background-color: #6b7280;
    }

    @keyframes pulse-green {
      0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
      70% { box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
      100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }

    /* Tab Page Wrapper */
    .tab-content {
      display: none;
      animation: fadeIn 0.4s ease-out forwards;
    }

    .tab-content.active {
      display: block;
    }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(8px); }
      to { opacity: 1; transform: translateY(0); }
    }

    /* Glassmorphism Card Panels */
    .glass-card {
      background: var(--bg-card);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border: 1px solid var(--border-color);
      border-radius: 16px;
      padding: 1.75rem;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
      transition: var(--transition);
      position: relative;
      overflow: hidden;
    }

    .glass-card:hover {
      border-color: rgba(255, 255, 255, 0.15);
      box-shadow: 0 15px 35px rgba(0, 0, 0, 0.4), 0 0 20px var(--border-glow);
    }

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1.5rem;
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);
      padding-bottom: 0.75rem;
    }

    .card-title {
      font-family: var(--font-outfit);
      font-size: 1.15rem;
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .card-title i {
      color: var(--primary);
    }

    /* Grid Layouts */
    .grid-2 {
      display: grid;
      grid-template-columns: 1.2fr 1.8fr;
      gap: 1.5rem;
      margin-bottom: 1.5rem;
    }

    .grid-3 {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 1.5rem;
      margin-bottom: 1.5rem;
    }

    /* Dashboard: Gauge styling */
    .gauge-wrapper {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 1rem 0;
      text-align: center;
    }

    .gauge-svg {
      width: 200px;
      height: 200px;
      transform: rotate(-90deg);
      filter: drop-shadow(0 0 12px rgba(0,0,0,0.5));
    }

    .gauge-bg {
      fill: none;
      stroke: rgba(255, 255, 255, 0.05);
      stroke-width: 14;
    }

    .gauge-fill {
      fill: none;
      stroke: var(--primary);
      stroke-width: 14;
      stroke-linecap: round;
      transition: stroke-dashoffset 0.8s ease-out, stroke 0.5s ease;
      stroke-dasharray: 527.7; /* 2 * PI * r (r=84) */
      stroke-dashoffset: 527.7;
    }

    .gauge-text-group {
      position: absolute;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
    }

    .gauge-value {
      font-family: var(--font-outfit);
      font-size: 3rem;
      font-weight: 800;
      line-height: 1;
      letter-spacing: -1px;
    }

    .gauge-unit {
      font-size: 1rem;
      color: var(--text-muted);
      font-weight: 500;
      margin-top: 0.1rem;
    }

    .gauge-alert-pulse {
      position: absolute;
      width: 100%;
      height: 100%;
      top: 0;
      left: 0;
      border-radius: 16px;
      pointer-events: none;
      box-shadow: inset 0 0 0px var(--danger);
      transition: var(--transition);
    }

    .gauge-alert-active .gauge-alert-pulse {
      box-shadow: inset 0 0 30px rgba(239, 68, 68, 0.25);
      animation: alert-glow 1.5s infinite alternate;
      border: 1px solid rgba(239, 68, 68, 0.4);
    }

    @keyframes alert-glow {
      from { box-shadow: inset 0 0 20px rgba(239, 68, 68, 0.15), 0 0 5px rgba(239, 68, 68, 0.2); }
      to { box-shadow: inset 0 0 40px rgba(239, 68, 68, 0.45), 0 0 20px rgba(239, 68, 68, 0.5); }
    }

    /* Info Lists */
    .info-list {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .info-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 0.85rem 1rem;
      background: rgba(255, 255, 255, 0.02);
      border: 1px solid rgba(255, 255, 255, 0.03);
      border-radius: 12px;
    }

    .info-label {
      color: var(--text-muted);
      font-size: 0.9rem;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .info-value {
      font-weight: 600;
      font-size: 0.95rem;
    }

    .info-value.alert-danger {
      color: var(--danger);
      text-shadow: 0 0 10px rgba(239, 68, 68, 0.3);
    }

    .info-value.alert-success {
      color: var(--success);
      text-shadow: 0 0 10px rgba(16, 185, 129, 0.3);
    }

    /* Forms & Inputs */
    .form-group {
      margin-bottom: 1.25rem;
    }

    .form-label {
      display: block;
      color: var(--text-muted);
      font-size: 0.85rem;
      font-weight: 500;
      margin-bottom: 0.5rem;
    }

    .input-wrapper {
      position: relative;
      display: flex;
      align-items: center;
    }

    .input-wrapper i {
      position: absolute;
      left: 1rem;
      color: var(--text-muted);
      font-size: 0.95rem;
    }

    .form-control {
      width: 100%;
      background: rgba(17, 24, 39, 0.6);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 0.75rem 1rem 0.75rem 2.5rem;
      color: #ffffff;
      font-size: 0.95rem;
      font-family: var(--font-inter);
      transition: var(--transition);
    }

    .form-control:focus {
      outline: none;
      border-color: var(--primary);
      box-shadow: 0 0 0 3px var(--primary-glow);
      background: rgba(17, 24, 39, 0.8);
    }

    select.form-control {
      appearance: none;
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%239ca3af'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'/%3E%3C/svg%3E");
      background-repeat: no-repeat;
      background-position: right 1rem center;
      background-size: 1.2em;
      padding-right: 2.5rem;
    }

    /* Sliders */
    .slider-container {
      display: flex;
      align-items: center;
      gap: 1rem;
    }

    .range-slider {
      flex: 1;
      -webkit-appearance: none;
      width: 100%;
      height: 6px;
      border-radius: 99px;
      background: rgba(255, 255, 255, 0.1);
      outline: none;
      transition: background 0.3s;
    }

    .range-slider::-webkit-slider-thumb {
      -webkit-appearance: none;
      appearance: none;
      width: 18px;
      height: 18px;
      border-radius: 50%;
      background: var(--primary);
      box-shadow: 0 0 8px var(--primary-glow);
      cursor: pointer;
      transition: var(--transition);
    }

    .range-slider::-webkit-slider-thumb:hover {
      transform: scale(1.25);
    }

    .slider-val {
      font-family: var(--font-outfit);
      font-size: 1.25rem;
      font-weight: 700;
      width: 60px;
      text-align: right;
      color: var(--primary);
    }

    /* Buttons */
    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      color: var(--text-main);
      padding: 0.75rem 1.5rem;
      font-size: 0.95rem;
      font-weight: 600;
      cursor: pointer;
      transition: var(--transition);
      font-family: var(--font-inter);
      text-decoration: none;
    }

    .btn:hover {
      background: rgba(255, 255, 255, 0.1);
      border-color: rgba(255, 255, 255, 0.2);
      transform: translateY(-1px);
    }

    .btn:active {
      transform: translateY(0);
    }

    .btn-primary {
      background: var(--primary);
      border-color: var(--primary);
      box-shadow: 0 4px 15px rgba(59, 130, 246, 0.2);
    }

    .btn-primary:hover {
      background: var(--primary-hover);
      border-color: var(--primary-hover);
      box-shadow: 0 6px 20px rgba(59, 130, 246, 0.35);
    }

    .btn-danger {
      background: var(--danger);
      border-color: var(--danger);
      box-shadow: 0 4px 15px rgba(239, 68, 68, 0.2);
    }

    .btn-danger:hover {
      background: #dc2626;
      border-color: #dc2626;
      box-shadow: 0 6px 20px rgba(239, 68, 68, 0.35);
    }

    .btn-sm {
      padding: 0.45rem 0.85rem;
      font-size: 0.85rem;
      border-radius: 8px;
    }

    .btn-icon-only {
      width: 32px;
      height: 32px;
      padding: 0;
      border-radius: 8px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
    }

    /* Switch Component */
    .switch {
      position: relative;
      display: inline-block;
      width: 44px;
      height: 24px;
    }

    .switch input {
      opacity: 0;
      width: 0;
      height: 0;
    }

    .slider {
      position: absolute;
      cursor: pointer;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background-color: rgba(255, 255, 255, 0.1);
      transition: .4s;
      border-radius: 24px;
      border: 1px solid var(--border-color);
    }

    .slider:before {
      position: absolute;
      content: "";
      height: 16px;
      width: 16px;
      left: 3px;
      bottom: 3px;
      background-color: #ffffff;
      transition: .4s;
      border-radius: 50%;
      box-shadow: 0 1px 3px rgba(0,0,0,0.4);
    }

    input:checked + .slider {
      background-color: var(--success);
    }

    input:focus + .slider {
      box-shadow: 0 0 1px var(--success);
    }

    input:checked + .slider:before {
      transform: translateX(20px);
    }

    /* Custom Tables */
    .table-container {
      overflow-x: auto;
      border-radius: 12px;
      border: 1px solid var(--border-color);
      background: rgba(17, 24, 39, 0.3);
    }

    table {
      width: 100%;
      border-collapse: collapse;
      text-align: left;
      font-size: 0.9rem;
    }

    th {
      background: rgba(17, 24, 39, 0.7);
      padding: 1rem;
      font-weight: 600;
      color: var(--text-muted);
      border-bottom: 1px solid var(--border-color);
    }

    td {
      padding: 1rem;
      border-bottom: 1px solid rgba(255, 255, 255, 0.03);
      vertical-align: middle;
    }

    tr:last-child td {
      border-bottom: none;
    }

    tbody tr:hover {
      background: rgba(255, 255, 255, 0.01);
    }

    /* Status Badges */
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      padding: 0.25rem 0.65rem;
      border-radius: 99px;
      font-size: 0.75rem;
      font-weight: 600;
      line-height: 1;
    }

    .badge-danger {
      background: rgba(239, 68, 68, 0.15);
      color: #fca5a5;
      border: 1px solid rgba(239, 68, 68, 0.2);
    }

    .badge-success {
      background: rgba(16, 185, 129, 0.15);
      color: #a7f3d0;
      border: 1px solid rgba(16, 185, 129, 0.2);
    }

    .badge-warning {
      background: rgba(245, 158, 11, 0.15);
      color: #fde68a;
      border: 1px solid rgba(245, 158, 11, 0.2);
    }

    .badge-info {
      background: rgba(59, 130, 246, 0.15);
      color: #bfdbfe;
      border: 1px solid rgba(59, 130, 246, 0.2);
    }

    .badge-secondary {
      background: rgba(255, 255, 255, 0.08);
      color: var(--text-muted);
      border: 1px solid rgba(255, 255, 255, 0.05);
    }

    /* Toast Notification System */
    .toast-container {
      position: fixed;
      bottom: 2rem;
      right: 2rem;
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
      z-index: 9999;
    }

    .toast {
      background: rgba(17, 24, 39, 0.9);
      backdrop-filter: blur(10px);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 1rem 1.5rem;
      color: #ffffff;
      display: flex;
      align-items: center;
      gap: 0.85rem;
      box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
      animation: slideInRight 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards;
      min-width: 280px;
      max-width: 400px;
    }

    @keyframes slideInRight {
      from { transform: translateX(120%); opacity: 0; }
      to { transform: translateX(0); opacity: 1; }
    }

    .toast-success { border-left: 4px solid var(--success); }
    .toast-success i { color: var(--success); }
    .toast-danger { border-left: 4px solid var(--danger); }
    .toast-danger i { color: var(--danger); }
    .toast-warning { border-left: 4px solid var(--warning); }
    .toast-warning i { color: var(--warning); }
    .toast-info { border-left: 4px solid var(--primary); }
    .toast-info i { color: var(--primary); }

    .toast-close {
      margin-left: auto;
      cursor: pointer;
      color: var(--text-muted);
      transition: var(--transition);
    }

    .toast-close:hover {
      color: #ffffff;
    }

    /* Modal dialog */
    .modal-overlay {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.75);
      backdrop-filter: blur(4px);
      z-index: 1000;
      display: flex;
      align-items: center;
      justify-content: center;
      opacity: 0;
      pointer-events: none;
      transition: var(--transition);
    }

    .modal-overlay.active {
      opacity: 1;
      pointer-events: all;
    }

    .modal-content {
      background: rgba(22, 28, 45, 0.95);
      border: 1px solid var(--border-color);
      border-radius: 16px;
      width: 100%;
      max-width: 500px;
      padding: 2rem;
      box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6);
      transform: scale(0.95);
      transition: var(--transition);
    }

    .modal-overlay.active .modal-content {
      transform: scale(1);
    }

    .modal-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1.5rem;
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);
      padding-bottom: 0.75rem;
    }

    .modal-title {
      font-family: var(--font-outfit);
      font-size: 1.25rem;
      font-weight: 700;
    }

    .modal-close {
      cursor: pointer;
      color: var(--text-muted);
      font-size: 1.2rem;
      transition: var(--transition);
    }

    .modal-close:hover {
      color: #ffffff;
    }

    .modal-footer {
      display: flex;
      justify-content: flex-end;
      gap: 0.75rem;
      margin-top: 1.5rem;
      border-top: 1px solid rgba(255, 255, 255, 0.05);
      padding-top: 1rem;
    }

    /* Logs Controls */
    .logs-toolbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1rem;
      gap: 1rem;
      flex-wrap: wrap;
    }

    .search-input-group {
      flex: 1;
      max-width: 350px;
      position: relative;
    }

    .search-input-group i {
      position: absolute;
      left: 1rem;
      top: 50%;
      transform: translateY(-50%);
      color: var(--text-muted);
    }

    .search-input {
      width: 100%;
      background: rgba(17, 24, 39, 0.6);
      border: 1px solid var(--border-color);
      border-radius: 10px;
      padding: 0.6rem 1rem 0.6rem 2.5rem;
      color: #ffffff;
      font-size: 0.9rem;
      transition: var(--transition);
    }

    .search-input:focus {
      outline: none;
      border-color: var(--primary);
    }

    /* Pagination controls */
    .pagination {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .page-info {
      font-size: 0.85rem;
      color: var(--text-muted);
      margin: 0 0.5rem;
    }

    /* Skeleton Loading effect */
    .skeleton {
      background: linear-gradient(90deg, rgba(255,255,255,0.03) 25%, rgba(255,255,255,0.08) 50%, rgba(255,255,255,0.03) 75%);
      background-size: 200% 100%;
      animation: loading-pulse 1.5s infinite;
      border-radius: 4px;
    }

    .skeleton-text {
      height: 1rem;
      margin-bottom: 0.5rem;
      width: 100%;
    }

    .skeleton-avatar {
      height: 40px;
      width: 40px;
      border-radius: 50%;
    }

    @keyframes loading-pulse {
      0% { background-position: 200% 0; }
      100% { background-position: -200% 0; }
    }

    /* Responsive adjustments */
    @media (max-width: 992px) {
      .grid-2 {
        grid-template-columns: 1fr;
      }
      .grid-3 {
        grid-template-columns: 1fr;
      }
    }

    @media (max-width: 768px) {
      aside {
        width: 70px;
        padding: 2rem 0.5rem;
        align-items: center;
      }
      
      .brand-title, .nav-link-text {
        display: none;
      }

      .brand-section {
        justify-content: center;
        padding-left: 0;
      }

      .nav-link {
        justify-content: center;
        padding: 0.85rem;
      }

      main {
        margin-left: 70px;
        padding: 1.5rem;
      }

      header {
        flex-direction: column;
        align-items: flex-start;
        gap: 1rem;
      }

      .system-status-indicator {
        align-self: flex-start;
      }
    }
  </style>
</head>
<body>

  <div class="app-container">
    <!-- Sidebar -->
    <aside>
      <div class="brand-section">
        <span class="brand-logo">🌡️</span>
        <span class="brand-title">環境溫度監控</span>
      </div>
      
      <ul class="nav-menu">
        <li class="nav-item">
          <a class="nav-link active" onclick="switchTab('dashboard')">
            <i class="fa-solid fa-chart-line"></i>
            <span class="nav-link-text">狀態儀表板</span>
          </a>
        </li>
        <li class="nav-item">
          <a class="nav-link" onclick="switchTab('settings')">
            <i class="fa-solid fa-sliders"></i>
            <span class="nav-link-text">系統設定管理</span>
          </a>
        </li>
        <li class="nav-item">
          <a class="nav-link" onclick="switchTab('contacts')">
            <i class="fa-solid fa-users-gear"></i>
            <span class="nav-link-text">聯絡人名冊</span>
          </a>
        </li>
        <li class="nav-item">
          <a class="nav-link" onclick="switchTab('history')">
            <i class="fa-solid fa-history"></i>
            <span class="nav-link-text">歷史通報紀錄</span>
          </a>
        </li>
      </ul>
    </aside>

    <!-- Main Content -->
    <main>
      <!-- Header -->
      <header>
        <div class="header-title">
          <h1 id="page-heading">狀態儀表板</h1>
          <p id="page-subheading">即時監控 CWA 伸港觀測站環境氣溫與系統心跳</p>
        </div>
        
        <div class="system-status-indicator">
          <span class="status-dot offline" id="system-status-dot"></span>
          <span id="system-status-text">連線更新中...</span>
        </div>
      </header>

      <!-- TAB 1: Dashboard -->
      <div id="tab-dashboard" class="tab-content active">
        <div class="grid-2">
          
          <!-- Gauge Card -->
          <div class="glass-card gauge-alert-active" id="gauge-card">
            <div class="gauge-alert-pulse"></div>
            <div class="card-header">
              <div class="card-title">
                <i class="fa-solid fa-temperature-half"></i> 即時溫度觀測
              </div>
              <span class="badge badge-secondary" id="obs-station-id">伸港站 C2G870</span>
            </div>
            
            <div class="gauge-wrapper">
              <svg class="gauge-svg" viewBox="0 0 200 200">
                <circle class="gauge-bg" cx="100" cy="100" r="84"></circle>
                <circle class="gauge-fill" id="temp-gauge-fill" cx="100" cy="100" r="84"></circle>
              </svg>
              <div class="gauge-text-group">
                <span class="gauge-value" id="current-temp-val">--.-</span>
                <span class="gauge-unit">°C</span>
              </div>
            </div>
            
            <div style="text-align: center; margin-top: 1rem;">
              <span class="badge" id="alert-state-badge">偵測中...</span>
              <p style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.5rem;" id="obs-time-text">最新氣象發布時間：--</p>
            </div>
          </div>
          
          <!-- System Status & Details Card -->
          <div class="glass-card">
            <div class="card-header">
              <div class="card-title">
                <i class="fa-solid fa-server"></i> 系統活動與閥值狀態
              </div>
              <button class="btn btn-sm btn-icon-only" onclick="refreshDashboard()" title="重新載入即時狀態"><i class="fa-solid fa-arrows-rotate"></i></button>
            </div>
            
            <div class="info-list">
              <div class="info-item">
                <span class="info-label"><i class="fa-solid fa-bullseye"></i> 溫度告警閾值</span>
                <span class="info-value" id="dash-threshold">-- °C</span>
              </div>
              <div class="info-item">
                <span class="info-label"><i class="fa-solid fa-clock"></i> 每日監測時段</span>
                <span class="info-value" id="dash-time-window">--:00 - --:00</span>
              </div>
              <div class="info-item">
                <span class="info-label"><i class="fa-solid fa-repeat"></i> 雲端監測頻率</span>
                <span class="info-value" id="dash-frequency">-- 分鐘</span>
              </div>
              <div class="info-item">
                <span class="info-label"><i class="fa-solid fa-heartbeat"></i> 本機監控最後心跳</span>
                <span class="info-value" id="dash-last-heartbeat">讀取中...</span>
              </div>
              <div class="info-item">
                <span class="info-label"><i class="fa-solid fa-shield-halved"></i> 雲端備援機制</span>
                <span class="info-value alert-success" id="dash-backup-status">運作中</span>
              </div>
            </div>
          </div>
          
        </div>
        
        <!-- Quick Actions / Quick Instructions -->
        <div class="glass-card">
          <div class="card-header">
            <div class="card-title"><i class="fa-solid fa-bolt"></i> 快速工具與功能測試</div>
          </div>
          <div style="display: flex; gap: 1rem; flex-wrap: wrap;">
            <button class="btn btn-primary" onclick="triggerTestNotify()">
              <i class="fa-solid fa-paper-plane"></i> 測試即時通報 (發送 LINE 與 信件)
            </button>
            <button class="btn" onclick="triggerResetLock()">
              <i class="fa-solid fa-trash-can"></i> 重置防重複鎖定
            </button>
            <button class="btn" onclick="triggerResetColumnWidths()">
              <i class="fa-solid fa-arrows-left-right"></i> 重設紀錄分頁寬度
            </button>
          </div>
        </div>
      </div>

      <!-- TAB 2: Settings -->
      <div id="tab-settings" class="tab-content">
        <div class="glass-card" style="max-width: 650px; margin: 0 auto;">
          <div class="card-header">
            <div class="card-title">
              <i class="fa-solid fa-gear"></i> 系統溫度與時段設定
            </div>
          </div>
          
          <form id="settings-form" onsubmit="saveSettings(event)">
            <!-- Threshold slider -->
            <div class="form-group">
              <label class="form-label">高溫警報閾值設定 (°C)</label>
              <p style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 0.75rem;">當觀測溫度超過此設定值時，系統將發送高溫告警通知；回落此溫度以下時發送解除通知。</p>
              <div class="slider-container">
                <input type="range" class="range-slider" id="input-threshold" min="20.0" max="40.0" step="0.5" value="28.0" oninput="updateSliderVal(this.value)">
                <span class="slider-val" id="input-threshold-val">28.0</span>
              </div>
            </div>
            
            <!-- Start/End hours -->
            <div class="grid-2" style="margin-bottom: 0;">
              <div class="form-group">
                <label class="form-label" for="input-start-hour">監測開始時間 (點)</label>
                <div class="input-wrapper">
                  <i class="fa-solid fa-clock"></i>
                  <select class="form-control" id="input-start-hour" onchange="validateTimeWindow()">
                    <!-- Options populated by JS -->
                  </select>
                </div>
              </div>
              
              <div class="form-group">
                <label class="form-label" for="input-end-hour">監測結束時間 (點)</label>
                <div class="input-wrapper">
                  <i class="fa-solid fa-clock"></i>
                  <select class="form-control" id="input-end-hour" onchange="validateTimeWindow()">
                    <!-- Options populated by JS -->
                  </select>
                </div>
              </div>
            </div>
            
            <p id="time-window-tip" style="font-size: 0.8rem; color: var(--warning); margin-bottom: 1.25rem; display: none;"></p>
            
            <!-- Frequency dropdown -->
            <div class="form-group">
              <label class="form-label" for="input-frequency">環境監測檢查頻率 (分鐘)</label>
              <p style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 0.5rem;">設定雲端定時檢查的頻率（儲存時會自動同步調整 GAS 雲端時間觸發器）。</p>
              <div class="input-wrapper">
                <i class="fa-solid fa-arrows-spin"></i>
                <select class="form-control" id="input-frequency">
                  <option value="10">10 分鐘 (密集監測)</option>
                  <option value="15">15 分鐘</option>
                  <option value="30">30 分鐘</option>
                  <option value="60">60 分鐘 (一般頻率 - 預設)</option>
                  <option value="120">120 分鐘 (低頻率)</option>
                </select>
              </div>
            </div>
            
            <div style="margin-top: 2rem; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 1.5rem; display: flex; justify-content: flex-end;">
              <button type="submit" class="btn btn-primary" id="btn-save-settings">
                <i class="fa-solid fa-floppy-disk"></i> 儲存並套用設定
              </button>
            </div>
          </form>
        </div>
      </div>

      <!-- TAB 3: Contacts -->
      <div id="tab-contacts" class="tab-content">
        <div class="glass-card">
          <div class="card-header">
            <div class="card-title">
              <i class="fa-solid fa-users"></i> 通報聯絡人清單
            </div>
            <button class="btn btn-primary btn-sm" onclick="openAddContactModal()">
              <i class="fa-solid fa-plus"></i> 新增聯絡收件人
            </button>
          </div>
          
          <div class="table-container">
            <table>
              <thead>
                <tr>
                  <th>姓名</th>
                  <th>電子郵件 (Email)</th>
                  <th>LINE ID (個人/群組)</th>
                  <th style="width: 100px; text-align: center;">啟用狀態</th>
                  <th style="width: 100px; text-align: center;">操作</th>
                </tr>
              </thead>
              <tbody id="contacts-table-body">
                <!-- Data populated dynamically -->
                <tr>
                  <td colspan="5" style="text-align: center; color: var(--text-muted); padding: 2rem;">
                    <i class="fa-solid fa-spinner fa-spin" style="margin-right: 0.5rem;"></i> 讀取聯絡人清單中...
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- TAB 4: History Logs -->
      <div id="tab-history" class="tab-content">
        <div class="glass-card">
          <div class="card-header">
            <div class="card-title">
              <i class="fa-solid fa-clock-rotate-left"></i> 本月通報紀錄查詢
            </div>
            <button class="btn btn-sm" onclick="exportLogsToCSV()" title="匯出成 CSV 檔案">
              <i class="fa-solid fa-file-csv"></i> 匯出本頁 CSV
            </button>
          </div>
          
          <div class="logs-toolbar">
            <div class="search-input-group">
              <i class="fa-solid fa-magnifying-glass"></i>
              <input type="text" class="search-input" id="logs-search" placeholder="搜尋時間、警報狀態、通知管道..." oninput="handleSearch()">
            </div>
            
            <div class="pagination">
              <button class="btn btn-sm btn-icon-only" id="btn-prev-page" onclick="prevPage()"><i class="fa-solid fa-chevron-left"></i></button>
              <span class="page-info" id="page-info">第 1 / 1 頁</span>
              <button class="btn btn-sm btn-icon-only" id="btn-next-page" onclick="nextPage()"><i class="fa-solid fa-chevron-right"></i></button>
            </div>
          </div>
          
          <div class="table-container">
            <table>
              <thead>
                <tr>
                  <th>通報時間</th>
                  <th>設定閾值</th>
                  <th>觀測環境溫度</th>
                  <th>氣象觀測時間</th>
                  <th>警報狀態</th>
                  <th>通知管道與狀態</th>
                </tr>
              </thead>
              <tbody id="logs-table-body">
                <tr>
                  <td colspan="6" style="text-align: center; color: var(--text-muted); padding: 2rem;">
                    <i class="fa-solid fa-spinner fa-spin" style="margin-right: 0.5rem;"></i> 正在讀取雲端通報歷史紀錄...
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

    </main>
  </div>

  <!-- Add Contact Modal -->
  <div class="modal-overlay" id="add-contact-modal">
    <div class="modal-content">
      <div class="modal-header">
        <h3 class="modal-title">新增通報聯絡人</h3>
        <span class="modal-close" onclick="closeAddContactModal()">&times;</span>
      </div>
      
      <form id="contact-form" onsubmit="addNewContact(event)">
        <div class="form-group">
          <label class="form-label" for="contact-name">聯絡人姓名 <span style="color: var(--danger);">*</span></label>
          <div class="input-wrapper">
            <i class="fa-solid fa-user"></i>
            <input type="text" class="form-control" id="contact-name" placeholder="例如：張三" required>
          </div>
        </div>
        
        <div class="form-group">
          <label class="form-label" for="contact-email">電子信箱 (Email)</label>
          <div class="input-wrapper">
            <i class="fa-solid fa-envelope"></i>
            <input type="email" class="form-control" id="contact-email" placeholder="example@email.com">
          </div>
        </div>
        
        <div class="form-group">
          <label class="form-label" for="contact-line">LINE ID (個人 ID 或 群組 ID)</label>
          <div class="input-wrapper">
            <i class="fa-brands fa-line" style="font-weight: bold;"></i>
            <input type="text" class="form-control" id="contact-line" placeholder="U1234abcd... 或 C1234abcd...">
          </div>
          <p style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.25rem; padding-left: 0.5rem;">
            ※ LINE ID 必須以 U (個人)、C (群組) 或 R (聊天室) 開頭。
          </p>
        </div>
        
        <div class="form-group" style="display: flex; align-items: center; gap: 1rem; margin-top: 1.5rem;">
          <label class="switch">
            <input type="checkbox" id="contact-enabled" checked>
            <span class="slider"></span>
          </label>
          <span style="font-size: 0.9rem; font-weight: 500;">預設啟用此聯絡人</span>
        </div>
        
        <div class="modal-footer">
          <button type="button" class="btn" onclick="closeAddContactModal()">取消</button>
          <button type="submit" class="btn btn-primary">確認新增</button>
        </div>
      </form>
    </div>
  </div>

  <!-- Toast Notification Area -->
  <div class="toast-container" id="toast-container"></div>

  <!-- Script logic -->
  <script>
    // Tab switching controller
    const headings = {
      dashboard: { title: "狀態儀表板", sub: "即時監控 CWA 伸港觀測站環境氣溫與系統心跳" },
      settings: { title: "系統設定管理", sub: "動態調整告警閾值、監控開始與結束時段、檢查間隔" },
      contacts: { title: "聯絡人名冊管理", sub: "設定 LINE 與電子郵件通報名單，提供快速啟用開關" },
      history: { title: "歷史通報紀錄", sub: "查詢與篩選當月份環境溫度通報及心跳歷史紀錄" }
    };

    function switchTab(tabId) {
      // 1. Update navigation active state
      document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
      });
      event.currentTarget.classList.add('active');

      // 2. Switch tab view visibility
      document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
      });
      document.getElementById(`tab-${tabId}`).classList.add('active');

      // 3. Update headers
      document.getElementById('page-heading').innerText = headings[tabId].title;
      document.getElementById('page-subheading').innerText = headings[tabId].sub;

      // 4. Specific actions per tab
      if (tabId === 'dashboard') {
        refreshDashboard();
      } else if (tabId === 'settings') {
        loadSettingsToForm();
      } else if (tabId === 'contacts') {
        loadContacts();
      } else if (tabId === 'history') {
        loadLogs();
      }
    }

    // Global application state
    let appState = {
      dashboard: null,
      contacts: [],
      logs: [],
      filteredLogs: [],
      currentPage: 1,
      pageSize: 15
    };

    // Time window options builder
    function buildTimeOptions() {
      const startSelect = document.getElementById('input-start-hour');
      const endSelect = document.getElementById('input-end-hour');
      startSelect.innerHTML = '';
      endSelect.innerHTML = '';
      
      for (let i = 0; i <= 24; i++) {
        const hourLabel = i === 24 ? "24 點 (午夜)" : `${i} 點`;
        const val = i;
        
        const optStart = new Option(hourLabel, val);
        const optEnd = new Option(hourLabel, val);
        
        startSelect.add(optStart);
        endSelect.add(optEnd);
      }
    }

    // Toast notification creator
    function showToast(message, type = 'info') {
      const container = document.getElementById('toast-container');
      const toast = document.createElement('div');
      toast.className = `toast toast-${type}`;
      
      let icon = 'fa-info-circle';
      if (type === 'success') icon = 'fa-check-circle';
      else if (type === 'danger') icon = 'fa-exclamation-circle';
      else if (type === 'warning') icon = 'fa-exclamation-triangle';
      
      toast.innerHTML = `
        <i class="fa-solid ${icon}"></i>
        <div class="toast-message">${message}</div>
        <span class="toast-close" onclick="this.parentElement.remove()">&times;</span>
      `;
      
      container.appendChild(toast);
      
      // Auto dismiss after 5s
      setTimeout(() => {
        toast.style.animation = 'slideInRight 0.3s reverse forwards';
        setTimeout(() => toast.remove(), 300);
      }, 5000);
    }

    // Range slider value updater
    function updateSliderVal(val) {
      document.getElementById('input-threshold-val').innerText = parseFloat(val).toFixed(1);
    }

    // Time window validation helper
    function validateTimeWindow() {
      const start = parseInt(document.getElementById('input-start-hour').value);
      const end = parseInt(document.getElementById('input-end-hour').value);
      const tip = document.getElementById('time-window-tip');
      
      if (start === end) {
        tip.innerText = "⚠️ 警告：開始與結束時間相同，代表「整天 24 小時均不監測」，系統不會執行通報。";
        tip.style.display = 'block';
      } else if (start > end) {
        tip.innerText = `💡 提示：開始時間 (${start}點) 大於結束時間 (${end}點)，系統將採取「跨夜監測」模式 (每日 ${start}:00 至隔日 ${end}:00)。`;
        tip.style.color = '#3b82f6';
        tip.style.display = 'block';
      } else {
        tip.style.display = 'none';
      }
    }

    // SVG Circular Gauge renderer
    function updateTempGauge(temp, threshold) {
      const minTemp = 0;
      const maxTemp = 50;
      const r = 84;
      const circumference = 2 * Math.PI * r; // ~527.7
      
      let percent = (temp - minTemp) / (maxTemp - minTemp);
      if (percent < 0) percent = 0;
      if (percent > 1) percent = 1;
      
      const offset = circumference - (percent * circumference);
      const fillCircle = document.getElementById('temp-gauge-fill');
      fillCircle.style.strokeDashoffset = offset;
      
      // Color scheme selector depending on temperature & threshold
      const gaugeCard = document.getElementById('gauge-card');
      const badge = document.getElementById('alert-state-badge');
      
      if (temp === -99) {
        fillCircle.style.stroke = 'var(--text-muted)';
        badge.className = 'badge badge-secondary';
        badge.innerText = '觀測站維護中 / 斷線';
        gaugeCard.className = 'glass-card';
        return;
      }
      
      if (temp > threshold) {
        fillCircle.style.stroke = 'var(--danger)';
        badge.className = 'badge badge-danger';
        badge.innerText = `⚠️ 高溫警報中 (閾值 ${threshold}°C)`;
        gaugeCard.className = 'glass-card gauge-alert-active';
        fillCircle.style.filter = 'drop-shadow(0 0 8px rgba(239, 68, 68, 0.6))';
      } else if (temp > threshold - 2) {
        fillCircle.style.stroke = 'var(--warning)';
        badge.className = 'badge badge-warning';
        badge.innerText = `⚠️ 溫度偏高 (閾值 ${threshold}°C)`;
        gaugeCard.className = 'glass-card';
        fillCircle.style.filter = 'drop-shadow(0 0 8px rgba(245, 158, 11, 0.4))';
      } else {
        fillCircle.style.stroke = 'var(--success)';
        badge.className = 'badge badge-success';
        badge.innerText = '✅ 正常 (未超標)';
        gaugeCard.className = 'glass-card';
        fillCircle.style.filter = 'drop-shadow(0 0 8px rgba(16, 185, 129, 0.4))';
      }
    }

    // Humanize timestamp display
    function formatTimeDiff(timestamp, nowServer) {
      if (!timestamp) return "無紀錄";
      const past = parseInt(timestamp);
      const now = parseInt(nowServer);
      const diffMs = now - past;
      const diffMins = Math.floor(diffMs / (1000 * 60));
      
      if (diffMins < 0) return "剛剛";
      if (diffMins < 1) return "剛剛";
      if (diffMins < 60) return `${diffMins} 分鐘前`;
      
      const diffHours = Math.floor(diffMins / 60);
      if (diffHours < 24) return `${diffHours} 小時前`;
      
      const date = new Date(past);
      return `${date.getMonth() + 1}/${date.getDate()} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
    }

    // Backend RPC wrappers
    function runRPC(funcName, args = null, onSuccess = null, onFailure = null) {
      // Show page loader indicator
      document.getElementById('system-status-dot').className = 'status-dot online';
      document.getElementById('system-status-text').innerText = '與雲端資料庫同步中...';
      
      let runner = google.script.run;
      if (onSuccess) {
        runner = runner.withSuccessHandler((data) => {
          document.getElementById('system-status-dot').className = 'status-dot online';
          document.getElementById('system-status-text').innerText = '雲端連接正常';
          onSuccess(data);
        });
      }
      if (onFailure) {
        runner = runner.withFailureHandler((err) => {
          document.getElementById('system-status-dot').className = 'status-dot offline';
          document.getElementById('system-status-text').innerText = '雲端通訊失敗';
          showToast(`雲端作業失敗: ${err.message}`, 'danger');
          onFailure(err);
        });
      } else {
        runner = runner.withFailureHandler((err) => {
          document.getElementById('system-status-dot').className = 'status-dot offline';
          document.getElementById('system-status-text').innerText = '雲端通訊失敗';
          showToast(`雲端通訊失敗: ${err.message}`, 'danger');
        });
      }
      
      if (args !== null) {
        runner[funcName](args);
      } else {
        runner[funcName]();
      }
    }

    // Refresh dashboard values
    function refreshDashboard() {
      runRPC('getDashboardData', null, (data) => {
        appState.dashboard = data;
        
        // 1. Current Temp & Gauge
        const temp = data.currentTemp;
        document.getElementById('current-temp-val').innerText = temp === -99 ? '--.-' : temp.toFixed(1);
        document.getElementById('obs-time-text').innerText = `最新氣象觀測時間：${data.obsTime || '--'}`;
        updateTempGauge(temp, data.threshold);
        
        // 2. Settings Details Card
        document.getElementById('dash-threshold').innerText = `${data.threshold.toFixed(1)} °C`;
        document.getElementById('dash-time-window').innerText = `${data.startHour}:00 - ${data.endHour}:00`;
        document.getElementById('dash-frequency').innerText = `${data.frequency} 分鐘`;
        
        // 3. Heartbeat details
        const hbValSpan = document.getElementById('dash-last-heartbeat');
        if (data.lastLocalHeartbeat) {
          const formattedDiff = formatTimeDiff(data.lastLocalHeartbeat, data.nowTime);
          const timeDate = new Date(parseInt(data.lastLocalHeartbeat));
          const dateStr = `${timeDate.getMonth()+1}/${timeDate.getDate()} ${String(timeDate.getHours()).padStart(2,'0')}:${String(timeDate.getMinutes()).padStart(2,'0')}`;
          
          // Determine if heartbeat is timed out (offline)
          const diffMinutes = (parseInt(data.nowTime) - parseInt(data.lastLocalHeartbeat)) / (1000 * 60);
          const limit = Math.max(25, data.frequency * 2.5);
          
          if (diffMinutes < limit) {
            hbValSpan.innerHTML = `<span class="badge badge-success"><i class="fa-solid fa-circle-check"></i> 本機在線 (${formattedDiff})</span> <span style="font-size:0.8rem;color:var(--text-muted)">[${dateStr}]</span>`;
          } else {
            hbValSpan.innerHTML = `<span class="badge badge-danger"><i class="fa-solid fa-circle-exclamation"></i> 離線警報 (${formattedDiff})</span> <span style="font-size:0.8rem;color:var(--text-muted)">[${dateStr}]</span>`;
          }
        } else {
          hbValSpan.innerHTML = `<span class="badge badge-secondary">尚未發送心跳</span>`;
        }
      });
    }

    // Load configurations into settings form
    function loadSettingsToForm() {
      if (appState.dashboard) {
        const data = appState.dashboard;
        document.getElementById('input-threshold').value = data.threshold;
        document.getElementById('input-threshold-val').innerText = data.threshold.toFixed(1);
        document.getElementById('input-start-hour').value = data.startHour;
        document.getElementById('input-end-hour').value = data.endHour;
        document.getElementById('input-frequency').value = data.frequency;
        validateTimeWindow();
      } else {
        runRPC('getDashboardData', null, (data) => {
          appState.dashboard = data;
          loadSettingsToForm();
        });
      }
    }

    // Save configuration settings
    function saveSettings(e) {
      e.preventDefault();
      const btn = document.getElementById('btn-save-settings');
      const originalHtml = btn.innerHTML;
      btn.disabled = true;
      btn.innerHTML = `<i class="fa-solid fa-circle-notch fa-spin"></i> 套用設定中...`;
      
      const payload = {
        threshold: parseFloat(document.getElementById('input-threshold').value),
        startHour: parseInt(document.getElementById('input-start-hour').value),
        endHour: parseInt(document.getElementById('input-end-hour').value),
        frequency: parseInt(document.getElementById('input-frequency').value)
      };
      
      runRPC('saveSystemSettings', payload, (res) => {
        btn.disabled = false;
        btn.innerHTML = originalHtml;
        if (res.status === 'success') {
          showToast('系統設定儲存成功，定時排程已自動重建更新！', 'success');
          // Update cache
          if (appState.dashboard) {
            appState.dashboard.threshold = payload.threshold;
            appState.dashboard.startHour = payload.startHour;
            appState.dashboard.endHour = payload.endHour;
            appState.dashboard.frequency = payload.frequency;
          }
        }
      }, () => {
        btn.disabled = false;
        btn.innerHTML = originalHtml;
      });
    }

    // Load contacts management list
    function loadContacts() {
      const tbody = document.getElementById('contacts-table-body');
      tbody.innerHTML = `
        <tr>
          <td colspan="5" style="text-align: center; color: var(--text-muted); padding: 2rem;">
            <i class="fa-solid fa-spinner fa-spin" style="margin-right: 0.5rem;"></i> 讀取聯絡人清單中...
          </td>
        </tr>
      `;
      
      runRPC('getContactsData', null, (data) => {
        appState.contacts = data;
        renderContactsTable();
      });
    }

    // Render contacts to table layout
    function renderContactsTable() {
      const tbody = document.getElementById('contacts-table-body');
      tbody.innerHTML = '';
      
      if (appState.contacts.length === 0) {
        tbody.innerHTML = `
          <tr>
            <td colspan="5" style="text-align: center; color: var(--text-muted); padding: 2rem;">
              <i class="fa-solid fa-triangle-exclamation"></i> 尚未建立任何聯絡收件人
            </td>
          </tr>
        `;
        return;
      }
      
      appState.contacts.forEach((contact, idx) => {
        const tr = document.createElement('tr');
        
        tr.innerHTML = `
          <td style="font-weight: 600;">${escapeHTML(contact.name)}</td>
          <td>${contact.email ? escapeHTML(contact.email) : `<span style="color:var(--text-muted);font-style:italic;">未設定</span>`}</td>
          <td>${contact.lineId ? `<code>${escapeHTML(contact.lineId)}</code>` : `<span style="color:var(--text-muted);font-style:italic;">未設定</span>`}</td>
          <td style="text-align: center;">
            <label class="switch">
              <input type="checkbox" ${contact.enabled ? 'checked' : ''} onchange="toggleContactEnabled(${idx}, this.checked)">
              <span class="slider"></span>
            </label>
          </td>
          <td style="text-align: center;">
            <button class="btn btn-sm btn-icon-only btn-danger" onclick="deleteContact(${idx})" title="刪除聯絡人">
              <i class="fa-solid fa-trash-can"></i>
            </button>
          </td>
        `;
        
        tbody.appendChild(tr);
      });
    }

    // Toggle contact enabled/disabled on switch click
    function toggleContactEnabled(idx, checked) {
      appState.contacts[idx].enabled = checked;
      
      // Save contacts automatically
      runRPC('saveContactsData', appState.contacts, (res) => {
        if (res.status === 'success') {
          const actionText = checked ? '已啟用' : '已停用';
          showToast(`聯絡人「${appState.contacts[idx].name}」${actionText}`, 'success');
        }
      });
    }

    // Delete contact row and sync
    function deleteContact(idx) {
      const name = appState.contacts[idx].name;
      if (!confirm(`確定要將「${name}」從通報名冊中刪除嗎？`)) return;
      
      appState.contacts.splice(idx, 1);
      
      runRPC('saveContactsData', appState.contacts, (res) => {
        if (res.status === 'success') {
          showToast(`聯絡人「${name}」已成功刪除`, 'success');
          renderContactsTable();
        }
      });
    }

    // Modal controls
    function openAddContactModal() {
      document.getElementById('contact-form').reset();
      document.getElementById('add-contact-modal').classList.add('active');
    }

    function closeAddContactModal() {
      document.getElementById('add-contact-modal').classList.remove('active');
    }

    // Add new contact action
    function addNewContact(e) {
      e.preventDefault();
      
      const name = document.getElementById('contact-name').value.trim();
      const email = document.getElementById('contact-email').value.trim();
      const lineId = document.getElementById('contact-line').value.trim();
      const enabled = document.getElementById('contact-enabled').checked;
      
      if (email === "" && lineId === "") {
        showToast('電子郵件 與 LINE ID 至少必須填寫一項！', 'warning');
        return;
      }
      
      // Validation of LINE ID format
      if (lineId !== "") {
        const prefix = lineId.charAt(0).toUpperCase();
        if (prefix !== 'U' && prefix !== 'C' && prefix !== 'R') {
          showToast('LINE ID 必須以 U (個人)、C (群組) 或 R (聊天室) 開頭！', 'warning');
          return;
        }
      }
      
      const newContact = { name, email, lineId, enabled };
      appState.contacts.push(newContact);
      
      runRPC('saveContactsData', appState.contacts, (res) => {
        if (res.status === 'success') {
          showToast(`新增聯絡人「${name}」成功！`, 'success');
          closeAddContactModal();
          renderContactsTable();
        }
      });
    }

    // Load History Logs
    function loadLogs() {
      const tbody = document.getElementById('logs-table-body');
      tbody.innerHTML = `
        <tr>
          <td colspan="6" style="text-align: center; color: var(--text-muted); padding: 2rem;">
            <i class="fa-solid fa-spinner fa-spin" style="margin-right: 0.5rem;"></i> 正在讀取雲端通報歷史紀錄...
          </td>
        </tr>
      `;
      
      runRPC('getHistoryLogs', null, (data) => {
        appState.logs = data;
        appState.filteredLogs = [...data];
        appState.currentPage = 1;
        renderLogsTable();
      });
    }

    // Render logs with local filtering & pagination
    function renderLogsTable() {
      const tbody = document.getElementById('logs-table-body');
      tbody.innerHTML = '';
      
      const startIdx = (appState.currentPage - 1) * appState.pageSize;
      const endIdx = startIdx + appState.pageSize;
      const pageData = appState.filteredLogs.slice(startIdx, endIdx);
      
      if (pageData.length === 0) {
        tbody.innerHTML = `
          <tr>
            <td colspan="6" style="text-align: center; color: var(--text-muted); padding: 2rem;">
              <i class="fa-solid fa-folder-open"></i> 查無任何相符的通報紀錄
            </td>
          </tr>
        `;
        updatePaginationControls();
        return;
      }
      
      pageData.forEach(log => {
        const tr = document.createElement('tr');
        
        // Alarm badge
        let stateBadgeHtml = '';
        if (log.alertState.includes('高溫超標') || log.alertState.includes('高溫警報')) {
          stateBadgeHtml = `<span class="badge badge-danger"><i class="fa-solid fa-circle-exclamation"></i> ${log.alertState}</span>`;
        } else if (log.alertState.includes('回落') || log.alertState.includes('解除')) {
          stateBadgeHtml = `<span class="badge badge-success"><i class="fa-solid fa-circle-check"></i> ${log.alertState}</span>`;
        } else if (log.alertState.includes('高溫持續')) {
          stateBadgeHtml = `<span class="badge badge-warning"><i class="fa-solid fa-triangle-exclamation"></i> ${log.alertState}</span>`;
        } else {
          stateBadgeHtml = `<span class="badge badge-secondary">${log.alertState}</span>`;
        }
        
        // Channel badge
        let statusBadgeHtml = '';
        if (log.statusText.includes('已發送')) {
          statusBadgeHtml = `<span class="badge badge-info"><i class="fa-solid fa-paper-plane"></i> ${log.statusText}</span>`;
        } else if (log.statusText.includes('未發送')) {
          statusBadgeHtml = `<span class="badge badge-secondary"><i class="fa-solid fa-ban"></i> ${log.statusText}</span>`;
        } else {
          statusBadgeHtml = `<span class="badge badge-secondary">${log.statusText}</span>`;
        }
        
        tr.innerHTML = `
          <td style="font-family:var(--font-outfit);font-weight:500;">${escapeHTML(log.time)}</td>
          <td>${log.threshold.toFixed(1)} °C</td>
          <td style="font-weight:700;color:${log.temp > log.threshold ? 'var(--danger)' : 'var(--success)'}">${log.temp.toFixed(1)} °C</td>
          <td style="font-size:0.85rem;color:var(--text-muted);">${escapeHTML(log.obsTime)}</td>
          <td>${stateBadgeHtml}</td>
          <td>${statusBadgeHtml}</td>
        `;
        
        tbody.appendChild(tr);
      });
      
      updatePaginationControls();
    }

    // Update pagination variables & buttons state
    function updatePaginationControls() {
      const totalPages = Math.max(1, Math.ceil(appState.filteredLogs.length / appState.pageSize));
      document.getElementById('page-info').innerText = `第 ${appState.currentPage} / ${totalPages} 頁 (共 ${appState.filteredLogs.length} 筆)`;
      
      document.getElementById('btn-prev-page').disabled = (appState.currentPage === 1);
      document.getElementById('btn-next-page').disabled = (appState.currentPage === totalPages);
    }

    function prevPage() {
      if (appState.currentPage > 1) {
        appState.currentPage--;
        renderLogsTable();
      }
    }

    function nextPage() {
      const totalPages = Math.ceil(appState.filteredLogs.length / appState.pageSize);
      if (appState.currentPage < totalPages) {
        appState.currentPage++;
        renderLogsTable();
      }
    }

    // Filter logs list on input change
    function handleSearch() {
      const query = document.getElementById('logs-search').value.trim().toLowerCase();
      
      if (query === '') {
        appState.filteredLogs = [...appState.logs];
      } else {
        appState.filteredLogs = appState.logs.filter(log => {
          return log.time.toLowerCase().includes(query) ||
                 log.alertState.toLowerCase().includes(query) ||
                 log.statusText.toLowerCase().includes(query) ||
                 String(log.temp).includes(query);
        });
      }
      
      appState.currentPage = 1;
      renderLogsTable();
    }

    // CSV exporter helper
    function exportLogsToCSV() {
      if (appState.filteredLogs.length === 0) {
        showToast('目前沒有可匯出的紀錄資料！', 'warning');
        return;
      }
      
      let csvContent = '\uFEFF'; // UTF-8 BOM
      csvContent += '通報時間,溫度閾值設定(°C),通報環境溫度(°C),氣象觀測時間,警報狀態,通知狀態\n';
      
      appState.filteredLogs.forEach(log => {
        const row = [
          `"${log.time}"`,
          log.threshold,
          log.temp,
          `"${log.obsTime}"`,
          `"${log.alertState}"`,
          `"${log.statusText}"`
        ];
        csvContent += row.join(',') + '\n';
      });
      
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      
      const today = new Date();
      const monthStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}`;
      
      link.setAttribute('href', url);
      link.setAttribute('download', `溫度通報紀錄_${monthStr}.csv`);
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      showToast('通報紀錄 CSV 匯出成功！', 'success');
    }

    // Dashboard quick action buttons RPC calls
    function triggerTestNotify() {
      if (!confirm("確定要發送測試通報嗎？系統將抓取當前最新氣溫，並強制發送通知給所有已啟用的聯絡人。")) return;
      
      showToast('正在發送測試通報請求，請稍候...', 'info');
      runRPC('testNotifyForce', null, () => {
        // success alert is shown inside GAS Code.gs, but let's notify HMI
        showToast('測試通報已執行完成，請查看通報通道！', 'success');
        refreshDashboard();
      });
    }

    function triggerResetLock() {
      if (!confirm("確定要清除系統防重複通報鎖定嗎？")) return;
      
      runRPC('clearNotifiedState', null, () => {
        showToast('重複鎖定已成功清除！下一小時溫度有變動將會正常通報。', 'success');
      });
    }

    function triggerResetColumnWidths() {
      runRPC('resetColumnWidths', null, () => {
        showToast('當月通報紀錄分頁之欄寬已成功重置為預設美化設定！', 'success');
      });
    }

    // Escape HTML strings for security
    function escapeHTML(str) {
      if (!str) return '';
      return str.replace(/[&<>'"]/g, 
        tag => ({
          '&': '&amp;',
          '<': '&lt;',
          '>': '&gt;',
          "'": '&#39;',
          '"': '&quot;'
        }[tag] || tag)
      );
    }

    // Initialize application
    window.addEventListener('DOMContentLoaded', () => {
      buildTimeOptions();
      refreshDashboard();
    });
  </script>

</body>
</html>
"""

def copy_to_clipboard(text):
    try:
        # Use powershell Set-Clipboard to copy to clipboard in Windows
        ps_command = "Set-Clipboard -Value @'\n" + text + "\n'@ -AsPlainText"
        subprocess.run(["powershell", "-Command", ps_command], capture_output=True, check=True)
        return True
    except Exception as e:
        # Fallback using clip command if powershell fails
        try:
            p = subprocess.Popen(["clip"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            p.communicate(input=text)
            return True
        except:
            return False

def main():
    print("==================================================")
    print("🌡️  環境溫度監控系統 - 雲端 HMI 部署工具 (v4.0)")
    print("==================================================")
    
    # 1. Write files locally
    try:
        dir_path = os.path.dirname(os.path.abspath(__file__))
        code_gs_path = os.path.join(dir_path, "Code.gs")
        index_html_path = os.path.join(dir_path, "Index.html")
        
        with open(code_gs_path, "w", encoding="utf-8") as f:
            f.write(GAS_CODE)
            
        with open(index_html_path, "w", encoding="utf-8") as f:
            f.write(HTML_CODE)
            
        print(f"【成功】已成功在本地生成兩個雲端部署檔案：")
        print(f"  📂 Code.gs   -> {code_gs_path}")
        print(f"  📂 Index.html -> {index_html_path}")
        print("==================================================")
    except Exception as e:
        print(f"【警告】在本地寫入檔案時失敗: {e}")
        print("將繼續執行剪貼簿複製作業...")
        print("==================================================")

    # 2. Ask user which file to copy
    while True:
        print("請選擇要複製到剪貼簿的程式碼：")
        print(" [1] 複製後端 Code.gs 程式碼")
        print(" [2] 複製前端 Index.html 網頁代碼")
        print(" [3] 離開離開程式")
        try:
            choice = input("請輸入選項 (1/2/3): ").strip()
        except KeyboardInterrupt:
            print("
已退出。")
            break
            
        if choice == "1":
            if copy_to_clipboard(GAS_CODE):
                print("
【成功】後端 Code.gs 程式碼已成功複製到剪貼簿！")
                print(" -> 請到 Google Apps Script 的 Code.gs 檔案中貼上。")
            else:
                print("
【失敗】無法複製到剪貼簿。您可以在本地目錄中直接打開 Code.gs 進行複製。")
            print("--------------------------------------------------")
        elif choice == "2":
            if copy_to_clipboard(HTML_CODE):
                print("
【成功】前端 Index.html 網頁代碼已成功複製到剪貼簿！")
                print(" -> 請在 Google Apps Script 中新增一個 HTML 檔案，命名為「Index」，並貼上網頁程式碼。")
            else:
                print("
【失敗】無法複製到剪貼簿。您可以在本地目錄中直接打開 Index.html 進行複製。")
            print("--------------------------------------------------")
        elif choice == "3" or choice == "":
            print("
感謝使用，請記得在 Google Apps Script 儲存並部署為 Web App！")
            break
        else:
            print("
【錯誤】無效選項，請重新輸入。")
            print("--------------------------------------------------")

if __name__ == "__main__":
    main()
