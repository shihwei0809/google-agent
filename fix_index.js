const fs = require('fs');
const p = 'C:/GOOGLE ANGET/第二類_生產管理與API串接/QC-系統客製化電子化工廠/3_Cloudflare_D1版/functions/api/index.js';
let t = fs.readFileSync(p, 'utf8');

// Fix garbled '需特採' in status check
t = t.replace(/result === "FAIL" \|\| result === "[^"]{1,20}"/, 'result === "FAIL" || result === "需特採"');
// Fix garbled '特採' and '需特採' in finalNote condition
t = t.replace(/result === '([^'\u0000-\x7F]{1,10})' && sample\.qcResult === '([^'\u0000-\x7F]{1,10})'/, "result === '特採' && sample.qcResult === '需特採'");
// Fix garbled prefixes in template literal
t = t.replace(/`\[[^[\]]{0,8}:\$\{sample\.qcApprover\}\]/, '`[初驗:${sample.qcApprover}]');
t = t.replace(/\[[^[\]]{0,8}:\$\{approver\}\]/, '[特採:${approver}]');

fs.writeFileSync(p, t, 'utf8');

// Verify key lines
const lines = t.split('\n');
lines.forEach((l, i) => {
  if (l.includes('status = "failed"') || l.includes('finalNote') || l.includes('特採')) {
    if (i > 105 && i < 125) console.log(`Line ${i+1}: ${l.trim()}`);
  }
});
console.log('Done');
