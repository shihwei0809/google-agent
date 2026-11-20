-- 鴻勝資材部｜季年報智慧分析系統 Cloudflare D1 Schema
CREATE TABLE IF NOT EXISTS monthly_metrics (
    ym TEXT NOT NULL,
    category TEXT NOT NULL,
    source TEXT NOT NULL,
    mt REAL,
    trips INTEGER,
    pallets INTEGER,
    rows_count INTEGER DEFAULT 0,
    breakdown_json TEXT DEFAULT '{}',
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (ym, category, source)
);

CREATE TABLE IF NOT EXISTS daily_management (
    id INTEGER PRIMARY KEY,
    period TEXT NOT NULL,
    date TEXT,
    type TEXT NOT NULL,
    content TEXT NOT NULL,
    status TEXT DEFAULT '記錄中'
);

CREATE TABLE IF NOT EXISTS key_projects (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    desc TEXT,
    effect TEXT,
    eta TEXT,
    status TEXT DEFAULT '進行中'
);

CREATE INDEX IF NOT EXISTS idx_metrics_ym ON monthly_metrics (ym);
CREATE INDEX IF NOT EXISTS idx_mgmt_period ON daily_management (period);
