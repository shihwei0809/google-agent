// Cloudflare Pages Functions API: /api/ai-read
// 專門用於「三合一單 AI 拍照讀單」，自動解析送達地點、供應商、料號、槽號、批號
// 支援向 GAS 獲取最新金鑰與雙 Key 自動輪詢

import {
  getVisionApiKeysList,
  getNextRoundRobinIndex,
  isVisionKeyUnderQuota,
  incrementVisionKeyQuota,
  callGeminiFallback
} from "./_gas_helper.js";

async function callGoogleVisionWithRetry(base64Image, keyList, env, startIndex = 0) {
  let cleanB64 = base64Image;
  if (cleanB64.includes(",")) {
    cleanB64 = cleanB64.split(",")[1];
  }
  cleanB64 = cleanB64.replace(/\s/g, "");

  let lastError = null;
  const totalKeys = keyList.length;

  for (let attempt = 0; attempt < totalKeys; attempt++) {
    const idx = (startIndex + attempt) % totalKeys;
    const apiKey = keyList[idx];

    // ★ 防收費鐵律：若該把 Key 當月累計已達 900 次上限，強制略過不呼叫
    const underQuota = await isVisionKeyUnderQuota(env, apiKey);
    if (!underQuota) continue;

    try {
      const url = `https://vision.googleapis.com/v1/images:annotate?key=${apiKey}`;
      const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          requests: [
            {
              image: { content: cleanB64 },
              features: [{ type: "TEXT_DETECTION", maxResults: 10 }]
            }
          ]
        })
      });

      if (response.ok) {
        const json = await response.json();
        if (!json.error) {
          await incrementVisionKeyQuota(env, apiKey);
          return { data: json, usedKey: apiKey };
        }
        lastError = new Error(`Google Vision API 錯誤: ${json.error.message}`);
      } else {
        const errText = await response.text();
        lastError = new Error(`Google Vision API 呼叫失敗 (${response.status}): ${errText}`);
      }
    } catch (err) {
      lastError = err;
    }
  }

  // 當所有 Vision API Key 都達 900 次上限或失敗時，自動切換至 Gemini 模型備援 (優先 gemini-3.8-flash)
  if (env) {
    const geminiText = await callGeminiFallback(base64Image, env);
    if (geminiText !== null) {
      return {
        data: { responses: [{ fullTextAnnotation: { text: geminiText } }] },
        usedKey: "GEMINI_FALLBACK_3.8"
      };
    }
  }

  throw lastError || new Error("所有 Google Vision 與 Gemini 備援 API 金鑰皆已用盡或無法連線");
}

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
    return new Response(JSON.stringify({ success: false, message: "Method not allowed" }), {
      status: 405,
      headers: corsHeaders
    });
  }

  try {
    const input = await request.json();
    const photoData = input.photoData;
    if (!photoData) {
      return new Response(JSON.stringify({ success: false, message: "未收到照片資料" }), {
        status: 400,
        headers: corsHeaders
      });
    }

    // ★ 向 GAS 或環境獲取最新 Vision API Key 清單並支援輪流分攤與 900 次上限保護
    const keyList = await getVisionApiKeysList(env);
    const startIdx = getNextRoundRobinIndex();
    const { data: ocrResult, usedKey } = await callGoogleVisionWithRetry(photoData, keyList, env, startIdx);
    const text = ocrResult?.responses?.[0]?.fullTextAnnotation?.text || "";

    // 預處理：全形符號替換
    const cleanText = text
      .replace(/：/g, ":")
      .replace(/　/g, " ")
      .replace(/\|/g, " ");

    const data = {
      batchNo: "",
      tankNo: "",
      materialNo: "",
      deliveryPlace: "",
      supplier: ""
    };

    // 1. 送達地點
    let m = cleanText.match(/送達地點[\s:.]*([E|F][0-9A-Z]+)/);
    if (m) data.deliveryPlace = m[1];
    else {
      m = cleanText.match(/地點[\s:.]*([E|F][0-9A-Z]+)/);
      if (m) data.deliveryPlace = m[1];
    }

    // 2. 供應商
    m = cleanText.match(/供應商[\s:.]*([0-9]+)/);
    if (m) data.supplier = m[1];

    // 3. 料號
    m = cleanText.match(/料號[\s:.]*([A-Z0-9]+)/);
    if (m) data.materialNo = m[1];

    // 4. 槽號
    m = cleanText.match(/槽號[\s:.]*([0-9A-Z]+)/);
    if (m) data.tankNo = m[1];

    // 5. 批號
    m = cleanText.match(/批號[\s:.]*([0-9A-Z]+)/);
    if (m) data.batchNo = m[1];

    // --- 保險機制 (Fallback 偵測) ---
    if (!data.deliveryPlace) {
      m = cleanText.match(/\b([E|F][A-Z0-9]{5,})\b/);
      if (m) data.deliveryPlace = m[1];
    }
    if (!data.batchNo) {
      m = cleanText.match(/\b(626[0-9A-Z]{5,}|261[0-9A-Z]{5,})\b/);
      if (m) data.batchNo = m[1];
    }
    if (!data.tankNo) {
      m = cleanText.match(/\b(5?E3[0-9]{2,})\b/);
      if (m) data.tankNo = m[1];
    }

    // 記錄 API 日誌 (非同步寫入 D1)
    if (env.DB) {
      try {
        await env.DB.prepare(
          "INSERT INTO api_logs (api_type, model_name, key_snippet, status, note) VALUES (?, ?, ?, ?, ?)"
        ).bind("VISION_AI_READ", "Google-Vision-OCR", (usedKey || "").slice(0, 8) + "...", "SUCCESS", `批號: ${data.batchNo || "未讀到"}`).run();
      } catch (logErr) {
        console.error("D1 log error:", logErr);
      }
    }

    return new Response(JSON.stringify({ success: true, data, rawText: text.slice(0, 300) }), {
      headers: corsHeaders
    });
  } catch (err) {
    return new Response(JSON.stringify({ success: false, message: "AI 讀單失敗: " + err.message }), {
      status: 500,
      headers: corsHeaders
    });
  }
}
