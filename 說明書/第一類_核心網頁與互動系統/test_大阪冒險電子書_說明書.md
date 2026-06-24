# 大阪冒險之旅四格漫畫電子書 (test) - 操作說明書

> 🔗 **GitHub 專案庫**：[shihwei0809/google-agent/tree/main/test](https://github.com/shihwei0809/google-agent/tree/main/test)


## 專案簡介
本專案為小妤一家四口大阪五天四夜旅遊的四格漫畫互動式電子書，內建雙語音播放（微軟原生台灣國語與 ElevenLabs 電影級語音）與角色試聽功能。

## 主要功能特色
- **微軟原生 (Microsoft Native) 模式**：優化台灣腔聲線；針對 10 歲主角弟弟「小融 (Taiga)」進行童音校正（以微軟台灣男聲 `zh-TW-YunJheNeural` 結合 `+35Hz` 音高及 `+15%` 語速調整），完美呈現活潑小男童聲音。
- **ElevenLabs 模式**：支援電影級高擬真配音，且設有額度耗盡自動降級至微軟語音的防錯機制。
- **試聽面板**：提供獨立試聽按鈕，方便預覽個別角色音色。

## 技術棧
- 前端：HTML5, CSS3, JavaScript
- 後端語音生成：Python (edge-tts), ElevenLabs API

## 本機執行與操作
1. 雙擊開起 `test/index.html` 查看電子書。
2. 點選頁面右上角的設定（齒輪）圖示，可切換「語音模式」或對各角色進行語音試聽。
