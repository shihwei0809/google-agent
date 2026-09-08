const express = require('express');
const multer = require('multer');
const xlsx = require('xlsx');
const fs = require('fs');
const path = require('path');
const os = require('os');
const webpush = require('web-push');

const app = express();
let PORT = parseInt(process.env.PORT, 10) || 3000;

app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true, limit: '50mb' }));
app.use((req, res, next) => {
  res.setHeader('Cache-Control', 'no-cache, no-store, must-revalidate');
  res.setHeader('Pragma', 'no-cache');
  res.setHeader('Expires', '0');
  next();
});
app.use(express.static(path.join(__dirname, 'public'), { etag: false, maxAge: 0 }));

// Web Push VAPID 配置
const VAPID_FILE = path.join(__dirname, 'vapid.json');
let vapidKeys = null;
if (fs.existsSync(VAPID_FILE)) {
  try {
    vapidKeys = JSON.parse(fs.readFileSync(VAPID_FILE, 'utf-8'));
  } catch (e) {
    console.error('Error reading vapid.json:', e);
  }
}
if (!vapidKeys || !vapidKeys.publicKey || !vapidKeys.privateKey) {
  vapidKeys = webpush.generateVAPIDKeys();
  fs.writeFileSync(VAPID_FILE, JSON.stringify(vapidKeys, null, 2), 'utf-8');
  console.log('[WebPush] 已自動生成 VAPID 金鑰並儲存至 vapid.json');
}

webpush.setVapidDetails(
  'mailto:tech_support@shinychem.com.tw',
  vapidKeys.publicKey,
  vapidKeys.privateKey
);

const DB_FILE = path.join(__dirname, 'database.json');
const upload = multer({ storage: multer.memoryStorage() });

const DEFAULT_USERS = [
  { username: 'admin', password: '123', role: 'admin', displayName: '系統管理員', status: 'active' },
  { username: 'shihwei', password: '123', role: 'admin', displayName: '鴻勝世偉', status: 'active' },
  { username: 'eshinemmd', password: '123', role: 'admin', displayName: '鴻勝資材課', status: 'active' },
  { username: 'sales', password: '123', role: 'sales', displayName: '業務人員', status: 'active' },
  { username: 'production', password: '123', role: 'production', displayName: '生產人員', status: 'active' },
  { username: 'tech_mgr', password: '123', role: 'tech_manager', displayName: '技服主管', status: 'active' },
  { username: 'transporter', password: '123', role: 'transporter', displayName: '運輸公司', status: 'active' },
  { username: '林聖龍', password: '123', role: 'tech_staff', displayName: '林聖龍', status: 'active' },
  { username: '楊立凱', password: '123', role: 'tech_staff', displayName: '楊立凱', status: 'active' },
  { username: '胡富閔', password: '123', role: 'tech_staff', displayName: '胡富閔', status: 'active' },
  { username: '陳國安', password: '123', role: 'tech_staff', displayName: '陳國安', status: 'active' },
  { username: '陳俊佑', password: '123', role: 'tech_staff', displayName: '陳俊佑', status: 'active' },
  { username: '陳志彥', password: '123', role: 'tech_staff', displayName: '陳志彥', status: 'active' },
  { username: '陳志源', password: '123', role: 'tech_staff', displayName: '陳志源', status: 'active' },
  { username: '廖家民', password: '123', role: 'tech_staff', displayName: '廖家民', status: 'active' },
  { username: '蘇昭溢', password: '123', role: 'tech_staff', displayName: '蘇昭溢', status: 'active' },
  { username: '王善禾', password: '123', role: 'tech_staff', displayName: '王善禾', status: 'active' }
];

const DEFAULT_ROLES = [
  { id: 'admin', name: '系統管理員 (admin)' },
  { id: 'production', name: '生產人員 (production)' },
  { id: 'sales', name: '業務人員 (sales)' },
  { id: 'tech_manager', name: '技服主管 (tech_manager)' },
  { id: 'tech_staff', name: '技服人員 (tech_staff)' },
  { id: 'transporter', name: '運輸公司 (transporter)' }
];

const DEFAULT_SYSTEM_FEATURES = [
  { id: 'tab-dashboard', name: '儀表板總覽' },
  { id: 'tab-sales', name: '業務專區' },
  { id: 'tab-production', name: '生產專區' },
  { id: 'tab-tech', name: '技服課專區' },
  { id: 'tab-transport', name: '運輸商專區' },
  { id: 'tab-query', name: '技服個人查詢' },
  { id: 'tab-users', name: '帳號管理' },
  { id: 'tab-permissions', name: '權限設定' },
  { id: 'tab-logs', name: '作業日誌' }
];

const DEFAULT_PERMISSIONS = {
  admin: ['tab-dashboard', 'tab-sales', 'tab-production', 'tab-tech', 'tab-transport', 'tab-query', 'tab-users', 'tab-permissions', 'tab-logs'],
  production: ['tab-dashboard', 'tab-sales', 'tab-production'],
  sales: ['tab-dashboard', 'tab-sales', 'tab-tech', 'tab-transport', 'tab-query'],
  tech_manager: ['tab-dashboard', 'tab-sales', 'tab-tech', 'tab-transport', 'tab-query'],
  tech_staff: ['tab-query'],
  transporter: ['tab-dashboard', 'tab-transport']
};

const USER_EXCEL_FILE = path.join(__dirname, '帳號密碼管理.xlsx');
let lastUserMtime = 0;
let cachedUsers = null;

function loadUsersFromExcel(forceReload = false) {
  if (!fs.existsSync(USER_EXCEL_FILE)) return null;
  try {
    const stat = fs.statSync(USER_EXCEL_FILE);
    if (!forceReload && cachedUsers && stat.mtimeMs === lastUserMtime) {
      return cachedUsers;
    }
    const workbook = xlsx.readFile(USER_EXCEL_FILE);
    const sheet = workbook.Sheets[workbook.SheetNames[0]];
    const config = {
      username: 'A',
      password: 'B',
      role: 'C',
      displayName: 'D',
      status: 'E'
    };
    
    const rows = parseSheetByColumns(sheet, 2, config);
    const users = rows
      .filter(r => r.username && r.password && r.role)
      .map(r => ({
        username: String(r.username).trim(),
        password: String(r.password).trim(),
        role: String(r.role).trim(),
        displayName: r.displayName ? String(r.displayName).trim() : String(r.username).trim(),
        status: (r.status && String(r.status).trim() === '停用') ? 'inactive' : 'active'
      }));
      
    if (users.length > 0) {
      if (!users.some(u => u.username.toLowerCase() === 'admin')) {
        users.unshift({
          username: 'admin',
          password: '123',
          role: 'admin',
          displayName: '系統管理員',
          status: 'active'
        });
      }
      cachedUsers = users;
      lastUserMtime = stat.mtimeMs;
      return users;
    }
  } catch (err) {
    console.error('Error loading users from Excel:', err);
  }
  return cachedUsers || null;
}

function saveUsersToExcel(users) {
  try {
    const headers = ['帳號', '密碼', '權限角色 (必填)', '顯示名稱', '狀態', '角色說明對照 (參考用)'];
    const data = [headers];
    users.forEach(u => {
      data.push([
        u.username,
        u.password,
        u.role,
        u.displayName || u.username,
        u.status === 'inactive' ? '停用' : '啟用',
        u.role === 'admin' ? '系統管理員' : (u.role === 'sales' ? '業務員' : '')
      ]);
    });
    const wb = xlsx.utils.book_new();
    const ws = xlsx.utils.aoa_to_sheet(data);
    xlsx.utils.book_append_sheet(wb, ws, '帳號清單');
    const buffer = xlsx.write(wb, { type: 'buffer', bookType: 'xlsx' });
    fs.writeFileSync(USER_EXCEL_FILE, buffer);
    console.log('[UserManagement] 成功同步鏡像回寫至 帳號密碼管理.xlsx');
  } catch (err) {
    console.error('Error exporting users to Excel:', err);
  }
}

const DRIVER_EXCEL_FILE = path.join(__dirname, '司機名冊管理.xlsx');
let lastDriverMtime = 0;
let cachedDrivers = null;

