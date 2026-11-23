-- Local SQLite Schema for FastAPI PWA server
CREATE TABLE IF NOT EXISTS sp_plan_state (
  id TEXT PRIMARY KEY,
  plan_json TEXT NOT NULL,
  version INTEGER NOT NULL DEFAULT 1,
  updated_by TEXT DEFAULT '系統',
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sp_plan_archives (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  description TEXT DEFAULT '',
  plan_json TEXT NOT NULL,
  created_by TEXT DEFAULT '系統',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sp_change_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  action TEXT NOT NULL,
  actor TEXT NOT NULL,
  summary TEXT NOT NULL,
  created_at TEXT NOT NULL
);
