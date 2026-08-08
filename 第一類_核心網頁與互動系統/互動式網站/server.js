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

// Gemini API 模組備援與自動嘗試最新版本機制 (由最新 3.6 往前回退)
function callGeminiWithFallback(geminiKey, requestBody, modelIndex = 0, callback) {
  const models = ['gemini-3.6-flash', 'gemini-3.5-flash', 'gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-flash-latest'];
  if (modelIndex >= models.length) {
    return callback(new Error('所有可用的 Gemini 模組皆呼叫失敗'));
  }
  const modelName = models[modelIndex];
  console.log(`[Gemini] 嘗試呼叫模組: ${modelName}`);
  
  const req = https.request({
    hostname: 'generativelanguage.googleapis.com',
    path: `/v1beta/models/${modelName}:generateContent?key=${geminiKey}`,
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Content-Length': Buffer.byteLength(requestBody)
    }
  }, (res) => {
    let data = '';
    res.on('data', chunk => data += chunk);
    res.on('end', () => {
      if (res.statusCode === 200) {
        callback(null, data);
      } else {
        console.warn(`[Gemini] 模組 ${modelName} 返回錯誤碼: ${res.statusCode}，嘗試下一個模組。`);
        callGeminiWithFallback(geminiKey, requestBody, modelIndex + 1, callback);
      }
    });
  });
  
  req.on('error', (err) => {
    console.warn(`[Gemini] 模組 ${modelName} 連線異常: ${err.message}，嘗試下一個模組。`);
    callGeminiWithFallback(geminiKey, requestBody, modelIndex + 1, callback);
  });
  
  req.write(requestBody);
  req.end();
}

