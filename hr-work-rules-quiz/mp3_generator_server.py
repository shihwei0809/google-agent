"""
SOP 內容與配音視覺化管理工具 — 本機 Web UI 版
雙擊 exe / bat 啟動，自動開啟瀏覽器
"""

import asyncio, os, json, csv, sys, io, threading, webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# PyInstaller 打包後 __file__ 指向暫存資料夾，改用 sys.executable
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SLIDES_DIR = os.path.join(BASE_DIR, "slides")
CONFIG_PATH = os.path.join(BASE_DIR, "quiz_data.json")
CSV_PATH = os.path.join(BASE_DIR, "results.csv")
PORT = 7788

# ── 預設設定（當檔案不存在時建立） ──────────────────────────────
DEFAULT_CONFIG = {
    "status": "ok",
    "title": "員工教育訓練測驗系統 — 工作規則",
    "subtitle": "請仔細觀看簡報，看完後即可解鎖測驗進行答題。",
    "slides": [
        { "img": "slides/slide_01.png", "label": "第 1 頁｜簡介", "say": "歡迎參加本次教育訓練，請仔細聆聽每一頁的說明內容。" }
    ],
    "questions": [
        {
            "question": "新進同仁到職幾天後，實施第一次考核評估？",
            "a": "A. 30天", "b": "B. 40天", "c": "C. 60天", "d": "D. 90天",
            "answer": "B"
        }
    ]
}

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return DEFAULT_CONFIG
    else:
        # 嘗試舊版升級
        return DEFAULT_CONFIG

def save_config(data):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ── 偵測目錄中實際的 png 檔案 ────────────────────────────────
def detect_slide_files():
    slides = []
    if os.path.isdir(SLIDES_DIR):
        for f in sorted(os.listdir(SLIDES_DIR)):
            if f.lower().endswith(".png") and f.startswith("slide_") and "img" not in f:
                slides.append(f"slides/{f}")
    return slides

# ── 生成單一 MP3 ──────────────────────────────────────────────
async def gen_one(name, text, voice, rate_str):
    try:
        import edge_tts
    except ImportError:
        return False, "請先安裝 edge-tts：pip install edge-tts"
    os.makedirs(SLIDES_DIR, exist_ok=True)
    out = os.path.join(SLIDES_DIR, f"{name}.mp3")
    try:
        c = edge_tts.Communicate(text, voice, rate=rate_str)
        await c.save(out)
        size = os.path.getsize(out)
        return True, f"{size//1024} KB"
    except Exception as e:
        return False, str(e)

