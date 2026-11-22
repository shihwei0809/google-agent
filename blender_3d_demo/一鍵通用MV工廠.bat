@echo off
cd /d "%~dp0"
echo ====================================================================
echo   Universal AI MV Factory (Google Flow Agent + 1080p Assembler)
echo ====================================================================
echo.
echo Available MV projects (folders containing storyboard.json):
for /d %%D in (*) do (
    if exist "%%D\storyboard.json" echo   - %%D
)
echo.
set /p proj=Enter project folder name (default: peace_love_mv): 
if "%proj%"=="" set proj=peace_love_mv

echo.
echo Project selected: [%proj%]
echo [1] Generate ALL missing scenes on Google Flow (360p, 10 credits/clip)
echo [2] Generate ALL missing scenes on Google Flow (720p, high res)
echo [3] Re-generate specific scenes (--only, e.g. s04 s09 s12)
echo [4] Assemble final 1080p MV (with synced lyrics subtitles)
echo [5] Assemble final 1080p MV (clean version, NO subtitles)
echo.
set /p choice=Select action (1/2/3/4/5, default 4): 
if "%choice%"=="" set choice=4

if "%choice%"=="1" (
    python -u mv_flow_runner.py --project "%proj%" --res 360p --duration 10
) else if "%choice%"=="2" (
    python -u mv_flow_runner.py --project "%proj%" --res 720p --duration 10
) else if "%choice%"=="3" (
    set /p shots=Enter shot IDs separated by space (e.g. s04 s09 s12): 
    set /p res=Resolution (360p or 720p, default 360p): 
    if "%res%"=="" set res=360p
    python -u mv_flow_runner.py --project "%proj%" --only %shots% --force --res %res% --duration 10
) else if "%choice%"=="4" (
    python -u mv_builder.py --project "%proj%"
) else if "%choice%"=="5" (
    python -u mv_builder.py --project "%proj%" --no-subtitles
)
echo.
pause
