-- 企業活動簽到系統 Cloudflare D1 資料表結構 (schema.sql)

CREATE TABLE IF NOT EXISTS event_settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS roster (
  emp_id TEXT PRIMARY KEY,
  dept TEXT NOT NULL,
  name TEXT NOT NULL,
  dependents_json TEXT DEFAULT '[]',
  checked_in INTEGER DEFAULT 0,
  arrived_dependents_json TEXT DEFAULT '[]',
  extra_count INTEGER DEFAULT 0,
  total_arrived INTEGER DEFAULT 0,
  checkin_time TEXT,
  seq INTEGER,
  verify_status TEXT DEFAULT 'verified',
  note TEXT DEFAULT '',
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS surveys (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  emp_id TEXT NOT NULL,
  name TEXT NOT NULL,
  dept TEXT NOT NULL,
  overall INTEGER DEFAULT 5,
  venue INTEGER DEFAULT 5,
  activity INTEGER DEFAULT 5,
  service INTEGER DEFAULT 5,
  favorites_json TEXT DEFAULT '[]',
  comment TEXT DEFAULT '',
  submitted_at TEXT NOT NULL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_roster_checked ON roster(checked_in);
CREATE INDEX IF NOT EXISTS idx_roster_dept ON roster(dept);
CREATE INDEX IF NOT EXISTS idx_surveys_submitted ON surveys(id DESC);
