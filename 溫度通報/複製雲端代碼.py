#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自動複製 Google Apps Script 程式碼至剪貼簿 (一日一次版)
"""

import os
import sys
import subprocess

# Google Apps Script 程式碼
GAS_CODE = r"""/**
 * 當試算表開啟時，自動建立頂端自訂選單，方便人員點選測試與重置
 */
function onOpen() {
  var ui = SpreadsheetApp.getUi();
  ui.createMenu('🌡️ 溫度通報系統')
      .addItem('🧪 測試即時通報 (強制發送)', 'testNotifyForce')
      .addItem('🔄 重置防重複鎖定', 'clearNotifiedState')
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
"""
 
def copy_to_clipboard(text):
    ps_command = f"Set-Clipboard -Value @'\n{text}\n'@ -AsPlainText"
    subprocess.run(["powershell", "-Command", ps_command], capture_output=True)
 
if __name__ == "__main__":
    try:
        copy_to_clipboard(GAS_CODE)
        print("【成功】Google Apps Script 雲端版 (每小時狀態機版) 程式碼已成功複製到您的剪貼簿！")
        print("您現在可以直接到 Google 試算表的 Apps Script 頁面，按下 Ctrl + V 貼上程式碼。")
    except Exception as e:
        print(f"【錯誤】複製程式碼失敗: {e}", file=sys.stderr)
