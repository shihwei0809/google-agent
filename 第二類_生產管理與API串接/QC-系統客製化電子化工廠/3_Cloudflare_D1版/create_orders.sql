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
    createdAt DATETIME DEFAULT CURRENT_TIMESTAMP
);
