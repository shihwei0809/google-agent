export async function onRequest(context) {
  const { request, env } = context;
  const url = new URL(request.url);

  const corsHeaders = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Content-Type": "application/json;charset=utf-8"
  };

  if (request.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const payload = request.method === "POST"
      ? await request.json()
      : Object.fromEntries(url.searchParams);
    const { action, username } = payload;
    const pin = payload.password !== undefined ? payload.password : payload.pin;
    const db = env.DB;

    if (!db) {
      throw new Error("D1 資料庫 (DB) 尚未綁定，請檢查 Cloudflare Pages 設定");
    }

    // 0. 自助註冊新帳號（完全開放）
    if (action === "register") {
      const cleanUser = String(username || "").trim();
      const cleanPwd = String(pin || "").trim();
      validateUsernameFormat(cleanUser);
      validatePasswordFormat(cleanPwd);

      const exists = await db.prepare(
        "SELECT username FROM sk_users WHERE LOWER(username) = LOWER(?)"
      ).bind(cleanUser).first();
      if (exists) throw new Error("此使用者名稱已被註冊，請換一個名稱");

      const hashed = await hashPassword(cleanPwd);
      await db.batch([
        db.prepare("INSERT INTO sk_users (username, pin) VALUES (?, ?)").bind(cleanUser, hashed),
        db.prepare("INSERT INTO sk_summary (category, content, username) VALUES (?, ?, ?)")
          .bind("目前狀態", "新建立的個人保養空間！可按右上角「➕ 快速新增產品」拍照建檔，或到「💬 AI 諮詢」讓助理幫你規劃流程。", cleanUser)
      ]);

      const data = await loadUserData(db, cleanUser);
      return jsonResp({ success: true, username: cleanUser, data }, corsHeaders);
    }

    // 1. 登入並讀取個人資料
    if (action === "login") {
      if (!username || !pin) throw new Error("請輸入使用者名稱與密碼");
      const uname = await validateUser(db, username, pin);
      const data = await loadUserData(db, uname);
      return jsonResp({ success: true, username: uname, data }, corsHeaders);
    }

    // 2. 查詢資料庫防忘登記總表（公開唯讀摘要）
    if (action === "getRegistry") {
      const reg = await db.prepare(
        "SELECT system_code, system_name, table_name, description FROM _system_registry ORDER BY system_code, table_name"
      ).all();
      return jsonResp({ success: true, data: reg.results }, corsHeaders);
    }

    // 以下所有敏感操作均須驗證密碼
    const uname = await validateUser(db, username, pin);

    // 2.5 修改密碼
    if (action === "changePassword") {
      const newPwd = String(payload.newPassword || "").trim();
      validatePasswordFormat(newPwd);
      const hashed = await hashPassword(newPwd);
      await db.prepare(
        "UPDATE sk_users SET pin = ? WHERE LOWER(username) = LOWER(?)"
      ).bind(hashed, uname).run();
      return jsonResp({ success: true, data: { success: true, message: "密碼已更新成功" } }, corsHeaders);
    }

    // 3. 儲存勾選狀態
    if (action === "saveChecklist") {
      await db.prepare(
        "INSERT OR REPLACE INTO sk_checklist (username, step_key, value, updated_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)"
      ).bind(uname, payload.key, payload.value ? 1 : 0).run();
      return jsonResp({ success: true, data: { success: true } }, corsHeaders);
    }

    // 4. 清除今日勾選
    if (action === "clearChecklist") {
      await db.prepare("DELETE FROM sk_checklist WHERE LOWER(username) = LOWER(?)").bind(uname).run();
      return jsonResp({ success: true, data: { success: true } }, corsHeaders);
    }

    // 5. 新增保養品（含照片縮圖 image_data）
    if (action === "addNewProduct") {
      const p = payload.productData || {};
      const productName = (p.Product || p.productName || "").trim();
      if (!productName) throw new Error("產品名稱不能為空");

      await db.batch([
        db.prepare("INSERT INTO sk_products (product, status, description, image_data, username) VALUES (?, ?, ?, ?, ?)")
          .bind(productName, p.Status || "適合", p.Description || "", p.ImageData || "", uname),
        db.prepare("INSERT INTO sk_instructions (product, dosage, usage_method, interval_time, attention, username) VALUES (?, ?, ?, ?, ?, ?)")
          .bind(productName, p.Dosage || "", p.UsageMethod || "", p.Interval || "", p.Attention || "", uname)
      ]);

      return jsonResp({
        success: true,
        data: { success: true, message: `成功新增產品：${productName}` }
      }, corsHeaders);
    }

    // 6. 補傳 / 更新現有產品照片
    if (action === "updateProductImage") {
      const productName = (payload.productName || "").trim();
      const imageData = payload.imageData || "";
      if (!productName) throw new Error("缺少產品名稱");
      await db.prepare(
        "UPDATE sk_products SET image_data = ? WHERE LOWER(username) = LOWER(?) AND product = ?"
      ).bind(imageData, uname, productName).run();
      return jsonResp({ success: true, data: { success: true, message: `已更新「${productName}」照片` } }, corsHeaders);
    }

    // 7. 刪除保養品
    if (action === "deleteProduct") {
      const productName = (payload.productName || "").trim();
      if (!productName) throw new Error("缺少產品名稱");
      await db.batch([
        db.prepare("DELETE FROM sk_products WHERE LOWER(username)=LOWER(?) AND product=?").bind(uname, productName),
        db.prepare("DELETE FROM sk_instructions WHERE LOWER(username)=LOWER(?) AND product=?").bind(uname, productName)
      ]);
      return jsonResp({ success: true, data: { success: true, message: `已刪除：${productName}` } }, corsHeaders);
    }

    // 8. AI 拍照辨識保養品並自動填表
    if (action === "analyzeProductImage") {
      const dataUrl = payload.imageBase64 || "";
      if (!dataUrl) throw new Error("未提供圖片資料");

      const match = dataUrl.match(/^data:(image\/[a-zA-Z0-9.+-]+);base64,(.+)$/);
      const mimeType = match ? match[1] : "image/jpeg";
      const base64Data = match ? match[2] : dataUrl;

      const [sum, prod, avoid] = await Promise.all([
        db.prepare("SELECT category, content FROM sk_summary WHERE LOWER(username)=LOWER(?)").bind(uname).all(),
        db.prepare("SELECT product, status FROM sk_products WHERE LOWER(username)=LOWER(?)").bind(uname).all(),
        db.prepare("SELECT do_not, reason FROM sk_avoid_rules").all()
      ]);

      const userCtx =
        "【用戶膚況】\n" + sum.results.map(r => `- ${r.category}: ${r.content}`).join("\n") +
        "\n【避雷規則】\n" + avoid.results.map(r => `- 不要:${r.do_not}(${r.reason})`).join("\n") +
        "\n【現有保養品】" + prod.results.map(r => r.product).join("、");

      const prompt = `請仔細辨識這張保養品照片上的品牌、產品名稱與成分/類型，並對照以下用戶膚況與避雷規則進行專業評估。
${userCtx}

請「只回傳純 JSON 物件」（不要包含 markdown 標記或任何多餘解釋文字），欄位固定如下：
{
  "Product": "品牌＋中文品名 (原文/英文名)",
  "Status": "從以下四選一：非常適合 / 適合 / 穩定後再用 / 目前不建議",
  "Description": "簡潔說明主要成分、功效，以及對該用戶膚況的評估理由（若與現有品重複請註明）",
  "Dosage": "建議單次用量（如：1～2滴管、半顆黃豆、兩指長）",
  "UsageMethod": "建議使用方式（如：手掌輕壓吸收、薄擦全臉）",
  "Interval": "使用頻率或與下一步驟間隔時間（如：30～60秒、一週2次）",
  "Attention": "注意事項與避雷提醒（如：乾燥刺痛時停用、避開眼周、勿與A醛同晚）"
}`;

      const visionResult = await callVisionAnalyze(env, mimeType, base64Data, prompt);
      return jsonResp({ success: true, data: visionResult.parsed, model: visionResult.model }, corsHeaders);
    }

    // 9. AI 諮詢（支援 Cloudflare Workers AI + Gemini 多階降級）
    if (action === "askGemini" || action === "askAi") {
      const question = (payload.question || "").trim();
      if (!question) throw new Error("問題不可為空");
      const engine = payload.engine || "deepseek-r1";

      const [sum, prod, avoid, rout] = await Promise.all([
        db.prepare("SELECT category, content FROM sk_summary WHERE LOWER(username)=LOWER(?)").bind(uname).all(),
        db.prepare("SELECT product, status, description FROM sk_products WHERE LOWER(username)=LOWER(?)").bind(uname).all(),
        db.prepare("SELECT do_not, reason, correct_way FROM sk_avoid_rules").all(),
        db.prepare("SELECT time_of_day, flow FROM sk_routines WHERE LOWER(username)=LOWER(?)").bind(uname).all()
      ]);

      let ctx = "【目前皮膚狀態與主力組合】\n" + sum.results.map(r => `- ${r.category}: ${r.content}`).join("\n");
      ctx += "\n\n【保養產品清單與適合度】\n" + prod.results.map(r => `- ${r.product} (${r.status}): ${r.description}`).join("\n");
      ctx += "\n\n【保養避雷規則】\n" + avoid.results.map(r => `- 不要: ${r.do_not} | 原因: ${r.reason} | 正確做法: ${r.correct_way}`).join("\n");
      ctx += "\n\n【早晚保養流程】\n" + rout.results.map(r => `- ${r.time_of_day}: ${r.flow}`).join("\n");

      const systemInstruction =
        "你是一位專業的個人皮膚保養顧問。請使用繁體中文，根據以下用戶保養資料庫親切、專業、精簡地回答問題。\n" +
        "當用戶皮膚紅腫、刺痛、脫皮時，務必依據避雷規則警告暫停酸類、A醛、高濃度維C，改以修護為主。\n" +
        "【新產品評估】：若用戶詢問資料庫外的新產品，請比對膚況與避雷規則，判定適合度（「非常適合」、「穩定後再用」、「目前不建議」）並說明原因。\n" +
        "【自動登錄】：若用戶明確要求「幫我新增」、「加到資料庫」，回覆最尾端必須附加：\n" +
        '[[ADD_PRODUCT_JSON: {"Product":"產品名稱","Status":"適合度","Description":"用途說明","Dosage":"用量","UsageMethod":"使用方法","Interval":"間隔","Attention":"注意事項"}]]\n\n' +
        `【當前使用者：${uname} 的保養品資料庫】\n${ctx}`;

      let reply = "";
      let usedModel = "";

      if (engine === "deepseek-r1" && env.AI) {
        const cfModels = [
          "@cf/qwen/qwq-32b",
          "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
          "@cf/google/gemma-3-12b-it",
          "@cf/meta/llama-3.1-8b-instruct-fast"
        ];
        let cfLastErr = "";
        for (const cfModel of cfModels) {
          try {
            const aiRes = await env.AI.run(cfModel, {
              messages: [
                { role: "system", content: systemInstruction },
                { role: "user", content: question }
              ],
              max_tokens: 1200,
              temperature: 0.6
            });
            let rawText = aiRes.response || aiRes.choices?.[0]?.message?.content || "";
            if (rawText) {
              reply = rawText.replace(/<think>[\s\S]*?<\/think>/gi, "").trim() || rawText;
              usedModel = `Cloudflare AI (${cfModel})`;
              break;
            }
          } catch (e) {
            cfLastErr = `${cfModel}: ${e.message}`;
          }
        }
        if (!reply) {
          const fallback = await callGeminiFallback(env.GEMINI_API_KEY, systemInstruction, question);
          reply = fallback.text + `\n\n_(Cloudflare AI 備援切換：${cfLastErr})_`;
          usedModel = fallback.model;
        }
      } else {
        const res = await callGeminiFallback(env.GEMINI_API_KEY, systemInstruction, question);
        reply = res.text;
        usedModel = res.model;
      }

      return jsonResp({ success: true, data: reply, model: usedModel }, corsHeaders);
    }

    throw new Error(`未定義的操作類型: ${action}`);
  } catch (err) {
    return jsonResp({ success: false, error: err.message || String(err) }, corsHeaders, 400);
  }
}

