// Cloudflare Pages Functions API: /api/sync-from-gas
// 專門供 Google Apps Script (GAS) 或試算表自動推送/同步核對紀錄至 Cloudflare D1

export async function onRequest(context) {
  const { request, env } = context;

  const corsHeaders = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Content-Type": "application/json; charset=utf-8"
  };

  if (request.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  if (request.method !== "POST") {
    return new Response(JSON.stringify({ success: false, message: "Method not allowed. Use POST." }), {
      status: 405,
      headers: corsHeaders
    });
  }

  try {
    if (!env.DB) {
      return new Response(JSON.stringify({ success: false, message: "D1 database not bound." }), {
        status: 500,
        headers: corsHeaders
      });
    }

    const body = await request.json();
    let records = [];

    if (Array.isArray(body)) {
      records = body;
    } else if (Array.isArray(body.records)) {
      records = body.records;
    } else if (typeof body === "object" && body !== null) {
      records = [body];
    }

    if (records.length === 0) {
      return new Response(JSON.stringify({ success: false, message: "No records found in request body." }), {
        status: 400,
        headers: corsHeaders
      });
    }

    let inserted = 0;
    let skipped = 0;

    for (const r of records) {
      // 欄位標準化與相容 (支援多種常見命名)
      const materialNo = (r.material_no || r.materialNo || r["料號"] || "").trim();
      const tankNo = (r.tank_no || r.tankNo || r["槽號"] || "").trim();
      const batchNo = (r.batch_no || r.batchNo || r["批號"] || "").trim();
      const supplier = (r.supplier || r["供應商"] || "").trim();
      const deliveryPlace = (r.delivery_place || r.deliveryPlace || r["送達地點"] || "").trim();
      const rawQr = (r.raw_qr || r.rawQr || r["原始QR"] || "").trim();
      const sourceDocNo = (r.source_doc_no || r.sourceDocNo || r["來源單號"] || "").trim();
      const weighbridgeNo = (r.weighbridge_no || r.weighbridgeNo || r["磅單"] || r["磅單號"] || "").trim();
      let status = (r.verification_status || r.verificationStatus || r.status || r["狀態"] || "核對成功").trim();
      if (!status) status = "核對成功";

      const photoBatchUrl = (r.photo_batch_url || r.photoBatchUrl || r["COA照片"] || "").trim();
      const photoLocUrl = (r.photo_loc_url || r.photoLocUrl || r["地磅照片"] || "").trim();
      const errorDetails = (r.error_details || r.errorDetails || "").trim();
      const ocrSnippet = (r.ocr_snippet || r.ocrSnippet || "").trim();

      // 日期處理
      let createdAt = (r.created_at || r.createdAt || r["時間"] || "").trim();
      if (createdAt) {
        // 處理常見 Google Sheet 日期格式 "2026/11/8 下午 1:29:09" 或 "2026-11-08 13:29:09"
        try {
          // 若包含 下午 / 上午
          if (createdAt.includes("下午") || createdAt.includes("上午")) {
            const isPM = createdAt.includes("下午");
            const cleanStr = createdAt.replace("下午", "").replace("上午", "").trim();
            const parts = cleanStr.split(" ");
            const dateParts = parts[0].split(/[/-]/);
            const timeParts = (parts[1] || "00:00:00").split(":");
            let hour = parseInt(timeParts[0], 10);
            if (isPM && hour < 12) hour += 12;
            if (!isPM && hour === 12) hour = 0;
            const pad = n => String(n).padStart(2, "0");
            createdAt = `${dateParts[0]}-${pad(dateParts[1])}-${pad(dateParts[2])} ${pad(hour)}:${pad(timeParts[1] || 0)}:${pad(timeParts[2] || 0)}`;
          } else {
            const d = new Date(createdAt);
            if (!isNaN(d.getTime())) {
              const pad = n => String(n).padStart(2, "0");
              createdAt = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
            }
          }
        } catch (e) {
          // 保留原始字串
        }
      } else {
        const now = new Date();
        const pad = n => String(n).padStart(2, "0");
        createdAt = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`;
      }

      // 防呆去重檢查：同批號 + 同時間 (或同批號 + 同磅單) 則視為重複已存在
      const existing = await env.DB.prepare(`
        SELECT id FROM coa_verification_logs 
        WHERE batch_no = ? AND (created_at = ? OR (weighbridge_no = ? AND weighbridge_no != ''))
        LIMIT 1
      `).bind(batchNo, createdAt, weighbridgeNo).first();

      if (existing) {
        skipped++;
        continue;
      }

      await env.DB.prepare(`
        INSERT INTO coa_verification_logs 
        (material_no, tank_no, batch_no, supplier, delivery_place, raw_qr, source_doc_no, weighbridge_no, verification_status, photo_batch_url, photo_loc_url, error_details, ocr_snippet, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `).bind(
        materialNo,
        tankNo,
        batchNo,
        supplier,
        deliveryPlace,
        rawQr,
        sourceDocNo,
        weighbridgeNo,
        status,
        photoBatchUrl,
        photoLocUrl,
        errorDetails,
        ocrSnippet,
        createdAt
      ).run();

      inserted++;
    }

    return new Response(JSON.stringify({
      success: true,
      message: `同步完成！新增 ${inserted} 筆，略過重複 ${skipped} 筆。`,
      inserted,
      skipped,
      total_received: records.length
    }), {
      status: 200,
      headers: corsHeaders
    });

  } catch (err) {
    return new Response(JSON.stringify({
      success: false,
      message: `伺服器同步發生錯誤: ${err.message}`
    }), {
      status: 500,
      headers: corsHeaders
    });
  }
}
