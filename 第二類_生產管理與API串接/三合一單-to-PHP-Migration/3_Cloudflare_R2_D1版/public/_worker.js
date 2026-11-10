// 3_Cloudflare_R2_D1版/functions/api/_gas_helper.js
function sanitizeKey(k) {
  if (!k || typeof k !== "string") return k;
  let clean = k.trim();
  if (clean.includes("AIzaSyCdl7")) {
    clean = clean.replace("AIzaSyCdl7", "AIzaSyCdI7");
  }
  return clean;
}
var DEFAULT_TEAMS_WEBHOOK_URL = "https://defaulta46d9e33ad01451aaec52ee61979c6.d0.environment.api.powerplatform.com:443/powerautomate/automations/direct/cu/22/workflows/91b9b15b99a64990bf3f7116c031dea4/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=huhEyZ8m-m8EKJ7JXRmhR-CtuVI83kTLRADHB12g-7k";
var cachedVisionKeys = null;
var cachedTeamsWebhookUrl = null;
var lastKeyFetchTime = 0;
var CACHE_TTL_MS = 10 * 60 * 1e3;
async function fetchConfigFromGas(env) {
  const gasUrl = (env.GAS_WEB_APP_URL || "").trim();
  if (!gasUrl || !gasUrl.startsWith("http")) return null;
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 3e3);
    const res = await fetch(gasUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "getConfig" }),
      signal: controller.signal
    });
    clearTimeout(timeoutId);
    if (res.ok) {
      const data = await res.json();
      if (data && data.success) {
        if (Array.isArray(data.visionKeys) && data.visionKeys.length > 0) {
          cachedVisionKeys = data.visionKeys;
        }
        if (data.teamsWebhookUrl) {
          cachedTeamsWebhookUrl = data.teamsWebhookUrl;
        }
        lastKeyFetchTime = Date.now();
        if (env.DB) {
          try {
            if (data.visionKeys) {
              for (let idx = 0; idx < data.visionKeys.length; idx++) {
                await env.DB.prepare(
                  "INSERT INTO system_config (key, value, description) VALUES (?, ?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value"
                ).bind(`VISION_API_KEY_${idx + 1}`, data.visionKeys[idx], "\u5F9E GAS \u540C\u6B65\u4E4B Vision \u91D1\u9470").run();
              }
            }
            if (data.teamsWebhookUrl) {
              await env.DB.prepare(
                "INSERT INTO system_config (key, value, description) VALUES (?, ?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value"
              ).bind("TEAMS_WEBHOOK_URL", data.teamsWebhookUrl, "\u5F9E GAS \u540C\u6B65\u4E4B Teams Webhook").run();
            }
          } catch (e) {
          }
        }
        return data;
      }
    }
  } catch (gasErr) {
    console.warn("\u5411 GAS \u8B80\u53D6\u8A2D\u5B9A\u903E\u6642\u6216\u672A\u5C31\u7DD2\uFF0C\u555F\u7528\u964D\u7D1A\u6A21\u5F0F:", gasErr.message);
  }
  return null;
}
async function getVisionApiKeysList(env) {
  const now = Date.now();
  let keys = [];
  if (cachedVisionKeys && cachedVisionKeys.length > 0 && now - lastKeyFetchTime < CACHE_TTL_MS) {
    keys = cachedVisionKeys;
  } else {
    const gasData = await fetchConfigFromGas(env);
    if (gasData && Array.isArray(gasData.visionKeys) && gasData.visionKeys.length > 0) {
      keys = gasData.visionKeys;
    } else if (env.DB) {
      try {
        const { results } = await env.DB.prepare(
          "SELECT value FROM system_config WHERE key LIKE 'VISION_API_KEY%'"
        ).all();
        if (results && results.length > 0) {
          keys = results.map((r) => r.value).filter(Boolean);
        }
      } catch (e) {
      }
    }
  }
  const allCandidates = [
    ...keys,
    env.VISION_API_KEY_1,
    env.DEFAULT_VISION_KEY_1,
    env.VISION_API_KEY_2,
    env.DEFAULT_VISION_KEY_2
  ].filter(Boolean).map(sanitizeKey);
  const validVisionKeys = Array.from(new Set(allCandidates)).filter((k) => typeof k === "string" && k.startsWith("AIzaSy"));
  return validVisionKeys;
}
async function getTeamsWebhookUrl(env) {
  const now = Date.now();
  if (cachedTeamsWebhookUrl && now - lastKeyFetchTime < CACHE_TTL_MS) {
    return cachedTeamsWebhookUrl;
  }
  const gasData = await fetchConfigFromGas(env);
  if (gasData && gasData.teamsWebhookUrl) {
    return gasData.teamsWebhookUrl;
  }
  if (env.DB) {
    try {
      const row = await env.DB.prepare("SELECT value FROM system_config WHERE key = 'TEAMS_WEBHOOK_URL'").first();
      if (row && row.value) return row.value;
    } catch (e) {
    }
  }
  return env.TEAMS_WEBHOOK_URL || env.DEFAULT_TEAMS_WEBHOOK_URL || DEFAULT_TEAMS_WEBHOOK_URL;
}
async function syncRecordToGoogleSheets(env, recordPayload) {
  const gasUrl = (env.GAS_WEB_APP_URL || "").trim();
  if (!gasUrl || !gasUrl.startsWith("http")) {
    console.log("\u672A\u914D\u7F6E GAS_WEB_APP_URL\uFF0C\u7565\u904E Google \u8A66\u7B97\u8868\u96D9\u5411\u5BEB\u5165");
    return;
  }
  try {
    const res = await fetch(gasUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action: "sync_record",
        ...recordPayload
      })
    });
    const result = await res.json();
    console.log("GAS \u8A66\u7B97\u8868\u96D9\u5411\u5BEB\u5165\u7D50\u679C:", result);
  } catch (err) {
    console.error("\u540C\u6B65\u81F3 Google \u8A66\u7B97\u8868\u5931\u6557:", err.message);
  }
}

