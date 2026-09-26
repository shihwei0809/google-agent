from pathlib import Path
import base64
import io
from PIL import Image


ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "AI_Agent簡報_正式生圖版"
IMG_DIR = OUT_DIR / "type2_v8_fresh_generated_plates"
OUT = OUT_DIR / "AI_Agent簡報_類型3_HTML_正式生圖版_v3_SOIL互動重做.html"


def img_uri(path: Path, max_w: int = 1280, quality: int = 82) -> str:
    img = Image.open(path).convert("RGB")
    if img.width > max_w:
        h = int(img.height * max_w / img.width)
        img = img.resize((max_w, h), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def load_images():
    paths = [IMG_DIR / f"page_{i:02d}_fresh_plate.png" for i in range(1, 13)]
    missing = [str(p) for p in paths if not p.exists()]
    if missing:
        raise SystemExit("Missing images: " + ", ".join(missing))
    return [img_uri(p) for p in paths]


def main():
    imgs = load_images()
    css = r"""
:root{
  --bg:#0a0e27; --bg-2:#11163a;
  --ink:#eef3ff; --ink-2:#b8c5e0; --ink-3:#7a8bb8; --ink-4:#4a5680;
  --accent:#00d4ff; --accent-2:#ff006e; --gold:#ffb800; --good:#00ff88;
  --t1:55px; --t2:34px; --t3:21px; --t4:13px;
  --s1:80px; --s2:48px; --s3:24px; --s4:12px;
}
*{box-sizing:border-box}
html,body{width:100%;height:100%;margin:0;overflow:hidden;background:var(--bg);color:var(--ink);font-family:"Noto Sans TC","Microsoft JhengHei",sans-serif}
button,th{font-family:inherit}
#progress{position:fixed;left:0;top:0;height:3px;background:linear-gradient(90deg,var(--accent),var(--accent-2));z-index:100;transition:width .35s ease}
#section-tag{position:fixed;top:18px;left:24px;color:var(--ink-3);font:700 var(--t4) "JetBrains Mono",monospace;letter-spacing:.12em;z-index:100}
#pageInfo{position:fixed;right:24px;bottom:18px;color:var(--ink-3);font:700 var(--t4) "JetBrains Mono",monospace;z-index:100}
#hint{position:fixed;left:24px;bottom:18px;color:var(--ink-4);font-size:var(--t4);z-index:100}
.slide{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;padding:80px 100px;opacity:0;pointer-events:none;transform:translateY(16px);transition:opacity .55s ease,transform .55s ease;overflow:hidden}
.slide.active{opacity:1;pointer-events:auto;transform:translateY(0)}
.slide-inner{width:100%;max-width:1320px;position:relative;z-index:2}
.full-img{position:absolute;inset:0;z-index:0}.full-img img{width:100%;height:100%;object-fit:cover;opacity:.72}.full-img:after{content:"";position:absolute;inset:0;background:linear-gradient(90deg,rgba(10,14,39,.88),rgba(10,14,39,.52) 48%,rgba(10,14,39,.22))}
.kicker{display:inline-block;color:var(--accent);font:700 var(--t4) "JetBrains Mono",monospace;letter-spacing:.2em;margin-bottom:var(--s4);padding:6px 12px;border:1px solid rgba(0,212,255,.65);border-radius:4px;background:rgba(10,14,39,.35)}
h1{font-size:var(--t1);line-height:1.1;margin:0;font-weight:900;letter-spacing:0} h2{font-size:var(--t2);line-height:1.25;margin:0;font-weight:800}
.lead{font-size:var(--t3);line-height:1.72;color:var(--ink-2);max-width:760px;margin:var(--s3) 0 0}
.gradient{background:linear-gradient(135deg,var(--accent),var(--accent-2));-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.big-question{text-align:center}.big-question h1{font-size:70px}.big-question .lead{margin-left:auto;margin-right:auto}
.split{display:grid;grid-template-columns:1fr 1fr;gap:var(--s2);align-items:center}.split.flip .text{order:1}.split.flip .split-img{order:2}
.split-img{position:relative;aspect-ratio:16/10;border-radius:18px;overflow:hidden;box-shadow:0 30px 80px rgba(0,212,255,.18),0 0 0 1px rgba(255,255,255,.08)}.split-img img{width:100%;height:100%;object-fit:cover}.img-tag{position:absolute;top:16px;left:16px;background:rgba(10,14,39,.82);color:var(--accent);padding:6px 12px;border-radius:6px;font:700 11px "JetBrains Mono",monospace;letter-spacing:.1em}
.list{list-style:none;margin:var(--s3) 0 0;padding:0}.list li{font-size:20px;color:var(--ink);line-height:1.45;padding:12px 0;border-top:1px solid rgba(184,197,224,.25)}
.three-col{display:grid;grid-template-columns:repeat(3,1fr);gap:var(--s3);margin-top:var(--s2)}
.type-card,.choice-card,.soil-step{background:rgba(255,255,255,.035);border:1px solid rgba(255,255,255,.09);border-radius:8px;padding:22px;backdrop-filter:blur(10px)}
.type-card{cursor:pointer;transition:transform .25s ease,border-color .25s ease,background .25s ease}.type-card:hover{transform:translateY(-6px);border-color:var(--accent);background:rgba(0,212,255,.07)}
.card-img{aspect-ratio:16/10;border-radius:8px;overflow:hidden;margin-bottom:18px;background:var(--bg-2)}.card-img img{width:100%;height:100%;object-fit:cover}
.badge{display:inline-block;font:800 var(--t4) "JetBrains Mono",monospace;color:var(--bg);background:var(--accent);padding:4px 10px;border-radius:4px;margin-bottom:12px}.type-card:nth-child(2) .badge{background:var(--accent-2)}.type-card:nth-child(3) .badge{background:var(--gold)}
.type-card h3,.choice-card h3,.soil-step h3{font-size:24px;margin:0 0 10px}.type-card p,.choice-card p,.soil-step p{font-size:16px;line-height:1.6;color:var(--ink-2);margin:0}
.compare-layout{display:grid;grid-template-columns:.85fr 1.15fr;gap:var(--s2);align-items:center}.support-img{border-radius:16px;overflow:hidden;box-shadow:0 30px 80px rgba(255,0,110,.14)}.support-img img{width:100%;height:100%;object-fit:cover}
table.compare{width:100%;border-collapse:collapse;margin-top:var(--s3);font-size:18px}table.compare th,table.compare td{padding:15px 16px;text-align:left;border-bottom:1px solid rgba(255,255,255,.08)}table.compare th{color:var(--accent);font:800 13px "JetBrains Mono",monospace;letter-spacing:.1em;cursor:pointer;user-select:none}table.compare th:hover{color:var(--accent-2)}table.compare tr:hover td{background:rgba(0,212,255,.045)}.yes{color:var(--good);font-weight:900}.no{color:var(--ink-4)}.mid{color:var(--gold);font-weight:900}
.chart-wrap{height:440px;margin-top:var(--s3);padding:20px;border-radius:14px;background:rgba(255,255,255,.035);border:1px solid rgba(255,255,255,.08)}
.tree-wrap{position:relative;margin-top:var(--s2);height:420px}.tree-lines{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}.question-node{position:absolute;left:50%;top:0;transform:translateX(-50%);width:360px;text-align:center;border:1px solid rgba(0,212,255,.7);border-radius:10px;padding:20px;background:rgba(10,14,39,.82);box-shadow:0 0 36px rgba(0,212,255,.15)}.choice-card{position:absolute;top:230px;width:31%;cursor:pointer;transition:.25s}.choice-card:hover{border-color:var(--accent);transform:translateY(-5px)}.choice-card.a{left:0}.choice-card.b{left:34.5%}.choice-card.c{right:0}.tree-result{margin-top:14px;color:var(--ink-2);font-size:18px}
.soil-flow{display:grid;grid-template-columns:repeat(3,1fr);gap:var(--s4);margin-top:var(--s2)}.soil-step{border-top:3px solid var(--accent)}.soil-step:nth-child(2n){border-top-color:var(--accent-2)}.soil-step .num{font:900 var(--t4) "JetBrains Mono",monospace;color:var(--accent);letter-spacing:.1em}
.closing{text-align:left;max-width:850px}.closing .answer{font-size:64px;line-height:1.14;font-weight:900;margin:18px 0}.cta{display:inline-flex;align-items:center;margin-top:var(--s3);padding:14px 22px;border:1px solid rgba(0,212,255,.65);border-radius:999px;color:var(--ink);background:rgba(0,212,255,.08);font-size:20px;font-weight:800}
@media(max-width:900px){.slide{padding:48px 24px}.slide-inner{max-width:none}h1{font-size:38px}.big-question h1,.closing .answer{font-size:42px}.lead{font-size:17px}.split,.compare-layout,.three-col,.soil-flow{grid-template-columns:1fr}.split.flip .text,.split.flip .split-img{order:initial}.tree-wrap{height:auto;display:grid;gap:14px}.tree-lines{display:none}.question-node,.choice-card{position:static;transform:none;width:auto}.choice-card:hover{transform:none}.chart-wrap{height:340px}}
"""
    js = r"""
const slides=[...document.querySelectorAll('.slide')];
let cur=0, chartBuilt=false;
const progressBar=document.getElementById('progress');
const sectionTagEl=document.getElementById('section-tag');
const pageInfoEl=document.getElementById('pageInfo');
const treeResultEl=document.getElementById('treeResult');
function goto(n){
  cur=Math.max(0,Math.min(slides.length-1,n-1));
  slides.forEach((s,i)=>s.classList.toggle('active',i===cur));
  progressBar.style.width=((cur+1)/slides.length*100)+'%';
  sectionTagEl.textContent='— '+slides[cur].dataset.section+' —';
  pageInfoEl.textContent=String(cur+1).padStart(2,'0')+' / '+String(slides.length).padStart(2,'0');
  if(cur===8 && !chartBuilt) buildChart();
}
function next(){goto(cur+2)} function prev(){goto(cur)}
addEventListener('keydown',e=>{
  if(['ArrowRight',' ','PageDown'].includes(e.key)){e.preventDefault();next()}
  if(['ArrowLeft','PageUp'].includes(e.key)){e.preventDefault();prev()}
  if(e.key.toLowerCase()==='f')document.documentElement.requestFullscreen?.()
});
addEventListener('click',e=>{
  if(e.target.closest('button,th,.type-card,.choice-card,.split-img,.support-img'))return;
  if(e.clientX>innerWidth*.7)next();
  if(e.clientX<innerWidth*.3)prev();
});
function sortTable(col){
  const body=document.querySelector('#compareBody');
  const rows=[...body.rows].sort((a,b)=>a.cells[col].textContent.localeCompare(b.cells[col].textContent,'zh-Hant',{numeric:true}));
  body.replaceChildren(...rows);
}
function choose(text){treeResultEl.textContent=text}
function buildChart(){
  chartBuilt=true;
  new Chart(document.getElementById('radarChart'),{
    type:'radar',
    data:{
      labels:['視覺衝擊','可編輯','互動性','製作速度','長期維護','分享便利'],
      datasets:[
        {label:'類型 1 純圖片',data:[5,1,1,5,2,3],borderColor:'#00d4ff',backgroundColor:'rgba(0,212,255,.18)',pointBackgroundColor:'#00d4ff'},
        {label:'類型 2 可編輯',data:[4,5,2,3,5,3],borderColor:'#ffb800',backgroundColor:'rgba(255,184,0,.15)',pointBackgroundColor:'#ffb800'},
        {label:'類型 3 HTML',data:[4,4,5,3,4,5],borderColor:'#ff006e',backgroundColor:'rgba(255,0,110,.16)',pointBackgroundColor:'#ff006e'}
      ]
    },
    options:{
      responsive:true,maintainAspectRatio:false,
      plugins:{legend:{labels:{color:'#eef3ff',font:{size:14,family:'Noto Sans TC'}}}},
      scales:{r:{min:0,max:5,ticks:{display:false,stepSize:1},grid:{color:'rgba(184,197,224,.18)'},angleLines:{color:'rgba(184,197,224,.2)'},pointLabels:{color:'#b8c5e0',font:{size:14,family:'Noto Sans TC'}}}}
    }
  });
}
goto(1);
"""
    html = f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI Agent 時代的簡報最終解答｜HTML 互動版</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700;900&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>{css}</style>
</head>
<body>
<div id="progress"></div>
<div id="section-tag"></div>
<div id="pageInfo"></div>
<div id="hint">← → 切頁　|　F 全螢幕　|　點右側前進</div>
<main id="deck">
  <section class="slide active" data-slide="1" data-section="引起動機">
    <div class="full-img"><img src="{imgs[0]}" alt=""></div>
    <div class="slide-inner closing">
      <span class="kicker">2026 LIVE · AI AGENT</span>
      <h1>簡報的最終解答</h1>
      <p class="lead">AI Agent 時代，三種重新定義簡報的路徑。</p>
      <div class="answer gradient">Image 2 × PowerPoint × HTML</div>
    </div>
  </section>
  <section class="slide" data-slide="2" data-section="引起動機">
    <div class="full-img"><img src="{imgs[1]}" alt=""></div>
    <div class="slide-inner big-question">
      <span class="kicker">PROBLEM</span>
      <h1>你還在為簡報<br><span class="gradient">熬夜到凌晨三點嗎？</span></h1>
      <p class="lead">問題不是你不夠努力，而是工具的時代已經換了。</p>
    </div>
  </section>
  <section class="slide" data-slide="3" data-section="引起動機">
    <div class="full-img"><img src="{imgs[2]}" alt=""></div>
    <div class="slide-inner">
      <span class="kicker">THESIS</span>
      <h1>簡報不再是工具<br><span class="gradient">而是 AI Agent 的輸出</span></h1>
      <p class="lead">過去我們服務 PowerPoint；現在，是 Agent 服務我們的想法。</p>
    </div>
  </section>
  <section class="slide" data-slide="4" data-section="維持注意">
    <div class="slide-inner">
      <span class="kicker">OVERVIEW · CLICKABLE</span>
      <h1>三種重新定義簡報的方式</h1>
      <div class="three-col">
        <article class="type-card" onclick="goto(5)"><div class="card-img"><img src="{imgs[4]}" alt=""></div><span class="badge">TYPE 01</span><h3>純圖片 .pptx</h3><p>每頁都是 AI 整頁生成的圖，視覺一次到位。</p></article>
        <article class="type-card" onclick="goto(6)"><div class="card-img"><img src="{imgs[5]}" alt=""></div><span class="badge">TYPE 02</span><h3>圖 + 可編輯文字</h3><p>AI 圖當底層，文字保留成 PowerPoint 物件。</p></article>
        <article class="type-card" onclick="goto(7)"><div class="card-img"><img src="{imgs[6]}" alt=""></div><span class="badge">TYPE 03</span><h3>HTML 簡報</h3><p>把簡報變成網頁，加入圖表、排序、互動。</p></article>
      </div>
    </div>
  </section>
  <section class="slide" data-slide="5" data-section="維持注意">
    <div class="slide-inner split">
      <div class="split-img"><span class="img-tag">TYPE 01 · IMAGE</span><img src="{imgs[4]}" alt=""></div>
      <div class="text"><span class="kicker">類型 1</span><h1>純圖片簡報</h1><p class="lead">每頁都是 Image 2 整頁生成，文字、視覺、構圖一次到位。</p><ul class="list"><li>✓ 視覺衝擊最強</li><li>✓ 文字精準度遠超 NotebookLM</li><li>✗ 文字燒在圖裡，無法後改</li></ul></div>
    </div>
  </section>
  <section class="slide" data-slide="6" data-section="維持注意">
    <div class="slide-inner split flip">
      <div class="split-img"><span class="img-tag">TYPE 02 · EDITABLE</span><img src="{imgs[5]}" alt=""></div>
      <div class="text"><span class="kicker">類型 2</span><h1>圖 + 可編輯文字</h1><p class="lead">AI 圖當視覺底層，文字獨立成 PowerPoint 物件，雙擊即改。</p><ul class="list"><li>✓ 保留圖像式視覺衝擊</li><li>✓ 同時擁有 PowerPoint 編輯彈性</li><li>✓ 適合企業 / 教學長期維護</li></ul></div>
    </div>
  </section>
  <section class="slide" data-slide="7" data-section="維持注意">
    <div class="slide-inner split">
      <div class="split-img"><span class="img-tag">TYPE 03 · HTML</span><img src="{imgs[6]}" alt=""></div>
      <div class="text"><span class="kicker">類型 3</span><h1>HTML 簡報</h1><p class="lead">用 HTML 模仿簡報邏輯，圖像由 Image 2 生成，排版與互動全由 JS 處理。</p><ul class="list"><li>✓ 自由度天花板</li><li>✓ 嵌圖表、影片、互動</li><li>✓ 一個 URL 跨裝置分享</li></ul></div>
    </div>
  </section>
  <section class="slide" data-slide="8" data-section="維持注意">
    <div class="slide-inner compare-layout">
      <div class="support-img"><img src="{imgs[7]}" alt=""></div>
      <div><span class="kicker">SORTABLE TABLE</span><h1>傳統 vs HTML</h1><p class="lead">點欄位標題排序，讓比較不是一張死圖。</p>
        <table class="compare"><thead><tr><th onclick="sortTable(0)">能力 ⇅</th><th onclick="sortTable(1)">傳統簡報 ⇅</th><th onclick="sortTable(2)">HTML 簡報 ⇅</th></tr></thead>
        <tbody id="compareBody"><tr><td>互動圖表</td><td class="no">不易</td><td class="yes">Chart.js / D3</td></tr><tr><td>跨裝置分享</td><td class="mid">常需轉檔</td><td class="yes">一個 URL</td></tr><tr><td>資料排序</td><td class="no">靜態</td><td class="yes">即時排序</td></tr><tr><td>影片 / 表單</td><td class="mid">有限</td><td class="yes">直接嵌入</td></tr></tbody></table></div>
    </div>
  </section>
  <section class="slide" data-slide="9" data-section="維持注意">
    <div class="slide-inner">
      <span class="kicker">DATA · LAZY CHART</span><h1>三種類型的能力強項</h1><p class="lead">這張雷達圖在進入本頁時才初始化，是真正的網頁互動元件。</p>
      <div class="chart-wrap"><canvas id="radarChart"></canvas></div>
    </div>
  </section>
  <section class="slide" data-slide="10" data-section="喚起行動">
    <div class="slide-inner">
      <span class="kicker">DECISION TREE</span><h1>問自己一個問題</h1><p class="lead">這份簡報之後還會改嗎？點一個答案。</p>
      <div class="tree-wrap">
        <svg class="tree-lines" viewBox="0 0 1200 420" preserveAspectRatio="none"><path d="M600 92 L190 230 M600 92 L600 230 M600 92 L1010 230" stroke="rgba(0,212,255,.55)" stroke-width="3" fill="none"/></svg>
        <div class="question-node"><h2>之後還會改嗎？</h2><div id="treeResult" class="tree-result">請選一個情境</div></div>
        <article class="choice-card a" onclick="choose('不會改：選 01 純圖片，最快拿到視覺衝擊。')"><h3>場景 A · 不會</h3><p>01 純圖片<br>soil-image-deck</p></article>
        <article class="choice-card b" onclick="choose('會改且要協作：選 02 可編輯，文字保留在 PowerPoint。')"><h3>場景 B · 會 + 協作</h3><p>02 可編輯<br>soil-teaching-deck</p></article>
        <article class="choice-card c" onclick="choose('會改且要互動：選 03 HTML，讓簡報變成網頁體驗。')"><h3>場景 C · 會 + 互動</h3><p>03 HTML<br>soil-html-deck</p></article>
      </div>
    </div>
  </section>
  <section class="slide" data-slide="11" data-section="喚起行動">
    <div class="slide-inner split">
      <div class="split-img"><span class="img-tag">SOIL · WORKFLOW</span><img src="{imgs[10]}" alt=""></div>
      <div><span class="kicker">SOIL ENGINE</span><h1>背後是 SOIL 六引擎</h1>
      <div class="soil-flow"><article class="soil-step"><span class="num">01</span><h3>概念定位</h3><p>抓主軸</p></article><article class="soil-step"><span class="num">02</span><h3>脈絡定位</h3><p>動機、注意、行動</p></article><article class="soil-step"><span class="num">03</span><h3>頁面架構</h3><p>每頁一任務</p></article><article class="soil-step"><span class="num">04</span><h3>認知編修</h3><p>降雜訊、區塊化</p></article><article class="soil-step"><span class="num">05</span><h3>風格建構</h3><p>字級與階層</p></article><article class="soil-step"><span class="num">06</span><h3>總導演</h3><p>整合 prompt</p></article></div></div>
    </div>
  </section>
  <section class="slide" data-slide="12" data-section="喚起行動">
    <div class="full-img"><img src="{imgs[11]}" alt=""></div>
    <div class="slide-inner closing">
      <span class="kicker">FINAL ANSWER</span><p class="lead">未來真正的簡報能力</p>
      <div class="answer">不是會用 PowerPoint<br><span class="gradient">而是知道該召喚哪個 Agent</span></div>
      <div class="cta">今晚就試試其中一種 →</div>
    </div>
  </section>
</main>
<script>{js}</script>
</body>
</html>"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
