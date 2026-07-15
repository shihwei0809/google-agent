@echo off
title 內網伺服器已啟動
chcp 65001 > nul

:: 使用 Python 自動獲取本機內網 IP 位址並顯示說明資訊
python -c "import socket; s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.connect(('8.8.8.8', 80)); ip = s.getsockname()[0]; s.close(); print('='*60 + '\n  📋 員工教育訓練測驗系統 — 內網網頁伺服器\n' + '='*60 + '\n\n  伺服器正在運行中...\n\n  💡 注意事項：\n  1. 請【勿】關閉此視窗，關閉後內網服務將會中斷。\n  2. 同仁的手機或電腦必須連線至與您【相同】的 Wi-Fi 或公司網路。\n\n  📢 同仁請在瀏覽器輸入以下網址開啟測驗（或使用瀏覽器分享功能產生的 QR 碼）：\n  👉 http://' + ip + ':8000/index.html\n\n' + '='*60 + '\n')"

:: 啟動網頁伺服器在 8000 連接埠
python -m http.server 8000
