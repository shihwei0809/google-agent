---
name: ai-video-generator
description: AI 影音自動剪輯工作站，能將素材（圖片/影片）與文字合成為符合 IG Reels/Shorts 規格的 9:16 短影音。
---

# AI 影音自動剪輯工作站 Skill

當使用者需要：
1. 依據上傳的素材（影片或圖片）與文字劇本，自動輸出成直式 9:16 影片。
2. 自動配音（Edge-TTS）、自動疊加標題卡與動態字幕。

## 執行指令
- 啟動服務：`python main.py` 或執行 `啟動AI影音剪輯工作站.bat`
- 核心渲染模組：`video_generator.py`
  ```python
  from video_generator import render_short_video
  render_short_video(
      source_media="素材路徑.png",
      text_script="旁白內容...",
      output_video_path="輸出路徑.mp4",
      title="影片標題",
      accent_color="#FF7A1A"
  )
  ```
