// Cloudflare Pages Functions API: /api/photos/[[path]]
// 從 Cloudflare R2 (PHOTOS) 高速讀取照片，支援邊緣快取與 ETag 304

export async function onRequest(context) {
  const { request, env, params } = context;

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

    const key = Array.isArray(params.path) ? params.path.join("/") : (params.path || "");
    if (!key) {
      return new Response("Photo key is missing", { status: 400 });
    }

    const object = await env.PHOTOS.get(key);
    if (!object) {
      return new Response("Photo not found in R2", { status: 404 });
    }

    const headers = new Headers();
    object.writeHttpMetadata(headers);

    if (!headers.get("Content-Type")) {
      headers.set("Content-Type", "image/jpeg");
    }

    headers.set("etag", object.httpEtag);
    headers.set("Cache-Control", "public, max-age=31536000, immutable");
    headers.set("Access-Control-Allow-Origin", "*");

    // 處理 If-None-Match 快取協商
    const ifNoneMatch = request.headers.get("if-none-match");
    if (ifNoneMatch && (ifNoneMatch === object.httpEtag || ifNoneMatch === `W/"${object.httpEtag}"`)) {
      return new Response(null, { headers, status: 304 });
    }

    return new Response(object.body, { headers });
  } catch (err) {
    return new Response("Error fetching photo: " + err.message, { status: 500 });
  }
}
