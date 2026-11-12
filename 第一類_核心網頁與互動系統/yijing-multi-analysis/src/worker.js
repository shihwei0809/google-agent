const SYSTEM_PROMPT = `你是「易見｜多重命理分析」的專業文化反思與財務策略顧問。
請根據使用者提供的「四柱八字、五行旺衰喜忌、十神格局、易經本卦/互卦/變卦六爻結構與財務問卷參數」，撰寫一份結構清晰、沉穩溫暖、具東方哲學底蘊且高度務實的繁體中文深度綜合解讀。

【嚴格遵守原則】
1. 這是「傳統文化與自我反思」工具：不得將結果寫成保證、宿命預言、醫療診斷、具體個股/幣種推薦或買賣訊號。
2. 【首要任務 - 直面解答提問】：若輸入中包含「使用者特定提問」，請務必在第一章節【使用者特定提問直面解答】以易經卦象（動爻）與八字喜用神，第一時間正面、透徹、具體地給予解答與策略建議，絕對不可略過或避而不答！
3. 必須精準結合輸入提供的【四柱八字（年月日時柱）、日主旺衰、五行喜忌】與【易經本卦、互卦、變卦與動爻辭】，針對該生辰命盤進行獨一無二的客製化深度推演，杜絕模稜兩可的罐頭廢話。
4. 排版規範：請使用清晰的段落與條列式（• 清單），**請勿輸出過度龐大的 ASCII/Markdown 複雜多列表格**，以避免佔用過多 token 導致輸出被截斷。
5. 請依下列五個段落標題依序完整輸出：
   一、【使用者特定提問直面解答】（直擊提問痛點，結合易經動爻與五行喜忌給出核心解答）
   二、【本命八字格局與日元五行定位】（解析日主元神旺衰、十神生剋與調候用神）
   三、【易經本卦、互卦與變卦動爻行動指引】（闡述當前局勢、內在轉折與未來落點）
   四、【正偏財現金流、資產架構與風險紅線交叉診斷】（針對財務目標與風險防線的立體配置建議）
   五、【未來 90 天具體可執行的 3 個關鍵行動步驟】`;

const GROQ_MODELS = [
  'llama-3.3-70b-versatile',
  'llama-3.1-8b-instant',
  'qwen-qwq-32b'
];

const WORKERS_AI_MODELS = [
  '@cf/meta/llama-3.3-70b-instruct-fp8-fast',
  '@cf/meta/llama-3.1-8b-instruct',
  '@cf/qwen/qwen2.5-7b-instruct'
];

async function runGroqFallback(apiKey, userPrompt) {
  let lastError = '';
  for (const model of GROQ_MODELS) {
    try {
      const resp = await fetch('https://api.groq.com/openai/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${apiKey}`
        },
        body: JSON.stringify({
          model,
          messages: [
            { role: 'system', content: SYSTEM_PROMPT },
            { role: 'user', content: userPrompt }
          ],
          temperature: 0.6,
          max_tokens: 3500
        })
      });

      const data = await resp.json().catch(() => ({}));
      if (!resp.ok) {
        const msg = data?.error?.message || `HTTP ${resp.status}`;
        lastError = `[Groq:${model}] ${msg}`;
        continue;
      }

      const text = data?.choices?.[0]?.message?.content?.trim();
      if (text) {
        return {
          ok: true,
          provider: 'Groq Cloud (Built-in)',
          model,
          text
        };
      }
      lastError = `[Groq:${model}] 回傳空內容`;
    } catch (err) {
      lastError = `[Groq:${model}] ${err && err.message ? err.message : String(err)}`;
    }
  }
  return { ok: false, error: lastError };
}

async function runWorkersAiFallback(aiBinding, userPrompt) {
  if (!aiBinding) {
    return { ok: false, error: 'Cloudflare Workers AI 尚未綁定 (env.AI is undefined)' };
  }
  let lastError = '';
  for (const model of WORKERS_AI_MODELS) {
    try {
      const result = await aiBinding.run(model, {
        messages: [
          { role: 'system', content: SYSTEM_PROMPT },
          { role: 'user', content: userPrompt }
        ],
        max_tokens: 2500,
        temperature: 0.6
      });

      const text = result && (result.response || (result.choices && result.choices[0]?.message?.content));
      if (text && String(text).trim()) {
        return {
          ok: true,
          provider: 'Cloudflare Workers AI',
          model,
          text: String(text).trim()
        };
      }
      lastError = `[CF:${model}] 回傳空內容`;
    } catch (err) {
      lastError = `[CF:${model}] ${err && err.message ? err.message : String(err)}`;
    }
  }
  return { ok: false, error: lastError };
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // AI 深度解讀無狀態端點（不儲存任何請求資料）
    if (url.pathname === '/api/ai-insight' && request.method === 'POST') {
      try {
        const body = await request.json();
        const userPrompt = String(body.prompt || '').slice(0, 3500);
        const preferredEngine = String(body.engine || 'groq'); // 'groq' | 'cloudflare'
        if (!userPrompt) {
          return JsonResponse({ ok: false, error: '缺少分析提示內容 (prompt is empty)' }, 400);
        }

        const errors = [];

        // 1. 若選擇 Groq (預設) 且環境具有 GROQ_API_KEY，優先執行 Groq 高速推演
        if (preferredEngine !== 'cloudflare' && env.GROQ_API_KEY) {
          const groqRes = await runGroqFallback(env.GROQ_API_KEY, userPrompt);
          if (groqRes.ok) return JsonResponse(groqRes);
          errors.push(groqRes.error);
        }

        // 2. 自動備援或指定使用 Cloudflare Workers AI
        const cfRes = await runWorkersAiFallback(env.AI, userPrompt);
        if (cfRes.ok) return JsonResponse(cfRes);
        errors.push(cfRes.error);

        // 3. 若原先指定 cloudflare 失敗但有 GROQ_API_KEY，反向備援 Groq
        if (preferredEngine === 'cloudflare' && env.GROQ_API_KEY) {
          const groqBackup = await runGroqFallback(env.GROQ_API_KEY, userPrompt);
          if (groqBackup.ok) return JsonResponse(groqBackup);
          errors.push(groqBackup.error);
        }

        return JsonResponse({
          ok: false,
          error: `內建 AI 引擎皆無法完成回應。最後錯誤：${errors.join(' | ')}`
        }, 502);
      } catch (err) {
        return JsonResponse({
          ok: false,
          error: `伺服器解析請求失敗：${err && err.message ? err.message : String(err)}`
        }, 500);
      }
    }

    const response = await env.ASSETS.fetch(request);
    const headers = new Headers(response.headers);
    headers.set('X-Content-Type-Options', 'nosniff');
    headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
    headers.set('Permissions-Policy', 'camera=(), microphone=(), geolocation=()');
    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers
    });
  }
};

function JsonResponse(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      'Cache-Control': 'no-store',
      'X-Content-Type-Options': 'nosniff'
    }
  });
}
