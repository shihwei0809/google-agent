const CONFIG = {
  sheetName: 'QC_Samples',
  configSheetName: 'System_Config', // 存放密碼與 Webhook 的工作表 (QC_PIN, TEAMS_WEBHOOK)
  ordersSheetName: 'Orders',        // 存放每日進出貨排程 (從 Excel 匯入後同步至此)
  spreadsheetId: '1_4zrITMtrKCC9x_DmazqxYz63366ro-OpZOkNRTFhqo',
  
  // Teams 頻道 Webhook 預設設定 (亦可於 System_Config 工作表動態填寫)
  teamsRouting: {
    MANAGER_WEBHOOK: '', // 品管/製造主管頻道 Webhook (必收所有逾時警報與檢驗完成)
    DEPTS: {
      '資材課': '',
      '現場一課': '',
      '現場二課': '',
      '回收處理課': ''
    },
    PWA_URL: 'https://google-agent.pages.dev/qc-system'
  },

  headers: [
    'id', 'barcode', 'productName', 'tankNo', 'customer', 
    'quantity', 'flowType', 'dept', 'requester', 'grade', 
    'qcResult', 'createdAt', 'completedAt', 'status', 'qcNote', 'isAlerted'
  ]
};

// 支援純網頁開啟或 API 呼叫
function doGet(e) {
  if (e && e.parameter && e.parameter.action) {
    return handleApiGet(e.parameter);
  }
  return HtmlService.createHtmlOutputFromFile('Index')
    .setTitle('鴻勝化學 QC 檢驗即時看板系統')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

// 支援外部 POST API (Cloudflare Pages 或本機 PWA 呼叫)
function doPost(e) {
  try {
    const postData = JSON.parse(e.postData.contents);
    const action = postData.action;
    let result = { success: false, error: '未知操作' };

    if (action === 'createSample') {
      result = createSample(postData.payload);
    } else if (action === 'completeSample') {
      result = completeSample(postData.id, postData.result, postData.note, postData.pin);
    } else if (action === 'checkOverdue') {
      result = checkOverdueSamples();
    } else if (action === 'testTeams') {
      result = testTeamsNotification(postData.dept);
    } else if (action === 'saveOrders') {
      result = saveOrders(postData.orders);
    }

    return ContentService.createTextOutput(JSON.stringify(result))
      .setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({ success: false, error: err.message }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

function handleApiGet(params) {
  let result = [];
  if (params.action === 'getSamples') {
    result = getSamples();
  } else if (params.action === 'checkOverdue') {
    result = checkOverdueSamples();
  } else if (params.action === 'getConfig') {
    result = getSystemConfig();
  } else if (params.action === 'getOrders') {
    result = getOrders();
  }
  return ContentService.createTextOutput(JSON.stringify(result))
    .setMimeType(ContentService.MimeType.JSON);
}

// 從試算表動態讀取系統設定 (QC_PIN, Teams Webhooks 與 動態下拉選單)
function getSystemConfigFromSheet_() {
  const config = {
    pin: '8888',
    managerWebhook: CONFIG.teamsRouting.MANAGER_WEBHOOK,
    deptWebhooks: Object.assign({}, CONFIG.teamsRouting.DEPTS),
    pwaUrl: CONFIG.teamsRouting.PWA_URL,
    flowTypes: ['出貨', '進料', '補料', '委託'],
    grades: ['工業級', 'UPS', 'IF'],
    depts: ['資材課', '現場一課', '現場二課', '回收處理課'],
    products: [
      'IPA', 'IPAUPS', 'IPAHQ', 'CPNE3(T)', 'CPNE4', 'CPN-P1R',
      'EBR', 'EBR-P1R', 'NBAC', 'NBAC-P1R', 'CPN', 'EG',
      'NMP', 'GAA', 'ACT', 'PM', 'PMA98', 'heavy-R',
      'DPM', 'DPM-B1', 'SEP73', 'Anone', 'GBL', 'PG', 'EBRR'
    ]
  };

  try {
    const ss = SpreadsheetApp.openById(CONFIG.spreadsheetId);
    let sheet = ss.getSheetByName(CONFIG.configSheetName);
    if (!sheet) {
      initSystemConfigSheet();
      return config;
    }
    
    const data = sheet.getDataRange().getValues();
    for (let i = 1; i < data.length; i++) {
      const key = String(data[i][0] || '').trim();
      const val = String(data[i][1] || '').trim();
      if (key === 'QC_PIN' && val) config.pin = val;
      if (key === 'TEAMS_MANAGER_WEBHOOK' && val) config.managerWebhook = val;
      if (key.startsWith('TEAMS_WEBHOOK_') && val) {
        const deptName = key.replace('TEAMS_WEBHOOK_', '').trim();
        config.deptWebhooks[deptName] = val;
      }
      if (key === 'PWA_URL' && val) config.pwaUrl = val;
      if (key === 'OPTIONS_FLOW_TYPES' && val) {
        config.flowTypes = val.split(/[,，]/).map(s => s.trim()).filter(Boolean);
      }
      if (key === 'OPTIONS_GRADES' && val) {
        config.grades = val.split(/[,，]/).map(s => s.trim()).filter(Boolean);
      }
      if (key === 'OPTIONS_DEPTS' && val) {
        config.depts = val.split(/[,，]/).map(s => s.trim()).filter(Boolean);
      }
      if (key === 'OPTIONS_PRODUCTS' && val) {
        config.products = val.split(/[,，]/).map(s => s.trim()).filter(Boolean);
      }
    }
  } catch(e) {
    console.warn("讀取 System_Config 失敗，使用預設值", e);
  }
  return config;
}

// 提供前端呼叫以取得全套系統配置 (含密碼、Teams 狀態與選單項目)
function getSystemConfig() {
  const cfg = getSystemConfigFromSheet_();
  return {
    success: true,
    pin: cfg.pin,
    flowTypes: cfg.flowTypes,
    grades: cfg.grades,
    depts: cfg.depts,
    products: cfg.products,
    pwaUrl: cfg.pwaUrl,
    hasManagerWebhook: !!(cfg.managerWebhook && cfg.managerWebhook.startsWith('http'))
  };
}

// 輔助工具：一鍵在 Google 試算表補齊 System_Config 工作表預設列
function initSystemConfigSheet() {
  try {
    const ss = SpreadsheetApp.openById(CONFIG.spreadsheetId);
    let sheet = ss.getSheetByName(CONFIG.configSheetName);
    if (!sheet) {
      sheet = ss.insertSheet(CONFIG.configSheetName);
      sheet.appendRow(['設定項目 (Key)', '設定值 (Value)', '說明與範例']);
    }
    
    const existingKeys = sheet.getDataRange().getValues().slice(1).map(r => String(r[0]).trim());
    const defaults = [
      ['QC_PIN', '8888', '品管放行授權 4 碼 PIN 碼'],
      ['TEAMS_MANAGER_WEBHOOK', '', '品管/製造主管頻道 Webhook (必收逾時警報與完成)'],
      ['TEAMS_WEBHOOK_資材課', '', '資材課專屬 Webhook'],
      ['TEAMS_WEBHOOK_現場一課', '', '現場一課專屬 Webhook'],
      ['TEAMS_WEBHOOK_現場二課', '', '現場二課專屬 Webhook'],
      ['TEAMS_WEBHOOK_回收處理課', '', '回收處理課專屬 Webhook'],
      ['PWA_URL', 'https://google-agent.pages.dev/qc-system', 'PWA 系統網址'],
      ['OPTIONS_FLOW_TYPES', '出貨, 進料, 補料, 委託', '動向選單項目 (以逗號隔開)'],
      ['OPTIONS_GRADES', '工業級, UPS, IF', '等級選單項目 (以逗號隔開)'],
      ['OPTIONS_DEPTS', '資材課, 現場一課, 現場二課, 回收處理課', '送樣單位選單 (以逗號隔開)'],
      ['OPTIONS_PRODUCTS', 'IPA, IPAUPS, IPAHQ, CPNE3(T), CPNE4, CPN-P1R, EBR, EBR-P1R, NBAC, NBAC-P1R, CPN, EG, NMP, GAA, ACT, PM, PMA98, heavy-R, DPM, DPM-B1, SEP73, Anone, GBL, PG, EBRR', '品名建議選單 (以逗號隔開)']
    ];
    
    defaults.forEach(item => {
      if (!existingKeys.includes(item[0])) {
        sheet.appendRow(item);
      }
    });
    return { success: true, message: "System_Config 設定項已自動補齊！" };
  } catch(err) {
    return { success: false, error: err.message };
  }
}

// =========================================================================
// 排程雲端同步模組：saveOrders / getOrders
// =========================================================================

const ORDERS_HEADERS = [
  'importedAt', 'doc_no', 'date', 'time', 'flowType',
  'productName', 'tankNo', 'customer', 'container', 'quantity', 'grade', 'note'
];

// 前端匯入 Excel 後呼叫：完全覆蓋 Orders 工作表（以最新匯入資料為準）
function saveOrders(orders) {
  try {
    if (!Array.isArray(orders) || orders.length === 0) {
      return { success: false, error: '無有效排程資料' };
    }
    const ss = SpreadsheetApp.openById(CONFIG.spreadsheetId);
    let sheet = ss.getSheetByName(CONFIG.ordersSheetName);
    if (!sheet) {
      sheet = ss.insertSheet(CONFIG.ordersSheetName);
    } else {
      sheet.clearContents();
    }
    // 寫入標題列
    sheet.appendRow(ORDERS_HEADERS.map(h => {
      const labels = {
        importedAt: '匯入時間', doc_no: '單號', date: '排程日期', time: '排程時間',
        flowType: '類型', productName: '品名', tankNo: '槽號/櫃號', customer: '客戶/車號',
        container: '容器/艙別', quantity: '數量', grade: '等級', note: '備註'
      };
      return labels[h] || h;
    }));
    // 批次寫入所有訂單
    const nowStr = Utilities.formatDate(new Date(), 'GMT+8', 'yyyy-MM-dd HH:mm:ss');
    const rows = orders.map(o => ORDERS_HEADERS.map(h => {
      if (h === 'importedAt') return nowStr;
      return o[h] !== undefined ? String(o[h]) : '';
    }));
    if (rows.length > 0) {
      sheet.getRange(2, 1, rows.length, ORDERS_HEADERS.length).setValues(rows);
    }
    return { success: true, count: orders.length, importedAt: nowStr };
  } catch (err) {
    return { success: false, error: err.message };
  }
}

// 前端頁面載入時呼叫：讀取 Orders 工作表，回傳排程陣列
function getOrders() {
  try {
    const ss = SpreadsheetApp.openById(CONFIG.spreadsheetId);
    const sheet = ss.getSheetByName(CONFIG.ordersSheetName);
    if (!sheet) return { success: true, orders: [], count: 0 };
    const data = sheet.getDataRange().getValues();
    if (data.length <= 1) return { success: true, orders: [], count: 0 };
    const headers = data[0]; // 中文標題列，改用固定 ORDERS_HEADERS 索引對應
    const orders = data.slice(1).filter(row => row[1]).map(row => {
      const obj = {};
      ORDERS_HEADERS.forEach((h, i) => { obj[h] = String(row[i] || ''); });
      return obj;
    });
    return { success: true, orders: orders, count: orders.length };
  } catch (err) {
    return { success: false, error: err.message, orders: [] };
  }
}

function getSamples() {
  try {
    const ss = SpreadsheetApp.openById(CONFIG.spreadsheetId);
    const sheet = ss.getSheetByName(CONFIG.sheetName);
    const data = sheet.getDataRange().getValues();
    if (data.length <= 1) return [];
    return data.slice(1).filter(row => row[0]).map(row => {
      let obj = {};
      CONFIG.headers.forEach((h, i) => {
        let val = row[i];
        if (val instanceof Date) { val = val.toISOString(); }
        obj[h] = val;
      });
      return obj;
    }).sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
  } catch(e) { return []; }
}

function createSample(payload) {
  const ss = SpreadsheetApp.openById(CONFIG.spreadsheetId);
  const sheet = ss.getSheetByName(CONFIG.sheetName);
  const defaultBarcode = Utilities.formatDate(new Date(), "GMT+8", "yyyyMMdd") + '-庫存';
  const rowData = CONFIG.headers.map(h => {
    if (h === 'id') return payload.id || Utilities.getUuid();
    if (h === 'status') return 'pending';
    if (h === 'createdAt') return payload.createdAt || new Date().toISOString();
    if (h === 'barcode') return payload.barcode || defaultBarcode;
    if (h === 'isAlerted') return '';
    return payload[h] || '';
  });
  sheet.appendRow(rowData);
  return { success: true };
}

function completeSample(id, result, note, pin) {
  const sysConfig = getSystemConfigFromSheet_();
  if (pin !== sysConfig.pin) {
    return { success: false, error: '⛔ 授權失敗：品管專屬密碼錯誤！' };
  }

  const ss = SpreadsheetApp.openById(CONFIG.spreadsheetId);
  const sheet = ss.getSheetByName(CONFIG.sheetName);
  const data = sheet.getDataRange().getValues();
  const h = CONFIG.headers;
  
  for (let i = 1; i < data.length; i++) {
    if (data[i][h.indexOf('id')] === id) {
      const row = i + 1;
      const completedTime = new Date().toISOString();
      sheet.getRange(row, h.indexOf('status') + 1).setValue('completed');
      sheet.getRange(row, h.indexOf('completedAt') + 1).setValue(completedTime);
      sheet.getRange(row, h.indexOf('qcResult') + 1).setValue(result);
      sheet.getRange(row, h.indexOf('qcNote') + 1).setValue(note);
      
      const barcode = data[i][h.indexOf('barcode')];
      const productName = data[i][h.indexOf('productName')];
      const tankNo = data[i][h.indexOf('tankNo')];
      const customer = data[i][h.indexOf('customer')];
      const dept = data[i][h.indexOf('dept')];
      const requester = data[i][h.indexOf('requester')];

      // Microsoft Teams 精準分流通知 (只送主管 + 該送樣課室)
      sendTeamsCompletionNotify(dept, requester, barcode, productName, tankNo, customer, result, note, sysConfig);
      
      return { success: true };
    }
  }
  return { success: false, error: '找不到該筆資料' };
}

// =========================================================================
// Microsoft Teams 核心模組：精準分流與 2 小時超時預警
// =========================================================================

// Teams MessageCard 發送核心 (支援指定課室 + 主管雙發送)
function sendTeamsCard(targetDept, cardPayload, sysConfig) {
  const cfg = sysConfig || getSystemConfigFromSheet_();
  const targetWebhooks = [];

  // 1. 加入主管頻道 Webhook
  if (cfg.managerWebhook && cfg.managerWebhook.startsWith('http')) {
    targetWebhooks.push(cfg.managerWebhook);
  }

  // 2. 加入送樣課室專屬 Webhook
  if (targetDept && cfg.deptWebhooks && cfg.deptWebhooks[targetDept] && cfg.deptWebhooks[targetDept].startsWith('http')) {
    targetWebhooks.push(cfg.deptWebhooks[targetDept]);
  }

  if (targetWebhooks.length === 0) {
    console.log("未配置有效 Teams Webhook，跳過發送。");
    return;
  }

  const options = {
    method: "post",
    contentType: "application/json",
    payload: JSON.stringify(cardPayload),
    muteHttpExceptions: true
  };

  targetWebhooks.forEach(url => {
    try {
      UrlFetchApp.fetch(url, options);
    } catch(err) {
      console.error("Teams 發送至 " + url + " 失敗", err);
    }
  });
}

// 檢驗完成：發送 Teams 放行/不合格卡片
function sendTeamsCompletionNotify(dept, requester, barcode, productName, tankNo, truck, result, note, sysConfig) {
  const cfg = sysConfig || getSystemConfigFromSheet_();
  const isPass = (result === 'PASS');
  const themeColor = isPass ? "107C41" : "D9381E"; // 綠色合格 / 紅色不合格
  const statusTitle = isPass ? "✅【QC 檢驗完成 - 判定合格放行】" : "❌【QC 檢驗完成 - 判定不合格】";

  const completionCard = {
    "@type": "MessageCard",
    "@context": "http://schema.org/extensions",
    "themeColor": themeColor,
    "summary": statusTitle,
    "sections": [{
      "activityTitle": statusTitle,
      "activitySubtitle": `檢驗結果已判定，請 ${dept} 進行後續作業`,
      "facts": [
        { "name": "🏢 送樣單位", "value": `${dept}（送樣人：${requester || '無'}）` },
        { "name": "🧪 檢驗品名", "value": productName },
        { "name": "🛢️ 槽號 / 車牌", "value": `${tankNo || '-'} / ${truck || '-'}` },
        { "name": "📋 檢驗單號", "value": barcode },
        { "name": "🎯 判定結果", "value": `**${result}**` },
        { "name": "📝 判定備註", "value": note || "無" },
        { "name": "⏱️ 完成時間", "value": Utilities.formatDate(new Date(), "GMT+8", "yyyy-MM-dd HH:mm") }
      ],
      "markdown": true
    }],
    "potentialAction": [{
      "@type": "OpenUri",
      "name": "📱 開啟 PWA 看板查看",
      "targets": [{ "os": "default", "uri": cfg.pwaUrl }]
    }]
  };

  sendTeamsCard(dept, completionCard, cfg);
}

// 逾時 2 小時巡檢 (GAS 時間驅動觸發器：建議設定每 10 分鐘執行一次)
function checkOverdueSamples() {
  const sysConfig = getSystemConfigFromSheet_();
  const ss = SpreadsheetApp.openById(CONFIG.spreadsheetId);
  const sheet = ss.getSheetByName(CONFIG.sheetName);
  const data = sheet.getDataRange().getValues();
  if (data.length <= 1) return { checked: 0, alerted: 0 };

  const h = CONFIG.headers;
  const now = Date.now();
  const TWO_HOURS_MS = 2 * 60 * 60 * 1000;
  let alertedCount = 0;

  for (let i = 1; i < data.length; i++) {
    const row = data[i];
    const status = row[h.indexOf('status')];
    const createdAtStr = row[h.indexOf('createdAt')];
    const isAlerted = row[h.indexOf('isAlerted')];

    if (status === 'pending' && createdAtStr && !isAlerted) {
      const createdTime = new Date(createdAtStr).getTime();
      const diffMs = now - createdTime;

      // 判定超過 2 小時 (2 * 60 * 60 * 1000 ms)
      if (diffMs >= TWO_HOURS_MS) {
        const diffHours = (diffMs / (1000 * 60 * 60)).toFixed(1);
        const barcode = row[h.indexOf('barcode')];
        const prod = row[h.indexOf('productName')];
        const tank = row[h.indexOf('tankNo')];
        const truck = row[h.indexOf('customer')];
        const dept = row[h.indexOf('dept')];
        const requester = row[h.indexOf('requester')];

        const overdueCard = {
          "@type": "MessageCard",
          "@context": "http://schema.org/extensions",
          "themeColor": "D9381E", // 鮮紅警示色
          "summary": `🚨【QC 檢驗超時警報】${prod} 等候已達 ${diffHours} 小時`,
          "sections": [{
            "activityTitle": `🚨【QC 檢驗超時警報】等候已達 ${diffHours} 小時`,
            "activitySubtitle": `樣品檢驗已逾 2 小時未判定，請品管與 ${dept} 儘速處理`,
            "facts": [
              { "name": "🏢 送樣單位", "value": `${dept}（送樣人：${requester || '無'}）` },
              { "name": "🧪 檢驗品名", "value": prod },
              { "name": "🛢️ 槽號 / 車牌", "value": `${tank || '-'} / ${truck || '-'}` },
              { "name": "📋 單號編號", "value": barcode },
              { "name": "⏰ 送樣時間", "value": Utilities.formatDate(new Date(createdTime), "GMT+8", "yyyy-MM-dd HH:mm") }
            ],
            "markdown": true
          }],
          "potentialAction": [{
            "@type": "OpenUri",
            "name": "📱 開啟 PWA 看板立即判定",
            "targets": [{ "os": "default", "uri": sysConfig.pwaUrl }]
          }]
        };

        // 精準推送給主管 + 該送樣課室頻道
        sendTeamsCard(dept, overdueCard, sysConfig);

        // 標記 YES，避免下次觸發時重複發送洗版
        sheet.getRange(i + 1, h.indexOf('isAlerted') + 1).setValue('YES');
        alertedCount++;
      }
    }
  }
  return { success: true, checked: data.length - 1, alerted: alertedCount };
}

// 測試 Teams Webhook 功能
function testTeamsNotification(dept) {
  const targetDept = dept || '現場一課';
  const sysConfig = getSystemConfigFromSheet_();
  const testCard = {
    "@type": "MessageCard",
    "@context": "http://schema.org/extensions",
    "themeColor": "0078D4",
    "summary": "🧪 Teams Webhook 連線測試成功",
    "sections": [{
      "activityTitle": "🧪【QC 系統 - Teams Webhook 測試連線】",
      "activitySubtitle": `此訊息由 Google Apps Script 測試發送至 ${targetDept} 與主管頻道`,
      "facts": [
        { "name": "測試單位", "value": targetDept },
        { "name": "發送時間", "value": Utilities.formatDate(new Date(), "GMT+8", "yyyy-MM-dd HH:mm:ss") },
        { "name": "連線狀態", "value": "🟢 正常運作" }
      ],
      "markdown": true
    }]
  };
  sendTeamsCard(targetDept, testCard, sysConfig);
  return { success: true, dept: targetDept };
}
