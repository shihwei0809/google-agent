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
    round INTEGER DEFAULT 1,
    remark TEXT
);

DROP TABLE IF EXISTS T100_Orders;
CREATE TABLE T100_Orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_no TEXT,
    flowType TEXT,
    productName TEXT,
    tankNo TEXT,
    container TEXT,
    quantity TEXT,
    customer TEXT,
    grade TEXT,
    targetDate TEXT,
    date TEXT,
    time TEXT,
    note TEXT,
    createdAt DATETIME DEFAULT CURRENT_TIMESTAMP
);

DROP TABLE IF EXISTS Employees;
CREATE TABLE Employees (
    emp_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    department TEXT
);



﻿INSERT OR IGNORE INTO Employees (emp_id, name) VALUES 
('C0606', '陳世偉'),
('C0663', '陳彥志'),
('C0704', '黃俊翰'),
('C0768', '黃宏吉'),
('C0770', '張立杰'),
('C0588', '郭育綾'),
('C0664', '黃玟寧'),
('C0723', '趙令融'),
('C0926', '王莠婷'),
('C0589', '辛俊宏'),
('C0605', '莊世民'),
('C0614', '洪源松'),
('C0676', '鄭健利'),
('C0683', '蔡孟賢'),
('C0718', '楊溢銜'),
('C0731', '許原暢'),
('C0735', '梁聖國'),
('C0736', '林佳隆'),
('C0761', '涂敬宗'),
('C0765', '吳皓楷'),
('C0769', '陳志修'),
('C0800', '黃俊源'),
('C0810', '林東和'),
('C0818', '黃崇恩'),
('C0854', '江承河'),
('C0861', '林家宏'),
('C0865', '陳志弘'),
('C0885', '蘇明宏'),
('C0895', '鄧博文'),
('C0896', '邱建霖'),
('C0905', '黃振榮'),
('C0909', '張韋勝'),
('C0615', '辛俊杉'),
('C0670', '盧銘傑'),
('C0590', '黃坦意'),
('C0637', '紀睿展'),
('C0644', '詹鎧鍵'),
('C0672', '黃信銘'),
('C0779', '莊峯弦'),
('C0834', '林小平'),
('C0850', '黃嘉慶'),
('C0851', '陳培瑋'),
('C0877', '林峻民'),
('C0880', '許文豪'),
('C0884', '董烱輝'),
('C0892', '周奕承'),
('C0899', '林冠霆'),
('C0902', '黃弘名'),
('C0918', '劉嘉憲'),
('C0924', '楊濬陽'),
('C0699', '林佳宏'),
('C0623', '黃衍順'),
('C0632', '楊騰方'),
('C0642', '楊淑玲'),
('C0650', '吳青山'),
('C0693', '陳志雄'),
('C0696', '莊勝淵'),
('C0712', '林雨霖'),
('C0726', '粘淳淼'),
('C0752', '陳盈守'),
('C0760', '林建豪'),
('C0763', '黃柏程'),
('C0781', '林裕峰'),
('C0784', '邱振皓'),
('C0795', '陳正育'),
('C0796', '張宥騰'),
('C0801', '林東昇'),
('C0807', '廖啓貿'),
('C0812', '蕭耀琳'),
('C0822', '洪宗寶'),
('C0838', '謝承洧'),
('C0901', '鍾宏達'),
('C0906', '邱信凱');
