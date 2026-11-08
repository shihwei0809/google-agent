// Cloudflare Pages Functions API: /api/config
// 動態取得與管理系統設定

export async function onRequest(context) {
  const { request, env } = context;

  const corsHeaders = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Content-Type": "application/json; charset=utf-8"
  };

  if (request.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    if (request.method === "GET") {
      let configs = {};
      if (env.DB) {
        try {
          const { results } = await env.DB.prepare("SELECT key, value, description FROM system_config").all();
          if (results) {
            results.forEach(r => { configs[r.key] = r.value; });
          }
        } catch (e) {}
      }

      // 遮罩敏感金鑰顯示
      const mask = str => str ? str.slice(0, 6) + "******" + str.slice(-4) : "";

      return new Response(JSON.stringify({
        success: true,
        data: {
          hasD1: !!env.DB,
          hasR2: !!env.PHOTOS,
          visionKey1Masked: mask(configs.VISION_API_KEY_1 || env.VISION_API_KEY_1 || env.DEFAULT_VISION_KEY_1),
          visionKey2Masked: mask(configs.VISION_API_KEY_2 || env.VISION_API_KEY_2 || env.DEFAULT_VISION_KEY_2),
          teamsWebhookConfigured: !!(configs.TEAMS_WEBHOOK_URL || env.TEAMS_WEBHOOK_URL || env.DEFAULT_TEAMS_WEBHOOK_URL)
        }
      }), { headers: corsHeaders });
    }

    if (request.method === "POST") {
      if (!env.DB) {
        return new Response(JSON.stringify({ success: false, message: "無 D1 綁定，無法儲存設定" }), {
          status: 400,
          headers: corsHeaders
        });
      }
      const body = await request.json();
      const { key, value } = body;
      if (!key || value === undefined) {
        return new Response(JSON.stringify({ success: false, message: "缺少 key 或 value" }), {
          status: 400,
          headers: corsHeaders
        });
      }

      await env.DB.prepare(
        "INSERT INTO system_config (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value"
      ).bind(key, String(value)).run();

      return new Response(JSON.stringify({ success: true, message: `設定 [${key}] 已更新` }), {
        headers: corsHeaders
      });
    }

    return new Response("Method not allowed", { status: 405 });
  } catch (err) {
    return new Response(JSON.stringify({ success: false, message: err.message }), {
      status: 500,
      headers: corsHeaders
    });
  }
}