function jsonResp(obj, headers, status = 200) {
  return new Response(JSON.stringify(obj), { status, headers });
}

function validateUsernameFormat(username) {
  if (!username || username.length < 2 || username.length > 32) {
    throw new Error("使用者名稱長度需為 2～32 字元");
  }
  if (!/^[a-zA-Z0-9_\u4e00-\u9fff.-]+$/.test(username)) {
    throw new Error("使用者名稱僅支援中英文、數字與 _ . -");
  }
}

function validatePasswordFormat(password) {
  if (!password || password.length < 4 || password.length > 64) {
    throw new Error("密碼長度需為 4～64 字元");
  }
}

function toHex(buf) {
  return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, "0")).join("");
}

function fromHex(hex) {
  const bytes = new Uint8Array(hex.length / 2);
  for (let i = 0; i < bytes.length; i++) {
    bytes[i] = parseInt(hex.slice(i * 2, i * 2 + 2), 16);
  }
  return bytes;
}

async function hashPassword(password, saltBytes = null, iterations = 10000) {
  const salt = saltBytes || crypto.getRandomValues(new Uint8Array(16));
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(password),
    "PBKDF2",
    false,
    ["deriveBits"]
  );
  const bits = await crypto.subtle.deriveBits(
    { name: "PBKDF2", salt, iterations, hash: "SHA-256" },
    key,
    256
  );
  return `pbkdf2$${iterations}$${toHex(salt)}$${toHex(bits)}`;
}

