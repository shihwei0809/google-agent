// Cloudflare Pages Functions API: /api/verify
// 核心四重核對引擎 + Cloudflare R2 照片儲存 + D1 紀錄 + Google 試算表 (GAS) 雙向同步 + Teams 警報推播

import { getVisionApiKeysList, callGeminiFallback, getTeamsWebhookUrl, syncRecordToGoogleSheets } from "./_gas_helper.js";

async function callGoogleVisionWithRetry(base64Image, keyList, env) {
  let cleanB64 = base64Image;
  if (cleanB64.includes(",")) {
    cleanB64 = cleanB64.split(",")[1];
  }
  cleanB64 = cleanB64.replace(/\s/g, "");

  let lastError = null;
  for (const apiKey of keyList) {
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
          return json;
        }
        lastError = new Error(`Google Vision API 錯誤: ${json.error.message}`);
      } else {
        const errText = await response.text();
        lastError = new Error(`Google Vision API 失敗 (${response.status}): ${errText}`);
      }
      console.warn(`Vision API Key [${apiKey.slice(0, 10)}...] 失敗，切換下一把金鑰重試...`);
    } catch (err) {
      lastError = err;
    }
  }

  // 當所有 Vision API Key 都用完或失敗時，自動切換至 Gemini 模型備援 (優先 gemini-3.8-flash)
  if (env) {
    const geminiText = await callGeminiFallback(base64Image, env);
    if (geminiText !== null) {
      return {
        responses: [{ fullTextAnnotation: { text: geminiText } }]
      };
    }
  }

  throw lastError || new Error("所有 Google Vision 與 Gemini 備援 API 金鑰皆已用盡或無法連線");
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
  if (!text) return "";
  return text.split("").map(c => FUZZY_MAP[c] || c).join("");
}

// 完整對齊 GAS advancedFuzzyCheck + 螢幕摩爾紋單字漏讀容錯 (末4碼流水槽號必須100%相符)
function advancedFuzzyCheck(ocrText, target, isBatchOnScreen = false) {
  if (!ocrText || !target) return false;
  const cleanOCR = ocrText.toUpperCase().replace(/[\s\-:：]/g, "");
  const cleanTarget = target.toUpperCase().replace(/[\s\-:：]/g, "");
  if (!cleanTarget) return false;

  function testMatch(t) {
    if (!t) return false;
    if (cleanOCR.includes(t)) return true;
    if (cleanOCR.includes(t.replace(/8/g, "B"))) return true;
    if (cleanOCR.includes(t.replace(/B/g, "8"))) return true;
    if (cleanOCR.includes(t.replace(/3/g, "5"))) return true;
    if (cleanOCR.includes(t.replace(/5/g, "3"))) return true;
    const variant1 = t.replace(/3/g, "5").replace(/8/g, "B");
    if (cleanOCR.includes(variant1)) return true;
    const variant2 = t.replace(/5/g, "3").replace(/B/g, "8");
    if (cleanOCR.includes(variant2)) return true;
    if (applyFuzzy(cleanOCR).includes(applyFuzzy(t))) return true;

    // 針對地磅電腦螢幕拍攝之 10 碼批號 (如 26B09E3061)，容許螢幕網格干擾造成前段單一字元漏讀 (如 26B9E3061 或 26B093071)，但末 4 碼流水槽號必須 100% 精確一致
    if (isBatchOnScreen && t.length >= 9) {
      const suffix4 = t.slice(-4);
      const prefix = t.slice(0, -4);
      for (let i = 1; i < prefix.length; i++) {
        const droppedOne = prefix.slice(0, i) + prefix.slice(i + 1) + suffix4;
        if (cleanOCR.includes(droppedOne) || applyFuzzy(cleanOCR).includes(applyFuzzy(droppedOne))) {
          return true;
        }
      }
    }
    return false;
  }

  if (testMatch(cleanTarget)) return true;
  if (/^\d/.test(cleanTarget)) {
    const noPrefix = cleanTarget.substring(1);
    if (noPrefix.length >= 3 && testMatch(noPrefix)) return true;
  }
  return false;
}

