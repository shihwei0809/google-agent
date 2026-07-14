# Project Rules

- **Python Execution Command**: Always use the system default `python` command (e.g., `python app.py`) instead of hardcoding absolute paths (like `C:\Python313\python.exe`). This ensures the code and scripts remain portable across different computers.
- **Batch File Encoding**: When writing Windows batch (`.bat`) files, use pure ASCII text for display messages to prevent encoding errors (Big5 vs UTF-8) from misinterpreting Chinese characters as system commands.
- **收工備份規範**：當收到「收工備份」指令時，除了同步本地程式至 Google 雲端硬碟備份以外，必須自動執行 Git 提交（git commit）並上傳（git push）至 GitHub 專案庫，確保程式在雲端硬碟與 GitHub 上都是最新版本。
