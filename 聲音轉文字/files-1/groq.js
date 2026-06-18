const fs = require('fs');
const { getStore } = require('../store');

/**
 * 使用 Groq Whisper API 進行語音辨識（免費、速度快）
 * @param {string} audioFilePath - 音訊檔案路徑（.ogg）
 * @returns {Promise<string>} - 辨識後的文字
 */
async function transcribeWithGroq(audioFilePath) {
  const store = getStore();
  const apiKey = store.get('groqApiKey');
  const language = store.get('language') || 'zh-TW';
  const langCode = language.split('-')[0]; // zh-TW → zh

  if (!apiKey) {
    throw new Error('未設定 Groq API Key，請至設定頁面填寫。');
  }

  const audioBuffer = fs.readFileSync(audioFilePath);
  console.log('[groq] 音訊大小:', audioBuffer.length, 'bytes');

  // 使用 FormData 上傳（ogg 格式，Groq 支援）
  const formData = new FormData();
  const blob = new Blob([audioBuffer], { type: 'audio/ogg' });
  formData.append('file', blob, 'recording.ogg');
  formData.append('model', 'whisper-large-v3-turbo');
  formData.append('language', langCode);
  formData.append('response_format', 'json');

  console.log('[groq] 送出 STT 請求...');

  const response = await fetch('https://api.groq.com/openai/v1/audio/transcriptions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${apiKey}`,
    },
    body: formData,
  });

  if (!response.ok) {
    const errText = await response.text();
    console.error('[groq] API 錯誤回應:', errText);
    throw new Error(`Groq Whisper API 錯誤 (${response.status}): ${errText}`);
  }

  const data = await response.json();
  const text = (data.text || '').trim();
  console.log('[groq] 辨識結果:', text);
  return text;
}

module.exports = { transcribeWithGroq };
