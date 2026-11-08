// Cloudflare Pages Functions API: /api/verify
// 核心四重核對引擎 + Cloudflare R2 照片儲存 + D1 紀錄 + Google 試算表 (GAS) 雙向同步 + Teams 警報推播

import { getVisionApiKey, getTeamsWebhookUrl, syncRecordToGoogleSheets } from "./_gas_helper.js";

async function callGoogleVision(base64Image, apiKey) {
  let cleanB64 = base64Image;
  if (cleanB64.includes(",")) {
    cleanB64 = cleanB64.split(",")[1];
  }
  cleanB64 = cleanB64.replace(/\s/g, "");

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

  if (!response.ok) {
    const errText = await response.text();
    throw new Error(`Google Vision API 失敗 (${response.status}): ${errText}`);
  }

  return await response.json();
}

function parseBase64ToBytes(base64String) {
  if (!base64String || typeof base64String !== "string") return null;
  let mimeType = "image/jpeg";
  let base64Data = base64String.trim();

  const match = base64Data.match(/^data:([a-zA-Z0-9]+\/[a-zA-Z0-9-.+]+);base64,/);
  if (match) {
    mimeType = match[1];
    base64Data = base64Data.substring(match[0].length);
  }
  base64Data = base64Data.replace(/\s/g, "");

  const binaryStr = atob(base64Data);
  const len = binaryStr.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) {
    bytes[i] = binaryStr.charCodeAt(i);
  }
  return { bytes, mimeType };
}

async function saveToR2(env, key, base64String) {
  if (!env.PHOTOS) return null;
  const parsed = parseBase64ToBytes(base64String);
  if (!parsed) return null;

  await env.PHOTOS.put(key, parsed.bytes, {
    httpMetadata: { contentType: parsed.mimeType }
  });
  return `/api/photos/${key}`;
}

const FUZZY_MAP = {
  O: "0", D: "0", Q: "0",
  I: "1", L: "1", "|": "1",
  Z: "2",
  S: "5",
  B: "8",
  G: "6"
};

function applyFuzzy(text) {
  return text.split("").map(c => FUZZY_MAP[c] || c).join("");
}

