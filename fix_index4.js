const fs = require('fs');
const p = 'C:/GOOGLE ANGET/第二類_生產管理與API串接/QC-系統客製化電子化工廠/3_Cloudflare_D1版/functions/api/index.js';
const t = fs.readFileSync(p, 'utf8');
const lines = t.split('\n');

let start = -1;
let end = -1;
for (let i = 0; i < lines.length; i++) {
  if (lines[i].includes('if (action === "completeSample"')) start = i;
  if (lines[i].includes('if (action === "updateSample"')) end = i;
}
console.log('start:', start, 'end:', end);

if (start > -1 && end > start) {
  const replacement = `
    if (action === "completeSample" && request.method === "POST") {
      const { id, result, note, pin, approver } = payload;
      
      const { results: cfgResults } = await env.DB.prepare("SELECT * FROM System_Config").all();
      let configMap = {}; cfgResults.forEach(r => { configMap[r.config_key] = r.config_value; });

      // 取得原本樣品資訊，為了發送 Teams
      const sample = await env.DB.prepare("SELECT * FROM QC_Samples WHERE id = ?").bind(id).first();
      if (!sample) {
        return new Response(JSON.stringify({ success: false, error: "找不到該樣品" }), { headers: h });
      }

      let status = "completed";
      if (result === "FAIL" || result === "需特採") status = "failed";
      
      let finalNote = note;
      if (result === '特採' && sample.qcResult === '需特採') {
        finalNote = \`[初驗:\${sample.qcApprover}] \${sample.qcNote || ''}\\n[特採:\${approver}] \${note}\`;
      }
      
      // 若已有紀錄，不覆蓋原來的 completedAt
      let completedAt = sample.completedAt || new Date(new Date().getTime() + 8*60*60*1000).toISOString().replace('T', ' ').substring(0, 19);

      await env.DB.prepare("UPDATE QC_Samples SET status = ?, qcResult = ?, qcNote = ?, qcApprover = ?, completedAt = ? WHERE id = ?")
        .bind(status, result, finalNote, approver || 'QC', completedAt, id).run();

      // 如果是不合格(FAIL)，自動產生下一輪重送排程
      if (result === 'FAIL') {
        const newId = crypto.randomUUID();
        const parentId = sample.parentId || sample.id;
        const round = parseInt(sample.round || 1) + 1;
        await env.DB.prepare(\`
          INSERT INTO QC_Samples (id, barcode, productName, tankNo, customer, quantity, flowType, dept, requester, grade, parentId, round, status, isAlerted)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', 0)
        \`).bind(newId, sample.barcode, sample.productName, sample.tankNo, sample.customer, sample.quantity, sample.flowType, sample.dept, sample.requester, sample.grade, parentId, round).run();
      }

      // 通知 Teams
      const deptWebhook = configMap['TEAMS_WEBHOOK_' + sample.dept];
      const managerWebhook = configMap['TEAMS_MANAGER_WEBHOOK'];

      const isPass = (status === 'completed' || result === 'PASS' || result === '特採');
      let resultTitle = result;
      if (result === 'FAIL') resultTitle = '⛔ FAIL (已自動產生下一次重送排程)';
      else if (result === '需特採') resultTitle = '⚠️ 不符合內控 (等待主管審核特採)';
      else if (result === '特採') resultTitle = '🚨 經主管特採放行';
      
      const title = isPass
        ? \`✅【檢驗完成】\${sample.productName}\` 
        : \`❌【檢驗未通過】\${sample.productName}\`;
      const color = isPass ? '28a745' : 'dc3545';
      const actualApprover = approver || 'QC';

      const facts = [
        { name: '檢驗結果', value: \`**\${resultTitle}**\` },
        { name: '審核人員', value: actualApprover },
        { name: '單號', value: sample.barcode || '-' },
        { name: '槽號/車牌', value: \`\${sample.tankNo || '-'} / \${sample.customer || '-'}\` },
        { name: '檢驗備註', value: finalNote || '無' }
      ];

      const msg = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "themeColor": color,
        "summary": title,
        "sections": [{ "activityTitle": title, "activitySubtitle": "QC 品管系統", "facts": facts }]
      };

      const sendWebhook = async (url) => {
        if (!url) return;
        try { await fetch(url, { method: 'POST', body: JSON.stringify(msg) }); } catch(e) {}
      };

      await Promise.all([sendWebhook(deptWebhook), sendWebhook(managerWebhook)]);

      return new Response(JSON.stringify({ success: true }), { headers: h });
    }
`;
  
  // replace from start to end-1
  const newLines = [
    ...lines.slice(0, start),
    ...replacement.split('\n'),
    ...lines.slice(end)
  ];
  
  fs.writeFileSync(p, newLines.join('\n'), 'utf8');
  console.log('Replaced');
}
