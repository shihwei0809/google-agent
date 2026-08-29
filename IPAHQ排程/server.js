const express = require('express');
const multer = require('multer');
const xlsx = require('xlsx');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

const DB_FILE = path.join(__dirname, 'database.json');
const upload = multer({ storage: multer.memoryStorage() });

const DEFAULT_USERS = [
  { username: 'sales', password: '123', role: 'sales', displayName: '業務人員' },
  { username: 'tech_mgr', password: '123', role: 'tech_manager', displayName: '技服主管' },
  { username: 'transporter', password: '123', role: 'transporter', displayName: '運輸公司' },
  { username: '林聖龍', password: '123', role: 'tech_staff', displayName: '林聖龍' },
  { username: '楊立凱', password: '123', role: 'tech_staff', displayName: '楊立凱' },
  { username: '胡富閔', password: '123', role: 'tech_staff', displayName: '胡富閔' },
  { username: '陳國安', password: '123', role: 'tech_staff', displayName: '陳國安' },
  { username: '陳俊佑', password: '123', role: 'tech_staff', displayName: '陳俊佑' },
  { username: '陳志彥', password: '123', role: 'tech_staff', displayName: '陳志彥' },
  { username: '陳志源', password: '123', role: 'tech_staff', displayName: '陳志源' },
  { username: '廖家民', password: '123', role: 'tech_staff', displayName: '廖家民' },
  { username: '蘇昭溢', password: '123', role: 'tech_staff', displayName: '蘇昭溢' },
  { username: '王善禾', password: '123', role: 'tech_staff', displayName: '王善禾' }
];

const USER_EXCEL_FILE = path.join(__dirname, '帳號密碼管理.xlsx');

function loadUsersFromExcel() {
  if (!fs.existsSync(USER_EXCEL_FILE)) return null;
  try {
    const workbook = xlsx.readFile(USER_EXCEL_FILE);
    const sheet = workbook.Sheets[workbook.SheetNames[0]];
    const config = {
      username: 'A',
      password: 'B',
      role: 'C',
      displayName: 'D'
    };
    
    // Note: parseSheetByColumns is defined below, but we can call it here as long as it's defined in scope.
    // However, function declarations are hoisted in JS, so it's perfectly safe to call it here!
    const rows = parseSheetByColumns(sheet, 2, config);
    const users = rows
      .filter(r => r.username && r.password && r.role)
      .map(r => ({
        username: String(r.username).trim(),
        password: String(r.password).trim(),
        role: String(r.role).trim(),
        displayName: r.displayName ? String(r.displayName).trim() : String(r.username).trim()
      }));
      
    if (users.length > 0) {
      return users;
    }
  } catch (err) {
    console.error('Error loading users from Excel:', err);
  }
  return null;
}

const DRIVER_EXCEL_FILE = path.join(__dirname, '司機名冊管理.xlsx');

function loadDriversFromExcel() {
  if (!fs.existsSync(DRIVER_EXCEL_FILE)) return null;
  try {
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
      return drivers;
    }
  } catch (err) {
    console.error('Error loading drivers from Excel:', err);
  }
  return null;
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
  let db = { orders: [], drivers: [], users: DEFAULT_USERS };
  
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
    
    return db;
  } catch (err) {
    const excelUsers = loadUsersFromExcel();
    const excelDrivers = loadDriversFromExcel();
    return { orders: [], drivers: excelDrivers || [], users: excelUsers || DEFAULT_USERS };
  }
}

function saveDB(db) {
  fs.writeFileSync(DB_FILE, JSON.stringify(db, null, 2), 'utf-8');
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

// 1. Get all orders
app.get('/api/orders', (req, res) => {
  const db = getDB();
  res.json({ success: true, data: db.orders });
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
    addLog(db, user.username, user.role, '使用者登入', '登入成功');
    saveDB(db);
    res.json({
      success: true,
      user: {
        username: user.username,
        role: user.role,
        displayName: user.displayName
      }
    });
  } else {
    addLog(db, username || '未知使用者', 'unknown', '使用者登入', '登入失敗 (密碼錯誤或帳號不存在)');
    saveDB(db);
    res.status(401).json({ success: false, message: '帳號或密碼錯誤！' });
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
        updatedCount++;
      }
    });

    addLog(db, operator || '未知使用者', role || 'tech_manager', '匯入技服充填手', `成功比對更新了 ${updatedCount} 筆充填手資料`);
    saveDB(db);
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
    const dbOrder = db.orders[orderIndex];
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

    saveDB(db);
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



app.listen(PORT, () => {
  console.log(`Server is running at http://localhost:${PORT}`);
});