// 3_Cloudflare_R2_D1版/functions/api/verify.js
async function callGoogleVisionWithRetry(base64Image, keyList) {
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
        return await response.json();
      }
      const errText = await response.text();
      lastError = new Error(`Google Vision API \u5931\u6557 (${response.status}): ${errText}`);
      console.warn(`Vision API Key [${apiKey.slice(0, 10)}...] \u5931\u6557\uFF0C\u5207\u63DB\u4E0B\u4E00\u628A\u91D1\u9470\u91CD\u8A66...`);
    } catch (err) {
      lastError = err;
    }
  }
  throw lastError || new Error("\u6240\u6709 Google Vision API \u91D1\u9470\u7686\u7121\u6CD5\u9023\u7DDA");
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
var FUZZY_MAP = {
  O: "0",
  D: "0",
  Q: "0",
  I: "1",
  L: "1",
  "|": "1",
  Z: "2",
  S: "5",
  B: "8",
  G: "6"
};
function applyFuzzy(text) {
  if (!text) return "";
  return text.split("").map((c) => FUZZY_MAP[c] || c).join("");
}
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
  if (cleanOCR.includes(target) || fWeigh.includes(applyFuzzy(target))) {
    return { pass: true, debug: "" };
  }
  let core = target;
  if (core.startsWith("E")) core = core.substring(1);
  let coreNoA = core;
  if (coreNoA.endsWith("A") && coreNoA.length > 5) {
    coreNoA = coreNoA.slice(0, -1);
  }
  const candidates = Array.from(/* @__PURE__ */ new Set([core, coreNoA]));
  for (const cand of candidates) {
    if (cand && (cleanOCR.includes(cand) || fWeigh.includes(applyFuzzy(cand)))) {
      return { pass: true, debug: "" };
    }
  }
  for (const cand of candidates) {
    if (cand.length >= 7) {
      const part1 = cand.substring(0, 4);
      const part2 = cand.substring(4);
      const part2Variants = [part2];
      if (part2.startsWith("L") && part2.length > 1) {
        part2Variants.push(part2.substring(1));
      }
      const part1Fuzzy = applyFuzzy(part1);
      const hasPart1 = cleanOCR.includes(part1) || fWeigh.includes(part1Fuzzy);
      const hasPart2 = part2Variants.some((p2) => cleanOCR.includes(p2) || fWeigh.includes(applyFuzzy(p2)));
      if (hasPart1 && hasPart2) {
        return { pass: true, debug: "" };
      }
      const r23OCR = cleanOCR.replace(/2/g, "3");
      const r23P1 = part1.replace(/2/g, "3");
      const r23HasP1 = r23OCR.includes(r23P1);
      const r23HasP2 = part2Variants.some((p2) => r23OCR.includes(p2.replace(/2/g, "3")));
      if (r23HasP1 && r23HasP2) {
        return { pass: true, debug: "" };
      }
    }
  }
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
      const candNoL = cand.replace(/([A-Z0-9]{4})L/, "$1");
      if (cand === t100_Combined || applyFuzzy(cand) === fuzzyCombined || candNoL === t100_Combined || applyFuzzy(candNoL) === fuzzyCombined || t100_Combined.includes(cand) || cand.includes(t100_Combined)) {
        return { pass: true, debug: "" };
      }
    }
    return {
      pass: false,
      debug: `(\u7CFB\u7D71\u62FC\u6E4A: ${t100_Combined} vs \u55AE\u64DA: ${core})`
    };
  }
  return { pass: false, debug: `(\u55AE\u64DA\u5730\u9EDE: ${core})` };
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
                color: title.includes("\u6210\u529F") ? "Good" : "Attention"
              },
              {
                type: "TextBlock",
                text,
                wrap: true
              },
              {
                type: "FactSet",
                facts: [
                  { title: "\u6279\u865F:", value: String(details.batchNo || "\u7121") },
                  { title: "\u69FD\u865F:", value: String(details.tankNo || "\u7121") },
                  { title: "\u5730\u9EDE:", value: String(details.deliveryPlace || "\u7121") },
                  { title: "\u4F9B\u61C9\u5546:", value: String(details.supplier || "\u7121") },
                  { title: "\u4F86\u6E90\u55AE\u865F:", value: String(details.sourceDocNo || "\u7121") },
                  { title: "\u5730\u78C5\u55AE\u865F:", value: String(details.weighbridgeNo || "\u7121") }
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
async function onRequest(context) {
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
      return new Response(JSON.stringify({ success: false, message: "\u8ACB\u62CD\u651D COA \u8207\u5730\u78C5\u5169\u5F35\u7167\u7247" }), {
        status: 400,
        headers: corsHeaders
      });
    }
    const keyList = await getVisionApiKeysList(env);
    const [ocrResultBatch, ocrResultLoc] = await Promise.all([
      callGoogleVisionWithRetry(photoBatch, keyList),
      callGoogleVisionWithRetry(photoLoc, keyList)
    ]);
    const textCOA = ocrResultBatch?.responses?.[0]?.fullTextAnnotation?.text || "";
    const cleanCOA = textCOA.replace(/\s+/g, "").toUpperCase();
    const textWeigh = ocrResultLoc?.responses?.[0]?.fullTextAnnotation?.text || "";
    const cleanWeigh = textWeigh.replace(/\s+/g, "").toUpperCase();
    let sourceDocNo = "";
    let weighbridgeNo = "";
    const fixedOcr = textWeigh.replace(/E\s+S\s+X\s+M/gi, "ESXM").replace(/ESXM\s+/gi, "ESXM");
    const docMatch = fixedOcr.match(/\b(ESXM1[A-Z0-9\-]+)/i) || cleanWeigh.match(/(ESXM101-[0-9A-Z]{8,11})/);
    if (docMatch) sourceDocNo = docMatch[1];
    const weighMatch = fixedOcr.match(/\b(ESXM2[A-Z0-9\-]+)/i) || cleanWeigh.match(/(ESXM201-[0-9A-Z]{8,11})/);
    if (weighMatch) weighbridgeNo = weighMatch[1];
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
    const locTarget = rawLoc.replace(/\s+/g, "").toUpperCase();
    let check1_Batch = false;
    if (batchTargets.length > 0) {
      for (const t of batchTargets) {
        if (advancedFuzzyCheck(textCOA, t, false)) {
          check1_Batch = true;
          break;
        }
      }
    }
    const locResult = smartLocationCheck(cleanWeigh, fuzzyWeigh, locTarget);
    const check2_Loc = locResult.pass;
    const locDebugMsg = locResult.debug ? ` ${locResult.debug}` : "";
    let check3_Tank = false;
    let tankErrorMsg = "";
    if (tankTargets.length === 0) {
      tankErrorMsg = "(QR Code \u7F3A\u5C11\u69FD\u865F)";
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
      if (!check3_Tank) tankErrorMsg = "(\u672A\u767C\u73FE\u7368\u7ACB\u69FD\u865F)";
    }
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
        batchDebugMsg = `
\u{1F50D} \u7CFB\u7D71\u767C\u73FE\u7591\u4F3C: ${candidates.slice(0, 2).join(", ")}`;
      } else {
        batchDebugMsg = `
\u{1F50D} AI \u8B80\u5230\u958B\u982D: ${cleanWeigh.slice(0, 15)}...`;
      }
    }
    const isSuccess = check1_Batch && check2_Loc && check3_Tank && check4_SystemBatch;
    let responseMsg = isSuccess ? "\u2705 \u56DB\u91CD\u6838\u5C0D\u6210\u529F\uFF01" : "\u274C \u6838\u5C0D\u5931\u6557 (\u7981\u6B62\u5165\u6599\uFF01\u6B64\u7B46\u8CC7\u6599\u3010\u672A\u5B58\u6A94\u3011)";
    responseMsg += "\n----------------";
    responseMsg += check1_Batch ? "\n\u2705 COA\u6279\u865F: OK" : "\n\u274C COA\u6279\u865F\u4E0D\u7B26";
    responseMsg += check2_Loc ? "\n\u2705 \u5730\u9EDE: OK" : `
\u274C \u5730\u9EDE\u4E0D\u7B26 ${locDebugMsg}`;
    responseMsg += check3_Tank ? "\n\u2705 \u69FD\u865F: OK" : `
\u274C \u69FD\u865F\u4E0D\u7B26 ${tankErrorMsg}`;
    responseMsg += check4_SystemBatch ? "\n\u2705 \u7CFB\u7D71\u6279\u865F: OK" : `
\u274C \u7CFB\u7D71\u6279\u865F\u4E0D\u7B26 ${batchDebugMsg}`;
    if (sourceDocNo) responseMsg += `
\u{1F4C4} \u4F86\u6E90: ${sourceDocNo}`;
    if (weighbridgeNo) responseMsg += `
\u2696\uFE0F \u78C5\u55AE: ${weighbridgeNo}`;
    if (finalSupplier) responseMsg += `
\u{1F3ED} \u4F9B\u61C9\u5546: ${finalSupplier}`;
    if (!isSuccess) {
      responseMsg += "\n\n\u{1F6D1} \u932F\u8AA4\u963B\u64CB\uFF1A\u55AE\u64DA\u898F\u683C\u6216\u7167\u7247\u4E0D\u7B26\uFF0C\u8ACB\u7ACB\u5373\u73FE\u5834\u7CFE\u6B63\uFF01\u6B64\u932F\u8AA4\u8CC7\u6599\u3010\u7D55\u4E0D\u4E0A\u50B3\u3011\uFF0C\u8ACB\u91CD\u65B0\u62CD\u7167\u6216\u6383\u63CF\uFF01";
    }
    let photoBatchUrl = "";
    let photoLocUrl = "";
    const statusText = isSuccess ? "\u56DB\u91CD\u6838\u5C0D\u6210\u529F" : "\u6838\u5C0D\u5931\u6557";
    if (isSuccess) {
      const now = /* @__PURE__ */ new Date();
      const pad = (n) => String(n).padStart(2, "0");
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
            `COA: ${cleanCOA.slice(0, 100)} | \u5730\u78C5: ${cleanWeigh.slice(0, 100)}`
          ).run();
        } catch (dbErr) {
          console.error("D1 Insert error:", dbErr);
        }
      }
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
        syncRecordToGoogleSheets(env, gasPayload).catch((e) => console.error("GAS sync:", e));
      }
    }
    const teamsWebhook = await getTeamsWebhookUrl(env);
    if (teamsWebhook && (!isSuccess || env.ENABLE_TEAMS_ON_SUCCESS === "true")) {
      const title = isSuccess ? "\u2705 \u4E09\u5408\u4E00\u55AE\u8207 COA \u56DB\u91CD\u6838\u5C0D\u6210\u529F" : "\u{1F6A8} \u4E09\u5408\u4E00\u55AE\u8207 COA \u6838\u5C0D\u8B66\u5831 (\u5931\u6557)";
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
    return new Response(JSON.stringify({ success: false, message: "\u7CFB\u7D71\u932F\u8AA4: " + err.message }), {
      status: 500,
      headers: corsHeaders
    });
  }
}

