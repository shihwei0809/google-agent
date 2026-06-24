# 聲音轉文字 (NoType 語音助理) - 操作說明書

> 🔗 **GitHub 專案庫**：[shihwei0809/google-agent/tree/main/聲音轉文字](https://github.com/shihwei0809/google-agent/tree/main/聲音轉文字)


## 專案簡介
NoType 是一個本機安裝的語音助理，允許使用者按下快捷鍵進行快速錄音，並自動透過 Whisper / Groq API 轉成文字，隨後模擬鍵盤將文字自動輸入至目前游標所在的任何應用程式中。

## 主要功能特色
- **全域快捷鍵**：可在任何視窗下按下快捷鍵觸發錄音。
- **自動打字輸入**：識別完成後，免手動貼上，程式會模擬鍵盤直接打字輸入。
- **設定面板**：支援設定 API KEY、AI 模型推薦、以及快捷鍵綁定。

## 技術棧
- 框架：Electron (Node.js)
- API 服務：OpenAI Whisper API / Groq API

## 本機執行與操作
1. 雙擊執行 `聲音轉文字` 目錄底下的 `start.bat`。
2. 啟動後會在系統右下角系統匣（Tray）運行。
3. 按下設定好的錄音快捷鍵，說完話後再次按下快捷鍵，系統將自動在您光標位置輸入識別後的文字。
