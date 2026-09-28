const fs = require('fs');

const dirs = ['1_Web_網頁版', '2_PWA_App版', '3_Cloudflare_D1版'];
const base = 'C:/GOOGLE ANGET/第二類_生產管理與API串接/QC-系統客製化電子化工廠/';

dirs.forEach(dir => {
  const suffix = dir === '1_Web_網頁版' ? 'Index.html' : 'index.html';
  const p = base + dir + '/' + suffix;
  if (!fs.existsSync(p)) { console.log('Not found:', p); return; }
  let html = fs.readFileSync(p, 'utf8');

  // Replace the buggy resampleCount calculation
  const oldBadCount = `    // 取樣重送數量（品質不合格 + 需特採 + 自動重送待驗）
    const resampleCount = [
      ...((typeof cData !== 'undefined' ? cData : []).filter(c => c.status === 'failed')),
      ...((typeof allData !== 'undefined' ? allData : []).filter(c => c.status === 'pending' && parseInt(c.round || 1) > 1))
    ].length;`;

  const newBadCount = `    // 取樣重送數量 - 直接從 t100Orders 的送樣狀態計算（不依賴 render() 的局部變數）
    const resampleCount = (!t100Orders || !Array.isArray(t100Orders)) ? 0 : t100Orders.filter(o => {
      const sub = getOrderSubmissionInfo(o);
      return sub && (sub.status === 'failed' || (sub.status === 'pending' && (parseInt(sub.round || 1) > 1 || sub.parentId)));
    }).length;`;

  if (html.includes(oldBadCount)) {
    html = html.replace(oldBadCount, newBadCount);
    console.log(dir + ': Fixed resampleCount');
  } else {
    // Also try CRLF version
    const oldBadCRLF = oldBadCount.replace(/\n/g, '\r\n');
    if (html.includes(oldBadCRLF)) {
      html = html.replace(oldBadCRLF, newBadCount);
      console.log(dir + ': Fixed resampleCount (CRLF)');
    } else {
      console.log(dir + ': Not found, trying partial...');
      const partial = `typeof cData !== 'undefined' ? cData : []).filter(c => c.status === 'failed')`;
      if (html.includes(partial)) {
        // find the entire const resampleCount = [...].length; block and replace
        const startStr = `    // 取樣重送數量`;
        const endStr = `].length;`;
        const startIdx = html.indexOf(startStr);
        if (startIdx >= 0) {
          const endIdx = html.indexOf(endStr, startIdx) + endStr.length;
          html = html.substring(0, startIdx) + newBadCount + html.substring(endIdx);
          console.log(dir + ': Fixed via index');
        }
      }
    }
  }

  fs.writeFileSync(p, html, 'utf8');
  const bad = html.match(/[\ue000-\uf8ff]/g);
  const hasfix = html.includes('getOrderSubmissionInfo(o);\n      return sub && (sub.status');
  console.log(dir + ' PUA:', bad ? bad.length : 0, '| fixed:', hasfix || html.includes('sub.status === \'failed\' || (sub.status'));
});
