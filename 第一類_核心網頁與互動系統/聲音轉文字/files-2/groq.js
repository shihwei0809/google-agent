const fs = require('fs');
const { getStore } = require('../store');

/**
 * 使用 Groq Whisper API 進行語音辨識
 * @param {string} audioFilePath - WAV 音訊檔案路徑
 * @returns {Promise<string>} - 辨識後的文字
 */
async function transcribeWithGroq(audioFilePath) {
  const store = getStore();
  const apiKey = store.get('groqApiKey');
  const language = store.get('language') || 'zh-TW';
  const langCode = language.split('-')[0];

  if (!apiKey) {
    throw new Error('未設定 Groq API Key，請至設定頁面填寫。');
  }

  const audioBuffer = fs.readFileSync(audioFilePath);
  console.log('[groq] WAV 大小:', audioBuffer.length, 'bytes');

  const formData = new FormData();
  const blob = new Blob([audioBuffer], { type: 'audio/wav' });
  formData.append('file', blob, 'recording.wav');
  formData.append('model', 'whisper-large-v3-turbo');
  formData.append('language', langCode);
  formData.append('response_format', 'json');

  console.log('[groq] 送出 STT 請求...');

  const response = await fetch('https://api.groq.com/openai/v1/audio/transcriptions', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${apiKey}` },
    body: formData,
  });

  if (!response.ok) {
    const errText = await response.text();
    console.error('[groq] API 錯誤:', errText);
    throw new Error(`Groq Whisper API 錯誤 (${response.status}): ${errText}`);
  }

  const data = await response.json();
  const text = (data.text || '').trim();
  console.log('[groq] 辨識結果:', text);
  return text;
}

module.exports = { transcribeWithGroq };
