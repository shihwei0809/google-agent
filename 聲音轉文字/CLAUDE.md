# NoType — AI 語音輸入工具

## 專案簡介
NoType 是一個 AI 語音輸入工具，讓使用者不需要打字，透過語音即可完成文字輸入。類似 Typeless，但使用者自帶 API Key，程式常駐系統匣。

## 關鍵時程
- 專案啟動：2026-04-12
- v0.1 完成：2026-04-12（核心功能完整，可端對端運作）
- v1.0 優化版完成：2026-06-06（包含實時置中膠囊型波形浮動框與自訂快捷鍵修復）

## 語言與風格
- 所有回應、文件皆使用**繁體中文**
- 修改前先確認計畫，優先保留原有資料結構

## 技術架構
- **框架**：Electron（系統匣常駐 + Web UI 設定頁）
- **STT**：OpenAI Whisper API / Groq Whisper API（使用者在設定中切換，已優化為 WebM/Opus 動態格式，加入 Prompt 精準度優化）
- **LLM 潤飾**：OpenAI GPT-4o-mini / Groq Llama 3.3（移除贅詞、修正文法、自動標點）
- **鍵盤模擬**：koffi 呼叫 Windows `keybd_event` API（剪貼簿 + Ctrl+V）
- **按鍵偵測**：koffi 呼叫 Windows `GetAsyncKeyState` API（自訂快捷鍵動態映射與 Polling 偵測）
- **設定儲存**：electron-store v8（JSON 存本地，CJS 格式）
- **圖示生成**：pngjs 程式化繪製 64x64 藍色麥克風 PNG
- **音訊監控**：AudioContext + AnalyserNode（本地音量振幅 VAD 檢測，智慧過濾靜音與誤觸）

## 目前進度
- [x] 專案初始化
- [x] 規劃核心功能與技術架構
- [x] Electron 骨架 + 系統匣（藍色麥克風圖示）
- [x] 設定頁面 UI + 本地儲存（IPC 通訊）
- [x] 語音錄製模組（MediaRecorder WebM/Opus + 隱藏視窗）
- [x] STT API 模組（OpenAI Whisper / Groq + Prompt 優化）
- [x] LLM 文字潤飾模組
- [x] 鍵盤模擬輸入模組（koffi + Windows API）
- [x] 全域快捷鍵：動態解析自訂快捷鍵並進行實時按鍵 Polling
- [x] 智慧音訊過濾（過濾小於 400ms 的誤觸，或低於 0.02 振幅的靜音，防止 Whisper 幻覺）
- [x] 錄音狀態浮動視窗（置中膠囊型外觀、實時對稱波形動畫、轉圈 Spinner、成功/錯誤狀態邊框亮色）
- [x] 修正鍵盤卡住問題（貼上前強制釋放所有修飾鍵）
- [x] 端到端測試確認文字成功輸入到目標欄位
- [x] 快速啟動優化（新增雙擊執行批次檔 `start.bat` 與背景靜音執行的 `start-hidden.vbs`）
- [x] 打包與發布（以 electron-builder 編譯 Windows 安裝檔及可攜式版，上傳至 GitHub Release 與 Google 雲端硬碟）

## 開發過程中遇到的問題與解法

### 1. electron-store v11 不相容 CommonJS
- **問題**：`Store is not a constructor` — v11 是 ESM-only
- **解法**：降級至 electron-store v8（最後一個 CJS 版本）
- **注意**：v8 不支援 `encryptionKey` 參數，已移除

### 2. node-global-key-listener 無法在 Electron 中使用
- **問題**：`spawn UNKNOWN` — 它試圖 spawn 子程序，被 Electron 沙箱阻擋
- **解法**：改用 `koffi`（純 JS FFI，有 prebuilt binary）直接呼叫 Windows `GetAsyncKeyState` API

### 3. uiohook-napi 需要 Visual Studio 編譯
- **問題**：`Could not find any Visual Studio installation` — native addon 需要 C++ 編譯器
- **解法**：放棄 uiohook-napi，統一使用 koffi（不需要編譯）

### 4. @nut-tree-fork/nut-js 鍵盤模擬無效
- **問題**：同樣需要原生編譯，且可能根本沒有正確載入
- **解法**：改用 koffi 呼叫 Windows `keybd_event` API 模擬 Ctrl+V

### 5. Alt 鍵卡住導致鍵盤無法使用
- **問題**：按住 Alt+Space 錄音後放開，系統仍認為 Alt 被按住，模擬的 Ctrl+V 變成 Alt+Ctrl+V
- **解法**：在 `typer.js` 中，模擬 Ctrl+V 前後都呼叫 `releaseAllModifiers()` 強制釋放 Alt/Space/Ctrl
- **狀態**：已修復

### 6. SVG 圖示在 Windows 系統匣不顯示
- **問題**：Electron 的 `nativeImage.createFromDataURL` 對 SVG 支援不完整
- **解法**：用 `pngjs` 程式化繪製 64x64 PNG 圖示（`scripts/generate-icon.js`）

### 7. 靜音/空白錄音造成 Whisper 產生幻覺文字
- **問題**：完全不說話或放開快捷鍵過快時，Whisper 會因為試圖填補空白而幻覺出「謝謝」或「作詞作曲」等無關文字。
- **解法**：在 `recorder-page.html` 中以 `AudioContext` 動態監測最大振幅，若低於 `0.02` 或長度短於 `400ms`，直接視為 `'silent'` 無效錄音，主行程直接關閉浮動提示框而不送出 API 請求。