async function verifyPassword(password, stored) {
  if (!stored) return { ok: false, needsUpgrade: false };
  if (stored.startsWith("pbkdf2$")) {
    const parts = stored.split("$");
    if (parts.length !== 4) return { ok: false, needsUpgrade: false };
    const iterations = parseInt(parts[1], 10);
    const salt = fromHex(parts[2]);
    const expected = parts[3];
    const computed = await hashPassword(password, salt, iterations);
    const computedHash = computed.split("$")[3];
    if (computedHash.length !== expected.length) return { ok: false, needsUpgrade: false };
    let diff = 0;
    for (let i = 0; i < expected.length; i++) {
      diff |= expected.charCodeAt(i) ^ computedHash.charCodeAt(i);
    }
    return { ok: diff === 0, needsUpgrade: false };
  }
  return { ok: stored === password, needsUpgrade: stored === password };
}

async function loadUserData(db, uname) {
  const [summary, products, instructions, routines, sunscreens, avoidRules, dupes, checklist] = await Promise.all([
    db.prepare("SELECT id, category as Category, content as Content FROM sk_summary WHERE LOWER(username)=LOWER(?) ORDER BY id").bind(uname).all(),
    db.prepare("SELECT id, product as Product, status as Status, description as Description, COALESCE(image_data, '') as ImageData FROM sk_products WHERE LOWER(username)=LOWER(?) ORDER BY id").bind(uname).all(),
    db.prepare("SELECT id, product as Product, dosage as Dosage, usage_method as UsageMethod, interval_time as Interval, attention as Attention FROM sk_instructions WHERE LOWER(username)=LOWER(?) ORDER BY id").bind(uname).all(),
    db.prepare("SELECT id, time_of_day as TimeOfDay, flow as Flow FROM sk_routines WHERE LOWER(username)=LOWER(?) ORDER BY id").bind(uname).all(),
    db.prepare("SELECT id, rank as Rank, product as Product, score as Score, position as Position, recommendation as Recommendation FROM sk_sunscreens ORDER BY id").all(),
    db.prepare("SELECT id, do_not as DoNot, reason as Reason, correct_way as CorrectWay FROM sk_avoid_rules ORDER BY id").all(),
    db.prepare("SELECT id, original_product as OriginalProduct, dupe_product as DupeProduct, category as Category FROM sk_dupes ORDER BY id").all(),
    db.prepare("SELECT step_key, value FROM sk_checklist WHERE LOWER(username)=LOWER(?)").bind(uname).all()
  ]);

  const checklistMap = {};
  checklist.results.forEach(r => { checklistMap[r.step_key] = (r.value === 1); });

  return {
    summary: summary.results,
    products: products.results,
    instructions: instructions.results,
    routines: routines.results,
    sunscreens: sunscreens.results,
    avoidRules: avoidRules.results,
    dupes: dupes.results,
    checklistState: checklistMap
  };
}

