const express = require('express');
const mysql = require('mysql2/promise');
const cors = require('cors');
require('dotenv').config();

const app = express();
app.use(cors());
app.use(express.json());

const PORT = process.env.PORT || 3000;

// 資料庫連接池與自動初始化
let pool;
async function initDb() {
  const host = process.env.DB_HOST || '127.0.0.1';
  const user = process.env.DB_USER || 'root';
  const password = process.env.DB_PASSWORD || '';
  const port = parseInt(process.env.DB_PORT || '3306');
  const database = process.env.DB_NAME || 'barcode_db';

  try {
    // 1. 先連接到 MySQL 伺服器本身 (不指定資料庫)，以便檢查與建立資料庫
    const tempConnection = await mysql.createConnection({
      host,
      user,
      password,
      port
    });

    console.log('🔄 正在檢查/建立資料庫...');
    await tempConnection.query(`CREATE DATABASE IF NOT EXISTS \`${database}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;`);
    await tempConnection.end();

    // 2. 初始化連接池 (指定資料庫)
    pool = mysql.createPool({
      host,
      user,
      password,
      database,
      port,
      waitForConnections: true,
      connectionLimit: 10,
      queueLimit: 0,
      enableKeepAlive: true,
      keepAliveInitialDelay: 0
    });
    
    // 3. 測試連線並自動建立資料表
    const conn = await pool.getConnection();
    console.log('✅ 成功連接到 MySQL 資料庫');
    
    console.log('🔄 正在檢查/建立資料表...');
    const createTableSql = `
      CREATE TABLE IF NOT EXISTS barcode_shipments (
        id INT AUTO_INCREMENT PRIMARY KEY,
        mode VARCHAR(50) NOT NULL COMMENT '出貨模式 (ship_full, ship_mixed, ship_loose, ship_az)',
        location VARCHAR(100) NOT NULL COMMENT '場所 (彰濱一廠, 彰濱二廠)',
        f0 VARCHAR(100) DEFAULT '',
        f1 VARCHAR(100) DEFAULT '',
        f2 VARCHAR(100) DEFAULT '',
        f3 VARCHAR(100) DEFAULT '',
        f4 VARCHAR(100) DEFAULT '',
        f5 VARCHAR(100) DEFAULT '',
        f6 VARCHAR(100) DEFAULT '',
        f7 VARCHAR(100) DEFAULT '',
        f8 VARCHAR(100) DEFAULT '',
        f9 VARCHAR(100) DEFAULT '',
        f10 VARCHAR(100) DEFAULT '',
        f11 VARCHAR(100) DEFAULT '',
        f12 VARCHAR(100) DEFAULT '',
        f13 VARCHAR(100) DEFAULT '',
        f14 VARCHAR(100) DEFAULT '',
        f15 VARCHAR(100) DEFAULT '',
        f16 VARCHAR(100) DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '同步寫入時間'
      ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    `;
    await conn.query(createTableSql);
    console.log('✅ 資料表驗證/建立完成');
    conn.release();
  } catch (error) {
    console.error('❌ 資料庫初始化或連接失敗，請確認 XAMPP / MySQL 是否已啟動：', error.message);
    process.exit(1);
  }
}

// 接收同步資料 API
app.post('/api/shipments/sync', async (req, res) => {
  console.log(`[${new Date().toISOString()}] 📥 收到同步請求`);
  
  try {
    let data = req.body;
    
    // 相容性處理：若收到的資料是用 GAS 外層包裝格式 {"barcode": "內部JSON字串"}
    if (data.barcode && typeof data.barcode === 'string') {
      try {
        data = JSON.parse(data.barcode);
      } catch (e) {
        console.error('⚠️ 無法解析包裹的 barcode JSON 字串，使用原始 body:', e.message);
      }
    }
    
    const fields = data.fields;
    const mode = data.mode;
    const location = data.location;
    
    if (!fields || !Array.isArray(fields)) {
      console.warn('⚠️ 請求格式錯誤：缺少 fields 陣列');
      return res.status(400).json({
        status: 'error',
        message: '格式錯誤：缺少 fields 陣列'
      });
    }
    
    // 確保有 17 個欄位 (補空字串)
    const paddedFields = Array(17).fill('');
    for (let i = 0; i < Math.min(fields.length, 17); i++) {
      paddedFields[i] = (fields[i] !== null && fields[i] !== undefined) ? String(fields[i]).trim() : '';
    }
    
    // 插入資料庫 SQL
    const sql = `
      INSERT INTO barcode_shipments (
        mode, location, 
        f0, f1, f2, f3, f4, f5, f6, f7, f8, f9, f10, f11, f12, f13, f14, f15, f16
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `;
    
    const params = [
      mode || '',
      location || '',
      ...paddedFields
    ];
    
    const [result] = await pool.execute(sql, params);
    console.log(`✅ 資料成功寫入資料庫，新增 ID: ${result.insertId}`);
    
    return res.status(200).json({
      status: 'success',
      message: '同步成功',
      insertId: result.insertId
    });
    
  } catch (error) {
    console.error('❌ 寫入資料庫時發生錯誤:', error);
    return res.status(500).json({
      status: 'error',
      message: `伺服器內部錯誤: ${error.message}`
    });
  }
});

// 健康檢查端點
app.get('/health', (req, res) => {
  res.json({ status: 'ok', time: new Date() });
});

// 啟動伺服器
initDb().then(() => {
  app.listen(PORT, '0.0.0.0', () => {
    console.log(`🚀 API 伺服器正在運行於 http://localhost:${PORT}`);
    console.log(`📡 同步端點 API: http://localhost:${PORT}/api/shipments/sync`);
  });
});
