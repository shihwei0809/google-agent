# 程式碼備份與修改紀錄: interactive_template.js

本文件為 `interactive_template.js` 的程式碼備份，便於後續版本比對與修改紀錄追蹤。

## 原始程式碼

```javascript
export const INTERACTIVE_TEMPLATE = `<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>__TRAINING_TITLE__ — 互動式情境模擬闖關</title>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Noto+Sans+TC:wght@300;400;500;700;900&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --bg: #070b13;
      --surface: #0e1626;
      --surface-card: rgba(20, 32, 54, 0.6);
      --border: rgba(255, 255, 255, 0.08);
      --text: #f3f4f6;
      --text-muted: #9ca3af;
      --primary: #6366f1;
      --primary-hover: #4f46e5;
      --success: #10b981;
      --success-bg: rgba(16, 185, 129, 0.1);
      --error: #f43f5e;
      --error-bg: rgba(244, 63, 94, 0.1);
    }
    body {
      background-color: var(--bg);
      background-image: radial-gradient(circle at 50% 30%, rgba(99, 102, 241, 0.15) 0%, transparent 70%);
      color: var(--text);
      font-family: 'Outfit', 'Noto Sans TC', sans-serif;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 20px;
      overflow-x: hidden;
    }
    .game-container {
      width: 100%;
      max-width: 750px;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 16px;
      box-shadow: 0 20px 40px rgba(0,0,0,0.5);
      padding: 30px;
      min-height: 480px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      position: relative;
    }
    .screen {
      display: none;
      animation: fadeIn 0.4s ease forwards;
    }
    .screen.active {
      display: flex;
      flex-direction: column;
      gap: 20px;
    }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }
    h1, h2 {
      font-weight: 700;
      background: linear-gradient(to right, #fff, #c7d2fe);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    .title-large { font-size: 2rem; text-align: center; margin-bottom: 10px; }
    .title-mid { font-size: 1.5rem; display: flex; align-items: center; gap: 10px; }
    .desc { color: var(--text-muted); line-height: 1.6; font-size: 0.95rem; }
    .btn-action {
      background: linear-gradient(135deg, var(--primary), #8b5cf6);
      border: none;
      color: #fff;
      padding: 14px 28px;
      font-size: 1.05rem;
      font-weight: 600;
      border-radius: 10px;
      cursor: pointer;
      transition: all 0.2s;
      box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
      text-align: center;
    }
    .btn-action:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 16px rgba(99, 102, 241, 0.4);
    }
    .input-group {
      display: flex;
      flex-direction: column;
      gap: 8px;
      margin: 20px 0;
    }
    .form-input {
      background: rgba(0,0,0,0.3);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 14px;
      color: #fff;
      font-size: 1.05rem;
      outline: none;
      transition: border-color 0.2s;
    }
    .form-input:focus { border-color: var(--primary); }
    
    .steps-indicator {
      display: flex;
      justify-content: space-between;
      margin-bottom: 24px;
      position: relative;
    }
    .steps-indicator::before {
      content: '';
      position: absolute;
      top: 15px;
      left: 10%;
      right: 10%;
      height: 2px;
      background: var(--border);
      z-index: 1;
    }
    .step-dot {
      width: 32px;
      height: 32px;
      background: #142036;
      border: 2px solid var(--border);
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.85rem;
      font-weight: 700;
      z-index: 2;
      transition: all 0.3s;
    }
    .step-dot.active {
      border-color: var(--primary);
      background: var(--primary);
      box-shadow: 0 0 12px rgba(99, 102, 241, 0.5);
    }
    .step-dot.done {
      border-color: var(--success);
      background: var(--success);
    }

    .scenario-card {
      background: var(--surface-card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 24px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    .option-group {
      display: flex;
      flex-direction: column;
      gap: 12px;
      margin-top: 10px;
    }
    .option-btn {
      background: rgba(255,255,255,0.03);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 16px;
      text-align: left;
      cursor: pointer;
      transition: all 0.2s;
      display: flex;
      align-items: flex-start;
      gap: 12px;
      color: var(--text);
      font-size: 0.95rem;
      line-height: 1.5;
    }
    .option-btn:hover:not(.disabled) {
      background: rgba(255,255,255,0.07);
      border-color: rgba(255,255,255,0.2);
    }
    .option-btn.correct {
      background: var(--success-bg);
      border-color: var(--success);
      color: #a7f3d0;
    }
    .option-btn.incorrect {
      background: var(--error-bg);
      border-color: var(--error);
      color: #fecdd3;
    }
    .option-btn.disabled {
      cursor: not-allowed;
      opacity: 0.6;
    }
    .badge-icon {
      font-size: 1.5rem;
      min-width: 30px;
    }
    .feedback-box {
      margin-top: 14px;
      padding: 14px;
      border-radius: 8px;
      display: none;
      font-size: 0.9rem;
      line-height: 1.6;
      animation: fadeIn 0.3s;
    }
    .feedback-box.correct { background: rgba(16, 185, 129, 0.15); border-left: 4px solid var(--success); color: #a7f3d0; }
    .feedback-box.incorrect { background: rgba(244, 63, 94, 0.15); border-left: 4px solid var(--error); color: #fecdd3; }
    
    .score-badge {
      display: inline-block;
      padding: 4px 10px;
      border-radius: 12px;
      font-size: 0.8rem;
      font-weight: 600;
      align-self: flex-start;
    }
    .score-badge.perfect { background: rgba(16,185,129,0.15); color: var(--success); }
    
    .result-summary {
      text-align: center;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 15px;
    }
    .score-value {
      font-size: 3rem;
      font-weight: 800;
      color: var(--success);
      margin: 10px 0;
    }
    .badge-unlocked {
      font-size: 1.2rem;
      color: #fbbf24;
      background: rgba(251,191,36,0.1);
      border: 1px dashed #fbbf24;
      padding: 8px 16px;
      border-radius: 20px;
      margin-bottom: 10px;
    }
  </style>
</head>
<body>

  <div class="game-container">
    
    <div class="screen active" id="screen-welcome">
      <div style="text-align: center; margin-bottom: 20px;">
        <div style="font-size: 4rem;">🎮</div>
        <h1 class="title-large">一日 SOP 職人挑戰</h1>
        <p class="desc">歡迎來到《__TRAINING_TITLE__》合規情境模擬闖關挑戰！本測驗將以擬真工作情境測試您對標準作業規章的了解程度。</p>
      </div>
      
      <div class="input-group">
        <label style="font-weight: 600; color: var(--text-muted); font-size: 0.9rem;">請輸入您的姓名以開始挑戰：</label>
        <input type="text" class="form-input" id="user-name" placeholder="例如：陳大明" maxlength="15" oninput="toggleStartBtn()">
      </div>
      
      <button class="btn-action" id="btn-start-game" onclick="startGame()" disabled>🎮 開始模擬挑戰</button>
    </div>

    <div class="screen" id="screen-game">
      <div class="steps-indicator" id="game-steps-indicator">
      </div>

      <div class="scenario-card">
        <h2 class="title-mid" id="sc-title">關卡載入中...</h2>
        <p class="desc" id="sc-desc">SOP 規範學習內容...</p>
        
        <div style="border-top: 1px solid var(--border); margin: 10px 0;"></div>
        
        <p style="font-weight: 700; font-size: 0.95rem; color: #fff;" id="sc-challenge">情境挑戰題...</p>
        
        <div class="option-group" id="sc-options">
        </div>
        
        <div class="feedback-box" id="sc-feedback">
        </div>
      </div>

      <button class="btn-action" id="btn-next" onclick="nextLevel()" style="display: none; align-self: flex-end;">進入下一關 ➔</button>
    </div>

    <div class="screen" id="screen-result">
      <div class="result-summary">
        <div style="font-size: 4rem;">🏆</div>
        <h2>一日挑戰完成！</h2>
        <p class="desc" id="res-name-label">恭喜同仁完成闖關</p>
        <div class="score-value" id="res-score">100 分</div>
        <div class="badge-unlocked" id="res-badge">🎖️ SOP守護者</div>
        <p class="desc" id="res-desc">合規挑戰結束，系統正在自動保存並同步您的作答結果...</p>
      </div>

      <div id="submit-status-box" style="text-align: center; margin: 20px 0; padding: 14px; border-radius: 8px; font-weight: 600; color: #fbbf24; background: rgba(251,191,36,0.1); border: 1px solid rgba(251,191,36,0.2); animation: fadeIn 0.4s;">
        📤 正在寫入成績至本機 results.csv，請勿關閉網頁...
      </div>
    </div>

  </div>

  <script>
    let userName = "";
    let curLevel = 0;
    let score = 0;
    let answersRecord = [];
    let speechSynth = window.speechSynthesis;
    let currentUtterance = null;

    const LEVELS = __QUIZ_JSON__;

    function toggleStartBtn() {
      const nameVal = document.getElementById("user-name").value.trim();
      document.getElementById("btn-start-game").disabled = nameVal.length < 1;
    }

    function playSuccessSound() {
      try {
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(523.25, ctx.currentTime);
        osc.frequency.setValueAtTime(659.25, ctx.currentTime + 0.1);
        osc.frequency.setValueAtTime(783.99, ctx.currentTime + 0.2);
        gain.gain.setValueAtTime(0.1, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.4);
        osc.start();
        osc.stop(ctx.currentTime + 0.4);
      } catch (e) {}
    }

    function playFailSound() {
      try {
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(220, ctx.currentTime);
        osc.frequency.linearRampToValueAtTime(110, ctx.currentTime + 0.3);
        gain.gain.setValueAtTime(0.1, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.35);
        osc.start();
        osc.stop(ctx.currentTime + 0.35);
      } catch (e) {}
    }

    function speakText(text) {
      if (speechSynth) {
        speechSynth.cancel();
        currentUtterance = new SpeechSynthesisUtterance(text);
        const voices = speechSynth.getVoices();
        const zhVoice = voices.find(v => v.lang.includes("zh-TW") || v.lang.includes("zh-CN") || v.lang.includes("zh"));
        if (zhVoice) currentUtterance.voice = zhVoice;
        speechSynth.speak(currentUtterance);
      }
    }

    function startGame() {
      userName = document.getElementById("user-name").value.trim();
      document.getElementById("screen-welcome").classList.remove("active");
      document.getElementById("screen-game").classList.add("active");
      
      const stepIndicator = document.getElementById("game-steps-indicator");
      stepIndicator.innerHTML = "";
      for(let i=0; i<LEVELS.length; i++) {
        const dot = document.createElement("div");
        dot.className = i === 0 ? "step-dot active" : "step-dot";
        dot.id = "step-" + i;
        dot.textContent = i + 1;
        stepIndicator.appendChild(dot);
      }
      
      loadLevel();
    }

    function loadLevel() {
      const lv = LEVELS[curLevel];
      
      for(let i=0; i<LEVELS.length; i++) {
        const dot = document.getElementById("step-" + i);
        if (dot) {
          if(i < curLevel) {
            dot.className = "step-dot done";
          } else if (i === curLevel) {
            dot.className = "step-dot active";
          } else {
            dot.className = "step-dot";
          }
        }
      }

      document.getElementById("sc-title").textContent = lv.title;
      document.getElementById("sc-desc").textContent = lv.desc;
      document.getElementById("sc-challenge").textContent = lv.challenge;
      
      const optContainer = document.getElementById("sc-options");
      optContainer.innerHTML = "";
      
      lv.options.forEach((opt, idx) => {
        const btn = document.createElement("button");
        btn.className = "option-btn";
        btn.innerHTML = \`<span class="badge-icon">\${idx === 0 ? 'A' : idx === 1 ? 'B' : idx === 2 ? 'C' : 'D'}</span> <span>\${opt.text}</span>\`;
        btn.onclick = () => selectOption(idx, btn);
        optContainer.appendChild(btn);
      });

      document.getElementById("sc-feedback").style.display = "none";
      document.getElementById("btn-next").style.display = "none";
      
      speakText(lv.title + "。" + lv.desc + lv.challenge);
    }

    function selectOption(idx, btn) {
      const lv = LEVELS[curLevel];
      const opt = lv.options[idx];
      
      const allBtns = document.querySelectorAll(".option-btn");
      allBtns.forEach(b => b.classList.add("disabled"));

      const feedbackBox = document.getElementById("sc-feedback");
      
      const optLabel = idx === 0 ? "A" : idx === 1 ? "B" : idx === 2 ? "C" : "D";
      answersRecord.push({
        num: curLevel + 1,
        question: lv.challenge,
        selected: optLabel,
        isCorrect: opt.correct
      });

      if (opt.correct) {
        btn.classList.add("correct");
        feedbackBox.className = "feedback-box correct";
        feedbackBox.innerHTML = "<strong>🎉 回答正確！</strong> " + opt.feedback;
        score += Math.round(100 / LEVELS.length);
        playSuccessSound();
      } else {
        btn.classList.add("incorrect");
        feedbackBox.className = "feedback-box incorrect";
        feedbackBox.innerHTML = "<strong>❌ 選擇方案不合規！</strong> " + opt.feedback;
        playFailSound();
      }
      
      feedbackBox.style.display = "block";
      document.getElementById("btn-next").style.display = "block";
      
      speakText(opt.feedback);
    }

    function nextLevel() {
      if (speechSynth) speechSynth.cancel();
      curLevel++;
      if (curLevel < LEVELS.length) {
        loadLevel();
      } else {
        if (score > 100 || (score >= 98 && score <= 100)) { score = 100; }
        showResults();
      }
    }

    function showResults() {
      document.getElementById("screen-game").classList.remove("active");
      document.getElementById("screen-result").classList.add("active");
      
      document.getElementById("res-name-label").textContent = "🏆 恭喜同仁 " + userName + " 順利完成闖關！";
      document.getElementById("res-score").textContent = score + " 分";
      
      const badge = document.getElementById("res-badge");
      if (score === 100) {
        badge.textContent = "🎖️ SOP 完美守護專家 (100分)";
        badge.style.borderColor = "#fbbf24";
        badge.style.color = "#fbbf24";
      } else if (score >= 75) {
        badge.textContent = "🏅 優秀學員";
        badge.style.borderColor = "#6366f1";
        badge.style.color = "#818cf8";
      } else {
        badge.textContent = "🥈 繼續加油";
        badge.style.borderColor = "#9ca3af";
        badge.style.color = "#9ca3af";
      }
      
      speakText("恭喜完成挑戰！您的得分是，" + score + "分！");
      
      submitGameScore();
    }

    function submitGameScore() {
      const payload = {
        name: userName,
        timestamp: new Date().toLocaleString("zh-TW", { timeZone: "Asia/Taipei" }),
        score: score,
        correctCount: Math.round((score / 100) * LEVELS.length),
        total: LEVELS.length
      };

      answersRecord.forEach((rec, idx) => {
        payload[\`q\${idx + 1}_question\`] = rec.question;
        payload[\`q\${idx + 1}_answer\`] = \`答: \${rec.selected} (\${rec.isCorrect ? "對" : "錯"})\`;
        payload[\`q\${idx + 1}\`] = \`答: \${rec.selected} (\text{對})\`;
      });

      const statusBox = document.getElementById("submit-status-box");

      fetch("/api/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      })
      .then(res => res.json())
      .then(data => {
        console.log("本機伺服器儲存成功:", data);
        statusBox.innerHTML = "✅ 成績已成功寫入本機 results.csv！您可以關閉此網頁。";
        statusBox.style.color = "var(--success)";
        statusBox.style.background = "rgba(16, 185, 129, 0.1)";
        statusBox.style.borderColor = "rgba(16, 185, 129, 0.2)";
      })
      .catch(err => {
        console.warn("未連接本機伺服器或傳送失敗 (單機版模式):", err);
        const cloudUrl = localStorage.getItem("training_cloud_url") || "";
        if (cloudUrl) {
          fetch(cloudUrl, {
            method: "POST",
            mode: "no-cors",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
          })
          .then(() => {
            statusBox.innerHTML = "✅ 成績已送出備份至雲端試算表！您可以關閉此網頁。";
            statusBox.style.color = "var(--success)";
            statusBox.style.background = "rgba(16, 185, 129, 0.1)";
            statusBox.style.borderColor = "rgba(16, 185, 129, 0.2)";
          })
          .catch(e => {
            statusBox.innerHTML = "❌ 提交失敗，請通知管理員確認伺服器或網路狀態。";
            statusBox.style.color = "var(--error)";
            statusBox.style.background = "rgba(244, 63, 94, 0.1)";
            statusBox.style.borderColor = "rgba(244, 63, 94, 0.2)";
          });
        } else {
          statusBox.innerHTML = "⚠️ 本機伺服器未開啟，且未設定雲端同步，成績已保存在本機快取中。";
          statusBox.style.color = "#fbbf24";
          statusBox.style.background = "rgba(251, 191, 129, 0.1)";
          statusBox.style.borderColor = "rgba(251, 191, 129, 0.2)";
        }
      });
    }
  </script>
</body>
</html>\`;
`;

```
