import re
with open(r'd:\GOOGLE ANGET\第二類_生產管理與API串接\溫度通報\3_Cloudflare_D1版\functions\api\check.js', 'r', encoding='utf-8') as f:
    c = f.read()

patch = '''
    // 防止重複觸發 (防呆機制)
    const existing = await env.DB.prepare("SELECT id FROM temperature_logs WHERE obs_time = ?").bind(obsTime).first();
    if (existing) {
        return new Response(JSON.stringify({status: "skipped", reason: "Data for this obs_time already exists"}), {
            headers: { "content-type": "application/json" }
        });
    }

    await env.DB.prepare(
        "INSERT INTO temperature_logs
'''
c = re.sub(r'await\s+env\.DB\.prepare\(\s*"INSERT\s+INTO\s+temperature_logs', patch.strip(), c)

with open(r'd:\GOOGLE ANGET\第二類_生產管理與API串接\溫度通報\3_Cloudflare_D1版\functions\api\check.js', 'w', encoding='utf-8') as f:
    f.write(c)
