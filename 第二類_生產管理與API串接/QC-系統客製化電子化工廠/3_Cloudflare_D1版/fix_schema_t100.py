path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\schema.sql'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

import re
old_t100 = """CREATE TABLE T100_Orders (
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
    createdAt DATETIME DEFAULT CURRENT_TIMESTAMP
);"""

new_t100 = """CREATE TABLE T100_Orders (
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
);"""

text = text.replace(old_t100, new_t100)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