async function sendTeamsAlert(webhookUrl, title, text, details) {
  if (!webhookUrl) return;
  try {
    const card = {
      type: "message",
      attachments: [
        {
          contentType: "application/vnd.microsoft.card.adaptive",
          content: {
            $schema: "http://adaptivecards.io/schemas/adaptive-card.json",
            type: "AdaptiveCard",
            version: "1.2",
            body: [
              {
                type: "TextBlock",
                text: title,
                weight: "Bolder",
                size: "Large",
                color: title.includes("成功") ? "Good" : "Attention"
              },
              {
                type: "TextBlock",
                text: text,
                wrap: true
              },
              {
                type: "FactSet",
                facts: [
                  { title: "批號:", value: String(details.batchNo || "無") },
                  { title: "槽號:", value: String(details.tankNo || "無") },
                  { title: "地點:", value: String(details.deliveryPlace || "無") },
                  { title: "供應商:", value: String(details.supplier || "無") },
                  { title: "來源單號:", value: String(details.sourceDocNo || "無") },
                  { title: "地磅單號:", value: String(details.weighbridgeNo || "無") }
                ]
              }
            ]
          }
        }
      ]
    };

    await fetch(webhookUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(card)
    });
  } catch (e) {
    console.error("Teams webhook trigger error:", e);
  }
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
    const rawQrBatch = (input.batchNo || "").trim();
    const rawLoc = (input.deliveryPlace || "").trim();
    const rawTank = (input.tankNo || "").trim();
    const inputSupplier = (input.supplier || "").trim();
    const materialNo = (input.materialNo || "").trim();
    const rawQr = (input.rawQr || "").trim();

    const photoBatch = input.photoBatch || "";
    const photoLoc = input.photoLoc || "";

    if (!photoBatch || !photoLoc) {
      return new Response(JSON.stringify({ success: false, message: "請拍攝 COA 與地磅兩張照片" }), {
        status: 400,
        headers: corsHeaders
      });
    }

    // 1. Google Vision OCR 解析 (向 GAS 或環境要最新 Key)
    const apiKey = await getVisionApiKey(env);
    const [ocrResultBatch, ocrResultLoc] = await Promise.all([
      callGoogleVision(photoBatch, apiKey),
      callGoogleVision(photoLoc, apiKey)
    ]);

    const textCOA = ocrResultBatch?.responses?.[0]?.fullTextAnnotation?.text || "";
    const cleanCOA = textCOA.replace(/\s+/g, "").toUpperCase();

    const textWeigh = ocrResultLoc?.responses?.[0]?.fullTextAnnotation?.text || "";
    const cleanWeigh = textWeigh.replace(/\s+/g, "").toUpperCase();

    // 2. 雙單號截取 (11碼)
    let sourceDocNo = "";
    let weighbridgeNo = "";
    const docMatch = cleanWeigh.match(/(ESXM101-[0-9A-Z]{11})/);
    if (docMatch) sourceDocNo = docMatch[1];
    const weighMatch = cleanWeigh.match(/(ESXM201-[0-9A-Z]{11})/);
    if (weighMatch) weighbridgeNo = weighMatch[1];

    // 3. 供應商補償
    let finalSupplier = inputSupplier;
    if (!finalSupplier) {
      const sMatch1 = textWeigh.match(/供應商[\s:.]*([0-9]{5,})/);
      if (sMatch1) finalSupplier = sMatch1[1];
      else {
        const sMatch2 = cleanWeigh.match(/(3759[0-9]+|1000[0-9]{3,})/);
        if (sMatch2) finalSupplier = sMatch2[1];
      }
    }

    const fuzzyWeigh = applyFuzzy(cleanWeigh);

    // 4. 比對目標準備
    // A. 批號目標
    const cleanRawBatch = rawQrBatch.replace(/\s+/g, "").toUpperCase();
    const batchTargets = [];
    if (cleanRawBatch) {
      batchTargets.push(cleanRawBatch);
      if (cleanRawBatch.startsWith("6") || cleanRawBatch.length >= 11) {
        batchTargets.push(cleanRawBatch.substring(1));
      }
    }

    // B. 槽號目標
    const cleanRawTank = rawTank.replace(/\s+/g, "").toUpperCase();
    let tankTargets = [];
    if (cleanRawTank) {
      tankTargets.push(cleanRawTank);
      if (cleanRawTank.startsWith("5")) tankTargets.push(cleanRawTank.substring(1));
      if (cleanRawTank.length > 3) tankTargets.push(cleanRawTank.substring(1));
      tankTargets = Array.from(new Set(tankTargets));
    }

    // C. 地點目標 (標準版)
    const locTarget = rawLoc.replace(/\s+/g, "").toUpperCase();
    const locTargets = [];
    if (locTarget) {
      locTargets.push(locTarget);
      if (locTarget.length > 3) {
        if (locTarget.startsWith("E")) locTargets.push(locTarget.substring(1));
        if (locTarget.endsWith("A")) locTargets.push(locTarget.slice(0, -1));
        if (locTarget.startsWith("E") && locTarget.endsWith("A")) locTargets.push(locTarget.slice(1, -1));
      }
    }

    // 🛑 關卡 1: COA 批號核對
    let check1_Batch = false;
    if (batchTargets.length > 0) {
      const fuzzyCOA = applyFuzzy(cleanCOA);
      for (const t of batchTargets) {
        const fuzzyT = applyFuzzy(t);
        if (cleanCOA.includes(t) || fuzzyCOA.includes(fuzzyT)) {
          check1_Batch = true;
          break;
        }
      }
    }

    // 🛑 關卡 2: 地磅 地點 (V45 T100 拆解組合比對)
    let check2_Loc = false;
    let locDebugMsg = "";
    if (locTargets.length > 0) {
      for (const lt of locTargets) {
        const fuzzyLT = applyFuzzy(lt);
        if (cleanWeigh.includes(lt) || fuzzyWeigh.includes(fuzzyLT)) {
          check2_Loc = true;
          break;
        }
      }
    }

    if (!check2_Loc && locTarget.length > 5) {
      const sheetCore = locTarget.slice(1, -1);
      const fuzzySheetCore = applyFuzzy(sheetCore);

      let t100_Factory = "";
      let t100_Area = "";

      const facMatch = cleanWeigh.match(/廠別\D*([A-Z0-9]{4})/);
      if (facMatch) t100_Factory = facMatch[1];

      const areaMatch = cleanWeigh.match(/廠區\D*([A-Z0-9]{3})/);
      if (areaMatch) t100_Area = areaMatch[1];

      if (t100_Factory && t100_Area) {
        const t100_Combined = t100_Factory + t100_Area;
        const fuzzy_T100_Combined = applyFuzzy(t100_Combined);

        if (sheetCore === t100_Combined ||
            fuzzySheetCore === fuzzy_T100_Combined ||
            t100_Combined.includes(sheetCore)) {
          check2_Loc = true;
        } else {
          locDebugMsg = `(系統拼湊: ${t100_Combined} vs 單據: ${sheetCore})`;
        }
      }
    }

    // 🛑 關卡 3: 地磅 槽號 (排除批號後的獨立槽號檢查)
    let check3_Tank = false;
    let tankErrorMsg = "";
    if (tankTargets.length === 0) {
      tankErrorMsg = "(QR Code 缺少槽號)";
    } else {
      let textForTankCheck = cleanWeigh;
      let fuzzyTextForTankCheck = fuzzyWeigh;
      for (const bt of batchTargets) {
        textForTankCheck = textForTankCheck.replaceAll(bt, "------");
        const fuzzyBT = applyFuzzy(bt);
        fuzzyTextForTankCheck = fuzzyTextForTankCheck.replaceAll(fuzzyBT, "------");
      }
      for (const tankT of tankTargets) {
        if (!tankT) continue;
        const fuzzyTankT = applyFuzzy(tankT);
        if (textForTankCheck.includes(tankT) || fuzzyTextForTankCheck.includes(fuzzyTankT)) {
          check3_Tank = true;
          break;
        }
      }
      if (!check3_Tank) tankErrorMsg = "(未發現獨立槽號)";
    }

    // 🛑 關卡 4: 地磅 系統批號
    let check4_SystemBatch = false;
    let batchDebugMsg = "";
    if (batchTargets.length > 0) {
      for (const t of batchTargets) {
        const fuzzyT = applyFuzzy(t);
        if (cleanWeigh.includes(t) || fuzzyWeigh.includes(fuzzyT)) {
          check4_SystemBatch = true;
          break;
        }
      }
    }
    if (!check4_SystemBatch) {
      const candidates = cleanWeigh.match(/(26[0-9A-Z]{7,}|626[0-9A-Z]{7,})/g);
      if (candidates && candidates.length > 0) {
        batchDebugMsg = `\n🔍 系統發現疑似: ${candidates.slice(0, 2).join(", ")}`;
      } else {
        batchDebugMsg = `\n🔍 AI 讀到開頭: ${cleanWeigh.slice(0, 15)}...`;
      }
    }

    const isSuccess = check1_Batch && check2_Loc && check3_Tank && check4_SystemBatch;
    let responseMsg = isSuccess ? "✅ 四重核對成功！" : "❌ 核對失敗";
    responseMsg += "\n----------------";
    responseMsg += check1_Batch ? "\n✅ COA批號: OK" : "\n❌ COA批號不符";
    responseMsg += check2_Loc ? "\n✅ 地點: OK" : `\n❌ 地點不符 ${locDebugMsg}`;
    responseMsg += check3_Tank ? "\n✅ 槽號: OK" : `\n❌ 槽號不符 ${tankErrorMsg}`;
    responseMsg += check4_SystemBatch ? "\n✅ 系統批號: OK" : `\n❌ 系統批號不符 ${batchDebugMsg}`;

    if (sourceDocNo) responseMsg += `\n📄 來源: ${sourceDocNo}`;
    if (weighbridgeNo) responseMsg += `\n⚖️ 磅單: ${weighbridgeNo}`;
    if (finalSupplier) responseMsg += `\n🏭 供應商: ${finalSupplier}`;

    // 5. 儲存照片至 Cloudflare R2
    const now = new Date();
    const pad = n => String(n).padStart(2, "0");
    const yyyy = now.getFullYear();
    const mm = pad(now.getMonth() + 1);
    const dd = pad(now.getDate());
    const hh = pad(now.getHours());
    const min = pad(now.getMinutes());
    const ss = pad(now.getSeconds());
    const monthFolder = `${yyyy}${mm}`;
    const timestamp = `${yyyy}${mm}${dd}_${hh}${min}${ss}`;

    const cleanBatchKey = rawQrBatch.replace(/[^A-Za-z0-9]/g, "") || "BATCH";
    const cleanLocKey = rawLoc.replace(/[^A-Za-z0-9]/g, "") || "LOC";

    const file1Key = `coa-photos/${monthFolder}/Batch_${cleanBatchKey}_${timestamp}.jpg`;
    const file2Key = `coa-photos/${monthFolder}/Loc_${cleanLocKey}_${timestamp}.jpg`;

    let photoBatchUrl = "";
    let photoLocUrl = "";

    try {
      const [u1, u2] = await Promise.all([
        saveToR2(env, file1Key, photoBatch),
        saveToR2(env, file2Key, photoLoc)
      ]);
      photoBatchUrl = u1 || "";
      photoLocUrl = u2 || "";
    } catch (r2Err) {
      console.error("R2 Upload error:", r2Err);
    }

    const statusText = isSuccess ? "四重核對成功" : "核對失敗";

    // 6. 雙邊寫入 1: 寫入 Cloudflare D1
    if (env.DB) {
      try {
        await env.DB.prepare(`
          INSERT INTO coa_verification_logs 
          (material_no, tank_no, batch_no, supplier, delivery_place, raw_qr, source_doc_no, weighbridge_no, verification_status, photo_batch_url, photo_loc_url, error_details, ocr_snippet)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        `).bind(
          materialNo,
          rawTank,
          rawQrBatch,
          finalSupplier,
          rawLoc,
          rawQr,
          sourceDocNo,
          weighbridgeNo,
          statusText,
          photoBatchUrl,
          photoLocUrl,
          responseMsg,
          `COA: ${cleanCOA.slice(0, 100)} | 地磅: ${cleanWeigh.slice(0, 100)}`
        ).run();
      } catch (dbErr) {
        console.error("D1 Insert error:", dbErr);
      }
    }

    // 7. 雙邊寫入 2: 同步寫入 Google 試算表 (GAS)
    // 取得完整 R2 照片網址 (包含網域) 方便在 Google Sheet 點開
    const host = request.headers.get("host") || "";
    const protocol = request.headers.get("x-forwarded-proto") || "https";
    const origin = `${protocol}://${host}`;
    const fullPhotoBatchUrl = photoBatchUrl ? `${origin}${photoBatchUrl}` : "";
    const fullPhotoLocUrl = photoLocUrl ? `${origin}${photoLocUrl}` : "";

    const gasPayload = {
      materialNo,
      tankNo: rawTank,
      batchNo: rawQrBatch,
      supplier: finalSupplier,
      deliveryPlace: rawLoc,
      rawQr,
      sourceDocNo,
      weighbridgeNo,
      status: statusText,
      photoBatchUrl: fullPhotoBatchUrl,
      photoLocUrl: fullPhotoLocUrl,
      errorDetails: responseMsg
    };

    if (context.waitUntil) {
      context.waitUntil(syncRecordToGoogleSheets(env, gasPayload));
    } else {
      syncRecordToGoogleSheets(env, gasPayload).catch(e => console.error("GAS sync:", e));
    }

    // 8. Teams Webhook 通知 (優先從試算表「設定」分頁讀取)
    const teamsWebhook = await getTeamsWebhookUrl(env);
    if (teamsWebhook && (!isSuccess || env.ENABLE_TEAMS_ON_SUCCESS === "true")) {
      const title = isSuccess ? "✅ 三合一單與 COA 四重核對成功" : "🚨 三合一單與 COA 核對警報 (失敗)";
      if (context.waitUntil) {
        context.waitUntil(sendTeamsAlert(teamsWebhook, title, responseMsg, {
          batchNo: rawQrBatch,
          tankNo: rawTank,
          deliveryPlace: rawLoc,
          supplier: finalSupplier,
          sourceDocNo,
          weighbridgeNo
        }));
      }
    }

    return new Response(JSON.stringify({
      success: isSuccess,
      message: responseMsg,
      details: {
        check1_Batch,
        check2_Loc,
        check3_Tank,
        check4_SystemBatch,
        sourceDocNo,
        weighbridgeNo,
        supplier: finalSupplier,
        photoBatchUrl,
        photoLocUrl
      }
    }), { headers: corsHeaders });

  } catch (err) {
    return new Response(JSON.stringify({ success: false, message: "系統錯誤: " + err.message }), {
      status: 500,
      headers: corsHeaders
    });
  }
}
