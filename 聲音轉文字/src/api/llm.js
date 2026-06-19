const { getStore } = require('../store');

/**
 * 系統提示詞：僅修正語音辨識錯字，嚴禁過度改寫與潤飾
 */
const SYSTEM_PROMPT = `你是一個語音輸入文字的微調修正助手。
使用者會提供一段語音辨識後的原始文字，你的任務是：
1. 【嚴禁重寫與改寫】：絕對不要重新排列句子、不要改寫句子結構、不要將口語口吻轉換為正式書面語。必須百分之百保留使用者說話的原始語氣與風格。
2. 【僅修正明顯錯別字】：只修正因語音辨識出錯的同音錯字（例如將「園藝」修正為「原意」）。對於任何專有名詞、技術術語、英文單字（如 Keyup, GitHub, API 等），請務必維持原樣，絕對不要刪除或替換。
3. 【僅補上必要標點】：只在語意斷開處補上最基礎的逗號、句號或問號，不要隨意拆分或重組句子。
4. 【嚴格保留所有內容】：絕對不要增添任何原話沒有的詞彙，也不要刪減使用者的任何說話內容。
5. 【絕對禁止擴寫、延伸與補完】：使用者沒有說的話，你絕對不准自行聯想、延伸細節或補充大綱（例如使用者只提到了「資料分析」，絕對不准自行編造其用途或定義）。字數與內容必須與原文高度吻合。
6. 【直接輸出結果】：直接輸出修正後的文字，不要任何解釋或額外說明。`;

/**
 * 使用 OpenAI GPT 潤飾文字
 */
async function polishWithOpenAI(text, apiKey) {
  const response = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: 'gpt-4o-mini',
      max_tokens: 1000,
      temperature: 0.0,
      messages: [
        { role: 'system', content: SYSTEM_PROMPT },
        { role: 'user', content: text },
      ],
    }),
  });

  if (!response.ok) {
    const errText = await response.text();
    throw new Error(`OpenAI LLM 錯誤 (${response.status}): ${errText}`);
  }

  const data = await response.json();
  return (data.choices?.[0]?.message?.content || text).trim();
}

/**
 * 使用 Groq Llama 潤飾文字（免費、速度快）
 */
async function polishWithGroq(text, apiKey) {
  const response = await fetch('https://api.groq.com/openai/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: 'llama-3.3-70b-versatile',
      max_tokens: 1000,
      temperature: 0.0,
      messages: [
        { role: 'system', content: SYSTEM_PROMPT },
        { role: 'user', content: text },
      ],
    }),
  });

  if (!response.ok) {
    const errText = await response.text();
    throw new Error(`Groq LLM 錯誤 (${response.status}): ${errText}`);
  }

  const data = await response.json();
  return (data.choices?.[0]?.message?.content || text).trim();
}

/**
 * 主入口：依照設定選擇潤飾提供者
 * @param {string} rawText - 原始 STT 辨識文字
 * @returns {Promise<string>} - 潤飾後的文字
 */
async function polishText(rawText) {
  const store = getStore();
  const enablePolish = store.get('enablePolish');

  // 若關閉潤飾，直接回傳原文
  if (!enablePolish) {
    console.log('[llm] 潤飾已關閉，直接使用原文');
    return rawText;
  }

  const polishProvider = store.get('polishProvider') || 'openai';

  try {
    if (polishProvider === 'groq') {
      const apiKey = store.get('groqApiKey');
      if (!apiKey) {
        console.warn('[llm] Groq API Key 未設定，跳過潤飾');
        return rawText;
      }
      console.log('[llm] 使用 Groq Llama 潤飾...');
      const result = await polishWithGroq(rawText, apiKey);
      console.log('[llm] 潤飾完成:', result);
      return result;

    } else {
      const apiKey = store.get('openaiApiKey');
      if (!apiKey) {
        console.warn('[llm] OpenAI API Key 未設定，跳過潤飾');
        return rawText;
      }
      console.log('[llm] 使用 OpenAI GPT-4o-mini 潤飾...');
      const result = await polishWithOpenAI(rawText, apiKey);
      console.log('[llm] 潤飾完成:', result);
      return result;
    }

  } catch (err) {
    // 潤飾失敗時不中斷流程，回傳原始文字
    console.error('[llm] 潤飾失敗，使用原始文字:', err.message);
    return rawText;
  }
}

module.exports = { polishText };
