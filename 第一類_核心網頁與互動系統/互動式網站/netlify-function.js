/**
 * Netlify Function: ask-ai.js
 * 
 * 部署說明：
 * 1. 在專案根目錄建立 `netlify/functions/ask-ai.js`。
 * 2. 在 Netlify 後端設定環境變數 `GROQ_API_KEY` 或 `GEMINI_API_KEY`。
 * 3. 前端以 POST 請求呼叫 `/.netlify/functions/ask-ai` 並傳送作答文字。
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
    const { essayAnswer } = JSON.parse(event.body);

    if (!essayAnswer) {
      return {
        statusCode: 400,
        body: JSON.stringify({ error: 'Missing essayAnswer' })
      };
    }

    const apiKey = process.env.GROQ_API_KEY || process.env.GEMINI_API_KEY;
    
    // 如果沒有設定 API Key，則回傳模擬資料 (方便離線開發測試)
    if (!apiKey) {
      const mockResponses = [
        { score: 85, feedback: "【AI 模擬批改】回答結構完整，清楚指出 Lv.4 不存資料與 Lv.5 持久化儲存的差異。若能更具體提及 Firestore 欄位設計會更好。" },
        { score: 95, feedback: "【AI 模擬批改】內容非常精確！詳盡說明了資料流：Lv.4 做完即丟，Lv.5 把批改後的評語和分數一併寫入 Firebase 供長期學習歷程追蹤。" },
        { score: 60, feedback: "【AI 模擬批改】回答較為簡略，僅提到一個存一個不存。建議多加描述兩者對教師教學決策與學習追蹤上的影響。" }
      ];
      
      // 隨機選一個模擬回答
      const mockResult = mockResponses[Math.floor(Math.random() * mockResponses.length)];
      
      return {
        statusCode: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          score: mockResult.score,
          feedback: mockResult.feedback,
          simulated: true
        })
      };
    }

    // 呼叫 Groq Llama3 或 Gemini 進行問答題批改
    // 這裡以 Groq API 為例
    const response = await fetch('https://api.groq.com/openai/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model: 'llama3-8b-8192',
        messages: [
          {
            role: 'system',
            content: '你是一位教育科技專家與程式助教。請批改學生關於「互動式教學網頁 Lv.4（Netlify Functions + AI）與 Lv.5（AI + 資料庫）差別」的簡答題。\n請以繁體中文回答，格式必須為 JSON 格式，只包含 score (0-100) 與 feedback (100字以內具體建議與稱讚)。\n範例格式：{"score": 90, "feedback": "回答非常好..."}'
          },
          {
            role: 'user',
            content: `學生的回答是：\n「${essayAnswer}」\n請依此進行批改，僅回傳合法的 JSON 字串，不要有任何其他多餘敘述。`
          }
        ],
        temperature: 0.3,
        response_format: { type: "json_object" }
      })
    });

    const data = await response.json();
    const aiContent = JSON.parse(data.choices[0].message.content);

    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        score: aiContent.score,
        feedback: aiContent.feedback,
        simulated: false
      })
    };

  } catch (error) {
    return {
      statusCode: 500,
      body: JSON.stringify({ error: 'AI processing failed: ' + error.message })
    };
  }
};
