const fs = require('fs');

const dirs = ['1_Web_網頁版', '2_PWA_App版', '3_Cloudflare_D1版'];
const base = 'C:/GOOGLE ANGET/第二類_生產管理與API串接/QC-系統客製化電子化工廠/';

dirs.forEach(dir => {
  const suffix = dir === '1_Web_網頁版' ? 'Index.html' : 'index.html';
  const p = base + dir + '/' + suffix;
  if (!fs.existsSync(p)) { console.log('Not found:', p); return; }
  let html = fs.readFileSync(p, 'utf8');

  // 1. Add 🔄 取樣重送 button after 待送樣放櫃 button
  const oldPendingBtn = `<button type="button" class="btn-t100-filter" id="btnFilterPending" onclick="setT100FilterMode('pending')" title="查詢所有放櫃或未送樣車次">📦 待送樣放櫃</button>`;
  const newPendingBtn = `<button type="button" class="btn-t100-filter" id="btnFilterPending" onclick="setT100FilterMode('pending')" title="查詢所有放櫃或未送樣車次">📦 待送樣放櫃</button>
            <button type="button" class="btn-t100-filter" id="btnFilterResample" onclick="setT100FilterMode('resample')" title="顯示品質不合格需重取或待特採的單據">🔄 取樣重送</button>`;

  if (html.includes(oldPendingBtn)) {
    html = html.replace(oldPendingBtn, newPendingBtn);
    console.log(dir + ': Added 取樣重送 button');
  } else {
    // Try with \r\n
    const oldCRLF = oldPendingBtn.replace(/\n/g, '\r\n');
    if (html.includes(oldCRLF)) {
      html = html.replace(oldCRLF, newPendingBtn);
      console.log(dir + ': Added 取樣重送 button (CRLF)');
    } else {
      console.log(dir + ': button not found - checking actual text...');
      const idx = html.indexOf('btnFilterPending');
      if(idx>=0) console.log(JSON.stringify(html.substring(idx-10, idx+150)));
    }
  }

  // 2. Add button highlight for resample in setT100FilterMode
  const oldFilterMode = `document.querySelectorAll('.btn-t100-filter').forEach(b => b.classList.remove('active'));`;
  if (html.includes(oldFilterMode)) {
    // Add btnFilterResample activation after existing active logic
    const oldActive = `document.getElementById('btnFilter' + (mode.charAt(0).toUpperCase() + mode.slice(1)))`;
    // just add the resample to the CSS class approach - it should work automatically
    console.log(dir + ': filter mode uses class toggle, should work auto');
  }

  fs.writeFileSync(p, html, 'utf8');
  const bad = html.match(/[\ue000-\uf8ff]/g);
  console.log(dir + ' PUA:', bad ? bad.length : 0, '| has 取樣重送:', html.includes('取樣重送'));
});
