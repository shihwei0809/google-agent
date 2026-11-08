// Cloudflare Pages Functions API: /api/query
// 專門用於查詢 D1 資料庫內的 COA 四重核對紀錄與照片連結

export async function onRequest(context) {
  const { request, env } = context;

  const corsHeaders = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Content-Type": "application/json; charset=utf-8"
  };

  if (request.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  if (request.method !== "GET") {
    return new Response(JSON.stringify({ success: false, message: "Method not allowed" }), {
      status: 405,
      headers: corsHeaders
    });
  }

  try {
    if (!env.DB) {
      return new Response(JSON.stringify({ 
        success: false, 
        message: "D1 資料庫未綁定", 
        data: [],
        total: 0
      }), { headers: corsHeaders });
    }

    const url = new URL(request.url);
    const search = (url.searchParams.get("q") || "").trim();
    const startDate = (url.searchParams.get("start_date") || "").trim();
    const endDate = (url.searchParams.get("end_date") || "").trim();
    const status = (url.searchParams.get("status") || "").trim();
    const page = Math.max(1, parseInt(url.searchParams.get("page") || "1", 10));
    const limit = Math.min(100, Math.max(1, parseInt(url.searchParams.get("limit") || "15", 10)));
    const offset = (page - 1) * limit;

    const conditions = [];
    const params = [];

    if (search) {
      conditions.push("(batch_no LIKE ? OR material_no LIKE ? OR source_doc_no LIKE ? OR weighbridge_no LIKE ? OR supplier LIKE ? OR delivery_place LIKE ?)");
      const term = `%${search}%`;
      params.push(term, term, term, term, term, term);
    }

    if (startDate) {
      conditions.push("date(created_at) >= ?");
      params.push(startDate);
    }

    if (endDate) {
      conditions.push("date(created_at) <= ?");
      params.push(endDate);
    }

    if (status && status !== "all") {
      if (status === "success") {
        conditions.push("(verification_status LIKE '%成功%' OR verification_status LIKE '%合格%')");
      } else {
        conditions.push("(verification_status LIKE '%失敗%' OR verification_status LIKE '%未通過%')");
      }
    }

    const whereClause = conditions.length > 0 ? "WHERE " + conditions.join(" AND ") : "";

    // 總筆數
    const countSql = `SELECT COUNT(*) as total FROM coa_verification_logs ${whereClause}`;
    const countStmt = env.DB.prepare(countSql);
    const countResult = await (params.length > 0 ? countStmt.bind(...params) : countStmt).first();
    const total = countResult ? countResult.total : 0;
    const totalPages = Math.ceil(total / limit) || 1;

    // 清單資料
    const listSql = `
      SELECT id, material_no, tank_no, batch_no, supplier, delivery_place, raw_qr,
             source_doc_no, weighbridge_no, verification_status,
             photo_batch_url, photo_loc_url, error_details, created_at
      FROM coa_verification_logs
      ${whereClause}
      ORDER BY id DESC
      LIMIT ? OFFSET ?
    `;
    const listParams = [...params, limit, offset];
    const listStmt = env.DB.prepare(listSql);
    const { results } = await listStmt.bind(...listParams).all();

    return new Response(JSON.stringify({
      success: true,
      data: results || [],
      pagination: {
        page,
        limit,
        total,
        totalPages
      }
    }), { headers: corsHeaders });

  } catch (err) {
    return new Response(JSON.stringify({ success: false, message: "查詢失敗: " + err.message }), {
      status: 500,
      headers: corsHeaders
    });
  }
}