// 3_Cloudflare_R2_D1版/functions/api/ai-read.js
async function callGoogleVisionWithRetry2(base64Image, keyList) {
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
        return { data: await response.json(), usedKey: apiKey };
      }
      const errText = await response.text();
      lastError = new Error(`Google Vision API \u547C\u53EB\u5931\u6557 (${response.status}): ${errText}`);
    } catch (err) {
      lastError = err;
    }
  }
  throw lastError || new Error("\u6240\u6709 Google Vision API \u91D1\u9470\u7686\u7121\u6CD5\u9023\u7DDA");
}
async function onRequest2(context) {
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
      return new Response(JSON.stringify({ success: false, message: "\u672A\u6536\u5230\u7167\u7247\u8CC7\u6599" }), {
        status: 400,
        headers: corsHeaders
      });
    }
    const keyList = await getVisionApiKeysList(env);
    const { data: ocrResult, usedKey } = await callGoogleVisionWithRetry2(photoData, keyList);
    const text = ocrResult?.responses?.[0]?.fullTextAnnotation?.text || "";
    const cleanText = text.replace(/：/g, ":").replace(/　/g, " ").replace(/\|/g, " ");
    const data = {
      batchNo: "",
      tankNo: "",
      materialNo: "",
      deliveryPlace: "",
      supplier: ""
    };
    let m = cleanText.match(/送達地點[\s:.]*([E|F][0-9A-Z]+)/);
    if (m) data.deliveryPlace = m[1];
    else {
      m = cleanText.match(/地點[\s:.]*([E|F][0-9A-Z]+)/);
      if (m) data.deliveryPlace = m[1];
    }
    m = cleanText.match(/供應商[\s:.]*([0-9]+)/);
    if (m) data.supplier = m[1];
    m = cleanText.match(/料號[\s:.]*([A-Z0-9]+)/);
    if (m) data.materialNo = m[1];
    m = cleanText.match(/槽號[\s:.]*([0-9A-Z]+)/);
    if (m) data.tankNo = m[1];
    m = cleanText.match(/批號[\s:.]*([0-9A-Z]+)/);
    if (m) data.batchNo = m[1];
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
    if (env.DB) {
      try {
        await env.DB.prepare(
          "INSERT INTO api_logs (api_type, model_name, key_snippet, status, note) VALUES (?, ?, ?, ?, ?)"
        ).bind("VISION_AI_READ", "Google-Vision-OCR", (usedKey || "").slice(0, 8) + "...", "SUCCESS", `\u6279\u865F: ${data.batchNo || "\u672A\u8B80\u5230"}`).run();
      } catch (logErr) {
        console.error("D1 log error:", logErr);
      }
    }
    return new Response(JSON.stringify({ success: true, data, rawText: text.slice(0, 300) }), {
      headers: corsHeaders
    });
  } catch (err) {
    return new Response(JSON.stringify({ success: false, message: "AI \u8B80\u55AE\u5931\u6557: " + err.message }), {
      status: 500,
      headers: corsHeaders
    });
  }
}

