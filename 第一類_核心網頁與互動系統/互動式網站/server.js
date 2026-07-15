/**
 * Zero-Dependency Local Dev Server (server.js)
 * 
 * 運行方式：
 * 直接在終端機執行：`node server.js`
 * 
 * 特點：
 * - 0% 依賴，無須執行 npm install，本機直接啟動
 * - 自動讀取 `.env` 檔案
 * - 靜態網頁伺服器（Port 8888）
 * - 代理中轉 /netlify/functions/groq-chat (Groq API)
 * - 代理中轉 /netlify/functions/ask-ai (Gemini API)
 */

const http = require('http');
const fs = require('fs');
const path = require('path');
const https = require('https');

// 1. 簡易讀取並解析 .env 檔案
const env = {};
try {
  const envPath = path.join(__dirname, '.env');
  if (fs.existsSync(envPath)) {
    const content = fs.readFileSync(envPath, 'utf8');
    content.split(/\r?\n/).forEach(line => {
      const match = line.match(/^\s*([\w.-]+)\s*=\s*(.*)?\s*$/);
      if (match) {
        let val = match[2] || '';
        // 移除引號
        if (val.startsWith('"') && val.endsWith('"')) val = val.slice(1, -1);
        if (val.startsWith("'") && val.endsWith("'")) val = val.slice(1, -1);
        env[match[1]] = val.trim();
      }
    });
    console.log('✅ 成功載入 .env 環境變數');
  } else {
    console.log('⚠️ 未找到 .env 檔案，將使用系統環境變數');
  }
} catch (e) {
  console.error('讀取 .env 錯誤:', e.message);
}

const PORT = 8888;

// 支援的檔案類型 Mime-Types
const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css',
  '.js': 'application/javascript',
  '.json': 'application/json',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.gif': 'image/gif',
  '.ico': 'image/x-icon'
};

