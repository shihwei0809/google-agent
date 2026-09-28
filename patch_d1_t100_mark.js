const fs = require('fs');
const p = 'C:/GOOGLE ANGET/第二類_生產管理與API串接/QC-系統客製化電子化工廠/3_Cloudflare_D1版/index.html';
let html = fs.readFileSync(p, 'utf8');

// Fix the existing (partial) mark to the full updated one
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

// Find exact position by searching with actual line content
const idx = html.indexOf("let mark = '⏳[待送樣] ';\r\n          if (sub) {\r\n            if (sub.status === 'completed') mark = '✅[已驗合格] ';\r\n            else if (sub.status === 'failed') mark = '⛔[被退件需重送] ';\r\n            else mark = '✅[已送樣待驗] ';\r\n          }");

if (idx >= 0) {
  html = html.replace("let mark = '⏳[待送樣] ';\r\n          if (sub) {\r\n            if (sub.status === 'completed') mark = '✅[已驗合格] ';\r\n            else if (sub.status === 'failed') mark = '⛔[被退件需重送] ';\r\n            else mark = '✅[已送樣待驗] ';\r\n          }", newMark);
  fs.writeFileSync(p, html, 'utf8');
  console.log('Patched mark - CRLF');
  console.log('Has 已自動重送:', html.includes('已自動重送待驗'));
} else {
  // try LF
  const idx2 = html.indexOf("let mark = '⏳[待送樣] ';\n          if (sub) {\n            if (sub.status === 'completed') mark = '✅[已驗合格] ';\n            else if (sub.status === 'failed') mark = '⛔[被退件需重送] ';\n            else mark = '✅[已送樣待驗] ';\n          }");
  if (idx2 >= 0) {
    html = html.replace("let mark = '⏳[待送樣] ';\n          if (sub) {\n            if (sub.status === 'completed') mark = '✅[已驗合格] ';\n            else if (sub.status === 'failed') mark = '⛔[被退件需重送] ';\n            else mark = '✅[已送樣待驗] ';\n          }", newMark);
    fs.writeFileSync(p, html, 'utf8');
    console.log('Patched mark - LF');
    console.log('Has 已自動重送:', html.includes('已自動重送待驗'));
  } else {
    console.log('Could not find mark');
    // show surrounding area
    const start = html.indexOf("let mark = '");
    console.log(JSON.stringify(html.substring(start, start+300)));
  }
}
