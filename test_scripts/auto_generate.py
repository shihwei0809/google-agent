import json
import os

# Data for Document 1
quiz_data_1 = {
    'title': '進出貨作業管理辦法 (3.0版)',
    'subtitle': '請詳閱簡報內容並完成測驗',
    'slides': [
        {
            'title': '1. 目的與適用範圍',
            'bullets': ['規範原物料進貨與製成品出貨作業程序。', '確保進出貨數量正確及品質符合標準。', '適用於全廠進出貨相關單位。'],
            'narration': '本辦法的目的在於規範進出貨作業程序，確保數量與品質正確。'
        },
        {
            'title': '2. 進貨作業流程',
            'bullets': ['供應商車輛進入需於警衛室登記。', '倉管人員依據「採購單」核對品名、規格、數量。', '通知品管人員進行進料檢驗。'],
            'narration': '進貨時，倉管人員必須核對採購單，並通知品管進行檢驗。'
        },
        {
            'title': '3. 出貨作業流程',
            'bullets': ['業務部開立「出貨單」。', '倉管依出貨單備妥貨物並核對批號與數量。', '裝載後由司機與倉管人員共同簽收確認。'],
            'narration': '出貨時，需依據業務部開立的出貨單備貨，並確實核對數量。'
        },
        {
            'title': '4. 異常處理與表單歸檔',
            'bullets': ['進貨數量不符或檢驗不合格，依異常處理流程退退或特採。', '進出貨表單應妥善保存歸檔以供追溯。', '落實先進先出 (FIFO) 管理原則。'],
            'narration': '若有異常狀況需依規定處理，且表單必須妥善保存。'
        }
    ],
    'quiz': [
        {
            'question': '進貨時，倉管人員主要依據什麼單據核對貨物？',
            'options': ['A. 出貨單', 'B. 採購單', 'C. 請款單', 'D. 報價單'],
            'answer': 'B',
            'explanation': '進貨時應依據採購單核對供應商送來的貨物。'
        },
        {
            'question': '出貨單通常由哪一個單位開立？',
            'options': ['A. 倉管部', 'B. 品管部', 'C. 業務部', 'D. 生產部'],
            'answer': 'C',
            'explanation': '出貨單由業務部開立，倉管依單出貨。'
        },
        {
            'question': '進出貨物品的庫存管理應遵守什麼基本原則？',
            'options': ['A. 後進先出', 'B. 先進先出 (FIFO)', 'C. 隨機出貨', 'D. 先進後出'],
            'answer': 'B',
            'explanation': '庫存管理應落實先進先出 (FIFO) 原則。'
        }
    ]
}

# Data for Document 2
quiz_data_2 = {
    'title': '儲槽進出貨作業方法 (3.1版)',
    'subtitle': '請詳閱簡報內容並完成測驗',
    'slides': [
        {
            'title': '1. 儲槽進貨前準備',
            'bullets': ['確認儲槽可用容量是否足以容納進貨量。', '作業人員需穿戴適當之個人防護具 (PPE)。', '槽車到達後確實接地，防止靜電。'],
            'narration': '儲槽進貨前，必須確認槽體容量、穿戴防護具，並確實將槽車接地。'
        },
        {
            'title': '2. 進出貨管線與閥門確認',
            'bullets': ['核對槽車物質與儲槽標示是否一致。', '連接專用卸料管線，確認接頭鎖緊無洩漏。', '依SOP開啟對應閥門 (進料閥/排氣閥)。'],
            'narration': '進料前需再三確認物質正確，並確保管線鎖緊無洩漏風險。'
        },
        {
            'title': '3. 作業中監控與紀錄',
            'bullets': ['作業中人員不得擅自離開現場。', '隨時監控液位變化與管線壓力。', '發現異常或洩漏應立即停止作業並通報。'],
            'narration': '作業期間必須全程監控液位與壓力，遇到異常立即停止並通報。'
        },
        {
            'title': '4. 作業完成與復原',
            'bullets': ['卸料完畢後先關閉閥門，排空管線殘液。', '拆除管線並蓋上盲板。', '填寫「儲槽進出貨作業紀錄表」。'],
            'narration': '作業結束後，必須確實關閉閥門、排空管線，並完成紀錄表填寫。'
        }
    ],
    'quiz': [
        {
            'question': '槽車進行儲槽卸料作業前，最重要的防靜電措施是什麼？',
            'options': ['A. 灑水降溫', 'B. 槽車確實接地', 'C. 關閉引擎', 'D. 打開車門'],
            'answer': 'B',
            'explanation': '為防止靜電引發危害，槽車作業前必須確實接地。'
        },
        {
            'question': '儲槽進出貨作業中，作業人員可以離開現場嗎？',
            'options': ['A. 可以，只要管線接好', 'B. 可以，只要有人替代', 'C. 絕對不可擅自離開', 'D. 視天氣情況而定'],
            'answer': 'C',
            'explanation': '作業中人員必須全程監控，不得擅自離開現場。'
        },
        {
            'question': '卸料作業完成後，管線拆除前的必要步驟是什麼？',
            'options': ['A. 直接拔除管線', 'B. 用水沖洗管線', 'C. 關閉閥門並排空管線殘液', 'D. 請司機直接開走'],
            'answer': 'C',
            'explanation': '拆除管線前，必須先關閉閥門並排空殘餘液體以防外洩。'
        }
    ]
}