// 2. 建立 HTTP 伺服器
const server = http.createServer((req, res) => {
  const url = new URL(req.url, `http://${req.headers.host}`);
  const pathname = url.pathname;

  console.log(`[${req.method}] ${pathname}`);

  // ─── 代理中轉 1：Groq Chat 對談 ───
  if (pathname === '/.netlify/functions/groq-chat' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      try {
        const { messages, model } = JSON.parse(body);
        const groqKey = env.GROQ_API_KEY || process.env.GROQ_API_KEY;

        if (!groqKey) {
          res.writeHead(401, { 'Content-Type': 'application/json' });
          return res.end(JSON.stringify({ error: '未配置 GROQ_API_KEY，請檢查 .env 檔案。' }));
        }

        // 使用 https 模組向 Groq 發送請求
        const groqReqBody = JSON.stringify({
          model: model || 'llama-3.3-70b-versatile',
          messages: messages,
          temperature: 0.7
        });

        const groqReq = https.request({
          hostname: 'api.groq.com',
          path: '/v1/chat/completions',
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${groqKey}`,
            'Content-Type': 'application/json',
            'Content-Length': Buffer.byteLength(groqReqBody)
          }
        }, (groqRes) => {
          let resData = '';
          groqRes.on('data', chunk => { resData += chunk; });
          groqRes.on('end', () => {
            try {
              const parsed = JSON.parse(resData);
              if (groqRes.statusCode === 200) {
                res.writeHead(200, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ reply: parsed.choices[0].message.content }));
              } else {
                res.writeHead(groqRes.statusCode, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ error: parsed.error?.message || 'Groq API 錯誤' }));
              }
            } catch (err) {
              res.writeHead(500, { 'Content-Type': 'application/json' });
              res.end(JSON.stringify({ error: '解析 Groq 回傳資料失敗' }));
            }
          });
        });

        groqReq.on('error', (err) => {
          res.writeHead(500, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: '連線到 Groq 失敗: ' + err.message }));
        });

        groqReq.write(groqReqBody);
        groqReq.end();

      } catch (err) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: '無效的 JSON 請求' }));
      }
    });
    return;
  }

  // ─── 代理中轉 2：Gemini AI 批改 ───
  if (pathname === '/.netlify/functions/ask-ai' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      try {
        const { essayAnswer } = JSON.parse(body);
        const geminiKey = env.GEMINI_API_KEY || process.env.GEMINI_API_KEY;

        if (!geminiKey) {
          res.writeHead(401, { 'Content-Type': 'application/json' });
          return res.end(JSON.stringify({ error: '未配置 GEMINI_API_KEY' }));
        }

        // 呼叫 Gemini 進行批改 (使用 1.5-flash)
        const geminiReqBody = JSON.stringify({
          contents: [{
            parts: [{
              text: `你是一位教育科技專家與程式助教。請批改學生關於「互動式教學網頁 Lv.4（Netlify Functions + AI）與 Lv.5（AI + 資料庫）差別」的簡答題。\n請以繁體中文回答，格式必須為 JSON 格式，只包含 score (0-100) 與 feedback (100字以內具體建議與稱讚)。\n學生的回答是：\n「${essayAnswer}」\n範例格式：{"score": 90, "feedback": "回答非常好..."}`
            }]
          }],
          generationConfig: {
            responseMimeType: "application/json"
          }
        });

        const geminiReq = https.request({
          hostname: 'generativelanguage.googleapis.com',
          path: `/v1beta/models/gemini-1.5-flash:generateContent?key=${geminiKey}`,
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Content-Length': Buffer.byteLength(geminiReqBody)
          }
        }, (geminiRes) => {
          let resData = '';
          geminiRes.on('data', chunk => { resData += chunk; });
          geminiRes.on('end', () => {
            try {
              const parsed = JSON.parse(resData);
              if (geminiRes.statusCode === 200) {
                const textResult = parsed.candidates[0].content.parts[0].text;
                const grading = JSON.parse(textResult.trim());
                res.writeHead(200, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({
                  score: grading.score,
                  feedback: grading.feedback,
                  simulated: false
                }));
              } else {
                res.writeHead(geminiRes.statusCode, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ error: parsed.error?.message || 'Gemini API 錯誤' }));
              }
            } catch (err) {
              res.writeHead(500, { 'Content-Type': 'application/json' });
              res.end(JSON.stringify({ error: '解析 Gemini 回傳資料失敗' }));
            }
          });
        });

        geminiReq.on('error', (err) => {
          res.writeHead(500, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: '連線到 Gemini 失敗: ' + err.message }));
        });

        geminiReq.write(geminiReqBody);
        geminiReq.end();

      } catch (err) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: '無效的 JSON 請求' }));
      }
    });
    return;
  }

  // ─── 課堂即時同步狀態庫 (Level 3 Multi-user Sync) ───
  // 用於模擬 Firebase Realtime 效果，無須配置與聯網
  if (!global.classState) {
    global.classState = {
      currentSlide: 1,
      answers: { "A": 0, "B": 0, "C": 0, "D": 0 },
      voters: [] // 記錄已投票暱稱，防止重複投票
    };
  }

  // 1. 獲取當前課堂狀態 (Tutor & Student 都會頻繁 polling 此端點)
  if (pathname === '/api/class-state' && req.method === 'GET') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(global.classState));
    return;
  }

  // 2. 講師更新當前投影片頁數 (會自動清除上一題的投票數據)
  if (pathname === '/api/class-state' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      try {
        const { currentSlide } = JSON.parse(body);
        
        // 如果翻頁了，自動重置上一題的學員回答
        if (global.classState.currentSlide !== currentSlide) {
          global.classState.answers = { "A": 0, "B": 0, "C": 0, "D": 0 };
          global.classState.voters = [];
        }
        
        global.classState.currentSlide = currentSlide;
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ status: 'success', classState: global.classState }));
      } catch (e) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: '無效的狀態請求' }));
      }
    });
    return;
  }

  // 3. 學員提交測驗答案 (即時累加，並回傳最新統計)
  if (pathname === '/api/submit-answer' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      try {
        const { nickname, answer } = JSON.parse(body);
        const upperAnswer = (answer || '').toUpperCase();

        if (!nickname) {
          res.writeHead(400, { 'Content-Type': 'application/json' });
          return res.end(JSON.stringify({ error: '暱稱必填' }));
        }

        if (!['A', 'B', 'C', 'D'].includes(upperAnswer)) {
          res.writeHead(400, { 'Content-Type': 'application/json' });
          return res.end(JSON.stringify({ error: '無效的答案選項' }));
        }

        // 防重複投票
        if (global.classState.voters.includes(nickname)) {
          res.writeHead(400, { 'Content-Type': 'application/json' });
          return res.end(JSON.stringify({ error: '你已經提交過答案囉！' }));
        }

        global.classState.answers[upperAnswer]++;
        global.classState.voters.push(nickname);

        console.log(`[即時同步] 學員 ${nickname} 提交了答案 ${upperAnswer}。目前統計:`, global.classState.answers);

        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ status: 'success', classState: global.classState }));
      } catch (e) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: '無效的作答請求' }));
      }
    });
    return;
  }

  // 4. 重置投票數據 (講師點擊重置按鍵)
  if (pathname === '/api/reset-class' && req.method === 'POST') {
    global.classState.answers = { "A": 0, "B": 0, "C": 0, "D": 0 };
    global.classState.voters = [];
    console.log('[即時同步] 講師重置了全班作答數據');
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'success', classState: global.classState }));
    return;
  }

  // ─── 靜態檔案伺服器 ───
  let safePath = pathname === '/' ? '/index.html' : pathname;
  const filePath = path.join(__dirname, safePath);

  fs.exists(filePath, (exists) => {
    if (!exists) {
      res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
      res.end('404 找不到檔案');
      return;
    }

    const ext = path.extname(filePath).toLowerCase();
    const contentType = MIME_TYPES[ext] || 'application/octet-stream';

    fs.readFile(filePath, (err, content) => {
      if (err) {
        res.writeHead(500);
        res.end(`伺服器錯誤: ${err.code}`);
      } else {
        res.writeHead(200, { 'Content-Type': contentType });
        res.end(content, 'utf-8');
      }
    });
  });
});

server.listen(PORT, () => {
  console.log(`\n🚀 本地開發伺服器啟動成功！`);
  console.log(`👉 請在瀏覽器中開啟：http://localhost:${PORT}`);
  console.log(`按 Ctrl+C 可停止伺服器。\n`);
});