# ── HTML 頁面 ──────────────────────────────────────────────────
HTML = r"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🎙 SOP 教育訓練與題目管理工具</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

  :root {
    --bg: #0f1117;
    --surface: #1a1d27;
    --surface2: #232635;
    --border: #2e3247;
    --accent: #6366f1;
    --accent2: #818cf8;
    --green: #22c55e;
    --red: #ef4444;
    --yellow: #f59e0b;
    --text: #e2e8f0;
    --muted: #64748b;
    --radius: 12px;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    font-family: 'Inter', sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    padding: 24px;
  }

  .header {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 28px;
    padding-bottom: 20px;
    border-bottom: 1px solid var(--border);
  }

  .header-icon {
    width: 52px; height: 52px;
    background: linear-gradient(135deg, var(--accent), #8b5cf6);
    border-radius: 14px;
    display: flex; align-items: center; justify-content: center;
    font-size: 24px;
    box-shadow: 0 4px 20px rgba(99,102,241,.4);
  }

  h1 { font-size: 22px; font-weight: 700; }
  .subtitle { color: var(--muted); font-size: 13px; margin-top: 3px; }

  /* 頁籤 Tab */
  .tabs {
    display: flex;
    gap: 10px;
    margin-bottom: 20px;
    border-bottom: 1px solid var(--border);
    padding-bottom: 10px;
  }

  .tab-btn {
    background: none;
    border: none;
    color: var(--muted);
    font-size: 15px;
    font-weight: 600;
    padding: 10px 20px;
    cursor: pointer;
    border-radius: 8px;
    transition: all .2s;
  }

  .tab-btn:hover {
    color: var(--text);
    background: rgba(255,255,255,.03);
  }

  .tab-btn.active {
    color: #fff;
    background: var(--accent);
    box-shadow: 0 4px 15px rgba(99,102,241,.3);
  }

  .tab-content {
    display: none;
  }

  .tab-content.active {
    display: block;
  }

  /* 通用區塊 */
  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 20px;
    margin-bottom: 20px;
  }

  .form-group {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-bottom: 16px;
  }

  .form-group label {
    font-size: 13px;
    color: var(--muted);
    font-weight: 600;
  }

  input[type=text], select, textarea {
    background: var(--surface2);
    border: 1px solid var(--border);
    color: var(--text);
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 14px;
    outline: none;
    transition: border-color .2s;
  }

  input[type=text]:focus, select:focus, textarea:focus {
    border-color: var(--accent);
  }

  /* 按鈕 */
  .btn {
    display: inline-flex; align-items: center; gap: 8px;
    padding: 10px 20px;
    border-radius: 8px;
    border: none;
    font-size: 14px; font-weight: 600;
    cursor: pointer;
    transition: all .18s;
  }
  .btn:disabled { opacity: .4; cursor: not-allowed; }
  .btn-primary {
    background: linear-gradient(135deg, var(--accent), #8b5cf6);
    color: #fff;
    box-shadow: 0 4px 15px rgba(99,102,241,.35);
  }
  .btn-primary:hover:not(:disabled) { transform: translateY(-1px); }
  .btn-secondary {
    background: var(--surface2);
    color: var(--text);
    border: 1px solid var(--border);
  }
  .btn-secondary:hover:not(:disabled) { border-color: var(--accent); color: var(--accent2); }
  .btn-danger {
    background: rgba(239,68,68,.15);
    color: var(--red);
    border: 1px solid rgba(239,68,68,.3);
  }
  .btn-danger:hover:not(:disabled) { background: rgba(239,68,68,.25); }

  /* 簡報旁白表格 */
  table { width: 100%; border-collapse: collapse; }
  thead th {
    background: var(--surface2);
    padding: 12px 16px;
    text-align: left;
    font-size: 11px;
    font-weight: 600;
    color: var(--muted);
    border-bottom: 1px solid var(--border);
  }
  tbody tr { border-bottom: 1px solid var(--border); transition: background .15s; }
  tbody tr:last-child { border-bottom: none; }
  tbody tr:hover { background: rgba(255,255,255,.01); }
  td { padding: 12px 16px; vertical-align: middle; }

  .slide-thumb {
    width: 60px;
    height: 35px;
    object-fit: cover;
    border-radius: 4px;
    border: 1px solid var(--border);
    background: #000;
  }

  /* 考題卡片編輯 */
  .question-item {
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 18px;
    margin-bottom: 16px;
    background: rgba(255,255,255,.01);
  }

  .question-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 14px;
  }

  .option-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 14px;
    margin-bottom: 12px;
  }

  /* 進度條 */
  .progress-wrap {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 16px 20px;
    margin-bottom: 20px;
    display: none;
  }
  .progress-wrap.show { display: block; }
  .progress-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
  .progress-label { font-size: 13px; font-weight: 500; }
  .progress-pct { font-size: 13px; color: var(--accent2); font-weight: 700; }
  .progress-bar-bg { background: var(--surface2); border-radius: 99px; height: 8px; overflow: hidden; }
  .progress-bar-fill { height: 100%; background: linear-gradient(90deg, var(--accent), #8b5cf6); border-radius: 99px; width: 0%; transition: width .3s; }

  /* 狀態 */
  .status-badge {
    display: inline-flex; align-items: center; gap: 5px;
    padding: 4px 10px;
    border-radius: 99px;
    font-size: 11px;
    font-weight: 600;
  }
  .status-idle    { background: rgba(100,116,139,.15); color: var(--muted); }
  .status-running { background: rgba(99,102,241,.15);  color: var(--accent2); }
  .status-ok      { background: rgba(34,197,94,.15);   color: var(--green); }
  .status-err     { background: rgba(239,68,68,.15);   color: var(--red); }

  /* 通知 toast */
  #toast {
    position: fixed; bottom: 24px; right: 24px;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 12px 18px;
    font-size: 13px;
    box-shadow: 0 8px 30px rgba(0,0,0,.5);
    transform: translateY(80px); opacity: 0;
    transition: all .3s;
    z-index: 999;
  }
  #toast.show { transform: translateY(0); opacity: 1; }
  #toast.success { border-color: var(--green); color: var(--green); }
  #toast.error   { border-color: var(--red);   color: var(--red); }
</style>
</head>
<body>

<div class="header">
  <div class="header-icon">⚙️</div>
  <div>
    <h1>SOP 教育訓練與題目管理中心</h1>
    <div class="subtitle">視覺化修改訓練標題、更換投影片旁白與考題選項</div>
  </div>
</div>

<div class="tabs">
  <button class="tab-btn active" onclick="switchTab('tab-slides')">📋 簡報旁白與配音</button>
  <button class="tab-btn" onclick="switchTab('tab-questions')">📝 測驗題目編輯</button>
  <button class="tab-btn" onclick="switchTab('tab-results')">📊 作答紀錄收集</button>
</div>

<div style="display:flex; justify-content:flex-end; margin-bottom: 20px;">
  <button class="btn btn-primary" onclick="saveAllConfig()" style="background: linear-gradient(135deg, #10b981, #059669); box-shadow: 0 4px 15px rgba(16,185,129,.3);">
    💾 儲存所有 SOP 設定
  </button>
</div>

<!-- 進度條 -->
<div class="progress-wrap" id="progress-wrap">
  <div class="progress-header">
    <span class="progress-label" id="progress-label">配音生成中...</span>
    <span class="progress-pct" id="progress-pct">0%</span>
  </div>
  <div class="progress-bar-bg">
    <div class="progress-bar-fill" id="progress-fill"></div>
  </div>
</div>

<!-- Tab 1: 簡報與旁白管理 -->
<div id="tab-slides" class="tab-content active">
  <div class="card">
    <h3 style="margin-bottom:14px">訓練主題標題設定</h3>
    <div class="option-row">
      <div class="form-group">
        <label>大標題（呈現於網頁最上方）</label>
        <input type="text" id="cfg-title" placeholder="例如：新進同仁消防安全教育訓練">
      </div>
      <div class="form-group">
        <label>說明副標題</label>
        <input type="text" id="cfg-subtitle" placeholder="例如：請仔細聆聽簡報，看完後即可進入測驗。">
      </div>
    </div>
  </div>

  <div class="card">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px">
      <h3>投影片旁白列表</h3>
      <div style="display:flex; gap:10px; align-items:center">
        <label style="font-size:12px; color:var(--muted)">配音設定：</label>
        <select id="voice-sel" style="padding:6px 12px; font-size:12px">
          <option value="zh-TW-HsiaoChenNeural">曉臻（女聲・清晰）</option>
          <option value="zh-TW-HsiaoYuNeural">曉宇（女聲・溫柔）</option>
          <option value="zh-TW-YunJheNeural">雲哲（男聲）</option>
        </select>
        <input type="range" id="rate-slider" min="-30" max="30" value="0" step="5" style="width:100px">
        <span class="rate-display" id="rate-display" style="font-size:12px">正常</span>
        <button class="btn btn-primary btn-sm" onclick="generateAllVoices()">▶ 一鍵生成全部配音</button>
      </div>
    </div>
    
    <table id="slides-table">
      <thead>
        <tr>
          <th style="width:60px">預覽</th>
          <th style="width:140px">投影片標題</th>
          <th>語音旁白朗讀內容</th>
          <th style="width:100px; text-align:center">狀態</th>
          <th style="width:80px; text-align:center">配音</th>
        </tr>
      </thead>
      <tbody id="slides-tbody"></tbody>
    </table>
    <div style="margin-top:14px; text-align:right">
      <button class="btn btn-secondary btn-sm" onclick="addNewSlide()">＋ 新增投影片頁面</button>
    </div>
  </div>
</div>

<!-- Tab 2: 測驗題目編輯 -->
<div id="tab-questions" class="tab-content">
  <div class="card">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:18px">
      <h3>題目列表</h3>
      <button class="btn btn-secondary btn-sm" onclick="addNewQuestion()">＋ 新增考題</button>
    </div>
    
    <div id="questions-list"></div>
  </div>
</div>

<!-- Tab 3: 作答紀錄收集 -->
<div id="tab-results" class="tab-content">
  <div class="card">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:18px">
      <h3>本機收集之同仁作答紀錄 (results.csv)</h3>
      <div>
        <button class="btn btn-primary btn-sm" onclick="downloadCSVFile()">📥 下載 results.csv</button>
        <button class="btn btn-danger btn-sm" onclick="clearResultsFile()">🗑 清除全部紀錄</button>
      </div>
    </div>
    <div style="overflow-x:auto;">
      <table id="results-table">
        <thead>
          <tr id="results-thead-tr">
            <th>時間戳記</th>
            <th>姓名</th>
            <th>得分</th>
            <th>答對題數</th>
          </tr>
        </thead>
        <tbody id="results-tbody"></tbody>
      </table>
    </div>
  </div>
</div>

<div id="toast"></div>

<script>
let globalConfig = { title: "", subtitle: "", slides: [], questions: [] };
let voiceRunning = false;

// ── 切換頁籤 ────────────────────────────────────────────────
function switchTab(tabId) {
  document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
  
  event.target.classList.add('active');
  document.getElementById(tabId).classList.add('active');

  if(tabId === 'tab-results') {
    loadResults();
  }
}

// ── 載入設定 ────────────────────────────────────────────────
async function init() {
  const res = await fetch('/api/get_config');
  globalConfig = await res.json();
  
  document.getElementById('cfg-title').value = globalConfig.title || "";
  document.getElementById('cfg-subtitle').value = globalConfig.subtitle || "";
  
  renderSlidesTable();
  renderQuestionsList();
}

// ── 渲染投影片 ──────────────────────────────────────────────
function renderSlidesTable() {
  const tbody = document.getElementById('slides-tbody');
  tbody.innerHTML = '';
  
  globalConfig.slides.forEach((s, idx) => {
    // 預設圖片路徑格式：slides/slide_01.png
    const imgName = s.img.split('/').pop();
    const name = imgName.split('.').shift();
    
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><img src="${s.img}" class="slide-thumb" onerror="this.src='https://placehold.co/120x70/232635/e2e8f0?text=No+Image'"></td>
      <td>
        <input type="text" value="${s.label || ''}" style="width:100%" onchange="updateSlideLabel(${idx}, this.value)" placeholder="頁面標籤">
        <div style="font-size:10px; color:var(--muted); margin-top:4px; font-family:monospace">${s.img}</div>
      </td>
      <td>
        <textarea style="width:100%; min-height:45px;" onchange="updateSlideSay(${idx}, this.value)" placeholder="請輸入本頁朗讀旁白...">${s.say || ''}</textarea>
      </td>
      <td style="text-align:center">
        <span class="status-badge status-idle" id="st-${name}">－</span>
      </td>
      <td style="text-align:center">
        <button class="btn btn-sm btn-secondary" onclick="generateVoiceOne('${name}', ${idx})" style="padding:6px 10px">▶</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function updateSlideLabel(idx, val) { globalConfig.slides[idx].label = val; }
function updateSlideSay(idx, val) { globalConfig.slides[idx].say = val; }

function addNewSlide() {
  const num = globalConfig.slides.length + 1;
  const numStr = String(num).padStart(2, '0');
  globalConfig.slides.push({
    img: `slides/slide_${numStr}.png`,
    label: `第 ${num} 頁`,
    say: ""
  });
  renderSlidesTable();
}

// ── 渲染考題 ────────────────────────────────────────────────
function renderQuestionsList() {
  const container = document.getElementById('questions-list');
  container.innerHTML = '';
  
  if(!globalConfig.questions || globalConfig.questions.length === 0) {
    container.innerHTML = '<div style="color:var(--muted); text-align:center; padding:20px;">目前尚無考題，請點擊右上方「新增考題」按鈕開始建立。</div>';
    return;
  }
  
  globalConfig.questions.forEach((q, idx) => {
    const qDiv = document.createElement('div');
    qDiv.className = 'question-item';
    qDiv.innerHTML = `
      <div class="question-header">
        <strong style="color:var(--accent2)">第 ${idx+1} 題</strong>
        <button class="btn btn-sm btn-danger" onclick="deleteQuestion(${idx})" style="padding:4px 10px; font-size:11px">刪除題目</button>
      </div>
      <div class="form-group" style="margin-bottom:12px">
        <label>題目內容</label>
        <input type="text" value="${q.question || ''}" style="width:100%" onchange="updateQText(${idx}, this.value)" placeholder="請輸入題目內容...">
      </div>
      <div class="option-row">
        <div class="form-group">
          <label>選項 A</label>
          <input type="text" value="${q.a || ''}" onchange="updateQOption(${idx}, 'a', this.value)">
        </div>
        <div class="form-group">
          <label>選項 B</label>
          <input type="text" value="${q.b || ''}" onchange="updateQOption(${idx}, 'b', this.value)">
        </div>
      </div>
      <div class="option-row">
        <div class="form-group">
          <label>選項 C</label>
          <input type="text" value="${q.c || ''}" onchange="updateQOption(${idx}, 'c', this.value)">
        </div>
        <div class="form-group">
          <label>選項 D</label>
          <input type="text" value="${q.d || ''}" onchange="updateQOption(${idx}, 'd', this.value)">
        </div>
      </div>
      <div class="form-group" style="width:200px; margin-bottom:0">
        <label>🎯 正確答案</label>
        <select onchange="updateQAns(${idx}, this.value)">
          <option value="A" ${q.answer === 'A' ? 'selected' : ''}>A</option>
          <option value="B" ${q.answer === 'B' ? 'selected' : ''}>B</option>
          <option value="C" ${q.answer === 'C' ? 'selected' : ''}>C</option>
          <option value="D" ${q.answer === 'D' ? 'selected' : ''}>D</option>
        </select>
      </div>
    `;
    container.appendChild(qDiv);
  });
}

// 變更考題資訊
function updateQText(idx, val) { globalConfig.questions[idx].question = val; }
function updateQOption(idx, key, val) { globalConfig.questions[idx][key] = val; }
function updateQAns(idx, val) { globalConfig.questions[idx].answer = val; }

function addNewQuestion() {
  if(!globalConfig.questions) globalConfig.questions = [];
  globalConfig.questions.push({
    question: "",
    a: "", b: "", c: "", d: "",
    answer: "A"
  });
  renderQuestionsList();
}

function deleteQuestion(idx) {
  if(confirm('確定要刪除此題目嗎？')) {
    globalConfig.questions.splice(idx, 1);
    renderQuestionsList();
  }
}

// ── 語速設定與顯示 ──────────────────────────────────────────
document.getElementById('rate-slider').addEventListener('input', function() {
  const v = parseInt(this.value);
  const labels = { '-30':'很慢', '-20':'慢', '-10':'稍慢', '0':'正常', '10':'稍快', '20':'快', '30':'很快' };
  document.getElementById('rate-display').textContent = labels[String(v)] || (v > 0 ? `+${v}%` : `${v}%`);
});

function getRate() {
  const v = parseInt(document.getElementById('rate-slider').value);
  return v >= 0 ? `+${v}%` : `${v}%`;
}
function getVoice() { return document.getElementById('voice-sel').value; }

// ── 單頁配音生成 ────────────────────────────────────────────
async function generateVoiceOne(name, idx) {
  const text = globalConfig.slides[idx].say.trim();
  if(!text) { showToast('請填入該頁旁白再進行配音', 'error'); return; }
  
  setStatus(name, 'running', '生成中…');
  try {
    const res = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, text, voice: getVoice(), rate: getRate() })
    });
    const d = await res.json();
    if(d.ok) {
      setStatus(name, 'ok', '✓ ' + d.size);
      showToast(`${name}.mp3 生成完成`, 'success');
    } else {
      setStatus(name, 'err', '錯誤');
      showToast('配音失敗：' + d.error, 'error');
    }
  } catch(e) {
    setStatus(name, 'err', '錯誤');
  }
}

