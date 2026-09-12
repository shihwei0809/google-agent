# 勝一三合一單產生系統 - 一鍵環境安裝腳本
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host " 正在為 [勝一三合一單產生系統] 安裝必要 Python 套件..." -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

pip install openpyxl qrcode pillow pytesseract python-docx pywin32 --upgrade

Write-Host "
環境套件安裝完成！您可以直接執行 [啟動_勝一三合一單產生器.bat] 開啟系統。" -ForegroundColor Green
