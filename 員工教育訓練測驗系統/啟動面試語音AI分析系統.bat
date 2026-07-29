@echo off
chcp 65001 > NUL
echo 正在啟動 AI 面試語音特質與逐字稿歸檔系統...
cd /d "%~dp0interview_analyzer"

if not defined GEMINI_API_KEYS (
    if not defined GEMINI_API_KEY (
        echo [提醒] 支援多組 API Key！多組請以半形逗號分隔 (例如: key1,key2,key3)
        set /p GEMINI_API_KEYS=請輸入您的 Gemini API Key(s): 
    )
)

echo 檢查並安裝 Python 依賴庫...
pip install -r requirements.txt

echo 啟動系統 Web 服務 (http://localhost:8000)...
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause
