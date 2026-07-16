const http = require('http');
const fs = require('fs');
const path = require('path');
const https = require('https');

const PORT = 3000;

// 1. Load env variables
const env = {};
try {
  const envPath = path.join(__dirname, '.env');
  if (fs.existsSync(envPath)) {
    const content = fs.readFileSync(envPath, 'utf8');
    content.split(/\r?\n/).forEach(line => {
      const match = line.match(/^\s*([\w.-]+)\s*=\s*(.*)?\s*$/);
      if (match) {
        let val = match[2] || '';
        if (val.startsWith('"') && val.endsWith('"')) val = val.slice(1, -1);
        if (val.startsWith("'") && val.endsWith("'")) val = val.slice(1, -1);
        env[match[1]] = val.trim();
      }
    });
    console.log('✅ Loaded .env environment variables successfully.');
  }
} catch (e) {
  console.error('Error loading .env:', e.message);
}

// 2. Class State store for live sync
if (!global.classState) {
  global.classState = {
    currentSlide: 1,
    answers: { "A": 0, "B": 0, "C": 0, "D": 0 },
    voters: [],
    activeDeckId: 'hongsheng_sop_safety',
    slides: [],
    onlineStudents: {} // mapping of nickname -> lastSeen timestamp
  };
}

if (!global.webrtcState) {
  global.webrtcState = {
    offers: {},
    answers: {}
  };
}

const DECKS_DIR = path.join(__dirname, 'decks');
if (!fs.existsSync(DECKS_DIR)) {
  fs.mkdirSync(DECKS_DIR);
}

// Load decks from disk
let decksCache = {};
function loadDecksFromDisk() {
  try {
    const files = fs.readdirSync(DECKS_DIR);
    files.forEach(file => {
      if (file.endsWith('.json')) {
        const filePath = path.join(DECKS_DIR, file);
        const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
        if (data.id && data.slides) {
          decksCache[data.id] = data;
        }
      }
    });
    console.log(`✅ Loaded ${Object.keys(decksCache).length} slide decks from disk.`);
  } catch (err) {
    console.error('Error loading slide decks:', err.message);
  }
}
loadDecksFromDisk();

// Populate initial slides if empty
if (!global.classState.slides || global.classState.slides.length === 0) {
  const defaultDeck = decksCache[global.classState.activeDeckId];
  if (defaultDeck) {
    global.classState.slides = defaultDeck.slides;
  }
}

// Mime types
const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.gif': 'image/gif',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
};

http.createServer((req, res) => {
  const parsedUrl = new URL(req.url, `http://${req.headers.host}`);
  const pathname = parsedUrl.pathname;

  // Decoded URL-encoded paths
  let safeUrl = decodeURIComponent(pathname);

  // ─── API 1: Groq Chat ───
  if (safeUrl === '/.netlify/functions/groq-chat' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      try {
        const { messages, model } = JSON.parse(body);
        const groqKey = env.GROQ_API_KEY || process.env.GROQ_API_KEY;

        if (!groqKey) {
          res.writeHead(401, { 'Content-Type': 'application/json' });
          return res.end(JSON.stringify({ error: 'Missing GROQ_API_KEY' }));
        }

        const groqReqBody = JSON.stringify({
          model: model || 'llama-3.3-70b-versatile',
          messages: messages,
          temperature: 0.7
        });

        const groqReq = https.request({
          hostname: 'api.groq.com',
          path: '/openai/v1/chat/completions',
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
                res.end(JSON.stringify({ error: parsed.error?.message || 'Groq API error' }));
              }
            } catch (err) {
              res.writeHead(500, { 'Content-Type': 'application/json' });
              res.end(JSON.stringify({ error: 'Failed to parse Groq response' }));
            }
          });
        });

        groqReq.on('error', (err) => {
          res.writeHead(500, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: 'Connection to Groq failed: ' + err.message }));
        });

        groqReq.write(groqReqBody);
        groqReq.end();
      } catch (err) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Invalid JSON request' }));
      }
    });
    return;
  }

  // ─── API 2: Gemini AI Grading ───
  if (safeUrl === '/.netlify/functions/ask-ai' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      try {
        const { essayAnswer } = JSON.parse(body);
        const geminiKey = env.GEMINI_API_KEY || process.env.GEMINI_API_KEY;

        if (!geminiKey) {
          res.writeHead(401, { 'Content-Type': 'application/json' });
          return res.end(JSON.stringify({ error: 'Missing GEMINI_API_KEY' }));
        }

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
                res.end(JSON.stringify({ error: parsed.error?.message || 'Gemini API Error' }));
              }
            } catch (err) {
              res.writeHead(500, { 'Content-Type': 'application/json' });
              res.end(JSON.stringify({ error: 'Failed to parse Gemini response' }));
            }
          });
        });

        geminiReq.on('error', (err) => {
          res.writeHead(500, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: 'Connection to Gemini failed: ' + err.message }));
        });

        geminiReq.write(geminiReqBody);
        geminiReq.end();
      } catch (err) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Invalid JSON request' }));
      }
    });
    return;
  }

  // ─── API 3: Class state ───
  if (safeUrl === '/api/class-state') {
    if (req.method === 'GET') {
      // Handle student heartbeat
      const nickname = parsedUrl.searchParams.get('nickname');
      if (nickname) {
        global.classState.onlineStudents[nickname] = Date.now();
      }

      // Cleanup offline students (active in last 8 seconds)
      const now = Date.now();
      const onlineList = [];
      Object.entries(global.classState.onlineStudents).forEach(([name, lastSeen]) => {
        if (now - lastSeen < 8000) {
          onlineList.push(name);
        } else {
          delete global.classState.onlineStudents[name];
        }
      });
      // Sort online list alphabetically
      onlineList.sort();

      // Return state including slides & online list
      const responseState = {
        currentSlide: global.classState.currentSlide,
        answers: global.classState.answers,
        voters: global.classState.voters,
        activeDeckId: global.classState.activeDeckId,
        slides: global.classState.slides,
        onlineStudents: onlineList
      };

      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(responseState));
    } else if (req.method === 'POST') {
      let body = '';
      req.on('data', chunk => { body += chunk; });
      req.on('end', () => {
        try {
          const { currentSlide } = JSON.parse(body);
          if (global.classState.currentSlide !== currentSlide) {
            global.classState.answers = { "A": 0, "B": 0, "C": 0, "D": 0 };
            global.classState.voters = [];
          }
          global.classState.currentSlide = currentSlide;
          res.writeHead(200, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ status: 'success', classState: global.classState }));
        } catch (e) {
          res.writeHead(400, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: 'Invalid state request' }));
        }
      });
    }
    return;
  }

  // ─── API: Get All Decks ───
  if (safeUrl === '/api/decks' && req.method === 'GET') {
    loadDecksFromDisk();
    const list = Object.values(decksCache).map(deck => ({
      id: deck.id,
      title: deck.title,
      slideCount: deck.slides.length
    }));
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(list));
    return;
  }

  // ─── API: Select Active Deck ───
  if (safeUrl === '/api/select-deck' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      try {
        const { deckId } = JSON.parse(body);
        if (!decksCache[deckId]) {
          res.writeHead(404, { 'Content-Type': 'application/json' });
          return res.end(JSON.stringify({ error: 'Deck not found' }));
        }
        global.classState.activeDeckId = deckId;
        global.classState.slides = decksCache[deckId].slides;
        global.classState.currentSlide = 1;
        global.classState.answers = { "A": 0, "B": 0, "C": 0, "D": 0 };
        global.classState.voters = [];
        
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ status: 'success', activeDeckId: deckId }));
      } catch (e) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Invalid request' }));
      }
    });
    return;
  }

  // ─── API: Upload New Deck ───
  if (safeUrl === '/api/upload-deck' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      try {
        const deckData = JSON.parse(body);
        
        // Validation
        if (!deckData.title || !deckData.slides || !Array.isArray(deckData.slides)) {
          res.writeHead(400, { 'Content-Type': 'application/json' });
          return res.end(JSON.stringify({ error: 'Invalid deck format: title and slides array are required' }));
        }
        
        // Generate a clean slug for id
        const cleanId = (deckData.id || deckData.title.toLowerCase()
          .replace(/[^\w\s-]/g, '')
          .replace(/[\s_]+/g, '_'))
          .trim();
        
        if (!cleanId) {
          res.writeHead(400, { 'Content-Type': 'application/json' });
          return res.end(JSON.stringify({ error: 'Invalid deck title/id' }));
        }
        
        deckData.id = cleanId;
        
        // Standardize slide indexes
        deckData.slides.forEach((slide, idx) => {
          slide.index = idx + 1;
        });
        
        // Write to file
        const filePath = path.join(DECKS_DIR, `${cleanId}.json`);
        fs.writeFileSync(filePath, JSON.stringify(deckData, null, 2), 'utf8');
        
        // Reload cache
        decksCache[cleanId] = deckData;
        
        // Set as active
        global.classState.activeDeckId = cleanId;
        global.classState.slides = deckData.slides;
        global.classState.currentSlide = 1;
        global.classState.answers = { "A": 0, "B": 0, "C": 0, "D": 0 };
        global.classState.voters = [];
        
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ status: 'success', deckId: cleanId }));
      } catch (e) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Failed to parse JSON or save file: ' + e.message }));
      }
    });
    return;
  }

  // ─── API: WebRTC Signaling ───
  if (safeUrl === '/api/webrtc/offer' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      try {
        const { nickname, offer } = JSON.parse(body);
        global.webrtcState.offers[nickname] = offer;
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ status: 'success' }));
      } catch (e) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: e.message }));
      }
    });
    return;
  }

  if (safeUrl === '/api/webrtc/offers' && req.method === 'GET') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(global.webrtcState.offers));
    return;
  }

  if (safeUrl === '/api/webrtc/answer' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      try {
        const { nickname, answer } = JSON.parse(body);
        global.webrtcState.answers[nickname] = answer;
        delete global.webrtcState.offers[nickname];
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ status: 'success' }));
      } catch (e) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: e.message }));
      }
    });
    return;
  }

  if (safeUrl === '/api/webrtc/answer' && req.method === 'GET') {
    const nickname = parsedUrl.searchParams.get('nickname');
    const answer = global.webrtcState.answers[nickname] || null;
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ answer }));
    return;
  }

  if (safeUrl === '/api/webrtc/reset' && req.method === 'POST') {
    global.webrtcState.offers = {};
    global.webrtcState.answers = {};
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'success' }));
    return;
  }

  // ─── API 4: Submit Answer ───
  if (safeUrl === '/api/submit-answer' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      try {
        const { nickname, answer } = JSON.parse(body);
        const upperAnswer = (answer || '').toUpperCase();

        if (!nickname) {
          res.writeHead(400, { 'Content-Type': 'application/json' });
          return res.end(JSON.stringify({ error: 'Nickname is required' }));
        }

        if (!['A', 'B', 'C', 'D'].includes(upperAnswer)) {
          res.writeHead(400, { 'Content-Type': 'application/json' });
          return res.end(JSON.stringify({ error: 'Invalid option' }));
        }

        if (global.classState.voters.includes(nickname)) {
          res.writeHead(400, { 'Content-Type': 'application/json' });
          return res.end(JSON.stringify({ error: 'Already submitted' }));
        }

        global.classState.answers[upperAnswer]++;
        global.classState.voters.push(nickname);

        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ status: 'success', classState: global.classState }));
      } catch (e) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Invalid submit request' }));
      }
    });
    return;
  }

  // ─── API 5: Reset Class ───
  if (safeUrl === '/api/reset-class' && req.method === 'POST') {
    global.classState.answers = { "A": 0, "B": 0, "C": 0, "D": 0 };
    global.classState.voters = [];
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'success', classState: global.classState }));
    return;
  }

  // Default to index.html if pointing to directory root
  let filePath = path.join(__dirname, safeUrl);
  if (safeUrl === '/' || safeUrl.endsWith('/')) {
    filePath = path.join(filePath, 'index.html');
  }

  const extname = String(path.extname(filePath)).toLowerCase();
  const contentType = MIME_TYPES[extname] || 'application/octet-stream';

  fs.readFile(filePath, (error, content) => {
    if (error) {
      if (error.code === 'ENOENT') {
        res.writeHead(404, { 'Content-Type': 'text/html' });
        res.end('404 Not Found', 'utf-8');
      } else {
        res.writeHead(500);
        res.end('Error: ' + error.code);
      }
    } else {
      res.writeHead(200, {
        'Content-Type': contentType,
        'Cache-Control': 'no-store, no-cache, must-revalidate, proxy-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
      });
      res.end(content, 'utf-8');
    }
  });
}).listen(PORT, () => {
  console.log(`TrainBuddy local server running at http://localhost:${PORT}/`);
});
