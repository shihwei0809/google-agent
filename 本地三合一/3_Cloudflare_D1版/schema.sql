-- D1 Database Schema for TSMC Verification System
DROP TABLE IF EXISTS verifications;
CREATE TABLE verifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    material_no TEXT,
    tank_no TEXT,
    batch_no TEXT,
    supplier TEXT,
    original_location TEXT,
    target_location TEXT,
    raw_qr TEXT,
    status TEXT,
    photo_batch_url TEXT,
    photo_loc_url TEXT,
    source_order TEXT,
    doc_order TEXT
);

CREATE INDEX idx_verifications_created_at ON verifications(created_at);
CREATE INDEX idx_verifications_batch_no ON verifications(batch_no);
