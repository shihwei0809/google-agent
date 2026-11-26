-- Cloudflare D1 SQLite Schema for SOP / WI 電子化檢點系統 (v1.0.0)
-- 共用主庫 (hs-material-report-db) + wi_* 表前綴隔離，嚴禁整表 DELETE+INSERT

CREATE TABLE IF NOT EXISTS wi_templates (
  id TEXT PRIMARY KEY,
  group_key TEXT NOT NULL,
  form_code TEXT NOT NULL,
  wi_version TEXT NOT NULL,
  is_latest INTEGER NOT NULL DEFAULT 1,
  payload_json TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_wi_templates_group_latest ON wi_templates(group_key, is_latest);

CREATE TABLE IF NOT EXISTS wi_records (
  id TEXT PRIMARY KEY,
  seq INTEGER,
  group_key TEXT NOT NULL,
  form_code TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  created_at TEXT NOT NULL,
  template_snapshot_json TEXT NOT NULL,
  meta_json TEXT NOT NULL,
  answers_json TEXT NOT NULL,
  signatures_json TEXT NOT NULL DEFAULT '{}',
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_wi_records_created ON wi_records(created_at DESC);

CREATE TABLE IF NOT EXISTS wi_saved_signatures (
  role TEXT PRIMARY KEY,
  role_label TEXT NOT NULL,
  name TEXT NOT NULL,
  pin TEXT NOT NULL DEFAULT '1234',
  data_url TEXT NOT NULL DEFAULT '',
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS wi_drafts (
  id TEXT PRIMARY KEY,
  group_key TEXT NOT NULL,
  plant TEXT NOT NULL DEFAULT '',
  payload_json TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_wi_drafts_updated ON wi_drafts(updated_at DESC);
