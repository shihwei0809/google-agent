DROP TABLE IF EXISTS System_Config;
CREATE TABLE System_Config (
    config_key TEXT PRIMARY KEY,
    config_value TEXT
);

INSERT INTO System_Config (config_key, config_value) VALUES
('QC_PIN', '8888'),
('TEAMS_MANAGER_WEBHOOK', ''),
('TEAMS_WEBHOOK_資材課', ''),
('TEAMS_WEBHOOK_二部一課', ''),
('TEAMS_WEBHOOK_二部二課', ''),
('TEAMS_WEBHOOK_一部一課', ''),
('TEAMS_WEBHOOK_一部二課', ''),
('PWA_URL', 'https://google-agent.pages.dev/qc-system'),
('OPTIONS_FLOW_TYPES', '出貨, 進料, 補料, 委託'),
('OPTIONS_GRADES', '工業級, 電子級, IF'),
('OPTIONS_DEPTS', '資材課, 二部一課, 二部二課, 一部一課, 一部二課'),
('OPTIONS_PRODUCTS', 'IPA, IPAUPS, IPAHQ, CPNE3(T), CPNE4, CPN-P1R, EBR, EBR-P1R, NBAC, NBAC-P1R, CPN, EG, NMP, GAA, ACT, PM, PMA98, heavy-R, DPM, DPM-B1, SEP73, Anone, GBL, PG, EBRR');

DROP TABLE IF EXISTS Accounts;
CREATE TABLE Accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'admin',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO Accounts (username, password_hash, role) VALUES ('admin', 'admin123', 'admin');

DROP TABLE IF EXISTS QC_Samples;
CREATE TABLE QC_Samples (
    id TEXT PRIMARY KEY,
    barcode TEXT,
    productName TEXT,
    tankNo TEXT,
    customer TEXT,
    quantity TEXT,
    flowType TEXT,
    dept TEXT,
    requester TEXT,
    grade TEXT,
    qcResult TEXT,
    createdAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    completedAt DATETIME,
    status TEXT,
    qcNote TEXT,
    qcApprover TEXT,
    isAlerted INTEGER DEFAULT 0,
    parentId TEXT,
    round INTEGER DEFAULT 1
);

DROP TABLE IF EXISTS Orders;
CREATE TABLE Orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_date TEXT,
    flowType TEXT,
    productName TEXT,
    tankNo TEXT,
    customer TEXT,
    quantity TEXT,
    createdAt DATETIME DEFAULT CURRENT_TIMESTAMP
);

DROP TABLE IF EXISTS Employees;
CREATE TABLE Employees (
    emp_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    department TEXT
);

