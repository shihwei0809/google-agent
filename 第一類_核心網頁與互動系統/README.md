# 🌐 第一類：核心網頁與互動系統 (Core Web & Interactive Systems)

> 🔗 **GitHub 路徑**：[google-agent / 第一類\_核心網頁與互動系統](https://github.com/shihwei0809/google-agent/tree/main/%E7%AC%AC%E4%B8%80%E9%A1%9E_%E6%A0%B8%E5%BF%83%E7%B6%B2%E9%A0%81%E8%88%87%E4%BA%92%E5%8B%95%E7%B3%BB%E7%B5%B1)

本分類匯集所有**互動式 Web 應用程式、SVG 動畫模擬、教育訓練測驗系統與影音生成模組**。

---

## 📁 專案目錄與簡述

| 專案名稱 | 說明簡述 | 主要技術 |
|---|---|---|
| 🎬 [影片生成](./影片生成/) | PDF 簡報轉語音影片生成器模組群（包含 pdf-to-video、pure-tts、消防演習分鏡等） | FastAPI, Edge-TTS, Gemini TTS, MoviePy, loudnorm |
| 📊 [flowchart-web](./flowchart-web/) | 廠區產品製程 SVG 流程圖、動態液位水波計、壓力與 N2 吹掃模擬系統 | HTML5, CSS3, SVG, JavaScript |
| 🏗️ [isotank-training](./isotank-training/) | 化學品卸料安全訓練與 ISO Tank 槽車卸料模擬教學系統 | HTML5, Canvas, Web Audio |
| 🚛 [isotank-hf](./isotank-hf/) / [isotank-hf-demo](./isotank-hf-demo/) | 氫氟酸 (HF) 專用 ISO Tank 槽車防護演練與安全規格防呆說明 | SVG Animation, JS, WebUI |
| 📐 [isotank-layout-app](./isotank-layout-app/) | ISO Tank 廠區擺放配置與區域佈局規劃互動工具 | HTML5, Drag&Drop, Canvas |
| 🏗️ [isotank-crane-app](./isotank-crane-app/) | ISO Tank 天車吊掛與吊裝作業安全路徑視覺化模擬 | HTML5, CSS Animations |
| 📏 [isotank-100x200-app](./isotank-100x200-app/) / [isotank-70x70-max100](./isotank-70x70-max100/) | 特殊規格 ISO Tank 尺寸對照與擺放邊界規劃系統 | Web Interactive Tool |
| 📝 [員工教育訓練測驗系統](./員工教育訓練測驗系統/) | 廠區 SOP 教育訓練測驗系統，支援語音朗讀、圖形化後台與 CSV 本機評分 | HTML5, 微軟 TTS, CSV 本機存取 |
| 🎙️ [聲音轉文字](./聲音轉文字/) | 免打字語音輸入助理，支援桌面快捷鍵與語音辨識轉寫 | Electron, Whisper API |
| 🔍 [OCR測試](./OCR測試/) | 圖片與 PDF 光學文字辨識 (OCR) 演算法與引擎效能測試工具 | Python, EasyOCR, PyMuPDF |
| 🌐 [互動式網站](./互動式網站/) | 廠區互動式教育訓練與簡報視覺化元件展示頁 | HTML5, SCSS, JS |

---

## 🚀 一鍵環境初始化

若要為此分類下的所有 Python/Web 工具安裝軟體與套件，可執行：
```powershell
.\setup_env.ps1
```
