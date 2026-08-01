# 🎬 影片生成 模組群 (Video Generation Hub)

> 🔗 **GitHub 路徑**：[google-agent / 第一類\_核心網頁與互動系統 / 影片生成](https://github.com/shihwei0809/google-agent/tree/main/%E7%AC%AC%E4%B8%80%E9%A1%9E_%E6%A0%B8%E5%BF%83%E7%B6%B2%E9%A0%81%E8%88%87%E4%BA%92%E5%8B%95%E7%B3%BB%E7%B5%B1/%E5%BD%B1%E7%89%87%E7%94%9F%E6%88%90)

本資料夾匯集所有與「自動影片合成」相關的子專案，涵蓋 PDF 簡報轉影片、AI 語音合成工具、消防演習分鏡腳本產生器等。所有工具均以 **本機優先 + Web UI 操作** 為設計原則。

---

## 📁 子專案一覽

### 1. 🎥 [pdf-to-video](./pdf-to-video/) — 簡報自動語音影片生成器（主系統）
**一鍵將 PDF 簡報轉換為附有 AI 語音旁白的 MP4 影片。**

| 功能 | 說明 |
|---|---|
| PDF 解析 | 支援 Google Gemini 視覺模型 / EasyOCR / 本機字型提取 |
| 語音引擎 | Edge TTS（免費台灣女聲）/ Gemini TTS（AI 情緒語音） |
| 背景音樂 | 上傳 BGM、AI 生成音樂（Lyria 3）、ffmpeg -23 LUFS 響度正規化 |
| 浮水印 | 自訂中文字浮水印，Pillow 渲染 + 微軟正黑體 |
| 硬體加速 | Intel QSV 顯卡自動偵測，fallback 至 libx264 |
| 網路存取 | 本機 `localhost:8002` 或區網 IP 多人同時使用 |

- 🚀 啟動：雙擊 `啟動語音影片生成器.bat`
- 📖 詳細說明：[pdf-to-video/README.md](./pdf-to-video/README.md)

---

### 2. 🎥 [pdf-to-video-cloning](./pdf-to-video-cloning/) — 影片生成器（公司環境版）
與 `pdf-to-video` 功能相同，為公司網路環境獨立部署版本，Port、路徑設定與主系統分開，可同時執行互不干擾。

- 🚀 啟動：雙擊 `啟動語音影片生成器.bat`
- 📖 詳細說明：[pdf-to-video-cloning/README.md](./pdf-to-video-cloning/README.md)

---

### 3. 🔊 [pure-tts](./pure-tts/) — 純 TTS 語音合成工具
**不需要 PDF，直接輸入文字即可合成並下載語音 MP3。**

| 功能 | 說明 |
|---|---|
| 引擎 | Edge TTS（免費）/ Gemini TTS（需 API Key） |
| 語速調整 | 0.5x ~ 2.0x，支援即時預覽 |
| 批次合成 | 多頁文字一次產出多個 MP3 |
| 區網共用 | Port `8004`，自動顯示本機 IP，自動切換備用 Port |

- 🚀 啟動：雙擊 `啟動語音合成工具.bat`

---

### 4. 🚒 [fire-drill-storyboard](./fire-drill-storyboard/) — 消防演習分鏡腳本產生器
**以 AI 自動產生消防演習的分鏡腳本與提示詞（Prompt），搭配 Gemini API 生成圖像。**

| 功能 | 說明 |
|---|---|
| 分鏡腳本 | FastAPI + Web UI，自動生成各場景提示詞 |
| 圖像產生 | 串接 Gemini Imagen 模型批次渲染 |
| 輸出格式 | HTML 投影片 / Google Slides（GAS 整合）|

- 🚀 啟動：雙擊 `啟動消防演習分鏡與提示詞產生器.bat`

---

### 5. 📝 [hr_quiz_v2](./hr_quiz_v2/) — 員工教育訓練測驗系統（本機優先版）
**通用 SOP 教育訓練與測驗系統，支援語音播放題目、自動評分。**

| 功能 | 說明 |
|---|---|
| 題目設定 | 前端圖形化管理後台，免後端即可改題 |
| 語音朗讀 | 微軟 TTS 自動朗讀題目 |
| 評分記錄 | 作答結果自動寫入本機 `results.csv` |
| 離線優先 | 純 HTML/CSS/JS，無需網路即可使用 |

- 🚀 啟動：直接開啟 `index_with_mp3.html`

---

## 🛠️ 環境一鍵安裝

```powershell
# 在本資料夾執行，自動安裝所有子專案的 Python 套件環境
.\setup_env.ps1
```

## 📋 共用技術棧

- **後端**：Python 3.11+ / FastAPI / Uvicorn
- **影片合成**：MoviePy 2.x / FFmpeg（含 loudnorm、QSV）
- **語音引擎**：Edge TTS / Google Gemini TTS
- **AI 視覺**：Google Gemini Flash / EasyOCR
- **前端**：HTML5 / Vanilla CSS / JavaScript（無框架）
