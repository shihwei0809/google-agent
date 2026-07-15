# AI 自動影片生成系統

這是一個可本地或雲端部署的 Python 專案，流程如下：

1. 接收表單輸入：主題、場景、角色
2. 依輸入自動建立 50 組分鏡提示詞
3. 使用 OpenAI Image API 生成 50 張圖片
4. 產出 `.srt` 字幕檔
5. 透過 FFmpeg 合成 MP4 影片、燒錄字幕、加入背景音樂
6. 上傳影片到 Google Drive
7. 回傳影片連結

## 專案結構

```text
.
├─ app/
│  ├─ api/
│  │  └─ routes.py
│  ├─ core/
│  │  ├─ config.py
│  │  └─ logging.py
│  ├─ models/
│  │  └─ schemas.py
│  ├─ services/
│  │  ├─ drive_service.py
│  │  ├─ openai_service.py
│  │  ├─ pipeline_service.py
│  │  ├─ subtitle_service.py
│  │  └─ video_service.py
│  ├─ utils/
│  │  ├─ command_utils.py
│  │  └─ file_utils.py
│  └─ main.py
├─ assets/
│  └─ background_music.mp3
├─ credentials/
│  └─ .gitkeep
├─ output/
│  └─ .gitkeep
├─ templates/
│  └─ index.html
├─ .env.example
├─ Dockerfile
├─ requirements.txt
└─ run.py
```

## 先決條件

- Python 3.11+
- FFmpeg 已安裝，且 `ffmpeg` / `ffprobe` 可執行
- OpenAI API Key
- Google Drive Service Account 憑證 JSON
- 一個可寫入的 Google Drive 資料夾，並已分享給 Service Account Email

## 安裝

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
pip install -r requirements.txt
```

macOS / Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

## 環境變數

1. 複製 `.env.example` 為 `.env`
2. 填入：

- `OPENAI_API_KEY`
- `GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE`
- `GOOGLE_DRIVE_FOLDER_ID`
- `BACKGROUND_MUSIC_PATH`

## 啟動

```bash
python run.py
```

啟動後開啟：

```text
http://127.0.0.1:8000
```

## API

### 表單頁

- `GET /`

### 生成影片

- `POST /generate-video`

Form fields:

- `topic`
- `scene`
- `character`

回傳 JSON 範例：

```json
{
  "job_id": "20260429_120000_ab12cd34",
  "video_path": "output/20260429_120000_ab12cd34/final_video.mp4",
  "subtitle_path": "output/20260429_120000_ab12cd34/subtitles.srt",
  "drive_file_id": "1AbCdEf...",
  "drive_link": "https://drive.google.com/file/d/1AbCdEf.../view?usp=sharing"
}
```

## Docker 部署

```bash
docker build -t ai-video-generator .
docker run --rm -p 8000:8000 --env-file .env ai-video-generator
```

注意：

- Docker image 內已安裝 FFmpeg
- `credentials/` 與 `assets/` 需正確放入容器可讀取的位置

## 背景音樂

請將背景音樂放到：

```text
assets/background_music.mp3
```

若檔案不存在，系統會停止並回報錯誤，避免輸出不完整影片。

## Google Drive 設定重點

1. 在 Google Cloud 建立 Service Account
2. 啟用 Google Drive API
3. 下載 JSON 金鑰至 `credentials/google-drive-service-account.json`
4. 將目標 Drive 資料夾分享給該 Service Account Email

## 備註

- 單次生成 50 張圖片成本與時間都不低，建議先用較小 `IMAGE_COUNT` 測試
- 預設每張圖片 3 秒，總片長約 150 秒
- 若要部署到雲端，可直接放到 VM、Docker 主機或容器平台

## 參考

- OpenAI 官方影像生成文件：
  [Image generation guide](https://developers.openai.com/api/docs/guides/image-generation)