function loadDriversFromExcel(forceReload = false) {
  if (!fs.existsSync(DRIVER_EXCEL_FILE)) return null;
  try {
    const stat = fs.statSync(DRIVER_EXCEL_FILE);
    if (!forceReload && cachedDrivers && stat.mtimeMs === lastDriverMtime) {
      return cachedDrivers;
    }
    const workbook = xlsx.readFile(DRIVER_EXCEL_FILE);
    const sheet = workbook.Sheets[workbook.SheetNames[0]];
    const config = {
      code: 'B',
      plate: 'C',
      name: 'D',
      phone: 'E',
      id_card: 'F'
    };
    
    const rows = parseSheetByColumns(sheet, 2, config);
    const drivers = rows
      .filter(r => r.code)
      .map(r => ({
        code: String(r.code).trim(),
        plate: r.plate ? String(r.plate).trim() : '',
        name: r.name ? String(r.name).trim() : '',
        phone: r.phone ? String(r.phone).trim() : '',
        id_card: r.id_card ? String(r.id_card).trim() : ''
      }));
      
    if (drivers.length > 0) {
      cachedDrivers = drivers;
      lastDriverMtime = stat.mtimeMs;
      return drivers;
    }
  } catch (err) {
    console.error('Error loading drivers from Excel:', err);
  }
  return cachedDrivers || null;
}

function saveDriversToExcel(drivers) {
  try {
    const headers = [null, "景山司機代碼", "車牌", "司機", "電話", "ID/身份證號碼"];
    const data = [headers];
    drivers.forEach(d => {
      data.push([
        null,
        d.code ? Number(d.code) || d.code : null,
        d.plate,
        d.name,
        d.phone,
        d.id_card
      ]);
    });
    const wb = xlsx.book_new();
    const ws = xlsx.utils.aoa_to_sheet(data);
    xlsx.book_append_sheet(wb, ws, "司機清單");
    const buffer = xlsx.write(wb, { type: 'buffer', bookType: 'xlsx' });
    fs.writeFileSync(DRIVER_EXCEL_FILE, buffer);
    console.log('Saved drivers list to Excel successfully.');
  } catch (err) {
    console.error('Error exporting drivers list to Excel:', err);
  }
}

// Initialize database
function initDB() {
  let dbExists = fs.existsSync(DB_FILE);
  let db = { orders: [], drivers: [], users: DEFAULT_USERS, push_subscriptions: {} };
  
  if (dbExists) {
    try {
      const data = fs.readFileSync(DB_FILE, 'utf-8');
      db = JSON.parse(data);
      let updated = false;
      
      const excelUsers = loadUsersFromExcel();
      if (excelUsers) {
        db.users = excelUsers;
        updated = true;
      }
      
      const excelDrivers = loadDriversFromExcel();
      if (excelDrivers) {
        db.drivers = excelDrivers;
        updated = true;
      }

      if (!db.push_subscriptions) {
        db.push_subscriptions = {};
        updated = true;
      }

      if (!db.roles) {
        db.roles = DEFAULT_ROLES;
        updated = true;
      }

      if (!db.permissions) {
        db.permissions = DEFAULT_PERMISSIONS;
        updated = true;
      }
      
      if (updated) {
        fs.writeFileSync(DB_FILE, JSON.stringify(db, null, 2), 'utf-8');
      }
    } catch (err) {
      fs.writeFileSync(DB_FILE, JSON.stringify(db, null, 2), 'utf-8');
    }
  } else {
    const excelUsers = loadUsersFromExcel();
    const excelDrivers = loadDriversFromExcel();
    if (excelUsers) db.users = excelUsers;
    if (excelDrivers) db.drivers = excelDrivers;
    db.push_subscriptions = {};
    db.roles = DEFAULT_ROLES;
    db.permissions = DEFAULT_PERMISSIONS;
    fs.writeFileSync(DB_FILE, JSON.stringify(db, null, 2), 'utf-8');
  }
}
initDB();

function getDB() {
  try {
    const data = fs.readFileSync(DB_FILE, 'utf-8');
    const db = JSON.parse(data);
    
    const excelUsers = loadUsersFromExcel();
    if (excelUsers) db.users = excelUsers;
    
    const excelDrivers = loadDriversFromExcel();
    if (excelDrivers) db.drivers = excelDrivers;
    
    db.push_subscriptions = db.push_subscriptions || {};
    db.roles = db.roles || DEFAULT_ROLES;
    db.permissions = db.permissions || DEFAULT_PERMISSIONS;
    return db;
  } catch (err) {
    const excelUsers = loadUsersFromExcel();
    const excelDrivers = loadDriversFromExcel();
    return {
      orders: [],
      drivers: excelDrivers || [],
      users: excelUsers || DEFAULT_USERS,
      push_subscriptions: {},
      roles: DEFAULT_ROLES,
      permissions: DEFAULT_PERMISSIONS
    };
  }
}

function saveDB(db) {
  fs.writeFileSync(DB_FILE, JSON.stringify(db, null, 2), 'utf-8');
}

// 發送 Web Push 推播函式 (可精準發送至技服人員登記的所有手機/設備)
async function sendPushNotificationToUser(targetName, payload) {
  if (!targetName) return;
  const db = getDB();
  db.push_subscriptions = db.push_subscriptions || {};

  const cleanName = String(targetName).split(/[\r\n\s]/)[0].trim().toLowerCase();
  if (!cleanName) return;

  // 1. 取得該人員可能對應的所有別名 (帳號、顯示名稱)
  const candidateNames = new Set([cleanName]);
  if (db.users) {
    db.users.forEach(u => {
      const uName = (u.username || '').trim().toLowerCase();
      const dName = (u.displayName || '').trim().toLowerCase();
      if (uName === cleanName || dName === cleanName || (cleanName && (uName.includes(cleanName) || dName.includes(cleanName)))) {
        if (uName) candidateNames.add(uName);
        if (dName) candidateNames.add(dName);
      }
    });
  }

  // 2. 在推播訂閱名冊中搜尋匹配的憑證
  const matchingKeys = Object.keys(db.push_subscriptions).filter(k => {
    const lk = k.trim().toLowerCase();
    for (const name of candidateNames) {
      if (lk === name || lk.includes(name) || name.includes(lk)) return true;
    }
    return false;
  });

  if (matchingKeys.length === 0) {
    console.log(`[WebPush] 未找到技服同仁「${cleanName}」的手機推播憑證 (尚未在手機啟用通知)`);
    return;
  }

  let dbUpdated = false;

  for (const key of matchingKeys) {
    const subs = db.push_subscriptions[key] || [];
    const validSubs = [];

    for (const sub of subs) {
      try {
        await webpush.sendNotification(sub, JSON.stringify(payload));
        console.log(`[WebPush] 🔔 成功發送推播給「${key}」: ${payload.title}`);
        validSubs.push(sub);
      } catch (err) {
        console.error(`[WebPush] 發送給「${key}」失敗:`, err.statusCode || err.message);
        if (err.statusCode === 404 || err.statusCode === 410) {
          console.log(`[WebPush] 設備推播憑證已過期失效，自動自名冊剔除: ${key}`);
          dbUpdated = true;
        } else {
          validSubs.push(sub);
        }
      }
    }
    db.push_subscriptions[key] = validSubs;
  }

  if (dbUpdated) {
    saveDB(db);
  }
}


function addLog(db, operator, role, action, details) {
  try {
    if (!db.logs) db.logs = [];
    const timestamp = new Date().toLocaleString('zh-TW', { timeZone: 'Asia/Taipei' });
    db.logs.push({
      operator: operator || '系統',
      role: role || 'system',
      action: action,
      details: details,
      timestamp: timestamp
    });
    if (db.logs.length > 200) {
      db.logs = db.logs.slice(-200);
    }
  } catch (err) {
    console.error('Error writing operation log:', err);
  }
}

// Normalization Helpers
function normalizeStr(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/\s+/g, '') // remove all whitespace
    .replace(/[\uff01-\uff5e]/g, (ch) => String.fromCharCode(ch.charCodeAt(0) - 0xfee0)) // full-width to half-width
    .toLowerCase();
}

function normalizeDate(d) {
  if (!d) return '';
  if (d instanceof Date) {
    // Offset local timezone if parsed by SheetJS
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
  }
  // Try to parse string
  const str = String(d).trim();
  const match = str.match(/^(\d{4})[-/](\d{1,2})[-/](\d{1,2})/);
  if (match) {
    return `${match[1]}-${match[2].padStart(2, '0')}-${match[3].padStart(2, '0')}`;
  }
  // Handle Taiwan year Minguo format like 115-07-03
  const minguoMatch = str.match(/^(\d{2,3})[-/](\d{1,2})[-/](\d{1,2})/);
  if (minguoMatch) {
    const adYear = parseInt(minguoMatch[1]) + 1911;
    return `${adYear}-${minguoMatch[2].padStart(2, '0')}-${minguoMatch[3].padStart(2, '0')}`;
  }
  return str;
}