# Common setup
gen_dir = r"C:\GOOGLE ANGET\第一類_核心網頁與互動系統\員工教育訓練測驗系統\sop_generator"
template_path = os.path.join(gen_dir, "player_template.js")
try:
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    # Extract just the HTML part from player_template.js (remove const PLAYER_TEMPLATE =  and ;)
    html_template = template_content.replace('const PLAYER_TEMPLATE = ', '')
    if html_template.endswith(';'):
        html_template = html_template[:-2]
    if html_template.endswith(';\n'):
        html_template = html_template[:-3]
except:
    html_template = "<html><body>Error loading template</body></html>"

schema_sql = '''DROP TABLE IF EXISTS exam_records;
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
);'''

wrangler_toml = '''name = "sop-training"
pages_build_output_dir = "."
compatibility_date = "2024-03-20"

[[d1_databases]]
binding = "DB"
database_name = "sop_exam_records"
database_id = "your-database-id-here"'''

submit_js = '''export async function onRequestPost(context) {
  try {
    const data = await context.request.json();
    const name = data.name || "未知";
    const timestamp = data.timestamp || new Date().toLocaleString('zh-TW');
    const score = data.score !== undefined ? data.score : 0;
    const correctCount = data.correctCount || 0;
    const total = data.total || 5;
    const q1 = data.q1 || "";
    const q2 = data.q2 || "";
    const q3 = data.q3 || "";
    const q4 = data.q4 || "";
    const q5 = data.q5 || "";
    const stmt = context.env.DB.prepare(
      INSERT INTO exam_records (timestamp, name, score, correctCount, total, q1, q2, q3, q4, q5)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ).bind(timestamp, name, score, correctCount, total, q1, q2, q3, q4, q5);
    await stmt.run();
    return new Response(JSON.stringify({ status: "ok" }), { headers: { "Content-Type": "application/json" } });
  } catch (err) {
    return new Response(JSON.stringify({ status: "error", message: err.message }), { status: 500 });
  }
}'''

def create_project(data, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(os.path.join(out_dir, "functions", "api"), exist_ok=True)
    
    html = html_template
    html = html.replace('__TRAINING_TITLE__', data['title'])
    html = html.replace('__TRAINING_SUBTITLE__', data['subtitle'])
    html = html.replace('__SLIDES_DATA__', json.dumps(data['slides'], ensure_ascii=False))
    html = html.replace('__QUIZ_DATA__', json.dumps(data['quiz'], ensure_ascii=False))
    html = html.replace('__PASS_SCORE__', '100')
    html = html.replace('__REQUIRE_LISTEN__', 'false')
    html = html.replace('__CLOSE_SCRIPT__', '</script>')
    
    with open(os.path.join(out_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(html)
    
    with open(os.path.join(out_dir, 'schema.sql'), 'w', encoding='utf-8') as f:
        f.write(schema_sql)
        
    with open(os.path.join(out_dir, 'wrangler.toml'), 'w', encoding='utf-8') as f:
        f.write(wrangler_toml)
        
    with open(os.path.join(out_dir, 'functions', 'api', 'submit.js'), 'w', encoding='utf-8') as f:
        f.write(submit_js)
        
    print(f"Project created at {out_dir}")

dir1 = r"C:\GOOGLE ANGET\第一類_核心網頁與互動系統\員工教育訓練測驗系統\C50110-INV-02_進出貨作業管理辦法_教材"
dir2 = r"C:\GOOGLE ANGET\第一類_核心網頁與互動系統\員工教育訓練測驗系統\C50110-INV-02-01_儲槽進出貨作業方法_教材"

create_project(quiz_data_1, dir1)
create_project(quiz_data_2, dir2)

