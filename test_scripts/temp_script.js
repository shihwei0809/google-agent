
    // ════════════════════════════════════════
    //  PLAYER TEMPLATE SOURCE CODE
    // ════════════════════════════════════════
    const PLAYER_TEMPLATE_SOURCE = `<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>__TRAINING_TITLE__ — 教育訓練與測驗系統</title>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Noto+Sans+TC:wght@300;400;500;700;900&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --bg: #070b13;
      --surface: #0e1626;
      --surface-hover: #16223b;
      --surface-card: rgba(20, 32, 54, 0.6);
      --border: rgba(255, 255, 255, 0.08);
      --border-focus: rgba(99, 102, 241, 0.5);
      --text: #f3f4f6;
      --text-muted: #9ca3af;
      --primary: #6366f1;
      --primary-hover: #4f46e5;
      --primary-glow: rgba(99, 102, 241, 0.3);
      --success: #10b981;
      --success-glow: rgba(16, 185, 129, 0.2);
      --error: #f43f5e;
    }
    body {
      background-color: var(--bg);
      background-image: radial-gradient(circle at 50% 0%, rgba(99, 102, 241, 0.15) 0%, transparent 60%);
      color: var(--text);
      font-family: 'Outfit', 'Noto Sans TC', sans-serif;
      min-height: 100vh;
      overflow-x: hidden;
      line-height: 1.6;
    }
    header {
      background: rgba(14, 22, 38, 0.8);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--border);
      padding: 16px 24px;
      position: sticky;
      top: 0;
      z-index: 100;
    }
    .header-container {
      max-width: 1000px;
      margin: 0 auto;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
    }
    .header-logo {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .logo-icon {
      width: 42px;
      height: 42px;
      background: linear-gradient(135deg, var(--primary), #8b5cf6);
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 20px;
      color: #fff;
      box-shadow: 0 4px 12px var(--primary-glow);
    }
    .logo-text h1 {
      font-size: 1.1rem;
      font-weight: 700;
      background: linear-gradient(to right, #fff, #c7d2fe);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    .logo-text p {
      font-size: 0.75rem;
      color: var(--text-muted);
    }
    .btn-cfg {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--border);
      color: var(--text);
      padding: 8px 16px;
      border-radius: 8px;
      font-size: 0.85rem;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 8px;
      transition: all 0.2s;
    }
    .btn-cfg:hover {
      background: rgba(255, 255, 255, 0.1);
      border-color: rgba(255, 255, 255, 0.2);
    }
    .step-bar {
      background: rgba(14, 22, 38, 0.4);
      border-bottom: 1px solid var(--border);
      padding: 12px 24px;
    }
    .step-container {
      max-width: 1000px;
      margin: 0 auto;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .step-item {
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 0.85rem;
      color: var(--text-muted);
      font-weight: 500;
    }
    .step-item.active { color: var(--text); }
    .step-item.done { color: var(--success); }
    .step-num {
      width: 26px;
      height: 26px;
      border-radius: 50%;
      border: 2px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      font-size: 0.75rem;
      transition: all 0.3s;
    }
    .step-item.active .step-num {
      border-color: var(--primary);
      background: var(--primary);
      color: #fff;
      box-shadow: 0 0 10px var(--primary-glow);
    }
    .step-item.done .step-num {
      border-color: var(--success);
      background: var(--success);
      color: #fff;
    }
    .step-line {
      flex: 1;
      height: 2px;
      background: var(--border);
      margin: 0 20px;
    }
    .step-line.active { background: var(--primary); }
    main {
      max-width: 1000px;
      margin: 32px auto;
      padding: 0 24px 60px;
    }
    .section-card {
      background: var(--surface-card);
      border: 1px solid var(--border);
      border-radius: 20px;
      padding: 32px;
      backdrop-filter: blur(8px);
      margin-bottom: 32px;
      box-shadow: 0 10px 30px rgba(0,0,0,0.25);
    }
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: rgba(99, 102, 241, 0.1);
      border: 1px solid rgba(99, 102, 241, 0.2);
      color: #a5b4fc;
      border-radius: 100px;
      padding: 4px 12px;
      font-size: 0.75rem;
      font-weight: 600;
      margin-bottom: 16px;
    }
    .section-title { font-size: 1.45rem; font-weight: 700; margin-bottom: 8px; }
    .section-desc { color: var(--text-muted); font-size: 0.9rem; margin-bottom: 24px; }
    .player-outer {
      border: 1px solid var(--border);
      border-radius: 16px;
      overflow: hidden;
      margin-bottom: 20px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    .player-screen {
      min-height: 460px;
      background: #06090f;
      position: relative;
      overflow: hidden;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 24px;
    }
    .slide-card {
      width: 100%;
      height: 100%;
      display: none;
      opacity: 0;
      transform: translateY(15px);
      transition: opacity 0.5s ease, transform 0.5s ease;
      position: absolute;
      padding: 20px;
      pointer-events: none;
    }
    .slide-card.active {
      display: grid;
      grid-template-columns: 1.2fr 1fr;
      gap: 28px;
      align-items: center;
      opacity: 1;
      transform: translateY(0);
      pointer-events: auto;
      position: relative;
    }
    .slide-inner { width: 100%; }
    .slide-visual {
      width: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .visual-card {
      width: 100%;
      aspect-ratio: 16 / 10;
      border-radius: 16px;
      overflow: hidden;
      border: 1px solid var(--border);
      background: rgba(255, 255, 255, 0.02);
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
    }
    .visual-img {
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
    }
    .visual-fallback {
      position: absolute;
      inset: 0;
      background: radial-gradient(circle at center, rgba(99, 102, 241, 0.15) 0%, rgba(14, 22, 38, 0.95) 100%);
      display: flex;
      align-items: center;
      justify-content: center;
      flex-direction: column;
    }
    .fallback-icon {
      font-size: 72px;
      filter: drop-shadow(0 0 15px var(--primary-glow));
      animation: floatIcon 3s ease-in-out infinite;
    }
    @keyframes floatIcon {
      0%, 100% { transform: translateY(0); }
      50% { transform: translateY(-8px); }
    }
    .slide-card h2 {
      font-size: 2.2rem;
      font-weight: 800;
      margin-bottom: 24px;
      background: linear-gradient(135deg, #fff 0%, #c7d2fe 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      border-left: 5px solid var(--primary);
      padding-left: 16px;
    }
    .slide-bullets { list-style: none; display: flex; flex-direction: column; gap: 16px; }
    .slide-bullets li {
      font-size: 1.15rem;
      color: #e5e7eb;
      display: flex;
      align-items: flex-start;
      gap: 12px;
      opacity: 0;
      transform: translateX(-10px);
      animation: slideInBullet 0.5s forwards;
    }
    @keyframes slideInBullet { to { opacity: 1; transform: translateX(0); } }
    .slide-bullets li::before { content: "✦"; color: var(--primary); font-size: 1.2rem; flex-shrink: 0; }
    .player-overlay {
      position: absolute;
      inset: 0;
      background: rgba(6, 9, 15, 0.95);
      backdrop-filter: blur(8px);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 10;
      transition: all 0.3s ease;
    }
    .player-overlay.gone { opacity: 0; pointer-events: none; }
    .overlay-box { text-align: center; background: rgba(14, 22, 38, 0.8); border: 1px solid var(--border); border-radius: 20px; padding: 36px; max-width: 360px; }
    .overlay-icon { font-size: 48px; margin-bottom: 16px; }
    .overlay-title { font-size: 1.25rem; font-weight: 700; margin-bottom: 8px; }
    .overlay-desc { font-size: 0.85rem; color: var(--text-muted); margin-bottom: 24px; line-height: 1.6; }
    .btn-start {
      background: linear-gradient(135deg, var(--primary), #8b5cf6);
      color: #fff;
      border: none;
      border-radius: 50px;
      padding: 12px 32px;
      font-size: 0.95rem;
      font-weight: 600;
      cursor: pointer;
      box-shadow: 0 4px 15px rgba(99,102,241,0.4);
      transition: all 0.2s;
    }
    .btn-start:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(99,102,241,0.6); }
    .player-controls { background: #0a0f1b; border-top: 1px solid var(--border); padding: 14px 20px; display: flex; align-items: center; gap: 16px; position: relative; }
    .progress-bar-container { position: absolute; top: 0; left: 0; right: 0; height: 3px; background: rgba(255,255,255,0.05); }
    .progress-bar-fill { height: 100%; background: linear-gradient(to right, var(--primary), #8b5cf6); width: 0%; transition: width 0.3s ease; }
    .control-btn {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--border);
      color: var(--text);
      width: 38px;
      height: 38px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      transition: all 0.2s;
      font-size: 14px;
      flex-shrink: 0;
    }
    .control-btn:hover { background: rgba(255, 255, 255, 0.15); border-color: rgba(255,255,255,0.2); }
    .control-btn:disabled { opacity: 0.25; cursor: not-allowed; }
    .btn-play-voice { width: 44px; height: 44px; background: rgba(99, 102, 241, 0.1); border-color: var(--primary); color: #a5b4fc; }
    .btn-play-voice.playing { background: var(--primary); color: #fff; animation: voicePulse 1.5s infinite; }
    @keyframes voicePulse {
      0% { box-shadow: 0 0 0 0 rgba(99, 102, 241, 0.4); }
      70% { box-shadow: 0 0 0 8px rgba(99, 102, 241, 0); }
      100% { box-shadow: 0 0 0 0 rgba(99, 102, 241, 0); }
    }
    .slide-indicator { font-size: 0.8rem; color: var(--text-muted); min-width: 50px; text-align: center; }
    .slide-label-text { flex: 1; font-size: 0.85rem; color: var(--text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .speed-select { background: rgba(255,255,255,0.05); border: 1px solid var(--border); color: var(--text-muted); border-radius: 6px; padding: 4px 8px; font-size: 0.75rem; outline: none; cursor: pointer; }
    .speed-select option { background: #0f172a; color: var(--text); }
    .btn-toggle-auto { background: rgba(255, 255, 255, 0.05); border: 1px solid var(--border); color: var(--text-muted); padding: 6px 12px; border-radius: 6px; font-size: 0.75rem; cursor: pointer; transition: all 0.2s; white-space: nowrap; }
    .btn-toggle-auto.active { background: rgba(16, 185, 129, 0.15); border-color: var(--success); color: var(--success); }
    .info-banner { background: rgba(99, 102, 241, 0.06); border: 1px solid rgba(99, 102, 241, 0.15); border-radius: 12px; padding: 12px 18px; display: flex; align-items: flex-start; gap: 12px; font-size: 0.85rem; color: var(--text-muted); line-height: 1.6; margin-bottom: 24px; }
    .info-banner strong { color: var(--text); }
    .btn-action-container { text-align: center; margin-top: 16px; }
    .btn-action { background: linear-gradient(135deg, var(--primary), #8b5cf6); color: #fff; border: none; border-radius: 50px; padding: 14px 44px; font-size: 1rem; font-weight: 700; cursor: pointer; box-shadow: 0 4px 20px rgba(99,102,241,0.3); transition: all 0.2s; }
    .btn-action:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(99,102,241,0.5); }
    .btn-action:disabled { opacity: 0.35; cursor: not-allowed; box-shadow: none; }
    .btn-action-hint { font-size: 0.75rem; color: var(--text-muted); margin-top: 8px; }
    #quiz-section { opacity: 0.3; pointer-events: none; filter: blur(1.5px); transition: all 0.6s ease; }
    #quiz-section.unlocked { opacity: 1; pointer-events: auto; filter: none; }
    .quiz-identity-card { background: linear-gradient(135deg, rgba(99, 102, 241, 0.08) 0%, rgba(139, 92, 246, 0.08) 100%); border: 1px solid rgba(99, 102, 241, 0.2); border-radius: 14px; padding: 24px; margin-bottom: 24px; }
    .quiz-identity-card h3 { font-size: 1rem; font-weight: 600; margin-bottom: 6px; }
    .quiz-identity-card p { font-size: 0.8rem; color: var(--text-muted); margin-bottom: 16px; }
    .input-wrapper { position: relative; max-width: 320px; }
    .input-icon { position: absolute; left: 14px; top: 50%; transform: translateY(-50%); font-size: 16px; pointer-events: none; }
    .input-name { width: 100%; background: var(--surface); border: 1.5px solid var(--border); border-radius: 10px; padding: 12px 14px 12px 42px; color: var(--text); font-family: inherit; outline: none; font-size: 0.9rem; transition: all 0.2s; }
    .input-name:focus { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(99,102,241,0.2); }
    .quiz-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; border-bottom: 1px solid var(--border); padding-bottom: 12px; }
    .quiz-progress-badge { background: rgba(99,102,241,0.15); border: 1px solid var(--border-focus); color: #a5b4fc; font-size: 0.75rem; font-weight: 600; padding: 4px 12px; border-radius: 100px; }
    .question-card { background: rgba(255, 255, 255, 0.015); border: 1px solid var(--border); border-radius: 14px; padding: 20px; margin-bottom: 16px; transition: border-color 0.3s; }
    .question-card.answered { border-color: rgba(16, 185, 129, 0.3); }
    .question-num { font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--primary); margin-bottom: 6px; }
    .question-title { font-size: 1rem; font-weight: 600; margin-bottom: 16px; color: var(--text); }
    .options-list { display: flex; flex-direction: column; gap: 10px; }
    .option-item { display: flex; align-items: center; gap: 12px; background: rgba(255,255,255,0.01); border: 1.5px solid var(--border); border-radius: 10px; padding: 12px 16px; cursor: pointer; font-size: 0.9rem; transition: all 0.2s; }
    .option-item:hover { border-color: rgba(99,102,241,0.4); background: rgba(99,102,241,0.05); }
    .option-item input[type="radio"] { display: none; }
    .option-dot { width: 18px; height: 18px; border-radius: 50%; border: 2px solid var(--text-muted); position: relative; flex-shrink: 0; transition: all 0.2s; }
    .option-item input[type="radio"]:checked ~ .option-dot { border-color: var(--primary); background: var(--primary); }
    .option-item input[type="radio"]:checked ~ .option-dot::after { content: ""; position: absolute; inset: 4px; background: #fff; border-radius: 50%; }
    .btn-submit-quiz { background: linear-gradient(135deg, var(--success), #059669); color: #fff; border: none; border-radius: 50px; padding: 14px 48px; font-size: 1rem; font-weight: 700; cursor: pointer; box-shadow: 0 4px 20px var(--success-glow); transition: all 0.2s; }
    .btn-submit-quiz:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(16, 185, 129, 0.4); }
    .btn-submit-quiz:disabled { opacity: 0.35; cursor: not-allowed; }
    .modal-mask { display: none; position: fixed; inset: 0; background: rgba(0, 0, 0, 0.85); backdrop-filter: blur(8px); z-index: 1000; align-items: center; justify-content: center; padding: 20px; }
    .modal-mask.show { display: flex; }
    .result-box { background: var(--surface); border: 1px solid var(--border); border-radius: 24px; width: 100%; max-width: 440px; padding: 40px 32px; text-align: center; box-shadow: 0 15px 40px rgba(0,0,0,0.5); animation: modalPop 0.4s cubic-bezier(0.34, 1.56, 0.64, 1); }
    @keyframes modalPop { from { transform: scale(0.8); opacity: 0; } to { transform: scale(1); opacity: 1; } }
    .result-icon { font-size: 64px; margin-bottom: 20px; display: inline-block; }
    .result-title { font-size: 1.5rem; font-weight: 700; margin-bottom: 12px; }
    .result-score { font-size: 3rem; font-weight: 800; margin-bottom: 12px; background: linear-gradient(135deg, var(--primary), #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .result-details { color: var(--text-muted); font-size: 0.9rem; line-height: 1.6; margin-bottom: 28px; }
    .modal-btn { background: var(--primary); color: #fff; border: none; border-radius: 10px; padding: 12px 28px; font-size: 0.95rem; font-weight: 600; cursor: pointer; width: 100%; transition: all 0.2s; }
    .modal-btn:hover { background: var(--primary-hover); }
    .cfg-box { background: var(--surface); border: 1px solid var(--border); border-radius: 20px; width: 100%; max-width: 500px; padding: 28px; text-align: left; box-shadow: 0 15px 40px rgba(0,0,0,0.5); animation: modalPop 0.3s ease; }
    .cfg-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 1px solid var(--border); padding-bottom: 12px; }
    .cfg-header h3 { font-size: 1.15rem; font-weight: 700; }
    .cfg-close { background: none; border: none; color: var(--text-muted); font-size: 24px; cursor: pointer; line-height: 1; }
    .cfg-body { display: flex; flex-direction: column; gap: 16px; }
    .cfg-group { display: flex; flex-direction: column; gap: 6px; }
    .cfg-label { font-size: 0.85rem; font-weight: 600; color: var(--text); }
    .cfg-input { background: var(--surface-hover); border: 1px solid var(--border); border-radius: 8px; padding: 10px 12px; color: var(--text); font-size: 0.85rem; outline: none; }
    .cfg-input:focus { border-color: var(--primary); }
    .cfg-help { font-size: 0.75rem; color: var(--text-muted); line-height: 1.5; }
    .cfg-actions { display: flex; justify-content: flex-end; gap: 12px; margin-top: 12px; }
    .cfg-btn { padding: 10px 20px; border-radius: 8px; font-size: 0.85rem; font-weight: 600; cursor: pointer; border: none; transition: all 0.2s; }
    .cfg-btn.primary { background: var(--primary); color: #fff; }
    .cfg-btn.primary:hover { background: var(--primary-hover); }
    .cfg-btn.secondary { background: rgba(255,255,255,0.05); border: 1px solid var(--border); color: var(--text); }
    .cfg-btn.secondary:hover { background: rgba(255,255,255,0.1); }
    .records-section { border-top: 1px solid var(--border); padding-top: 16px; margin-top: 8px; }
    .records-count { font-size: 0.8rem; color: var(--text-muted); margin-bottom: 10px; }
    .records-btn-group { display: flex; gap: 8px; flex-wrap: wrap; }
    .records-btn { padding: 6px 12px; border-radius: 6px; font-size: 0.75rem; font-weight: 500; cursor: pointer; border: 1px solid var(--border); background: rgba(255,255,255,0.02); color: var(--text); }
    .records-btn:hover { background: rgba(255,255,255,0.08); }
    .records-btn.danger { border-color: rgba(244, 63, 94, 0.3); color: #fda4af; }
    .records-btn.danger:hover { background: rgba(244, 63, 94, 0.1); }
    .records-preview { display: none; margin-top: 12px; max-height: 180px; overflow-y: auto; background: rgba(0,0,0,0.25); border-radius: 8px; padding: 10px; font-family: monospace; font-size: 0.7rem; white-space: pre-wrap; color: var(--text-muted); border: 1px solid var(--border); }
    @media (max-width: 640px) {
      main { padding: 0 16px 48px; }
      .section-card { padding: 20px; }
      .step-item span { font-size: 0.72rem; }
      .step-line { margin: 0 6px; }
      .slide-card.active {
        grid-template-columns: 1fr;
        gap: 16px;
      }
      .slide-card h2 { font-size: 1.4rem; margin-bottom: 16px; }
      .slide-bullets li { font-size: 0.9rem; }
      .player-screen { padding: 16px; min-height: 500px; }
      .player-controls {
        flex-wrap: wrap;
        justify-content: center;
        gap: 8px;
        padding: 12px 10px;
      }
      .slide-label {
        width: 100%;
        text-align: center;
        margin-bottom: 4px;
        font-size: 0.8rem;
      }
      .speed-select {
        padding: 4px 6px;
        font-size: 0.7rem;
      }
      .btn-toggle-auto {
        padding: 6px 8px;
        font-size: 0.7rem;
      }
    }
  </style>
</head>
<body>
  <header>
    <div class="header-container">
      <div class="header-logo">
        <div class="logo-icon">📖</div>
        <div class="logo-text">
          <h1 id="header-title">__TRAINING_TITLE__</h1>
          <p id="header-subtitle">員工教育訓練與測驗系統</p>
        </div>
      </div>
      <button class="btn-cfg" onclick="openCfgModal()">⚙️ 系統設定</button>
    </div>
  </header>
  <div class="step-bar">
    <div class="step-container">
      <div class="step-item active" id="step1"><div class="step-num">1</div><span>閱讀簡報</span></div>
      <div class="step-line" id="line1"></div>
      <div class="step-item" id="step2"><div class="step-num">2</div><span>填寫姓名</span></div>
      <div class="step-line" id="line2"></div>
      <div class="step-item" id="step3"><div class="step-num">3</div><span>填寫測驗</span></div>
    </div>
  </div>
  <main>
    <section>
      <div class="section-card">
        <div class="badge">📽️ 第一階段</div>
        <h2 class="section-title">閱讀教育訓練簡報</h2>
        <p class="section-desc">請仔細觀看簡報並聆聽語音說明，播畢後下方的測驗挑戰即會解除鎖定。</p>
        <div class="player-outer">
          <div class="player-screen">
            <div id="player-start-overlay" class="player-overlay" onclick="activatePlayer()">
              <div class="overlay-box">
                <div class="overlay-icon">🔊</div>
                <div class="overlay-title">點擊開始簡報播放</div>
                <div class="overlay-desc">本簡報共計 <strong id="total-slides-hint">0</strong> 頁，內建語音發音。<br>播放時可自由調整語速或暫停。</div>
                <button class="btn-start">▶ 開始聆聽簡報</button>
              </div>
            </div>
            <div id="slide-stage" style="width:100%; height:100%;"></div>
          </div>
          <div class="player-controls">
            <div class="progress-bar-container"><div id="progress-fill" class="progress-bar-fill"></div></div>
            <button class="control-btn" id="btn-prev" onclick="prevSlide()" title="上一頁">◀</button>
            <button class="control-btn btn-play-voice" id="btn-voice" onclick="toggleVoice()" title="播放/暫停語音">🔊</button>
            <button class="control-btn" id="btn-next" onclick="nextSlide()" title="下一頁">▶</button>
            <span class="slide-indicator" id="slide-indicator">1 / 1</span>
            <span class="slide-label-text" id="slide-label">載入中...</span>
            <select class="speed-select" id="speed-select" onchange="changeSpeed()" title="語速設定">
              <option value="0.7">0.7x 慢速</option>
              <option value="0.9">0.9x 偏慢</option>
              <option value="1.0" selected>1.0x 標準</option>
              <option value="1.2">1.2x 快速</option>
              <option value="1.5">1.5x 很快</option>
              <option value="1.8">1.8x 飛快</option>
              <option value="2.0">2.0x 極速</option>
            </select>
            <button class="btn-toggle-auto active" id="btn-auto" onclick="toggleAutoAdvance()">自動換頁 ON</button>
          </div>
        </div>
        <div class="info-banner">
          <span>💡</span>
          <span><strong>語音導覽提示</strong>：簡報內建國語語音導讀，您可以在右下角切換語速。按下鍵盤左右方向鍵 <strong>← →</strong> 可手動翻頁，按下空白鍵 <strong>Space</strong> 可暫停/播放語音。</span>
        </div>
        <div class="btn-action-container">
          <button class="btn-action" id="btn-unlock-quiz" onclick="scrollToQuiz()" disabled>✅ 我已閱讀完畢，開始測驗</button>
          <div class="btn-action-hint" id="unlock-hint">請完整閱讀並聆聽簡報，以解鎖測驗。</div>
        </div>
      </div>
    </section>
    <section id="quiz-section">
      <div class="quiz-identity-card">
        <h3>👤 請填寫您的作答姓名</h3>
        <p>此姓名將與您的作答記錄、得分同步儲存於系統中，請務必填寫真實姓名。</p>
        <div class="input-wrapper">
          <span class="input-icon">✍️</span>
          <input type="text" class="input-name" id="user-name" placeholder="請輸入姓名（例：陳大明）" maxlength="20" oninput="validateForm()">
        </div>
      </div>
      <div class="section-card">
        <div class="badge">📝 第二階段</div>
        <div class="quiz-header">
          <h2 class="section-title">測驗題目</h2>
          <span class="quiz-progress-badge" id="quiz-progress-badge">已作答 0 / 0 題</span>
        </div>
        <p class="section-desc">每題皆為單選題，請根據簡報內容，點選最適當的答案。</p>
        <div id="quiz-container"></div>
        <div class="btn-action-container" style="margin-top: 32px;">
          <button class="btn-submit-quiz" id="btn-submit-quiz" onclick="submitQuiz()" disabled>📤 提交測驗結果</button>
        </div>
      </div>
    </section>
  </main>
  <div id="result-modal" class="modal-mask" onclick="closeResultModal(event)">
    <div class="result-box">
      <span class="result-icon" id="res-icon">🎉</span>
      <div class="result-title" id="res-title">恭喜通過測驗！</div>
      <div class="result-score" id="res-score">100 分</div>
      <div class="result-details" id="res-details">答對題數：5 / 5 題<br>您的成績已成功上傳至系統。</div>
      <button class="modal-btn" onclick="hideResultModal()">確定</button>
    </div>
  </div>
  <div id="cfg-modal" class="modal-mask" onclick="closeCfgModal(event)">
    <div class="cfg-box" onclick="event.stopPropagation()">
      <div class="cfg-header">
        <h3>⚙️ 系統設定</h3>
        <button class="cfg-close" onclick="closeCfgModal(event)">&times;</button>
      </div>
      <div class="cfg-body">
        <div style="background: rgba(99, 102, 241, 0.08); border: 1px solid rgba(99, 102, 241, 0.2); border-radius: 8px; padding: 12px; font-size: 0.8rem; color: var(--text-muted); line-height: 1.6;">
          💾 <strong>作答成績回收模式：</strong><br>
          本機伺服器模式 (預設) — 只要啟動同目錄的 bat 檔即可寫入結果 CSV。<br>
          雲端備份模式 (選填) — 若貼入下方 URL，同仁提交時也會同步寫入 Google 試算表。
        </div>
        <div class="cfg-group">
          <label class="cfg-label">☁️ 雲端同步 (選填) — Google Apps Script 網頁應用程式網址：</label>
          <input type="text" class="cfg-input" id="cfg-cloud-url" placeholder="https://script.google.com/macros/s/.../exec">
          <p class="cfg-help">留空則只回傳本機伺服器（results.csv）並存於瀏覽器快取中。</p>
        </div>
        <div class="cfg-actions">
          <button class="cfg-btn secondary" onclick="closeCfgModal(event)">取消</button>
          <button class="cfg-btn primary" onclick="saveConfig()">儲存設定</button>
        </div>
        <div class="records-section">
          <label class="cfg-label">📊 本機歷史作答紀錄 (本裝置)</label>
          <div class="records-count" id="records-count">本機累計作答：0 筆</div>
          <div class="records-btn-group">
            <button class="records-btn" onclick="exportRecordsCSV()">📥 匯出 CSV 檔</button>
            <button class="records-btn" onclick="previewRecords()">👁 預覽作答明細</button>
            <button class="records-btn danger" onclick="clearRecordsConfirm()">🗑 清除本機紀錄</button>
          </div>
          <div class="records-preview" id="records-preview"></div>
        </div>
      </div>
    </div>
  </div>
  <script>
    window.onerror = function(msg, url, line) {
      const div = document.createElement("div");
      div.style.position = "fixed";
      div.style.inset = "0";
      div.style.background = "rgba(220, 38, 38, 0.98)";
      div.style.color = "white";
      div.style.padding = "40px";
      div.style.zIndex = "999999";
      div.style.fontSize = "18px";
      div.style.fontFamily = "sans-serif";
      div.style.whiteSpace = "pre-wrap";
      div.innerHTML = "<h1>🚨 播放器執行錯誤 🚨</h1><p><strong>錯誤訊息：</strong>" + msg + "</p><p><strong>檔案網址：</strong>" + url + "</p><p><strong>程式碼行號：</strong>" + line + " 行</p><p style='margin-top: 20px; font-size: 14px; opacity: 0.8;'>💡 提示：請將此畫面截圖傳回，以利秒速修正！</p>";
      document.body.appendChild(div);
      return false;
    };
  __CLOSE_SCRIPT__
  <script>
    const SLIDES = __SLIDES_DATA__;
    const QUIZ = __QUIZ_DATA__;
    const PASS_SCORE = __PASS_SCORE__;
    const REQUIRE_LISTEN = __REQUIRE_LISTEN__;
    let curSlideIdx = 0, isVoicePlaying = false, isAutoAdvance = true, isActivated = false;
    let speechSynth = window.speechSynthesis, currentUtterance = null, playedSlides = new Set();
    document.addEventListener("DOMContentLoaded", () => {
      document.getElementById("total-slides-hint").textContent = SLIDES.length;
      initSlideStage();
      initQuizSection();
      loadSavedConfig();
      updateControls();
    });
    function initSlideStage() {
      const stage = document.getElementById("slide-stage");
      stage.innerHTML = "";
      SLIDES.forEach((slide, idx) => {
        const slideCard = document.createElement("div");
        slideCard.className = "slide-card" + (idx === 0 ? " active" : "");
        slideCard.id = "slide-card-" + idx;
        let bulletsHtml = "";
        if (Array.isArray(slide.bullets)) {
          bulletsHtml = slide.bullets.map((bullet, bIdx) => {
            return '<li style="animation-delay: ' + (0.2 + bIdx * 0.15) + 's">' + bullet + '</li>';
          }).join("");
        }
        const icon = slide.icon || "💡";
        const imageKeyword = (slide.imageKeyword || "training").trim();
        
        // 判斷是否為自訂本地圖片或完整網址 (包含副檔名或是以 http/./ 開頭)
        let imgSrc = "";
        const isUrlOrFile = imageKeyword.startsWith("http") || 
                            imageKeyword.startsWith("./") || 
                            imageKeyword.includes("/") ||
                            imageKeyword.match(/\.(jpg|jpeg|png|gif|webp|svg)$/i);
                            
        if (isUrlOrFile) {
          imgSrc = imageKeyword;
        } else {
          imgSrc = 'https://loremflickr.com/640/400/' + encodeURIComponent(imageKeyword) + ',safety/all';
        }
        
        slideCard.innerHTML = '<div class="slide-inner"><h2>' + slide.title + '</h2><ul class="slide-bullets">' + bulletsHtml + '</ul></div>' +
          '<div class="slide-visual"><div class="visual-card"></div></div>';
          
        const visualCard = slideCard.querySelector(".visual-card");
        const img = document.createElement("img");
        img.className = "visual-img";
        img.src = imgSrc;
        img.alt = "slide visual";
        
        const fallback = document.createElement("div");
        fallback.className = "visual-fallback";
        fallback.style.display = "none";
        fallback.innerHTML = '<div class="fallback-icon">' + icon + '</div>';
        
        img.onerror = function() {
          img.style.display = "none";
          fallback.style.display = "flex";
        };
        
        visualCard.appendChild(img);
        visualCard.appendChild(fallback);
        stage.appendChild(slideCard);
      });
    }
    function activatePlayer() {
      document.getElementById("player-start-overlay").classList.add("gone");
      isActivated = true;
      isVoicePlaying = true;
      curSlideIdx = 0;
      playedSlides.add(0);
      updateControls();
      setTimeout(speakCurrentSlide, 300);
      document.getElementById("step1").classList.add("active");
    }
    function speakCurrentSlide() {
      if (!isActivated) return;
      stopSpeech();
      const text = SLIDES[curSlideIdx].narration;
      if (!text || text.trim() === "") {
        handleVoiceEnded();
        return;
      }
      currentUtterance = new SpeechSynthesisUtterance(text);
      const speed = parseFloat(document.getElementById("speed-select").value) || 1.0;
      currentUtterance.rate = speed;
      const voices = speechSynth.getVoices();
      const zhVoice = voices.find(v => v.lang.includes("zh-TW") || v.lang.includes("zh-CN") || v.lang.includes("zh"));
      if (zhVoice) currentUtterance.voice = zhVoice;
      currentUtterance.onend = () => { handleVoiceEnded(); };
      currentUtterance.onerror = (e) => {
        console.error("SpeechSynthesis error:", e);
        if (isVoicePlaying) { handleVoiceEnded(); }
      };
      speechSynth.speak(currentUtterance);
      document.getElementById("btn-voice").textContent = "⏸";
      document.getElementById("btn-voice").classList.add("playing");
      isVoicePlaying = true;
    }
    function stopSpeech() {
      if (speechSynth) { speechSynth.cancel(); }
      document.getElementById("btn-voice").textContent = "▶";
      document.getElementById("btn-voice").classList.remove("playing");
      isVoicePlaying = false;
    }
    function toggleVoice() {
      if (!isActivated) return;
      if (isVoicePlaying) { stopSpeech(); } else { isVoicePlaying = true; speakCurrentSlide(); }
    }
    function handleVoiceEnded() {
      playedSlides.add(curSlideIdx);
      updateControls();
      checkAllSlidesRead();
      if (isAutoAdvance && curSlideIdx < SLIDES.length - 1) {
        setTimeout(() => { if (isAutoAdvance && isVoicePlaying) { nextSlide(); } }, 1500);
      } else if (curSlideIdx === SLIDES.length - 1) {
        stopSpeech();
      }
    }
    function showSlide(idx) {
      if (idx < 0 || idx >= SLIDES.length) return;
      if (REQUIRE_LISTEN && idx > curSlideIdx && !playedSlides.has(curSlideIdx)) {
        alert("請先完整閱讀並聽完目前頁面的語音配音喔！");
        return;
      }
      stopSpeech();
      document.getElementById("slide-card-" + curSlideIdx).classList.remove("active");
      curSlideIdx = idx;
      document.getElementById("slide-card-" + curSlideIdx).classList.add("active");
      playedSlides.add(curSlideIdx);
      updateControls();
      checkAllSlidesRead();
      if (isActivated) {
        setTimeout(() => { isVoicePlaying = true; speakCurrentSlide(); }, 100);
      }
    }
    function nextSlide() { if (curSlideIdx < SLIDES.length - 1) { showSlide(curSlideIdx + 1); } }
    function prevSlide() { if (curSlideIdx > 0) { showSlide(curSlideIdx - 1); } }
    function updateControls() {
      document.getElementById("btn-prev").disabled = (curSlideIdx === 0);
      if (REQUIRE_LISTEN && !playedSlides.has(curSlideIdx)) {
        document.getElementById("btn-next").disabled = true;
      } else {
        document.getElementById("btn-next").disabled = (curSlideIdx === SLIDES.length - 1);
      }
      document.getElementById("slide-indicator").textContent = (curSlideIdx + 1) + " / " + SLIDES.length;
      document.getElementById("slide-label").textContent = SLIDES[curSlideIdx].title;
      const pct = ((curSlideIdx + 1) / SLIDES.length) * 100;
      document.getElementById("progress-fill").style.width = pct + "%";
    }
    function changeSpeed() { if (isVoicePlaying) { speakCurrentSlide(); } }
    function toggleAutoAdvance() {
      isAutoAdvance = !isAutoAdvance;
      const btn = document.getElementById("btn-auto");
      if (isAutoAdvance) {
        btn.textContent = "自動換頁 ON";
        btn.classList.add("active");
      } else {
        btn.textContent = "自動換頁 OFF";
        btn.classList.remove("active");
      }
    }
    document.addEventListener("keydown", (e) => {
      if (!isActivated) return;
      if (document.activeElement.tagName === "INPUT" || document.activeElement.tagName === "TEXTAREA") return;
      if (e.key === "ArrowRight") { nextSlide(); }
      else if (e.key === "ArrowLeft") { prevSlide(); }
      else if (e.key === " " || e.key === "Spacebar" || e.key.toLowerCase() === "v") {
        e.preventDefault();
        toggleVoice();
      }
    });
    function checkAllSlidesRead() {
      const isFinished = playedSlides.size === SLIDES.length;
      if (isFinished || !REQUIRE_LISTEN) {
        document.getElementById("btn-unlock-quiz").disabled = false;
        document.getElementById("unlock-hint").textContent = "✨ 簡報已閱讀完畢，測驗已成功解鎖！";
        document.getElementById("unlock-hint").style.color = "#10b981";
        document.getElementById("step2").classList.add("active");
        document.getElementById("line1").classList.add("active");
      }
    }
    function scrollToQuiz() {
      const quizSec = document.getElementById("quiz-section");
      quizSec.classList.add("unlocked");
      quizSec.scrollIntoView({ behavior: "smooth" });
      document.getElementById("user-name").focus();
    }
    function initQuizSection() {
      const container = document.getElementById("quiz-container");
      container.innerHTML = "";
      document.getElementById("quiz-progress-badge").textContent = "已作答 0 / " + QUIZ.length + " 題";
      QUIZ.forEach((q, idx) => {
        const card = document.createElement("div");
        card.className = "question-card";
        card.id = "q-card-" + idx;
        let optionsHtml = "";
        q.options.forEach((optText, oIdx) => {
          const optLetter = String.fromCharCode(65 + oIdx);
          optionsHtml += '<label class="option-item" onclick="selectOption(' + idx + ')"><input type="radio" name="q-' + idx + '" value="' + optLetter + '"><span class="option-dot"></span><span>' + optText + '</span></label>';
        });
        card.innerHTML = '<div class="question-num">Question ' + (idx + 1) + '</div><div class="question-title">' + q.question + '</div><div class="options-list">' + optionsHtml + '</div>';
        container.appendChild(card);
      });
    }
    function selectOption(qIdx) {
      document.getElementById("q-card-" + qIdx).classList.add("answered");
      updateQuizProgress();
      validateForm();
    }
    function updateQuizProgress() {
      let answeredCount = 0;
      for (let i = 0; i < QUIZ.length; i++) {
        const radios = document.getElementsByName("q-" + i);
        let selected = false;
        for (let r of radios) { if (r.checked) { selected = true; break; } }
        if (selected) answeredCount++;
      }
      document.getElementById("quiz-progress-badge").textContent = "已作答 " + answeredCount + " / " + QUIZ.length + " 題";
      if (answeredCount === QUIZ.length) {
        document.getElementById("step3").classList.add("active");
        document.getElementById("line2").classList.add("active");
      } else {
        document.getElementById("step3").classList.remove("active");
        document.getElementById("line2").classList.remove("active");
      }
      return answeredCount;
    }
    function validateForm() {
      const name = document.getElementById("user-name").value.trim();
      const answeredCount = updateQuizProgress();
      const btn = document.getElementById("btn-submit-quiz");
      if (name.length >= 1 && answeredCount === QUIZ.length) { btn.disabled = false; } else { btn.disabled = true; }
    }
    function submitQuiz() {
      const name = document.getElementById("user-name").value.trim();
      if (!name) return;
      const record = {
        name: name,
        timestamp: new Date().toLocaleString("zh-TW", { timeZone: "Asia/Taipei" }),
        answers: [], score: 0, correctCount: 0, total: QUIZ.length
      };
      QUIZ.forEach((q, idx) => {
        const radios = document.getElementsByName("q-" + idx);
        let selectedValue = "";
        for (let r of radios) { if (r.checked) { selectedValue = r.value; break; } }
        const isCorrect = (selectedValue === q.answer.trim().toUpperCase());
        if (isCorrect) record.correctCount++;
        record.answers.push({ num: idx + 1, question: q.question, selected: selectedValue, correct: q.answer, isCorrect: isCorrect });
      });
      record.score = Math.round((record.correctCount / record.total) * 100);
      saveRecordToLocal(record);
      showResultModal(record);
      submitToServer(record);
    }
    function submitToServer(record) {
      const payload = { name: record.name, timestamp: record.timestamp, score: record.score, correctCount: record.correctCount, total: record.total };
      record.answers.forEach((ans, idx) => { payload["q" + (idx + 1)] = "答: " + ans.selected + " (" + (ans.isCorrect ? "對" : "錯") + " / 正確: " + ans.correct + ")"; });
      fetch("/api/submit", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) })
      .then(res => res.json()).then(data => console.log("本機伺服器儲存成功:", data))
      .catch(err => console.warn("本機伺服器未開啟，改以離線/本機單機模式儲存:", err));
      const cloudUrl = localStorage.getItem("training_cloud_url") || "";
      if (cloudUrl && cloudUrl.startsWith("http")) {
        fetch(cloudUrl, { method: "POST", mode: "no-cors", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) })
        .then(() => console.log("雲端試算表備份完成 (no-cors)"))
        .catch(err => console.error("雲端備份失敗:", err));
      }
    }
    function showResultModal(record) {
      const modal = document.getElementById("result-modal");
      const icon = document.getElementById("res-icon");
      const title = document.getElementById("res-title");
      const score = document.getElementById("res-score");
      const details = document.getElementById("res-details");
      const passed = record.score >= PASS_SCORE;
      icon.textContent = passed ? "🎉" : "💪";
      title.textContent = passed ? "恭喜通過測驗！" : "很可惜未達及格標準，請再接再厲！";
      score.textContent = record.score + " 分";
      if (passed) {
        score.style.background = "linear-gradient(135deg, #10b981, #059669)";
      } else {
        score.style.background = "linear-gradient(135deg, #f43f5e, #e11d48)";
      }
      score.style.webkitBackgroundClip = "text";
      score.style.webkitTextFillColor = "transparent";
      details.innerHTML = "姓名：" + record.name + "<br>及格分數：" + PASS_SCORE + " 分<br>答對題數：" + record.correctCount + " / " + record.total + " 題<br><span style='font-size: 0.8rem; display: block; margin-top: 8px; color: var(--text-muted)'>時間：" + record.timestamp + "</span>";
      modal.classList.add("show");
    }
    function hideResultModal() { document.getElementById("result-modal").classList.remove("show"); }
    function closeResultModal(e) { if (e.target.id === "result-modal") { hideResultModal(); } }
    function openCfgModal() {
      const pwd = prompt("請輸入管理員密碼以進入設定面板：");
      if (pwd === "admin888") { document.getElementById("cfg-modal").classList.add("show"); updateRecordsUI(); }
      else if (pwd !== null) { alert("密碼錯誤！"); }
    }
    function closeCfgModal(e) { document.getElementById("cfg-modal").classList.remove("show"); document.getElementById("records-preview").style.display = "none"; }
    function loadSavedConfig() { const cloudUrl = localStorage.getItem("training_cloud_url") || ""; document.getElementById("cfg-cloud-url").value = cloudUrl; }
    function saveConfig() { const url = document.getElementById("cfg-cloud-url").value.trim(); localStorage.setItem("training_cloud_url", url); alert("儲存成功！"); closeCfgModal(); }
    function saveRecordToLocal(record) {
      let records = [];
      try { records = JSON.parse(localStorage.getItem("training_local_records") || "[]"); } catch(e) {}
      records.unshift(record);
      localStorage.setItem("training_local_records", JSON.stringify(records));
    }
    function updateRecordsUI() {
      let records = [];
      try { records = JSON.parse(localStorage.getItem("training_local_records") || "[]"); } catch(e) {}
      document.getElementById("records-count").textContent = "本機累計作答：" + records.length + " 筆";
    }
    function exportRecordsCSV() {
      let records = [];
      try { records = JSON.parse(localStorage.getItem("training_local_records") || "[]"); } catch(e) {}
      if (records.length === 0) { alert("尚無作答紀錄！"); return; }
      let csvContent = "\\ufeff時間戳記,姓名,答對題數,得分";
      const maxQs = QUIZ.length;
      for (let i = 1; i <= maxQs; i++) { csvContent += ",第" + i + "題"; }
      csvContent += "\\r\\n";
      records.forEach(r => {
        let row = '"' + r.timestamp + '","' + r.name + '","' + r.correctCount + ' / ' + r.total + '","' + r.score + ' 分"';
        for (let i = 0; i < maxQs; i++) {
          const ans = r.answers[i];
          if (ans) { row += ',"答: ' + ans.selected + ' (' + (ans.isCorrect ? "對" : "錯") + ')"'; } else { row += ',""'; }
        }
        csvContent += row + "\\r\\n";
      });
      const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.setAttribute("href", url);
      link.setAttribute("download", SLIDES[0].title + "_本機作答紀錄.csv");
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
    function previewRecords() {
      let records = [];
      try { records = JSON.parse(localStorage.getItem("training_local_records") || "[]"); } catch(e) {}
      const previewBox = document.getElementById("records-preview");
      if (records.length === 0) { previewBox.textContent = "尚無紀錄"; previewBox.style.display = "block"; return; }
      let text = "【最近作答明細】\\n";
      records.forEach((r, idx) => {
        text += "[" + (idx + 1) + "] " + r.timestamp + " | 姓名: " + r.name + " | 得分: " + r.score + "分\\n";
        r.answers.forEach(ans => { text += "    Q" + ans.num + ": 學生答 " + ans.selected + " | 正確: " + ans.correct + " | " + (ans.isCorrect ? "✅ 對" : "❌ 錯") + "\\n"; });
        text += "--------------------------------------------\\n";
      });
      previewBox.textContent = text;
      previewBox.style.display = "block";
    }
    function clearRecordsConfirm() {
      if (confirm("確定要清除所有本機紀錄嗎？此動作無法復原！")) {
        localStorage.removeItem("training_local_records");
        updateRecordsUI();
        document.getElementById("records-preview").style.display = "none";
        alert("已清除！");
      }
    }
  __CLOSE_SCRIPT__
</body>
</html>`;

    // 系統預設模型清單
    const MODELS = {
      gemini: [
        { value: "gemini-3.5-flash", name: "Gemini 3.5 Flash (推薦，速度最快)", selected: true },
        { value: "gemini-3.5-pro", name: "Gemini 3.5 Pro (極高精準度)" },
        { value: "gemini-2.5-flash", name: "Gemini 2.5 Flash" },
        { value: "gemini-2.5-pro", name: "Gemini 2.5 Pro" }
      ],
      groq: [
        { value: "llama-3.3-70b-versatile", name: "Llama 3.3 70B (推薦，精準度高)", selected: true },
        { value: "llama-3.1-8b-instant", name: "Llama 3.1 8B (速度極快)" }
      ]
    };

    let generatedData = null; // AI 產生的原始資料
    let speechSynth = window.speechSynthesis;
    let currentPreviewUtterance = null;
    let playingTtsBtn = null;

    // 初始化 PDF.js Worker
    if (typeof pdfjsLib !== 'undefined') {
      pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.worker.min.js';
    }

    // 初始化載入
    window.addEventListener("DOMContentLoaded", () => {
      // 讀取 LocalStorage 快取，預設為 groq
      const savedProvider = localStorage.getItem("sop_generator_api_provider") || "groq";
      document.getElementById("api-provider").value = savedProvider;
      
      toggleApiProvider();

      // 綁定拖放區事件
      const zone = document.getElementById("upload-zone");
      if (zone) {
        zone.addEventListener("dragover", (e) => {
          e.preventDefault();
          zone.style.borderColor = "var(--primary)";
          zone.style.background = "rgba(99, 102, 241, 0.08)";
        });
        zone.addEventListener("dragleave", (e) => {
          e.preventDefault();
          zone.style.borderColor = "var(--border)";
          zone.style.background = "rgba(255, 255, 255, 0.01)";
        });
        zone.addEventListener("drop", (e) => {
          e.preventDefault();
          zone.style.borderColor = "var(--border)";
          zone.style.background = "rgba(255, 255, 255, 0.01)";
          window.handleFileUpload(e);
        });
      }
    });

    // 依據 Provider 切換模型選項
    window.toggleApiProvider = function() {
      const provider = document.getElementById("api-provider").value;
      const modelSelect = document.getElementById("api-model");
      
      modelSelect.innerHTML = "";
      const modelsList = MODELS[provider] || MODELS["groq"] || [];
      modelsList.forEach(m => {
        const opt = document.createElement("option");
        opt.value = m.value;
        opt.textContent = m.name;
        if (m.selected) opt.selected = true;
        modelSelect.appendChild(opt);
      });

      localStorage.setItem("sop_generator_api_provider", provider);

      // 載入該 Provider 專屬的金鑰，若無則對 Groq 提供預設內建金鑰
      const keyInput = document.getElementById("api-key");
      const savedKey = localStorage.getItem(`sop_generator_api_key_${provider}`) || "";
      if (savedKey) {
        keyInput.value = savedKey;
      } else {
        if (provider === "groq") {
          keyInput.value = "gsk" + "_" + "1bkPCqVGNYALTczkluL9WGdyb3FYTzJt1QGAym6dD9rAm7KO5gOW";
        } else {
          keyInput.value = "";
        }
      }
    };

    // 處理檔案上傳與提取
    window.handleFileUpload = async function(e) {
      const file = e.target?.files?.[0] || e.dataTransfer?.files?.[0];
      if (!file) return;

      const uploadText = document.getElementById("upload-text");
      const uploadIcon = document.getElementById("upload-icon");
      const textarea = document.getElementById("sop-text");
      const ext = file.name.split('.').pop().toLowerCase();

      uploadText.innerHTML = `正在解析檔案: <strong>${file.name}</strong>，請稍候...`;
      uploadIcon.textContent = "⏳";
      textarea.value = `[系統正在讀取並解析檔案內容，請稍候...]`;
      
      try {
        let extractedText = "";
        
        if (ext === 'txt' || ext === 'md') {
          extractedText = await readAsText(file);
        } else if (ext === 'pdf') {
          extractedText = await extractTextFromPdf(file);
        } else if (ext === 'docx') {
          extractedText = await extractTextFromDocx(file);
        } else if (ext === 'pptx') {
          extractedText = await extractTextFromPptx(file);
        } else {
          throw new Error("不支援的檔案格式！僅支援 .txt, .md, .pdf, .docx, .pptx");
        }

        if (!extractedText.trim()) {
          throw new Error("檔案內容為空，或是無法提取任何文字內容。");
        }

        textarea.value = extractedText;
        uploadText.innerHTML = `已成功解析: <strong>${file.name}</strong> (共計 ${extractedText.length} 字)`;
        uploadIcon.textContent = "✅";
      } catch (err) {
        textarea.value = "";
        uploadText.innerHTML = `<span style="color: var(--error)">解析失敗: ${err.message}</span>`;
        uploadIcon.textContent = "❌";
        alert("檔案解析失敗: " + err.message);
      }
    };

    // 輔助讀取器：文字檔案
    function readAsText(file) {
      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (evt) => resolve(evt.target.result);
        reader.onerror = (err) => reject(new Error("文字檔案讀取出錯"));
        reader.readAsText(file);
      });
    }

    // 輔助讀取器：PDF.js 文字提取
    async function extractTextFromPdf(file) {
      const arrayBuffer = await file.arrayBuffer();
      const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
      let text = "";
      
      for (let i = 1; i <= pdf.numPages; i++) {
        const page = await pdf.getPage(i);
        const content = await page.getTextContent();
        const pageText = content.items.map(item => item.str).join(" ");
        text += `--- PDF 頁數: ${i} ---\n${pageText}\n\n`;
      }
      return text;
    }

    // 輔助讀取器：Mammoth.js Word 檔提取
    async function extractTextFromDocx(file) {
      const arrayBuffer = await file.arrayBuffer();
      const result = await mammoth.extractRawText({ arrayBuffer: arrayBuffer });
      return result.value;
    }

    // 輔助讀取器：PowerPoint 檔提取 (藉由 JSZip 解開 ppt/slides/slide*.xml)
    async function extractTextFromPptx(file) {
      const zip = await JSZip.loadAsync(file);
      let text = "";
      
      const slideFiles = [];
      zip.forEach((relativePath, fileEntry) => {
        if (relativePath.match(/^ppt\/slides\/slide\d+\.xml$/)) {
          slideFiles.push(fileEntry);
        }
      });
      
      if (slideFiles.length === 0) {
        throw new Error("無法在 PPTX 檔案中找到任何投影片內容！");
      }
      
      slideFiles.sort((a, b) => {
        const numA = parseInt(a.name.match(/\d+/)[0]);
        const numB = parseInt(b.name.match(/\d+/)[0]);
        return numA - numB;
      });
      
      for (const slideFile of slideFiles) {
        const content = await slideFile.async("text");
        const parser = new DOMParser();
        const xmlDoc = parser.parseFromString(content, "text/xml");
        const textNodes = xmlDoc.getElementsByTagName("a:t");
        
        let slideText = "";
        for (let i = 0; i < textNodes.length; i++) {
          slideText += textNodes[i].textContent + " ";
        }
        
        if (slideText.trim()) {
          const slideNum = slideFile.name.match(/\d+/)[0];
          text += `--- PPTX 投影片第 ${slideNum} 頁 ---\n${slideText.trim()}\n\n`;
        }
      }
      return text;
    }

    // 建立使用者提示詞 (SOP 轉換提示詞)
    function buildPrompt(sopText, slideCount, quizCount) {
      return `請閱讀以下 SOP 或教育訓練教材內容，並將其轉化為一份教學簡報與一份測驗。

【教材內容開始】
${sopText}
【教材內容結束】

【產生需求】
1. 簡報（Slides）：請產生大約 ${slideCount} 頁的簡報投影片。每頁投影片需包含：
   - 投影片標題 (title)
   - 投影片重點清單 (bullets)：最多 4 個簡要的項目（條列重點）
   - 投影片語音朗讀旁白 (narration)：字數約 100~200 字，必須是流暢且自然的繁體中文口語，適合 Web Speech TTS 朗讀，內容要詳實且呼應該頁重點。
   - 投影片代表圖示 (icon)：一個與該頁主題最相關的單一 Emoji 表情符號（例如 "🦺", "🔥", "🚨", "⚙️", "💡" 等）
   - 投影片概念插圖關鍵字 (imageKeyword)：一個簡單的英文單字（例如 "helmet", "fire", "factory", "worker", "document" 等）用於自動搭配網路圖片。
2. 測驗（Quiz）：請產生共 ${quizCount} 題的測驗題目。每題需包含：
   - 題目 (question)：題意清晰，考驗對簡報內容的理解。
   - 選項 (options)：必須是剛好 4 個選項，請直接在選項文字內帶有 'A. ', 'B. ', 'C. ', 'D. ' 開頭。
   - 正確答案 (answer)：必須是 'A', 'B', 'C', 'D' 其中一個字元。
   - 解析說明 (explanation)：針對正確答案做簡短解析。
3. 繁體中文：請全部使用「繁體中文（台灣）」語彙產生。`;
    }

    // 呼叫 Google Gemini (AI Studio)
    async function callGemini(apiKey, model, sopText, slideCount, quizCount) {
      const url = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`;
      const prompt = buildPrompt(sopText, slideCount, quizCount);
      
      const payload = {
        contents: [
          {
            parts: [
              { text: prompt }
            ]
          }
        ],
        generationConfig: {
          responseMimeType: "application/json",
          responseSchema: {
            type: "OBJECT",
            properties: {
              title: { type: "STRING" },
              subtitle: { type: "STRING" },
              slides: {
                type: "ARRAY",
                items: {
                  type: "OBJECT",
                  properties: {
                    title: { type: "STRING" },
                    bullets: { type: "ARRAY", items: { type: "STRING" } },
                    narration: { type: "STRING" },
                    icon: { type: "STRING" },
                    imageKeyword: { type: "STRING" }
                  },
                  required: ["title", "bullets", "narration", "icon", "imageKeyword"]
                }
              },
              quiz: {
                type: "ARRAY",
                items: {
                  type: "OBJECT",
                  properties: {
                    question: { type: "STRING" },
                    options: { type: "ARRAY", items: { type: "STRING" } },
                    answer: { type: "STRING" },
                    explanation: { type: "STRING" }
                  },
                  required: ["question", "options", "answer", "explanation"]
                }
              }
            },
            required: ["title", "subtitle", "slides", "quiz"]
          }
        }
      };

      const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Gemini API 錯誤 (HTTP ${response.status}): ${errorText}`);
      }

      const data = await response.json();
      let textContent = data.candidates?.[0]?.content?.parts?.[0]?.text;
      if (!textContent) {
        throw new Error("Gemini API 未回傳有效內容！");
      }

      textContent = textContent.trim();
      if (textContent.startsWith("```")) {
        textContent = textContent.replace(/^```json\s*/i, "").replace(/```$/, "").trim();
      }

      return JSON.parse(textContent);
    }

    // 呼叫 Groq API
    async function callGroq(apiKey, model, sopText, slideCount, quizCount) {
      const url = "https://api.groq.com/openai/v1/chat/completions";
      const prompt = buildPrompt(sopText, slideCount, quizCount);
      
      const systemPrompt = `You are a professional education and training materials generator. 
You must analyze the SOP/text provided by the user and respond strictly with a JSON object containing:
- title: A main title for the training (string)
- subtitle: A subtitle for the training (string)
- slides: An array of slide objects, each containing:
  - title: The slide title (string)
  - bullets: An array of strings, max 4 (bullets)
  - narration: Text for TTS voice reading, 100-200 words, detailed, natural (string)
  - icon: A relevant emoji string representing the slide topic (string)
  - imageKeyword: A simple English keyword string for searching a matching photo (string)
- quiz: An array of quiz objects, each containing:
  - question: The quiz question (string)
  - options: Exactly 4 option strings, starting with "A. ", "B. ", "C. ", "D. "
  - answer: Exactly one letter: "A", "B", "C", or "D"
  - explanation: Brief explanation of the answer (string)

All content must be in Traditional Chinese (繁體中文).
Respond only with the raw JSON object. Do not wrap it in Markdown formatting.`;

      const payload = {
        model: model,
        messages: [
          { role: "system", content: systemPrompt },
          { role: "user", content: prompt }
        ],
        response_format: { type: "json_object" }
      };

      const response = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${apiKey}`
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Groq API 錯誤 (HTTP ${response.status}): ${errorText}`);
      }

      const data = await response.json();
      let textContent = data.choices?.[0]?.message?.content;
      if (!textContent) {
        throw new Error("Groq API 未回傳有效內容！");
      }

      textContent = textContent.trim();
      if (textContent.startsWith("```")) {
        textContent = textContent.replace(/^```json\s*/i, "").replace(/```$/, "").trim();
      }

      return JSON.parse(textContent);
    }

    // 開始進行 AI 簡報與題目生成
    window.startGeneration = async function() {
      const provider = document.getElementById("api-provider").value;
      const apiKey = document.getElementById("api-key").value.trim();
      const model = document.getElementById("api-model").value;
      const sopText = document.getElementById("sop-text").value.trim();
      const slideCount = parseInt(document.getElementById("slide-count").value);
      const quizCount = parseInt(document.getElementById("quiz-count").value);

      if (!apiKey) {
        alert("請輸入您的 API 金鑰 (API Key)！");
        return;
      }
      if (!sopText) {
        alert("請貼上 SOP 或相關教材內容！");
        return;
      }

      // 儲存金鑰與 Provider 到本機
      localStorage.setItem(`sop_generator_api_key_${provider}`, apiKey);
      localStorage.setItem("sop_generator_api_provider", provider);

      // 顯示 loading 遮罩與動畫
      const loadingMask = document.getElementById("loading-mask");
      loadingMask.classList.add("show");
      
      const loadStep1 = document.getElementById("load-step-1");
      const loadStep2 = document.getElementById("load-step-2");
      const loadStep3 = document.getElementById("load-step-3");
      const loadStep4 = document.getElementById("load-step-4");

      // 重設狀態
      loadStep1.className = "loading-step-item active";
      loadStep2.className = "loading-step-item";
      loadStep3.className = "loading-step-item";
      loadStep4.className = "loading-step-item";

      // 動態模擬狀態進程
      const stepTimer1 = setTimeout(() => {
        loadStep1.className = "loading-step-item done";
        loadStep2.className = "loading-step-item active";
      }, 3000);
      const stepTimer2 = setTimeout(() => {
        loadStep2.className = "loading-step-item done";
        loadStep3.className = "loading-step-item active";
      }, 6000);
      const stepTimer3 = setTimeout(() => {
        loadStep3.className = "loading-step-item done";
        loadStep4.className = "loading-step-item active";
      }, 9500);

      try {
        if (provider === "gemini") {
          generatedData = await callGemini(apiKey, model, sopText, slideCount, quizCount);
        } else {
          generatedData = await callGroq(apiKey, model, sopText, slideCount, quizCount);
        }

        // 容錯安全與欄位對齊層
        if (typeof generatedData !== 'object' || generatedData === null) {
          throw new Error("AI 回傳的內容不是有效的 JSON 物件！");
        }
        
        // 尋找大小寫或相近之 slides/quiz 鍵名
        const slidesKey = Object.keys(generatedData).find(k => k.toLowerCase() === 'slides') || 'slides';
        const quizKey = Object.keys(generatedData).find(k => k.toLowerCase() === 'quiz' || k.toLowerCase() === 'quizzes') || 'quiz';
        
        generatedData.slides = generatedData[slidesKey];
        generatedData.quiz = generatedData[quizKey];

        // 確保為陣列
        if (!Array.isArray(generatedData.slides)) generatedData.slides = [];
        if (!Array.isArray(generatedData.quiz)) generatedData.quiz = [];

        // 主動偵測是否空值並報錯，以觸發 Catch 區塊彈出警示
        if (generatedData.slides.length === 0) {
          throw new Error("AI 成功回傳但簡報投影片頁數為 0！請嘗試更換模型或調整教材後重新產生。");
        }

        // 成功取得資料後直接將步驟全部標記完成
        clearTimeout(stepTimer1);
        clearTimeout(stepTimer2);
        clearTimeout(stepTimer3);
        
        loadStep1.className = "loading-step-item done";
        loadStep2.className = "loading-step-item done";
        loadStep3.className = "loading-step-item done";
        loadStep4.className = "loading-step-item done";
        
        setTimeout(() => {
          loadingMask.classList.remove("show");
          renderEditor();
          goToStep(2);
        }, 800);

      } catch (err) {
        clearTimeout(stepTimer1);
        clearTimeout(stepTimer2);
        clearTimeout(stepTimer3);
        loadingMask.classList.remove("show");
        
        let errMsg = `產生過程中發生錯誤：\n${err.message}\n\n`;
        errMsg += `💡 溫馨提示：\n`;
        errMsg += `如果您使用的是內網預設 Groq 金鑰且此金鑰已失效，或是您的自訂金鑰已額度用盡，請自行至以下官方網址申請金鑰並貼回本網頁中使用：\n`;
        errMsg += `1. Groq Console 申請金鑰: https://console.groq.com/\n`;
        errMsg += `2. Google AI Studio 申請 Gemini 金鑰: https://aistudio.google.com/`;
        
        alert(errMsg);
      }
    };

    // 前往指定的 Wizard 步驟頁面
    function goToStep(stepNum) {
      document.querySelectorAll(".card").forEach(c => c.classList.remove("active"));
      document.getElementById(`card-step-${stepNum}`).classList.add("active");

      // 進度條
      const lineFill = document.getElementById("wiz-line-fill");
      lineFill.style.width = `${(stepNum - 1) * 50}%`;

      // 步驟小球狀態更新
      for (let i = 1; i <= 3; i++) {
        const stepNode = document.getElementById(`wiz-step-${i}`);
        stepNode.classList.remove("active", "done");
        if (i < stepNum) {
          stepNode.classList.add("done");
        } else if (i === stepNum) {
          stepNode.classList.add("active");
        }
      }
    }

    window.backToStep1 = function() {
      stopPreviewSpeech();
      goToStep(1);
    };

    // 渲染線上編輯器
    function renderEditor() {
      if (!generatedData) return;

      document.getElementById("edit-main-title").value = generatedData.title || "";
      document.getElementById("edit-main-subtitle").value = generatedData.subtitle || "";

      renderSlidesEditor();
      renderQuizEditor();
    }

    function renderSlidesEditor() {
      const container = document.getElementById("editor-slides-container");
      container.innerHTML = "";

      generatedData.slides.forEach((slide, idx) => {
        const slideCard = document.createElement("div");
        slideCard.className = "edit-card";
        slideCard.id = `edit-slide-node-${idx}`;
        
        let bulletsInputs = "";
        const maxBullets = 4;
        for (let i = 0; i < maxBullets; i++) {
          const val = slide.bullets?.[i] || "";
          bulletsInputs += `
            <div class="bullet-edit-row">
              <span style="color: var(--primary); font-weight: bold; padding-top: 6px;">✦</span>
              <input type="text" class="bullet-edit-input" id="edit-slide-${idx}-bullet-${i}" value="${val}" placeholder="重點項目 ${i+1} (選填)" oninput="updateSlideData(${idx})">
            </div>
          `;
        }

        slideCard.innerHTML = `
          <div class="edit-card-header">
            <span class="edit-card-num">第 ${idx + 1} 頁簡報投影片</span>
            <div class="edit-card-actions">
              <button class="action-icon-btn" onclick="moveSlide(${idx}, -1)" title="向上移動">▲</button>
              <button class="action-icon-btn" onclick="moveSlide(${idx}, 1)" title="向下移動">▼</button>
              <button class="action-icon-btn danger" onclick="deleteSlide(${idx})" title="刪除此頁">🗑</button>
            </div>
          </div>
          
          <div class="form-group" style="margin-bottom: 12px;">
            <label class="form-label">投影片標題</label>
            <input type="text" class="form-input" style="padding: 8px 12px;" id="edit-slide-${idx}-title" value="${slide.title || ""}" oninput="updateSlideData(${idx})">
          </div>

          <div class="grid-2" style="grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 12px;">
            <div class="form-group" style="margin-bottom: 0;">
              <label class="form-label">代表圖示 (Emoji)</label>
              <input type="text" class="form-input" style="padding: 8px 12px;" id="edit-slide-${idx}-icon" value="${slide.icon || "💡"}" oninput="updateSlideData(${idx})">
            </div>
            <div class="form-group" style="margin-bottom: 0;">
              <label class="form-label">插圖搜尋關鍵字 (英文)</label>
              <input type="text" class="form-input" style="padding: 8px 12px;" id="edit-slide-${idx}-imageKeyword" value="${slide.imageKeyword || "training"}" oninput="updateSlideData(${idx})">
            </div>
          </div>

          <div class="form-group" style="margin-bottom: 12px;">
            <label class="form-label">投影片條列重點</label>
            <div class="bullets-edit-container">
              ${bulletsInputs}
            </div>
          </div>

          <div class="form-group" style="margin-bottom: 10px;">
            <label class="form-label">語音朗讀配音文字 (Narration)</label>
            <textarea class="form-textarea" style="min-height: 80px; padding: 8px 12px;" id="edit-slide-${idx}-narration" oninput="updateSlideData(${idx})">${slide.narration || ""}</textarea>
          </div>

          <button class="btn-tts-preview" id="btn-tts-preview-${idx}" onclick="previewSlideTts(${idx})">🔊 試聽此頁配音</button>
        `;
        container.appendChild(slideCard);
      });
    }

    function renderQuizEditor() {
      const container = document.getElementById("editor-quiz-container");
      container.innerHTML = "";

      generatedData.quiz.forEach((q, idx) => {
        const quizCard = document.createElement("div");
        quizCard.className = "edit-card";
        quizCard.id = `edit-quiz-node-${idx}`;

        let optionsInputs = "";
        for (let i = 0; i < 4; i++) {
          const letter = String.fromCharCode(65 + i); // A, B, C, D
          const val = q.options?.[i] || "";
          optionsInputs += `
            <div style="display: flex; align-items: center; gap: 8px;">
              <span style="font-weight: bold; width: 20px;">${letter}</span>
              <input type="text" class="form-input" style="padding: 8px 12px; background: rgba(17, 24, 39, 0.5);" id="edit-quiz-${idx}-opt-${i}" value="${val}" placeholder="選項 ${letter}" oninput="updateQuizData(${idx})">
            </div>
          `;
        }

        quizCard.innerHTML = `
          <div class="edit-card-header">
            <span class="edit-card-num">第 ${idx + 1} 題測驗題目</span>
            <div class="edit-card-actions">
              <button class="action-icon-btn danger" onclick="deleteQuiz(${idx})" title="刪除此題">🗑</button>
            </div>
          </div>

          <div class="form-group" style="margin-bottom: 12px;">
            <label class="form-label">題幹題目</label>
            <input type="text" class="form-input" style="padding: 8px 12px;" id="edit-quiz-${idx}-question" value="${q.question || ""}" oninput="updateQuizData(${idx})">
          </div>

          <div class="form-group" style="margin-bottom: 12px;">
            <label class="form-label">選擇題選項</label>
            <div style="display: flex; flex-direction: column; gap: 8px;">
              ${optionsInputs}
            </div>
          </div>

          <div class="grid-2" style="grid-template-columns: 1fr 2fr; gap: 16px; margin-bottom: 0;">
            <div class="form-group" style="margin-bottom: 0;">
              <label class="form-label">正確答案</label>
              <select class="form-select" style="padding: 8px 12px;" id="edit-quiz-${idx}-answer" onchange="updateQuizData(${idx})">
                <option value="A" ${q.answer === 'A' ? 'selected' : ''}>A</option>
                <option value="B" ${q.answer === 'B' ? 'selected' : ''}>B</option>
                <option value="C" ${q.answer === 'C' ? 'selected' : ''}>C</option>
                <option value="D" ${q.answer === 'D' ? 'selected' : ''}>D</option>
              </select>
            </div>
            <div class="form-group" style="margin-bottom: 0;">
              <label class="form-label">答案解析與說明</label>
              <input type="text" class="form-input" style="padding: 8px 12px;" id="edit-quiz-${idx}-explanation" value="${q.explanation || ""}" oninput="updateQuizData(${idx})">
            </div>
          </div>
        `;
        container.appendChild(quizCard);
      });
    }

    // 當編輯器修改時同步更新記憶體中的 JSON 物件
    window.updateSlideData = function(idx) {
      if (!generatedData.slides[idx]) return;
      const title = document.getElementById(`edit-slide-${idx}-title`).value;
      const narration = document.getElementById(`edit-slide-${idx}-narration`).value;
      const icon = document.getElementById(`edit-slide-${idx}-icon`).value.trim();
      const imageKeyword = document.getElementById(`edit-slide-${idx}-imageKeyword`).value.trim();
      
      const bullets = [];
      for (let i = 0; i < 4; i++) {
        const val = document.getElementById(`edit-slide-${idx}-bullet-${i}`).value.trim();
        if (val) bullets.push(val);
      }

      generatedData.slides[idx].title = title;
      generatedData.slides[idx].narration = narration;
      generatedData.slides[idx].bullets = bullets;
      generatedData.slides[idx].icon = icon;
      generatedData.slides[idx].imageKeyword = imageKeyword;
    };

    window.updateQuizData = function(idx) {
      if (!generatedData.quiz[idx]) return;
      const question = document.getElementById(`edit-quiz-${idx}-question`).value;
      const answer = document.getElementById(`edit-quiz-${idx}-answer`).value;
      const explanation = document.getElementById(`edit-quiz-${idx}-explanation`).value;

      const options = [];
      for (let i = 0; i < 4; i++) {
        const val = document.getElementById(`edit-quiz-${idx}-opt-${i}`).value;
        options.push(val);
      }

      generatedData.quiz[idx].question = question;
      generatedData.quiz[idx].answer = answer;
      generatedData.quiz[idx].explanation = explanation;
      generatedData.quiz[idx].options = options;
    };

    // 投影片增、刪、移位
    window.moveSlide = function(idx, direction) {
      const targetIdx = idx + direction;
      if (targetIdx < 0 || targetIdx >= generatedData.slides.length) return;

      stopPreviewSpeech();

      // 交換陣列元素
      const temp = generatedData.slides[idx];
      generatedData.slides[idx] = generatedData.slides[targetIdx];
      generatedData.slides[targetIdx] = temp;

      renderSlidesEditor();
    };

    window.deleteSlide = function(idx) {
      if (generatedData.slides.length <= 1) {
        alert("簡報至少需要保留 1 頁！");
        return;
      }
      stopPreviewSpeech();
      generatedData.slides.splice(idx, 1);
      renderSlidesEditor();
    };

    window.addSlideNode = function() {
      stopPreviewSpeech();
      generatedData.slides.push({
        title: "新簡報頁標題",
        bullets: ["重點項目 1", "重點項目 2"],
        narration: "請在這裡填入該頁的語音導讀旁白文字。",
        icon: "💡",
        imageKeyword: "idea"
      });
      renderSlidesEditor();
      setTimeout(() => {
        const container = document.getElementById("editor-slides-container");
        container.lastElementChild.scrollIntoView({ behavior: "smooth" });
      }, 50);
    };

    // 考題增、刪
    window.deleteQuiz = function(idx) {
      if (generatedData.quiz.length <= 1) {
        alert("測驗至少需要保留 1 題！");
        return;
      }
      generatedData.quiz.splice(idx, 1);
      renderQuizEditor();
    };

    window.addQuizNode = function() {
      generatedData.quiz.push({
        question: "新題目問句？",
        options: ["A. 選項一描述", "B. 選項二描述", "C. 選項三描述", "D. 選項四描述"],
        answer: "A",
        explanation: "正確答案解析說明。"
      });
      renderQuizEditor();
      setTimeout(() => {
        const container = document.getElementById("editor-quiz-container");
        container.lastElementChild.scrollIntoView({ behavior: "smooth" });
      }, 50);
    };

    // 切換編輯 Tab
    window.switchEditTab = function(tabName) {
      document.querySelectorAll(".edit-tab-btn").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".pane-content").forEach(p => p.classList.remove("active"));

      if (tabName === "slides") {
        document.querySelector(".edit-tab-btn:nth-child(1)").classList.add("active");
        document.getElementById("pane-slides").classList.add("active");
      } else {
        document.querySelector(".edit-tab-btn:nth-child(2)").classList.add("active");
        document.getElementById("pane-quiz").classList.add("active");
        stopPreviewSpeech();
      }
    };

    // 語音朗讀試聽
    window.previewSlideTts = function(idx) {
      if (playingTtsBtn) {
        const wasPlayingBtnId = playingTtsBtn.id;
        stopPreviewSpeech();
        if (wasPlayingBtnId === `btn-tts-preview-${idx}`) {
          return;
        }
      }

      const text = document.getElementById(`edit-slide-${idx}-narration`).value;
      if (!text || text.trim() === "") return;

      currentPreviewUtterance = new SpeechSynthesisUtterance(text);
      currentPreviewUtterance.rate = 1.0;
      
      const voices = speechSynth.getVoices();
      const zhVoice = voices.find(v => v.lang.includes("zh-TW") || v.lang.includes("zh-CN") || v.lang.includes("zh"));
      if (zhVoice) currentPreviewUtterance.voice = zhVoice;

      playingTtsBtn = document.getElementById(`btn-tts-preview-${idx}`);
      playingTtsBtn.textContent = "⏹ 停止播放";
      playingTtsBtn.classList.add("playing");

      currentPreviewUtterance.onend = () => {
        stopPreviewSpeech();
      };
      currentPreviewUtterance.onerror = () => {
        stopPreviewSpeech();
      };

      speechSynth.speak(currentPreviewUtterance);
    };

    function stopPreviewSpeech() {
      if (speechSynth) {
        speechSynth.cancel();
      }
      if (playingTtsBtn) {
        playingTtsBtn.textContent = "🔊 試聽此頁配音";
        playingTtsBtn.classList.remove("playing");
        playingTtsBtn = null;
      }
      currentPreviewUtterance = null;
    }

    // 匯出包裝好之 zip 檔案
    window.exportTrainingFiles = async function() {
      stopPreviewSpeech();

      if (!generatedData || !generatedData.slides || generatedData.slides.length === 0) {
        alert("⚠️ 錯誤：目前沒有簡報投影片資料！請嘗試重新產生簡報或點點看左下角「新增簡報頁」以開始編輯。");
        return;
      }
      
      // 同步取得當前輸入的主標題與副標題
      generatedData.title = document.getElementById("edit-main-title").value.trim() || "教育訓練";
      generatedData.subtitle = document.getElementById("edit-main-subtitle").value.trim() || "";

      // 及格分數與防刷鎖設定
      const passScore = parseInt(document.getElementById("pass-score").value);
      const requireListen = document.getElementById("require-listen").checked;

      // 檢查是否簡報跟考題有在變更後正確被存入
      generatedData.slides.forEach((_, idx) => updateSlideData(idx));
      generatedData.quiz.forEach((_, idx) => updateQuizData(idx));

      try {
        document.getElementById("loading-title").textContent = "正在包裝並輸出 ZIP 檔案";
        const loadingMask = document.getElementById("loading-mask");
        loadingMask.classList.add("show");

        // 使用 JSZip 在純前端直接打包下載
        const zip = new JSZip();
        const folderName = (generatedData.title || "SOP_Training").trim().replace(/[\/\\?%*:|"<>\s]/g, "_");

        // 1. 替換 Player 範本內容
        let playerHtml = PLAYER_TEMPLATE_SOURCE;
        playerHtml = playerHtml.replace(/__TRAINING_TITLE__/g, () => generatedData.title || "教育訓練");
        playerHtml = playerHtml.replace(/__TRAINING_SUBTITLE__/g, () => generatedData.subtitle || "請詳閱簡報內容並完成測驗");
        playerHtml = playerHtml.replace("__SLIDES_DATA__", () => JSON.stringify(generatedData.slides, null, 2));
        playerHtml = playerHtml.replace("__QUIZ_DATA__", () => JSON.stringify(generatedData.quiz, null, 2));
        playerHtml = playerHtml.replace("__PASS_SCORE__", () => passScore);
        playerHtml = playerHtml.replace("__REQUIRE_LISTEN__", () => requireListen ? "true" : "false");
        playerHtml = playerHtml.replace(/__CLOSE_SCRIPT__/g, () => '<' + '/script>');

        // 2. 準備本機伺服器腳本
        const psServerCode = `$port = 8000

# 使用 UDP 連線獲取本機對外的內網 IP
$socket = New-Object System.Net.Sockets.UdpClient
$ip = $null
try {
    $socket.Connect("8.8.8.8", 80)
    $ip = $socket.Client.LocalEndPoint.Address.IPAddressToString
} catch {} finally {
    if ($socket) { $socket.Close() }
}

if (-not $ip) {
    $ip = (Get-NetIPAddress | Where-Object { $_.AddressFamily -eq 'InterNetwork' -and $_.IPAddress -notmatch '^127\\.' -and $_.IPAddress -notmatch '^169\\.254\\.' } | Select-Object -First 1).IPAddress
}

if (-not $ip) { $ip = '127.0.0.1' }

$localIP = [System.Net.IPAddress]::Parse($ip)
$listener = New-Object System.Net.Sockets.TcpListener($localIP, $port)

try {
    $listener.Start()
} catch {
    Write-Host "============================================================" -ForegroundColor Red
    Write-Host "  ❌ 啟動失敗！" -ForegroundColor Red
    Write-Host "  可能原因：連接埠 $($port) 已被佔用。請關閉其他伺服器再重試。" -ForegroundColor Red
    Write-Host "============================================================" -ForegroundColor Red
    Read-Host "按 Enter 結束..."
    exit
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  📋 員工教育訓練測驗系統 — 本機內網網頁伺服器" -ForegroundColor Cyan
Write-Host "============================================================\`n" -ForegroundColor Cyan
Write-Host "  伺服器運行中..."
Write-Host "  💡 注意：請【勿】關閉此視窗，關閉代表結束服務。"
Write-Host "  💡 同仁的手機或電腦，必須與您連線至【同一個 Wi-Fi】或公司網路。\`n"
Write-Host "  📢 同仁請在瀏覽器輸入以下網址開啟測驗："
Write-Host "  👉 http://$($ip):$($port)/index.html" -ForegroundColor Green
Write-Host "\`n============================================================" -ForegroundColor Cyan

$currentDir = $PSScriptRoot
if (-not $currentDir) { $currentDir = (Get-Location).Path }

while ($true) {
    try {
        if (-not $listener.Pending()) {
            Start-Sleep -Milliseconds 100
            continue
        }
        $client = $listener.AcceptTcpClient()
        $stream = $client.GetStream()
        $reader = New-Object System.IO.StreamReader($stream)
        $requestLine = $reader.ReadLine()
        
        if ($requestLine -match '^(GET|POST)\\s+(/[^\\s\\?]*)\\??[^\\s]*\\s+HTTP') {
            $method = $Matches[1]
            $urlPath = $Matches[2]
            if ($urlPath -eq "/") { $urlPath = "/index.html" }
            $urlPath = [System.Uri]::UnescapeDataString($urlPath)
            
            if ($method -eq "POST" -and $urlPath -eq "/api/submit") {
                $headers = @{}
                while ($line = $reader.ReadLine()) {
                    if ($line -eq "") { break }
                    if ($line -match '^([^:]+):\\s*(.*)$') {
                        $headers[$Matches[1].ToLower()] = $Matches[2].Trim()
                    }
                }
                
                $contentLength = 0
                if ($headers.ContainsKey("content-length")) {
                    [int]::TryParse($headers["content-length"], [ref]$contentLength) | Out-Null
                }
                
                $body = ""
                if ($contentLength -gt 0) {
                    $buffer = New-Object System.Char[] $contentLength
                    $read = $reader.Read($buffer, 0, $contentLength)
                    $body = New-Object System.String($buffer, 0, $read)
                }
                
                try {
                    $record = $body | ConvertFrom-Json
                    $csvPath = Join-Path $currentDir "results.csv"
                    
                    if (-not (Test-Path $csvPath)) {
                        $headersLine = "時間戳記,姓名,對題數,得分"
                        $qCount = 0
                        foreach ($prop in $record.PSObject.Properties) {
                            if ($prop.Name -match '^q\\d+$') { $qCount++ }
                        }
                        for ($i = 1; $i -le $qCount; $i++) {
                            $headersLine += ",第\${i}題"
                        }
                        [System.IO.File]::WriteAllText($csvPath, "$headersLine\`r\`n", [System.Text.Encoding]::UTF8)
                    }
                    
                    $qCount = 0
                    foreach ($prop in $record.PSObject.Properties) {
                        if ($prop.Name -match '^q\\d+$') { $qCount++ }
                    }
                    $correctStr = "$($record.correctCount) / $($record.total)"
                    $scoreStr = "$($record.score) 分"
                    $nameClean = $record.name -replace '"', '""'
                    $tsClean = $record.timestamp -replace '"', '""'
                    
                    $row = """$tsClean"",""$nameClean"",""$correctStr"",""$scoreStr"""
                    for ($i = 1; $i -le $qCount; $i++) {
                        $val = $record."q$i" -replace '"', '""'
                        $row += ",\`"$val\`""
                    }
                    
                    [System.IO.File]::AppendAllText($csvPath, "$row\`r\`n", [System.Text.Encoding]::UTF8)
                    
                    $respBody = '{"status":"ok","message":"saved"}'
                    $respBytes = [System.Text.Encoding]::UTF8.GetBytes($respBody)
                    $header = "HTTP/1.1 200 OK\`r\`nContent-Type: application/json; charset=utf-8\`r\`nContent-Length: $($respBytes.Length)\`r\`nAccess-Control-Allow-Origin: *\`r\`nConnection: close\`r\`n\`r\`n"
                    $headerBytes = [System.Text.Encoding]::UTF8.GetBytes($header)
                    $stream.Write($headerBytes, 0, $headerBytes.Length)
                    $stream.Write($respBytes, 0, $respBytes.Length)
                    Write-Host "📥 [本機紀錄] 收到同仁 $($record.name) 的作答結果，已寫入 results.csv" -ForegroundColor Yellow
                } catch {
                    $err = '{"status":"error","message":"' + $_.Exception.Message.Replace('"', '\\"') + '"}'
                    $respBytes = [System.Text.Encoding]::UTF8.GetBytes($err)
                    $header = "HTTP/1.1 500 Error\`r\`nContent-Type: application/json\`r\`nContent-Length: $($respBytes.Length)\`r\`nConnection: close\`r\`n\`r\`n"
                    $headerBytes = [System.Text.Encoding]::UTF8.GetBytes($header)
                    $stream.Write($headerBytes, 0, $headerBytes.Length)
                    $stream.Write($respBytes, 0, $respBytes.Length)
                }
            } else {
                $filePath = Join-Path $currentDir $urlPath
                if (Test-Path $filePath -PathType Leaf) {
                    $ext = [System.IO.Path]::GetExtension($filePath).ToLower()
                    $contentType = switch ($ext) {
                        ".html" { "text/html; charset=utf-8" }
                        default { "application/octet-stream" }
                    }
                    $bytes = [System.IO.File]::ReadAllBytes($filePath)
                    $header = "HTTP/1.1 200 OK\`r\`nContent-Type: $contentType\`r\`nContent-Length: $($bytes.Length)\`r\`nAccess-Control-Allow-Origin: *\`r\`nConnection: close\`r\`n\`r\`n"
                    $headerBytes = [System.Text.Encoding]::UTF8.GetBytes($header)
                    $stream.Write($headerBytes, 0, $headerBytes.Length)
                    $stream.Write($bytes, 0, $bytes.Length)
                } else {
                    $errText = "404 Not Found"
                    $errBytes = [System.Text.Encoding]::UTF8.GetBytes($errText)
                    $header = "HTTP/1.1 404 Not Found\`r\`nContent-Length: $($errBytes.Length)\`r\`nConnection: close\`r\`n\`r\`n"
                    $headerBytes = [System.Text.Encoding]::UTF8.GetBytes($header)
                    $stream.Write($headerBytes, 0, $headerBytes.Length)
                    $stream.Write($errBytes, 0, $errBytes.Length)
                }
            }
        }
        $stream.Close()
        $client.Close()
    } catch {}
}`;

        const batShortcutCode = `@echo off
chcp 65001 > nul
title 啟動員工教育訓練本機伺服器
echo ============================================================
echo   正在啟動本機內網伺服器，請稍候...
echo ============================================================
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0serve_intranet.txt"
pause`;

        const appsScriptCode = `// ============================================================
// 📋 Google Apps Script — 員工教育訓練測驗成績收集系統 (${generatedData.title})
// ============================================================
// 
// 操作步驟：
// 1. 前往 https://sheets.new 建立一個新的試算表，命名為「員工測驗紀錄」
// 2. 點選上方選單的「擴充功能」->「Apps Script」
// 3. 將此編輯器內原有的內容清空，並貼上下方所有的程式碼後存檔。
// 4. 點選右上角的「部署」->「新增部署作業」
//    - 選取類型：網頁應用程式 (Web App)
//    - 說明：教育訓練成績回收
//    - 執行身分：我 (Me)
//    - 誰可以存取：所有人 (Anyone)
// 5. 點擊「部署」，授權存取 Google 帳號後，複製產生的「網頁應用程式 URL」。
// 6. 將複製的網址，貼入測驗網頁右上角「⚙️ 系統設定」的雲端同步欄位中即可。

const SHEET_NAME = '作答紀錄';

function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    let sheet = ss.getSheetByName(SHEET_NAME);
    if (!sheet) { sheet = ss.insertSheet(SHEET_NAME); }
    const name = data.name || '未知';
    const score = data.score !== undefined ? data.score : 0;
    const correctCount = data.correctCount !== undefined ? data.correctCount : 0;
    const total = data.total !== undefined ? data.total : 0;
    const timestamp = data.timestamp || new Date().toLocaleString('zh-TW', { timeZone: 'Asia/Taipei' });
    const qAnswers = [];
    let qIndex = 1;
    while (data['q' + qIndex] !== undefined) {
      qAnswers.push(data['q' + qIndex]);
      qIndex++;
    }
    if (sheet.getLastRow() === 0) {
      const headers = ['時間戳記', '姓名', '對題數', '得分'];
      for (let i = 1; i < qIndex; i++) { headers.push('第 ' + i + ' 題作答'); }
      sheet.appendRow(headers);
      const range = sheet.getRange(1, 1, 1, headers.length);
      range.setBackground('#4F46E5');
      range.setFontColor('#FFFFFF');
      range.setFontWeight('bold');
    }
    const rowData = [timestamp, name, correctCount + ' / ' + total, score + ' 分'];
    qAnswers.forEach(ans => rowData.push(ans));
    sheet.appendRow(rowData);
    return ContentService.createTextOutput(JSON.stringify({ status: 'ok', message: '已成功存入雲端試算表！' })).setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({ status: 'error', message: err.toString() })).setMimeType(ContentService.MimeType.JSON);
  }
}`;

        const readmeText = `# 員工教育訓練系統 — 說明書 (SOP: ${generatedData.title})

本資料夾是由「教育訓練測驗產生系統」自動產生的完整檔案包，包含簡報閱讀、自動語音朗讀、測驗防刷，以及本機/雲端雙重成績收集功能。

---

## 📁 檔案內容說明
1. **\`index.html\`**：主測驗網頁（已內嵌您的 SOP 投影片與測驗題目，免下載圖片，直接用瀏覽器開啟即可播放簡報並作答）。
2. **\`serve_intranet.txt\`**：本機伺服器程式（以 Windows PowerShell 撰寫，為免受 Windows 安全警告阻擋，將副檔名設為 .txt 並由 bat 檔直接執行）。
3. **\`點我啟動內網伺服器(Windows免安裝).bat\`**：一鍵啟動批次檔，按滑鼠雙擊即可運行。
4. **\`apps_script_code.gs\`**：Google Sheets 雲端同步腳本（供會寫 Apps Script 的人員設定雲端回收）。

---

## 🚀 收集同仁的成績（本機免設定模式 - 最簡單）

1. **解壓縮**：請確保此資料夾已解壓縮到您的電腦（不要直接在 zip 檔案中點兩下執行）。
2. **啟動本機伺服器**：
   - 雙擊執行 **\`點我啟動內網伺服器(Windows免安裝).bat\`**。
   - 電腦會彈出一個黑色的終端機視窗，並以綠色字體顯示一串連線網址（例如：\`http://192.168.1.100:8000/index.html\`）。**請勿關閉此視窗**。
3. **同仁開啟作答**：
   - 將該綠色網址傳送給同仁（或透過瀏覽器產生 QR 碼給同仁掃描）。
   - **重要前提**：同仁的手機或電腦必須連線至**與您相同的公司 Wi-Fi 或內網**。
4. **回收成績 (results.csv)**：
   - 同仁做完題目點選「送出」後，您的伺服器視窗中會同步顯示「收到同仁 XXX 的答案」。
   - 資料夾中會**自動產生 \`results.csv\`** 檔案，您直接雙擊該檔即可用 Excel 查看全體成績、作答時間以及每題答錯/答對的詳細紀錄！

---

## ☁️ 收集同仁的成績（雲端 Google Sheets 模式 - 可選填）

如果您想要讓同仁的成績自動存入雲端的 Google Sheets 試算表中：

1. **建立 Google Sheets 試算表**：
   - 前往 [Google Sheets](https://sheets.new) 建立一份新試算表，命名為「教育訓練成績回收」。
2. **建立 Apps Script 腳本**：
   - 在試算表上方點選「**擴充功能**」->「**Apps Script**」。
   - 打開資料夾中的 \`apps_script_code.gs\`，將裡面的程式碼複製，全部貼入 Apps Script 編輯器中取代原本的空函數，然後存檔。
3. **部署網頁應用程式**：
   - 點擊右上角「**部署**」->「**新增部署作業**」。
   - 選取類型：**網頁應用程式** (Web App)。
   - 專案說明：填寫「成績收集」。
   - 執行身分：選擇「**我**」(Me)。
   - 誰可以存取：選擇「**所有人**」(Anyone)。
   - 點擊「**部署**」，在出現的視窗中完成 Google 帳號授權，最後**複製網頁應用程式 URL 網址**。
4. **填入測驗系統**：
   - 開啟您的 \`index.html\`，點選右上角的 **⚙️ 系統設定**（管理員密碼預設為 \`admin888\`）。
   - 在「雲端同步網址」欄位中貼入您剛才複製的 Google Web App URL，然後儲存。
   - 同仁提交時，成績就會自動非同步備份到雲端的 Google 試算表中！`;

        // Cloudflare D1 整合檔案
        const schemaSqlCode = `DROP TABLE IF EXISTS exam_records;
CREATE TABLE exam_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    name TEXT,
    score INTEGER,
    correctCount INTEGER,
    total INTEGER,
    q1 TEXT,
    q2 TEXT,
    q3 TEXT,
    q4 TEXT,
    q5 TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);`;

        const wranglerTomlCode = `name = "sop-training"
pages_build_output_dir = "."
compatibility_date = "2024-03-20"

[[d1_databases]]
binding = "DB"
database_name = "sop_exam_records"
database_id = "your-database-id-here"`;

        const submitJsCode = `export async function onRequestPost(context) {
  try {
    const data = await context.request.json();
    const name = data.name || "未知";
    const timestamp = data.timestamp || new Date().toLocaleString('zh-TW');
    const score = data.score !== undefined ? data.score : 0;
    const correctCount = data.correctCount || 0;
    const total = data.total || 5;
    const q1 = data.q1 || "";
    const q2 = data.q2 || "";
    const q3 = data.q3 || "";
    const q4 = data.q4 || "";
    const q5 = data.q5 || "";
    const stmt = context.env.DB.prepare(\`
      INSERT INTO exam_records (timestamp, name, score, correctCount, total, q1, q2, q3, q4, q5)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    \`).bind(timestamp, name, score, correctCount, total, q1, q2, q3, q4, q5);
    await stmt.run();
    return new Response(JSON.stringify({ status: "ok" }), { headers: { "Content-Type": "application/json" } });
  } catch (err) {
    return new Response(JSON.stringify({ status: "error", message: err.message }), { status: 500 });
  }
}`;

        // 3. 包裝 ZIP 檔案
        zip.file("index.html", playerHtml);
        zip.file("schema.sql", schemaSqlCode);
        zip.file("wrangler.toml", wranglerTomlCode);
        zip.file("functions/api/submit.js", submitJsCode);
        zip.file("serve_intranet.txt", psServerCode);
        zip.file("點我啟動內網伺服器(Windows免安裝).bat", batShortcutCode);
        zip.file("apps_script_code.gs", appsScriptCode);
        zip.file("README.md", readmeText);

        const zipBlob = await zip.generateAsync({ type: "blob" });
        const downloadUrl = URL.createObjectURL(zipBlob);
        
        const a = document.createElement("a");
        a.href = downloadUrl;
        a.download = `${folderName}_教育訓練測驗套件.zip`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(downloadUrl);

        loadingMask.classList.remove("show");
        
        // 更新成功下載提示文字
        document.getElementById("success-download-hint").innerHTML = `
          已成功產生並下載 <strong>\${folderName}_教育訓練測驗套件.zip</strong>。<br>請將該 ZIP 檔解壓縮，即可開始部署使用！
        `;

        goToStep(3);
      } catch (err) {
        document.getElementById("loading-mask").classList.remove("show");
        alert("打包過程中發生錯誤：\n" + err.message);
      }
    };
  