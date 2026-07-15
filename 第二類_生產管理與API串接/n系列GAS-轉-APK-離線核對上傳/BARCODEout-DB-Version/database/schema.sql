-- 建立資料庫 (若不存在)
CREATE DATABASE IF NOT EXISTS barcode_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE barcode_db;

-- 建立出貨/巡檢核對紀錄資料表
CREATE TABLE IF NOT EXISTS barcode_shipments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    mode VARCHAR(50) NOT NULL COMMENT '出貨模式 (ship_full, ship_mixed, ship_loose, ship_az)',
    location VARCHAR(100) NOT NULL COMMENT '場所 (彰濱一廠, 彰濱二廠)',
    -- 17 個條碼欄位 (f0 ~ f16)
    f0 VARCHAR(100) DEFAULT '' COMMENT '桶數條碼 1 / 其他條碼',
    f1 VARCHAR(100) DEFAULT '' COMMENT '四合一條碼 1 / 其他條碼',
    f2 VARCHAR(100) DEFAULT '' COMMENT '庫位條碼 1 / 其他條碼',
    f3 VARCHAR(100) DEFAULT '' COMMENT '桶數條碼 2 / 其他條碼',
    f4 VARCHAR(100) DEFAULT '' COMMENT '四合一條碼 2 / 其他條碼',
    f5 VARCHAR(100) DEFAULT '' COMMENT '庫位條碼 2 / 其他條碼',
    f6 VARCHAR(100) DEFAULT '' COMMENT '桶數條碼 3 / 其他條碼',
    f7 VARCHAR(100) DEFAULT '' COMMENT '四合一條碼 3 / 其他條碼',
    f8 VARCHAR(100) DEFAULT '' COMMENT '四合一料號 / 其他條碼',
    f9 VARCHAR(100) DEFAULT '' COMMENT '桶數條碼 4 / 其他條碼',
    f10 VARCHAR(100) DEFAULT '' COMMENT '四合一條碼 4 / 其他條碼',
    f11 VARCHAR(100) DEFAULT '' COMMENT '庫位條碼 4 / 其他條碼',
    f12 VARCHAR(100) DEFAULT '' COMMENT '庫位條碼 3 / 其他條碼',
    f13 VARCHAR(100) DEFAULT '' COMMENT '繳庫單號',
    f14 VARCHAR(100) DEFAULT '' COMMENT '繳庫-批號1',
    f15 VARCHAR(100) DEFAULT '' COMMENT '繳庫-批號2',
    f16 VARCHAR(100) DEFAULT '' COMMENT '繳庫-批號3',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '同步寫入時間'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
