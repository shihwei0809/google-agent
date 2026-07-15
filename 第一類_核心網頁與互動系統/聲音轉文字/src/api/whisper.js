const fs = require('fs');
const path = require('path');
const { getStore } = require('../store');

/**
 * 使用 OpenAI Whisper API 進行語音辨識
 * @param {string} audioFilePath - 音訊檔案路徑
 * @returns {Promise<string>} - 辨識後的文字
 */
async function transcribeWithWhisper(audioFilePath) {
  const store = getStore();
  const apiKey = store.get('openaiApiKey');
  const language = store.get('language') || 'zh-TW';

  if (!apiKey) {
    throw new Error('未設定 OpenAI API Key，請至設定頁面填寫。');
  }

  const audioBuffer = fs.readFileSync(audioFilePath);
  const ext = path.extname(audioFilePath); // .webm 或 .wav
  const mimeType = ext === '.webm' ? 'audio/webm' : 'audio/wav';
  const fileName = `recording${ext}`;
  const langCode = language.split('-')[0];

  const formData = new FormData();
  const blob = new Blob([audioBuffer], { type: mimeType });
  formData.append('file', blob, fileName);
  formData.append('model', 'whisper-1');
  formData.append('language', langCode);
  formData.append('response_format', 'json');
  
  // 💡 優化：加入 prompt 參數引導 Whisper 輸出繁體中文與正確標點，提高原始辨識精準度
  formData.append('prompt', '這是用語音輸入的內容，請使用繁體中文（台灣繁體），並加入適當的標點符號。');

  console.log('[whisper] 開始送出 STT 請求，檔案大小:', audioBuffer.length, 'bytes');

  const response = await fetch('https://api.openai.com/v1/audio/transcriptions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${apiKey}`,
    },
    body: formData,
  });

  if (!response.ok) {
    const errText = await response.text();
    throw new Error(`OpenAI Whisper API 錯誤 (${response.status}): ${errText}`);
  }

  const data = await response.json();
  const text = (data.text || '').trim();
  console.log('[whisper] 辨識結果:', text);
  return text;
}

module.exports = { transcribeWithWhisper };