function normalizeTime(t) {
  if (!t) return '';
  if (t instanceof Date) {
    const h = String(t.getHours()).padStart(2, '0');
    const m = String(t.getMinutes()).padStart(2, '0');
    return `${h}:${m}`;
  }
  const str = String(t).trim();
  const match = str.match(/^(\d{1,2}):(\d{2})/);
  if (match) {
    return `${match[1].padStart(2, '0')}:${match[2]}`;
  }
  return str;
}

// Parsing Excel sheet
function parseExcelBuffer(buffer) {
  const workbook = xlsx.read(buffer, { cellDates: true, dateNF: 'yyyy-mm-dd hh:mm:ss' });
  return workbook;
}

const orderColumns = {
  id: 'A',
  batch: 'B',
  client: 'C',
  destination: 'D',
  product: 'E',
  expected_date: 'F',
  arrival_time: 'G',
  transport_type: 'H',
  fill_hand: 'I',
  plate: 'J',
  driver: 'K',
  phone: 'L',
  departure_date: 'M',
  departure_time: 'N',
  driver_code: 'O'
};

const driverColumns = {
  code: 'B',
  plate: 'C',
  name: 'D',
  phone: 'E',
  id_card: 'F'
};

function getCellValue(cell, type) {
  if (!cell || cell.v === null || cell.v === undefined) return null;
  const val = cell.v;
  if (type === 'date') {
    return normalizeDate(val);
  }
  if (type === 'time') {
    return normalizeTime(val);
  }
  return String(val).trim();
}

function parseSheetByColumns(sheet, startRow, columnsConfig) {
  if (!sheet || !sheet['!ref']) return [];
  const range = xlsx.utils.decode_range(sheet['!ref']);
  const maxRow = range.e.r + 1;
  const data = [];
  
  for (let r = startRow; r <= maxRow; r++) {
    const rowObj = {};
    let hasValue = false;
    
    for (const [key, colLetter] of Object.entries(columnsConfig)) {
      const cellAddress = `${colLetter}${r}`;
      const cell = sheet[cellAddress];
      
      let type = 'string';
      if (key === 'expected_date' || key === 'departure_date') type = 'date';
      else if (key === 'arrival_time' || key === 'departure_time') type = 'time';
      
      const val = getCellValue(cell, type);
      if (val !== null && val !== '') {
        hasValue = true;
      }
      rowObj[key] = val;
    }
    
    // Check if the row has any content and is not completely empty
    if (hasValue) {
      data.push(rowObj);
    }
  }
  return data;
}

// API Routes

// 0. Web Push Notification APIs
app.get('/api/push/vapid-public-key', (req, res) => {
  res.json({ success: true, publicKey: vapidKeys.publicKey });
});

app.post('/api/push/subscribe', (req, res) => {
  try {
    const { username, subscription } = req.body;
    if (!username || !subscription || !subscription.endpoint) {
      return res.status(400).json({ success: false, message: '請提供使用者名稱與推播訂閱憑證' });
    }
    const cleanUser = String(username).split(/[\r\n\s]/)[0].trim();
    const db = getDB();
    db.push_subscriptions = db.push_subscriptions || {};
    db.push_subscriptions[cleanUser] = db.push_subscriptions[cleanUser] || [];

    // 檢查端點是否已登記過
    const existsIdx = db.push_subscriptions[cleanUser].findIndex(s => s.endpoint === subscription.endpoint);
    if (existsIdx >= 0) {
      db.push_subscriptions[cleanUser][existsIdx] = {
        ...subscription,
        updatedAt: new Date().toISOString()
      };
    } else {
      db.push_subscriptions[cleanUser].push({
        ...subscription,
        subscribedAt: new Date().toISOString()
      });
    }

    saveDB(db);
    console.log(`[WebPush] 成功為「${cleanUser}」登記推播設備。目前設備數：${db.push_subscriptions[cleanUser].length}`);
    res.json({ success: true, message: `成功為 ${cleanUser} 綁定此設備推播！` });
  } catch (err) {
    console.error('[WebPush] 訂閱錯誤:', err);
    res.status(500).json({ success: false, message: err.message });
  }
});

app.post('/api/push/test', async (req, res) => {
  try {
    const { username } = req.body;
    if (!username) {
      return res.status(400).json({ success: false, message: '請提供使用者名稱' });
    }
    const cleanUser = String(username).split(/[\r\n\s]/)[0].trim();
    await sendPushNotificationToUser(cleanUser, {
      title: '🔔 【勝一槽車排程】推播測試成功！',
      body: `您好，${cleanUser}！這台設備已成功連線推播系統，派工與時間異動將隨時提醒您。`,
      data: { url: '/' }
    });
    res.json({ success: true, message: '測試推播已發送！' });
  } catch (err) {
    console.error('[WebPush] 測試推播失敗:', err);
    res.status(500).json({ success: false, message: err.message });
  }
});

// 1. Get all orders
// Server-Sent Events (SSE) 即時推播事件流 (供電腦管理端與手機端即時雙向狀態同步)
let sseClients = [];

app.get('/api/events', (req, res) => {
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.flushHeaders();

  const clientId = Date.now();
  const newClient = { id: clientId, res };
  sseClients.push(newClient);

  // 立即回傳已連線心跳
  res.write(`data: ${JSON.stringify({ type: 'connected', clientId })}\n\n`);

  req.on('close', () => {
    sseClients = sseClients.filter(c => c.id !== clientId);
  });
});

function broadcastEvent(eventType, data) {
  const payload = `data: ${JSON.stringify({ type: eventType, data, timestamp: Date.now() })}\n\n`;
  sseClients.forEach(c => {
    try {
      c.res.write(payload);
    } catch(e) {}
  });
}

// 每 20 秒送出保活心跳註解，防止代理伺服器或 Tunnel 中斷
setInterval(() => {
  sseClients.forEach(c => {
    try {
      c.res.write(': keep-alive\n\n');
    } catch(e) {}
  });
}, 20000);

// 1. Get all current orders
app.get('/api/orders', (req, res) => {
  const db = getDB();
  res.json({ success: true, data: db.orders });
});

// 1.1 標記訂單為已讀 (技服人員點擊推播或開啟訂單卡片時記錄)
app.post('/api/orders/mark-read', (req, res) => {
  try {
    const { orderKey, username } = req.body;
    if (!orderKey || !username) {
      return res.status(400).json({ success: false, message: '缺少 orderKey 或 username' });
    }
    const db = getDB();
    const cleanUser = String(username).trim();
    
    // 比對 orderKey (支援 id 或複合欄位)
    let order = db.orders.find(o => o.id && o.id === orderKey);
    if (!order) {
      order = db.orders.find(o => `${o.destination}_${o.expected_date}_${o.arrival_time}` === orderKey);
    }

    if (!order) {
      return res.status(404).json({ success: false, message: '找不到對應訂單' });
    }

    const nowStr = new Date().toLocaleString('zh-TW', { timeZone: 'Asia/Taipei', hour12: false });
    order.read_status = 'read';
    order.read_at = nowStr;
    order.read_by = cleanUser;

    saveDB(db);
    console.log(`[ReadReceipt] 技服同仁「${cleanUser}」已讀訂單【${order.destination} (${order.arrival_time})】時間: ${nowStr}`);

    // 即時廣播給全系統所有已連線之電腦與手機客戶端！
    broadcastEvent('order_read', {
      orderKey,
      orderId: order.id,
      destination: order.destination,
      expected_date: order.expected_date,
      arrival_time: order.arrival_time,
      read_status: 'read',
      read_at: nowStr,
      read_by: cleanUser
    });

    res.json({ success: true, message: '已成功標記為已讀', read_status: 'read', read_at: nowStr, read_by: cleanUser });
  } catch (err) {
    console.error('Mark read error:', err);
    res.status(500).json({ success: false, message: err.message });
  }
});

// 2. Get all drivers
app.get('/api/drivers', (req, res) => {
  const db = getDB();
  res.json({ success: true, data: db.drivers });
});

