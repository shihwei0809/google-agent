---
name: Gmail Organizer
description: 使用 Google Gmail API 自動搜尋、讀取、分析及整理電子郵件。
---

# Gmail Organizer 說明書

本專案提供使用 Python 與 Gmail API 進行電子郵件整理的工具。

## 環境依賴
- Python 3.8+
- pip 套件：`google-api-python-client` `google-auth-oauthlib` `google-auth-httplib2`

## Google Cloud Console 設定指南
若要執行此工具，您必須：
1. 進入 [Google Cloud Console](https://console.cloud.google.com/)。
2. 建立新專案，並在 API 庫中搜尋並啟用 **Gmail API**。
3. 進入「OAuth 同意畫面」(OAuth consent screen)，設定為「外部」(External) 或「測試用」，並將您自己的 Gmail 帳號加入「測試使用者」(Test users)。
4. 進入「憑證」(Credentials) 頁面，點選「建立憑證」 -> 「OAuth 用戶端 ID」(OAuth client ID)。
5. 應用程式類型選擇「桌面應用程式」(Desktop App)，建立後下載 JSON 檔案，將其重新命名為 `credentials.json` 並存放在本專案資料夾下 (`d:\GOOGLE ANGET\gmail-organizer\credentials.json`)。

## 執行與安裝
- **初始化環境**：執行 `./setup_env.ps1`。
- **首次執行（需授權）**：執行虛擬環境中的 `organizer.py`。
  ```powershell
  .venv\Scripts\python.exe organizer.py
  ```
  這會開啟瀏覽器視窗要求您登入並同意授權。完成後會於目錄下生成 `token.json`。
- **整理郵件**：授權完成後，此工具可背景執行：
  ```powershell
  .venv\Scripts\python.exe organizer.py --limit 10
  ```
