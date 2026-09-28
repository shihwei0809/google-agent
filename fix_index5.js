const fs = require('fs');
const p = 'C:/GOOGLE ANGET/第二類_生產管理與API串接/QC-系統客製化電子化工廠/3_Cloudflare_D1版/functions/api/index.js';
let t = fs.readFileSync(p, 'utf8');
const lines = t.split('\n');

const fixes = [
  [/if \(result === "[^\x20-\x7E]{0,10}" \|\| result === "[^\x20-\x7E]{0,10}"\) status = "failed";/, 'if (result === "退件" || result === "重取樣") status = "failed";'],
  [/\/\/ [\s\S]*?(?=\/\/ \d+\. 檢查 PIN|\/\/ 1\. 檢查)/g, ''], // too hard, just do it line by line
];

for (let i = 0; i < lines.length; i++) {
  if (lines[i].includes('if (result === "?€隞?') || /result === "[^\x20-\x7E]{1,10}" \|\| result === "[^\x20-\x7E]{1,10}"/.test(lines[i])) {
    lines[i] = '      if (result === "退件" || result === "重取樣") status = "failed";';
  }
  if (lines[i].includes('// 蝣箔?鞈?銵典??其蒂?芸??湔蝯?')) lines[i] = '    // 匯入 T100 排程並自動建立新單據';
  if (lines[i].includes('// 皜征??蝔?')) lines[i] = '      // 檢查重複排程';
  if (lines[i].includes('// ?寞活撖怠?唳?蝔?')) lines[i] = '      // 批次插入新排程';
  if (lines[i].includes('// 蝣箔?鞈?銵典??其誑?脣??芸?憪?')) lines[i] = '    // 匯入 T100 排程以同步資料庫';
  if (lines[i].includes('// ?? Teams Webhook 閮剖?')) lines[i] = '      // 取得 Teams Webhook 設定';
  if (lines[i].includes('// 閮??典?????嚗???撠???')) lines[i] = '      // 計算是否超過檢驗時效，發送警告通知';
  if (lines[i].includes('alertTitle = `??C ?湧?頞?霅血')) lines[i] = '          alertTitle = `🔴【QC 嚴重超時警告】等待檢驗已達 ${s.diffHours.toFixed(1)} 小時 (超過4小時)`;';
  if (lines[i].includes('alertTitle = `???C 瑼ａ?頞?霅血')) lines[i] = '          alertTitle = `⚠️【QC 檢驗超時警告】等待檢驗已達 ${s.diffHours.toFixed(1)} 小時 (超過2小時)`;';
  if (lines[i].includes('"activitySubtitle": `璅??瑼ａ?撌脤€?${alertLevel === 2 ? \'4\' : \'2\'} 撠??芸摰?隢?蝞∟?')) lines[i] = '            "activitySubtitle": `樣品待檢驗已超過 ${alertLevel === 2 ? \'4\' : \'2\'} 小時未判定，請盡速處理！`,';
  if (lines[i].includes('{ "name": "? ?見?桐?", "value": `${s.dept}嚗€見鈭綽?${s.requester || \'??}嚗 },')) lines[i] = '            "facts": [{ "name": "🏢 樣品單位", "value": `${s.dept} (送樣人: ${s.requester || \'無\'})` },';
  if (lines[i].includes('{ "name": "?妒 瑼ａ???", "value": s.productName },')) lines[i] = '            { "name": "🧪 檢驗品名", "value": s.productName },';
  if (lines[i].includes('{ "name": "?儭?瑽質? / 頠?", "value": `${s.tankNo || \'-\'} / ${s.customer || \'-\'}`')) lines[i] = '            { "name": "🚚 槽號 / 車牌", "value": `${s.tankNo || \'-\'} / ${s.customer || \'-\'}` },';
  if (lines[i].includes('{ "name": "???見??", "value": s.createdAt }')) lines[i] = '            { "name": "⏰ 送樣時間", "value": s.createdAt }';
  if (lines[i].includes('// ?湔霅血??€??')) lines[i] = '        // 更新警告狀態';
  if (lines[i].includes('// 1. 撽? PIN')) lines[i] = '      // 1. 檢查 PIN';
  if (lines[i].includes('return new Response(JSON.stringify({ success: false, error: \'蝟餌絞甈?撖Ⅳ?航炊嚗??頛')) lines[i] = '        return new Response(JSON.stringify({ success: false, error: \'系統預設密碼錯誤，請重新輸入\' }), { headers: h });';
  if (lines[i].includes('// 2. ?脣?????')) lines[i] = '      // 2. 取得原記錄';
  if (lines[i].includes('return new Response(JSON.stringify({ success: false, error: \'?曆??啗府蝑€見蝝€??\' }')) lines[i] = '        return new Response(JSON.stringify({ success: false, error: \'找不到該筆樣品紀錄\' }), { headers: h });';
  if (lines[i].includes('// 3. ?湔????(failed)')) lines[i] = '      // 3. 更新原記錄 (failed)';
  if (lines[i].includes('`).bind(note || \'???文?銝??潘??€???圈€見\', nowStr, id).run();')) lines[i] = '      `).bind(note || \'檢驗判定不合格，退回重新送樣\', nowStr, id).run();';
  if (lines[i].includes('// 4. ?啣??€??????')) lines[i] = '      // 4. 新增退回重新送樣記錄';
}

fs.writeFileSync(p, lines.join('\n'), 'utf8');

const bad = lines.join('\n').match(/[\ue000-\uf8ff]/g);
console.log('PUA chars remaining:', bad ? bad.length : 0);
