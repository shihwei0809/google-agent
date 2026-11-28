@echo off
chcp 65001 >nul
echo ========================================================================
echo   山獅霸同款全自動 CLI — Wan 2.2 商用劇情短片 (100%% Apache-2.0)
echo   免開瀏覽器｜自動開 G4 → 上傳 → 生片 → NT$50 預算煞車 → 拉回本機 → 自動關機
echo ========================================================================
echo.
set "SCRIPT=C:\GOOGLE ANGET\.agents\skills\sop-cinema-video\scripts\colab_wan22_cli.py"

echo [步驟 1] 檢查 Colab CLI 與運算單元餘額...
python "%SCRIPT%" check
echo.

set /p "FRAMES_DIR=請輸入首幀圖片資料夾路徑 (直接按 Enter 預設為 tank_inbound_sop\flow_frames): "
if "%FRAMES_DIR%"=="" set "FRAMES_DIR=C:\GOOGLE ANGET\blender_3d_demo\tank_inbound_sop\flow_frames"

set /p "OUT_DIR=請輸入成品 MP4 輸出資料夾 (直接按 Enter 預設為 tank_inbound_sop\wan22_clips): "
if "%OUT_DIR%"=="" set "OUT_DIR=C:\GOOGLE ANGET\blender_3d_demo\tank_inbound_sop\wan22_clips"

set /p "BUDGET=請輸入單次預算上限新台幣 (直接按 Enter 預設為 50 元): "
if "%BUDGET%"=="" set "BUDGET=50"

set /p "GPU=請輸入 GPU 型號 G4 / A100 / L4 (直接按 Enter 預設為 G4): "
if "%GPU%"=="" set "GPU=G4"

echo.
echo 即將啟動全自動雲端生片（上限 NT$%BUDGET%，結束自動關機停費）...
python "%SCRIPT%" run --frames-dir "%FRAMES_DIR%" --out-dir "%OUT_DIR%" --budget %BUDGET% --gpu %GPU%
echo.
pause