// ── 一鍵生成全部配音 ────────────────────────────────────────
async function generateAllVoices() {
  if(voiceRunning) return;
  const toGen = [];
  globalConfig.slides.forEach((s, idx) => {
    if(s.say.trim()) {
      const imgName = s.img.split('/').pop().split('.').shift();
      toGen.push({ name: imgName, text: s.say.trim(), idx });
    }
  });
  
  if(toGen.length === 0) { showToast('沒有任何頁面有旁白文字', 'error'); return; }
  
  voiceRunning = true;
  const pw = document.getElementById('progress-wrap');
  pw.classList.add('show');
  
  let done = 0;
  for(const item of toGen) {
    updateProgress(done, toGen.length);
    setStatus(item.name, 'running', '生成中…');
    try {
      const res = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: item.name, text: item.text, voice: getVoice(), rate: getRate() })
      });
      const d = await res.json();
      setStatus(item.name, d.ok ? 'ok' : 'err', d.ok ? '✓ ' + d.size : '失敗');
    } catch(e) {
      setStatus(item.name, 'err', '錯誤');
    }
    done++;
  }
  
  updateProgress(done, toGen.length);
  showToast(`✅ 完成！共產出 ${done} 首配音`, 'success');
  setTimeout(() => pw.classList.remove('show'), 1500);
  voiceRunning = false;
}

