# ISOTANK 化學品卸料安全訓練動畫與影片 (isotank-hf-demo) - 操作說明書

> 🔗 **GitHub 專案庫**：[shihwei0809/google-agent/tree/main/isotank-hf-demo](https://github.com/shihwei0809/google-agent/tree/main/isotank-hf-demo)


## 專案簡介
本專案為鴻勝化學「ISOTANK 化學品卸料安全訓練」的動畫簡報與影片生成系統。本專案為 `isotank-training` 專案的全面升級版，使用最新的 **HyperFrames** 影音生成框架開發，採用深色暗黑科技感風格的網頁投影片（GSAP 動畫效果），配上微軟 Edge TTS 產生的台灣腔男聲旁白，並能自動渲染輸出高畫質的 MP4 教育訓練影片。

## 主要功能特色
- **HyperFrames 動畫簡報**：以 HTML + GSAP 編寫 12 頁精緻動畫投影片，每頁具有高質感、極流暢的動態圖形（Motion Graphics）。
- **精準音訊與字幕對齊**：旁白使用微軟 Edge TTS 台灣男聲 `zh-TW-YunJheNeural` 產生。每頁的播放時長會根據旁白音檔長度（外加 1 秒緩衝）進行動態調整（而不是固定 10 秒）。
- **自動化時間更新腳本**：提供 `fix_timing.py` 腳本，能夠根據旁白音檔的長度重新計算並自動修改 HTML 中各個 `clip` 的 `data-start` 與 `data-duration` 屬性。
- **全自動影片渲染**：可以直接使用 `npx hyperframes render`（或執行編譯腳本）調用 Playwright 於無頭瀏覽器中自動錄製網頁動畫，並合併旁白音軌，一鍵生成 1920x1080 規格的 MP4 影片。

## 技術棧
- **前端動畫**：HTML5, CSS3, GSAP (GreenSock Animation Platform)
- **影音渲染**：HyperFrames CLI (基於 Playwright)
- **語音合成**：edge-tts (Microsoft Cognitive Services)
- **多媒體處理**：FFmpeg (音訊延遲與音視訊混音)

## 專案結構
- `index.html`：主要的投影片動畫網頁（含 12 個投影片 clips、GSAP 時間軸等）。
- `assets/narration/`：每頁對應的旁白音檔（`page-01.mp3` ~ `page-12.mp3`）。
- `combined_audio.mp3`：串接完成的全程旁白音軌。
- `fix_timing.py` / `apply_timing.py`：時間碼自動更新與同步腳本。
- `package.json`：定義 `dev` (預覽)、`check` (檢查)、`render` (輸出影片) 等 script。
- `isotank-final.mp4`：最終產出的含音軌高畫質影片（4分6秒，1920×1080）。

## 本機執行與操作
1. **啟動預覽 Studio**：
   進入 `isotank-hf-demo` 目錄，執行：
   ```bash
   npm run dev
   ```
   即可在瀏覽器開啟 `http://localhost:3002` 預覽帶旁白與動畫的互動式簡報。

2. **時間碼校準**：
   若修改了簡報內容或旁白音檔，執行以下腳本自動重新計算並更新 `index.html` 的時間軸屬性：
   ```bash
   python fix_timing.py
   ```

3. **渲染輸出影片**：
   執行以下命令，將網頁動畫自動導出為無音軌影片：
   ```bash
   npm run render
   ```

4. **音軌合成**：
   使用 FFmpeg 將 `combined_audio.mp3` 與無音軌影片進行 mux，即可合成最終帶旁白的 `isotank-final.mp4` 教育訓練影片。
