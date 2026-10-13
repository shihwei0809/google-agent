-- 回收液入料記錄資料表
CREATE TABLE IF NOT EXISTS recycle_records (
    id TEXT PRIMARY KEY,
    date TEXT NOT NULL,
    license_plate TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending', -- pending | completed
    t_before_url TEXT,
    v_photo_url TEXT,
    t_after_url TEXT,
    before_time TEXT,
    after_time TEXT,
    duration INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_recycle_status ON recycle_records(status);
CREATE INDEX IF NOT EXISTS idx_recycle_date ON recycle_records(date);
