-- 鴻勝產銷動態計畫系統 - Cloudflare D1 Schema
CREATE TABLE IF NOT EXISTS _system_registry (
  system_id TEXT PRIMARY KEY,
  system_name TEXT NOT NULL,
  table_prefix TEXT NOT NULL,
  pages_url TEXT,
  updated_at TEXT NOT NULL
);

INSERT OR REPLACE INTO _system_registry (system_id, system_name, table_prefix, pages_url, updated_at)
VALUES ('sales-planner-pwa', '鴻勝產銷動態計畫系統', 'sp_', 'https://sales-planner-pwa.pages.dev', datetime('now'));

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
