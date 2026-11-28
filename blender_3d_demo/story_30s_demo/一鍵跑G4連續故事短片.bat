@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================================================
echo   30 秒副歌連續故事型 AI 動畫 — 山獅霸 G4 (Wan 2.2 尾幀接龍版)
echo ========================================================================
echo.
if not exist "frames\s01_cafe_door.jpg" (
    echo [提示] 請先放入 2 張錨點首幀圖到 frames\ ：
    echo   1. frames\s01_cafe_door.jpg
    echo   2. frames\s04_letter_closeup.jpg
    echo.
    pause
    exit /b 1
)
if not exist "frames\s04_letter_closeup.jpg" (
    echo [提示] 缺少第 2 張反打錨點圖：frames\s04_letter_closeup.jpg
    pause
    exit /b 1
)

set "SCRIPT=C:\GOOGLE ANGET\.agents\skills\sop-cinema-video\scripts\colab_wan22_cli.py"
python "%SCRIPT%" run --jobs "%~dp0video_jobs.json" --frames-dir "%~dp0frames" --out-dir "%~dp0clips" --budget 50 --gpu G4
if errorlevel 1 (
    echo [錯誤] Colab G4 執行未完成，請檢查上方訊息。
    pause
    exit /b 1
)

echo.
echo [合成] 正在串接 6 段連續分鏡 + 副歌 30s 音軌 + 同步字幕 ...
(
    echo file 'clips/s01_push_door.mp4'
    echo file 'clips/s02_look_around.mp4'
    echo file 'clips/s03_approach_letter.mp4'
    echo file 'clips/s04_open_letter_reverse.mp4'
    echo file 'clips/s05_window_sunlight.mp4'
    echo file 'clips/s06_walk_to_sunset.mp4'
) > concat_list.txt

ffmpeg -y -f concat -safe 0 -i concat_list.txt -i "audio\chorus_30s.mp3" -vf "ass=chorus_30s.ass" -c:v libx264 -crf 18 -pix_fmt yuv420p -c:a aac -b:a 192k -shortest story_30s_final.mp4
echo.
echo 完成！成片位於：%~dp0story_30s_final.mp4
pause
