const fs = require('fs');
const path = require('path');
const { getStore } = require('../store');

/**
 * 使用 Groq Whisper API 進行語音辨識
 * @param {string} audioFilePath - 音訊檔案路徑
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
  const ext = path.extname(audioFilePath); // .webm 或 .wav
  const mimeType = ext === '.webm' ? 'audio/webm' : 'audio/wav';
  const fileName = `recording${ext}`;

  console.log('[groq] 音訊大小:', audioBuffer.length, 'bytes, 格式:', mimeType);

  const formData = new FormData();
  const blob = new Blob([audioBuffer], { type: mimeType });
  formData.append('file', blob, fileName);
  formData.append('model', 'whisper-large-v3-turbo');
  formData.append('language', langCode);
  formData.append('response_format', 'json');
  
  // 💡 優化：加入 prompt 參數引導 Whisper 輸出繁體中文與適當標點
  formData.append('prompt', '這是語音輸入，請輸出繁體中文（台灣繁體），並加上合適的標點符號。');

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
