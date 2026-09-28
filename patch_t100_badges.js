const fs = require('fs');

const dirs = ['1_Web_網頁版', '2_PWA_App版', '3_Cloudflare_D1版'];
const base = 'C:/GOOGLE ANGET/第二類_生產管理與API串接/QC-系統客製化電子化工廠/';

dirs.forEach(dir => {
  const suffix = dir === '1_Web_網頁版' ? 'Index.html' : 'index.html';
  const p = base + dir + '/' + suffix;
  if (!fs.existsSync(p)) { console.log('Not found:', p); return; }
  let html = fs.readFileSync(p, 'utf8');

  // Inject updateT100ButtonCounts() function after setT100FilterMode function
  // Find the end of setT100FilterMode by looking for the closing of the function
  const markerStr = `function setT100FilterMode(mode) {`;
  const idx = html.indexOf(markerStr);
  if (idx < 0) { console.log(dir + ': setT100FilterMode not found'); return; }

  // Find the closing brace of setT100FilterMode
  let depth = 0;
  let i = idx;
  while (i < html.length) {
    if (html[i] === '{') depth++;
    if (html[i] === '}') { depth--; if (depth === 0) { i++; break; } }
    i++;
  }

  const insertPos = i; // right after the closing }

  const newFunction = `

  // 更新 T100 篩選按鈕上的數量徽章
  function updateT100ButtonCounts() {
    if (!t100Orders || !Array.isArray(t100Orders)) return;
    const todayStr = new Date().toISOString().split('T')[0];

    // 今日排程數量
    const todayCount = t100Orders.filter(o => o.date === todayStr).length;
    const btnToday = document.getElementById('btnFilterToday');
    if (btnToday) btnToday.innerHTML = \`📅 今日排程 <span style="background:rgba(255,255,255,0.35);border-radius:10px;padding:1px 7px;font-size:0.8em;margin-left:3px;">\${todayCount}</span>\`;

    // 待送樣放櫃數量（未送或退回件）
    const pendingCount = t100Orders.filter(o => {
      const sub = getOrderSubmissionInfo(o);
      if (!sub) return true;
      if (sub.status === 'failed') return true;
      if (sub.status === 'pending' && (sub.round > 1 || sub.parentId)) return true;
      return false;
    }).length;
    const btnPending = document.getElementById('btnFilterPending');
    if (btnPending) btnPending.innerHTML = \`📦 待送樣放櫃 <span style="background:rgba(255,255,255,0.35);border-radius:10px;padding:1px 7px;font-size:0.8em;margin-left:3px;">\${pendingCount}</span>\`;

    // 取樣重送數量（品質不合格 + 需特採 + 自動重送待驗）
    const resampleCount = [
      ...((typeof cData !== 'undefined' ? cData : []).filter(c => c.status === 'failed')),
      ...((typeof allData !== 'undefined' ? allData : []).filter(c => c.status === 'pending' && parseInt(c.round || 1) > 1))
    ].length;
    const btnResample = document.getElementById('btnFilterResample');
    if (btnResample) {
      const badge = resampleCount > 0
        ? \`<span style="background:#dc2626;color:white;border-radius:10px;padding:1px 7px;font-size:0.8em;margin-left:3px;">\${resampleCount}</span>\`
        : \`<span style="background:rgba(255,255,255,0.35);border-radius:10px;padding:1px 7px;font-size:0.8em;margin-left:3px;">0</span>\`;
      btnResample.innerHTML = \`🔄 取樣重送 \${badge}\`;
    }
  }`;

  html = html.substring(0, insertPos) + newFunction + html.substring(insertPos);

  // Now call updateT100ButtonCounts() inside render() after data is available
  // Find where filteredOrders is set and cData is available - best spot: after cData is defined
  const callMarker = `let cData = filtered.filter(s => s.status === 'completed' || s.status === 'failed');`;
  const callMarkerCRLF = `let cData = filtered.filter(s => s.status === 'completed' || s.status === 'failed');\r\n`;
  
  if (html.includes(callMarker)) {
    html = html.replace(callMarker, callMarker + '\n    updateT100ButtonCounts();');
    console.log(dir + ': Injected updateT100ButtonCounts call');
  } else {
    // Try alternative
    const alt = `let cData = filtered.filter(s => s.status === 'completed' || s.status === 'failed');`;
    const altIdx = html.indexOf(alt);
    if (altIdx >= 0) {
      html = html.substring(0, altIdx + alt.length) + '\n    updateT100ButtonCounts();' + html.substring(altIdx + alt.length);
      console.log(dir + ': Injected (alt)');
    } else {
      console.log(dir + ': Could not find cData definition');
    }
  }

  fs.writeFileSync(p, html, 'utf8');
  const bad = html.match(/[\ue000-\uf8ff]/g);
  console.log(dir + ' PUA:', bad ? bad.length : 0, '| has updateT100:', html.includes('updateT100ButtonCounts'));
});
