@echo off
chcp 65001 >nul
cd /d "%~dp0\.."
echo ========================================================================
echo   30 秒副歌連續故事短片 — Google Flow 360p 尾幀接龍版 (共 60 點)
echo ========================================================================
echo.
if not exist "story_30s_demo\frames\s01_cafe_door.png" (
    echo [提示] 找不到錨點圖 1：story_30s_demo\frames\s01_cafe_door.png
    pause
    exit /b 1
)
if not exist "story_30s_demo\frames\s04_letter_closeup.png" (
    echo [提示] 找不到錨點圖 2：story_30s_demo\frames\s04_letter_closeup.png
    pause
    exit /b 1
)

python -u mv_flow_runner.py --project story_30s_demo --res 360p --duration 5
if errorlevel 1 (
    echo [錯誤] Google Flow 生成未完成，請檢查上方訊息。
    pause
    exit /b 1
)

echo.
echo [組裝] 正在將 6 段連續分鏡 + 副歌 30s 音軌 + 同步字幕合為 1080p 成片...
python -u mv_builder.py --project story_30s_demo
echo.
pause
