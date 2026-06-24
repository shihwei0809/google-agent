# 畢業旅行與簡報企劃 (grad-trip) - 操作說明書

> 🔗 **GitHub 專案庫**：[shihwei0809/google-agent](https://github.com/shihwei0809/google-agent)


## 專案簡介
本專案用於生成國小畢旅二天一夜回憶錄的互動式電子書網頁與配音影片合成。

## 主要功能特色
- **配音語音合成**：使用 Python 腳本將段落文字合成語音 Mp3 檔。
- **影片與音訊混音**：提供 `mux_video.py` 與 `merge_audio.py`，使用 FFmpeg 自動將背景音樂與旁白配音進行混音，並與旅遊照片序列合成為最終 MP4 影片。

## 技術棧
- Python (edge-tts), FFmpeg, HTML5 (電子書展示)

## 操作步驟
1. 進入 `grad-trip` 目錄。
2. 執行 `python generate_narration.py` 產出旁白配音檔。
3. 執行 `python mux_video.py` 生成回憶錄 MP4 影片（已透過 .gitignore 排除大檔，影片會保留在本地 `grad-trip/renders/` 下）。
