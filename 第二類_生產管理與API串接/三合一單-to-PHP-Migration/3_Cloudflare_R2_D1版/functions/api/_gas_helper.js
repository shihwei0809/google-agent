// functions/api/_gas_helper.js
// 負責處理：向 GAS 試算表「設定」分頁取得動態金鑰 (Vision + Gemini) 與 Teams Webhook + 雙向同步寫入 Google 試算表

// 防呆過濾器：自動修正試算表中可能被誤植成小寫 l 的 Key
function sanitizeKey(k) {
  if (!k || typeof k !== 'string') return k;
  let clean = k.trim();
  if (clean.includes('AIzaSyCdl7')) {
    clean = clean.replace('AIzaSyCdl7', 'AIzaSyCdI7');
  }
  return clean;
}

// 自動升級已停用的 3.6 / 3.7 模型至 gemini-3.8-flash
function normalizeGeminiModels(models) {
  const rawList = Array.isArray(models) && models.length > 0
    ? models
    : ["gemini-3.8-flash", "gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite"];
  const mapped = rawList.map(m => {
    const clean = String(m || "").trim();
    if (clean === "gemini-3.6-flash" || clean === "gemini-3.7-flash") return "gemini-3.8-flash";
    return clean;
  }).filter(Boolean);
  return Array.from(new Set(mapped));
}

const DEFAULT_TEAMS_WEBHOOK_URL = "https://defaulta46d9e33ad01451aaec52ee61979c6.d0.environment.api.powerplatform.com:443/powerautomate/automations/direct/cu/22/workflows/91b9b15b99a64990bf3f7116c031dea4/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=huhEyZ8m-m8EKJ7JXRmhR-CtuVI83kTLRADHB12g-7k";

// 全域記憶體快取 (減少每次請求重複向 Google 請求所造成的延遲)
let cachedVisionKeys = null;
let cachedGeminiKeys = null;
let cachedGeminiModels = null;
let cachedTeamsWebhookUrl = null;
let lastKeyFetchTime = 0;
const CACHE_TTL_MS = 10 * 60 * 1000; // 快取 10 分鐘

async function fetchConfigFromGas(env) {
  const gasUrl = (env.GAS_WEB_APP_URL || "").trim();
  if (!gasUrl || !gasUrl.startsWith("http")) return null;

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 3000); // 3 秒超時保護

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
        if (Array.isArray(data.geminiKeys) && data.geminiKeys.length > 0) {
          cachedGeminiKeys = data.geminiKeys;
        }
        if (Array.isArray(data.geminiModels) && data.geminiModels.length > 0) {
          cachedGeminiModels = normalizeGeminiModels(data.geminiModels);
        }
        if (data.teamsWebhookUrl) {
          cachedTeamsWebhookUrl = data.teamsWebhookUrl;
        }
        lastKeyFetchTime = Date.now();

        // 同步存入 D1 作為本機快取備援
        if (env.DB) {
          try {
            if (data.visionKeys) {
              for (let idx = 0; idx < data.visionKeys.length; idx++) {
                await env.DB.prepare(
                  "INSERT INTO system_config (key, value, description) VALUES (?, ?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value"
                ).bind(`VISION_API_KEY_${idx + 1}`, data.visionKeys[idx], "從 GAS 同步之 Vision 金鑰").run();
              }
            }
            if (data.geminiKeys) {
              for (let idx = 0; idx < data.geminiKeys.length; idx++) {
                await env.DB.prepare(
                  "INSERT INTO system_config (key, value, description) VALUES (?, ?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value"
                ).bind(`GEMINI_API_KEY_${idx + 1}`, data.geminiKeys[idx], "從 GAS 同步之 Gemini 金鑰").run();
              }
            }
            if (data.teamsWebhookUrl) {
              await env.DB.prepare(
                "INSERT INTO system_config (key, value, description) VALUES (?, ?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value"
              ).bind("TEAMS_WEBHOOK_URL", data.teamsWebhookUrl, "從 GAS 同步之 Teams Webhook").run();
            }
          } catch (e) {}
        }
        return data;
      }
    }
  } catch (gasErr) {
    console.warn("向 GAS 讀取設定逾時或未就緒，啟用降級模式:", gasErr.message);
  }
  return null;
}

/**
 * 取得所有可用之 Google Vision API Key 清單 (從試算表「設定」分頁動態讀取)
 */