// 3_Cloudflare_R2_D1版/functions/api/config.js
async function onRequest3(context) {
  const { request, env } = context;
  const corsHeaders = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Content-Type": "application/json; charset=utf-8"
  };
  if (request.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }
  try {
    if (request.method === "GET") {
      let configs = {};
      if (env.DB) {
        try {
          const { results } = await env.DB.prepare("SELECT key, value, description FROM system_config").all();
          if (results) {
            results.forEach((r) => {
              configs[r.key] = r.value;
            });
          }
        } catch (e) {
        }
      }
      const mask = (str) => str ? str.slice(0, 6) + "******" + str.slice(-4) : "";
      return new Response(JSON.stringify({
        success: true,
        data: {
          hasD1: !!env.DB,
          hasR2: !!env.PHOTOS,
          visionKey1Masked: mask(configs.VISION_API_KEY_1 || env.VISION_API_KEY_1 || env.DEFAULT_VISION_KEY_1),
          visionKey2Masked: mask(configs.VISION_API_KEY_2 || env.VISION_API_KEY_2 || env.DEFAULT_VISION_KEY_2),
          teamsWebhookConfigured: !!(configs.TEAMS_WEBHOOK_URL || env.TEAMS_WEBHOOK_URL || env.DEFAULT_TEAMS_WEBHOOK_URL)
        }
      }), { headers: corsHeaders });
    }
    if (request.method === "POST") {
      if (!env.DB) {
        return new Response(JSON.stringify({ success: false, message: "\u7121 D1 \u7D81\u5B9A\uFF0C\u7121\u6CD5\u5132\u5B58\u8A2D\u5B9A" }), {
          status: 400,
          headers: corsHeaders
        });
      }
      const body = await request.json();
      const { key, value } = body;
      if (!key || value === void 0) {
        return new Response(JSON.stringify({ success: false, message: "\u7F3A\u5C11 key \u6216 value" }), {
          status: 400,
          headers: corsHeaders
        });
      }
      await env.DB.prepare(
        "INSERT INTO system_config (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value"
      ).bind(key, String(value)).run();
      return new Response(JSON.stringify({ success: true, message: `\u8A2D\u5B9A [${key}] \u5DF2\u66F4\u65B0` }), {
        headers: corsHeaders
      });
    }
    return new Response("Method not allowed", { status: 405 });
  } catch (err) {
    return new Response(JSON.stringify({ success: false, message: err.message }), {
      status: 500,
      headers: corsHeaders
    });
  }
}

