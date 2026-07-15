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
  const language = store.get('language') || 'zh';

  if (!apiKey) {
    throw new Error('未帶身攜 OpenAI API Key，請至設定頁面填寫。');
  }

  const audioBuffer = fs.readFileSync(audioFilePath);
  const fileName = path.basename(audioFilePath);

  // 建立 multipart/form-data
  const boundary = '----NoTypeBoundary' + Date.now();
  const CRLF = '\r\n';

  // 組合 form-data body
  let bodyParts = [];

  // model 欄位
  bodyParts.push(
    `--${boundary}${CRLF}`,
    `Content-Disposition: form-data; name="model"${CRLF}${CRLF}`,
    `whisper-1${CRLF}`
  );

  // language 欄位（取前2碼，例如 zh-TW → zh）
  const langCode = language.split('-')[0];
  bodyParts.push(
    `--${boundary}${CRLF}`,
    `Content-Disposition: form-data; name="language"${CRLF}${CRLF}`,
    `${langCode}${CRLF}`
  );

  // response_format 欄位
  bodyParts.push(
    `--${boundary}${CRLF}`,
    `Content-Disposition: form-data; name="response_format"${CRLF}${CRLF}`,
    `json${CRLF}`
  );

  // file 欄位
  const fileHeader = [
    `--${boundary}${CRLF}`,
    `Content-Disposition: form-data; name="file"; filename="${fileName}"${CRLF}`,
    `Content-Type: audio/webm${CRLF}${CRLF}`,
  ].join('');

  const fileFooter = `${CRLF}--${boundary}--${CRLF}`;

  // 組合完整 body（Buffer）
  const headerBuffer = Buffer.from(bodyParts.join(''), 'utf-8');
  const fileHeaderBuffer = Buffer.from(fileHeader, 'utf-8');
  const fileFooterBuffer = Buffer.from(fileFooter, 'utf-8');
  const body = Buffer.concat([headerBuffer, fileHeaderBuffer, audioBuffer, fileFooterBuffer]);

  console.log('[whisper] 開始送出 STT 請求，檔案大小:', audioBuffer.length, 'bytes');

  const response = await fetch('https://api.openai.com/v1/audio/transcriptions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': `multipart/form-data; boundary=${boundary}`,
    },
    body,
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