function smartLocationCheck(cleanWeigh, fuzzyWeigh, locTarget) {
  if (!cleanWeigh || !locTarget) return { pass: false, debug: "" };

  const target = locTarget.replace(/\s+/g, "").toUpperCase();
  const cleanOCR = cleanWeigh.replace(/\s+/g, "").toUpperCase();
  const fWeigh = fuzzyWeigh || applyFuzzy(cleanOCR);

  // 1. 完全命中 (或模糊全字串命中)
  if (cleanOCR.includes(target) || fWeigh.includes(applyFuzzy(target))) {
    return { pass: true, debug: "" };
  }

  // 2. 去除開頭 E、只有在結尾為 'A' 時才去除結尾 (絕不可誤截尾碼數字如 '2')
  let core = target;
  if (core.startsWith("E")) core = core.substring(1);

  let coreNoA = core;
  if (coreNoA.endsWith("A") && coreNoA.length > 5) {
    coreNoA = coreNoA.slice(0, -1);
  }

  // 候選清單直接比對
  const candidates = Array.from(new Set([core, coreNoA]));
  for (const cand of candidates) {
    if (cand && (cleanOCR.includes(cand) || fWeigh.includes(applyFuzzy(cand)))) {
      return { pass: true, debug: "" };
    }
  }

  // 3. GAS 經典雙重判定 (前4碼廠別 + 後續碼廠區，同在單據內即可)
  // 例: EF180L182 -> 去E為 F180L182 -> 廠別 F180, 廠區 L182 (或 182)
  for (const cand of candidates) {
    if (cand.length >= 7) {
      const part1 = cand.substring(0, 4); // 廠別 (如 F180, 1550, 0070)
      const part2 = cand.substring(4);    // 廠區 (如 L182, 183B, 156, 0001)

      const part2Variants = [part2];
      if (part2.startsWith("L") && part2.length > 1) {
        part2Variants.push(part2.substring(1)); // 支援去 L: 182
      }

      const part1Fuzzy = applyFuzzy(part1);
      const hasPart1 = cleanOCR.includes(part1) || fWeigh.includes(part1Fuzzy);
      const hasPart2 = part2Variants.some(p2 => cleanOCR.includes(p2) || fWeigh.includes(applyFuzzy(p2)));

      if (hasPart1 && hasPart2) {
        return { pass: true, debug: "" };
      }

      // 支援 2 與 3 螢幕反光雙向容錯 (GAS 經典機制)
      const r23OCR = cleanOCR.replace(/2/g, "3");
      const r23P1 = part1.replace(/2/g, "3");
      const r23HasP1 = r23OCR.includes(r23P1);
      const r23HasP2 = part2Variants.some(p2 => r23OCR.includes(p2.replace(/2/g, "3")));
      if (r23HasP1 && r23HasP2) {
        return { pass: true, debug: "" };
      }
    }
  }

  // 4. T100 欄位拼湊比對 (廠別 + 廠區)
  let t100_Factory = "";
  let t100_Area = "";
  const facMatch = cleanOCR.match(/廠別\D*([A-Z0-9]{4})/);
  if (facMatch) t100_Factory = facMatch[1];
  const areaMatch = cleanOCR.match(/廠區\D*([A-Z0-9]{3,4})/);
  if (areaMatch) t100_Area = areaMatch[1];

  if (t100_Factory && t100_Area) {
    const t100_Combined = t100_Factory + t100_Area;
    const fuzzyCombined = applyFuzzy(t100_Combined);

    for (const cand of candidates) {
      const candNoL = cand.replace(/([A-Z0-9]{4})L/, "$1"); // F180L182 -> F180182
      if (cand === t100_Combined ||
          applyFuzzy(cand) === fuzzyCombined ||
          candNoL === t100_Combined ||
          applyFuzzy(candNoL) === fuzzyCombined ||
          t100_Combined.includes(cand) ||
          cand.includes(t100_Combined)) {
        return { pass: true, debug: "" };
      }
    }
    return {
      pass: false,
      debug: `(系統拼湊: ${t100_Combined} vs 單據: ${core})`
    };
  }

  return { pass: false, debug: `(單據地點: ${core})` };
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

    // 1. Google Vision OCR 解析 (向 GAS 或環境要最新 Key 清單，若 Vision Key 全數用盡則自動切換 Gemini 3.8 備援)
    const keyList = await getVisionApiKeysList(env);
    const [ocrResultBatch, ocrResultLoc] = await Promise.all([
      callGoogleVisionWithRetry(photoBatch, keyList, env),
      callGoogleVisionWithRetry(photoLoc, keyList, env)
    ]);

    const textCOA = ocrResultBatch?.responses?.[0]?.fullTextAnnotation?.text || "";
    const cleanCOA = textCOA.replace(/\s+/g, "").toUpperCase();

    const textWeigh = ocrResultLoc?.responses?.[0]?.fullTextAnnotation?.text || "";
    const cleanWeigh = textWeigh.replace(/\s+/g, "").toUpperCase();

    // 2. 雙單號截取 (相容 GAS 空白修復與完整編號)
    let sourceDocNo = "";
    let weighbridgeNo = "";
    const fixedOcr = textWeigh.replace(/E\s+S\s+X\s+M/gi, "ESXM").replace(/ESXM\s+/gi, "ESXM");
    const docMatch = fixedOcr.match(/\b(ESXM1[A-Z0-9\-]+)/i) || cleanWeigh.match(/(ESXM101-[0-9A-Z]{8,11})/);
    if (docMatch) sourceDocNo = docMatch[1];
    const weighMatch = fixedOcr.match(/\b(ESXM2[A-Z0-9\-]+)/i) || cleanWeigh.match(/(ESXM201-[0-9A-Z]{8,11})/);
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

    // 4. 比對目標準備 (100% 對齊 GAS)
    // A. 批號目標
    const cleanRawBatch = rawQrBatch.replace(/\s+/g, "").toUpperCase();
    const batchTargets = [];
    if (cleanRawBatch) {
      batchTargets.push(cleanRawBatch);
      if (cleanRawBatch.startsWith("6") && cleanRawBatch.length > 1) {
        batchTargets.push(cleanRawBatch.substring(1));
      } else if (cleanRawBatch.length >= 11) {
        batchTargets.push(cleanRawBatch.substring(1, 11));
        batchTargets.push(cleanRawBatch.substring(1));
      }
    }

    // B. 槽號目標
    const cleanRawTank = rawTank.replace(/\s+/g, "").toUpperCase();
    let tankTargets = [];
    if (cleanRawTank) {
      tankTargets.push(cleanRawTank);
      if (cleanRawTank.startsWith("5") && cleanRawTank.length > 1) {
        tankTargets.push(cleanRawTank.substring(1));
      } else if (cleanRawTank.length > 3) {
        tankTargets.push(cleanRawTank.substring(1));
      }
      tankTargets = Array.from(new Set(tankTargets));
    }

    // C. 地點目標
    const locTarget = rawLoc.replace(/\s+/g, "").toUpperCase();

    // 🛑 關卡 1: COA 批號核對 (使用 GAS advancedFuzzyCheck 雙向容錯)
    let check1_Batch = false;
    if (batchTargets.length > 0) {
      for (const t of batchTargets) {
        if (advancedFuzzyCheck(textCOA, t, false)) {
          check1_Batch = true;
          break;
        }
      }
    }

    // 🛑 關卡 2: 地磅 地點 (智慧核對：包含 GAS 雙重相符 + 反光容錯 + T100 拼湊)
    const locResult = smartLocationCheck(cleanWeigh, fuzzyWeigh, locTarget);
    const check2_Loc = locResult.pass;
    const locDebugMsg = locResult.debug ? ` ${locResult.debug}` : "";

    // 🛑 關卡 3: 地磅 槽號 (排除批號後的獨立槽號檢查 + GAS fallback)
    let check3_Tank = false;
    let tankErrorMsg = "";
    if (tankTargets.length === 0) {
      tankErrorMsg = "(QR Code 缺少槽號)";
    } else {
      let textForTankCheck = textWeigh.toUpperCase();
      for (const bt of batchTargets) {
        if (bt.length > 5) {
          textForTankCheck = textForTankCheck.split(bt).join("------");
        }
      }
      for (const tankT of tankTargets) {
        if (!tankT) continue;
        if (advancedFuzzyCheck(textForTankCheck, tankT, false) || advancedFuzzyCheck(textWeigh, tankT, false)) {
          check3_Tank = true;
          break;
        }
      }
      if (!check3_Tank) tankErrorMsg = "(未發現獨立槽號)";
    }

    // 🛑 關卡 4: 地磅 系統批號 (支援 GAS B<->8, 3<->5 及電腦螢幕摩爾紋單字容錯)
    let check4_SystemBatch = false;
    let batchDebugMsg = "";
    if (batchTargets.length > 0) {
      for (const t of batchTargets) {
        if (advancedFuzzyCheck(textWeigh, t, true)) {
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
    let responseMsg = isSuccess ? "✅ 四重核對成功！" : "❌ 核對失敗 (禁止入料！此筆資料【未存檔】)";
    responseMsg += "\n----------------";
    responseMsg += check1_Batch ? "\n✅ COA批號: OK" : "\n❌ COA批號不符";
    responseMsg += check2_Loc ? "\n✅ 地點: OK" : `\n❌ 地點不符 ${locDebugMsg}`;
    responseMsg += check3_Tank ? "\n✅ 槽號: OK" : `\n❌ 槽號不符 ${tankErrorMsg}`;
    responseMsg += check4_SystemBatch ? "\n✅ 系統批號: OK" : `\n❌ 系統批號不符 ${batchDebugMsg}`;

    if (sourceDocNo) responseMsg += `\n📄 來源: ${sourceDocNo}`;
    if (weighbridgeNo) responseMsg += `\n⚖️ 磅單: ${weighbridgeNo}`;
    if (finalSupplier) responseMsg += `\n🏭 供應商: ${finalSupplier}`;

    if (!isSuccess) {
      responseMsg += "\n\n🛑 錯誤阻擋：單據規格或照片不符，請立即現場糾正！此錯誤資料【絕不上傳】，請重新拍照或掃描！";
    }

    // 5. 核心鐵律：只有核對「成功」(isSuccess === true) 才上傳 R2 照片、才寫入 D1 與 Google 試算表正式庫！
    // 若核對失敗，絕不上傳照片、絕不寫入正式紀錄表！
    let photoBatchUrl = "";
    let photoLocUrl = "";
    const statusText = isSuccess ? "四重核對成功" : "核對失敗";

    if (isSuccess) {
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

      // 6. 雙邊寫入 1: 寫入 Cloudflare D1 (僅限核對成功之正式紀錄)
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

      // 7. 雙邊寫入 2: 同步寫入 Google 試算表 (GAS 僅限核對成功才同步寫入 Data 表)
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
        success: true,
        photoBatchUrl: fullPhotoBatchUrl,
        photoLocUrl: fullPhotoLocUrl,
        errorDetails: responseMsg
      };

      if (context.waitUntil) {
        context.waitUntil(syncRecordToGoogleSheets(env, gasPayload));
      } else {
        syncRecordToGoogleSheets(env, gasPayload).catch(e => console.error("GAS sync:", e));
      }
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
