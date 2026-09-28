const fs = require('fs');
const p = 'C:/GOOGLE ANGET/第二類_生產管理與API串接/QC-系統客製化電子化工廠/3_Cloudflare_D1版/index.html';
let html = fs.readFileSync(p, 'utf8');

const oldStr = "filteredOrders = t100Orders.filter(o => !getOrderSubmissionInfo(o));";
const newStr = `filteredOrders = t100Orders.filter(o => {
        const sub = getOrderSubmissionInfo(o);
        if (!sub) return true;
        if (sub.status === 'failed') return true;
        if (sub.status === 'pending' && (sub.round > 1 || sub.parentId)) return true;
        return false;
      });`;

// Fix the mark as well
const oldMark = `let mark = '⏳[待送樣] ';
          if (sub) {
            if (sub.status === 'completed') mark = '✅[已驗合格] ';
            else if (sub.status === 'failed') mark = '⛔[被退件需重送] ';
            else mark = '✅[已送樣待驗] ';
          }`;
          
const newMark = `let mark = '⏳[待送樣] ';
          if (sub) {
            if (sub.status === 'completed') mark = '✅[已驗合格] ';
            else if (sub.status === 'failed' && sub.qcResult === '需特採') mark = '⚠️[不符內控需特採] ';
            else if (sub.status === 'failed') mark = '⛔[被退件需重送] ';
            else if (sub.status === 'pending' && (sub.round > 1 || sub.parentId)) mark = '🔄[已自動重送待驗] ';
            else mark = '✅[已送樣待驗] ';
          }`;

if (html.includes(oldStr)) {
  html = html.replace(oldStr, newStr);
  console.log('Patched D1 T100 filter');
} else {
  console.log('Filter not found');
}

if (html.includes(oldMark)) {
  html = html.replace(oldMark, newMark);
  console.log('Patched D1 T100 mark');
} else {
  console.log('Mark not found, checking for existing mark...');
  const idx = html.indexOf("let mark = '⏳");
  if(idx >= 0) console.log('Found at:', idx, html.substring(idx, idx+200));
}

fs.writeFileSync(p, html, 'utf8');
const bad = html.match(/[\ue000-\uf8ff]/g);
console.log('PUA remaining:', bad ? bad.length : 0);
console.log('Has 已自動重送:', html.includes('已自動重送待驗'));
