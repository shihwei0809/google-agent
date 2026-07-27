# 程式碼備份與修改紀錄: player_template.js

本文件為 `player_template.js` 的程式碼備份，便於後續版本比對與修改紀錄追蹤。

## 原始程式碼

```javascript
const PLAYER_TEMPLATE = `<!DOCTYPE html>
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

    /* STEP PROGRESS */
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

    .step-item.active {
      color: var(--text);
    }

    .step-item.done {
      color: var(--success);
    }

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

    .step-line.active {
      background: var(--primary);
    }

    /* MAIN CONTENT */
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

    .section-title {
      font-size: 1.45rem;
      font-weight: 700;
      margin-bottom: 8px;
    }

    .section-desc {
      color: var(--text-muted);
      font-size: 0.9rem;
      margin-bottom: 24px;
    }

    /* ── PRESENTATION PLAYER ── */
    .player-outer {
      border: 1px solid var(--border);
      border-radius: 16px;
      overflow: hidden;
      margin-bottom: 20px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }

    .player-screen {
      aspect-ratio: 16 / 9;
      background: #06090f;
      position: relative;
      overflow: hidden;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 40px;
    }

    /* Slide Card Style */
    .slide-card {
      width: 100%;
      height: 100%;
      display: flex;
      flex-direction: column;
      justify-content: center;
      opacity: 0;
      transform: translateY(15px);
      transition: opacity 0.5s ease, transform 0.5s ease;
      position: absolute;
      padding: 48px;
      pointer-events: none;
    }

    .slide-card.active {
      opacity: 1;
      transform: translateY(0);
      pointer-events: auto;
      position: relative;
    }

    .slide-inner {
      max-width: 90%;
      margin: 0 auto;
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

    .slide-bullets {
      list-style: none;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }

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

    @keyframes slideInBullet {
      to {
        opacity: 1;
        transform: translateX(0);
      }
    }

    .slide-bullets li::before {
      content: "✦";
      color: var(--primary);
      font-size: 1.2rem;
      flex-shrink: 0;
    }

    /* Player Overlay */
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

    .player-overlay.gone {
      opacity: 0;
      pointer-events: none;
    }

    .overlay-box {
      text-align: center;
      background: rgba(14, 22, 38, 0.8);
      border: 1px solid var(--border);
      border-radius: 20px;
      padding: 36px;
      max-width: 360px;
    }

    .overlay-icon {
      font-size: 48px;
      margin-bottom: 16px;
    }

    .overlay-title {
      font-size: 1.25rem;
      font-weight: 700;
      margin-bottom: 8px;
    }

    .overlay-desc {
      font-size: 0.85rem;
      color: var(--text-muted);
      margin-bottom: 24px;
      line-height: 1.6;
    }

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

    .btn-start:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(99,102,241,0.6);
    }

    /* Player Controls */
    .player-controls {
      background: #0a0f1b;
      border-top: 1px solid var(--border);
      padding: 14px 20px;
      display: flex;
      align-items: center;
      gap: 16px;
      position: relative;
    }

    .progress-bar-container {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 3px;
      background: rgba(255,255,255,0.05);
    }

    .progress-bar-fill {
      height: 100%;
      background: linear-gradient(to right, var(--primary), #8b5cf6);
      width: 0%;
      transition: width 0.3s ease;
    }

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

    .control-btn:hover {
      background: rgba(255, 255, 255, 0.15);
      border-color: rgba(255,255,255,0.2);
    }

    .control-btn:disabled {
      opacity: 0.25;
      cursor: not-allowed;
    }

    .btn-play-voice {
      width: 44px;
      height: 44px;
      background: rgba(99, 102, 241, 0.1);
      border-color: var(--primary);
      color: #a5b4fc;
    }

    .btn-play-voice.playing {
      background: var(--primary);
      color: #fff;
      animation: voicePulse 1.5s infinite;
    }

    @keyframes voicePulse {
      0% { box-shadow: 0 0 0 0 rgba(99, 102, 241, 0.4); }
      70% { box-shadow: 0 0 0 8px rgba(99, 102, 241, 0); }
      100% { box-shadow: 0 0 0 0 rgba(99, 102, 241, 0); }
    }

    .slide-indicator {
      font-size: 0.8rem;
      color: var(--text-muted);
      min-width: 50px;
      text-align: center;
    }

    .slide-label-text {
      flex: 1;
      font-size: 0.85rem;
      color: var(--text-muted);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .speed-select {
      background: rgba(255,255,255,0.05);
      border: 1px solid var(--border);
      color: var(--text-muted);
      border-radius: 6px;
      padding: 4px 8px;
      font-size: 0.75rem;
      outline: none;
      cursor: pointer;
    }

    .speed-select option {
      background: #0f172a;
      color: var(--text);
    }

    .btn-toggle-auto {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--border);
      color: var(--text-muted);
      padding: 6px 12px;
      border-radius: 6px;
      font-size: 0.75rem;
      cursor: pointer;
      transition: all 0.2s;
      white-space: nowrap;
    }

    .btn-toggle-auto.active {
      background: rgba(16, 185, 129, 0.15);
      border-color: var(--success);
      color: var(--success);
    }

    .info-banner {
      background: rgba(99, 102, 241, 0.06);
      border: 1px solid rgba(99, 102, 241, 0.15);
      border-radius: 12px;
      padding: 12px 18px;
      display: flex;
      align-items: flex-start;
      gap: 12px;
      font-size: 0.85rem;
      color: var(--text-muted);
      line-height: 1.6;
      margin-bottom: 24px;
    }

    .info-banner strong {
      color: var(--text);
    }

    .btn-action-container {
      text-align: center;
      margin-top: 16px;
    }

    .btn-action {
      background: linear-gradient(135deg, var(--primary), #8b5cf6);
      color: #fff;
      border: none;
      border-radius: 50px;
      padding: 14px 44px;
      font-size: 1rem;
      font-weight: 700;
      cursor: pointer;
      box-shadow: 0 4px 20px rgba(99,102,241,0.3);
      transition: all 0.2s;
    }

    .btn-action:hover:not(:disabled) {
      transform: translateY(-2px);
      box-shadow: 0 8px 25px rgba(99,102,241,0.5);
    }

    .btn-action:disabled {
      opacity: 0.35;
      cursor: not-allowed;
      box-shadow: none;
    }

    .btn-action-hint {
      font-size: 0.75rem;
      color: var(--text-muted);
      margin-top: 8px;
    }

    /* ── QUIZ SECTION ── */
    #quiz-section {
      opacity: 0.3;
      pointer-events: none;
      filter: blur(1.5px);
      transition: all 0.6s ease;
    }

    #quiz-section.unlocked {
      opacity: 1;
      pointer-events: auto;
      filter: none;
    }

    .quiz-identity-card {
      background: linear-gradient(135deg, rgba(99, 102, 241, 0.08) 0%, rgba(139, 92, 246, 0.08) 100%);
      border: 1px solid rgba(99, 102, 241, 0.2);
      border-radius: 14px;
      padding: 24px;
      margin-bottom: 24px;
    }

    .quiz-identity-card h3 {
      font-size: 1rem;
      font-weight: 600;
      margin-bottom: 6px;
    }

    .quiz-identity-card p {
      font-size: 0.8rem;
      color: var(--text-muted);
      margin-bottom: 16px;
    }

    .input-wrapper {
      position: relative;
      max-width: 320px;
    }

    .input-icon {
      position: absolute;
      left: 14px;
      top: 50%;
      transform: translateY(-50%);
      font-size: 16px;
      pointer-events: none;
    }

    .input-name {
      width: 100%;
      background: var(--surface);
      border: 1.5px solid var(--border);
      border-radius: 10px;
      padding: 12px 14px 12px 42px;
      color: var(--text);
      font-family: inherit;
      outline: none;
      font-size: 0.9rem;
      transition: all 0.2s;
    }

    .input-name:focus {
      border-color: var(--primary);
      box-shadow: 0 0 0 3px rgba(99,102,241,0.2);
    }

    .quiz-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 20px;
      border-bottom: 1px solid var(--border);
      padding-bottom: 12px;
    }

    .quiz-progress-badge {
      background: rgba(99,102,241,0.15);
      border: 1px solid var(--border-focus);
      color: #a5b4fc;
      font-size: 0.75rem;
      font-weight: 600;
      padding: 4px 12px;
      border-radius: 100px;
    }

    .question-card {
      background: rgba(255, 255, 255, 0.015);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 20px;
      margin-bottom: 16px;
      transition: border-color 0.3s;
    }

    .question-card.answered {
      border-color: rgba(16, 185, 129, 0.3);
    }

    .question-num {
      font-size: 0.7rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--primary);
      margin-bottom: 6px;
    }

    .question-title {
      font-size: 1rem;
      font-weight: 600;
      margin-bottom: 16px;
      color: var(--text);
    }

    .options-list {
      display: flex;
      flex-direction: column;
      gap: 10px;
    }

    .option-item {
      display: flex;
      align-items: center;
      gap: 12px;
      background: rgba(255,255,255,0.01);
      border: 1.5px solid var(--border);
      border-radius: 10px;
      padding: 12px 16px;
      cursor: pointer;
      font-size: 0.9rem;
      transition: all 0.2s;
    }

    .option-item:hover {
      border-color: rgba(99,102,241,0.4);
      background: rgba(99,102,241,0.05);
    }

    .option-item input[type="radio"] {
      display: none;
    }

    .option-dot {
      width: 18px;
      height: 18px;
      border-radius: 50%;
      border: 2px solid var(--text-muted);
      position: relative;
      flex-shrink: 0;
      transition: all 0.2s;
    }

    .option-item input[type="radio"]:checked ~ .option-dot {
      border-color: var(--primary);
      background: var(--primary);
    }

    .option-item input[type="radio"]:checked ~ .option-dot::after {
      content: "";
      position: absolute;
      inset: 4px;
      background: #fff;
      border-radius: 50%;
    }

    .btn-submit-quiz {
      background: linear-gradient(135deg, var(--success), #059669);
      color: #fff;
      border: none;
      border-radius: 50px;
      padding: 14px 48px;
      font-size: 1rem;
      font-weight: 700;
      cursor: pointer;
      box-shadow: 0 4px 20px var(--success-glow);
      transition: all 0.2s;
    }

    .btn-submit-quiz:hover:not(:disabled) {
      transform: translateY(-2px);
      box-shadow: 0 8px 25px rgba(16, 185, 129, 0.4);
    }

    .btn-submit-quiz:disabled {
      opacity: 0.35;
      cursor: not-allowed;
    }

    /* ── RESULT MODAL ── */
    .modal-mask {
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.85);
      backdrop-filter: blur(8px);
      z-index: 1000;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }

    .modal-mask.show {
      display: flex;
    }

    .result-box {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 24px;
      width: 100%;
      max-width: 440px;
      padding: 40px 32px;
      text-align: center;
      box-shadow: 0 15px 40px rgba(0,0,0,0.5);
      animation: modalPop 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
    }

    @keyframes modalPop {
      from { transform: scale(0.8); opacity: 0; }
      to { transform: scale(1); opacity: 1; }
    }

    .result-icon {
      font-size: 64px;
      margin-bottom: 20px;
      display: inline-block;
    }

    .result-title {
      font-size: 1.5rem;
      font-weight: 700;
      margin-bottom: 12px;
    }

    .result-score {
      font-size: 3rem;
      font-weight: 800;
      margin-bottom: 12px;
      background: linear-gradient(135deg, var(--primary), #8b5cf6);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    .result-details {
      color: var(--text-muted);
      font-size: 0.9rem;
      line-height: 1.6;
      margin-bottom: 28px;
    }

    .modal-btn {
      background: var(--primary);
      color: #fff;
      border: none;
      border-radius: 10px;
      padding: 12px 28px;
      font-size: 0.95rem;
      font-weight: 600;
      cursor: pointer;
      width: 100%;
      transition: all 0.2s;
    }

    .modal-btn:hover {
      background: var(--primary-hover);
    }

    /* ── SETTINGS MODAL ── */
    .cfg-box {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 20px;
      width: 100%;
      max-width: 500px;
      padding: 28px;
      text-align: left;
      box-shadow: 0 15px 40px rgba(0,0,0,0.5);
      animation: modalPop 0.3s ease;
    }

    .cfg-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
      border-bottom: 1px solid var(--border);
      padding-bottom: 12px;
    }

    .cfg-header h3 {
      font-size: 1.15rem;
      font-weight: 700;
    }

    .cfg-close {
      background: none;
      border: none;
      color: var(--text-muted);
      font-size: 24px;
      cursor: pointer;
      line-height: 1;
    }

    .cfg-body {
      display: flex;
      flex-direction: column;
      gap: 16px;
    }

    .cfg-group {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    .cfg-label {
      font-size: 0.85rem;
      font-weight: 600;
      color: var(--text);
    }

    .cfg-input {
      background: var(--surface-hover);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 10px 12px;
      color: var(--text);
      font-size: 0.85rem;
      outline: none;
    }

    .cfg-input:focus {
      border-color: var(--primary);
    }

    .cfg-help {
      font-size: 0.75rem;
      color: var(--text-muted);
      line-height: 1.5;
    }

    .cfg-actions {
      display: flex;
      justify-content: flex-end;
      gap: 12px;
      margin-top: 12px;
    }

    .cfg-btn {
      padding: 10px 20px;
      border-radius: 8px;
      font-size: 0.85rem;
      font-weight: 600;
      cursor: pointer;
      border: none;
      transition: all 0.2s;
    }

    .cfg-btn.primary {
      background: var(--primary);
      color: #fff;
    }

    .cfg-btn.primary:hover {
      background: var(--primary-hover);
    }

    .cfg-btn.secondary {
      background: rgba(255,255,255,0.05);
      border: 1px solid var(--border);
      color: var(--text);
    }

    .cfg-btn.secondary:hover {
      background: rgba(255,255,255,0.1);
    }

    .records-section {
      border-top: 1px solid var(--border);
      padding-top: 16px;
      margin-top: 8px;
    }

    .records-count {
      font-size: 0.8rem;
      color: var(--text-muted);
      margin-bottom: 10px;
    }

    .records-btn-group {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }

    .records-btn {
      padding: 6px 12px;
      border-radius: 6px;
      font-size: 0.75rem;
      font-weight: 500;
      cursor: pointer;
      border: 1px solid var(--border);
      background: rgba(255,255,255,0.02);
      color: var(--text);
    }

    .records-btn:hover {
      background: rgba(255,255,255,0.08);
    }

    .records-btn.danger {
      border-color: rgba(244, 63, 94, 0.3);
      color: #fda4af;
    }

    .records-btn.danger:hover {
      background: rgba(244, 63, 94, 0.1);
    }

    .records-preview {
      display: none;
      margin-top: 12px;
      max-height: 180px;
      overflow-y: auto;
      background: rgba(0,0,0,0.25);
      border-radius: 8px;
      padding: 10px;
      font-family: monospace;
      font-size: 0.7rem;
      white-space: pre-wrap;
      color: var(--text-muted);
      border: 1px solid var(--border);
    }

    @media (max-width: 640px) {
      main { padding: 0 16px 48px; }
      .section-card { padding: 20px; }
      .slide-card h2 { font-size: 1.5rem; margin-bottom: 16px; }
      .slide-bullets li { font-size: 0.95rem; }
      .player-screen { padding: 20px; }
      .player-controls { flex-wrap: wrap; justify-content: center; }
      .slide-label-text { width: 100%; text-align: center; }
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

  <!-- 步驟進度條 -->
  <div class="step-bar">
    <div class="step-container">
      <div class="step-item active" id="step1">
        <div class="step-num">1</div>
        <span>閱讀簡報</span>
      </div>
      <div class="step-line" id="line1"></div>
      <div class="step-item" id="step2">
        <div class="step-num">2</div>
        <span>填寫姓名</span>
      </div>
      <div class="step-line" id="line2"></div>
      <div class="step-item" id="step3">
        <div class="step-num">3</div>
        <span>填寫測驗</span>
      </div>
    </div>
  </div>

  <main>
    <!-- 簡報播放區區塊 -->
    <section>
      <div class="section-card">
        <div class="badge">📽️ 第一階段</div>
        <h2 class="section-title">閱讀教育訓練簡報</h2>
        <p class="section-desc">請仔細觀看簡報並聆聽語音說明，播畢後下方的測驗挑戰即會解除鎖定。</p>

        <div class="player-outer">
          <div class="player-screen">
            <!-- 啟動覆蓋層 -->
            <div id="player-start-overlay" class="player-overlay" onclick="activatePlayer()">
              <div class="overlay-box">
                <div class="overlay-icon">🔊</div>
                <div class="overlay-title">點擊開始簡報播放</div>
                <div class="overlay-desc">
                  本簡報共計 <strong id="total-slides-hint">0</strong> 頁，內建語音發音。<br>播放時可自由調整語速或暫停。
                </div>
                <button class="btn-start">▶ 開始聆聽簡報</button>
              </div>
            </div>

            <!-- 投影片內容容器 -->
            <div id="slide-stage" style="width:100%; height:100%;"></div>
          </div>

          <!-- 播放器控制列 -->
          <div class="player-controls">
            <!-- 播放進度 -->
            <div class="progress-bar-container">
              <div id="progress-fill" class="progress-bar-fill"></div>
            </div>

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

    <!-- 測驗區區塊 -->
    <section id="quiz-section">
      <!-- 填寫個人資料 -->
      <div class="quiz-identity-card">
        <h3>👤 請填寫您的作答姓名</h3>
        <p>此姓名將與您的作答記錄、得分同步儲存於系統中，請務必填寫真實姓名。</p>
        <div class="input-wrapper">
          <span class="input-icon">✍️</span>
          <input type="text" class="input-name" id="user-name" placeholder="請輸入姓名（例：陳大明）" maxlength="20" oninput="validateForm()">
        </div>
      </div>

      <!-- 測驗題目 -->
      <div class="section-card">
        <div class="badge">📝 第二階段</div>
        <div class="quiz-header">
          <h2 class="section-title">測驗題目</h2>
          <span class="quiz-progress-badge" id="quiz-progress-badge">已作答 0 / 0 題</span>
        </div>
        <p class="section-desc">每題皆為單選題，請根據簡報內容，點選最適當的答案。</p>

        <!-- 題目生成區 -->
        <div id="quiz-container"></div>

        <div class="btn-action-container" style="margin-top: 32px;">
          <button class="btn-submit-quiz" id="btn-submit-quiz" onclick="submitQuiz()" disabled>📤 提交測驗結果</button>
        </div>
      </div>
    </section>
  </main>

  <!-- 測驗結果彈窗 -->
  <div id="result-modal" class="modal-mask" onclick="closeResultModal(event)">
    <div class="result-box">
      <span class="result-icon" id="res-icon">🎉</span>
      <div class="result-title" id="res-title">恭喜通過測驗！</div>
      <div class="result-score" id="res-score">100 分</div>
      <div class="result-details" id="res-details">
        答對題數：5 / 5 題<br>
        您的成績已成功上傳至系統。
      </div>
      <button class="modal-btn" onclick="hideResultModal()">確定</button>
    </div>
  </div>

  <!-- ⚙️ 系統設定彈窗 -->
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
    // ════════════════════════════════════════
    //  嵌入的簡報與考題資料 (由產生器填入)
    // ════════════════════════════════════════
    const SLIDES = __SLIDES_DATA__;
    const QUIZ = __QUIZ_DATA__;
    const PASS_SCORE = __PASS_SCORE__;
    const REQUIRE_LISTEN = __REQUIRE_LISTEN__;

    // ════════════════════════════════════════
    //  播放器狀態與邏輯
    // ════════════════════════════════════════
    let curSlideIdx = 0;
    let isVoicePlaying = false;
    let isAutoAdvance = true;
    let isActivated = false;
    let speechSynth = window.speechSynthesis;
    let currentUtterance = null;
    let playedSlides = new Set(); // 已讀完的投影片頁面索引
    
    // 初始化投影片與題目
    document.addEventListener("DOMContentLoaded", () => {
      document.getElementById("total-slides-hint").textContent = SLIDES.length;
      initSlideStage();
      initQuizSection();
      loadSavedConfig();
      updateProgressUI();
    });

    // 1. 初始化投影片畫面
    function initSlideStage() {
      const stage = document.getElementById("slide-stage");
      stage.innerHTML = "";
      SLIDES.forEach((slide, idx) => {
        const slideCard = document.createElement("div");
        slideCard.className = \`slide-card\${idx === 0 ? " active" : ""}\`;
        slideCard.id = \`slide-card-\${idx}\`;
        
        let bulletsHtml = "";
        if (Array.isArray(slide.bullets)) {
          bulletsHtml = slide.bullets.map((bullet, bIdx) => {
            return \`<li style="animation-delay: \${0.2 + bIdx * 0.15}s">\${bullet}</li>\`;
          }).join("");
        }
        
        slideCard.innerHTML = \`
          <div class="slide-inner">
            <h2>\${slide.title}</h2>
            <ul class="slide-bullets">
              \${bulletsHtml}
            </ul>
          </div>
        \`;
        stage.appendChild(slideCard);
      });
      updateControls();
    }

    // 2. 啟動播放器 (覆蓋層點擊)
    function activatePlayer() {
      document.getElementById("player-start-overlay").classList.add("gone");
      isActivated = true;
      isVoicePlaying = true;
      curSlideIdx = 0;
      playedSlides.add(0);
      updateControls();
      setTimeout(speakCurrentSlide, 300);
      
      // 解鎖下一步的某些狀態
      document.getElementById("step1").classList.add("active");
    }

    // 3. 語音朗讀控制
    function speakCurrentSlide() {
      if (!isActivated) return;
      stopSpeech();

      const text = SLIDES[curSlideIdx].narration;
      if (!text || text.trim() === "") {
        // 如果沒有語音，則模擬播完
        handleVoiceEnded();
        return;
      }

      currentUtterance = new SpeechSynthesisUtterance(text);
      
      // 語音語速設定
      const speed = parseFloat(document.getElementById("speed-select").value) || 1.0;
      currentUtterance.rate = speed;
      
      // 嘗試獲取中文語音
      const voices = speechSynth.getVoices();
      const zhVoice = voices.find(v => v.lang.includes("zh-TW") || v.lang.includes("zh-CN") || v.lang.includes("zh"));
      if (zhVoice) currentUtterance.voice = zhVoice;
      
      currentUtterance.onend = () => {
        handleVoiceEnded();
      };

      currentUtterance.onerror = (e) => {
        console.error("SpeechSynthesis error:", e);
        // 出錯時做降級處理，避免卡死
        if (isVoicePlaying) {
          handleVoiceEnded();
        }
      };

      // 執行朗讀
      speechSynth.speak(currentUtterance);
      document.getElementById("btn-voice").textContent = "⏸";
      document.getElementById("btn-voice").classList.add("playing");
      isVoicePlaying = true;
    }

    // 4. 停止朗讀
    function stopSpeech() {
      if (speechSynth) {
        speechSynth.cancel();
      }
      document.getElementById("btn-voice").textContent = "▶";
      document.getElementById("btn-voice").classList.remove("playing");
      isVoicePlaying = false;
    }

    // 5. 播放/暫停按鈕
    function toggleVoice() {
      if (!isActivated) return;
      if (isVoicePlaying) {
        stopSpeech();
      } else {
        isVoicePlaying = true;
        speakCurrentSlide();
      }
    }

    // 6. 語意朗讀播放完畢
    function handleVoiceEnded() {
      playedSlides.add(curSlideIdx);
      updateControls();
      
      // 檢查是否看完所有投影片
      checkAllSlidesRead();

      if (isAutoAdvance && curSlideIdx < SLIDES.length - 1) {
        setTimeout(() => {
          if (isAutoAdvance && isVoicePlaying) {
            nextSlide();
          }
        }, 1500); // 延遲 1.5 秒換下一頁
      } else if (curSlideIdx === SLIDES.length - 1) {
        stopSpeech();
      }
    }

    // 7. 切換投影片
    function showSlide(idx) {
      if (idx < 0 || idx >= SLIDES.length) return;
      
      // 檢查防刷限制：如果規定必須聽完語音，且上一頁還沒聽完，不允許往後切換
      if (REQUIRE_LISTEN && idx > curSlideIdx && !playedSlides.has(curSlideIdx)) {
        alert("請先完整閱讀並聽完目前頁面的語音配音喔！");
        return;
      }

      stopSpeech();

      // 切換 HTML 卡片顯示
      document.getElementById(\`slide-card-\${curSlideIdx}\`).classList.remove("active");
      curSlideIdx = idx;
      document.getElementById(\`slide-card-\${curSlideIdx}\`).classList.add("active");
      
      playedSlides.add(curSlideIdx); // 只要切換到該頁，就算防刷有鎖，只要能切過去的就算已讀
      updateControls();
      checkAllSlidesRead();

      // 重新發聲
      if (isActivated) {
        setTimeout(() => {
          isVoicePlaying = true;
          speakCurrentSlide();
        }, 100);
      }
    }

    function nextSlide() {
      if (curSlideIdx < SLIDES.length - 1) {
        showSlide(curSlideIdx + 1);
      }
    }

    function prevSlide() {
      if (curSlideIdx > 0) {
        showSlide(curSlideIdx - 1);
      }
    }

    // 8. 更新播放器 UI 控制項
    function updateControls() {
      document.getElementById("btn-prev").disabled = (curSlideIdx === 0);
      
      // 下一頁按鈕：如果設定了需要聽完，且目前頁面尚未聽完，則禁用下一頁
      if (REQUIRE_LISTEN && !playedSlides.has(curSlideIdx)) {
        document.getElementById("btn-next").disabled = true;
      } else {
        document.getElementById("btn-next").disabled = (curSlideIdx === SLIDES.length - 1);
      }

      document.getElementById("slide-indicator").textContent = \`\${curSlideIdx + 1} / \${SLIDES.length}\`;
      document.getElementById("slide-label").textContent = SLIDES[curSlideIdx].title;
      
      // 進度條
      const pct = ((curSlideIdx + 1) / SLIDES.length) * 100;
      document.getElementById("progress-fill").style.width = \`\${pct}%\`;
    }

    // 9. 切換語速
    function changeSpeed() {
      if (isVoicePlaying) {
        speakCurrentSlide(); // 重新播放以套用語速
      }
    }

    // 10. 切換自動換頁
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

    // 11. 鍵盤事件監聽 (←, →, Space, V)
    document.addEventListener("keydown", (e) => {
      if (!isActivated) return;
      // 避免打字時觸發快捷鍵
      if (document.activeElement.tagName === "INPUT" || document.activeElement.tagName === "TEXTAREA") {
        return;
      }
      
      if (e.key === "ArrowRight") {
        nextSlide();
      } else if (e.key === "ArrowLeft") {
        prevSlide();
      } else if (e.key === " " || e.key === "Spacebar" || e.key.toLowerCase() === "v") {
        e.preventDefault();
        toggleVoice();
      }
    });

    // 12. 檢查是否聽完所有投影片並解鎖測驗
    function checkAllSlidesRead() {
      const isFinished = playedSlides.size === SLIDES.length;
      if (isFinished || !REQUIRE_LISTEN) {
        const unlockBtn = document.getElementById("btn-unlock-quiz");
        unlockBtn.disabled = false;
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

    // ════════════════════════════════════════
    //  測驗區邏輯
    // ════════════════════════════════════════
    
    // 1. 初始化測驗題目
    function initQuizSection() {
      const container = document.getElementById("quiz-container");
      container.innerHTML = "";
      
      document.getElementById("quiz-progress-badge").textContent = \`已作答 0 / \${QUIZ.length} 題\`;

      QUIZ.forEach((q, idx) => {
        const card = document.createElement("div");
        card.className = "question-card";
        card.id = \`q-card-\${idx}\`;
        
        let optionsHtml = "";
        q.options.forEach((optText, oIdx) => {
          const optLetter = String.fromCharCode(65 + oIdx); // A, B, C, D...
          optionsHtml += \`
            <label class="option-item" onclick="selectOption(\${idx})">
              <input type="radio" name="q-\${idx}" value="\${optLetter}">
              <span class="option-dot"></span>
              <span>\${optText}</span>
            </label>
          \`;
        });

        card.innerHTML = \`
          <div class="question-num">Question \${idx + 1}</div>
          <div class="question-title">\${q.question}</div>
          <div class="options-list">
            \${optionsHtml}
          </div>
        \`;
        container.appendChild(card);
      });
    }

    // 2. 點選選項
    function selectOption(qIdx) {
      document.getElementById(\`q-card-\${qIdx}\`).classList.add("answered");
      updateQuizProgress();
      validateForm();
    }

    // 3. 更新作答題數標記
    function updateQuizProgress() {
      let answeredCount = 0;
      for (let i = 0; i < QUIZ.length; i++) {
        const radios = document.getElementsByName(\`q-\${i}\`);
        let selected = false;
        for (let r of radios) {
          if (r.checked) { selected = true; break; }
        }
        if (selected) answeredCount++;
      }
      document.getElementById("quiz-progress-badge").textContent = \`已作答 \${answeredCount} / \${QUIZ.length} 題\`;
      
      if (answeredCount === QUIZ.length) {
        document.getElementById("step3").classList.add("active");
        document.getElementById("line2").classList.add("active");
      } else {
        document.getElementById("step3").classList.remove("active");
        document.getElementById("line2").classList.remove("active");
      }
      return answeredCount;
    }

    // 4. 驗證姓名輸入與題目是否作答完畢
    function validateForm() {
      const name = document.getElementById("user-name").value.trim();
      const answeredCount = updateQuizProgress();
      const btn = document.getElementById("btn-submit-quiz");
      
      if (name.length >= 1 && answeredCount === QUIZ.length) {
        btn.disabled = false;
      } else {
        btn.disabled = true;
      }
    }

    // 5. 提交考卷
    function submitQuiz() {
      const name = document.getElementById("user-name").value.trim();
      if (!name) return;

      const record = {
        name: name,
        timestamp: new Date().toLocaleString("zh-TW", { timeZone: "Asia/Taipei" }),
        answers: [],
        score: 0,
        correctCount: 0,
        total: QUIZ.length
      };

      // 計算分數
      QUIZ.forEach((q, idx) => {
        const radios = document.getElementsByName(\`q-\${idx}\`);
        let selectedValue = "";
        for (let r of radios) {
          if (r.checked) {
            selectedValue = r.value; // A, B, C, D
            break;
          }
        }
        
        const isCorrect = (selectedValue === q.answer.trim().toUpperCase());
        if (isCorrect) record.correctCount++;
        
        record.answers.push({
          num: idx + 1,
          question: q.question,
          selected: selectedValue,
          correct: q.answer,
          isCorrect: isCorrect
        });
      });

      record.score = Math.round((record.correctCount / record.total) * 100);
      
      // 儲存至本機
      saveRecordToLocal(record);
      
      // 顯示結果 Modal
      showResultModal(record);

      // 同步傳送至本機網頁伺服器及選填的雲端試算表
      submitToServer(record);
    }

    // 6. 送出至後端
    function submitToServer(record) {
      // 建立伺服器通用的 Payload 結構
      const payload = {
        name: record.name,
        timestamp: record.timestamp,
        score: record.score,
        correctCount: record.correctCount,
        total: record.total
      };
      
      // 動態加上 q1, q2... 屬性方便後端寫入 CSV/Google Sheets
      record.answers.forEach((ans, idx) => {
        payload[\`q\${idx + 1}\`] = \`答: \${ans.selected} (\${ans.isCorrect ? "對" : "錯"} / 正確: \${ans.correct})\`;
      });

      // (A) 嘗試傳送到本機 PowerShell 伺服器
      fetch("/api/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      })
      .then(res => res.json())
      .then(data => console.log("本機伺服器儲存成功:", data))
      .catch(err => console.warn("未連接本機伺服器或傳送失敗 (本機單機版模式):", err));

      // (B) 嘗試傳送到 Google Apps Script 雲端
      const cloudUrl = localStorage.getItem("training_cloud_url") || "";
      if (cloudUrl && cloudUrl.startsWith("http")) {
        // 使用 no-cors 或傳送 form-data / JSONP，因為 Apps Script 通常存在 CORS 轉址問題
        // 我們直接使用 JSON 傳送並捕獲結果
        fetch(cloudUrl, {
          method: "POST",
          mode: "no-cors", // Apps Script 轉導常導致 CORS 錯誤，用 no-cors 可確保請求送出
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        })
        .then(() => console.log("雲端 Google Sheets 備份已送出 (no-cors 模式不回傳狀態)"))
        .catch(err => console.error("雲端備份傳送出錯:", err));
      }
    }

    // 7. 顯示/隱藏結果 Modal
    function showResultModal(record) {
      const modal = document.getElementById("result-modal");
      const icon = document.getElementById("res-icon");
      const title = document.getElementById("res-title");
      const score = document.getElementById("res-score");
      const details = document.getElementById("res-details");
      
      const passed = record.score >= PASS_SCORE;
      
      icon.textContent = passed ? "🎉" : "💪";
      title.textContent = passed ? "恭喜通過測驗！" : "很可惜未達及格標準，請再接再厲！";
      score.textContent = \`\${record.score} 分\`;
      
      // 動態更新分數卡片顏色
      if (passed) {
        score.style.background = "linear-gradient(135deg, #10b981, #059669)";
      } else {
        score.style.background = "linear-gradient(135deg, #f43f5e, #e11d48)";
      }
      score.style.webkitBackgroundClip = "text";
      score.style.webkitTextFillColor = "transparent";
      
      details.innerHTML = \`
        姓名：\${record.name}<br>
        及格分數：\${PASS_SCORE} 分<br>
        答對題數：\${record.correctCount} / \${record.total} 題<br>
        <span style="font-size: 0.8rem; display: block; margin-top: 8px; color: var(--text-muted)">時間：\${record.timestamp}</span>
      \`;
      
      modal.classList.add("show");
    }

    function hideResultModal() {
      document.getElementById("result-modal").classList.remove("show");
    }

    function closeResultModal(e) {
      if (e.target.id === "result-modal") {
        hideResultModal();
      }
    }

    // ════════════════════════════════════════
    //  設定面板與本機 LocalStorage 管理
    // ════════════════════════════════════════
    
    function openCfgModal() {
      const pwd = prompt("請輸入管理員密碼以進入設定面板：");
      if (pwd === "admin888") {
        document.getElementById("cfg-modal").classList.add("show");
        updateRecordsUI();
      } else if (pwd !== null) {
        alert("密碼錯誤，拒絕存取！");
      }
    }

    function closeCfgModal(e) {
      document.getElementById("cfg-modal").classList.remove("show");
      document.getElementById("records-preview").style.display = "none";
    }

    function loadSavedConfig() {
      const cloudUrl = localStorage.getItem("training_cloud_url") || "";
      document.getElementById("cfg-cloud-url").value = cloudUrl;
    }

    function saveConfig() {
      const url = document.getElementById("cfg-cloud-url").value.trim();
      localStorage.setItem("training_cloud_url", url);
      alert("設定儲存成功！");
      document.getElementById("cfg-modal").classList.remove("show");
    }

    // 本機作答存檔
    function saveRecordToLocal(record) {
      let records = [];
      try {
        records = JSON.parse(localStorage.getItem("training_local_records") || "[]");
      } catch(e) { records = []; }
      
      records.unshift(record); // 最新的一筆排在最前面
      localStorage.setItem("training_local_records", JSON.stringify(records));
    }

    function updateRecordsUI() {
      let records = [];
      try {
        records = JSON.parse(localStorage.getItem("training_local_records") || "[]");
      } catch(e) { records = []; }
      
      document.getElementById("records-count").textContent = \`本機累計作答：\${records.length} 筆\`;
    }

    // 匯出 CSV 檔
    function exportRecordsCSV() {
      let records = [];
      try { records = JSON.parse(localStorage.getItem("training_local_records") || "[]"); } catch(e) {}
      
      if (records.length === 0) {
        alert("目前尚無任何本機作答紀錄！");
        return;
      }

      let csvContent = "\\ufeff時間戳記,姓名,答對題數,得分";
      
      // 動態抓取最大題目數
      const maxQs = QUIZ.length;
      for (let i = 1; i <= maxQs; i++) {
        csvContent += \`,第\${i}題\`;
      }
      csvContent += "\\r\\n";

      records.forEach(r => {
        let row = \`"\${r.timestamp}","\${r.name}","\${r.correctCount} / \${r.total}","\${r.score} 分"\`;
        
        for (let i = 0; i < maxQs; i++) {
          const ans = r.answers[i];
          if (ans) {
            row += \`,"答: \${ans.selected} (\${ans.isCorrect ? "對" : "錯"})"\`;
          } else {
            row += ',""';
          }
        }
        csvContent += row + "\\r\\n";
      });

      const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.setAttribute("href", url);
      link.setAttribute("download", \`\${SLIDES[0].title}_作答紀錄.csv\`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }

    // 預覽本機紀錄
    function previewRecords() {
      let records = [];
      try { records = JSON.parse(localStorage.getItem("training_local_records") || "[]"); } catch(e) {}
      
      const previewBox = document.getElementById("records-preview");
      if (records.length === 0) {
        previewBox.textContent = "尚無紀錄";
        previewBox.style.display = "block";
        return;
      }

      let text = "【最近作答明細】\\n";
      records.forEach((r, idx) => {
        text += \`[\${idx+1}] \${r.timestamp} | 姓名: \${r.name} | 得分: \${r.score}分 (\${r.correctCount}/\${r.total}題)\\n\`;
        r.answers.forEach(ans => {
          text += \`    Q\${ans.num}: 學生答 \${ans.selected} | 正確: \${ans.correct} | \${ans.isCorrect ? "✅ 對" : "❌ 錯"}\\n\`;
        });
        text += "--------------------------------------------\\n";
      });

      previewBox.textContent = text;
      previewBox.style.display = "block";
    }

    // 清除紀錄
    function clearRecordsConfirm() {
      if (confirm("確定要【清除本機所有作答紀錄】嗎？此操作無法還原！\\n(若有連接本機 server 或 Google Sheet，已上傳之紀錄不受影響)")) {
        localStorage.removeItem("training_local_records");
        updateRecordsUI();
        document.getElementById("records-preview").style.display = "none";
        alert("本機紀錄已清除！");
      }
    }
  </script>
</body>
</html>`;

export { PLAYER_TEMPLATE };

```
