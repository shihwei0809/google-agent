// Cloudflare Pages Advanced Mode Worker
// 負責攔截 /api/* 請求對接 D1 資料庫 (ipa-pwa-db)，其餘路徑直接走靜態檔案 env.ASSETS

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;

    // 1. 處理主資料 API: /api/data
    if (path === '/api/data') {
      // GET: 讀取主資料
      if (request.method === 'GET') {
        try {
          if (!env.DB) {
            return new Response(JSON.stringify({ _error: "D1 資料庫未綁定 (env.DB is undefined)" }), {
              status: 500,
              headers: { 'Content-Type': 'application/json' }
            });
          }
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
            headers: {
              'Content-Type': 'application/json; charset=utf-8',
              'Cache-Control': 'no-cache, no-store, must-revalidate'
            }
          });
        } catch (err) {
          return new Response(JSON.stringify({ _error: err.toString() }), {
            status: 500,
            headers: { 'Content-Type': 'application/json; charset=utf-8' }
          });
        }
      }

      // POST: 儲存主資料
      if (request.method === 'POST') {
        try {
          if (!env.DB) {
            return new Response("ERROR: D1 資料庫未綁定", { status: 500 });
          }
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

          return new Response("SUCCESS", {
            headers: {
              'Content-Type': 'text/plain; charset=utf-8',
              'Cache-Control': 'no-cache, no-store'
            }
          });
        } catch (err) {
          return new Response("ERROR: " + err.toString(), { status: 500 });
        }
      }
    }

    // 2. 處理歷史備份 API: /api/archive
    if (path === '/api/archive') {
      // GET: 讀取備份清單
      if (request.method === 'GET') {
        try {
          if (!env.DB) {
            return new Response(JSON.stringify([]), {
              headers: { 'Content-Type': 'application/json; charset=utf-8' }
            });
          }
          const { results } = await env.DB.prepare("SELECT id, timestamp, data_json FROM ipa_archives ORDER BY timestamp DESC").all();
          const list = (results || []).map(row => ({
            id: row.id,
            time: row.timestamp,
            dataStr: row.data_json
          }));
          return new Response(JSON.stringify(list), {
            headers: {
              'Content-Type': 'application/json; charset=utf-8',
              'Cache-Control': 'no-cache, no-store'
            }
          });
        } catch (err) {
          return new Response(JSON.stringify([]), {
            headers: { 'Content-Type': 'application/json; charset=utf-8' }
          });
        }
      }

      // POST: 新增備份紀錄
      if (request.method === 'POST') {
        try {
          if (!env.DB) {
            return new Response("ERROR: D1 資料庫未綁定", { status: 500 });
          }
          const { archiveName, payload } = await request.json();

          // 產生台灣時區的 timestamp
          const now = new Date();
          const twTime = new Date(now.getTime() + 8 * 60 * 60 * 1000);
          const timestamp = twTime.toISOString().replace('T', ' ').substring(0, 19);

          const dataJSON = JSON.stringify(payload);

          await env.DB.prepare("INSERT INTO ipa_archives (id, timestamp, data_json) VALUES (?1, ?2, ?3)")
            .bind(String(archiveName), timestamp, dataJSON)
            .run();

          return new Response("SUCCESS", {
            headers: {
              'Content-Type': 'text/plain; charset=utf-8',
              'Cache-Control': 'no-cache, no-store'
            }
          });
        } catch (err) {
          return new Response("ERROR: " + err.toString(), { status: 500 });
        }
      }
    }

    // 3. 其餘靜態檔案由 env.ASSETS (Cloudflare Pages 預設靜態服務) 提供
    return env.ASSETS.fetch(request);
  }
};