function updateProgress(done, total) {
  const pct = Math.round(done / total * 100);
  document.getElementById('progress-fill').style.width = pct + '%';
  document.getElementById('progress-pct').textContent = pct + '%';
  document.getElementById('progress-label').textContent = `配音進度 ${done} / ${total}`;
}

function setStatus(name, type, text) {
  const el = document.getElementById('st-' + name);
  if(el) {
    el.className = 'status-badge status-' + type;
    el.textContent = text;
  }
}

// ── 儲存設定 ────────────────────────────────────────────────
async function saveAllConfig() {
  globalConfig.title = document.getElementById('cfg-title').value.trim();
  globalConfig.subtitle = document.getElementById('cfg-subtitle').value.trim();
  
  try {
    const res = await fetch('/api/save_config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(globalConfig)
    });
    const d = await res.json();
    if(d.ok) {
      showToast('🎉 SOP 設定與考題已儲存成功！', 'success');
    } else {
      showToast('儲存失敗：' + d.error, 'error');
    }
  } catch(e) {
    showToast('連線失敗：' + e, 'error');
  }
}

// ── 載入結果紀錄 ────────────────────────────────────────────
async function loadResults() {
  try {
    const res = await fetch('/api/results');
    const data = await res.json();
    const tbody = document.getElementById('results-tbody');
    const trHead = document.getElementById('results-thead-tr');
    
    tbody.innerHTML = '';
    
    if(!data || data.length === 0) {
      tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; color:var(--muted)">目前尚無同仁的作答紀錄。</td></tr>';
      return;
    }
    
    // 動態補滿第 N 題的 Header
    const maxCols = Math.max(...data.map(r => r.length));
    trHead.innerHTML = '<th>時間戳記</th><th>姓名</th><th>得分</th><th>答對題數</th>';
    for(let i = 1; i <= (maxCols - 4); i++) {
      const th = document.createElement('th');
      th.textContent = `第 ${i} 題`;
      trHead.appendChild(th);
    }
    
    data.forEach(r => {
      const tr = document.createElement('tr');
      // r[0]: ts, r[1]: name, r[2]: correct, r[3]: score
      tr.innerHTML = `
        <td>${r[0] || ''}</td>
        <td style="color:var(--accent2); font-weight:600">${r[1] || ''}</td>
        <td style="color:var(--green); font-weight:600">${r[3] || ''}</td>
        <td>${r[2] || ''}</td>
      `;
      for(let i = 4; i < maxCols; i++) {
        const td = document.createElement('td');
        td.textContent = r[i] || '';
        tr.appendChild(td);
      }
      tbody.appendChild(tr);
    });
    
  } catch(e) {
    console.warn('載入紀錄失敗', e);
  }
}

