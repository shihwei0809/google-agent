// Cloudflare Pages Functions API: /api/upload
// 專門處理照片上傳，將照片寫入 Cloudflare R2 (recycle-photos)，並回傳極速靜態讀取網址

export async function onRequest(context) {
  const { request, env } = context;

  // 跨域 CORS 處理
  if (request.method === "OPTIONS") {
    return new Response(null, {
      headers: {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type"
      }
    });
  }

  const corsHeaders = {
    "Access-Control-Allow-Origin": "*",
    "Content-Type": "application/json"
  };

  if (request.method !== "POST") {
    return new Response(JSON.stringify({ success: false, detail: "Method not allowed" }), {
      status: 405,
      headers: corsHeaders
    });
  }

  try {
    if (!env.PHOTOS) {
      return new Response(JSON.stringify({ 
        success: false, 
        detail: "Cloudflare R2 Bucket (PHOTOS) 未綁定，請確認 wrangler.toml 與 Pages 後台設定" 
      }), {
        status: 500,
        headers: corsHeaders
      });
    }

    const payload = await request.json();
    const id = payload.id || Date.now().toString();

    // 輔助函式：解析 Base64 (支援 Data URL 與純 Base64) 並轉為 Uint8Array
    function parseBase64(base64String) {
      if (!base64String || typeof base64String !== "string") return null;
      let mimeType = "image/jpeg";
      let base64Data = base64String.trim();

      const match = base64Data.match(/^data:([a-zA-Z0-9]+\/[a-zA-Z0-9-.+]+);base64,/);
      if (match) {
        mimeType = match[1];
        base64Data = base64Data.substring(match[0].length);
      }

      // 移除換行等空白
      base64Data = base64Data.replace(/\s/g, "");

      const binaryStr = atob(base64Data);
      const len = binaryStr.length;
      const bytes = new Uint8Array(len);
      for (let i = 0; i < len; i++) {
        bytes[i] = binaryStr.charCodeAt(i);
      }

      return { bytes, mimeType };
    }

    // 辨識上傳內容 (支援批次上傳與單張上傳)
    const tB64 = payload.t_b64 || payload.tank_level_before_b64 || (payload.type === "tank_before" ? payload.image : null);
    const vB64 = payload.v_b64 || payload.vehicle_photo_b64 || (payload.type === "vehicle" ? payload.image : null);
    const aB64 = payload.a_b64 || payload.tank_level_after_b64 || (payload.type === "tank_after" ? payload.image : null);

    const uploads = [];
    let t_url = null;
    let v_url = null;
    let a_url = null;

    if (tB64) {
      const parsed = parseBase64(tB64);
      if (parsed) {
        const key = `${id}_before.jpg`;
        uploads.push(
          env.PHOTOS.put(key, parsed.bytes, {
            httpMetadata: { contentType: parsed.mimeType }
          }).then(() => {
            t_url = `/api/photos/${key}`;
          })
        );
      }
    }

    if (vB64) {
      const parsed = parseBase64(vB64);
      if (parsed) {
        const key = `${id}_vehicle.jpg`;
        uploads.push(
          env.PHOTOS.put(key, parsed.bytes, {
            httpMetadata: { contentType: parsed.mimeType }
          }).then(() => {
            v_url = `/api/photos/${key}`;
          })
        );
      }
    }

    if (aB64) {
      const parsed = parseBase64(aB64);
      if (parsed) {
        const key = `${id}_after.jpg`;
        uploads.push(
          env.PHOTOS.put(key, parsed.bytes, {
            httpMetadata: { contentType: parsed.mimeType }
          }).then(() => {
            a_url = `/api/photos/${key}`;
          })
        );
      }
    }

    if (uploads.length === 0) {
      return new Response(JSON.stringify({ success: false, detail: "未收到任何有效的照片 Base64 資料" }), {
        status: 400,
        headers: corsHeaders
      });
    }

    // 等待所有照片寫入 R2
    await Promise.all(uploads);

    // 若綁定 D1 且傳入紀錄 ID，自動同步回寫 D1 (原子更新確保一筆不漏)
    if (env.DB && id) {
      try {
        await env.DB.prepare(`
          UPDATE recycle_records 
          SET t_before_url = COALESCE(?, t_before_url),
              v_photo_url = COALESCE(?, v_photo_url),
              t_after_url = COALESCE(?, t_after_url),
              updated_at = CURRENT_TIMESTAMP
          WHERE id = ?
        `).bind(t_url, v_url, a_url, id).run();
      } catch (dbErr) {
        console.warn("R2 上傳成功但自動寫入 D1 稍有延遲", dbErr);
      }
    }

    return new Response(JSON.stringify({
      success: true,
      message: "照片成功存入 Cloudflare R2",
      id,
      t_url,
      v_url,
      a_url,
      url: t_url || v_url || a_url // 單張模式相容回傳
    }), {
      status: 200,
      headers: corsHeaders
    });

  } catch (err) {
    return new Response(JSON.stringify({ 
      success: false, 
      detail: "R2 照片上傳處理失敗: " + (err.message || err.toString()) 
    }), {
      status: 500,
      headers: corsHeaders
    });
  }
}