// 3_Cloudflare_R2_D1版/functions/api/query.js
async function onRequest4(context) {
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
        message: "D1 \u8CC7\u6599\u5EAB\u672A\u7D81\u5B9A",
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
        conditions.push("(verification_status LIKE '%\u6210\u529F%' OR verification_status LIKE '%\u5408\u683C%')");
      } else {
        conditions.push("(verification_status LIKE '%\u5931\u6557%' OR verification_status LIKE '%\u672A\u901A\u904E%')");
      }
    }
    const whereClause = conditions.length > 0 ? "WHERE " + conditions.join(" AND ") : "";
    const countSql = `SELECT COUNT(*) as total FROM coa_verification_logs ${whereClause}`;
    const countStmt = env.DB.prepare(countSql);
    const countResult = await (params.length > 0 ? countStmt.bind(...params) : countStmt).first();
    const total = countResult ? countResult.total : 0;
    const totalPages = Math.ceil(total / limit) || 1;
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
    return new Response(JSON.stringify({ success: false, message: "\u67E5\u8A62\u5931\u6557: " + err.message }), {
      status: 500,
      headers: corsHeaders
    });
  }
}

// 3_Cloudflare_R2_D1版/functions/api/sync-from-gas.js
async function onRequest5(context) {
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
      const materialNo = (r.material_no || r.materialNo || r["\u6599\u865F"] || "").trim();
      const tankNo = (r.tank_no || r.tankNo || r["\u69FD\u865F"] || "").trim();
      const batchNo = (r.batch_no || r.batchNo || r["\u6279\u865F"] || "").trim();
      const supplier = (r.supplier || r["\u4F9B\u61C9\u5546"] || "").trim();
      const deliveryPlace = (r.delivery_place || r.deliveryPlace || r["\u9001\u9054\u5730\u9EDE"] || "").trim();
      const rawQr = (r.raw_qr || r.rawQr || r["\u539F\u59CBQR"] || "").trim();
      const sourceDocNo = (r.source_doc_no || r.sourceDocNo || r["\u4F86\u6E90\u55AE\u865F"] || "").trim();
      const weighbridgeNo = (r.weighbridge_no || r.weighbridgeNo || r["\u78C5\u55AE"] || r["\u78C5\u55AE\u865F"] || "").trim();
      let status = (r.verification_status || r.verificationStatus || r.status || r["\u72C0\u614B"] || "\u6838\u5C0D\u6210\u529F").trim();
      if (!status) status = "\u6838\u5C0D\u6210\u529F";
      const photoBatchUrl = (r.photo_batch_url || r.photoBatchUrl || r["COA\u7167\u7247"] || "").trim();
      const photoLocUrl = (r.photo_loc_url || r.photoLocUrl || r["\u5730\u78C5\u7167\u7247"] || "").trim();
      const errorDetails = (r.error_details || r.errorDetails || "").trim();
      const ocrSnippet = (r.ocr_snippet || r.ocrSnippet || "").trim();
      let createdAt = (r.created_at || r.createdAt || r["\u6642\u9593"] || "").trim();
      if (createdAt) {
        try {
          if (createdAt.includes("\u4E0B\u5348") || createdAt.includes("\u4E0A\u5348")) {
            const isPM = createdAt.includes("\u4E0B\u5348");
            const cleanStr = createdAt.replace("\u4E0B\u5348", "").replace("\u4E0A\u5348", "").trim();
            const parts = cleanStr.split(" ");
            const dateParts = parts[0].split(/[/-]/);
            const timeParts = (parts[1] || "00:00:00").split(":");
            let hour = parseInt(timeParts[0], 10);
            if (isPM && hour < 12) hour += 12;
            if (!isPM && hour === 12) hour = 0;
            const pad = (n) => String(n).padStart(2, "0");
            createdAt = `${dateParts[0]}-${pad(dateParts[1])}-${pad(dateParts[2])} ${pad(hour)}:${pad(timeParts[1] || 0)}:${pad(timeParts[2] || 0)}`;
          } else {
            const d = new Date(createdAt);
            if (!isNaN(d.getTime())) {
              const pad = (n) => String(n).padStart(2, "0");
              createdAt = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
            }
          }
        } catch (e) {
        }
      } else {
        const now = /* @__PURE__ */ new Date();
        const pad = (n) => String(n).padStart(2, "0");
        createdAt = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`;
      }
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
      message: `\u540C\u6B65\u5B8C\u6210\uFF01\u65B0\u589E ${inserted} \u7B46\uFF0C\u7565\u904E\u91CD\u8907 ${skipped} \u7B46\u3002`,
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
      message: `\u4F3A\u670D\u5668\u540C\u6B65\u767C\u751F\u932F\u8AA4: ${err.message}`
    }), {
      status: 500,
      headers: corsHeaders
    });
  }
}

// 3_Cloudflare_R2_D1版/functions/api/photos/[[path]].js
async function onRequest6(context) {
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
    const key = Array.isArray(params.path) ? params.path.join("/") : params.path || "";
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
    const ifNoneMatch = request.headers.get("if-none-match");
    if (ifNoneMatch && (ifNoneMatch === object.httpEtag || ifNoneMatch === `W/"${object.httpEtag}"`)) {
      return new Response(null, { headers, status: 304 });
    }
    return new Response(object.body, { headers });
  } catch (err) {
    return new Response("Error fetching photo: " + err.message, { status: 500 });
  }
}

// <stdin>
var stdin_default = {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const pathname = url.pathname;
    const context = {
      request,
      env,
      params: {},
      waitUntil: (p) => ctx && ctx.waitUntil ? ctx.waitUntil(p) : p,
      next: () => env.ASSETS.fetch(request),
      data: {}
    };
    try {
      if (pathname === "/api/verify") {
        return await onRequest(context);
      }
      if (pathname === "/api/ai-read") {
        return await onRequest2(context);
      }
      if (pathname === "/api/config") {
        return await onRequest3(context);
      }
      if (pathname === "/api/query") {
        return await onRequest4(context);
      }
      if (pathname === "/api/sync-from-gas") {
        return await onRequest5(context);
      }
      if (pathname.startsWith("/api/photos")) {
        const rest = pathname.replace(/^\/api\/photos\/?/, "");
        context.params = { path: rest ? rest.split("/") : [] };
        return await onRequest6(context);
      }
      return await env.ASSETS.fetch(request);
    } catch (err) {
      console.error("Pages Functions Error:", err);
      return new Response(JSON.stringify({ success: false, message: "\u4F3A\u670D\u5668\u57F7\u884C\u932F\u8AA4: " + err.message }), {
        status: 500,
        headers: { "Content-Type": "application/json; charset=utf-8" }
      });
    }
  }
};
export {
  stdin_default as default
};
