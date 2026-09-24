@echo off
chcp 65001 >nul
echo ===================================================
echo 🚀 IPA 系統 (Cloudflare PWA 版) 本機開發伺服器
echo ===================================================
echo.
echo ⚠️ 啟動前，請確認您已執行過 setup_env.ps1 完成環境與 D1 資料庫設定。
echo.
echo 正在使用 Wrangler 啟動本機測試環境 (包含 API 與 D1 本機模擬)...
echo (請在瀏覽器開啟下方提示的網址，通常為 http://localhost:8788)
echo.

npx wrangler pages dev public
pause