function downloadCSVFile() {
  window.open('/api/download_results');
}

async function clearResultsFile() {
  if(confirm('確定要永久刪除主機上的結果紀錄 (results.csv) 嗎？此操作無法還原！')) {
    const res = await fetch('/api/clear_results', { method: 'POST' });
    const d = await res.json();
    if(d.ok) {
      showToast('作答紀錄已全部清除', 'success');
      loadResults();
    }
  }
}

// ── Toast ────────────────────────────────────────────────────
function showToast(msg, type='success') {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = 'show ' + type;
  clearTimeout(t._timer);
  t._timer = setTimeout(() => { t.className = ''; }, 3500);
}

init();
</script>
</body>
</html>"""

# ── HTTP Handler ──────────────────────────────────────────────
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass  # 靜音 log

    def send_json(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/api/get_config":
            self.send_json(load_config())

        elif path == "/api/slides":
            cfg = load_config()
            slides_detected = detect_slide_files()
            # 與偵測到的實體投影片路徑整合
            slides_list = []
            narrations = {}
            
            # 從實體檔案和設定檔中找出所有 slide name
            slide_names = set()
            for s in cfg.get("slides", []):
                img_name = s["img"].split('/')[-1].split('.')[0]
                slide_names.add(img_name)
                narrations[img_name] = s.get("say", "")
            for s_path in slides_detected:
                img_name = s_path.split('/')[-1].split('.')[0]
                slide_names.add(img_name)
            
            sorted_names = sorted(list(slide_names))
            self.send_json({"slides": sorted_names, "narrations": narrations})

        elif path == "/api/results":
            results = []
            if os.path.exists(CSV_PATH):
                try:
                    with open(CSV_PATH, newline="", encoding="utf-8-sig") as f:
                        reader = csv.reader(f)
                        header = next(reader, None) # 跳過 header
                        for row in reader:
                            if row: results.append(row)
                except Exception:
                    pass
            self.send_json(results)

        elif path == "/api/download_results":
            if os.path.exists(CSV_PATH):
                self.send_response(200)
                self.send_header("Content-Type", "text/csv; charset=utf-8-sig")
                self.send_header("Content-Disposition", "attachment; filename=results.csv")
                self.end_headers()
                with open(CSV_PATH, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"No results record file found.")

        else:  # 預設回傳 HTML
            body = HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self.wfile.write(body)

    def do_POST(self):
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw)
        except Exception:
            payload = {}

        if path == "/api/generate":
            name  = payload.get("name", "")
            text  = payload.get("text", "").strip()
            voice = payload.get("voice", "zh-TW-HsiaoChenNeural")
            rate  = payload.get("rate", "+0%")
            if not text:
                self.send_json({"ok": False, "error": "文字為空"})
                return
            ok, msg = asyncio.run(gen_one(name, text, voice, rate))
            if ok:
                self.send_json({"ok": True, "size": msg})
            else:
                self.send_json({"ok": False, "error": msg})

        elif path == "/api/save_config":
            try:
                save_config(payload)
                self.send_json({"ok": True})
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, 500)

        elif path == "/api/clear_results":
            try:
                if os.path.exists(CSV_PATH):
                    os.remove(CSV_PATH)
                self.send_json({"ok": True})
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, 500)

        elif path == "/api/submit":
            # 處理來自 index.html 的本機提交
            csv_path = os.path.join(BASE_DIR, "results.csv")
            try:
                # 計算第 N 題的數量
                q_keys = sorted([k for k in payload.keys() if k.startswith('q')])
                
                # 檔案不存在則建標頭
                file_exists = os.path.exists(csv_path)
                with open(csv_path, "a", newline="", encoding="utf-8-sig") as f:
                    writer = csv.writer(f)
                    if not file_exists:
                        headers = ["時間戳記", "姓名", "答對題數", "得分"]
                        for i in range(1, len(q_keys) + 1):
                            headers.append(f"第{i}題")
                        writer.writerow(headers)
                    
                    correct_str = f"{payload.get('correctCount', 0)} / {payload.get('total', 0)}"
                    score_str = f"{payload.get('score', 0)} 分"
                    row = [
                        payload.get("timestamp", ""),
                        payload.get("name", ""),
                        correct_str,
                        score_str
                    ]
                    for k in q_keys:
                        row.append(payload[k])
                    writer.writerow(row)
                
                print(f"📥 [本機紀錄] 收到同仁 {payload.get('name')} 的測驗結果，已寫入 results.csv")
                self.send_json({"status": "ok", "message": "saved locally"})
            except Exception as e:
                self.send_json({"status": "error", "message": str(e)}, 500)

        else:
            self.send_json({"error": "not found"}, 404)

# ── 啟動 ──────────────────────────────────────────────────────
if __name__ == "__main__":
    os.chdir(BASE_DIR)
    srv = HTTPServer(("127.0.0.1", PORT), Handler)
    url = f"http://127.0.0.1:{PORT}"
    print(f"🎙  SOP 與題目管理伺服器已啟動")
    print(f"🌐  {url}")
    print(f"    關閉此視窗即可停止")
    threading.Timer(1.2, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止")
