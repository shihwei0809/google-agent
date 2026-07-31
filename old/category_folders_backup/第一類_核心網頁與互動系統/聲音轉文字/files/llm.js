const { getStore } = require('../store');

/**
 * 系統提示詞：移除贅詞、修正標點、潤飾文法
 */
const SYSTEM_PROMPT = `你是一個專業的中文文字潤飾助手。
使用者會提供一段語音辨識後的原始文字，你的任務是：
1. 移除口語贅詞（例如：「那個」「就是說」「嗯」「啊」「然後」等填充詞）
2. 修正標點符號（加入適當的逗號、句號、問號）
3. 修正文法錯誤，使句子更通順自然
4. 保留原意，不要增加或刪除實質內容
5. 直接輸出潤飾後的文字，不要任何解釋或額外說明
6. 若原文已經很好，直接原文輸出即可`;

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
      temperature: 0.3,
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
      temperature: 0.3,
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
