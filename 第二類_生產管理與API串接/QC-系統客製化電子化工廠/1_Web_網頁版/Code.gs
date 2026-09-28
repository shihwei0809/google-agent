const CONFIG = {
  sheetName: 'QC_Samples',
  configSheetName: 'System_Config', // 摮撖Ⅳ??Webhook ?極雿” (QC_PIN, TEAMS_WEBHOOK)
  ordersSheetName: 'Orders',        // 摮瘥?脣鞎冽?蝔?(敺?Excel ?臬敺?甇亥甇?
  spreadsheetId: '1_4zrITMtrKCC9x_DmazqxYz63366ro-OpZOkNRTFhqo',
  
  // Teams ?駁? Webhook ?身閮剖? (鈭血??System_Config 撌乩?銵典??‵撖?
  teamsRouting: {
    MANAGER_WEBHOOK: '', // ?恣/鋆賡蜓蝞⊿??Webhook (敹??暹?霅血?炎撽???
    DEPTS: {
      '鞈?隤?: '',
      '?曉銝隤?: '',
      '?曉鈭玨': '',
      '???隤?: ''
    },
    PWA_URL: 'https://google-agent.pages.dev/qc-system'
  },

  headers: [
    'id', 'barcode', 'productName', 'tankNo', 'customer', 
    'quantity', 'flowType', 'dept', 'requester', 'grade', 
    'qcResult', 'createdAt', 'completedAt', 'status', 'qcNote', 'isAlerted',
    'parentId', 'round'
  ]
};

