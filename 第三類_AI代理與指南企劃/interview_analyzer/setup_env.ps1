Write-Host "=========================================" -ForegroundColor Cyan
Write-Host " 正在初始化 interview_analyzer 環境..." -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

python -m pip install -q -r requirements.txt python-docx

Write-Host "環境設定完成！即將啟動 Web 服務..." -ForegroundColor Green
python -m uvicorn main:app --host 0.0.0.0 --port 8000