// Login API
app.post('/api/login', (req, res) => {
  const { username, password } = req.body;
  const db = getDB();
  const user = db.users.find(u => u.username === username && u.password === password);
  if (user) {
    if (user.status === 'inactive') {
      addLog(db, user.username, user.role, '使用者登入', '登入失敗 (帳號已停用)');
      saveDB(db);
      return res.status(403).json({ success: false, message: '此帳號已被停用，請聯繫系統管理員！' });
    }
    addLog(db, user.username, user.role, '使用者登入', '登入成功');
    saveDB(db);
    res.json({
      success: true,
      user: {
        username: user.username,
        role: user.role,
        displayName: user.displayName || user.username,
        status: user.status || 'active'
      },
      permissions: (db.permissions && db.permissions[user.role]) ? db.permissions[user.role] : (DEFAULT_PERMISSIONS[user.role] || ['tab-dashboard'])
    });
  } else {
    addLog(db, username || '未知使用者', 'unknown', '使用者登入', '登入失敗 (密碼錯誤或帳號不存在)');
    saveDB(db);
    res.status(401).json({ success: false, message: '帳號或密碼錯誤！' });
  }
});

// =============================================================================
// 使用者帳號管理 (User Management) & 角色權限設定 (Permissions) APIs
// =============================================================================

// 取得所有使用者帳號列表
app.get('/api/users', (req, res) => {
  try {
    const db = getDB();
    const users = (db.users || []).map(u => ({
      username: u.username,
      displayName: u.displayName || u.username,
      role: u.role,
      status: u.status || 'active'
    }));
    res.json({ success: true, users });
  } catch (err) {
    res.status(500).json({ success: false, message: err.message });
  }
});

// 新增使用者帳號 (同步回寫 Excel)
app.post('/api/users', (req, res) => {
  try {
    const { username, password, role, displayName, status, operator } = req.body;
    if (!username || !password || !role) {
      return res.status(400).json({ success: false, message: '請填寫必填欄位 (帳號、密碼、權限角色)' });
    }
    const cleanUser = String(username).trim();
    const db = getDB();
    if (db.users.some(u => u.username.toLowerCase() === cleanUser.toLowerCase())) {
      return res.status(400).json({ success: false, message: `帳號「${cleanUser}」已存在！` });
    }

    const newUser = {
      username: cleanUser,
      password: String(password).trim(),
      role: String(role).trim(),
      displayName: displayName ? String(displayName).trim() : cleanUser,
      status: status === 'inactive' ? 'inactive' : 'active'
    };

    db.users.push(newUser);
    saveDB(db);
    saveUsersToExcel(db.users);
    addLog(db, operator || 'admin', 'admin', '新增使用者', `新增帳號「${cleanUser}」(${newUser.displayName} / 角色: ${newUser.role})`);
    saveDB(db);

    res.json({ success: true, message: `成功新增使用者「${cleanUser}」！`, user: newUser });
  } catch (err) {
    console.error('Add user error:', err);
    res.status(500).json({ success: false, message: err.message });
  }
});

// 編輯使用者帳號 (同步回寫 Excel)
app.put('/api/users/:username', (req, res) => {
  try {
    const targetUsername = req.params.username;
    const { password, role, displayName, status, operator } = req.body;
    const db = getDB();
    const userIndex = db.users.findIndex(u => u.username === targetUsername);
    if (userIndex === -1) {
      return res.status(404).json({ success: false, message: '找不到該使用者' });
    }

    const user = db.users[userIndex];
    if (displayName !== undefined) user.displayName = String(displayName).trim();
    if (role !== undefined) user.role = String(role).trim();
    if (status !== undefined) user.status = status === 'inactive' ? 'inactive' : 'active';
    if (password && String(password).trim()) {
      user.password = String(password).trim();
    }

    saveDB(db);
    saveUsersToExcel(db.users);
    addLog(db, operator || 'admin', 'admin', '編輯使用者', `修改帳號「${targetUsername}」資訊 (角色: ${user.role}, 狀態: ${user.status})`);
    saveDB(db);

    res.json({ success: true, message: `成功更新使用者「${targetUsername}」！`, user });
  } catch (err) {
    console.error('Update user error:', err);
    res.status(500).json({ success: false, message: err.message });
  }
});

// 刪除使用者帳號 (同步回寫 Excel)
app.delete('/api/users/:username', (req, res) => {
  try {
    const targetUsername = req.params.username;
    const operator = req.query.operator || 'admin';
    if (targetUsername.toLowerCase() === 'admin') {
      return res.status(403).json({ success: false, message: '系統管理員帳號 (admin) 為核心保護帳號，不可刪除！' });
    }

    const db = getDB();
    const userIndex = db.users.findIndex(u => u.username === targetUsername);
    if (userIndex === -1) {
      return res.status(404).json({ success: false, message: '找不到該使用者' });
    }

    const removed = db.users.splice(userIndex, 1)[0];
    saveDB(db);
    saveUsersToExcel(db.users);
    addLog(db, operator, 'admin', '刪除使用者', `刪除帳號「${targetUsername}」(${removed.displayName || targetUsername})`);
    saveDB(db);

    res.json({ success: true, message: `已成功刪除使用者「${targetUsername}」！` });
  } catch (err) {
    console.error('Delete user error:', err);
    res.status(500).json({ success: false, message: err.message });
  }
});

// 修改個人密碼 API
app.post('/api/users/change-password', (req, res) => {
  try {
    const { username, oldPassword, newPassword } = req.body;
    if (!username || !oldPassword || !newPassword) {
      return res.status(400).json({ success: false, message: '請提供帳號、舊密碼與新密碼' });
    }
    const db = getDB();
    const user = db.users.find(u => u.username === username);
    if (!user) {
      return res.status(404).json({ success: false, message: '使用者不存在' });
    }
    if (user.password !== oldPassword) {
      return res.status(400).json({ success: false, message: '原密碼輸入不正確，請重新輸入！' });
    }

    user.password = String(newPassword).trim();
    saveDB(db);
    saveUsersToExcel(db.users);
    addLog(db, username, user.role, '修改個人密碼', '密碼變更成功');
    saveDB(db);

    res.json({ success: true, message: '密碼修改成功！下次登入請使用新密碼。' });
  } catch (err) {
    console.error('Change password error:', err);
    res.status(500).json({ success: false, message: err.message });
  }
});

// 取得角色與功能權限設定對應矩陣
app.get('/api/permissions', (req, res) => {
  try {
    const db = getDB();
    res.json({
      success: true,
      roles: db.roles || DEFAULT_ROLES,
      features: DEFAULT_SYSTEM_FEATURES,
      permissions: db.permissions || DEFAULT_PERMISSIONS
    });
  } catch (err) {
    res.status(500).json({ success: false, message: err.message });
  }
});

// 儲存角色權限矩陣設定
app.post('/api/permissions', (req, res) => {
  try {
    const { permissions, operator } = req.body;
    if (!permissions || typeof permissions !== 'object') {
      return res.status(400).json({ success: false, message: '無效的權限設定格式' });
    }
    const db = getDB();
    db.permissions = permissions;
    saveDB(db);
    addLog(db, operator || 'admin', 'admin', '修改角色權限', '更新系統功能權限對應矩陣設定');
    saveDB(db);

    res.json({ success: true, message: '角色功能權限設定已成功儲存！' });
  } catch (err) {
    console.error('Save permissions error:', err);
    res.status(500).json({ success: false, message: err.message });
  }
});

// 新增自訂角色
app.post('/api/roles', (req, res) => {
  try {
    const { roleId, roleName, operator } = req.body;
    if (!roleId || !roleName) {
      return res.status(400).json({ success: false, message: '請提供角色代碼與角色名稱' });
    }
    const cleanId = String(roleId).trim().toLowerCase();
    const cleanName = String(roleName).trim();
    const db = getDB();
    db.roles = db.roles || DEFAULT_ROLES;
    if (db.roles.some(r => r.id === cleanId)) {
      return res.status(400).json({ success: false, message: `角色代碼「${cleanId}」已存在！` });
    }

    const newRole = { id: cleanId, name: `${cleanName} (${cleanId})` };
    db.roles.push(newRole);
    db.permissions = db.permissions || DEFAULT_PERMISSIONS;
    db.permissions[cleanId] = ['tab-dashboard'];
    saveDB(db);
    addLog(db, operator || 'admin', 'admin', '新增角色', `新增角色「${cleanName} (${cleanId})」`);
    saveDB(db);

    res.json({ success: true, message: `成功新增角色「${cleanName}」！`, role: newRole });
  } catch (err) {
    console.error('Add role error:', err);
    res.status(500).json({ success: false, message: err.message });
  }
});

