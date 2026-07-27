# QA.md - 為什麼 AI 需要上下文

## 檔案閘門

- [x] `SCRIPT.md` 已給使用者確認。
- [x] `DESIGN.md` 已給使用者確認。
- [x] `ASSETS.md` 已列出素材來源與缺口。
- [x] `final.mp4` 已產生。
- [x] `renders/frames/` 已抽 6 張關鍵幀。

## 視覺閘門

- [x] 字沒有超出畫面。
- [x] 字卡與字幕沒有重疊。
- [x] 字幕單行優先，每段不超過 25 字。
- [x] 每頁有明確視覺焦點。
- [x] 至少 5 種版面已使用。
- [x] 不是整支影片都像簡報截圖。

## 音訊閘門

- [x] 有視訊流。
- [x] 有音訊流。
- [x] 旁白沒有被 webm 空音軌覆蓋。
- [x] 旁白與字幕大致同步。
- [x] BGM 沒有蓋過旁白。
- [x] 結尾有自然淡出。

## 內容閘門

- [x] 前 3 秒有 Hook。
- [x] 可靜音閱讀主要訊息。
- [x] 有具體視覺錨點：AI 視野圖、提示對比、新同事插圖、四步流程、地圖線。
- [x] 內容為一般概念解釋，沒有需即時查證的價格、法規、最新型號或公司數據。

## 素材來源

- 視覺：HTML/CSS/SVG 自製。
- 插圖：CSS 自製新同事場景，未使用外部圖片。
- 旁白：Edge-TTS 生成。
- BGM：ffmpeg `aevalsrc` 程式生成 ambient bed，自製。

## QA 結果

- 本機渲染位置：`C:\CodexWork\ai-context-video\final.mp4`
- Google Drive 同步位置：`G:\我的雲端硬碟\新自動生成影片\ai-context-video\final.mp4`
- `ffprobe` 結果：H.264 視訊流 + AAC 音訊流。
- 已檢視關鍵幀：`frame-005.png`、`frame-060.png`、`frame-120.png`，畫面正常。

