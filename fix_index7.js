const fs = require('fs');
const p = 'C:/GOOGLE ANGET/第二類_生產管理與API串接/QC-系統客製化電子化工廠/3_Cloudflare_D1版/functions/api/index.js';
const t = fs.readFileSync(p, 'utf8');
const lines = t.split('\n');

const correctBlock = `          const cardPayload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": alertLevel === 2 ? "990000" : "D9381E",
            "summary": alertTitle,
            "sections": [{
              "activityTitle": alertTitle,
              "activitySubtitle": \`樣品待檢驗已超過 \${alertLevel === 2 ? '4' : '2'} 小時未判定，請盡速處理！\`,
              "facts": [
                { "name": "🏢 樣品單位", "value": \`\${s.dept} (送樣人: \${s.requester || '無'})\` },
                { "name": "🧪 檢驗品名", "value": s.productName },
                { "name": "🚚 槽號 / 車牌", "value": \`\${s.tankNo || '-'} / \${s.customer || '-'}\` },
                { "name": "🏷️ 條碼資訊", "value": s.barcode || '-' },
                { "name": "⏰ 送樣時間", "value": s.createdAt }
              ],
              "markdown": true
            }]
          };`;

let newLines = [];
let skip = false;
for (let i = 0; i < lines.length; i++) {
  if (lines[i].includes('const cardPayload = {')) {
    skip = true;
    newLines.push(...correctBlock.split('\n'));
  }
  if (skip && lines[i].includes('};') && lines[i-1] && lines[i-1].includes('}]')) {
    skip = false;
    continue;
  }
  if (!skip) {
    newLines.push(lines[i]);
  }
}

fs.writeFileSync(p, newLines.join('\n'), 'utf8');
console.log('Fixed syntax error!');