// Excel 批次匯入帳號
app.post('/api/users/upload', upload.single('file'), (req, res) => {
  try {
    const operator = req.query.operator || 'admin';
    if (!req.file) {
      return res.status(400).json({ success: false, message: '請選擇上傳的 Excel 檔案' });
    }
    const workbook = parseExcelBuffer(req.file.buffer);
    const sheet = workbook.Sheets[workbook.SheetNames[0]];
    const config = {
      username: 'A',
      password: 'B',
      role: 'C',
      displayName: 'D',
      status: 'E'
    };
    const rows = parseSheetByColumns(sheet, 2, config);
    const validRows = rows.filter(r => r.username && r.password && r.role);
    if (validRows.length === 0) {
      return res.status(400).json({ success: false, message: 'Excel 內無有效帳號資料列' });
    }

    const db = getDB();
    let addCount = 0;
    let updateCount = 0;

    validRows.forEach(r => {
      const uName = String(r.username).trim();
      const existing = db.users.find(u => u.username.toLowerCase() === uName.toLowerCase());
      if (existing) {
        existing.password = String(r.password).trim();
        existing.role = String(r.role).trim();
        if (r.displayName) existing.displayName = String(r.displayName).trim();
        existing.status = (r.status && String(r.status).trim() === '停用') ? 'inactive' : 'active';
        updateCount++;
      } else {
        db.users.push({
          username: uName,
          password: String(r.password).trim(),
          role: String(r.role).trim(),
          displayName: r.displayName ? String(r.displayName).trim() : uName,
          status: (r.status && String(r.status).trim() === '停用') ? 'inactive' : 'active'
        });
        addCount++;
      }
    });

    saveDB(db);
    saveUsersToExcel(db.users);
    addLog(db, operator, 'admin', 'Excel匯入帳號', `批次更新 ${updateCount} 筆，新增 ${addCount} 筆帳號`);
    saveDB(db);

    res.json({
      success: true,
      message: `成功自 Excel 匯入：新增 ${addCount} 筆、更新 ${updateCount} 筆帳號！`
    });
  } catch (err) {
    console.error('Import users error:', err);
    res.status(500).json({ success: false, message: err.message });
  }
});

// 下載帳號密碼 Excel 範本
app.get('/api/users/download-template', (req, res) => {
  try {
    const db = getDB();
    saveUsersToExcel(db.users);
    res.download(USER_EXCEL_FILE, '勝一帳號密碼名冊.xlsx');
  } catch (err) {
    res.status(500).json({ success: false, message: err.message });
  }
});



// 3. Sales uploads the baseline Excel
app.post('/api/upload/sales', upload.single('file'), (req, res) => {
  try {
    const operator = req.query.operator || '未知使用者';
    const role = req.query.role || 'sales';

    if (!req.file) {
      return res.status(400).json({ success: false, message: '請上傳檔案' });
    }
    const workbook = parseExcelBuffer(req.file.buffer);

    // Find "空白班表" or the first sheet
    let sheetName = workbook.SheetNames.find(name => name.includes('班表') || name.includes('清單'));
    if (!sheetName) sheetName = workbook.SheetNames[0];
    const sheet = workbook.Sheets[sheetName];
    
    const orders = parseSheetByColumns(sheet, 2, orderColumns);
    if (orders.length === 0) {
      return res.status(400).json({ success: false, message: '工作表內無有效資料列' });
    }

    // Load "司機清單" if exists
    let drivers = [];
    const driverSheetName = workbook.SheetNames.find(name => name.includes('司機'));
    if (driverSheetName) {
      const dSheet = workbook.Sheets[driverSheetName];
      drivers = parseSheetByColumns(dSheet, 2, driverColumns);
      // Filter out drivers where code is empty
      drivers = drivers.filter(d => d.code);
    }

    const db = getDB();
    db.orders = orders;
    if (drivers.length > 0) {
      db.drivers = drivers;
      saveDriversToExcel(drivers);
    }
    
    addLog(db, operator, role, '上傳基準 Excel', `成功匯入 ${orders.length} 筆訂單，${drivers.length} 筆司機清單資料`);
    saveDB(db);

    res.json({
      success: true,
      message: `成功匯入 ${orders.length} 筆訂單，${drivers.length} 筆司機資料`,
      orderCount: orders.length,
      driverCount: drivers.length
    });
  } catch (err) {
    console.error(err);
    res.status(500).json({ success: false, message: `伺服器處理錯誤: ${err.message}` });
  }
});

// Matching helper
function findMatchingOrder(dbOrders, uploadedOrder) {
  // 1. Try match by ID (出貨通知單單別號) if present
  if (uploadedOrder.id) {
    const match = dbOrders.find(o => o.id && o.id === uploadedOrder.id);
    if (match) return { match, matchBy: 'id' };
  }

  // 2. Else match by: 指送地, 品名, 預計到貨日期, 到貨時間 (4 columns)
  const normDest = normalizeStr(uploadedOrder.destination);
  const normProd = normalizeStr(uploadedOrder.product);
  const normDate = normalizeDate(uploadedOrder.expected_date);
  const normTime = normalizeTime(uploadedOrder.arrival_time);

  const match = dbOrders.find(o => {
    return (
      normalizeStr(o.destination) === normDest &&
      normalizeStr(o.product) === normProd &&
      normalizeDate(o.expected_date) === normDate &&
      normalizeTime(o.arrival_time) === normTime
    );
  });

  if (match) return { match, matchBy: 'fields' };
  return { match: null, matchBy: null };
}

// 4. Compare Tech Service Upload
app.post('/api/compare/tech', upload.single('file'), (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ success: false, message: '請上傳檔案' });
    }
        const workbook = parseExcelBuffer(req.file.buffer);
    const sheet = workbook.Sheets[workbook.SheetNames[0]];
    const uploadedOrders = parseSheetByColumns(sheet, 2, orderColumns);

    if (uploadedOrders.length === 0) {
      return res.status(400).json({ success: false, message: '工作表內無有效資料列' });
    }

    const db = getDB();

    const results = {
      matched: [],
      mismatched: [], // Rows in uploaded Excel that don't match any db order
      missing: []     // DB orders that aren't in uploaded Excel (optional info)
    };

    const matchedDbIds = new Set();

    uploadedOrders.forEach((uOrder, idx) => {
      const { match, matchBy } = findMatchingOrder(db.orders, uOrder);
      if (match) {
        matchedDbIds.add(match.id || `${match.destination}-${match.product}-${match.expected_date}-${match.arrival_time}`);
        results.matched.push({
          rowNum: idx + 2,
          uploaded: uOrder,
          existing: match,
          matchBy: matchBy,
          fillHandNew: uOrder.fill_hand
        });
      } else {
        results.mismatched.push({
          rowNum: idx + 2,
          uploaded: uOrder,
          reason: '找不到對應的基準訂單（請確認指送地、品名、預計到貨日期、到貨時間是否完全一致）'
        });
      }
    });

    // Find missing in upload
    db.orders.forEach(o => {
      const key = o.id || `${o.destination}-${o.product}-${o.expected_date}-${o.arrival_time}`;
      if (!matchedDbIds.has(key)) {
        results.missing.push(o);
      }
    });

    res.json({ success: true, results });
  } catch (err) {
    console.error(err);
    res.status(500).json({ success: false, message: `伺服器處理錯誤: ${err.message}` });
  }
});

