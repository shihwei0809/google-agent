export async function onRequest(context) {
  const { request, env } = context;
  const url = new URL(request.url);

  const corsHeaders = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
  };

  if (request.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  const jsonResponse = (data, status = 200) => {
    return new Response(JSON.stringify(data), {
      status,
      headers: {
        "Content-Type": "application/json; charset=utf-8",
        ...corsHeaders,
      },
    });
  };

  if (!env.WEGOVY_SYNC) {
    return jsonResponse(
      { success: false, error: "KV_NOT_BOUND", message: "雲端資料庫未綁定 (WEGOVY_SYNC)" },
      500
    );
  }

  // GET: 讀取同步資料 (?code=XXXXXX)
  if (request.method === "GET") {
    const code = (url.searchParams.get("code") || "").trim().toUpperCase();
    if (!code || code.length < 3 || code.length > 32) {
      return jsonResponse(
        { success: false, error: "INVALID_CODE", message: "請輸入有效的 3~32 碼同步代碼" },
        400
      );
    }

    try {
      const { value, metadata } = await env.WEGOVY_SYNC.getWithMetadata(code, { type: "json" });
      if (!value) {
        return jsonResponse(
          { success: false, error: "NOT_FOUND", message: `找不到同步碼 [${code}] 的雲端紀錄` },
          404
        );
      }
      return jsonResponse({
        success: true,
        code,
        data: value,
        updatedAt: metadata?.updatedAt || null,
        message: "雲端資料讀取成功",
      });
    } catch (err) {
      return jsonResponse(
        { success: false, error: "READ_FAILED", message: "讀取失敗: " + err.message },
        500
      );
    }
  }

  // POST: 上傳/更新同步資料 ({ code: 'XXXXXX', data: {...} })
  if (request.method === "POST") {
    try {
      const body = await request.json();
      const code = (body.code || "").trim().toUpperCase();
      const data = body.data;

      if (!code || code.length < 3 || code.length > 32) {
        return jsonResponse(
          { success: false, error: "INVALID_CODE", message: "請輸入有效的 3~32 碼同步代碼" },
          400
        );
      }
      if (!data || typeof data !== "object") {
        return jsonResponse(
          { success: false, error: "INVALID_DATA", message: "上傳資料格式不正確" },
          400
        );
      }

      const nowIso = new Date().toISOString();
      await env.WEGOVY_SYNC.put(code, JSON.stringify(data), {
        metadata: { updatedAt: nowIso },
      });

      return jsonResponse({
        success: true,
        code,
        updatedAt: nowIso,
        message: "✅ 雲端資料同步成功！",
      });
    } catch (err) {
      return jsonResponse(
        { success: false, error: "WRITE_FAILED", message: "寫入失敗: " + err.message },
        500
      );
    }
  }

  return jsonResponse({ success: false, error: "METHOD_NOT_ALLOWED" }, 405);
}
