# 程式碼備份與修改紀錄: index.html

本文件為 `index.html` 的程式碼備份，便於後續版本比對與修改紀錄追蹤。

## 原始程式碼

```html
<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <script>
    window.onerror = function(msg, url, line) {
      alert("產生器網頁錯誤：" + msg + "\n在：" + url + " 第 " + line + " 行");
      return false;
    };
  </script>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>員工教育訓練測驗產生器 — 智慧 SOP 自動化封裝</title>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Noto+Sans+TC:wght@300;400;500;700;900&display=swap" rel="stylesheet">
  <!-- 引入 JSZip 讓瀏覽器端可以打包 ZIP 檔案 -->
  <script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js"></script>
  <!-- 引入 PDF.js 用於本機端解析 PDF 檔案之文字內容 -->
  <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.min.js"></script>
  <!-- 引入 Mammoth.js 用於本機端解析 Word (.docx) 檔案之文字內容 -->
  <script src="https://cdnjs.cloudflare.com/ajax/libs/mammoth/1.6.0/mammoth.browser.min.js"></script>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    
    :root {
      --bg: #0b0f19;
      --surface: #111827;
      --surface-card: rgba(17, 24, 39, 0.7);
      --surface-hover: #1f2937;
      --border: rgba(255, 255, 255, 0.08);
      --border-focus: rgba(99, 102, 241, 0.6);
      --text: #f3f4f6;
      --text-muted: #9ca3af;
      --primary: #6366f1;
      --primary-hover: #4f46e5;
      --primary-glow: rgba(99, 102, 241, 0.4);
      --success: #10b981;
      --error: #f43f5e;
      --gradient: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
    }

    body {
      background-color: var(--bg);
      background-image: radial-gradient(circle at 50% 0%, rgba(99, 102, 241, 0.15) 0%, transparent 50%),
                        radial-gradient(circle at 0% 100%, rgba(139, 92, 246, 0.08) 0%, transparent 40%);
      background-attachment: fixed;
      color: var(--text);
      font-family: 'Outfit', 'Noto Sans TC', sans-serif;
      min-height: 100vh;
      line-height: 1.6;
    }

    header {
      background: rgba(17, 24, 39, 0.85);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--border);
      padding: 16px 24px;
      position: sticky;
      top: 0;
      z-index: 90;
    }

    .header-container {
      max-width: 1200px;
      margin: 0 auto;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }

    .logo {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .logo-icon {
      width: 44px;
      height: 44px;
      background: var(--gradient);
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 22px;
      color: #fff;
      box-shadow: 0 4px 14px var(--primary-glow);
    }

    .logo-text h1 {
      font-size: 1.2rem;
      font-weight: 800;
      background: linear-gradient(to right, #ffffff, #c7d2fe);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    .logo-text p {
      font-size: 0.75rem;
      color: var(--text-muted);
    }

    .nav-links {
      display: flex;
      align-items: center;
      gap: 16px;
    }

    .btn-github {
      background: rgba(255,255,255,0.04);
      border: 1px solid var(--border);
      color: var(--text);
      padding: 8px 16px;
      border-radius: 8px;
      text-decoration: none;
      font-size: 0.85rem;
      font-weight: 500;
      transition: all 0.2s;
    }

    .btn-github:hover {
      background: rgba(255,255,255,0.08);
      border-color: rgba(255,255,255,0.15);
    }

    main {
      max-width: 1200px;
      margin: 40px auto;
      padding: 0 24px 80px;
    }

    /* STEP WIZARD */
    .wizard-steps {
      display: flex;
      justify-content: space-between;
      max-width: 700px;
      margin: 0 auto 40px;
      position: relative;
    }

    .wizard-step {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 8px;
      z-index: 2;
      color: var(--text-muted);
      font-size: 0.85rem;
      font-weight: 500;
      flex: 1;
      text-align: center;
    }

    .wizard-step.active {
      color: var(--text);
    }

    .wizard-step.done {
      color: var(--success);
    }

    .wizard-num {
      width: 32px;
      height: 32px;
      border-radius: 50%;
      background: #1f2937;
      border: 2px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      font-size: 0.85rem;
      transition: all 0.3s;
    }

    .wizard-step.active .wizard-num {
      background: var(--primary);
      border-color: var(--primary);
      color: #fff;
      box-shadow: 0 0 15px var(--primary-glow);
    }

    .wizard-step.done .wizard-num {
      background: var(--success);
      border-color: var(--success);
      color: #fff;
    }

    .wizard-line {
      position: absolute;
      top: 16px;
      left: 10%;
      right: 10%;
      height: 2px;
      background: var(--border);
      z-index: 1;
    }

    .wizard-line-fill {
      height: 100%;
      background: var(--primary);
      width: 0%;
      transition: width 0.3s ease;
    }

    /* CARDS */
    .card {
      background: var(--surface-card);
      border: 1px solid var(--border);
      border-radius: 20px;
      padding: 36px;
      backdrop-filter: blur(12px);
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
      display: none;
    }

    .card.active {
      display: block;
      animation: fadeIn 0.4s ease-out;
    }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }

    .grid-2 {
      display: grid;
      grid-template-columns: 1fr 1.3fr;
      gap: 36px;
    }

    @media (max-width: 900px) {
      .grid-2 { grid-template-columns: 1fr; }
    }

    /* FORM ELEMENTS */
    .form-group {
      margin-bottom: 24px;
    }

    .form-label {
      display: block;
      font-size: 0.88rem;
      font-weight: 600;
      color: var(--text);
      margin-bottom: 8px;
    }

    .form-input, .form-select, .form-textarea {
      width: 100%;
      background: rgba(17, 24, 39, 0.8);
      border: 1.5px solid var(--border);
      border-radius: 10px;
      padding: 12px 14px;
      color: var(--text);
      font-family: inherit;
      font-size: 0.9rem;
      outline: none;
      transition: all 0.2s;
    }

    .form-input:focus, .form-select:focus, .form-textarea:focus {
      border-color: var(--primary);
      box-shadow: 0 0 0 3px var(--primary-glow);
    }

    .form-textarea {
      resize: vertical;
      min-height: 250px;
    }

    /* UPLOAD ZONE */
    .upload-zone {
      border: 2.5px dashed var(--border);
      border-radius: 14px;
      padding: 24px;
      text-align: center;
      cursor: pointer;
      background: rgba(255,255,255,0.01);
      transition: all 0.2s;
      margin-top: 8px;
    }

    .upload-zone:hover {
      border-color: var(--primary);
      background: rgba(99, 102, 241, 0.03);
    }

    .upload-icon {
      font-size: 32px;
      margin-bottom: 8px;
    }

    .upload-text {
      font-size: 0.85rem;
      color: var(--text-muted);
    }

    .upload-text strong {
      color: var(--primary);
    }

    /* CONFIG SLIDER GROUP */
    .slider-group {
      display: flex;
      align-items: center;
      gap: 16px;
    }

    .slider-val {
      min-width: 40px;
      font-weight: 700;
      color: var(--primary);
      font-size: 1.1rem;
    }

    .form-range {
      flex: 1;
      accent-color: var(--primary);
      height: 6px;
      border-radius: 3px;
      outline: none;
      cursor: pointer;
    }

    .checkbox-label {
      display: flex;
      align-items: center;
      gap: 10px;
      cursor: pointer;
      font-size: 0.88rem;
    }

    .checkbox-input {
      width: 18px;
      height: 18px;
      accent-color: var(--primary);
      cursor: pointer;
    }

    .btn-submit {
      background: var(--gradient);
      color: #fff;
      border: none;
      border-radius: 50px;
      padding: 16px 36px;
      font-size: 1.05rem;
      font-weight: 700;
      cursor: pointer;
      width: 100%;
      box-shadow: 0 4px 20px var(--primary-glow);
      transition: all 0.2s;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
    }

    .btn-submit:hover:not(:disabled) {
      transform: translateY(-2px);
      box-shadow: 0 8px 25px rgba(99, 102, 241, 0.6);
    }

    .btn-submit:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    /* EDITING INTERFACE */
    .edit-tabs {
      display: flex;
      gap: 8px;
      border-bottom: 1px solid var(--border);
      margin-bottom: 24px;
      padding-bottom: 12px;
    }

    .edit-tab-btn {
      background: none;
      border: none;
      color: var(--text-muted);
      padding: 8px 18px;
      font-weight: 600;
      font-size: 0.95rem;
      cursor: pointer;
      border-radius: 8px;
      transition: all 0.2s;
    }

    .edit-tab-btn:hover {
      background: rgba(255, 255, 255, 0.05);
      color: var(--text);
    }

    .edit-tab-btn.active {
      background: rgba(99, 102, 241, 0.12);
      color: #a5b4fc;
      border: 1px solid rgba(99, 102, 241, 0.2);
    }

    .pane-content {
      display: none;
    }

    .pane-content.active {
      display: block;
    }

    .card-list {
      display: flex;
      flex-direction: column;
      gap: 20px;
    }

    .edit-card {
      background: rgba(255, 255, 255, 0.02);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 24px;
      position: relative;
    }

    .edit-card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 18px;
      border-bottom: 1px solid rgba(255,255,255,0.05);
      padding-bottom: 10px;
    }

    .edit-card-num {
      font-size: 0.9rem;
      font-weight: 700;
      color: var(--primary);
    }

    .edit-card-actions {
      display: flex;
      gap: 8px;
    }

    .action-icon-btn {
      background: rgba(255,255,255,0.04);
      border: 1px solid var(--border);
      color: var(--text);
      width: 32px;
      height: 32px;
      border-radius: 6px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 14px;
      transition: all 0.2s;
    }

    .action-icon-btn:hover {
      background: rgba(255,255,255,0.1);
      color: #fff;
    }

    .action-icon-btn.danger:hover {
      background: rgba(244, 63, 94, 0.15);
      border-color: rgba(244, 63, 94, 0.3);
      color: #fda4af;
    }

    .bullets-edit-container {
      display: flex;
      flex-direction: column;
      gap: 8px;
      margin-bottom: 16px;
    }

    .bullet-edit-row {
      display: flex;
      gap: 8px;
    }

    .bullet-edit-input {
      flex: 1;
      background: rgba(17, 24, 39, 0.5);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 8px 12px;
      color: var(--text);
      font-size: 0.85rem;
    }

    .bullet-edit-input:focus {
      border-color: var(--primary);
      outline: none;
    }

    /* TTS PREVIEW BTN */
    .btn-tts-preview {
      background: rgba(99, 102, 241, 0.1);
      border: 1px solid rgba(99, 102, 241, 0.3);
      color: #a5b4fc;
      padding: 6px 12px;
      border-radius: 6px;
      font-size: 0.8rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }

    .btn-tts-preview:hover {
      background: var(--primary);
      color: #fff;
      border-color: var(--primary);
    }

    .btn-tts-preview.playing {
      background: var(--success);
      color: #fff;
      border-color: var(--success);
    }

    .btn-add-item {
      background: rgba(255,255,255,0.03);
      border: 1px dashed var(--border);
      color: var(--text-muted);
      border-radius: 12px;
      padding: 16px;
      text-align: center;
      cursor: pointer;
      font-weight: 600;
      font-size: 0.9rem;
      transition: all 0.2s;
    }

    .btn-add-item:hover {
      border-color: var(--primary);
      color: var(--primary);
      background: rgba(99, 102, 241, 0.02);
    }

    /* FOOTER ACTION BAR */
    .footer-actions {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 36px;
      border-top: 1px solid var(--border);
      padding-top: 24px;
    }

    .btn-secondary {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--border);
      color: var(--text);
      border-radius: 50px;
      padding: 14px 28px;
      font-size: 0.95rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
    }

    .btn-secondary:hover {
      background: rgba(255, 255, 255, 0.1);
    }

    /* LOADING OVERLAY */
    .loading-mask {
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(7, 11, 20, 0.9);
      backdrop-filter: blur(8px);
      z-index: 1000;
      align-items: center;
      justify-content: center;
      flex-direction: column;
    }

    .loading-mask.show {
      display: flex;
    }

    .loader {
      width: 60px;
      height: 60px;
      border: 5px solid rgba(99, 102, 241, 0.2);
      border-top-color: var(--primary);
      border-radius: 50%;
      animation: spin 1s linear infinite;
      margin-bottom: 24px;
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }

    .loading-title {
      font-size: 1.3rem;
      font-weight: 700;
      margin-bottom: 16px;
      background: var(--gradient);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    .loading-steps {
      display: flex;
      flex-direction: column;
      gap: 12px;
      max-width: 320px;
      width: 100%;
    }

    .loading-step-item {
      display: flex;
      align-items: center;
      gap: 12px;
      font-size: 0.88rem;
      color: var(--text-muted);
    }

    .loading-step-item.active {
      color: var(--text);
      font-weight: 600;
    }

    .loading-step-item.done {
      color: var(--success);
    }

    .loading-step-dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: var(--border);
      flex-shrink: 0;
    }

    .loading-step-item.active .loading-step-dot {
      background: var(--primary);
      box-shadow: 0 0 8px var(--primary);
    }

    .loading-step-item.done .loading-step-dot {
      background: var(--success);
    }

    /* EXPORT SUCCESS CARD */
    .success-icon-box {
      font-size: 64px;
      margin-bottom: 16px;
      text-align: center;
    }

    .success-desc {
      text-align: center;
      color: var(--text-muted);
      font-size: 0.95rem;
      max-width: 500px;
      margin: 0 auto 32px;
    }

    .step3-grid {
      display: grid;
      grid-template-columns: 1.2fr 1fr;
      gap: 28px;
    }

    @media (max-width: 768px) {
      .step3-grid { grid-template-columns: 1fr; }
    }

    .instruction-card {
      background: rgba(255,255,255,0.015);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 20px;
    }

    .instruction-card h3 {
      font-size: 1rem;
      margin-bottom: 12px;
      color: var(--primary);
    }

    .instruction-card ol {
      padding-left: 20px;
      font-size: 0.85rem;
      color: var(--text-muted);
      display: flex;
      flex-direction: column;
      gap: 8px;
    }

    .instruction-card ol strong {
      color: var(--text);
    }
    @media (max-width: 600px) {
      .wizard-steps {
        flex-direction: column;
        gap: 16px;
        align-items: flex-start;
        max-width: 240px;
        margin: 0 auto 30px;
      }
      .wizard-step {
        flex-direction: row;
        gap: 12px;
        text-align: left;
      }
      .wizard-line {
        display: none;
      }
    }
  </style>
</head>
<body>

  <header>
    <div class="header-container">
      <div class="logo">
        <div class="logo-icon">⚡</div>
        <div class="logo-text">
          <h1>員工教育訓練測驗產生系統</h1>
          <p>SOP 教材智慧解析與零安裝離線封裝網頁工具</p>
        </div>
      </div>
      <div class="nav-links">
        <span style="font-size: 0.85rem; color: var(--text-muted);">本機獨立運行版 (免伺服器)</span>
      </div>
    </div>
  </header>

  <!-- 步驟引導 -->
  <div class="wizard-steps">
    <div class="wizard-step active" id="wiz-step-1">
      <div class="wizard-num">1</div>
      <span>設定與輸入 SOP</span>
    </div>
    <div class="wizard-step" id="wiz-step-2">
      <div class="wizard-num">2</div>
      <span>檢視與修改內容</span>
    </div>
    <div class="wizard-step" id="wiz-step-3">
      <div class="wizard-num">3</div>
      <span>匯出與完成</span>
    </div>
    <div class="wizard-line">
      <div class="wizard-line-fill" id="wiz-line-fill"></div>
    </div>
  </div>

  <main>
    <!-- 第一步：輸入與 API 設定 -->
    <section class="card active" id="card-step-1">
      <div class="grid-2">
        <!-- 左欄：API 與參數設定 -->
        <div>
          <div class="badge">⚙️ 設定與參數</div>
          <h2 style="font-size: 1.3rem; font-weight: 700; margin-bottom: 24px;">模型 API 與生成引數</h2>

          <div class="form-group">
            <label class="form-label" for="api-provider">🤖 AI API 提供商</label>
            <select class="form-select" id="api-provider" onchange="toggleApiProvider()">
              <option value="gemini" selected>Google Gemini (AI Studio)</option>
              <option value="groq">Groq (Llama / Mixtral)</option>
            </select>
          </div>

          <div class="form-group">
            <label class="form-label" for="api-key">🔑 API 金鑰 (API Key)</label>
            <input type="password" class="form-input" id="api-key" placeholder="請貼上您的 API Key" />
          </div>

          <div class="form-group">
            <label class="form-label" for="api-model">📦 選擇模型 (Model)</label>
            <select class="form-select" id="api-model">
              <!-- 動態載入 -->
            </select>
          </div>

          <div class="form-group">
            <label class="form-label">📊 預計簡報投影片頁數</label>
            <div class="slider-group">
              <input type="range" class="form-range" id="slide-count" min="5" max="15" value="10" oninput="document.getElementById('slide-val').textContent = this.value">
              <span class="slider-val" id="slide-val">10</span>
              <span style="font-size: 0.8rem; color: var(--text-muted);">頁</span>
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">📝 預計測驗題目數量</label>
            <div class="slider-group">
              <input type="range" class="form-range" id="quiz-count" min="3" max="10" value="5" oninput="document.getElementById('quiz-val').textContent = this.value">
              <span class="slider-val" id="quiz-val">5</span>
              <span style="font-size: 0.8rem; color: var(--text-muted);">題</span>
            </div>
          </div>

          <div class="form-group">
            <label class="form-label" for="pass-score">🎯 測驗及格分數</label>
            <select class="form-select" id="pass-score">
              <option value="60">60 分 (及格)</option>
              <option value="70">70 分</option>
              <option value="80" selected>80 分</option>
              <option value="90">90 分</option>
              <option value="100">100 分 (完美)</option>
            </select>
          </div>

          <div class="form-group">
            <label class="checkbox-label">
              <input type="checkbox" class="checkbox-input" id="require-listen" checked>
              <span>🔒 啟用防刷限制（同仁需聽完該頁語音方可切換下一頁與測驗）</span>
            </label>
          </div>
        </div>

        <!-- 右欄：SOP 輸入 -->
        <div style="display: flex; flex-direction: column; justify-content: space-between;">
          <div>
            <div class="badge">📄 教育訓練素材</div>
            <h2 style="font-size: 1.3rem; font-weight: 700; margin-bottom: 24px;">貼上 SOP 或教材內容</h2>

            <div class="form-group" style="margin-bottom: 12px;">
              <textarea class="form-textarea" id="sop-text" placeholder="請將工作規則、SOP 手冊、消防演練教材或任何想要進行教育訓練的文字複製並貼到這裡..."></textarea>
            </div>

            <div class="upload-zone" id="upload-zone" onclick="document.getElementById('file-input').click()">
              <input type="file" id="file-input" style="display: none;" accept=".txt,.md,.pdf,.docx,.pptx" onchange="handleFileUpload(event)">
              <div class="upload-icon" id="upload-icon">📁</div>
              <div class="upload-text" id="upload-text">拖放或<strong>點擊上傳</strong>教材檔案 (支援 .txt, .md, .pdf, .docx, .pptx)</div>
            </div>
          </div>

          <button class="btn-submit" id="btn-generate" onclick="startGeneration()" style="margin-top: 24px;">
            <span>✨ 開始自動分析與產生簡報測驗</span>
          </button>
        </div>
      </div>
    </section>

    <!-- 第二步：審查與編輯 -->
    <section class="card" id="card-step-2">
      <div class="badge">✍️ 內容檢視與線上微調</div>
      
      <!-- 大標題編輯 -->
      <div class="grid-2" style="grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px;">
        <div class="form-group" style="margin-bottom: 0;">
          <label class="form-label">📋 主標題 (大標題)</label>
          <input type="text" class="form-input" id="edit-main-title">
        </div>
        <div class="form-group" style="margin-bottom: 0;">
          <label class="form-label">ℹ️ 副標題</label>
          <input type="text" class="form-input" id="edit-main-subtitle">
        </div>
      </div>

      <!-- Tab 控制項 -->
      <div class="edit-tabs">
        <button class="edit-tab-btn active" onclick="switchEditTab('slides')">📽️ 簡報投影片內容</button>
        <button class="edit-tab-btn" onclick="switchEditTab('quiz')">📝 測驗挑戰題目</button>
      </div>

      <!-- 簡報編輯面板 -->
      <div id="pane-slides" class="pane-content active">
        <p class="section-desc" style="margin-top: -12px; margin-bottom: 20px;">
          以下是為您產生的簡報投影片。您可以自由修改每一頁的標題、條列重點，以及語音朗讀文字，亦可進行試聽。
        </p>
        <div id="editor-slides-container" class="card-list"></div>
        <button class="btn-add-item" onclick="addSlideNode()" style="margin-top: 16px; width: 100%;">➕ 新增一頁簡報投影片</button>
      </div>

      <!-- 測驗題目編輯面板 -->
      <div id="pane-quiz" class="pane-content">
        <p class="section-desc" style="margin-top: -12px; margin-bottom: 20px;">
          以下是針對簡報內容產生的單選題。您可以修改題目、選項、正確答案與解析。
        </p>
        <div id="editor-quiz-container" class="card-list"></div>
        <button class="btn-add-item" onclick="addQuizNode()" style="margin-top: 16px; width: 100%;">➕ 新增一題測驗單選題</button>
      </div>

      <!-- 底部控制項 -->
      <div class="footer-actions">
        <button class="btn-secondary" onclick="backToStep1()">◀ 返回上一步</button>
        <button class="btn-submit" onclick="exportTrainingFiles()" style="width: auto;">
          <span>💾 產生並匯出教育訓練套件</span>
        </button>
      </div>
    </section>

    <!-- 第三步：完成與匯出 -->
    <section class="card" id="card-step-3">
      <div class="success-icon-box">🎉</div>
      <h2 style="text-align: center; font-size: 1.6rem; font-weight: 800; margin-bottom: 8px;">教育訓練套件匯出成功！</h2>
      <p class="success-desc" id="success-download-hint">
        您的訓練測驗套件 ZIP 壓縮包已下載完成。請解壓縮後查看資料夾內容！
      </p>

      <div class="step3-grid">
        <!-- 說明 1：本機免設定 -->
        <div class="instruction-card">
          <h3>🟢 模式一：本機內網回收 (最簡單，免任何設定)</h3>
          <ol>
            <li>將下載的壓縮包 (ZIP) <strong>完整解壓縮</strong> 至您的電腦上。</li>
            <li>滑鼠雙擊執行資料夾中的 <strong>「點我啟動內網伺服器(Windows免安裝).bat」</strong>。</li>
            <li>視窗會啟動並顯示綠色網址（例如：<code>http://192.168.x.x:8000/index.html</code>）。</li>
            <li><strong>不要關閉黑色視窗</strong>，把這串網址發給同仁（員工手機或電腦需連線同個 Wi-Fi）。</li>
            <li>同仁做完送出後，資料夾會<strong>自動產生 results.csv</strong>，可用 Excel 隨時開啟看結果！</li>
          </ol>
        </div>

        <!-- 說明 2：雲端試算表 -->
        <div class="instruction-card">
          <h3>🔵 模式二：Google Sheets 雲端同步 (可選填)</h3>
          <ol>
            <li>前往 <a href="https://sheets.new" target="_blank" style="color: var(--primary);">sheets.new</a> 建立一個新的 Google 試算表。</li>
            <li>點選上方選單「<strong>擴充功能</strong>」->「<strong>Apps Script</strong>」。</li>
            <li>將資料夾內的 <strong><code>apps_script_code.gs</code></strong> 內容貼入編輯器中，存檔。</li>
            <li>點選右上角「<strong>部署</strong>」->「網頁應用程式」，將存取權限設為「<strong>所有人 (Anyone)</strong>」並完成部署。</li>
            <li>複製產生的 Web App 網址，在測驗網頁右上角「<strong>⚙️ 系統設定</strong>」貼入即可自動備份雲端。</li>
          </ol>
        </div>
      </div>

      <div style="text-align: center; margin-top: 36px;">
        <button class="btn-submit" onclick="backToStep1()" style="width: auto; display: inline-flex;">
          🔄 重新解析另一份 SOP 教材
        </button>
      </div>
    </section>
  </main>

  <!-- 載入中遮罩 -->
  <div class="loading-mask" id="loading-mask">
    <div class="loader"></div>
    <div class="loading-title" id="loading-title">正在呼叫 AI 進行核心分析</div>
    <div class="loading-steps">
      <div class="loading-step-item active" id="load-step-1">
        <div class="loading-step-dot"></div>
        <span>分析並理解教材脈絡...</span>
      </div>
      <div class="loading-step-item" id="load-step-2">
        <div class="loading-step-dot"></div>
        <span>提煉多頁簡報重點大綱...</span>
      </div>
      <div class="loading-step-item" id="load-step-3">
        <div class="loading-step-dot"></div>
        <span>為每頁撰寫自然口語旁白...</span>
      </div>
      <div class="loading-step-item" id="load-step-4">
        <div class="loading-step-dot"></div>
        <span>設計緊扣教材的測驗挑戰...</span>
      </div>
    </div>
  </div>

  <script>
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
          keyInput.value = "gsk_PLACEHOLDER_KEY_YOUR_GROQ_API_KEY";
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

    // ════════════════════════════════════════
    //  INTERACTIVE CHALLENGE TEMPLATE SOURCE CODE (URL ENCODED)
    // ════════════════════════════════════════
    const INTERACTIVE_TEMPLATE_SOURCE = decodeURIComponent("%3C!DOCTYPE%20html%3E%0A%3Chtml%20lang%3D%22zh-TW%22%3E%0A%3Chead%3E%0A%20%20%3Cmeta%20charset%3D%22UTF-8%22%3E%0A%20%20%3Cmeta%20name%3D%22viewport%22%20content%3D%22width%3Ddevice-width%2C%20initial-scale%3D1.0%22%3E%0A%20%20%3Ctitle%3E__TRAINING_TITLE__%20%E2%80%94%20%E4%BA%92%E5%8B%95%E5%BC%8F%E6%83%85%E5%A2%83%E6%A8%A1%E6%93%AC%E9%97%96%E9%97%9C%3C%2Ftitle%3E%0A%20%20%3Clink%20href%3D%22https%3A%2F%2Ffonts.googleapis.com%2Fcss2%3Ffamily%3DOutfit%3Awght%40300%3B400%3B500%3B600%3B700%3B800%26family%3DNoto%2BSans%2BTC%3Awght%40300%3B400%3B500%3B700%3B900%26display%3Dswap%22%20rel%3D%22stylesheet%22%3E%0A%20%20%3Cstyle%3E%0A%20%20%20%20*%2C%20*%3A%3Abefore%2C%20*%3A%3Aafter%20%7B%20box-sizing%3A%20border-box%3B%20margin%3A%200%3B%20padding%3A%200%3B%20%7D%0A%20%20%20%20%3Aroot%20%7B%0A%20%20%20%20%20%20--bg%3A%20%23070b13%3B%0A%20%20%20%20%20%20--surface%3A%20%230e1626%3B%0A%20%20%20%20%20%20--surface-card%3A%20rgba(20%2C%2032%2C%2054%2C%200.6)%3B%0A%20%20%20%20%20%20--border%3A%20rgba(255%2C%20255%2C%20255%2C%200.08)%3B%0A%20%20%20%20%20%20--text%3A%20%23f3f4f6%3B%0A%20%20%20%20%20%20--text-muted%3A%20%239ca3af%3B%0A%20%20%20%20%20%20--primary%3A%20%236366f1%3B%0A%20%20%20%20%20%20--primary-hover%3A%20%234f46e5%3B%0A%20%20%20%20%20%20--success%3A%20%2310b981%3B%0A%20%20%20%20%20%20--success-bg%3A%20rgba(16%2C%20185%2C%20129%2C%200.1)%3B%0A%20%20%20%20%20%20--error%3A%20%23f43f5e%3B%0A%20%20%20%20%20%20--error-bg%3A%20rgba(244%2C%2063%2C%2094%2C%200.1)%3B%0A%20%20%20%20%7D%0A%20%20%20%20body%20%7B%0A%20%20%20%20%20%20background-color%3A%20var(--bg)%3B%0A%20%20%20%20%20%20background-image%3A%20radial-gradient(circle%20at%2050%25%2030%25%2C%20rgba(99%2C%20102%2C%20241%2C%200.15)%200%25%2C%20transparent%2070%25)%3B%0A%20%20%20%20%20%20color%3A%20var(--text)%3B%0A%20%20%20%20%20%20font-family%3A%20'Outfit'%2C%20'Noto%20Sans%20TC'%2C%20sans-serif%3B%0A%20%20%20%20%20%20min-height%3A%20100vh%3B%0A%20%20%20%20%20%20display%3A%20flex%3B%0A%20%20%20%20%20%20flex-direction%3A%20column%3B%0A%20%20%20%20%20%20align-items%3A%20center%3B%0A%20%20%20%20%20%20justify-content%3A%20center%3B%0A%20%20%20%20%20%20padding%3A%2020px%3B%0A%20%20%20%20%20%20overflow-x%3A%20hidden%3B%0A%20%20%20%20%7D%0A%20%20%20%20.game-container%20%7B%0A%20%20%20%20%20%20width%3A%20100%25%3B%0A%20%20%20%20%20%20max-width%3A%20750px%3B%0A%20%20%20%20%20%20background%3A%20var(--surface)%3B%0A%20%20%20%20%20%20border%3A%201px%20solid%20var(--border)%3B%0A%20%20%20%20%20%20border-radius%3A%2016px%3B%0A%20%20%20%20%20%20box-shadow%3A%200%2020px%2040px%20rgba(0%2C0%2C0%2C0.5)%3B%0A%20%20%20%20%20%20padding%3A%2030px%3B%0A%20%20%20%20%20%20min-height%3A%20480px%3B%0A%20%20%20%20%20%20display%3A%20flex%3B%0A%20%20%20%20%20%20flex-direction%3A%20column%3B%0A%20%20%20%20%20%20justify-content%3A%20space-between%3B%0A%20%20%20%20%20%20position%3A%20relative%3B%0A%20%20%20%20%7D%0A%20%20%20%20.screen%20%7B%0A%20%20%20%20%20%20display%3A%20none%3B%0A%20%20%20%20%20%20animation%3A%20fadeIn%200.4s%20ease%20forwards%3B%0A%20%20%20%20%7D%0A%20%20%20%20.screen.active%20%7B%0A%20%20%20%20%20%20display%3A%20flex%3B%0A%20%20%20%20%20%20flex-direction%3A%20column%3B%0A%20%20%20%20%20%20gap%3A%2020px%3B%0A%20%20%20%20%7D%0A%20%20%20%20%40keyframes%20fadeIn%20%7B%0A%20%20%20%20%20%20from%20%7B%20opacity%3A%200%3B%20transform%3A%20translateY(10px)%3B%20%7D%0A%20%20%20%20%20%20to%20%7B%20opacity%3A%201%3B%20transform%3A%20translateY(0)%3B%20%7D%0A%20%20%20%20%7D%0A%20%20%20%20h1%2C%20h2%20%7B%0A%20%20%20%20%20%20font-weight%3A%20700%3B%0A%20%20%20%20%20%20background%3A%20linear-gradient(to%20right%2C%20%23fff%2C%20%23c7d2fe)%3B%0A%20%20%20%20%20%20-webkit-background-clip%3A%20text%3B%0A%20%20%20%20%20%20-webkit-text-fill-color%3A%20transparent%3B%0A%20%20%20%20%7D%0A%20%20%20%20.title-large%20%7B%20font-size%3A%202rem%3B%20text-align%3A%20center%3B%20margin-bottom%3A%2010px%3B%20%7D%0A%20%20%20%20.title-mid%20%7B%20font-size%3A%201.5rem%3B%20display%3A%20flex%3B%20align-items%3A%20center%3B%20gap%3A%2010px%3B%20%7D%0A%20%20%20%20.desc%20%7B%20color%3A%20var(--text-muted)%3B%20line-height%3A%201.6%3B%20font-size%3A%200.95rem%3B%20%7D%0A%20%20%20%20.btn-action%20%7B%0A%20%20%20%20%20%20background%3A%20linear-gradient(135deg%2C%20var(--primary)%2C%20%238b5cf6)%3B%0A%20%20%20%20%20%20border%3A%20none%3B%0A%20%20%20%20%20%20color%3A%20%23fff%3B%0A%20%20%20%20%20%20padding%3A%2014px%2028px%3B%0A%20%20%20%20%20%20font-size%3A%201.05rem%3B%0A%20%20%20%20%20%20font-weight%3A%20600%3B%0A%20%20%20%20%20%20border-radius%3A%2010px%3B%0A%20%20%20%20%20%20cursor%3A%20pointer%3B%0A%20%20%20%20%20%20transition%3A%20all%200.2s%3B%0A%20%20%20%20%20%20box-shadow%3A%200%204px%2012px%20rgba(99%2C%20102%2C%20241%2C%200.3)%3B%0A%20%20%20%20%20%20text-align%3A%20center%3B%0A%20%20%20%20%7D%0A%20%20%20%20.btn-action%3Ahover%20%7B%0A%20%20%20%20%20%20transform%3A%20translateY(-2px)%3B%0A%20%20%20%20%20%20box-shadow%3A%200%206px%2016px%20rgba(99%2C%20102%2C%20241%2C%200.4)%3B%0A%20%20%20%20%7D%0A%20%20%20%20.input-group%20%7B%0A%20%20%20%20%20%20display%3A%20flex%3B%0A%20%20%20%20%20%20flex-direction%3A%20column%3B%0A%20%20%20%20%20%20gap%3A%208px%3B%0A%20%20%20%20%20%20margin%3A%2020px%200%3B%0A%20%20%20%20%7D%0A%20%20%20%20.form-input%20%7B%0A%20%20%20%20%20%20background%3A%20rgba(0%2C0%2C0%2C0.3)%3B%0A%20%20%20%20%20%20border%3A%201px%20solid%20var(--border)%3B%0A%20%20%20%20%20%20border-radius%3A%208px%3B%0A%20%20%20%20%20%20padding%3A%2014px%3B%0A%20%20%20%20%20%20color%3A%20%23fff%3B%0A%20%20%20%20%20%20font-size%3A%201.05rem%3B%0A%20%20%20%20%20%20outline%3A%20none%3B%0A%20%20%20%20%20%20transition%3A%20border-color%200.2s%3B%0A%20%20%20%20%7D%0A%20%20%20%20.form-input%3Afocus%20%7B%20border-color%3A%20var(--primary)%3B%20%7D%0A%20%20%20%20%0A%20%20%20%20.steps-indicator%20%7B%0A%20%20%20%20%20%20display%3A%20flex%3B%0A%20%20%20%20%20%20justify-content%3A%20space-between%3B%0A%20%20%20%20%20%20margin-bottom%3A%2024px%3B%0A%20%20%20%20%20%20position%3A%20relative%3B%0A%20%20%20%20%7D%0A%20%20%20%20.steps-indicator%3A%3Abefore%20%7B%0A%20%20%20%20%20%20content%3A%20''%3B%0A%20%20%20%20%20%20position%3A%20absolute%3B%0A%20%20%20%20%20%20top%3A%2015px%3B%0A%20%20%20%20%20%20left%3A%2010%25%3B%0A%20%20%20%20%20%20right%3A%2010%25%3B%0A%20%20%20%20%20%20height%3A%202px%3B%0A%20%20%20%20%20%20background%3A%20var(--border)%3B%0A%20%20%20%20%20%20z-index%3A%201%3B%0A%20%20%20%20%7D%0A%20%20%20%20.step-dot%20%7B%0A%20%20%20%20%20%20width%3A%2032px%3B%0A%20%20%20%20%20%20height%3A%2032px%3B%0A%20%20%20%20%20%20background%3A%20%23142036%3B%0A%20%20%20%20%20%20border%3A%202px%20solid%20var(--border)%3B%0A%20%20%20%20%20%20border-radius%3A%2050%25%3B%0A%20%20%20%20%20%20display%3A%20flex%3B%0A%20%20%20%20%20%20align-items%3A%20center%3B%0A%20%20%20%20%20%20justify-content%3A%20center%3B%0A%20%20%20%20%20%20font-size%3A%200.85rem%3B%0A%20%20%20%20%20%20font-weight%3A%20700%3B%0A%20%20%20%20%20%20z-index%3A%202%3B%0A%20%20%20%20%20%20transition%3A%20all%200.3s%3B%0A%20%20%20%20%7D%0A%20%20%20%20.step-dot.active%20%7B%0A%20%20%20%20%20%20border-color%3A%20var(--primary)%3B%0A%20%20%20%20%20%20background%3A%20var(--primary)%3B%0A%20%20%20%20%20%20box-shadow%3A%200%200%2012px%20rgba(99%2C%20102%2C%20241%2C%200.5)%3B%0A%20%20%20%20%7D%0A%20%20%20%20.step-dot.done%20%7B%0A%20%20%20%20%20%20border-color%3A%20var(--success)%3B%0A%20%20%20%20%20%20background%3A%20var(--success)%3B%0A%20%20%20%20%7D%0A%0A%20%20%20%20.scenario-card%20%7B%0A%20%20%20%20%20%20background%3A%20var(--surface-card)%3B%0A%20%20%20%20%20%20border%3A%201px%20solid%20var(--border)%3B%0A%20%20%20%20%20%20border-radius%3A%2012px%3B%0A%20%20%20%20%20%20padding%3A%2024px%3B%0A%20%20%20%20%20%20display%3A%20flex%3B%0A%20%20%20%20%20%20flex-direction%3A%20column%3B%0A%20%20%20%20%20%20gap%3A%2012px%3B%0A%20%20%20%20%7D%0A%20%20%20%20.option-group%20%7B%0A%20%20%20%20%20%20display%3A%20flex%3B%0A%20%20%20%20%20%20flex-direction%3A%20column%3B%0A%20%20%20%20%20%20gap%3A%2012px%3B%0A%20%20%20%20%20%20margin-top%3A%2010px%3B%0A%20%20%20%20%7D%0A%20%20%20%20.option-btn%20%7B%0A%20%20%20%20%20%20background%3A%20rgba(255%2C255%2C255%2C0.03)%3B%0A%20%20%20%20%20%20border%3A%201px%20solid%20var(--border)%3B%0A%20%20%20%20%20%20border-radius%3A%2010px%3B%0A%20%20%20%20%20%20padding%3A%2016px%3B%0A%20%20%20%20%20%20text-align%3A%20left%3B%0A%20%20%20%20%20%20cursor%3A%20pointer%3B%0A%20%20%20%20%20%20transition%3A%20all%200.2s%3B%0A%20%20%20%20%20%20display%3A%20flex%3B%0A%20%20%20%20%20%20align-items%3A%20flex-start%3B%0A%20%20%20%20%20%20gap%3A%2012px%3B%0A%20%20%20%20%20%20color%3A%20var(--text)%3B%0A%20%20%20%20%20%20font-size%3A%200.95rem%3B%0A%20%20%20%20%20%20line-height%3A%201.5%3B%0A%20%20%20%20%7D%0A%20%20%20%20.option-btn%3Ahover%3Anot(.disabled)%20%7B%0A%20%20%20%20%20%20background%3A%20rgba(255%2C255%2C255%2C0.07)%3B%0A%20%20%20%20%20%20border-color%3A%20rgba(255%2C255%2C255%2C0.2)%3B%0A%20%20%20%20%7D%0A%20%20%20%20.option-btn.correct%20%7B%0A%20%20%20%20%20%20background%3A%20var(--success-bg)%3B%0A%20%20%20%20%20%20border-color%3A%20var(--success)%3B%0A%20%20%20%20%20%20color%3A%20%23a7f3d0%3B%0A%20%20%20%20%7D%0A%20%20%20%20.option-btn.incorrect%20%7B%0A%20%20%20%20%20%20background%3A%20var(--error-bg)%3B%0A%20%20%20%20%20%20border-color%3A%20var(--error)%3B%0A%20%20%20%20%20%20color%3A%20%23fecdd3%3B%0A%20%20%20%20%7D%0A%20%20%20%20.option-btn.disabled%20%7B%0A%20%20%20%20%20%20cursor%3A%20not-allowed%3B%0A%20%20%20%20%20%20opacity%3A%200.6%3B%0A%20%20%20%20%7D%0A%20%20%20%20.badge-icon%20%7B%0A%20%20%20%20%20%20font-size%3A%201.5rem%3B%0A%20%20%20%20%20%20min-width%3A%2030px%3B%0A%20%20%20%20%7D%0A%20%20%20%20.feedback-box%20%7B%0A%20%20%20%20%20%20margin-top%3A%2014px%3B%0A%20%20%20%20%20%20padding%3A%2014px%3B%0A%20%20%20%20%20%20border-radius%3A%208px%3B%0A%20%20%20%20%20%20display%3A%20none%3B%0A%20%20%20%20%20%20font-size%3A%200.9rem%3B%0A%20%20%20%20%20%20line-height%3A%201.6%3B%0A%20%20%20%20%20%20animation%3A%20fadeIn%200.3s%3B%0A%20%20%20%20%7D%0A%20%20%20%20.feedback-box.correct%20%7B%20background%3A%20rgba(16%2C%20185%2C%20129%2C%200.15)%3B%20border-left%3A%204px%20solid%20var(--success)%3B%20color%3A%20%23a7f3d0%3B%20%7D%0A%20%20%20%20.feedback-box.incorrect%20%7B%20background%3A%20rgba(244%2C%2063%2C%2094%2C%200.15)%3B%20border-left%3A%204px%20solid%20var(--error)%3B%20color%3A%20%23fecdd3%3B%20%7D%0A%20%20%20%20%0A%20%20%20%20.score-badge%20%7B%0A%20%20%20%20%20%20display%3A%20inline-block%3B%0A%20%20%20%20%20%20padding%3A%204px%2010px%3B%0A%20%20%20%20%20%20border-radius%3A%2012px%3B%0A%20%20%20%20%20%20font-size%3A%200.8rem%3B%0A%20%20%20%20%20%20font-weight%3A%20600%3B%0A%20%20%20%20%20%20align-self%3A%20flex-start%3B%0A%20%20%20%20%7D%0A%20%20%20%20.score-badge.perfect%20%7B%20background%3A%20rgba(16%2C185%2C129%2C0.15)%3B%20color%3A%20var(--success)%3B%20%7D%0A%20%20%20%20%0A%20%20%20%20.result-summary%20%7B%0A%20%20%20%20%20%20text-align%3A%20center%3B%0A%20%20%20%20%20%20display%3A%20flex%3B%0A%20%20%20%20%20%20flex-direction%3A%20column%3B%0A%20%20%20%20%20%20align-items%3A%20center%3B%0A%20%20%20%20%20%20gap%3A%2015px%3B%0A%20%20%20%20%7D%0A%20%20%20%20.score-value%20%7B%0A%20%20%20%20%20%20font-size%3A%203rem%3B%0A%20%20%20%20%20%20font-weight%3A%20800%3B%0A%20%20%20%20%20%20color%3A%20var(--success)%3B%0A%20%20%20%20%20%20margin%3A%2010px%200%3B%0A%20%20%20%20%7D%0A%20%20%20%20.badge-unlocked%20%7B%0A%20%20%20%20%20%20font-size%3A%201.2rem%3B%0A%20%20%20%20%20%20color%3A%20%23fbbf24%3B%0A%20%20%20%20%20%20background%3A%20rgba(251%2C191%2C36%2C0.1)%3B%0A%20%20%20%20%20%20border%3A%201px%20dashed%20%23fbbf24%3B%0A%20%20%20%20%20%20padding%3A%208px%2016px%3B%0A%20%20%20%20%20%20border-radius%3A%2020px%3B%0A%20%20%20%20%20%20margin-bottom%3A%2010px%3B%0A%20%20%20%20%7D%0A%20%20%3C%2Fstyle%3E%0A%3C%2Fhead%3E%0A%3Cbody%3E%0A%0A%20%20%3Cdiv%20class%3D%22game-container%22%3E%0A%20%20%20%20%0A%20%20%20%20%3Cdiv%20class%3D%22screen%20active%22%20id%3D%22screen-welcome%22%3E%0A%20%20%20%20%20%20%3Cdiv%20style%3D%22text-align%3A%20center%3B%20margin-bottom%3A%2020px%3B%22%3E%0A%20%20%20%20%20%20%20%20%3Cdiv%20style%3D%22font-size%3A%204rem%3B%22%3E%F0%9F%8E%AE%3C%2Fdiv%3E%0A%20%20%20%20%20%20%20%20%3Ch1%20class%3D%22title-large%22%3E%E4%B8%80%E6%97%A5%20SOP%20%E8%81%B7%E4%BA%BA%E6%8C%91%E6%88%B0%3C%2Fh1%3E%0A%20%20%20%20%20%20%20%20%3Cp%20class%3D%22desc%22%3E%E6%AD%A1%E8%BF%8E%E4%BE%86%E5%88%B0%E3%80%8A__TRAINING_TITLE__%E3%80%8B%E5%90%88%E8%A6%8F%E6%83%85%E5%A2%83%E6%A8%A1%E6%93%AC%E9%97%96%E9%97%9C%E6%8C%91%E6%88%B0%EF%BC%81%E6%9C%AC%E6%B8%AC%E9%A9%97%E5%B0%87%E4%BB%A5%E6%93%AC%E7%9C%9F%E5%B7%A5%E4%BD%9C%E6%83%85%E5%A2%83%E6%B8%AC%E8%A9%A6%E6%82%A8%E5%B0%8D%E6%A8%99%E6%BA%96%E4%BD%9C%E6%A5%AD%E8%A6%8F%E7%AB%A0%E7%9A%84%E4%BA%86%E8%A7%A3%E7%A8%8B%E5%BA%A6%E3%80%82%3C%2Fp%3E%0A%20%20%20%20%20%20%3C%2Fdiv%3E%0A%20%20%20%20%20%20%0A%20%20%20%20%20%20%3Cdiv%20class%3D%22input-group%22%3E%0A%20%20%20%20%20%20%20%20%3Clabel%20style%3D%22font-weight%3A%20600%3B%20color%3A%20var(--text-muted)%3B%20font-size%3A%200.9rem%3B%22%3E%E8%AB%8B%E8%BC%B8%E5%85%A5%E6%82%A8%E7%9A%84%E5%A7%93%E5%90%8D%E4%BB%A5%E9%96%8B%E5%A7%8B%E6%8C%91%E6%88%B0%EF%BC%9A%3C%2Flabel%3E%0A%20%20%20%20%20%20%20%20%3Cinput%20type%3D%22text%22%20class%3D%22form-input%22%20id%3D%22user-name%22%20placeholder%3D%22%E4%BE%8B%E5%A6%82%EF%BC%9A%E9%99%B3%E5%A4%A7%E6%98%8E%22%20maxlength%3D%2215%22%20oninput%3D%22toggleStartBtn()%22%3E%0A%20%20%20%20%20%20%3C%2Fdiv%3E%0A%20%20%20%20%20%20%0A%20%20%20%20%20%20%3Cbutton%20class%3D%22btn-action%22%20id%3D%22btn-start-game%22%20onclick%3D%22startGame()%22%20disabled%3E%F0%9F%8E%AE%20%E9%96%8B%E5%A7%8B%E6%A8%A1%E6%93%AC%E6%8C%91%E6%88%B0%3C%2Fbutton%3E%0A%20%20%20%20%3C%2Fdiv%3E%0A%0A%20%20%20%20%3Cdiv%20class%3D%22screen%22%20id%3D%22screen-game%22%3E%0A%20%20%20%20%20%20%3Cdiv%20class%3D%22steps-indicator%22%20id%3D%22game-steps-indicator%22%3E%0A%20%20%20%20%20%20%3C%2Fdiv%3E%0A%0A%20%20%20%20%20%20%3Cdiv%20class%3D%22scenario-card%22%3E%0A%20%20%20%20%20%20%20%20%3Ch2%20class%3D%22title-mid%22%20id%3D%22sc-title%22%3E%E9%97%9C%E5%8D%A1%E8%BC%89%E5%85%A5%E4%B8%AD...%3C%2Fh2%3E%0A%20%20%20%20%20%20%20%20%3Cp%20class%3D%22desc%22%20id%3D%22sc-desc%22%3ESOP%20%E8%A6%8F%E7%AF%84%E5%AD%B8%E7%BF%92%E5%85%A7%E5%AE%B9...%3C%2Fp%3E%0A%20%20%20%20%20%20%20%20%0A%20%20%20%20%20%20%20%20%3Cdiv%20style%3D%22border-top%3A%201px%20solid%20var(--border)%3B%20margin%3A%2010px%200%3B%22%3E%3C%2Fdiv%3E%0A%20%20%20%20%20%20%20%20%0A%20%20%20%20%20%20%20%20%3Cp%20style%3D%22font-weight%3A%20700%3B%20font-size%3A%200.95rem%3B%20color%3A%20%23fff%3B%22%20id%3D%22sc-challenge%22%3E%E6%83%85%E5%A2%83%E6%8C%91%E6%88%B0%E9%A1%8C...%3C%2Fp%3E%0A%20%20%20%20%20%20%20%20%0A%20%20%20%20%20%20%20%20%3Cdiv%20class%3D%22option-group%22%20id%3D%22sc-options%22%3E%0A%20%20%20%20%20%20%20%20%3C%2Fdiv%3E%0A%20%20%20%20%20%20%20%20%0A%20%20%20%20%20%20%20%20%3Cdiv%20class%3D%22feedback-box%22%20id%3D%22sc-feedback%22%3E%0A%20%20%20%20%20%20%20%20%3C%2Fdiv%3E%0A%20%20%20%20%20%20%3C%2Fdiv%3E%0A%0A%20%20%20%20%20%20%3Cbutton%20class%3D%22btn-action%22%20id%3D%22btn-next%22%20onclick%3D%22nextLevel()%22%20style%3D%22display%3A%20none%3B%20align-self%3A%20flex-end%3B%22%3E%E9%80%B2%E5%85%A5%E4%B8%8B%E4%B8%80%E9%97%9C%20%E2%9E%94%3C%2Fbutton%3E%0A%20%20%20%20%3C%2Fdiv%3E%0A%0A%20%20%20%20%3Cdiv%20class%3D%22screen%22%20id%3D%22screen-result%22%3E%0A%20%20%20%20%20%20%3Cdiv%20class%3D%22result-summary%22%3E%0A%20%20%20%20%20%20%20%20%3Cdiv%20style%3D%22font-size%3A%204rem%3B%22%3E%F0%9F%8F%86%3C%2Fdiv%3E%0A%20%20%20%20%20%20%20%20%3Ch2%3E%E4%B8%80%E6%97%A5%E6%8C%91%E6%88%B0%E5%AE%8C%E6%88%90%EF%BC%81%3C%2Fh2%3E%0A%20%20%20%20%20%20%20%20%3Cp%20class%3D%22desc%22%20id%3D%22res-name-label%22%3E%E6%81%AD%E5%96%9C%E5%90%8C%E4%BB%81%E5%AE%8C%E6%88%90%E9%97%96%E9%97%9C%3C%2Fp%3E%0A%20%20%20%20%20%20%20%20%3Cdiv%20class%3D%22score-value%22%20id%3D%22res-score%22%3E100%20%E5%88%86%3C%2Fdiv%3E%0A%20%20%20%20%20%20%20%20%3Cdiv%20class%3D%22badge-unlocked%22%20id%3D%22res-badge%22%3E%F0%9F%8E%96%EF%B8%8F%20SOP%E5%AE%88%E8%AD%B7%E8%80%85%3C%2Fdiv%3E%0A%20%20%20%20%20%20%20%20%3Cp%20class%3D%22desc%22%20id%3D%22res-desc%22%3E%E5%90%88%E8%A6%8F%E6%8C%91%E6%88%B0%E7%B5%90%E6%9D%9F%EF%BC%8C%E7%B3%BB%E7%B5%B1%E6%AD%A3%E5%9C%A8%E8%87%AA%E5%8B%95%E4%BF%9D%E5%AD%98%E4%B8%A6%E5%90%8C%E6%AD%A5%E6%82%A8%E7%9A%84%E4%BD%9C%E7%AD%94%E7%B5%90%E6%9E%9C...%3C%2Fp%3E%0A%20%20%20%20%20%20%3C%2Fdiv%3E%0A%0A%20%20%20%20%20%20%3Cdiv%20id%3D%22submit-status-box%22%20style%3D%22text-align%3A%20center%3B%20margin%3A%2020px%200%3B%20padding%3A%2014px%3B%20border-radius%3A%208px%3B%20font-weight%3A%20600%3B%20color%3A%20%23fbbf24%3B%20background%3A%20rgba(251%2C191%2C36%2C0.1)%3B%20border%3A%201px%20solid%20rgba(251%2C191%2C36%2C0.2)%3B%20animation%3A%20fadeIn%200.4s%3B%22%3E%0A%20%20%20%20%20%20%20%20%F0%9F%93%A4%20%E6%AD%A3%E5%9C%A8%E5%AF%AB%E5%85%A5%E6%88%90%E7%B8%BE%E8%87%B3%E6%9C%AC%E6%A9%9F%20results.csv%EF%BC%8C%E8%AB%8B%E5%8B%BF%E9%97%9C%E9%96%89%E7%B6%B2%E9%A0%81...%0A%20%20%20%20%20%20%3C%2Fdiv%3E%0A%20%20%20%20%3C%2Fdiv%3E%0A%0A%20%20%3C%2Fdiv%3E%0A%0A%20%20%3Cscript%3E%0A%20%20%20%20let%20userName%20%3D%20%22%22%3B%0A%20%20%20%20let%20curLevel%20%3D%200%3B%0A%20%20%20%20let%20score%20%3D%200%3B%0A%20%20%20%20let%20answersRecord%20%3D%20%5B%5D%3B%0A%20%20%20%20let%20speechSynth%20%3D%20window.speechSynthesis%3B%0A%20%20%20%20let%20currentUtterance%20%3D%20null%3B%0A%0A%20%20%20%20const%20LEVELS%20%3D%20__QUIZ_JSON__%3B%0A%0A%20%20%20%20function%20toggleStartBtn()%20%7B%0A%20%20%20%20%20%20const%20nameVal%20%3D%20document.getElementById(%22user-name%22).value.trim()%3B%0A%20%20%20%20%20%20document.getElementById(%22btn-start-game%22).disabled%20%3D%20nameVal.length%20%3C%201%3B%0A%20%20%20%20%7D%0A%0A%20%20%20%20function%20playSuccessSound()%20%7B%0A%20%20%20%20%20%20try%20%7B%0A%20%20%20%20%20%20%20%20const%20ctx%20%3D%20new%20(window.AudioContext%20%7C%7C%20window.webkitAudioContext)()%3B%0A%20%20%20%20%20%20%20%20const%20osc%20%3D%20ctx.createOscillator()%3B%0A%20%20%20%20%20%20%20%20const%20gain%20%3D%20ctx.createGain()%3B%0A%20%20%20%20%20%20%20%20osc.connect(gain)%3B%0A%20%20%20%20%20%20%20%20gain.connect(ctx.destination)%3B%0A%20%20%20%20%20%20%20%20osc.type%20%3D%20'triangle'%3B%0A%20%20%20%20%20%20%20%20osc.frequency.setValueAtTime(523.25%2C%20ctx.currentTime)%3B%0A%20%20%20%20%20%20%20%20osc.frequency.setValueAtTime(659.25%2C%20ctx.currentTime%20%2B%200.1)%3B%0A%20%20%20%20%20%20%20%20osc.frequency.setValueAtTime(783.99%2C%20ctx.currentTime%20%2B%200.2)%3B%0A%20%20%20%20%20%20%20%20gain.gain.setValueAtTime(0.1%2C%20ctx.currentTime)%3B%0A%20%20%20%20%20%20%20%20gain.gain.exponentialRampToValueAtTime(0.01%2C%20ctx.currentTime%20%2B%200.4)%3B%0A%20%20%20%20%20%20%20%20osc.start()%3B%0A%20%20%20%20%20%20%20%20osc.stop(ctx.currentTime%20%2B%200.4)%3B%0A%20%20%20%20%20%20%7D%20catch%20(e)%20%7B%7D%0A%20%20%20%20%7D%0A%0A%20%20%20%20function%20playFailSound()%20%7B%0A%20%20%20%20%20%20try%20%7B%0A%20%20%20%20%20%20%20%20const%20ctx%20%3D%20new%20(window.AudioContext%20%7C%7C%20window.webkitAudioContext)()%3B%0A%20%20%20%20%20%20%20%20const%20osc%20%3D%20ctx.createOscillator()%3B%0A%20%20%20%20%20%20%20%20const%20gain%20%3D%20ctx.createGain()%3B%0A%20%20%20%20%20%20%20%20osc.connect(gain)%3B%0A%20%20%20%20%20%20%20%20gain.connect(ctx.destination)%3B%0A%20%20%20%20%20%20%20%20osc.type%20%3D%20'sawtooth'%3B%0A%20%20%20%20%20%20%20%20osc.frequency.setValueAtTime(220%2C%20ctx.currentTime)%3B%0A%20%20%20%20%20%20%20%20osc.frequency.linearRampToValueAtTime(110%2C%20ctx.currentTime%20%2B%200.3)%3B%0A%20%20%20%20%20%20%20%20gain.gain.setValueAtTime(0.1%2C%20ctx.currentTime)%3B%0A%20%20%20%20%20%20%20%20gain.gain.exponentialRampToValueAtTime(0.01%2C%20ctx.currentTime%20%2B%200.35)%3B%0A%20%20%20%20%20%20%20%20osc.start()%3B%0A%20%20%20%20%20%20%20%20osc.stop(ctx.currentTime%20%2B%200.35)%3B%0A%20%20%20%20%20%20%7D%20catch%20(e)%20%7B%7D%0A%20%20%20%20%7D%0A%0A%20%20%20%20function%20speakText(text)%20%7B%0A%20%20%20%20%20%20if%20(speechSynth)%20%7B%0A%20%20%20%20%20%20%20%20speechSynth.cancel()%3B%0A%20%20%20%20%20%20%20%20currentUtterance%20%3D%20new%20SpeechSynthesisUtterance(text)%3B%0A%20%20%20%20%20%20%20%20const%20voices%20%3D%20speechSynth.getVoices()%3B%0A%20%20%20%20%20%20%20%20const%20zhVoice%20%3D%20voices.find(v%20%3D%3E%20v.lang.includes(%22zh-TW%22)%20%7C%7C%20v.lang.includes(%22zh-CN%22)%20%7C%7C%20v.lang.includes(%22zh%22))%3B%0A%20%20%20%20%20%20%20%20if%20(zhVoice)%20currentUtterance.voice%20%3D%20zhVoice%3B%0A%20%20%20%20%20%20%20%20speechSynth.speak(currentUtterance)%3B%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%0A%20%20%20%20function%20startGame()%20%7B%0A%20%20%20%20%20%20userName%20%3D%20document.getElementById(%22user-name%22).value.trim()%3B%0A%20%20%20%20%20%20document.getElementById(%22screen-welcome%22).classList.remove(%22active%22)%3B%0A%20%20%20%20%20%20document.getElementById(%22screen-game%22).classList.add(%22active%22)%3B%0A%20%20%20%20%20%20%0A%20%20%20%20%20%20const%20stepIndicator%20%3D%20document.getElementById(%22game-steps-indicator%22)%3B%0A%20%20%20%20%20%20stepIndicator.innerHTML%20%3D%20%22%22%3B%0A%20%20%20%20%20%20for(let%20i%3D0%3B%20i%3CLEVELS.length%3B%20i%2B%2B)%20%7B%0A%20%20%20%20%20%20%20%20const%20dot%20%3D%20document.createElement(%22div%22)%3B%0A%20%20%20%20%20%20%20%20dot.className%20%3D%20i%20%3D%3D%3D%200%20%3F%20%22step-dot%20active%22%20%3A%20%22step-dot%22%3B%0A%20%20%20%20%20%20%20%20dot.id%20%3D%20%22step-%22%20%2B%20i%3B%0A%20%20%20%20%20%20%20%20dot.textContent%20%3D%20i%20%2B%201%3B%0A%20%20%20%20%20%20%20%20stepIndicator.appendChild(dot)%3B%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%0A%20%20%20%20%20%20loadLevel()%3B%0A%20%20%20%20%7D%0A%0A%20%20%20%20function%20loadLevel()%20%7B%0A%20%20%20%20%20%20const%20lv%20%3D%20LEVELS%5BcurLevel%5D%3B%0A%20%20%20%20%20%20%0A%20%20%20%20%20%20for(let%20i%3D0%3B%20i%3CLEVELS.length%3B%20i%2B%2B)%20%7B%0A%20%20%20%20%20%20%20%20const%20dot%20%3D%20document.getElementById(%22step-%22%20%2B%20i)%3B%0A%20%20%20%20%20%20%20%20if%20(dot)%20%7B%0A%20%20%20%20%20%20%20%20%20%20if(i%20%3C%20curLevel)%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20dot.className%20%3D%20%22step-dot%20done%22%3B%0A%20%20%20%20%20%20%20%20%20%20%7D%20else%20if%20(i%20%3D%3D%3D%20curLevel)%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20dot.className%20%3D%20%22step-dot%20active%22%3B%0A%20%20%20%20%20%20%20%20%20%20%7D%20else%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20dot.className%20%3D%20%22step-dot%22%3B%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%7D%0A%0A%20%20%20%20%20%20document.getElementById(%22sc-title%22).textContent%20%3D%20lv.title%3B%0A%20%20%20%20%20%20document.getElementById(%22sc-desc%22).textContent%20%3D%20lv.desc%3B%0A%20%20%20%20%20%20document.getElementById(%22sc-challenge%22).textContent%20%3D%20lv.challenge%3B%0A%20%20%20%20%20%20%0A%20%20%20%20%20%20const%20optContainer%20%3D%20document.getElementById(%22sc-options%22)%3B%0A%20%20%20%20%20%20optContainer.innerHTML%20%3D%20%22%22%3B%0A%20%20%20%20%20%20%0A%20%20%20%20%20%20lv.options.forEach((opt%2C%20idx)%20%3D%3E%20%7B%0A%20%20%20%20%20%20%20%20const%20btn%20%3D%20document.createElement(%22button%22)%3B%0A%20%20%20%20%20%20%20%20btn.className%20%3D%20%22option-btn%22%3B%0A%20%20%20%20%20%20%20%20btn.innerHTML%20%3D%20%5C%60%3Cspan%20class%3D%22badge-icon%22%3E%5C%24%7Bidx%20%3D%3D%3D%200%20%3F%20'A'%20%3A%20idx%20%3D%3D%3D%201%20%3F%20'B'%20%3A%20idx%20%3D%3D%3D%202%20%3F%20'C'%20%3A%20'D'%7D%3C%2Fspan%3E%20%3Cspan%3E%5C%24%7Bopt.text%7D%3C%2Fspan%3E%5C%60%3B%0A%20%20%20%20%20%20%20%20btn.onclick%20%3D%20()%20%3D%3E%20selectOption(idx%2C%20btn)%3B%0A%20%20%20%20%20%20%20%20optContainer.appendChild(btn)%3B%0A%20%20%20%20%20%20%7D)%3B%0A%0A%20%20%20%20%20%20document.getElementById(%22sc-feedback%22).style.display%20%3D%20%22none%22%3B%0A%20%20%20%20%20%20document.getElementById(%22btn-next%22).style.display%20%3D%20%22none%22%3B%0A%20%20%20%20%20%20%0A%20%20%20%20%20%20speakText(lv.title%20%2B%20%22%E3%80%82%22%20%2B%20lv.desc%20%2B%20lv.challenge)%3B%0A%20%20%20%20%7D%0A%0A%20%20%20%20function%20selectOption(idx%2C%20btn)%20%7B%0A%20%20%20%20%20%20const%20lv%20%3D%20LEVELS%5BcurLevel%5D%3B%0A%20%20%20%20%20%20const%20opt%20%3D%20lv.options%5Bidx%5D%3B%0A%20%20%20%20%20%20%0A%20%20%20%20%20%20const%20allBtns%20%3D%20document.querySelectorAll(%22.option-btn%22)%3B%0A%20%20%20%20%20%20allBtns.forEach(b%20%3D%3E%20b.classList.add(%22disabled%22))%3B%0A%0A%20%20%20%20%20%20const%20feedbackBox%20%3D%20document.getElementById(%22sc-feedback%22)%3B%0A%20%20%20%20%20%20%0A%20%20%20%20%20%20const%20optLabel%20%3D%20idx%20%3D%3D%3D%200%20%3F%20%22A%22%20%3A%20idx%20%3D%3D%3D%201%20%3F%20%22B%22%20%3A%20idx%20%3D%3D%3D%202%20%3F%20%22C%22%20%3A%20%22D%22%3B%0A%20%20%20%20%20%20answersRecord.push(%7B%0A%20%20%20%20%20%20%20%20num%3A%20curLevel%20%2B%201%2C%0A%20%20%20%20%20%20%20%20question%3A%20lv.challenge%2C%0A%20%20%20%20%20%20%20%20selected%3A%20optLabel%2C%0A%20%20%20%20%20%20%20%20isCorrect%3A%20opt.correct%0A%20%20%20%20%20%20%7D)%3B%0A%0A%20%20%20%20%20%20if%20(opt.correct)%20%7B%0A%20%20%20%20%20%20%20%20btn.classList.add(%22correct%22)%3B%0A%20%20%20%20%20%20%20%20feedbackBox.className%20%3D%20%22feedback-box%20correct%22%3B%0A%20%20%20%20%20%20%20%20feedbackBox.innerHTML%20%3D%20%22%3Cstrong%3E%F0%9F%8E%89%20%E5%9B%9E%E7%AD%94%E6%AD%A3%E7%A2%BA%EF%BC%81%3C%2Fstrong%3E%20%22%20%2B%20opt.feedback%3B%0A%20%20%20%20%20%20%20%20score%20%2B%3D%20Math.round(100%20%2F%20LEVELS.length)%3B%0A%20%20%20%20%20%20%20%20playSuccessSound()%3B%0A%20%20%20%20%20%20%7D%20else%20%7B%0A%20%20%20%20%20%20%20%20btn.classList.add(%22incorrect%22)%3B%0A%20%20%20%20%20%20%20%20feedbackBox.className%20%3D%20%22feedback-box%20incorrect%22%3B%0A%20%20%20%20%20%20%20%20feedbackBox.innerHTML%20%3D%20%22%3Cstrong%3E%E2%9D%8C%20%E9%81%B8%E6%93%87%E6%96%B9%E6%A1%88%E4%B8%8D%E5%90%88%E8%A6%8F%EF%BC%81%3C%2Fstrong%3E%20%22%20%2B%20opt.feedback%3B%0A%20%20%20%20%20%20%20%20playFailSound()%3B%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%0A%20%20%20%20%20%20feedbackBox.style.display%20%3D%20%22block%22%3B%0A%20%20%20%20%20%20document.getElementById(%22btn-next%22).style.display%20%3D%20%22block%22%3B%0A%20%20%20%20%20%20%0A%20%20%20%20%20%20speakText(opt.feedback)%3B%0A%20%20%20%20%7D%0A%0A%20%20%20%20function%20nextLevel()%20%7B%0A%20%20%20%20%20%20if%20(speechSynth)%20speechSynth.cancel()%3B%0A%20%20%20%20%20%20curLevel%2B%2B%3B%0A%20%20%20%20%20%20if%20(curLevel%20%3C%20LEVELS.length)%20%7B%0A%20%20%20%20%20%20%20%20loadLevel()%3B%0A%20%20%20%20%20%20%7D%20else%20%7B%0A%20%20%20%20%20%20%20%20if%20(score%20%3E%20100%20%7C%7C%20(score%20%3E%3D%2098%20%26%26%20score%20%3C%3D%20100))%20%7B%20score%20%3D%20100%3B%20%7D%0A%20%20%20%20%20%20%20%20showResults()%3B%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%0A%20%20%20%20function%20showResults()%20%7B%0A%20%20%20%20%20%20document.getElementById(%22screen-game%22).classList.remove(%22active%22)%3B%0A%20%20%20%20%20%20document.getElementById(%22screen-result%22).classList.add(%22active%22)%3B%0A%20%20%20%20%20%20%0A%20%20%20%20%20%20document.getElementById(%22res-name-label%22).textContent%20%3D%20%22%F0%9F%8F%86%20%E6%81%AD%E5%96%9C%E5%90%8C%E4%BB%81%20%22%20%2B%20userName%20%2B%20%22%20%E9%A0%86%E5%88%A9%E5%AE%8C%E6%88%90%E9%97%96%E9%97%9C%EF%BC%81%22%3B%0A%20%20%20%20%20%20document.getElementById(%22res-score%22).textContent%20%3D%20score%20%2B%20%22%20%E5%88%86%22%3B%0A%20%20%20%20%20%20%0A%20%20%20%20%20%20const%20badge%20%3D%20document.getElementById(%22res-badge%22)%3B%0A%20%20%20%20%20%20if%20(score%20%3D%3D%3D%20100)%20%7B%0A%20%20%20%20%20%20%20%20badge.textContent%20%3D%20%22%F0%9F%8E%96%EF%B8%8F%20SOP%20%E5%AE%8C%E7%BE%8E%E5%AE%88%E8%AD%B7%E5%B0%88%E5%AE%B6%20(100%E5%88%86)%22%3B%0A%20%20%20%20%20%20%20%20badge.style.borderColor%20%3D%20%22%23fbbf24%22%3B%0A%20%20%20%20%20%20%20%20badge.style.color%20%3D%20%22%23fbbf24%22%3B%0A%20%20%20%20%20%20%7D%20else%20if%20(score%20%3E%3D%2075)%20%7B%0A%20%20%20%20%20%20%20%20badge.textContent%20%3D%20%22%F0%9F%8F%85%20%E5%84%AA%E7%A7%80%E5%AD%B8%E5%93%A1%22%3B%0A%20%20%20%20%20%20%20%20badge.style.borderColor%20%3D%20%22%236366f1%22%3B%0A%20%20%20%20%20%20%20%20badge.style.color%20%3D%20%22%23818cf8%22%3B%0A%20%20%20%20%20%20%7D%20else%20%7B%0A%20%20%20%20%20%20%20%20badge.textContent%20%3D%20%22%F0%9F%A5%88%20%E7%B9%BC%E7%BA%8C%E5%8A%A0%E6%B2%B9%22%3B%0A%20%20%20%20%20%20%20%20badge.style.borderColor%20%3D%20%22%239ca3af%22%3B%0A%20%20%20%20%20%20%20%20badge.style.color%20%3D%20%22%239ca3af%22%3B%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%0A%20%20%20%20%20%20speakText(%22%E6%81%AD%E5%96%9C%E5%AE%8C%E6%88%90%E6%8C%91%E6%88%B0%EF%BC%81%E6%82%A8%E7%9A%84%E5%BE%97%E5%88%86%E6%98%AF%EF%BC%8C%22%20%2B%20score%20%2B%20%22%E5%88%86%EF%BC%81%22)%3B%0A%20%20%20%20%20%20%0A%20%20%20%20%20%20submitGameScore()%3B%0A%20%20%20%20%7D%0A%0A%20%20%20%20function%20submitGameScore()%20%7B%0A%20%20%20%20%20%20const%20payload%20%3D%20%7B%0A%20%20%20%20%20%20%20%20name%3A%20userName%2C%0A%20%20%20%20%20%20%20%20timestamp%3A%20new%20Date().toLocaleString(%22zh-TW%22%2C%20%7B%20timeZone%3A%20%22Asia%2FTaipei%22%20%7D)%2C%0A%20%20%20%20%20%20%20%20score%3A%20score%2C%0A%20%20%20%20%20%20%20%20correctCount%3A%20Math.round((score%20%2F%20100)%20*%20LEVELS.length)%2C%0A%20%20%20%20%20%20%20%20total%3A%20LEVELS.length%0A%20%20%20%20%20%20%7D%3B%0A%0A%20%20%20%20%20%20answersRecord.forEach((rec%2C%20idx)%20%3D%3E%20%7B%0A%20%20%20%20%20%20%20%20payload%5B%5C%60q%5C%24%7Bidx%20%2B%201%7D_question%5C%60%5D%20%3D%20rec.question%3B%0A%20%20%20%20%20%20%20%20payload%5B%5C%60q%5C%24%7Bidx%20%2B%201%7D_answer%5C%60%5D%20%3D%20%5C%60%E7%AD%94%3A%20%5C%24%7Brec.selected%7D%20(%5C%24%7Brec.isCorrect%20%3F%20%22%E5%B0%8D%22%20%3A%20%22%E9%8C%AF%22%7D)%5C%60%3B%0A%20%20%20%20%20%20%20%20payload%5B%5C%60q%5C%24%7Bidx%20%2B%201%7D%5C%60%5D%20%3D%20%5C%60%E7%AD%94%3A%20%5C%24%7Brec.selected%7D%20(%5Ctext%7B%E5%B0%8D%7D)%5C%60%3B%0A%20%20%20%20%20%20%7D)%3B%0A%0A%20%20%20%20%20%20const%20statusBox%20%3D%20document.getElementById(%22submit-status-box%22)%3B%0A%0A%20%20%20%20%20%20fetch(%22%2Fapi%2Fsubmit%22%2C%20%7B%0A%20%20%20%20%20%20%20%20method%3A%20%22POST%22%2C%0A%20%20%20%20%20%20%20%20headers%3A%20%7B%20%22Content-Type%22%3A%20%22application%2Fjson%22%20%7D%2C%0A%20%20%20%20%20%20%20%20body%3A%20JSON.stringify(payload)%0A%20%20%20%20%20%20%7D)%0A%20%20%20%20%20%20.then(res%20%3D%3E%20res.json())%0A%20%20%20%20%20%20.then(data%20%3D%3E%20%7B%0A%20%20%20%20%20%20%20%20console.log(%22%E6%9C%AC%E6%A9%9F%E4%BC%BA%E6%9C%8D%E5%99%A8%E5%84%B2%E5%AD%98%E6%88%90%E5%8A%9F%3A%22%2C%20data)%3B%0A%20%20%20%20%20%20%20%20statusBox.innerHTML%20%3D%20%22%E2%9C%85%20%E6%88%90%E7%B8%BE%E5%B7%B2%E6%88%90%E5%8A%9F%E5%AF%AB%E5%85%A5%E6%9C%AC%E6%A9%9F%20results.csv%EF%BC%81%E6%82%A8%E5%8F%AF%E4%BB%A5%E9%97%9C%E9%96%89%E6%AD%A4%E7%B6%B2%E9%A0%81%E3%80%82%22%3B%0A%20%20%20%20%20%20%20%20statusBox.style.color%20%3D%20%22var(--success)%22%3B%0A%20%20%20%20%20%20%20%20statusBox.style.background%20%3D%20%22rgba(16%2C%20185%2C%20129%2C%200.1)%22%3B%0A%20%20%20%20%20%20%20%20statusBox.style.borderColor%20%3D%20%22rgba(16%2C%20185%2C%20129%2C%200.2)%22%3B%0A%20%20%20%20%20%20%7D)%0A%20%20%20%20%20%20.catch(err%20%3D%3E%20%7B%0A%20%20%20%20%20%20%20%20console.warn(%22%E6%9C%AA%E9%80%A3%E6%8E%A5%E6%9C%AC%E6%A9%9F%E4%BC%BA%E6%9C%8D%E5%99%A8%E6%88%96%E5%82%B3%E9%80%81%E5%A4%B1%E6%95%97%20(%E5%96%AE%E6%A9%9F%E7%89%88%E6%A8%A1%E5%BC%8F)%3A%22%2C%20err)%3B%0A%20%20%20%20%20%20%20%20const%20cloudUrl%20%3D%20localStorage.getItem(%22training_cloud_url%22)%20%7C%7C%20%22%22%3B%0A%20%20%20%20%20%20%20%20if%20(cloudUrl)%20%7B%0A%20%20%20%20%20%20%20%20%20%20fetch(cloudUrl%2C%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20method%3A%20%22POST%22%2C%0A%20%20%20%20%20%20%20%20%20%20%20%20mode%3A%20%22no-cors%22%2C%0A%20%20%20%20%20%20%20%20%20%20%20%20headers%3A%20%7B%20%22Content-Type%22%3A%20%22application%2Fjson%22%20%7D%2C%0A%20%20%20%20%20%20%20%20%20%20%20%20body%3A%20JSON.stringify(payload)%0A%20%20%20%20%20%20%20%20%20%20%7D)%0A%20%20%20%20%20%20%20%20%20%20.then(()%20%3D%3E%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20statusBox.innerHTML%20%3D%20%22%E2%9C%85%20%E6%88%90%E7%B8%BE%E5%B7%B2%E9%80%81%E5%87%BA%E5%82%99%E4%BB%BD%E8%87%B3%E9%9B%B2%E7%AB%AF%E8%A9%A6%E7%AE%97%E8%A1%A8%EF%BC%81%E6%82%A8%E5%8F%AF%E4%BB%A5%E9%97%9C%E9%96%89%E6%AD%A4%E7%B6%B2%E9%A0%81%E3%80%82%22%3B%0A%20%20%20%20%20%20%20%20%20%20%20%20statusBox.style.color%20%3D%20%22var(--success)%22%3B%0A%20%20%20%20%20%20%20%20%20%20%20%20statusBox.style.background%20%3D%20%22rgba(16%2C%20185%2C%20129%2C%200.1)%22%3B%0A%20%20%20%20%20%20%20%20%20%20%20%20statusBox.style.borderColor%20%3D%20%22rgba(16%2C%20185%2C%20129%2C%200.2)%22%3B%0A%20%20%20%20%20%20%20%20%20%20%7D)%0A%20%20%20%20%20%20%20%20%20%20.catch(e%20%3D%3E%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20statusBox.innerHTML%20%3D%20%22%E2%9D%8C%20%E6%8F%90%E4%BA%A4%E5%A4%B1%E6%95%97%EF%BC%8C%E8%AB%8B%E9%80%9A%E7%9F%A5%E7%AE%A1%E7%90%86%E5%93%A1%E7%A2%BA%E8%AA%8D%E4%BC%BA%E6%9C%8D%E5%99%A8%E6%88%96%E7%B6%B2%E8%B7%AF%E7%8B%80%E6%85%8B%E3%80%82%22%3B%0A%20%20%20%20%20%20%20%20%20%20%20%20statusBox.style.color%20%3D%20%22var(--error)%22%3B%0A%20%20%20%20%20%20%20%20%20%20%20%20statusBox.style.background%20%3D%20%22rgba(244%2C%2063%2C%2094%2C%200.1)%22%3B%0A%20%20%20%20%20%20%20%20%20%20%20%20statusBox.style.borderColor%20%3D%20%22rgba(244%2C%2063%2C%2094%2C%200.2)%22%3B%0A%20%20%20%20%20%20%20%20%20%20%7D)%3B%0A%20%20%20%20%20%20%20%20%7D%20else%20%7B%0A%20%20%20%20%20%20%20%20%20%20statusBox.innerHTML%20%3D%20%22%E2%9A%A0%EF%B8%8F%20%E6%9C%AC%E6%A9%9F%E4%BC%BA%E6%9C%8D%E5%99%A8%E6%9C%AA%E9%96%8B%E5%95%9F%EF%BC%8C%E4%B8%94%E6%9C%AA%E8%A8%AD%E5%AE%9A%E9%9B%B2%E7%AB%AF%E5%90%8C%E6%AD%A5%EF%BC%8C%E6%88%90%E7%B8%BE%E5%B7%B2%E4%BF%9D%E5%AD%98%E5%9C%A8%E6%9C%AC%E6%A9%9F%E5%BF%AB%E5%8F%96%E4%B8%AD%E3%80%82%22%3B%0A%20%20%20%20%20%20%20%20%20%20statusBox.style.color%20%3D%20%22%23fbbf24%22%3B%0A%20%20%20%20%20%20%20%20%20%20statusBox.style.background%20%3D%20%22rgba(251%2C%20191%2C%20129%2C%200.1)%22%3B%0A%20%20%20%20%20%20%20%20%20%20statusBox.style.borderColor%20%3D%20%22rgba(251%2C%20191%2C%20129%2C%200.2)%22%3B%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%7D)%3B%0A%20%20%20%20%7D%0A%20%20%3C%2Fscript%3E%0A%3C%2Fbody%3E%0A%3C%2Fhtml%3E%5C%60%3B%0A");

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

        // 1.5 產生互動式闖關網頁的關卡資料與 HTML
        const gameLevels = generatedData.quiz.map((q, idx) => {
          return {
            title: `第 ${idx + 1} 關：${q.question.substring(0, 15)}...`,
            desc: `【SOP 規範】${q.explanation || '請根據標準作業程序回答以下情境問題。'}`,
            challenge: `【情境】${q.question}`,
            options: q.options.map((opt, oIdx) => {
              const label = ["A", "B", "C", "D"][oIdx] || "";
              const isCorrect = (label === q.answer.trim().toUpperCase());
              return {
                text: opt,
                correct: isCorrect,
                feedback: isCorrect 
                  ? `答對了！${q.explanation || '回答完全合規！'}` 
                  : `答錯囉！正確答案應該是 ${q.answer}。`
              };
            })
          };
        });

        let interactiveHtml = INTERACTIVE_TEMPLATE_SOURCE;
        interactiveHtml = interactiveHtml.replace(/__TRAINING_TITLE__/g, () => generatedData.title || "教育訓練");
        interactiveHtml = interactiveHtml.replace("__QUIZ_JSON__", () => JSON.stringify(gameLevels, null, 2));

        // 1.6 產生測驗題目與選項對照表 CSV (UTF-8 BOM)
        let quizCsvContent = "\ufeff題號,題目內容,選項A,選項B,選項C,選項D,正確答案,詳細解析\r\n";
        generatedData.quiz.forEach((q, idx) => {
          const num = "第 " + (idx + 1) + " 題";
          const questionClean = q.question.replace(/"/g, '""');
          const optA = (q.options[0] || "").replace(/"/g, '""');
          const optB = (q.options[1] || "").replace(/"/g, '""');
          const optC = (q.options[2] || "").replace(/"/g, '""');
          const optD = (q.options[3] || "").replace(/"/g, '""');
          const ans = q.answer.trim();
          const exp = q.explanation.replace(/"/g, '""');
          quizCsvContent += `"${num}","${questionClean}","${optA}","${optB}","${optC}","${optD}","${ans}","${exp}"\r\n`;
        });

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
1. **\`index.html\`**：主測驗網頁（傳統簡報閱讀與測驗模式）。
2. **\`interactive.html\`**：【新版】一日 SOP 職人情境模擬闖關（包含擬真工作場景選擇、闖關音效、即時語音回饋，能幫助同仁更有感吸收規章內容！）。
3. **\`對照表_測驗題目與選項.csv\`**：題目與選項對照表（以 Excel 打開此對照表即可直接看見 ABCD 各選項對應的詳細文字與解析說明，不需再開啟網頁核對）。
4. **\`serve_intranet.ps1\`**：本機伺服器程式（以 Windows PowerShell 撰寫，負責接收同仁提交的成績並存入本機試算表）。
5. **\`點我啟動內網伺服器(Windows免安裝).bat\`**：一鍵啟動批次檔，按滑鼠雙擊即可運行。
6. **\`apps_script_code.gs\`**：Google Sheets 雲端同步腳本（供會寫 Apps Script 的人員設定雲端回收）。

---

## 🚀 收集同仁的成績（本機免設定模式 - 最簡單）

1. **解壓縮**：請確保此資料夾已解壓縮到您的電腦（不要直接在 zip 檔案中點兩下執行）。
2. **啟動本機伺服器**：
   - 雙擊執行 **\`點我啟動內網伺服器(Windows免安裝).bat\`**。
   - 電腦會彈出一個黑色的終端機視窗，並以綠色字體顯示一串連線網址（例如：\`http://192.168.1.100:18080/index.html\`）。**請勿關閉此視窗**。
3. **同仁開啟作答**：
   - 將該網址尾部的 \`index.html\` 改為 \`interactive.html\`（例如：\`http://192.168.1.100:18080/interactive.html\`），即可讓同仁體驗最新的一日 SOP 職人闖關挑戰！
   - **重要前提**：同仁的手機或電腦必須連線至**與您相同的公司 Wi-Fi 或內網**。
4. **回收成績 (results.csv)**：
   - 同仁在闖關或作答結束後，成績就會自動寫入並回傳。
   - 資料夾中會**自動產生 \`results.csv\`** 檔案，您直接雙擊該檔即可用 Excel 查看全體成績、作答時間以及每題答錯/答對的詳細紀錄！`;

        // 3. 包裝 ZIP 檔案
        zip.file("index.html", playerHtml);
        zip.file("interactive.html", interactiveHtml);
        zip.file("對照表_測驗題目與選項.csv", quizCsvContent);
        zip.file("serve_intranet.ps1", "\ufeff" + psServerCode);
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
  </script>
</body>
</html>

```
