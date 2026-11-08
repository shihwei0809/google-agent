-- Cloudflare D1 資料表結構：三合一單與 COA 四重核對系統
-- 檔案：schema.sql

-- 1. 核對紀錄主表
CREATE TABLE IF NOT EXISTS coa_verification_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    material_no TEXT,
    tank_no TEXT,
    batch_no TEXT,
    supplier TEXT,
    delivery_place TEXT,
    raw_qr TEXT,
    source_doc_no TEXT,
    weighbridge_no TEXT,
    verification_status TEXT NOT NULL, -- '四重核對成功' 或 '核對失敗'
    photo_batch_url TEXT,              -- R2 COA 照片 URL (例如 /api/photos/coa-photos/202611/Batch_xxx.jpg)
    photo_loc_url TEXT,                -- R2 地磅照片 URL (例如 /api/photos/coa-photos/202611/Loc_xxx.jpg)
    error_details TEXT,                -- 失敗原因或詳細報告
    ocr_snippet TEXT,                  -- OCR 辨識字串節錄
    created_at DATETIME DEFAULT (datetime('now', '+8 hours'))
);

CREATE INDEX IF NOT EXISTS idx_logs_batch_no ON coa_verification_logs (batch_no);
CREATE INDEX IF NOT EXISTS idx_logs_material_no ON coa_verification_logs (material_no);
CREATE INDEX IF NOT EXISTS idx_logs_created_at ON coa_verification_logs (created_at);

-- 2. 系統動態設定表 (免改代碼即可調整 Webhook 與金鑰)
CREATE TABLE IF NOT EXISTS system_config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT
);

INSERT OR IGNORE INTO system_config (key, value, description) VALUES
('VISION_API_KEY_1', 'AIzaSyCxpDwmsFfKtYkz-_rnqPJW_iVh5j-wQd4', '主力 Google Vision OCR 金鑰'),
('VISION_API_KEY_2', 'AIzaSyCdI7WZKnyUtYL0mubKslz7Cvq2wqStS_8', '備用 Google Vision OCR 金鑰'),
('TEAMS_WEBHOOK_URL', 'https://defaulta46d9e33ad01451aaec52ee61979c6.d0.environment.api.powerplatform.com:443/powerautomate/automations/direct/cu/22/workflows/91b9b15b99a64990bf3f7116c031dea4/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=huhEyZ8m-m8EKJ7JXRmhR-CtuVI83kTLRADHB12g-7k', 'Teams 工作流程通知 Webhook'),
('ENABLE_TEAMS_ON_SUCCESS', 'false', '核對成功是否也推播 Teams (true/false)'),
('ENABLE_TEAMS_ON_FAILURE', 'true', '核對失敗是否推播 Teams 警報卡片 (true/false)');

-- 3. API 呼叫日誌 (記錄流量與狀態)
CREATE TABLE IF NOT EXISTS api_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_type TEXT NOT NULL,
    model_name TEXT,
    key_snippet TEXT,
    status TEXT NOT NULL,
    note TEXT,
    created_at DATETIME DEFAULT (datetime('now', '+8 hours'))
);
