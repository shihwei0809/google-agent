const fs = require('fs');
const p = 'C:/GOOGLE ANGET/第二類_生產管理與API串接/QC-系統客製化電子化工廠/3_Cloudflare_D1版/functions/api/index.js';
const t = fs.readFileSync(p, 'utf8');
const lines = t.split('\n');

lines[181] = '      if (result === "退件" || result === "重取樣") status = "failed";';
lines[259] = '            "activitySubtitle": `樣品待檢驗已超過 ${alertLevel === 2 ? \'4\' : \'2\'} 小時未判定，請盡速處理！`,';
lines[261] = '            "facts": [{ "name": "🏢 樣品單位", "value": `${s.dept} (送樣人: ${s.requester || \'無\'})` },';
lines[286] = '        // 更新警告狀態';
lines[309] = '        return new Response(JSON.stringify({ success: false, error: \'找不到該筆樣品紀錄\' }), { headers: h });';
lines[318] = '      `).bind(note || \'檢驗判定不合格，退回重新送樣\', nowStr, id).run();';
lines[320] = '      // 4. 新增退回重新送樣記錄';

fs.writeFileSync(p, lines.join('\n'), 'utf8');
console.log('Fixed by line numbers');
