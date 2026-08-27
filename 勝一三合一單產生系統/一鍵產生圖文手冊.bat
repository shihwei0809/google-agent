@echo off
chcp 65001 >nul
echo 正在產出 [勝一三合一單產生系統] 圖文步驟操作手冊...
python build_manual_doc.py
echo 手冊產生完畢！已產出 Word 與 PDF 檔案。
pause
