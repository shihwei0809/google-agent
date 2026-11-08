// Cloudflare Pages Functions API: /api/photos/[[path]]
// 專門自 Cloudflare R2 (recycle-photos) 高速串流回傳照片，支援全域 CDN 邊緣快取與 ETag 304

export async function onRequest(context) {
  const { request, env, params } = context;

  // 跨域 CORS 與 HEAD 請求處理
  if (request.method === "OPTIONS") {
    return new Response(null, {
      headers: {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
        "Access-Control-Allow-Headers": "*"
      }
    });
  }

  if (request.method !== "GET" && request.method !== "HEAD") {
    return new Response("Method not allowed", { status: 405 });
  }

  try {
    if (!env.PHOTOS) {
      return new Response("R2 storage bucket (PHOTOS) not configured", { status: 500 });
    }

    // 取得檔案路徑 (支援陣列 catch-all 或單一字串)
    const key = Array.isArray(params.path) ? params.path.join("/") : (params.path || "");
    if (!key) {
      return new Response("Photo key is missing", { status: 400 });
    }

    const object = await env.PHOTOS.get(key);
    if (!object) {
      return new Response("Photo not found", { status: 404 });
    }

    const headers = new Headers();
    object.writeHttpMetadata(headers);
    
    // 若原圖無特定 contentType，預設為 image/jpeg
    if (!headers.get("Content-Type")) {
      headers.set("Content-Type", "image/jpeg");
    }

    // 邊緣強效快取 1 年 (immutable)
    headers.set("etag", object.httpEtag);
    headers.set("Cache-Control", "public, max-age=31536000, immutable");
    headers.set("Access-Control-Allow-Origin", "*");

    // ETag 304 最佳化：若瀏覽器已有快取，秒回 304 零流量耗損
    const ifNoneMatch = request.headers.get("if-none-match");
    if (ifNoneMatch && (ifNoneMatch === object.httpEtag || ifNoneMatch === `"${object.httpEtag}"`)) {
      return new Response(null, { status: 304, headers });
    }

    if (request.method === "HEAD") {
      return new Response(null, { headers });
    }

    return new Response(object.body, { headers });

  } catch (err) {
    return new Response("Error retrieving photo: " + (err.message || err.toString()), { 
      status: 500,
      headers: { "Access-Control-Allow-Origin": "*" }
    });
  }
}
