path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\functions\api\index.js'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

injection = """
    if (action === "completeSample" && request.method === "POST") {
      const { id, result, note, pin, approver } = payload;
      
      const { results: cfgResults } = await env.DB.prepare("SELECT * FROM System_Config").all();
      let configMap = {}; cfgResults.forEach(r => { configMap[r.config_key] = r.config_value; });
      
      const validPin = configMap['QC_PIN'] || '8888';
      if (pin !== validPin) {
        return new Response(JSON.stringify({ success: false, error: "⛔ 授權失敗：品管專屬密碼錯誤！" }), { headers: h });
      }

      // 取得原本樣品資訊，為了發送 Teams
      const sample = await env.DB.prepare("SELECT * FROM QC_Samples WHERE id = ?").bind(id).first();
      if (!sample) {
        return new Response(JSON.stringify({ success: false, error: "找不到該樣品" }), { headers: h });
      }

      let status = "completed";
      if (result === "FAIL" || result === "退件" || result === "重取樣") status = "failed";
      
      // 若已有紀錄，不覆蓋原來的 completedAt
      let completedAt = sample.completedAt || new Date(new Date().getTime() + 8*60*60*1000).toISOString().replace('T', ' ').substring(0, 19);

      await env.DB.prepare("UPDATE QC_Samples SET status = ?, qcResult = ?, qcNote = ?, qcApprover = ?, completedAt = ? WHERE id = ?")
        .bind(status, result, note, approver || 'QC', completedAt, id).run();

      // 通知 Teams
      const deptWebhook = configMap['TEAMS_WEBHOOK_' + sample.dept];
      const managerWebhook = configMap['TEAMS_MANAGER_WEBHOOK'];

      const isPass = (status === 'completed' || result === 'PASS' || result.includes('合格'));
      const title = isPass
        ? `✅【品管檢驗通過通知】${sample.product}` 
        : `❌【品管檢驗退回通知】${sample.product}`;
      const color = isPass ? '28a745' : 'dc3545';
      const actualApprover = approver || 'QC';

      const facts = [
        { name: '檢驗結果', value: `**${result}**` },
        { name: '放行核准人', value: actualApprover },
        { name: '單號', value: sample.t100_no },
        { name: '槽號/車牌', value: `${sample.tank} / ${sample.container}` },
        { name: '檢驗備註', value: note || '無' }
      ];

      const msg = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "themeColor": color,
        "summary": title,
        "sections": [{ "activityTitle": title, "activitySubtitle": "系統自動通報", "facts": facts }]
      };

      const sendWebhook = async (url) => {
        if (!url) return;
        try { await fetch(url, { method: 'POST', body: JSON.stringify(msg) }); } catch(e) {}
      };

      await Promise.all([sendWebhook(deptWebhook), sendWebhook(managerWebhook)]);

      return new Response(JSON.stringify({ success: true }), { headers: h });
    }
"""

if 'action === "completeSample"' not in text:
    text = text.replace('    if (action === "updateSample"', injection + '\n    if (action === "updateSample"')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    print("Injected completeSample to index.js")
else:
    print("Already exists")
