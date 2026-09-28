const fs = require('fs');
const p = 'C:/GOOGLE ANGET/第二類_生產管理與API串接/QC-系統客製化電子化工廠/3_Cloudflare_D1版/functions/api/index.js';
let t = fs.readFileSync(p, 'utf8');

// Fix all garbled strings by replacing each broken line with correct content
const fixes = [
  // L105 - comment
  [/\/\/ [^\n]{0,30}Teams\n/, '// 取得原本樣品資訊，為了發送 Teams\n'],
  // L115 - finalNote condition
  [/if \(result === '[^']{0,20}' && sample\.qcResult === '[^']{0,20}'\) \{/, "if (result === '特採' && sample.qcResult === '需特採') {"],
  // L119 - comment
  [/\/\/ [^\n]{0,30}completedAt\n/, '// 若已有紀錄，不覆蓋原來的 completedAt\n'],
  // L125 - comment
  [/\/\/ [^\n]{0,30}\(FAIL\)[^\n]{0,30}\n/, '// 如果是不合格(FAIL)，自動產生下一輪重送排程\n'],
  // L137 - comment
  [/\/\/ [^\x20-\x7E]\n/, '// 通知 Teams\n'],
  // L141 - isPass line
  [/const isPass = \(status === 'completed' \|\| result === 'PASS' \|\| result\.includes\('[^']{0,30}'\)\);/, "const isPass = (status === 'completed' || result === 'PASS' || result === '特採');"],
  // L143 - FAIL resultTitle
  [/if \(result === 'FAIL'\) resultTitle = '[^']{0,60}';/, "if (result === 'FAIL') resultTitle = '⛔ FAIL (已自動產生下一次重送排程)';"],
  // L144 - 需特採 resultTitle
  [/else if \(result === '[^']{0,15}'\) resultTitle = '[^']{0,60}';/, "else if (result === '需特採') resultTitle = '⚠️ 不符合內控 (等待主管審核特採)';"],
  // L145 - 特採 resultTitle
  [/else if \(result === '[^']{0,10}'\) resultTitle = '[^']{0,60}';/, "else if (result === '特採') resultTitle = '🚨 經主管特採放行';"],
  // L148-149 title
  [/`[^\x20-\x7E]{0,8}【[^\x20-\x7E]{0,8}】\$\{sample\.productName\}`/, '`✅【檢驗完成】${sample.productName}`'],
  [/: `[^\x20-\x7E]{0,8}【[^\x20-\x7E]{0,8}】\$\{sample\.productName\}`;/, ': `❌【檢驗未通過】${sample.productName}`;'],
  // L154 - facts names
  [/\{ name: '[^\x20-\x7E]{0,6}', value: `\*\*\$\{resultTitle\}\*\*` \}/, "{ name: '檢驗結果', value: `**${resultTitle}**` }"],
  [/\{ name: '[^\x20-\x7E]{0,6}', value: actualApprover \}/, "{ name: '審核人員', value: actualApprover }"],
  [/\{ name: '[^\x20-\x7E]{0,6}', value: `\$\{sample\.tankNo \|\| '-'\} \/ \$\{sample\.customer \|\| '-'\}` \}/, "{ name: '槽號/車牌', value: `${sample.tankNo || '-'} / ${sample.customer || '-'}` }"],
  [/\{ name: '[^\x20-\x7E]{0,6}', value: finalNote \|\| '[^\x20-\x7E]{0,4}' \}/, "{ name: '檢驗備註', value: finalNote || '無' }"],
  // L166 - activitySubtitle
  [/"activitySubtitle": "[^\x20-\x7E]{0,10}"/, '"activitySubtitle": "QC 品管系統"'],
  // L184 - returnResample status
  [/result === "[^\x20-\x7E]{0,10}" \|\| result === "[^\x20-\x7E]{0,10}"/, 'result === "退件" || result === "重取樣"'],
  // L306 - returnResample note validation
  [/return new Response\(JSON\.stringify\(\{ success: false, error: '[^\x20-\x7E]{0,30}'\}\)/, "return new Response(JSON.stringify({ success: false, error: '退回備註不能為空' })"],
  // L312 - not found error
  [/return new Response\(JSON\.stringify\(\{ success: false, error: '[^\x20-\x7E]{0,30}'\}\), \{ headers: h \}\);$/, "return new Response(JSON.stringify({ success: false, error: '找不到該樣品記錄' }), { headers: h });"],
  // L321 - bind note
  [/bind\(note \|\| '[^\x20-\x7E]{0,30}'/, "bind(note || '送樣不合格，請確認退回原因'"],
];

for (const [pattern, replacement] of fixes) {
  t = t.replace(pattern, replacement);
}

fs.writeFileSync(p, t, 'utf8');

// Verify PUA remaining
const bad = t.match(/[\ue000-\uf8ff]/g);
console.log('PUA chars remaining:', bad ? bad.length : 0);

// Show key lines
const lines = t.split('\n');
[104,141,143,144,145,147,148,153,154,155,157,158,165,183].forEach(i => {
  if (lines[i]) console.log(`L${i+1}: ${lines[i].trim().substring(0,100)}`);
});
console.log('Done');
