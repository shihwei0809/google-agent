// Cloudflare Pages Advanced Mode (_worker.js)
// 確保 /api/* 路由 100% 正確對接到 Cloudflare D1 資料庫

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // 處理 API 請求
    if (url.pathname.startsWith('/api/')) {
      return handleApiRequest(url.pathname, request, env);
    }

    // 靜態資源交給 Cloudflare Pages 預設資產處理器
    return env.ASSETS.fetch(request);
  }
};

async function handleApiRequest(pathname, request, env) {
  // CORS 跨域標頭
  const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  };

  if (request.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  // 1. /api/data (主資料讀取與儲存)
  if (pathname === '/api/data') {
    if (request.method === 'GET') {
      try {
        const { results } = await env.DB.prepare("SELECT * FROM ipa_data").all();
        const data = {};
        for (const row of results || []) {
          try {
            if (typeof row.value === 'string' && (row.value.startsWith('{') || row.value.startsWith('['))) {
              data[row.key] = JSON.parse(row.value);
            } else {
              data[row.key] = row.value;
            }
          } catch (e) {
            data[row.key] = row.value;
          }
        }
        return new Response(JSON.stringify(data), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      } catch (err) {
        return new Response(JSON.stringify({ _error: err.toString() }), {
          status: 500,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }
    }

    if (request.method === 'POST') {
      try {
        const payload = await request.json();
        const stmts = [];

        for (const key of Object.keys(payload)) {
          let value = payload[key];
          if (value === undefined || value === null) value = '';
          if (typeof value === 'number' && isNaN(value)) value = '';
          if (typeof value === 'object') value = JSON.stringify(value);

          stmts.push(
            env.DB.prepare("INSERT INTO ipa_data (key, value) VALUES (?1, ?2) ON CONFLICT(key) DO UPDATE SET value=?2")
              .bind(key, String(value))
          );
        }

        if (stmts.length > 0) {
          await env.DB.batch(stmts);
        }

        return new Response("SUCCESS", { headers: corsHeaders });
      } catch (err) {
        return new Response("ERROR: " + err.toString(), {
          status: 500,
          headers: corsHeaders
        });
      }
    }
  }

  // 2. /api/archive (備份紀錄讀取與新增)
  if (pathname === '/api/archive') {
    if (request.method === 'GET') {
      try {
        const { results } = await env.DB.prepare("SELECT id, timestamp, data_json FROM ipa_archives ORDER BY timestamp DESC").all();
        const list = (results || []).map(row => ({
          id: row.id,
          time: row.timestamp,
          dataStr: row.data_json
        }));
        return new Response(JSON.stringify(list), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      } catch (err) {
        return new Response(JSON.stringify([]), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }
    }

    if (request.method === 'POST') {
      try {
        const { archiveName, payload } = await request.json();

        // 台灣時區 timestamp
        const now = new Date();
        const twTime = new Date(now.getTime() + 8 * 60 * 60 * 1000);
        const timestamp = twTime.toISOString().replace('T', ' ').substring(0, 19);

        const dataJSON = JSON.stringify(payload);

        await env.DB.prepare("INSERT INTO ipa_archives (id, timestamp, data_json) VALUES (?1, ?2, ?3)")
          .bind(String(archiveName), timestamp, dataJSON)
          .run();

        return new Response("SUCCESS", { headers: corsHeaders });
      } catch (err) {
        return new Response("ERROR: " + err.toString(), {
          status: 500,
          headers: corsHeaders
        });
      }
    }
  }

  return new Response("API Not Found", { status: 404, headers: corsHeaders });
}
