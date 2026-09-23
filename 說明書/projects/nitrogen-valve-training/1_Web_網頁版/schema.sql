DROP TABLE IF EXISTS exam_records;
CREATE TABLE exam_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    name TEXT,
    score INTEGER,
    correctCount INTEGER,
    total INTEGER,
    q1 TEXT,
    q2 TEXT,
    q3 TEXT,
    q4 TEXT,
    q5 TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
