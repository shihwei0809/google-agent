import re
path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\functions\api\index.js'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# Generate checkOverdue action
check_overdue_code = """
    if (action === "checkOverdue") {
      // 取得 Teams Webhook 設定
      const { results: cfgResults } = await env.DB.prepare("SELECT * FROM System_Config").all();
      let configMap = {}; cfgResults.forEach(r => { configMap[r.config_key] = r.config_value; });
      
      const managerWebhook = configMap['TEAMS_MANAGER_WEBHOOK'];
      const deptsWebhooks = {
        '資材課': configMap['TEAMS_WEBHOOK_資材課'],
        '現場一課': configMap['TEAMS_WEBHOOK_現場一課'],
        '現場二課': configMap['TEAMS_WEBHOOK_現場二課'],
        '二部一課': configMap['TEAMS_WEBHOOK_二部一課'],
        '二部二課': configMap['TEAMS_WEBHOOK_二部二課'],
        '回收處理課': configMap['TEAMS_WEBHOOK_回收處理課']
      };

      // 計算在台灣時間下，等候多少小時
      const { results: samples } = await env.DB.prepare(`
        SELECT *, (julianday('now', '+8 hours') - julianday(createdAt)) * 24 as diffHours
        FROM QC_Samples 
        WHERE status = 'pending'
      `).all();

      let alertedCount = 0;
      let logs = [];

      for (const s of samples) {
        let alertLevel = 0;
        let alertTitle = "";
        
        if (s.diffHours >= 4 && (s.isAlerted || 0) < 2) {
          alertLevel = 2;
          alertTitle = `🚨【QC 嚴重超時警報】等候已達 ${s.diffHours.toFixed(1)} 小時 (超過4小時)`;
        } else if (s.diffHours >= 2 && s.diffHours < 4 && (s.isAlerted || 0) < 1) {
          alertLevel = 1;
          alertTitle = `⚠️【QC 檢驗超時警報】等候已達 ${s.diffHours.toFixed(1)} 小時 (超過2小時)`;
        }

        if (alertLevel > 0) {
          const cardPayload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": alertLevel === 2 ? "990000" : "D9381E",
            "summary": alertTitle,
            "sections": [{
              "activityTitle": alertTitle,
              "activitySubtitle": `樣品檢驗已逾 ${alertLevel === 2 ? '4' : '2'} 小時未判定，請品管與 ${s.dept} 儘速處理`,
              "facts": [
                { "name": "🏢 送樣單位", "value": `${s.dept}（送樣人：${s.requester || '無'}）` },
                { "name": "🧪 檢驗品名", "value": s.productName },
                { "name": "🛢️ 槽號 / 車牌", "value": `${s.tankNo || '-'} / ${s.customer || '-'}` },
                { "name": "📋 單號編號", "value": s.barcode },
                { "name": "⏰ 送樣時間", "value": s.createdAt }
              ],
              "markdown": true
            }]
          };

          const urls = [];
          if (managerWebhook) urls.push(managerWebhook);
          if (s.dept && deptsWebhooks[s.dept]) urls.push(deptsWebhooks[s.dept]);

          for (const url of urls) {
            if (!url) continue;
            try {
              await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(cardPayload)
              });
            } catch(e) { logs.push(`Failed to send to ${s.dept}: ${e.message}`); }
          }

          // 更新警告狀態
          await env.DB.prepare("UPDATE QC_Samples SET isAlerted = ? WHERE id = ?").bind(alertLevel, s.id).run();
          alertedCount++;
          logs.push(`Alerted level ${alertLevel} for ${s.barcode}`);
        }
      }
      
      return new Response(JSON.stringify({ success: true, alertedCount, logs }), { headers: h });
    }
"""

text = text.replace('if (action === "getEmployees")', check_overdue_code + '\n    if (action === "getEmployees")')

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