async function validateUser(db, username, pin) {
  if (!username || !pin) throw new Error("認證失敗：未提供帳號或密碼");
  const user = await db.prepare(
    "SELECT username, pin FROM sk_users WHERE LOWER(username) = LOWER(?)"
  ).bind(String(username).trim()).first();
  if (!user) throw new Error("帳號或密碼錯誤");

  const check = await verifyPassword(String(pin).trim(), user.pin);
  if (!check.ok) throw new Error("帳號或密碼錯誤");

  // 舊明碼帳號於首次驗證通過時無痛升級為 PBKDF2 雜湊
  if (check.needsUpgrade) {
    try {
      const upgraded = await hashPassword(String(pin).trim());
      await db.prepare("UPDATE sk_users SET pin = ? WHERE username = ?")
        .bind(upgraded, user.username).run();
    } catch (_) {}
  }
  return user.username;
}

function extractJsonObject(text) {
  const cleaned = String(text || "").replace(/```json/gi, "").replace(/```/g, "").trim();
  const m = cleaned.match(/\{[\s\S]*\}/);
  if (!m) throw new Error("AI 回傳格式非 JSON：" + cleaned.slice(0, 120));
  return JSON.parse(m[0]);
}

async function callVisionAnalyze(env, mimeType, base64Data, prompt) {
  let lastError = "";
  const dataUrl = `data:${mimeType};base64,${base64Data}`;

  // 1. 優先使用 Cloudflare Workers AI 多模態視覺模型（原生內網直連、免受 HKG 區域封鎖、秒級回應）
  if (env.AI) {
    const cfVisionModels = [
      "@cf/meta/llama-4-scout-17b-16e-instruct",
      "@cf/google/gemma-3-12b-it"
    ];
    for (const cfModel of cfVisionModels) {
      try {
        const cfRes = await env.AI.run(cfModel, {
          messages: [{
            role: "user",
            content: [
              { type: "text", text: prompt },
              { type: "image_url", image_url: { url: dataUrl } }
            ]
          }],
          max_tokens: 900,
          temperature: 0.2
        });
        const text = cfRes.response || cfRes.choices?.[0]?.message?.content || "";
        if (text) {
          return { parsed: extractJsonObject(text), model: `Cloudflare Vision (${cfModel})` };
        }
      } catch (e) {
        lastError += `${cfModel}: ${e.message} | `;
      }
    }
  }

  // 2. 備援：Google Gemini Flash Vision 多階降級（5s 快速超時防卡死）
  if (env.GEMINI_API_KEY) {
    const models = ["gemini-3.8-flash", "gemini-3.7-flash", "gemini-3.6-flash", "gemini-2.5-flash", "gemini-1.5-flash"];
    for (const model of models) {
      try {
        const res = await fetch(
          `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${env.GEMINI_API_KEY}`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            signal: AbortSignal.timeout(5000),
            body: JSON.stringify({
              contents: [{
                role: "user",
                parts: [
                  { text: prompt },
                  { inlineData: { mimeType, data: base64Data } }
                ]
              }],
              generationConfig: {
                temperature: 0.2,
                maxOutputTokens: 900,
                responseMimeType: "application/json"
              }
            })
          }
        );
        if (res.ok) {
          const json = await res.json();
          const text = json.candidates?.[0]?.content?.parts?.[0]?.text;
          if (text) {
            return { parsed: extractJsonObject(text), model: `Gemini Vision (${model})` };
          }
        } else {
          const errBody = await res.text();
          lastError += `${model} (${res.status}): ${errBody.slice(0, 120)} | `;
        }
      } catch (e) {
        lastError += `${model}: ${e.message} | `;
      }
    }
  }

  throw new Error("圖片辨識失敗：" + (lastError || "無可用的視覺模型"));
}

