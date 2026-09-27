path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\schema.sql'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

import re
text = re.sub(
    r'DROP TABLE IF EXISTS Orders;.*?CREATE TABLE Orders \(.*?\);',
    '''DROP TABLE IF EXISTS T100_Orders;
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
    createdAt DATETIME DEFAULT CURRENT_TIMESTAMP
);''',
    text,
    flags=re.DOTALL
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
