@echo off
cd /d "%~dp0"
echo ====================================================================
echo   Peace and Love MV - Google Flow Batch Generator + 1080p Builder
echo ====================================================================
echo.
echo [1] Wave 1: Locked keyframes (s01 s02 s03 s06 s07) - 360p (10 credits/clip)
echo [2] All 19 scenes (auto resume, skip existing) - 360p
echo [3] All 19 scenes (auto resume, skip existing) - 720p
echo [4] Assemble final 1080p MV (Flow clips + keyframes + synced lyrics)
echo.
set /p choice=Select option (1/2/3/4, default 1): 
if "%choice%"=="" set choice=1

if "%choice%"=="1" (
    python -u peace_love_mv\flow_batch_peace_love.py --only s01 s02 s03 s06 s07 --res 360p --duration 10
) else if "%choice%"=="2" (
    python -u peace_love_mv\flow_batch_peace_love.py --start 1 --end 19 --res 360p --duration 10
) else if "%choice%"=="3" (
    python -u peace_love_mv\flow_batch_peace_love.py --start 1 --end 19 --res 720p --duration 10
) else if "%choice%"=="4" (
    python -u peace_love_mv\build_peace_love_mv.py
)
echo.
pause