async function callGeminiFallback(apiKey, systemInstruction, userQuestion) {
  if (!apiKey) {
    return {
      text: "⚠️ 系統尚未設定 GEMINI_API_KEY，建議切換上方引擎使用免費的 Cloudflare Workers AI。",
      model: "none"
    };
  }
  const models = ["gemini-3.8-flash", "gemini-3.7-flash", "gemini-3.6-flash", "gemini-2.5-flash", "gemini-1.5-flash"];
  let lastError = "";

  for (const model of models) {
    try {
      const res = await fetch(
        `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          signal: AbortSignal.timeout(12000),
          body: JSON.stringify({
            contents: [{ role: "user", parts: [{ text: userQuestion }] }],
            systemInstruction: { parts: [{ text: systemInstruction }] },
            generationConfig: { temperature: 0.7, maxOutputTokens: 1200 }
          })
        }
      );
      if (res.ok) {
        const json = await res.json();
        const text = json.candidates?.[0]?.content?.parts?.[0]?.text;
        if (text) return { text, model };
      } else {
        const errBody = await res.text();
        lastError = `${model} (${res.status}): ${errBody.slice(0, 150)}`;
      }
    } catch (e) {
      lastError = `${model}: ${e.message}`;
    }
  }
  return { text: `❌ 所有 Gemini 模型均呼叫失敗。最後錯誤：${lastError}`, model: "error" };
}