// 5. Commit Tech Service Upload
app.post('/api/import/tech', (req, res) => {
  try {
    const { matchedRows, operator, role } = req.body; // Array of { existingKey: ..., fillHandNew: ... }
    if (!matchedRows || !Array.isArray(matchedRows)) {
      return res.status(400).json({ success: false, message: '無效的匯入資料' });
    }

    const db = getDB();
    let updatedCount = 0;
    const techAssignments = {};

    matchedRows.forEach(item => {
      // Find the order in DB
      let order = null;
      if (item.id) {
        order = db.orders.find(o => o.id === item.id);
      } else {
        // Find by fields
        const nd = normalizeStr(item.destination);
        const np = normalizeStr(item.product);
        const ndate = normalizeDate(item.expected_date);
        const ntime = normalizeTime(item.arrival_time);
        order = db.orders.find(o => 
          normalizeStr(o.destination) === nd &&
          normalizeStr(o.product) === np &&
          normalizeDate(o.expected_date) === ndate &&
          normalizeTime(o.arrival_time) === ntime
        );
      }

      if (order) {
        order.fill_hand = item.fill_hand;
        order.read_status = 'unread';
        order.read_at = null;
        order.read_by = null;
        updatedCount++;
        const techName = (item.fill_hand || '').split(/[\r\n\s]/)[0].trim();
        if (techName) {
          if (!techAssignments[techName]) techAssignments[techName] = [];
          const oKey = order.id || `${order.destination}_${order.expected_date}_${order.arrival_time}`;
          techAssignments[techName].push({
            key: oKey,
            destination: order.destination,
            product: order.product,
            expected_date: order.expected_date,
            arrival_time: order.arrival_time
          });
        }
      }
    });

    addLog(db, operator || '未知使用者', role || 'tech_manager', '匯入技服充填手', `成功比對更新了 ${updatedCount} 筆充填手資料`);
    saveDB(db);

    // 發送即時推播通知給被指派之技服同仁
    for (const [techName, orders] of Object.entries(techAssignments)) {
      const count = orders.length;
      const first = orders[0];
      const bodyText = count === 1
        ? `【${first.destination}】${first.product || ''}\n到貨時間：${first.expected_date || ''} ${first.arrival_time || ''}，請點擊確認！`
        : `主管指派了 ${count} 筆槽車充填任務（首筆：${first.destination} ${first.expected_date || ''} ${first.arrival_time || ''}），請點擊查閱！`;
      sendPushNotificationToUser(techName, {
        title: `📋 【新派工通知】勝一槽車充填`,
        body: bodyText,
        data: { url: `/?openOrder=${encodeURIComponent(first.key)}`, orderKey: first.key }
      }).catch(err => console.error('[WebPush] 派工推播失敗:', err));
    }

    res.json({ success: true, message: `成功更新 ${updatedCount} 筆技服充填手資料` });
  } catch (err) {
    console.error(err);
    res.status(500).json({ success: false, message: `伺服器處理錯誤: ${err.message}` });
  }
});

// 6. Compare Transporter Upload
app.post('/api/compare/transport', upload.single('file'), (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ success: false, message: '請上傳檔案' });
    }
    const workbook = parseExcelBuffer(req.file.buffer);
    const sheet = workbook.Sheets[workbook.SheetNames[0]];
    const uploadedOrders = parseSheetByColumns(sheet, 2, orderColumns);

    if (uploadedOrders.length === 0) {
      return res.status(400).json({ success: false, message: '工作表內無有效資料列' });
    }

    const db = getDB();

    const results = {
      matched: [],
      mismatched: [],
      missing: []
    };

    const matchedDbIds = new Set();

    uploadedOrders.forEach((uOrder, idx) => {
      const { match, matchBy } = findMatchingOrder(db.orders, uOrder);
      if (match) {
        matchedDbIds.add(match.id || `${match.destination}-${match.product}-${match.expected_date}-${match.arrival_time}`);
        
        // Auto-lookup driver info if driver_code is provided and other fields are blank
        let autoPlate = uOrder.plate;
        let autoDriver = uOrder.driver;
        let autoPhone = uOrder.phone;
        
        if (uOrder.driver_code && (!uOrder.plate || !uOrder.driver || !uOrder.phone)) {
          const driverLookup = db.drivers.find(d => d.code === uOrder.driver_code);
          if (driverLookup) {
            autoPlate = autoPlate || driverLookup.plate;
            autoDriver = autoDriver || driverLookup.name;
            autoPhone = autoPhone || driverLookup.phone;
          }
        }

        results.matched.push({
          rowNum: idx + 2,
          uploaded: { ...uOrder, plate: autoPlate, driver: autoDriver, phone: autoPhone },
          existing: match,
          matchBy: matchBy
        });
      } else {
        results.mismatched.push({
          rowNum: idx + 2,
          uploaded: uOrder,
          reason: '找不到對應的基準訂單（請確認指送地、品名、預計到貨日期、到貨時間是否完全一致）'
        });
      }
    });

    db.orders.forEach(o => {
      const key = o.id || `${o.destination}-${o.product}-${o.expected_date}-${o.arrival_time}`;
      if (!matchedDbIds.has(key)) {
        results.missing.push(o);
      }
    });

    res.json({ success: true, results });
  } catch (err) {
    console.error(err);
    res.status(500).json({ success: false, message: `伺服器處理錯誤: ${err.message}` });
  }
});

// 7. Commit Transporter Upload
app.post('/api/import/transport', (req, res) => {
  try {
    const { matchedRows, operator, role } = req.body;
    if (!matchedRows || !Array.isArray(matchedRows)) {
      return res.status(400).json({ success: false, message: '無效的匯入資料' });
    }

    const db = getDB();
    let updatedCount = 0;

    matchedRows.forEach(item => {
      let order = null;
      if (item.id) {
        order = db.orders.find(o => o.id === item.id);
      } else {
        const nd = normalizeStr(item.destination);
        const np = normalizeStr(item.product);
        const ndate = normalizeDate(item.expected_date);
        const ntime = normalizeTime(item.arrival_time);
        order = db.orders.find(o => 
          normalizeStr(o.destination) === nd &&
          normalizeStr(o.product) === np &&
          normalizeDate(o.expected_date) === ndate &&
          normalizeTime(o.arrival_time) === ntime
        );
      }

      if (order) {
        order.plate = item.plate;
        order.driver = item.driver;
        order.phone = item.phone;
        order.departure_date = item.departure_date;
        order.departure_time = item.departure_time;
        order.driver_code = item.driver_code;
        updatedCount++;
      }
    });

    addLog(db, operator || '未知使用者', role || 'transporter', '確認匯入運輸派車車輛', `成功比對更新了 ${updatedCount} 筆車輛司機資料`);
    saveDB(db);
    res.json({ success: true, message: `成功更新 ${updatedCount} 筆運輸商司機車輛資料` });
  } catch (err) {
    console.error(err);
    res.status(500).json({ success: false, message: `伺服器處理錯誤: ${err.message}` });
  }
});

