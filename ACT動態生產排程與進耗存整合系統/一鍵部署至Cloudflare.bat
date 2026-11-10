@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo ========================================================
echo [?•æ??Ÿç”¢?’ç??‡é€²è€—å??´å?ç³»çµ±] ä¸€?µéƒ¨ç½²è‡³ Cloudflare Pages
echo ========================================================
echo.

rem ?ªå?è¼‰å…¥?¬ç›®??.env ?–çˆ¶ç´?.envï¼Œæ”¯?´ç„¡äººå€¼å??ªå??¨ç½²
if exist ".env" (
    for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
        set "%%a=%%b"
    )
)
if "%NODE_TLS_REJECT_UNAUTHORIZED%"=="" set NODE_TLS_REJECT_UNAUTHORIZED=0

echo ?? [1/2] æ­?œ¨?¨ç½²?³æ–°ä¸»è?ç¶²å? [prod-planner-pwa] ...
call npx --yes wrangler@4.158.0 pages deploy public --project-name prod-planner-pwa --no-bundle --commit-dirty=true
set DEPLOY_MAIN_STATUS=%ERRORLEVEL%

echo.
echo ?? [2/2] æ­?œ¨?Œæ­¥?¨ç½²?³ç›¸å®¹è?ç¶²å? [act-planner-pwa] (ç¢ºä??Šé€??/?¸ç±¤ä¸å¤±?? ...
call npx --yes wrangler@4.158.0 pages deploy public --project-name act-planner-pwa --no-bundle --commit-dirty=true
set DEPLOY_OLD_STATUS=%ERRORLEVEL%

echo.
if %DEPLOY_MAIN_STATUS% EQU 0 (
    echo ========================================================
    echo [SUCCESS] ?¨ç½²?å?ï¼é?ç¶²å??†å·²?Œæ­¥?¼å?ï¼?
    echo ?? ?°ç?æ­??ç¶²å?: https://prod-planner-pwa.pages.dev
    echo ?? ?¸å®¹?Šç?ç¶²å?: https://act-planner-pwa.pages.dev (?ªå??¡ç¸«å°å??°ç¶²?€)
    echo ========================================================
    start https://prod-planner-pwa.pages.dev
) else (
    echo ========================================================
    echo [?ç¤º] ?µæ¸¬??Cloudflare ?ˆæ??¯èƒ½?€è¦é??°é?è­‰ï?æ­?œ¨?‹å??è¦½?¨ç™»??..
    echo ========================================================
    call npx --yes wrangler login
    echo.
    echo æ­?œ¨ä½¿ç”¨?°æ?æ¬Šé€²è??¨ç½²...
    call npx --yes wrangler@4.158.0 pages deploy public --project-name prod-planner-pwa --no-bundle --commit-dirty=true
    call npx --yes wrangler@4.158.0 pages deploy public --project-name act-planner-pwa --no-bundle --commit-dirty=true
    if %ERRORLEVEL% EQU 0 (
        echo ========================================================
        echo [SUCCESS] ?¨ç½²?å?ï¼?
        echo ?? ?°ç?æ­??ç¶²å?: https://prod-planner-pwa.pages.dev
        echo ========================================================
        start https://prod-planner-pwa.pages.dev
    ) else (
        echo ========================================================
        echo [FAILED] ?¨ç½²ä»æœªå®Œæ?ï¼Œè?ç¢ºè?ç¶²è·¯????–ç™»?¥ç??‹ã€?
        echo ========================================================
    )
)

echo.
pause
