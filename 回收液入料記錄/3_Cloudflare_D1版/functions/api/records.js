// Cloudflare Pages Functions API: /api/records
// 提供高效能、毫秒級的回收液入料資料讀取、新增、狀態更新與刪除

export async function onRequest(context) {
  const { request, env } = context;
  const url = new URL(request.url);

  // 跨域 CORS 處理
  if (request.method === "OPTIONS") {
    return new Response(null, {
      headers: {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type"
      }
    });
  }

  const corsHeaders = {
    "Access-Control-Allow-Origin": "*",
    "Content-Type": "application/json"
  };

  try {
    // 檢查資料庫綁定
    if (!env.DB) {
      return new Response(JSON.stringify({ success: false, detail: "D1 資料庫未綁定" }), {
        status: 500,
        headers: corsHeaders
      });
    }

    // 自動建表（若尚未初始化）
    await env.DB.prepare(`
      CREATE TABLE IF NOT EXISTS recycle_records (
        id TEXT PRIMARY KEY,
        date TEXT NOT NULL,
        license_plate TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        t_before_url TEXT,
        v_photo_url TEXT,
        t_after_url TEXT,
        before_time TEXT,
        after_time TEXT,
        duration INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    `).run();

    // GET 請求處理
    if (request.method === "GET") {
      const action = url.searchParams.get("action");

      if (action === "query") {
        // 歷史查詢模式：回傳所有紀錄，依建立時間倒序
        const { results } = await env.DB.prepare(
          "SELECT * FROM recycle_records ORDER BY created_at DESC LIMIT 500"
        ).all();

        const formatted = results.map(r => ({
          id: r.id,
          date: r.date,
          license_plate: r.license_plate,
          status: r.status,
          tBeforeUrl: r.t_before_url,
          vPhotoUrl: r.v_photo_url,
          tAfterUrl: r.t_after_url,
          before_time: r.before_time,
          after_time: r.after_time,
          duration: r.duration
        }));

        return new Response(JSON.stringify({ records: formatted }), { headers: corsHeaders });
      } else {
        // 預設模式：僅回傳待入料清單 (status = 'pending')
        const { results } = await env.DB.prepare(
          "SELECT id, date, license_plate, before_time FROM recycle_records WHERE status = 'pending' ORDER BY created_at ASC"
        ).all();

        return new Response(JSON.stringify({ records: results }), { headers: corsHeaders });
      }
    }

    // POST 請求處理
    if (request.method === "POST") {
      const payload = await request.json();
      const action = payload.action;

      // 1. 入料前登錄 (before_feed)
      if (action === "before_feed") {
        const { id, date, license_plate, client_before_time, t_url, v_url } = payload;
        if (!id || !license_plate) {
          return new Response(JSON.stringify({ success: false, detail: "缺少必要欄位" }), {
            status: 400,
            headers: corsHeaders
          });
        }

        // 檢查是否已存在
        const existing = await env.DB.prepare("SELECT id FROM recycle_records WHERE id = ?").bind(id).first();
        if (existing) {
          return new Response(JSON.stringify({ success: true, message: "ID 已存在，略過新增" }), { headers: corsHeaders });
        }

        const bTime = client_before_time || new Date().toLocaleString('zh-TW', { hour12: false });
        await env.DB.prepare(`
          INSERT INTO recycle_records (id, date, license_plate, status, t_before_url, v_photo_url, before_time)
          VALUES (?, ?, ?, 'pending', ?, ?, ?)
        `).bind(id, date, license_plate, t_url || "", v_url || "", bTime).run();

        return new Response(JSON.stringify({ success: true, message: "入料前紀錄已建立至 D1" }), { headers: corsHeaders });
      }

      // 2. 入料完成更新 (after_feed)
      if (action === "after_feed") {
        const { id, client_after_time, a_url } = payload;
        if (!id) {
          return new Response(JSON.stringify({ success: false, detail: "缺少紀錄 ID" }), {
            status: 400,
            headers: corsHeaders
          });
        }

        const record = await env.DB.prepare("SELECT * FROM recycle_records WHERE id = ?").bind(id).first();
        if (!record) {
          // 若後台找不到該筆（例如管理員直接在後台刪除），回傳 deleted 告知前端立即清理本地快取
          return new Response(JSON.stringify({ success: false, isDeleted: true, detail: "此紀錄已在後台刪除" }), {
            status: 404,
            headers: corsHeaders
          });
        }

        const aTime = client_after_time || new Date().toLocaleString('zh-TW', { hour12: false });
        let durationMin = null;
        try {
          if (record.before_time) {
            const t1 = new Date(record.before_time.replace(/-/g, "/")).getTime();
            const t2 = new Date(aTime.replace(/-/g, "/")).getTime();
            if (!isNaN(t1) && !isNaN(t2) && t2 >= t1) {
              durationMin = Math.round((t2 - t1) / (1000 * 60));
            }
          }
        } catch (e) {}

        await env.DB.prepare(`
          UPDATE recycle_records 
          SET status = 'completed',
              t_after_url = COALESCE(?, t_after_url),
              after_time = ?,
              duration = ?,
              updated_at = CURRENT_TIMESTAMP
          WHERE id = ?
        `).bind(a_url || "", aTime, durationMin, id).run();

        return new Response(JSON.stringify({ success: true, message: "入料完成已更新至 D1" }), { headers: corsHeaders });
      }

      // 3. 一次性完成入料 (complete_feed，離線前後都在本機完成時)
      if (action === "complete_feed") {
        const { id, date, license_plate, client_before_time, client_after_time, t_url, v_url, a_url } = payload;
        
        let durationMin = null;
        try {
          if (client_before_time && client_after_time) {
            const t1 = new Date(client_before_time.replace(/-/g, "/")).getTime();
            const t2 = new Date(client_after_time.replace(/-/g, "/")).getTime();
            if (!isNaN(t1) && !isNaN(t2) && t2 >= t1) {
              durationMin = Math.round((t2 - t1) / (1000 * 60));
            }
          }
        } catch (e) {}

        await env.DB.prepare(`
          INSERT INTO recycle_records (id, date, license_plate, status, t_before_url, v_photo_url, t_after_url, before_time, after_time, duration)
          VALUES (?, ?, ?, 'completed', ?, ?, ?, ?, ?, ?)
          ON CONFLICT(id) DO UPDATE SET
            status = 'completed',
            t_after_url = excluded.t_after_url,
            after_time = excluded.after_time,
            duration = excluded.duration,
            updated_at = CURRENT_TIMESTAMP
        `).bind(id, date, license_plate, t_url || "", v_url || "", a_url || "", client_before_time || "", client_after_time || "", durationMin).run();

        return new Response(JSON.stringify({ success: true, message: "完整入料紀錄已寫入 D1" }), { headers: corsHeaders });
      }

      // 4. 補寫/更新 Google Drive 照片網址 (update_photos)
      if (action === "update_photos") {
        const { id, t_url, v_url, a_url } = payload;
        if (!id) return new Response(JSON.stringify({ success: false }), { headers: corsHeaders });

        await env.DB.prepare(`
          UPDATE recycle_records 
          SET t_before_url = COALESCE(?, t_before_url),
              v_photo_url = COALESCE(?, v_photo_url),
              t_after_url = COALESCE(?, t_after_url),
              updated_at = CURRENT_TIMESTAMP
          WHERE id = ?
        `).bind(t_url || null, v_url || null, a_url || null, id).run();

        return new Response(JSON.stringify({ success: true }), { headers: corsHeaders });
      }

      // 5. 後台手動刪除 (delete_record)
      if (action === "delete_record") {
        const { id } = payload;
        if (id) {
          await env.DB.prepare("DELETE FROM recycle_records WHERE id = ?").bind(id).run();
        }
        return new Response(JSON.stringify({ success: true }), { headers: corsHeaders });
      }

      return new Response(JSON.stringify({ success: false, detail: "未知的 action" }), {
        status: 400,
        headers: corsHeaders
      });
    }

    return new Response(JSON.stringify({ success: false, detail: "Method not allowed" }), {
      status: 405,
      headers: corsHeaders
    });

  } catch (err) {
    return new Response(JSON.stringify({ success: false, detail: err.toString() }), {
      status: 500,
      headers: corsHeaders
    });
  }
}
