/**
 * Secure Backend Netlify Function: groq-chat.js
 * 
 * 部署說明：
 * 1. 本地啟動：在根目錄執行 `netlify dev`，前端呼叫 `/.netlify/functions/groq-chat`
 * 2. 雲端部署：將 `GROQ_API_KEY` 加入 Netlify 後台 Site env vars。
 */

const fetch = require('node-fetch');

exports.handler = async function(event, context) {
  // 僅允許 POST 請求
  if (event.httpMethod !== 'POST') {
    return {
      statusCode: 405,
      body: JSON.stringify({ error: 'Method Not Allowed' })
    };
  }

  try {
    const { messages, model } = JSON.parse(event.body);

    if (!messages || !Array.isArray(messages)) {
      return {
        statusCode: 400,
        body: JSON.stringify({ error: 'Missing or invalid messages array' })
      };
    }

    const apiKey = process.env.GROQ_API_KEY;
    
    // 如果沒有配置金鑰，回傳提醒 (便於本機離線排錯)
    if (!apiKey) {
      return {
        statusCode: 401,
        body: JSON.stringify({ 
          error: 'Backend API key missing. Please configure GROQ_API_KEY in your server environment variables.' 
        })
      };
    }

    // 發送給 Groq
    const response = await fetch('https://api.groq.com/openai/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model: model || 'llama-3.3-70b-versatile',
        messages: messages,
        temperature: 0.7
      })
    });

    const data = await response.json();

    if (!response.ok) {
      return {
        statusCode: response.status,
        body: JSON.stringify({ error: data.error?.message || 'Groq API error' })
      };
    }

    // 將回覆安全傳回前端
    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        reply: data.choices[0].message.content
      })
    };

  } catch (error) {
    return {
      statusCode: 500,
      body: JSON.stringify({ error: 'Internal server error: ' + error.message })
    };
  }
};
