@echo off
chcp 65001 >nul
echo ==================================================
echo       🚀 GOOGLE AGENT 專案一鍵下載/同步工具
echo ==================================================
echo.

echo [1/2] 正在更新總大廳 (git pull)...
git pull
echo.

echo [2/2] 正在檢查並下載所有獨立的子專案...
set REPOS=ipa-production-scheduler ipahq-tanker-confirm ipahq-tanker-scan-app n-series-barcode-verify n-series-php-barcode-api n-series-gas-apk-offline n-series-shipping-php qc-factory-digitize triple-form-php-migration temperature-alert hose-keycode-manager ai-agent-guide ai-voice-cloner-guide aigc-music-video-hub clasp-netlify-mcp-guide claude-html-slide-builder claude-video-specs google-classroom-agent grad-trip padlet-board skincare-product-guide

for %%R in (%REPOS%) do (
    if not exist "%%R\" (
        echo 📥 正在下載 %%R...
        git clone https://github.com/shihwei0809/%%R.git
    ) else (
        echo ✅ [已存在] %%R 
    )
)

echo.
echo ==================================================
echo 🎉 全部子專案檢查與下載完成！現在您的環境已是最完整的狀態。
echo ==================================================
pause
