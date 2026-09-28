const fs = require('fs');

const dirs = ['1_Web_網頁版', '2_PWA_App版', '3_Cloudflare_D1版'];
const base = 'C:/GOOGLE ANGET/第二類_生產管理與API串接/QC-系統客製化電子化工廠/';

dirs.forEach(dir => {
  const suffix = dir === '1_Web_網頁版' ? 'Index.html' : 'index.html';
  const p = base + dir + '/' + suffix;
  if (!fs.existsSync(p)) { console.log('Not found:', p); return; }
  let html = fs.readFileSync(p, 'utf8');

  // 1. Rename label in dropdown mark
  html = html.replaceAll('⛔[被退件需重送]', '⛔[品質不合格重取]');
  html = html.replaceAll('⛔[被退件需重送] ', '⛔[品質不合格重取] ');

  // 2. Rename in mark assignment (both CRLF and LF)
  html = html.replaceAll("mark = '⛔[被退件需重送] ';", "mark = '⛔[品質不合格重取] ';");
  html = html.replaceAll('mark = "⛔[被退件需重送] ";', 'mark = "⛔[品質不合格重取] ";');

  // 3. Add "取樣重送" tab button after "待送樣放櫃" button
  // Find the 待送樣放櫃 button pattern and add after it
  const oldBtnPending = `<button onclick="setT100Filter('pending')" id="btnT100Pending"`;
  if (html.includes(oldBtnPending)) {
    // find the closing > or end of the button and add a new button after
    const idx = html.indexOf('</button>', html.indexOf(oldBtnPending));
    if (idx >= 0) {
      const insertAfter = html.substring(0, idx + 9); // include </button>
      const insertNew = `
        <button onclick="setT100Filter('resample')" id="btnT100Resample"
          style="padding:6px 12px; border:none; border-radius:6px; cursor:pointer; font-size:0.85rem; background:#fef3c7; color:#92400e; font-weight:600;"
          title="顯示品質不合格需重取的單據">
          🔄 取樣重送
        </button>`;
      const rest = html.substring(idx + 9);
      html = insertAfter + insertNew + rest;
      console.log(dir + ': Added 取樣重送 button');
    }
  } else {
    console.log(dir + ': Could not find 待送樣放櫃 button');
  }

  // 4. Add resample filter logic in setT100Filter function
  // Find 'pending' filter case and add resample case after it
  const oldPendingFilter = `filteredOrders = t100Orders.filter(o => {
        const sub = getOrderSubmissionInfo(o);
        if (!sub) return true;
        if (sub.status === 'failed') return true;
        if (sub.status === 'pending' && (sub.round > 1 || sub.parentId)) return true;
        return false;
      });`;
  
  const newPendingFilter = `filteredOrders = t100Orders.filter(o => {
        const sub = getOrderSubmissionInfo(o);
        if (!sub) return true;
        if (sub.status === 'failed') return true;
        if (sub.status === 'pending' && (sub.round > 1 || sub.parentId)) return true;
        return false;
      });`;

  // Find the resample filter - add a new mode
  // We need to add an else if block for 'resample' mode
  const oldAll = `} else if (t100FilterMode === 'all') {`;
  const newResampleBlock = `} else if (t100FilterMode === 'resample') {
      // 品質不合格重取 / 需特採待審
      const failedSubs = cData.filter(c => c.status === 'failed');
      const pendingResample = allData.filter(c => c.status === 'pending' && parseInt(c.round || 1) > 1);
      filteredOrders = [...failedSubs, ...pendingResample].map(c => ({
        ...c,
        isResampleItem: true,
        displayTitle: (c.status === 'failed' && c.qcResult === '需特採') 
          ? \`⚠️[不符內控需特採] \${c.barcode} - \${c.productName} (\${c.tankNo || c.customer || '-'})\`
          : (c.status === 'failed')
          ? \`⛔[品質不合格重取] \${c.barcode} - \${c.productName} (\${c.tankNo || c.customer || '-'}) (第\${c.round}次)\`
          : \`🔄[已自動重送待驗] \${c.barcode} - \${c.productName} (\${c.tankNo || c.customer || '-'}) (第\${c.round}次)\`
      }));
      filterDescription = '品質不合格重取 / 需特採';
    } else if (t100FilterMode === 'all') {`;

  if (html.includes(oldAll)) {
    html = html.replace(oldAll, newResampleBlock);
    console.log(dir + ': Added resample filter block');
  } else {
    console.log(dir + ': Could not find all filter block');
  }

  // 5. Add button highlight logic for resample tab
  const oldHighlight = `document.getElementById('btnT100Pending').style.background = t100FilterMode === 'pending' ? '#059669' : '';
      document.getElementById('btnT100Pending').style.color = t100FilterMode === 'pending' ? 'white' : '';`;
  
  const newHighlight = `document.getElementById('btnT100Pending').style.background = t100FilterMode === 'pending' ? '#059669' : '';
      document.getElementById('btnT100Pending').style.color = t100FilterMode === 'pending' ? 'white' : '';
      const resampleBtn = document.getElementById('btnT100Resample');
      if (resampleBtn) {
        resampleBtn.style.background = t100FilterMode === 'resample' ? '#d97706' : '#fef3c7';
        resampleBtn.style.color = t100FilterMode === 'resample' ? 'white' : '#92400e';
      }`;
  
  if (html.includes(oldHighlight)) {
    html = html.replace(oldHighlight, newHighlight);
    console.log(dir + ': Added resample button highlight');
  } else {
    console.log(dir + ': Could not find highlight block');
  }

  fs.writeFileSync(p, html, 'utf8');
  const bad = html.match(/[\ue000-\uf8ff]/g);
  console.log(dir + ' done. PUA:', bad ? bad.length : 0);
});
