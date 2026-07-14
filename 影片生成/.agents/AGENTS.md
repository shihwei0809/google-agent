# Project Rules

- **Python Execution Command**: Always use the system default `python` command (e.g., `python app.py`) instead of hardcoding absolute paths (like `C:\Python313\python.exe`). This ensures the code and scripts remain portable across different computers.
- **Batch File Encoding**: When writing Windows batch (`.bat`) files, use pure ASCII text for display messages to prevent encoding errors (Big5 vs UTF-8) from misinterpreting Chinese characters as system commands.
