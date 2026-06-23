# AIGC 音樂影片生成系統 (aigc-music-video-hub) - 操作說明書

> 🔗 **GitHub 專案庫**：[shihwei0809/google-agent](https://github.com/shihwei0809/google-agent)


## 專案簡介
本專案為 **勝一化學 AI 音樂影片 (AIGC Music Video Hub)** 的專案整合中心。它利用 Suno AI 生成企業宣傳與科普音樂，並搭配自動化腳本產出精緻的故事板 (Storyboard) 與影片畫面，最終使用 FFmpeg 合成帶有音軌的 MP4 高畫質音樂影片。本專案前端看板已託管於 Firebase Hosting 服務。

## 主要功能特色
- **AI 音樂生成與合輯**：包含《彰濱的科技之翼》、《綠色循環的脈動》、《純淨之光》等多首 Suno AI 創作的主題歌曲。
- **全自動故事板生成**：利用 Python 腳本 `generate_storyboards_for_all_songs.py` 自動為每首歌曲設計 12 畫面影像故事板與歌詞配對。
- **批次影片渲染與混音**：提供一鍵渲染指令，使用 FFmpeg 自動將生成的影像素材（每張播映時長已依歌詞對齊）與 MP3 背景音軌合成為最終的 MP4 音樂影片。
- **專案 HMI 看板**：具備網頁版「音樂影片專案總覽」看板，整合音樂試聽、故事板瀏覽與 MP4 影片線上播放。

## 技術棧
- **多媒體處理**：FFmpeg (影像轉場、音訊延遲與音視訊混音)
- **開發語言**：Python 3 (圖片重命名與批次影片渲染)
- **部署託管**：Firebase Hosting (託管前端看板)

## 專案結構
- `build_mv_dashboard.py`：建立音樂影片儀表板看板。
- `generate_storyboards_for_all_songs.py`：自動生成歌曲故事板腳本。
- `organize_and_generate_all_mvs.py` / `render_all_videos.py`：批次生成與渲染影片。
- `音樂影片專案總覽.html`：音樂影片本機/網頁版成果總覽看板。
- `純淨之光.mp3` / `勝一化學_純淨之光_MV.mp4`：生成的主打歌曲與 MV。
- `firebase.json`：Firebase Hosting 託管設定檔。

## 本機執行與操作
1. **生成故事板**：
   執行以下命令，自動產生所有歌曲的故事板描述：
   ```bash
   python generate_storyboards_for_all_songs.py
   ```
2. **影片批次渲染**：
   將生成的故事板圖片放至 `圖片/` 資料夾，執行以下腳本，將自動結合 MP3 合成 MP4 影片：
   ```bash
   python organize_and_generate_all_mvs.py
   ```
3. **開啟專案看板**：
   在瀏覽器雙擊開啟 `音樂影片專案總覽.html`，即可進入專案的 HMI 展示看板。
