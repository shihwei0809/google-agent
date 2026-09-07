@echo off
chcp 65001 >nul
echo ========================================================
echo   正在部署 PWA 看板至 Cloudflare Pages (專案: qc-samples)
echo ========================================================
echo 若尚未登入，瀏覽器將自動開啟授權頁面，請點擊【Allow】即可。
echo.
npx wrangler pages deploy . --project-name=qc-samples --commit-dirty=true
echo.
echo 部署指令執行完成！
pause