// 8. Single Manual Edit
app.post('/api/orders/update-single', (req, res) => {
  try {
    const { order: updatedOrder, operator, role } = req.body;
    if (!updatedOrder) {
      return res.status(400).json({ success: false, message: '無效的更新資料' });
    }

    const db = getDB();
    let orderIndex = -1;
    
    if (updatedOrder.id) {
      orderIndex = db.orders.findIndex(o => o.id === updatedOrder.id);
    } else {
      const nd = normalizeStr(updatedOrder.destination);
      const np = normalizeStr(updatedOrder.product);
      const ndate = normalizeDate(updatedOrder.expected_date);
      const ntime = normalizeTime(updatedOrder.arrival_time);
      orderIndex = db.orders.findIndex(o => 
        normalizeStr(o.destination) === nd &&
        normalizeStr(o.product) === np &&
        normalizeDate(o.expected_date) === ndate &&
        normalizeTime(o.arrival_time) === ntime
      );
    }

    if (orderIndex === -1) {
      return res.status(404).json({ success: false, message: '找不到對應訂單進行編輯' });
    }

    // Auto-lookup driver info if code is changed manually
    const oldOrder = { ...db.orders[orderIndex] };
    const dbOrder = oldOrder;
    let newDriverCode = updatedOrder.driver_code;
    let newPlate = updatedOrder.plate;
    let newDriver = updatedOrder.driver;
    let newPhone = updatedOrder.phone;

    if (newDriverCode && newDriverCode !== dbOrder.driver_code && (!newPlate || !newDriver || !newPhone || newPlate === dbOrder.plate)) {
      const driverLookup = db.drivers.find(d => d.code === newDriverCode);
      if (driverLookup) {
        newPlate = driverLookup.plate;
        newDriver = driverLookup.name;
        newPhone = driverLookup.phone;
      }
    }

    // Apply role-based restrictions
    if (role === 'transporter') {
      // ONLY allow updating transporter fields (plate, driver, phone, departure_date, departure_time, driver_code)
      db.orders[orderIndex] = {
        ...dbOrder,
        plate: newPlate,
        driver: newDriver,
        phone: newPhone,
        departure_date: updatedOrder.departure_date,
        departure_time: updatedOrder.departure_time,
        driver_code: newDriverCode
      };
    } else {
      // Sales / Tech Manager can edit all fields
      db.orders[orderIndex] = {
        ...dbOrder,
        ...updatedOrder,
        plate: newPlate,
        driver: newDriver,
        phone: newPhone
      };
    }

    // Generate change logs
    const changes = [];
    const fieldsToTrack = {
      client: '對象',
      destination: '指送地',
      product: '品名',
      expected_date: '預計到貨日期',
      arrival_time: '到貨時間',
      fill_hand: '充填手',
      plate: '車牌',
      driver: '司機',
      phone: '電話',
      departure_date: '出車日期',
      departure_time: '出車時間',
      driver_code: '司機代碼'
    };
    
    for (const [key, label] of Object.entries(fieldsToTrack)) {
      const oldVal = dbOrder[key] || '無';
      const newVal = db.orders[orderIndex][key] || '無';
      if (oldVal !== newVal) {
        changes.push(`${label}:「${oldVal}」→「${newVal}」`);
      }
    }
    const changeDetails = changes.join(', ') || '無欄位變動';
    addLog(db, operator, role, '手動編輯訂單', `修改訂單單號 ${dbOrder.id || '無'} / 指送地「${dbOrder.destination}」的內容：${changeDetails}`);

    // 偵測排程時間、日期、地點或充填手變更並發送即時推播
    const oldTime = dbOrder.arrival_time;
    const newTime = db.orders[orderIndex].arrival_time;
    const oldDate = dbOrder.expected_date;
    const newDate = db.orders[orderIndex].expected_date;
    const oldDest = dbOrder.destination;
    const newDest = db.orders[orderIndex].destination;
    const oldFill = dbOrder.fill_hand;
    const newFill = db.orders[orderIndex].fill_hand;

    const oldTech = (oldFill || '').split(/[\r\n\s]/)[0].trim();
    const newTech = (newFill || '').split(/[\r\n\s]/)[0].trim();

    // 1. 到貨時間、日期、指送地點或充填手異動：自動重設為「未讀」
    const hasScheduleChanged = (oldTime !== newTime || oldDate !== newDate || oldDest !== newDest || oldFill !== newFill);
    const orderKey = db.orders[orderIndex].id || `${newDest}_${newDate}_${newTime}`;

    if (hasScheduleChanged && newTech) {
      db.orders[orderIndex].read_status = 'unread';
      db.orders[orderIndex].read_at = null;
      db.orders[orderIndex].read_by = null;
      console.log(`[ReadStatus] 訂單【${newDest}】時間/內容異動，已重設為「未讀」等待技服同仁查閱`);
    }

    // 1. 到貨時間、日期或指送地點異動
    if (newTech && (oldTime !== newTime || oldDate !== newDate || oldDest !== newDest)) {
      const diffList = [];
      if (oldDate !== newDate) diffList.push(`日期：${oldDate || '無'} → ${newDate}`);
      if (oldTime !== newTime) diffList.push(`時間：${oldTime || '無'} → ${newTime}`);
      if (oldDest !== newDest) diffList.push(`地點：${oldDest || '無'} → ${newDest}`);

      sendPushNotificationToUser(newTech, {
        title: `⚠️ 【排程異動提醒】${newDest || '槽車排程'}`,
        body: `您負責的【${newDest} / ${db.orders[orderIndex].product || ''}】排程已變更：${diffList.join('，')}，請點擊確認！`,
        data: { url: `/?openOrder=${encodeURIComponent(orderKey)}`, orderKey: orderKey }
      }).catch(err => console.error('[WebPush] 異動推播失敗:', err));
    }

    // 2. 充填手更換 (移交給新同仁)
    if (newTech && oldTech && newTech !== oldTech) {
      sendPushNotificationToUser(oldTech, {
        title: `ℹ️ 【派工取消】任務已移交`,
        body: `您原負責的【${newDest} (${newDate} ${newTime})】已移交給 ${newTech}。`,
        data: { url: '/' }
      }).catch(err => console.error('[WebPush] 移交推播失敗:', err));

      sendPushNotificationToUser(newTech, {
        title: `📋 【新派工通知】勝一槽車充填`,
        body: `主管指派您負責【${newDest} / ${db.orders[orderIndex].product || ''}】到貨時間：${newDate} ${newTime}，請點擊確認！`,
        data: { url: `/?openOrder=${encodeURIComponent(orderKey)}`, orderKey: orderKey }
      }).catch(err => console.error('[WebPush] 派工推播失敗:', err));
    } else if (!oldTech && newTech) {
      sendPushNotificationToUser(newTech, {
        title: `📋 【新派工通知】勝一槽車充填`,
        body: `主管指派您負責【${newDest} / ${db.orders[orderIndex].product || ''}】到貨時間：${newDate} ${newTime}，請點擊確認！`,
        data: { url: `/?openOrder=${encodeURIComponent(orderKey)}`, orderKey: orderKey }
      }).catch(err => console.error('[WebPush] 派工推播失敗:', err));
    }

    saveDB(db);
    broadcastEvent('orders_changed', { order: db.orders[orderIndex] });
    res.json({ success: true, message: '訂單更新成功', order: db.orders[orderIndex] });
  } catch (err) {
    console.error(err);
    res.status(500).json({ success: false, message: `伺服器處理錯誤: ${err.message}` });
  }
});