// ?舀蝝雯???? API ?澆
function doGet(e) {
  if (e && e.parameter && e.parameter.action) {
    return handleApiGet(e.parameter);
  }
  return HtmlService.createHtmlOutputFromFile('Index')
    .setTitle('暾餃??飛 QC 瑼ａ??單??蝟餌絞')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

// ?舀憭 POST API (Cloudflare Pages ?璈?PWA ?澆)
function doPost(e) {
  try {
    const postData = JSON.parse(e.postData.contents);
    const action = postData.action;
    let result = { success: false, error: '?芰??' };

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
    } else if (action === 'returnForResample') {
      result = returnForResample(postData.id, postData.note, postData.pin);
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

// 敺岫蝞”??霈?頂蝯梯身摰?(QC_PIN, Teams Webhooks ????銝??詨)
function getSystemConfigFromSheet_() {
  const config = {
    pin: '8888',
    managerWebhook: CONFIG.teamsRouting.MANAGER_WEBHOOK,
    deptWebhooks: Object.assign({}, CONFIG.teamsRouting.DEPTS),
    pwaUrl: CONFIG.teamsRouting.PWA_URL,
    flowTypes: ['?箄疏', '?脫?', '鋆?', '憪?'],
    grades: ['撌交平蝝?, 'UPS', 'IF'],
    depts: ['鞈?隤?, '?曉銝隤?, '?曉鈭玨', '???隤?],
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
        config.flowTypes = val.split(/[,嚗/).map(s => s.trim()).filter(Boolean);
      }
      if (key === 'OPTIONS_GRADES' && val) {
        config.grades = val.split(/[,嚗/).map(s => s.trim()).filter(Boolean);
      }
      if (key === 'OPTIONS_DEPTS' && val) {
        config.depts = val.split(/[,嚗/).map(s => s.trim()).filter(Boolean);
      }
      if (key === 'OPTIONS_PRODUCTS' && val) {
        config.products = val.split(/[,嚗/).map(s => s.trim()).filter(Boolean);
      }
    }
  } catch(e) {
    console.warn("霈??System_Config 憭望?嚗蝙?券?閮剖?, e);
  }
  return config;
}

// ???垢?澆隞亙?敺憟頂蝯梢?蝵?(?怠?蝣潦eams ????詨?)
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

// 頛撌亙嚗??萄 Google 閰衣?銵刻?朣?System_Config 撌乩?銵券?閮剖?
function initSystemConfigSheet() {
  try {
    const ss = SpreadsheetApp.openById(CONFIG.spreadsheetId);
    let sheet = ss.getSheetByName(CONFIG.configSheetName);
    if (!sheet) {
      sheet = ss.insertSheet(CONFIG.configSheetName);
      sheet.appendRow(['閮剖?? (Key)', '閮剖???(Value)', '隤芣???靘?]);
    }
    
    const existingKeys = sheet.getDataRange().getValues().slice(1).map(r => String(r[0]).trim());
    const defaults = [
      ['QC_PIN', '8888', '?恣?曇??? 4 蝣?PIN 蝣?],
      ['TEAMS_MANAGER_WEBHOOK', '', '?恣/鋆賡蜓蝞⊿??Webhook (敹?暹?霅血????'],
      ['TEAMS_WEBHOOK_鞈?隤?, '', '鞈?隤脣?撅?Webhook'],
      ['TEAMS_WEBHOOK_?曉銝隤?, '', '?曉銝隤脣?撅?Webhook'],
      ['TEAMS_WEBHOOK_?曉鈭玨', '', '?曉鈭玨撠惇 Webhook'],
      ['TEAMS_WEBHOOK_???隤?, '', '???隤脣?撅?Webhook'],
      ['PWA_URL', 'https://google-agent.pages.dev/qc-system', 'PWA 蝟餌絞蝬脣?'],
      ['OPTIONS_FLOW_TYPES', '?箄疏, ?脫?, 鋆?, 憪?', '???詨? (隞仿???)'],
      ['OPTIONS_GRADES', '撌交平蝝? UPS, IF', '蝑??詨? (隞仿???)'],
      ['OPTIONS_DEPTS', '鞈?隤? ?曉銝隤? ?曉鈭玨, ???隤?, '?見?桐??詨 (隞仿???)'],
      ['OPTIONS_PRODUCTS', 'IPA, IPAUPS, IPAHQ, CPNE3(T), CPNE4, CPN-P1R, EBR, EBR-P1R, NBAC, NBAC-P1R, CPN, EG, NMP, GAA, ACT, PM, PMA98, heavy-R, DPM, DPM-B1, SEP73, Anone, GBL, PG, EBRR', '??撱箄降?詨 (隞仿???)']
    ];
    
    defaults.forEach(item => {
      if (!existingKeys.includes(item[0])) {
        sheet.appendRow(item);
      }
    });
    return { success: true, message: "System_Config 閮剖??歇?芸?鋆?嚗? };
  } catch(err) {
    return { success: false, error: err.message };
  }
}

// =========================================================================
// ???脩垢?郊璅∠?嚗aveOrders / getOrders
// =========================================================================

const ORDERS_HEADERS = [
  'importedAt', 'doc_no', 'date', 'time', 'flowType',
  'productName', 'tankNo', 'customer', 'container', 'quantity', 'grade', 'note'
];

// ?垢?臬 Excel 敺?恬?摰閬? Orders 撌乩?銵剁?隞交??啣?亥??皞?
function saveOrders(orders) {
  try {
    if (!Array.isArray(orders) || orders.length === 0) {
      return { success: false, error: '?⊥???蝔??? };
    }
    const ss = SpreadsheetApp.openById(CONFIG.spreadsheetId);
    let sheet = ss.getSheetByName(CONFIG.ordersSheetName);
    if (!sheet) {
      sheet = ss.insertSheet(CONFIG.ordersSheetName);
    } else {
      sheet.clearContents();
    }
    // 撖怠璅???
    sheet.appendRow(ORDERS_HEADERS.map(h => {
      const labels = {
        importedAt: '?臬??', doc_no: '?株?', date: '???交?', time: '????',
        flowType: '憿?', productName: '??', tankNo: '瑽質?/瑹?', customer: '摰Ｘ/頠?',
        container: '摰孵/?', quantity: '?賊?', grade: '蝑?', note: '?酉'
      };
      return labels[h] || h;
    }));
    // ?寞活撖怠?????
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

// ?垢?頛??恬?霈??Orders 撌乩?銵剁???????
function getOrders() {
  try {
    const ss = SpreadsheetApp.openById(CONFIG.spreadsheetId);
    const sheet = ss.getSheetByName(CONFIG.ordersSheetName);
    if (!sheet) return { success: true, orders: [], count: 0 };
    const data = sheet.getDataRange().getValues();
    if (data.length <= 1) return { success: true, orders: [], count: 0 };
    const headers = data[0]; // 銝剜?璅????寧?箏? ORDERS_HEADERS 蝝Ｗ?撠?
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
  const defaultBarcode = Utilities.formatDate(new Date(), "GMT+8", "yyyyMMdd") + '-摨怠?';
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
    return { success: false, error: '????憭望?嚗?蝞∪?撅砍?蝣潮隤歹?' };
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

      // Microsoft Teams 蝎暹???? (?芷蜓蝞?+ 閰脤見隤脣恕)
      sendTeamsCompletionNotify(dept, requester, barcode, productName, tankNo, customer, result, note, sysConfig);
      
      return { success: true };
    }
  }
  return { success: false, error: '?曆??啗府蝑??? };
}

// =========================================================================
// ????圈見璅∠?嚗eturnForResample
// =========================================================================

// ?恣?文? FAIL 敺??撠?閮?璅???'failed'嚗?遣蝡?round+1 ?閮?
function returnForResample(id, note, pin) {
  const sysConfig = getSystemConfigFromSheet_();
  if (pin !== sysConfig.pin) {
    return { success: false, error: '????憭望?嚗?蝞∪?撅砍?蝣潮隤歹?' };
  }

  const ss = SpreadsheetApp.openById(CONFIG.spreadsheetId);
  const sheet = ss.getSheetByName(CONFIG.sheetName);
  const data = sheet.getDataRange().getValues();
  const h = CONFIG.headers;

  for (let i = 1; i < data.length; i++) {
    if (data[i][h.indexOf('id')] === id) {
      const row = i + 1;

      // 1. 霈??閮????雿?
      const oldBarcode   = data[i][h.indexOf('barcode')];
      const oldProduct   = data[i][h.indexOf('productName')];
      const oldTankNo    = data[i][h.indexOf('tankNo')];
      const oldCustomer  = data[i][h.indexOf('customer')];
      const oldQuantity  = data[i][h.indexOf('quantity')];
      const oldFlowType  = data[i][h.indexOf('flowType')];
      const oldDept      = data[i][h.indexOf('dept')];
      const oldRequester = data[i][h.indexOf('requester')];
      const oldGrade     = data[i][h.indexOf('grade')];
      const oldParentId  = h.indexOf('parentId') >= 0 ? data[i][h.indexOf('parentId')] : '';
      const oldRound     = h.indexOf('round') >= 0 ? (parseInt(data[i][h.indexOf('round')]) || 1) : 1;

      // 2. 閮??寡???ID嚗arentId ?亙歇?停蝜潭嚗?撌勗停?舀嚗?
      const rootId = oldParentId || id;
      const newRound = oldRound + 1;

      // 3. 璅???? 'failed'嚗????舀閰ｇ?
      sheet.getRange(row, h.indexOf('status') + 1).setValue('failed');
      sheet.getRange(row, h.indexOf('completedAt') + 1).setValue(new Date().toISOString());
      sheet.getRange(row, h.indexOf('qcResult') + 1).setValue('FAIL');
      sheet.getRange(row, h.indexOf('qcNote') + 1).setValue(note || '?文?銝??潘?????圈見');

      // 4. 撱箇??啁? pending 閮?嚗????瑽質?嚗ound+1嚗?
      const newId = Utilities.getUuid();
      const newRowData = CONFIG.headers.map(field => {
        if (field === 'id')          return newId;
        if (field === 'status')      return 'pending';
        if (field === 'createdAt')   return new Date().toISOString();
        if (field === 'barcode')     return oldBarcode;
        if (field === 'productName') return oldProduct;
        if (field === 'tankNo')      return oldTankNo;
        if (field === 'customer')    return oldCustomer;
        if (field === 'quantity')    return oldQuantity;
        if (field === 'flowType')    return oldFlowType;
        if (field === 'dept')        return oldDept;
        if (field === 'requester')   return oldRequester;
        if (field === 'grade')       return oldGrade;
        if (field === 'parentId')    return rootId;
        if (field === 'round')       return newRound;
        return '';  // qcResult, completedAt, qcNote, isAlerted 蝑?蝛?
      });
      sheet.appendRow(newRowData);

      // 5. Teams ?嚗???圈見
      sendTeamsReturnNotify(oldDept, oldRequester, oldBarcode, oldProduct, oldTankNo, oldCustomer, newRound, note, sysConfig);

      return { success: true, newId: newId, round: newRound };
    }
  }
  return { success: false, error: '?曆??啗府蝑??? };
}

// =========================================================================
// Microsoft Teams ?詨?璅∠?嚗移皞?瘚? 2 撠?頞??郎
// =========================================================================

// Teams MessageCard ?潮敹?(?舀??隤脣恕 + 銝餌恣???
function sendTeamsCard(targetDept, cardPayload, sysConfig) {
  const cfg = sysConfig || getSystemConfigFromSheet_();
  const targetWebhooks = [];

  // 1. ?銝餌恣?駁? Webhook
  if (cfg.managerWebhook && cfg.managerWebhook.startsWith('http')) {
    targetWebhooks.push(cfg.managerWebhook);
  }

  // 2. ??見隤脣恕撠惇 Webhook
  if (targetDept && cfg.deptWebhooks && cfg.deptWebhooks[targetDept] && cfg.deptWebhooks[targetDept].startsWith('http')) {
    targetWebhooks.push(cfg.deptWebhooks[targetDept]);
  }

  if (targetWebhooks.length === 0) {
    console.log("?芷?蝵格???Teams Webhook嚗歲???);
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
      console.error("Teams ?潮 " + url + " 憭望?", err);
    }
  });
}

// 瑼ａ?摰?嚗??Teams ?曇?/銝??澆??
function sendTeamsCompletionNotify(dept, requester, barcode, productName, tankNo, truck, result, note, sysConfig) {
  const cfg = sysConfig || getSystemConfigFromSheet_();
  const isPass = (result === 'PASS');
  const themeColor = isPass ? "107C41" : "D9381E"; // 蝬? / 蝝銝???
  const statusTitle = isPass ? "?C 瑼ａ?摰? - ?文???曇??? : "?C 瑼ａ?摰? - ?文?銝??潦?;

  const completionCard = {
    "@type": "MessageCard",
    "@context": "http://schema.org/extensions",
    "themeColor": themeColor,
    "summary": statusTitle,
    "sections": [{
      "activityTitle": statusTitle,
      "activitySubtitle": `瑼ａ?蝯?撌脣摰?隢?${dept} ?脰?敺?雿平`,
      "facts": [
        { "name": "? ?見?桐?", "value": `${dept}嚗見鈭綽?${requester || '??}嚗 },
        { "name": "?妒 瑼ａ???", "value": productName },
        { "name": "?儭?瑽質? / 頠?", "value": `${tankNo || '-'} / ${truck || '-'}` },
        { "name": "?? 瑼ａ??株?", "value": barcode },
        { "name": "? ?文?蝯?", "value": `**${result}**` },
        { "name": "?? ?文??酉", "value": note || "?? },
        { "name": "?梧? 摰???", "value": Utilities.formatDate(new Date(), "GMT+8", "yyyy-MM-dd HH:mm") }
      ],
      "markdown": true
    }],
    "potentialAction": [{
      "@type": "OpenUri",
      "name": "? ?? PWA ??亦?",
      "targets": [{ "os": "default", "uri": cfg.pwaUrl }]
    }]
  };

  sendTeamsCard(dept, completionCard, cfg);
}

// ????圈見嚗??Teams ?蝯阡見隤脣恕
function sendTeamsReturnNotify(dept, requester, barcode, productName, tankNo, truck, newRound, note, sysConfig) {
  const cfg = sysConfig || getSystemConfigFromSheet_();
  const returnCard = {
    "@type": "MessageCard",
    "@context": "http://schema.org/extensions",
    "themeColor": "F97316", // 璈霅衣內
    "summary": `?抬??C ????圈見??{productName} ??脰?蝚?${newRound} 甈⊿見`,
    "sections": [{
      "activityTitle": `?抬??C ????圈見 - 蝚?${newRound} 甈～,
      "activitySubtitle": `?恣撌脣摰??嚗? ${dept} ??見`,
      "facts": [
        { "name": "? ?見?桐?", "value": `${dept}嚗見鈭綽?${requester || '??}嚗 },
        { "name": "?妒 瑼ａ???", "value": productName },
        { "name": "?儭?瑽質? / 頠?", "value": `${tankNo || '-'} / ${truck || '-'}` },
        { "name": "?? 瑼ａ??株?", "value": barcode },
        { "name": "?? ?見頛芣活", "value": `**蝚?${newRound} 甈⊿見**` },
        { "name": "?? ?????, "value": note || "?文?銝??潘?隢??圈見" },
        { "name": "?梧? ?????, "value": Utilities.formatDate(new Date(), "GMT+8", "yyyy-MM-dd HH:mm") }
      ],
      "markdown": true
    }],
    "potentialAction": [{
      "@type": "OpenUri",
      "name": "? ?? PWA ?蝣箄?",
      "targets": [{ "os": "default", "uri": cfg.pwaUrl }]
    }]
  };
  sendTeamsCard(dept, returnCard, cfg);
}

// ?暹? 2 撠?撌⊥炎 (GAS ??撽?閫貊?剁?撱箄降閮剖?瘥?10 ???瑁?銝甈?
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

      // ?文?頞? 2 撠? (2 * 60 * 60 * 1000 ms)
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
          "themeColor": "D9381E", // 擙桃?霅衣內??
          "summary": `??C 瑼ａ?頞?霅血??{prod} 蝑歇??${diffHours} 撠?`,
          "sections": [{
            "activityTitle": `??C 瑼ａ?頞?霅血???歇??${diffHours} 撠?`,
            "activitySubtitle": `璅??瑼ａ?撌脤?2 撠??芸摰?隢?蝞∟? ${dept} ???,
            "facts": [
              { "name": "? ?見?桐?", "value": `${dept}嚗見鈭綽?${requester || '??}嚗 },
              { "name": "?妒 瑼ａ???", "value": prod },
              { "name": "?儭?瑽質? / 頠?", "value": `${tank || '-'} / ${truck || '-'}` },
              { "name": "?? ?株?蝺刻?", "value": barcode },
              { "name": "???見??", "value": Utilities.formatDate(new Date(createdTime), "GMT+8", "yyyy-MM-dd HH:mm") }
            ],
            "markdown": true
          }],
          "potentialAction": [{
            "@type": "OpenUri",
            "name": "? ?? PWA ?蝡?文?",
            "targets": [{ "os": "default", "uri": sysConfig.pwaUrl }]
          }]
        };

        // 蝎暹??券策銝餌恣 + 閰脤見隤脣恕?駁?
        sendTeamsCard(dept, overdueCard, sysConfig);

        // 璅? YES嚗??甈∟孛?潭????潮???
        sheet.getRange(i + 1, h.indexOf('isAlerted') + 1).setValue('YES');
        alertedCount++;
      }
    }
  }
  return { success: true, checked: data.length - 1, alerted: alertedCount };
}

// 皜祈岫 Teams Webhook ?
function testTeamsNotification(dept) {
  const targetDept = dept || '?曉銝隤?;
  const sysConfig = getSystemConfigFromSheet_();
  const testCard = {
    "@type": "MessageCard",
    "@context": "http://schema.org/extensions",
    "themeColor": "0078D4",
    "summary": "?妒 Teams Webhook ???皜祈岫??",
    "sections": [{
      "activityTitle": "?妒?C 蝟餌絞 - Teams Webhook 皜祈岫?????,
      "activitySubtitle": `甇方??舐 Google Apps Script 皜祈岫?潮 ${targetDept} ?蜓蝞⊿?,
      "facts": [
        { "name": "皜祈岫?桐?", "value": targetDept },
        { "name": "?潮???, "value": Utilities.formatDate(new Date(), "GMT+8", "yyyy-MM-dd HH:mm:ss") },
        { "name": "??????, "value": "? 甇?虜??" }
      ],
      "markdown": true
    }]
  };
  sendTeamsCard(targetDept, testCard, sysConfig);
  return { success: true, dept: targetDept };
}