export async function getVisionApiKeysList(env) {
  const now = Date.now();
  let keys = [];

  // 1. 記憶體快取
  if (cachedVisionKeys && cachedVisionKeys.length > 0 && (now - lastKeyFetchTime < CACHE_TTL_MS)) {
    keys = cachedVisionKeys;
  } else {
    // 2. 向 GAS 獲取
    const gasData = await fetchConfigFromGas(env);
    if (gasData && Array.isArray(gasData.visionKeys) && gasData.visionKeys.length > 0) {
      keys = gasData.visionKeys;
    } else if (env.DB) {
      // 3. D1 資料庫
      try {
        const { results } = await env.DB.prepare(
          "SELECT value FROM system_config WHERE key LIKE 'VISION_API_KEY%'"
        ).all();
        if (results && results.length > 0) {
          keys = results.map(r => r.value).filter(Boolean);
        }
      } catch (e) {}
    }
  }

  // 4. 合併試算表「設定」分頁與環境變數 Key (不寫死於程式碼)
  const allCandidates = [
    ...keys,
    env.VISION_API_KEY_1,
    env.DEFAULT_VISION_KEY_1,
    env.VISION_API_KEY_2,
    env.DEFAULT_VISION_KEY_2
  ].filter(Boolean).map(sanitizeKey);

  // 去重並嚴格過濾：Google Vision API 金鑰必須以 AIzaSy 開頭 (排除 Gemini 專用之 AQ.Ab8RN 等其他金鑰)
  const validVisionKeys = Array.from(new Set(allCandidates)).filter(k => typeof k === 'string' && k.startsWith('AIzaSy'));
  return validVisionKeys;
}

export async function getVisionApiKey(env) {
  const list = await getVisionApiKeysList(env);
  const sec = new Date().getSeconds();
  return list[sec % list.length];
}

/**
 * 當所有 Google Vision API Key 都用盡或失敗時，自動啟動 Gemini 模型備援 (優先使用 gemini-3.8-flash)
 */
export async function callGeminiFallback(base64Image, env) {
  const now = Date.now();
  if (!cachedGeminiKeys || (now - lastKeyFetchTime >= CACHE_TTL_MS)) {
    await fetchConfigFromGas(env);
  }

  let geminiKeys = cachedGeminiKeys || [];
  if (geminiKeys.length === 0 && env.DB) {
    try {
      const { results } = await env.DB.prepare(
        "SELECT value FROM system_config WHERE key LIKE 'GEMINI_API_KEY%'"
      ).all();
      if (results && results.length > 0) {
        geminiKeys = results.map(r => r.value).filter(Boolean);
      }
    } catch (e) {}
  }

  const validGeminiKeys = geminiKeys.filter(k => typeof k === 'string' && k.startsWith('AIzaSy'));
  const models = normalizeGeminiModels(cachedGeminiModels);
  if (validGeminiKeys.length === 0 || models.length === 0) return null;

  const cleanBase64 = base64Image.includes(',') ? base64Image.split(',')[1] : base64Image;

  for (const modelName of models) {
    for (const apiKey of validGeminiKeys) {
      try {
        const url = `https://generativelanguage.googleapis.com/v1beta/models/${modelName}:generateContent?key=${apiKey}`;
        const res = await fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            contents: [{
              parts: [
                { text: "請將這張圖片裡的所有文字完整讀取出來，不要加上任何額外的說明或引號。" },
                { inlineData: { mimeType: "image/jpeg", data: cleanBase64 } }
              ]
            }]
          })
        });
        if (!res.ok) continue;
        const json = await res.json();
        const text = json?.candidates?.[0]?.content?.parts?.[0]?.text;
        if (text) {
          console.log(`✅ Gemini Fallback (${modelName}) 備援辨識成功`);
          return text;
        }
      } catch (e) {
        console.warn(`Gemini (${modelName}) 呼叫異常:`, e.message);
      }
    }
  }
  return null;
}

/**
 * 取得 Teams Webhook 網址 (優先從試算表「設定」分頁讀取)
 */
export async function getTeamsWebhookUrl(env) {
  const now = Date.now();
  if (cachedTeamsWebhookUrl && (now - lastKeyFetchTime < CACHE_TTL_MS)) {
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
    } catch (e) {}
  }

  return env.TEAMS_WEBHOOK_URL || env.DEFAULT_TEAMS_WEBHOOK_URL || DEFAULT_TEAMS_WEBHOOK_URL;
}

/**
 * 雙邊寫入：將核對資料同步推送到 Google 試算表 (GAS)
 */
export async function syncRecordToGoogleSheets(env, recordPayload) {
  const gasUrl = (env.GAS_WEB_APP_URL || "").trim();
  if (!gasUrl || !gasUrl.startsWith("http")) {
    console.log("未配置 GAS_WEB_APP_URL，略過 Google 試算表雙向寫入");
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
    console.log("GAS 試算表雙向寫入結果:", result);
  } catch (err) {
    console.error("同步至 Google 試算表失敗:", err.message);
  }
}
