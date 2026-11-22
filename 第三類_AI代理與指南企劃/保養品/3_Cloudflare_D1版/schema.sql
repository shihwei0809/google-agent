-- ============================================================
-- AI個人保養網站 V8 (Cloudflare Pages + D1 + DeepSeek R1/Gemini)
-- 共用資料庫：weather-monitor-db (521c2592-1953-42a3-a559-bd403c8d3017)
-- 所有資料表皆加上 sk_ 前綴以 100% 隔離防撞
-- ============================================================

CREATE TABLE IF NOT EXISTS _system_registry (
    system_code TEXT NOT NULL,
    system_name TEXT NOT NULL,
    table_name TEXT NOT NULL PRIMARY KEY,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
INSERT OR REPLACE INTO _system_registry (system_code, system_name, table_name, description) VALUES ('weather_monitor', '溫度通報系統', 'config', '溫度通報系統設定');
INSERT OR REPLACE INTO _system_registry (system_code, system_name, table_name, description) VALUES ('weather_monitor', '溫度通報系統', 'temperature_logs', '溫度監測歷史紀錄');
INSERT OR REPLACE INTO _system_registry (system_code, system_name, table_name, description) VALUES ('weather_monitor', '溫度通報系統', 'alert_logs', '高溫/異常通報紀錄');
INSERT OR REPLACE INTO _system_registry (system_code, system_name, table_name, description) VALUES ('weather_monitor', '溫度通報系統', 'materials', '物料資料表');
INSERT OR REPLACE INTO _system_registry (system_code, system_name, table_name, description) VALUES ('weather_monitor', '溫度通報系統', 'chat_logs', '對話/AI紀錄');
INSERT OR REPLACE INTO _system_registry (system_code, system_name, table_name, description) VALUES ('training', '教育訓練教材與測驗', 'nitrogen_valve_exam_records', '氮氣閥門教育訓練測驗紀錄');
INSERT OR REPLACE INTO _system_registry (system_code, system_name, table_name, description) VALUES ('skincare', 'AI個人保養品系統V8', 'sk_users', '使用者帳號與4位數PIN碼');
INSERT OR REPLACE INTO _system_registry (system_code, system_name, table_name, description) VALUES ('skincare', 'AI個人保養品系統V8', 'sk_summary', '膚況摘要與緊急警告');
INSERT OR REPLACE INTO _system_registry (system_code, system_name, table_name, description) VALUES ('skincare', 'AI個人保養品系統V8', 'sk_products', '保養品庫存與適合度清單');
INSERT OR REPLACE INTO _system_registry (system_code, system_name, table_name, description) VALUES ('skincare', 'AI個人保養品系統V8', 'sk_instructions', '各產品建議用量與使用方法');
INSERT OR REPLACE INTO _system_registry (system_code, system_name, table_name, description) VALUES ('skincare', 'AI個人保養品系統V8', 'sk_routines', '早晚與急救保養流程');
INSERT OR REPLACE INTO _system_registry (system_code, system_name, table_name, description) VALUES ('skincare', 'AI個人保養品系統V8', 'sk_sunscreens', '防曬品排行評分比較');
INSERT OR REPLACE INTO _system_registry (system_code, system_name, table_name, description) VALUES ('skincare', 'AI個人保養品系統V8', 'sk_avoid_rules', '保養避雷禁忌規則');
INSERT OR REPLACE INTO _system_registry (system_code, system_name, table_name, description) VALUES ('skincare', 'AI個人保養品系統V8', 'sk_dupes', '高CP值平替清單');
INSERT OR REPLACE INTO _system_registry (system_code, system_name, table_name, description) VALUES ('skincare', 'AI個人保養品系統V8', 'sk_checklist', '每日打勾任務雲端狀態');
INSERT OR REPLACE INTO _system_registry (system_code, system_name, table_name, description) VALUES ('skincare', 'AI個人保養品系統V8', 'sk_config', '保養系統設定參數');
INSERT OR REPLACE INTO _system_registry (system_code, system_name, table_name, description) VALUES ('system', '全域防忘登記表', '_system_registry', '記錄此共用D1內所有系統與資料表歸屬');

CREATE TABLE IF NOT EXISTS sk_users (
    username TEXT PRIMARY KEY,
    pin TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
INSERT OR IGNORE INTO sk_users (username, pin) VALUES ('shihwei', '1234');

CREATE TABLE IF NOT EXISTS sk_summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    content TEXT NOT NULL,
    username TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sk_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product TEXT NOT NULL,
    status TEXT NOT NULL,
    description TEXT,
    image_data TEXT DEFAULT '',
    username TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sk_instructions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product TEXT NOT NULL,
    dosage TEXT,
    usage_method TEXT,
    interval_time TEXT,
    attention TEXT,
    username TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sk_routines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    time_of_day TEXT NOT NULL,
    flow TEXT NOT NULL,
    username TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sk_sunscreens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rank TEXT NOT NULL,
    product TEXT NOT NULL,
    score TEXT NOT NULL,
    position TEXT NOT NULL,
    recommendation TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sk_avoid_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    do_not TEXT NOT NULL,
    reason TEXT NOT NULL,
    correct_way TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sk_dupes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_product TEXT NOT NULL,
    dupe_product TEXT NOT NULL,
    category TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sk_checklist (
    username TEXT NOT NULL,
    step_key TEXT NOT NULL,
    value INTEGER NOT NULL DEFAULT 0,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (username, step_key)
);

CREATE TABLE IF NOT EXISTS sk_config (
    config_key TEXT PRIMARY KEY,
    config_val TEXT NOT NULL
);
INSERT OR REPLACE INTO sk_config (config_key, config_val) VALUES ('AI_DEFAULT_ENGINE', 'deepseek-r1');
INSERT OR REPLACE INTO sk_config (config_key, config_val) VALUES ('GEMINI_MODEL', 'gemini-3.8-flash');

DELETE FROM sk_summary WHERE username = 'shihwei';
INSERT INTO sk_summary (category, content, username) VALUES ('目前皮膚狀態', '外油內乾、醫生提醒臉太乾、皮秒術後需修護、防曬與降低刺激優先。', 'shihwei');
INSERT INTO sk_summary (category, content, username) VALUES ('緊急警告', '乾、刺、脫皮、泛紅時：白黃橘瓶、A醛、酸類、泥膜、水楊酸洗面膜全部暫停。', 'shihwei');
INSERT INTO sk_summary (category, content, username) VALUES ('主力步驟', '雅漾或SD噴霧 → 神經醯胺 → 玻尿酸 → SD能量霜 → 主力臉部防曬。', 'shihwei');
INSERT INTO sk_summary (category, content, username) VALUES ('功效型恢復順序', '白瓶G → 橘瓶PV / Celladix 131 → 黃瓶V / A醛 → 酸類與清潔面膜。', 'shihwei');
DELETE FROM sk_products WHERE username = 'shihwei';
INSERT INTO sk_products (product, status, description, username) VALUES ('雅漾活泉水', '非常適合', '舒緩、降溫、降低緊繃，可取代SD噴霧。', 'shihwei');
INSERT INTO sk_products (product, status, description, username) VALUES ('SD噴霧', '適合', '洗臉後、臉熱、緊繃時使用。', 'shihwei');
INSERT INTO sk_products (product, status, description, username) VALUES ('SD舒緩精華', '適合', '主力修護精華。', 'shihwei');
INSERT INTO sk_products (product, status, description, username) VALUES ('SD能量霜', '適合', '鎖水修護，T字薄擦。', 'shihwei');
INSERT INTO sk_products (product, status, description, username) VALUES ('神經醯胺精華 1%', '非常適合', '屏障修護核心產品。', 'shihwei');
INSERT INTO sk_products (product, status, description, username) VALUES ('1%玻尿酸', '適合但要鎖水', '後面一定要接乳霜。', 'shihwei');
INSERT INTO sk_products (product, status, description, username) VALUES ('Celladix 131', '穩定後再用', '控油、毛孔、皮脂平衡。', 'shihwei');
INSERT INTO sk_products (product, status, description, username) VALUES ('B5水楊酸洗面膜', '少用', '穩定後一週最多1次，只T字區。', 'shihwei');
INSERT INTO sk_products (product, status, description, username) VALUES ('白瓶G', '14天後優先恢復', '穀胱甘肽亮白。', 'shihwei');
INSERT INTO sk_products (product, status, description, username) VALUES ('橘瓶PV', '白瓶後再加入', '維C抗氧亮白。', 'shihwei');
INSERT INTO sk_products (product, status, description, username) VALUES ('黃瓶V', '最後再用', '高濃維C，最容易刺、乾、脫皮。', 'shihwei');
INSERT INTO sk_products (product, status, description, username) VALUES ('Medi-Peel A醛', '後期低頻率', '一週1次開始，避開眼周。', 'shihwei');
INSERT INTO sk_products (product, status, description, username) VALUES ('TWG水楊酸/壬二酸', '14天後評估', '不要和A醛同晚。', 'shihwei');
INSERT INTO sk_products (product, status, description, username) VALUES ('芷豆泥膜', '目前不建議', '臉乾時停用。', 'shihwei');
INSERT INTO sk_products (product, status, description, username) VALUES ('SPF50+防曬', '每天必用', '皮秒後、防反黑、防老化。', 'shihwei');
INSERT INTO sk_products (product, status, description, username) VALUES ('安耐曬 (Anessa) 金鑽高效防曬露', '未購買 (已有相似現有品)', '高強度防曬。防護效果與現有的『理膚寶水 UVMune 400』相似，理膚防禦力更優，可直接用現有防曬替代。', 'shihwei');
INSERT INTO sk_products (product, status, description, username) VALUES ('AHC 極致防禦零油光防曬棒', '未購買 (防曬補擦用)', '不沾手防曬棒。目前手邊無同類型防曬棒，若有戶外快速補擦需求可考慮購買。', 'shihwei');
INSERT INTO sk_products (product, status, description, username) VALUES ('提提研 向日葵全光譜防曬乳', '未購買 (已有相似現有品)', '清爽型防曬乳。功效與現有的『DR.WU 保濕防曬』及『理膚寶水 UVMune 400』相似，質地清爽，可先用現有防曬。', 'shihwei');
INSERT INTO sk_products (product, status, description, username) VALUES ('Neogence 霓淨思 極透光亮白淡斑精華', '未購買 (已有相似現有品)', '亮白精華。功效與現有的『橘瓶PV (維C)』及『白瓶G (穀胱甘肽)』相似，皆為提亮淡斑，可先用現有的。', 'shihwei');
INSERT INTO sk_products (product, status, description, username) VALUES ('理膚寶水 MELA B3 淡斑淨亮精華', '未購買 (已有相似現有品)', '專利淡斑精華。淡斑功效與現有的『白瓶G (穀胱甘肽)』及『黃瓶V』相似，皆為亮白淡斑，可先用現有的。', 'shihwei');
INSERT INTO sk_products (product, status, description, username) VALUES ('AHC 淨光無瑕淡斑精華', '未購買 (已有相似現有品)', '傳明酸淡斑精華。功效與現有的『白瓶G』、『黃瓶V』差不多，皆為改善暗沉與斑點，可直接用現有產品。', 'shihwei');
INSERT INTO sk_products (product, status, description, username) VALUES ('Melano CC 高純度維他命C亮白精華', '未購買 (已有相似現有品)', '高純度維C精華。功效與現有的『橘瓶PV (維C)』及『黃瓶V (高濃維C)』一樣，皆為高活性維C，可直接用現有品替代。', 'shihwei');
DELETE FROM sk_instructions WHERE username = 'shihwei';
INSERT INTO sk_instructions (product, dosage, usage_method, interval_time, attention, username) VALUES ('雅漾/SD噴霧', '2～4下', '距離20公分噴，10～20秒後輕壓。', '半乾接精華', '不要自然乾到完全乾。', 'shihwei');
INSERT INTO sk_instructions (product, dosage, usage_method, interval_time, attention, username) VALUES ('SD舒緩精華', '1～2滴管', '輕壓，不用拍。', '30～60秒', '刺痛時可只用它＋乳霜。', 'shihwei');
INSERT INTO sk_instructions (product, dosage, usage_method, interval_time, attention, username) VALUES ('神經醯胺', '1～2滴管', '輕壓吸收。', '30～60秒', '早晚可用。', 'shihwei');
INSERT INTO sk_instructions (product, dosage, usage_method, interval_time, attention, username) VALUES ('玻尿酸', '2～4滴', '臉微濕時擦。', '30秒後接乳霜', '不可單擦。', 'shihwei');
INSERT INTO sk_instructions (product, dosage, usage_method, interval_time, attention, username) VALUES ('SD能量霜', '半～1顆黃豆', '全臉薄擦。', '最後一步', 'T字少量。', 'shihwei');
INSERT INTO sk_instructions (product, dosage, usage_method, interval_time, attention, username) VALUES ('白瓶G', '2～3滴', '14天後少量局部。', '1～2分鐘', '一週2～3次開始。', 'shihwei');
INSERT INTO sk_instructions (product, dosage, usage_method, interval_time, attention, username) VALUES ('黃瓶V', '1～2滴局部', '完全穩定後才用。', '2～3分鐘', '乾燥期停用。', 'shihwei');
INSERT INTO sk_instructions (product, dosage, usage_method, interval_time, attention, username) VALUES ('Medi-Peel A醛', '豌豆大小', '晚上用，避開眼周鼻翼嘴角。', '5～10分後補霜', '一週1次開始。', 'shihwei');
INSERT INTO sk_instructions (product, dosage, usage_method, interval_time, attention, username) VALUES ('B5水楊酸洗面膜', '薄敷T字', '5～8分鐘沖掉。', '沖掉後立刻修護', '一週最多1次。', 'shihwei');
INSERT INTO sk_instructions (product, dosage, usage_method, interval_time, attention, username) VALUES ('防曬', '兩指長', '早上最後一步。', '保養後等3～5分', '戶外2～3小時補擦。', 'shihwei');
INSERT INTO sk_instructions (product, dosage, usage_method, interval_time, attention, username) VALUES ('安耐曬 (Anessa) 金鑽高效防曬露', '兩指長', '出門前均勻塗抹於臉部與頸部', '戶外每 2-3 小時補擦', '具防水抗汗科技，洗臉時建議搭配卸妝產品清潔', 'shihwei');
INSERT INTO sk_instructions (product, dosage, usage_method, interval_time, attention, username) VALUES ('AHC 極致防禦零油光防曬棒', '來回塗抹 3-4 次', '直接塗抹於臉部，不需用手推開', '戶外每 2 小時補擦', '補擦前建議先用紙巾壓乾臉上汗水與髒污', 'shihwei');
INSERT INTO sk_instructions (product, dosage, usage_method, interval_time, attention, username) VALUES ('提提研 向日葵全光譜防曬乳', '兩指長', '早上最後一步均勻塗抹', '出門前使用', '一般潔膚產品即可洗淨', 'shihwei');
INSERT INTO sk_instructions (product, dosage, usage_method, interval_time, attention, username) VALUES ('Neogence 霓淨思 極透光亮白淡斑精華', '1 滴管', '夜間洗臉後局部塗抹於斑點處', '每晚使用', '清爽無香精，後續需搭配乳霜鎖水保濕', 'shihwei');
INSERT INTO sk_instructions (product, dosage, usage_method, interval_time, attention, username) VALUES ('理膚寶水 MELA B3 淡斑淨亮精華', '3-4 滴', '夜間清潔後均勻塗抹於斑點處', '每晚使用', '含微量水楊酸助代謝，若肌膚出現緊繃泛紅請先暫停', 'shihwei');
INSERT INTO sk_instructions (product, dosage, usage_method, interval_time, attention, username) VALUES ('AHC 淨光無瑕淡斑精華', '1-2 下', '洗臉後塗抹於斑點處，輕壓至吸收', '早晚使用', '水中帶油質地，後續仍需保濕乳霜', 'shihwei');
INSERT INTO sk_instructions (product, dosage, usage_method, interval_time, attention, username) VALUES ('Melano CC 高純度維他命C亮白精華', '4-5 滴', '局部塗抹於臉頰色素沉澱較深處', '每晚局部使用', '高活性維C，乾燥脫皮或皮秒術後敏感情況下暫停使用', 'shihwei');
DELETE FROM sk_routines WHERE username = 'shihwei';
INSERT INTO sk_routines (time_of_day, flow, username) VALUES ('早上', '清水/溫和洗臉 → 雅漾或SD噴霧 → 神經醯胺 → 玻尿酸 → SD能量霜薄擦 → 主力臉部防曬', 'shihwei');
INSERT INTO sk_routines (time_of_day, flow, username) VALUES ('晚上', '溫和洗臉 → 雅漾或SD噴霧 → SD舒緩精華或神經醯胺 → 玻尿酸 → SD能量霜', 'shihwei');
INSERT INTO sk_routines (time_of_day, flow, username) VALUES ('乾燥急救', '停用功效型產品 → 雅漾/SD噴霧 → 神經醯胺 → SD能量霜 → B5或CeraVe', 'shihwei');
DELETE FROM sk_sunscreens;
INSERT INTO sk_sunscreens (rank, product, score, position, recommendation) VALUES ('🥇 No.1', '理膚寶水 UVMune 400', '9.5/10', '主力臉部防曬', '適合皮秒後、怕反黑、需要高UVA防護。');
INSERT INTO sk_sunscreens (rank, product, score, position, recommendation) VALUES ('🥈 No.2', '雅漾防曬系列', '9/10', '敏感肌/修護期', '適合臉乾、術後、敏感時期。');
INSERT INTO sk_sunscreens (rank, product, score, position, recommendation) VALUES ('🥉 No.3', 'DR.WU 保濕防曬', '9/10', '保濕型防曬', '適合外油內乾、缺水。');
INSERT INTO sk_sunscreens (rank, product, score, position, recommendation) VALUES ('No.4', 'OBgE 素顏霜防曬', '8.5/10', '潤色修飾', '建議當修飾，不完全取代足量防曬。');
INSERT INTO sk_sunscreens (rank, product, score, position, recommendation) VALUES ('No.5', 'YIMIAOSI SPF50+', '7/10', '身體防曬優先', '臉部可用但非主力。');
DELETE FROM sk_avoid_rules;
INSERT INTO sk_avoid_rules (do_not, reason, correct_way) VALUES ('噴霧後完全自然乾', '可能更緊繃。', '噴後10～20秒輕壓。');
INSERT INTO sk_avoid_rules (do_not, reason, correct_way) VALUES ('用力拍打', '乾燥/術後易刺激。', '手掌輕壓。');
INSERT INTO sk_avoid_rules (do_not, reason, correct_way) VALUES ('玻尿酸單擦', '可能越擦越乾。', '後接乳霜鎖水。');
INSERT INTO sk_avoid_rules (do_not, reason, correct_way) VALUES ('A醛 + 酸類同晚', '太刺激。', '至少間隔2天。');
INSERT INTO sk_avoid_rules (do_not, reason, correct_way) VALUES ('水楊酸洗面膜 + A醛同晚', '屏障容易受不了。', '分開不同天。');
INSERT INTO sk_avoid_rules (do_not, reason, correct_way) VALUES ('臉乾還敷泥膜', '會更乾。', '穩定後只敷T字區。');
DELETE FROM sk_dupes;
INSERT INTO sk_dupes (original_product, dupe_product, category) VALUES ('SD噴霧', '雅漾活泉水、理膚寶水B5噴霧、Curel噴霧', '噴霧');
INSERT INTO sk_dupes (original_product, dupe_product, category) VALUES ('SD舒緩精華', 'DR.WU神經醯胺、理膚寶水B5精華、藝群神經醯胺', '精華液');
INSERT INTO sk_dupes (original_product, dupe_product, category) VALUES ('SD能量霜', 'CeraVe修護乳霜、理膚寶水B5+、Curel乳霜', '乳霜');
