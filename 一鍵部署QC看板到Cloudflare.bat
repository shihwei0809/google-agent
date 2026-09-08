@echo off
chcp 65001 >nul
echo =====================================================
echo   正在部署 PWA 獨立站點至 Cloudflare Pages (qc-samples)...
echo =====================================================
cd /d "d:\GOOGLE ANGET\說明書\qc-samples"
npx wrangler pages deploy . --project-name=qc-samples --commit-dirty=true
echo.
echo 部署流程結束，請按任意鍵關閉視窗...
pause