// 9. Export Compiled Excel
app.get('/api/export', (req, res) => {
  try {
    const db = getDB();
    
    // Construct rows for "空白班表" sheet
    const headers = [
      "出貨通知單單別號",
      "批號",
      "對象簡稱",
      "指送地",
      "品名",
      "預計到貨日期",
      "到貨時間",
      "運輸方式",
      "趟次",            // I
      "車牌",            // J
      "司機",            // K
      "電話 ",           // L
      "出車日期",        // M
      "出車時間",        // N
      "景山司機代碼"     // O
    ];

    const data = [headers];
    db.orders.forEach(o => {
      data.push([
        o.id,
        o.batch,
        o.client,
        o.destination,
        o.product,
        o.expected_date,
        o.arrival_time,
        o.transport_type,
        o.fill_hand,       // 趟次 (I) 
        o.plate,           // 車牌 (J)
        o.driver,          // 司機 (K)
        o.phone,           // 電話 (L)
        o.departure_date,  // 出車日期 (M)
        o.departure_time,  // 出車時間 (N)
        o.driver_code ? Number(o.driver_code) || o.driver_code : null // 景山司機代碼 (O)
      ]);
    });

    const wb = xlsx.utils.book_new();
    const ws = xlsx.utils.aoa_to_sheet(data);
    xlsx.utils.book_append_sheet(wb, ws, "空白班表");

    // Add Driver List sheet if exists
    if (db.drivers && db.drivers.length > 0) {
      const driverHeaders = [null, "景山司機代碼", "車牌", "司機", "電話", "ID/身份證號碼"];
      const driverData = [driverHeaders];
      db.drivers.forEach(d => {
        driverData.push([
          null,
          Number(d.code) || d.code,
          d.plate,
          d.name,
          d.phone,
          d.id_card
        ]);
      });
      const dWs = xlsx.utils.aoa_to_sheet(driverData);
      xlsx.utils.book_append_sheet(wb, dWs, "司機清單");
    }

    const buffer = xlsx.write(wb, { type: 'buffer', bookType: 'xlsx' });
    res.setHeader('Content-Disposition', 'attachment; filename=compiled_schedule.xlsx');
    res.setHeader('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
    res.send(buffer);
  } catch (err) {
    console.error(err);
    res.status(500).json({ success: false, message: `匯出失敗: ${err.message}` });
  }
});

// GET Operation Logs API
app.get('/api/logs', (req, res) => {
  try {
    const db = getDB();
    res.json({ success: true, data: db.logs || [] });
  } catch (err) {
    res.status(500).json({ success: false, message: err.message });
  }
});


// TSMC 3-in-1 API
app.get('/api/orders/:id/tsmc-3in1', (req, res) => {
  try {
    const orderId = req.params.id;
    const db = getDB();
    let order = null;
    
    if (orderId.startsWith('batch:')) {
      const batch = orderId.replace('batch:', '');
      order = db.orders.find(o => o.batch === batch);
    } else {
      order = db.orders.find(o => o.id === orderId);
    }
    
    if (!order) return res.status(404).json({ success: false, message: '找不到訂單' });
    
    const { execFile } = require('child_process');
    const path = require('path');
    
    const destB64 = Buffer.from(order.destination || '').toString('base64');
    const pyScript = path.join(__dirname, 'generate_3in1.py');
    const batchNo = order.batch || '';
    execFile('python', [pyScript, batchNo, destB64], { timeout: 30000 }, (err, stdout, stderr) => {
      if (err) {
        console.error('3in1 error:', err.message);
        console.error('stderr:', stderr);
        return res.status(500).json({ success: false, message: '生成失敗: ' + (stderr || err.message) });
      }
      const outFile = stdout.trim();
      if (fs.existsSync(outFile)) {
        const db = getDB();
        addLog(db, 'system', 'system', '下載三合一單', `訂單 ${orderId}`);
        saveDB(db);
              // 檔名格式: 2026.8.29. 20P1_S382_台積電槽車barcode三合一單.xlsx
      let dateStr = "";
      if (order.expected_date) {
          let parts = order.expected_date.split('-');
          if (parts.length === 3) {
              dateStr = `${parseInt(parts[0], 10)}.${parseInt(parts[1], 10)}.${parseInt(parts[2], 10)}. `;
          }
      }

      let tankNo = "";
      if (order.batch) {
          let m = order.batch.match(/(S\d+)/i);
          if (m) tankNo = m[1].toUpperCase();
          else tankNo = order.batch;
      }

      let locShort = "";
      const locFile = require('path').join(__dirname, '地點代號對照表.xlsx');
      if (require('fs').existsSync(locFile)) {
          const xlsxLocal = require('xlsx');
          const wbLoc = xlsxLocal.readFile(locFile);
          const sheetLoc = wbLoc.Sheets[wbLoc.SheetNames[0]];
          const rows = xlsxLocal.utils.sheet_to_json(sheetLoc, { header: 1, range: 1 });
          const destUpper = (order.destination || '').toUpperCase();
          for (let r of rows) {
              const sn = String(r[0] || '').trim();
              const fn = String(r[1] || '').trim();
              if (sn && (destUpper === sn.toUpperCase() || destUpper === fn.toUpperCase() || destUpper.includes(sn.toUpperCase()))) {
                  locShort = sn;
                  break;
              }
          }
      }
      if (!locShort) {
          let match = (order.destination||'').match(/([A-Z0-9]+)$/i);
          if(match) locShort = match[1];
          else locShort = order.destination || '未知';
      }

      const finalFileName = `${dateStr}${locShort}_${tankNo}_台積電槽車barcode三合一單.xlsx`;
      res.download(outFile, finalFileName);
      } else {
        console.error('3in1 stdout was:', JSON.stringify(stdout));
        res.status(500).json({ success: false, message: '找不到生成的檔案' });
      }
    });

  } catch(e) {
    res.status(500).json({ success: false, message: e.message });
  }
});

// Location Mapping API — 3 columns: 送達地簡稱 | 送達地全名 | 送達地點代號
const LOCATION_MAPPING_FILE = path.join(__dirname, '地點代號對照表.xlsx');

app.get('/api/location-mappings', (req, res) => {
  try {
    if (!fs.existsSync(LOCATION_MAPPING_FILE)) {
      return res.json({ success: true, data: [] });
    }
    const wb = xlsx.readFile(LOCATION_MAPPING_FILE);
    const sheet = wb.Sheets[wb.SheetNames[0]];
    const rows = xlsx.utils.sheet_to_json(sheet, { header: 1, range: 1 }); // skip header row
    const data = rows
      .filter(r => r[0] || r[2])  // must have shortName or code
      .map(r => ({
        shortName: String(r[0] || '').trim(),
        fullName:  String(r[1] || '').trim(),
        code:      String(r[2] || '').trim(),
      }));
    res.json({ success: true, data });
  } catch (err) {
    res.status(500).json({ success: false, message: '讀取失敗: ' + err.message });
  }
});

app.post('/api/location-mappings', (req, res) => {
  try {
    const { mappings, operator, role } = req.body;
    const wb = xlsx.utils.book_new();
    const wsData = [['送達地簡稱', '送達地全名', '送達地點代號']];
    mappings.forEach(m => {
      if (m.shortName || m.code) {
        wsData.push([m.shortName || '', m.fullName || '', m.code || '']);
      }
    });
    const ws = xlsx.utils.aoa_to_sheet(wsData);
    xlsx.utils.book_append_sheet(wb, ws, '對照表');
    xlsx.writeFile(wb, LOCATION_MAPPING_FILE);

    const db = getDB();
    addLog(db, operator || '未知', role || 'admin', '更新地點對照表', `更新了 ${mappings.length} 筆資料`);
    saveDB(db);
    res.json({ success: true, message: '地點對照表更新成功' });
  } catch (err) {
    res.status(500).json({ success: false, message: '儲存失敗: ' + err.message });
  }
});



function getLocalIP() {
  const interfaces = os.networkInterfaces();
  for (const name of Object.keys(interfaces)) {
    for (const iface of interfaces[name]) {
      if (iface.family === 'IPv4' && !iface.internal) {
        return iface.address;
      }
    }
  }
  return 'localhost';
}

const localtunnel = require('localtunnel');

let currentTunnel = null;
async function startTunnel(port) {
  const TARGET_SUBDOMAIN = 'shinychem-ipahq';
  const EXPECTED_URL = `https://${TARGET_SUBDOMAIN}.loca.lt`;
  try {
    const tunnel = await localtunnel({ port, subdomain: TARGET_SUBDOMAIN });
    if (tunnel.url !== EXPECTED_URL) {
      console.warn(`[Tunnel] 未取得指定的固定網址 (伺服器暫時給予 ${tunnel.url})，釋放連線並於 8 秒後重試鎖定 ${EXPECTED_URL}...`);
      tunnel.close();
      setTimeout(() => startTunnel(port), 8000);
      return;
    }
    currentTunnel = tunnel;
    console.log(`  [外網固定網址] ${tunnel.url}`);
    console.log(`  [Tunnel 密碼] 118.232.17.163`);
    console.log('============================================================');

    tunnel.on('close', () => {
      console.warn('[Tunnel] 連線中斷，8 秒後自動重連以保持固定網址...');
      setTimeout(() => startTunnel(port), 8000);
    });
    tunnel.on('error', (err) => {
      console.warn('[Tunnel 警告]', err.message);
      try { tunnel.close(); } catch(e) {}
    });
  } catch (err) {
    console.warn(`[Tunnel 連線重試] ${err.message}，8 秒後自動重試...`);
    setTimeout(() => startTunnel(port), 8000);
  }
}

function startServer(port) {
  const server = app.listen(port, () => {
    const localIP = getLocalIP();
    console.log('============================================================');
    console.log('  勝一化工 - 槽車排程管理與即時推播系統');
    console.log('============================================================');
    console.log(`  [本機電腦] http://localhost:${port}`);
    console.log(`  [手機/區網] http://${localIP}:${port}`);
    if (!process.env.RENDER) {
      startTunnel(port);
    }
  });

  server.on('error', (err) => {
    if (err.code === 'EADDRINUSE') {
      console.warn(`[Port Fallback] 連接埠 ${port} 已被佔用，自動嘗試切換至 ${port + 1}...`);
      startServer(port + 1);
    } else {
      console.error('Server error:', err);
    }
  });
}

startServer(PORT);

// Render 24/7 保活防休眠機制 (每 10 分鐘自動發送心跳請求以重置 15 分鐘閒置計時器)
const RENDER_EXTERNAL_URL = process.env.RENDER_EXTERNAL_URL || 'https://google-agent-4gzi.onrender.com';
if (process.env.RENDER || process.env.NODE_ENV === 'production' || process.env.KEEP_ALIVE) {
  const https = require('https');
  console.log(`[KeepAlive] 已啟動防休眠機制，目標網址: ${RENDER_EXTERNAL_URL}`);
  setInterval(() => {
    try {
      https.get(`${RENDER_EXTERNAL_URL}/api/orders`, (res) => {
        console.log(`[KeepAlive] 伺服器保活心跳成功 (${res.statusCode}) - ${new Date().toLocaleTimeString('zh-TW', { timeZone: 'Asia/Taipei' })}`);
      }).on('error', (err) => {
        console.warn('[KeepAlive 警告] 心跳失敗:', err.message);
      });
    } catch (e) {
      console.warn('[KeepAlive 例外]', e.message);
    }
  }, 10 * 60 * 1000); // 每 10 分鐘發送一次
}
