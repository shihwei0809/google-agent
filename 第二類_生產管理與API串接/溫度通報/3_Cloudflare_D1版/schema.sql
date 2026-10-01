-- schema.sql: 溫度通報系統 D1 資料庫結構

DROP TABLE IF EXISTS config;
CREATE TABLE config (
    id TEXT PRIMARY KEY,
    key TEXT UNIQUE NOT NULL,
    value TEXT NOT NULL,
    description TEXT
);

-- 寫入預設設定
INSERT INTO config (id, key, value, description) VALUES
('cwa_api_key', 'cwa_api_key', 'CWA-718BCC42-A79F-4138-99BC-81D9C317BE28', '氣象署 API Key'),
('cwa_station_id', 'cwa_station_id', 'C2G870', '氣象站代號 (預設: 彰化西鄉)'),
('threshold', 'threshold', '29.0', '高溫警報閾值 (°C)'),
('start_hour', 'start_hour', '0', '監控起始時間 (0-24)'),
('end_hour', 'end_hour', '24', '監控結束時間 (0-24)'),
('line_notify_token', 'line_notify_token', '', 'LINE Notify 權杖 (以逗號分隔多組)');

DROP TABLE IF EXISTS temperature_logs;
CREATE TABLE temperature_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    temperature REAL NOT NULL,
    obs_time TEXT NOT NULL,
    status TEXT NOT NULL
);

DROP TABLE IF EXISTS alert_logs;
CREATE TABLE alert_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    threshold REAL NOT NULL,
    temperature REAL NOT NULL,
    obs_time TEXT NOT NULL,
    alert_state TEXT NOT NULL,
    status_text TEXT NOT NULL
);
