# RUNBOOK.md - 本機產出 final.mp4

目前專案已包含：

- `SCRIPT.md`
- `DESIGN.md`
- `ASSETS.md`
- `index.html`
- `generate_narration.py`
- `record.cjs`
- `render.py`
- `QA.md`

## 1. 進入專案

```powershell
Set-Location "G:\我的雲端硬碟\新自動生成影片\ai-context-video"
```

## 2. 設定 UTF-8

```powershell
$env:PYTHONUTF8 = "1"
```

## 3. 安裝必要工具

需要：

- Python 3.8+
- Node.js 18+
- ffmpeg
- edge-tts
- Playwright

安裝 Python 套件：

```powershell
python -m pip install edge-tts
```

Playwright 不要裝在 Google Drive 目錄，請裝在 `%TEMP%`：

```powershell
$work = Join-Path $env:TEMP "cvs-render"
New-Item -ItemType Directory -Force -Path $work | Out-Null
Set-Location $work
npm init -y
npm install playwright
npx playwright install chromium
$env:NODE_PATH = "$env:TEMP\cvs-render\node_modules"
```

再回到專案：

```powershell
Set-Location "G:\我的雲端硬碟\新自動生成影片\ai-context-video"
```

## 4. 渲染

```powershell
python .\render.py
```

成功後會產出：

```text
G:\我的雲端硬碟\新自動生成影片\ai-context-video\final.mp4
```

## 5. 抽截圖 QA

```powershell
New-Item -ItemType Directory -Force -Path .\renders\frames | Out-Null
ffmpeg -y -ss 00:00:05 -i .\final.mp4 -frames:v 1 .\renders\frames\frame-005.png
ffmpeg -y -ss 00:00:20 -i .\final.mp4 -frames:v 1 .\renders\frames\frame-020.png
ffmpeg -y -ss 00:00:40 -i .\final.mp4 -frames:v 1 .\renders\frames\frame-040.png
ffmpeg -y -ss 00:01:00 -i .\final.mp4 -frames:v 1 .\renders\frames\frame-060.png
ffmpeg -y -ss 00:01:30 -i .\final.mp4 -frames:v 1 .\renders\frames\frame-090.png
ffmpeg -y -ss 00:02:00 -i .\final.mp4 -frames:v 1 .\renders\frames\frame-120.png
ffprobe -v error -show_streams .\final.mp4
```

## 6. 同步技能備份到雲端

影片完成與 QA 後，回到工作區根目錄並同步技能備份：

```powershell
Set-Location "G:\我的雲端硬碟\新自動生成影片\cloud-skill-backup"
.\sync-after-render.ps1
```

另一台電腦等 Google Drive 同步完成後，進入同一個 `cloud-skill-backup` 資料夾執行：

```powershell
.\install-or-update.ps1
```

## 備註

- BGM 是用 ffmpeg `aevalsrc` 自動生成的 ambient 音床，沒有使用外部商業音樂。
- 視覺素材是 HTML/CSS/SVG 自製，未使用外部圖片。
- 若 `edge-tts` 暫時連線失敗，重新執行 `python .\render.py` 即可續跑已完成的音檔。