// 存檔機制：將全域課堂狀態寫入本機 JSON 檔案中，確保伺服器重啟或斷線資料不遺失
function saveStateToDisk() {
  try {
    const dataDir = path.join(__dirname, 'data');
    if (!fs.existsSync(dataDir)) {
      fs.mkdirSync(dataDir, { recursive: true });
    }
    fs.writeFileSync(path.join(dataDir, 'classroom_save.json'), JSON.stringify(global.classState, null, 2), 'utf8');
  } catch (e) {
    console.error('寫入課堂存檔失敗:', e.message);
  }
}

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
        const { essayAnswer, clientApiKey } = JSON.parse(body);
        const geminiKey = clientApiKey || env.GEMINI_API_KEY || process.env.GEMINI_API_KEY;

        if (!geminiKey) {
          res.writeHead(401, { 'Content-Type': 'application/json' });
          return res.end(JSON.stringify({ error: '未配置 GEMINI_API_KEY，請在網頁輸入或配置 .env 檔案。' }));
        }

        // 呼叫 Gemini 進行批改
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

        callGeminiWithFallback(geminiKey, geminiReqBody, 0, (err, resData) => {
          if (err) {
            res.writeHead(500, { 'Content-Type': 'application/json' });
            return res.end(JSON.stringify({ error: err.message }));
          }
          try {
            const parsed = JSON.parse(resData);
            const textResult = parsed.candidates[0].content.parts[0].text;
            const grading = JSON.parse(textResult.trim());
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({
              score: grading.score,
              feedback: grading.feedback,
              simulated: false
            }));
          } catch (e) {
            res.writeHead(500, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ error: '解析 Gemini 回傳資料失敗: ' + e.message }));
          }
        });

      } catch (err) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: '無效的 JSON 請求' }));
      }
    });
    return;
  }

  if (!global.classState) {
    const saveFilePath = path.join(__dirname, 'data', 'classroom_save.json');
    if (fs.existsSync(saveFilePath)) {
      try {
        global.classState = JSON.parse(fs.readFileSync(saveFilePath, 'utf8'));
        console.log('💾 已成功載入之前的課堂存檔紀錄');
      } catch (e) {
        console.error('讀取課堂存檔失敗:', e.message);
      }
    }

    if (!global.classState) {
      global.classState = {
        currentSlide: 1,
        answers: { "A": 0, "B": 0, "C": 0, "D": 0 },
        voters: [], // 記錄已投票暱稱，防止重複投票
        voteRecords: [], // 學員答題歷史明細
        slidesData: [
          {
            index: 1,
            title: "1. 英國文化介紹 (Presentation)",
            type: "slide",
            headline: "Introduction to British Culture (英國文化介紹)",
            desc: "英國是位於西歐的島國，首都為倫敦。英國有著豐富的歷史和文化，包括著名的石亨奇（巨石陣）、巴斯古城等。英國人喜愛足球、板球等運動，同時也擁有許多著名的大學，如牛津、劍橋等。"
          },
          {
            index: 2,
            title: "2. 測驗 Q1: 英國的首都",
            type: "interactive",
            headline: "Q1: 英國的首都是什麼？ (What is the capital of the UK?)",
            options: { "A": "倫敦 (London)", "B": "巴黎 (Paris)", "C": "柏林 (Berlin)", "D": "羅馬 (Rome)" },
            correctAnswer: "A"
          },
          {
            index: 3,
            title: "3. 測驗 Q2: 喜愛的運動",
            type: "interactive",
            headline: "Q2: 英國人最喜愛的運動是什麼？ (What is the favorite sport?)",
            options: { "A": "籃球 (Basketball)", "B": "足球 (Football)", "C": "網球 (Tennis)", "D": "棒球 (Baseball)" },
            correctAnswer: "B"
          },
          {
            index: 4,
            title: "4. 測驗 Q3: 著名大學",
            type: "interactive",
            headline: "Q3: 英國有哪些著名的大學？ (Which are famous UK universities?)",
            options: { "A": "牛津、劍橋 (Oxford, Cambridge)", "B": "哈佛、斯坦福 (Harvard, Stanford)", "C": "劍橋、牛津、哈佛", "D": "東京大學、京都大學" },
            correctAnswer: "A"
          },
          {
            index: 5,
            title: "5. 測驗 Q4: 著名歷史文化古蹟",
            type: "interactive",
            headline: "Q4: 下列何者是簡報中提到英國著名的歷史古蹟？",
            options: { "A": "石亨奇與巴斯古城", "B": "羅馬競技場與萬神殿", "C": "埃及金字塔與獅身像", "D": "萬里長城與故宮" },
            correctAnswer: "A"
          },
          {
            index: 6,
            title: "6. 測驗 Q5: 英國的地理位置",
            type: "interactive",
            headline: "Q5: 根據簡報，英國是位於哪裡的島國？",
            options: { "A": "東歐 (Eastern Europe)", "B": "西歐 (Western Europe)", "C": "北美洲 (North America)", "D": "東南亞 (Southeast Asia)" },
            correctAnswer: "B"
          }
        ]
      };
    }
  }

  // ─── 代理中轉 3：上傳教材並透過 Gemini AI 生成課程簡報與測驗 ───
  if (pathname === '/api/generate-lesson' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      try {
        const { base64Data, mimeType, fileName, clientApiKey, pagesCount } = JSON.parse(body);
        const geminiKey = clientApiKey || env.GEMINI_API_KEY || process.env.GEMINI_API_KEY;

        const targetPages = parseInt(pagesCount) || 8;

        if (!geminiKey) {
          res.writeHead(401, { 'Content-Type': 'application/json' });
          return res.end(JSON.stringify({ error: '未配置 GEMINI_API_KEY，請在網頁輸入或配置 .env 檔案。' }));
        }

        if (!base64Data) {
          res.writeHead(400, { 'Content-Type': 'application/json' });
          return res.end(JSON.stringify({ error: '未接收到檔案數據' }));
        }

        // 移除 Base64 的 header 前綴 (例如 data:application/pdf;base64,)
        let cleanBase64 = base64Data;
        if (cleanBase64.indexOf(';base64,') !== -1) {
          cleanBase64 = cleanBase64.split(';base64,')[1];
        }

        const promptText = `你是一位專業的學科教育專家。請詳細閱讀上傳的教學材料（檔名為: ${fileName || '未命名'}），並將其製作成一套適合課堂互動的簡報與互動測驗（含有正確答案與解析）。

你的輸出必須是一個 JSON Array，格式必須完全符合以下 JSON 陣列規範，不包含任何 markdown 的 \`\`\` 標記，純粹輸出合法的 JSON，以符合 JSON.parse 解析要求：

每個項目代表一頁投影片或一個互動測驗，必須符合以下規格：
1. 投影片（type 為 'slide'）：
   {"index": 頁碼, "title": "短標題", "type": "slide", "headline": "精簡的簡報標題", "desc": "詳細的簡報介紹文字（約 100~200 字），供投影顯示或講師口述"}
2. 互動測驗（type 為 'interactive'）：
   {"index": 頁碼, "title": "測驗題目短標題", "type": "interactive", "headline": "互動測驗的完整單選題目內容？", "options": {"A": "選項 A 描述", "B": "選項 B 描述", "C": "選項 C 描述", "D": "選項 D 描述"}, "correctAnswer": "A" (必須是 A, B, C 或 D 之一), "explanation": "答案解析說明"}

注意：
1. 簡報教學頁（slide）與互動測驗頁（interactive）交錯穿插，講授完 1-2 頁簡報後，緊接著進行相關的 1-2 題測驗，以達到即時互動反饋的效果。
2. 課程的總頁數（即最大 index 值）必須精確地為 ${targetPages} 頁！
3. 選項（options）必須有 A, B, C, D 四個，不可少於或多於此數量。
4. 輸出必須是一個合法的 JSON 陣列，直接回傳 JSON。`;

        // 呼叫 Gemini 進行教材解析與生成
        const geminiReqBody = JSON.stringify({
          contents: [{
            parts: [
              {
                inlineData: {
                  mimeType: mimeType || 'application/pdf',
                  data: cleanBase64
                }
              },
              {
                text: promptText
              }
            ]
          }],
          generationConfig: {
            responseMimeType: "application/json"
          }
        });

        callGeminiWithFallback(geminiKey, geminiReqBody, 0, (err, resData) => {
          if (err) {
            res.writeHead(500, { 'Content-Type': 'application/json' });
            return res.end(JSON.stringify({ error: err.message }));
          }
          try {
            const parsed = JSON.parse(resData);
            let textResult = parsed.candidates[0].content.parts[0].text;
            // 去除可能存在的 markdown wrap
            textResult = textResult.replace(/^```json\s*/, '').replace(/```\s*$/, '').trim();
            
            const newSlidesData = JSON.parse(textResult);
            
            if (Array.isArray(newSlidesData) && newSlidesData.length > 0) {
              // 更新全域狀態
              global.classState.slidesData = newSlidesData;
              global.classState.currentSlide = 1;
              global.classState.answers = { "A": 0, "B": 0, "C": 0, "D": 0 };
              global.classState.voters = [];
              global.classState.voteRecords = []; // 重置歷史答題明細
              
              console.log(`[Level 5] 成功解析上傳教材 ${fileName} 並生成 ${newSlidesData.length} 頁簡報測驗！`);
              saveStateToDisk();
              
              res.writeHead(200, { 'Content-Type': 'application/json' });
              res.end(JSON.stringify({ status: 'success', slidesCount: newSlidesData.length }));
            } else {
              throw new Error('AI 回傳的資料結構不是有效的陣列');
            }
          } catch (e) {
            console.error('Gemini 解析教材錯誤:', e, resData);
            res.writeHead(500, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ error: '教材解析失敗，可能格式不支援或 AI 回傳格式有誤：' + e.message }));
          }
        });

      } catch (err) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: '無效的 JSON 請求: ' + err.message }));
      }
    });
    return;
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
        saveStateToDisk();
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ status: 'success', classState: global.classState }));
      } catch (e) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: '無效的狀態請求' }));
      }
    });
    return;
  }

  // ─── 講師線上更新投影片資料 (修正 typos 或錯誤) ───
  if (pathname === '/api/update-slides' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      try {
        const { slidesData } = JSON.parse(body);
        if (Array.isArray(slidesData)) {
           global.classState.slidesData = slidesData;
           console.log('[Level 5] 講師更新了簡報測驗內容');
           saveStateToDisk();
           res.writeHead(200, { 'Content-Type': 'application/json' });
           res.end(JSON.stringify({ status: 'success', classState: global.classState }));
        } else {
          res.writeHead(400, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: '無效的投影片資料格式' }));
        }
      } catch (e) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: '無效的 JSON 請求' }));
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

        // 紀錄明細
        const currentSlide = global.classState.slidesData[global.classState.currentSlide - 1];
        const isCorrect = currentSlide ? (upperAnswer === currentSlide.correctAnswer) : false;
        const questionText = currentSlide ? currentSlide.headline : '未知題目';
        const correctAnswer = currentSlide ? currentSlide.correctAnswer : '';
        
        if (!global.classState.voteRecords) {
          global.classState.voteRecords = [];
        }
        
        global.classState.voteRecords.push({
          nickname: nickname,
          slideIndex: global.classState.currentSlide,
          question: questionText,
          selectedAnswer: upperAnswer,
          correctAnswer: correctAnswer,
          isCorrect: isCorrect,
          timestamp: new Date().toLocaleString('zh-TW', { timeZone: 'Asia/Taipei' })
        });

        global.classState.answers[upperAnswer]++;
        global.classState.voters.push(nickname);

        console.log(`[即時同步] 學員 ${nickname} 提交了答案 ${upperAnswer}。目前統計:`, global.classState.answers);
        saveStateToDisk();

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
    saveStateToDisk();
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'success', classState: global.classState }));
    return;
  }

  // 5. 匯出歷史答題紀錄為 Excel CSV 格式
  if (pathname === '/api/export-csv' && req.method === 'GET') {
    res.writeHead(200, {
      'Content-Type': 'text/csv; charset=utf-8',
      'Content-Disposition': 'attachment; filename=classroom_grades.csv'
    });
    // 輸出 UTF-8 BOM，防 Excel 開啟亂碼
    res.write('\uFEFF');
    res.write('學生暱稱,簡報頁數,測驗題目,學生選答,正確答案,是否答對,提交時間\n');
    
    const records = global.classState.voteRecords || [];
    records.forEach(r => {
      res.write(`"${r.nickname.replace(/"/g, '""')}",${r.slideIndex},"${r.question.replace(/"/g, '""')}","${r.selectedAnswer}","${r.correctAnswer}","${r.isCorrect ? '對' : '錯'}","${r.timestamp}"\n`);
    });
    res.end();
    return;
  }

  // 6. 清除歷史累計答題明細
  if (pathname === '/api/clear-history' && req.method === 'POST') {
    global.classState.voteRecords = [];
    saveStateToDisk();
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
