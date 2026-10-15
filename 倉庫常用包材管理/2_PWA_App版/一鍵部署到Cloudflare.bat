@echo off
chcp 65001 >nul
title ??????????? Cloudflare Pages (eshine-package)
color 0b

echo ========================================================
echo    ?? ??? ???? PWA ??? Cloudflare Pages...
echo    ????: eshine-package
echo    ????: https://eshine-package.pages.dev
echo ========================================================
echo.

npx wrangler pages deploy . --project-name=eshine-package --commit-dirty=true

echo.
echo ========================================================
echo [?] ???????????????:
echo     https://eshine-package.pages.dev
echo ========================================================
pause