### 8. 自訂快捷鍵在背景輪詢中無效
- **問題**：先前程式寫死註冊 `Alt+Space`，且 `GetAsyncKeyState` 輪詢也寫死偵測 `VK_LMENU` (Alt) 和 `VK_SPACE`，導致更改設定後的自訂快捷鍵完全失效。
- **解法**：從 store 動態讀取快捷鍵設定，進行全域快捷鍵註冊；同時解析快捷鍵字串（如 `Ctrl`、`Shift`、`Space`、`A-Z` 等），動態映射為 Windows 虛擬按鍵碼（VK Codes）進行輪詢。

### 9. winCodeSign 符號連結權限錯誤導致打包失敗
- **問題**：在 Windows 上使用 `electron-builder` 打包時，7-Zip 解壓 `winCodeSign` 依賴套件中的 macOS 符號連結（`.dylib`）會因為無系統管理員權限而報錯中斷。
- **解法**：手動調用專案內 `7za.exe` 將其解壓到 `AppData/Local/electron-builder/Cache/winCodeSign/winCodeSign-2.6.0` 資料夾，忽略 macOS 專屬的 symlinks 錯誤。因為是編譯 Windows 版，這不會影響程式簽署與打包，隨後即可成功打包。

## 關鍵設計決策
- **koffi 是核心依賴**：取代了三個套件，統一用 Windows API 處理按鍵偵測和鍵盤模擬。
- **按住錄音機制**：globalShortcut 偵測設定快捷鍵按下 → 開始錄音 + setInterval 每 80ms 用 GetAsyncKeyState 檢查設定按鍵的物理狀態 → 放開時停止錄音。
- **音訊格式與 IPC 傳輸優化**：改用 `MediaRecorder` 與 `audio/webm;codecs=opus`，減少 10 倍以上音訊大小，提高 API 上傳速度；且直接傳送 `Uint8Array` 避免 JS Array 造成的 IPC 序列化開銷。
- **文字輸入方式**：剪貼簿寫入 + 模擬 Ctrl+V，相容中文輸入法和所有應用程式。
- **膠囊置中浮動提示框**：調整提示框為 `280x50` 置中於螢幕底部。左側 `✕` 取消、右側 `✓` 確認，中間 Canvas 渲染對稱柱狀波形動畫，隨講話音量高低律動。

## 最近更動紀錄
| 日期 | 變更摘要 | GitHub |
|------|----------|--------|
| 2026-04-12 | 專案初始化 | ✅ |
| 2026-04-12 | 完成 v0.1：骨架、設定頁、錄音、STT、LLM、鍵盤輸入 | ✅ |
| 2026-04-12 | 修正圖示（SVG→PNG）、快捷鍵（toggle→按住）、鍵盤卡住問題 | ✅ |
| 2026-06-04 | 優化音訊管線為 WebM/Opus、實時發送 Uint8Array，解決靜音幻覺、修復自訂快捷鍵與打包，新增一鍵啟動腳本與備份 | ✅ |
| 2026-06-06 | 實作底部置中膠囊型提示框，串接 Canvas 對稱音量波形動態動畫，完成 Release 打包與多處同步備份 | ✅ |

## 資料夾結構
```
notype/
├── package.json
├── CLAUDE.md
├── .gitignore
├── start.bat                # 一鍵點擊啟動腳本
├── start-hidden.vbs         # 一鍵隱藏 CMD 視窗背景啟動腳本
├── assets/
│   ├── icon-256.png         # 256x256 高解析度圖示
│   ├── icon.ico             # Windows 圖示檔
│   ├── icon.png             # 64x64 藍色麥克風圖示（pngjs 生成）
│   └── icon.svg             # SVG 版本（備用）
├── scripts/
│   └── generate-icon.js     # 圖示生成腳本
└── src/
    ├── main.js              # Electron 主程序入口 + IPC handlers
    ├── tray.js              # 系統匣管理
    ├── store.js             # 本地設定存儲（electron-store v8）
    ├── recorder.js          # 錄音及狀態膠囊浮動視窗管理
    ├── recorder-page.html   # 隱藏錄音及音量偵測頁面（MediaRecorder）
    ├── recorder-preload.js  # 錄音頁面 preload（包含 sendVolume 管道）
    ├── overlay.html         # 膠囊型狀態浮動提示與 Canvas 波形動畫
    ├── overlay-preload.js   # 浮動提示 preload（包含 onVolumeUpdate 管道）
    ├── shortcut.js          # 全域快捷鍵動態註冊 + 錄音流程控制（koffi）
    ├── typer.js             # 鍵盤模擬輸入（koffi + keybd_event）
    ├── api/
    │   ├── whisper.js       # OpenAI Whisper STT（原生 FormData 重構 + Prompt 優化）
    │   ├── groq.js          # Groq Whisper STT（動態格式 + Prompt 優化）
    │   └── llm.js           # LLM 文字潤飾
    └── settings/
        ├── index.html       # 設定頁面（深色主題）
        ├── settings.js      # 設定頁面邏輯
        ├── settings.css     # 設定頁面樣式
        └── preload.js       # 設定頁面 preload
```

## 同步資訊
| 平台 | 路徑 / 位置 | 用途 |
|------|-------------|------|
| 本機 | `C:\notype-master\` 以及 `c:\GOOGLE ANGET\聲音轉文字\` | 主要工作目錄與專案工作區 |
| GitHub | `shihwei0809/google-agent` | 版本控制與公開部署 (Releases) |
| 雲端硬碟 | `G:\我的雲端硬碟\GOOGLE ANGET\聲音轉文字\` | 雲端備份儲存區 |

## 工作注意事項
- 當使用者說「結束」、「休息」或「暫停」時，自動記錄進度並更新此檔案
- 新增或修改檔案後，更新「資料夾結構」與「最近更動紀錄」
- **此專案不能使用需要 Visual Studio 編譯的原生套件**，統一用 koffi 呼叫 Windows API
