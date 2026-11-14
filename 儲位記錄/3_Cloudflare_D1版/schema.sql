-- Cloudflare D1 Schema for 倉儲儲位 PWA 系統
CREATE TABLE IF NOT EXISTS locations (
  wh_id TEXT NOT NULL,
  location TEXT NOT NULL,
  zone TEXT NOT NULL DEFAULT '',
  item_no TEXT NOT NULL DEFAULT '',
  item_name TEXT NOT NULL DEFAULT '',
  lot_no TEXT NOT NULL DEFAULT '',
  package TEXT NOT NULL DEFAULT '',
  qty REAL NOT NULL DEFAULT 0,
  note TEXT NOT NULL DEFAULT '',
  updated_at TEXT NOT NULL DEFAULT (datetime('now')),
  PRIMARY KEY (wh_id, location)
);

CREATE TABLE IF NOT EXISTS daily_logs (
  id TEXT PRIMARY KEY,
  client_tx_id TEXT UNIQUE,
  log_date TEXT NOT NULL,
  log_time TEXT NOT NULL,
  wh_id TEXT NOT NULL,
  wh_name TEXT NOT NULL,
  zone TEXT NOT NULL DEFAULT '',
  location TEXT NOT NULL,
  action TEXT NOT NULL,
  item_no TEXT NOT NULL DEFAULT '',
  item_name TEXT NOT NULL DEFAULT '',
  lot_no TEXT NOT NULL DEFAULT '',
  package TEXT NOT NULL DEFAULT '',
  before_qty REAL NOT NULL DEFAULT 0,
  op_qty REAL NOT NULL DEFAULT 0,
  after_qty REAL NOT NULL DEFAULT 0,
  pallets INTEGER NOT NULL DEFAULT 1,
  note TEXT NOT NULL DEFAULT '',
  operator TEXT NOT NULL DEFAULT '現場人員'
);

CREATE INDEX IF NOT EXISTS idx_logs_date ON daily_logs(log_date);
CREATE INDEX IF NOT EXISTS idx_logs_lot ON daily_logs(lot_no);

CREATE TABLE IF NOT EXISTS warehouse_settings (
  wh_id TEXT PRIMARY KEY,
  items_json TEXT NOT NULL DEFAULT '[]',
  packages_json TEXT NOT NULL DEFAULT '[]',
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS users (
  username TEXT PRIMARY KEY,
  display_name TEXT NOT NULL,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'staff',
  enabled INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS warehouses (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  icon TEXT NOT NULL DEFAULT '🏬',
  sort_order INTEGER NOT NULL DEFAULT 10,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
