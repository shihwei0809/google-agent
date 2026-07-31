# 📱 家庭手機跨裝置檔案傳輸中心 (family-file-hub)

## 專案簡介
本專案為一個零設定、免安裝 App 的 Web 系統，專為讓家庭成員透過手機將照片、影片、文件與音樂傳輸至電腦而設計。支援**區域網路 (Wi-Fi)** 與 **Ngrok + SSH 雙套外網隧道系統**，並提供**線上建立與切換自訂資料夾**及 **100% 原圖無損直傳** 功能。

---

## 依賴環境與套件
- **Python**: 3.8+
- **依賴套件**: `flask`, `qrcode`, `pillow`, `waitress`, `pyngrok`
- **外網第一套系統**: `ngrok.exe` (Ngrok Tunnel)
- **外網第二套系統**: OpenSSH Tunnel (Windows 內建 SSH / `localhost.run`)
- **一鍵安裝腳本**: `setup_env.ps1`
- **本機 Server Port**: 預設 8080 (支援 Port 佔用自動切換至 8081, 8082...)

---

## 核心 API
- `GET /api/info`: 取得本機 IP、Port、區網/外網網址與 QR Code。
- `GET /api/folders`: 取得目前所有資料夾與檔案計數。
- `POST /api/create_folder`: 線上動態建立新資料夾。
- `POST /api/upload`: 100% 原圖無損上傳檔案至指定資料夾。
- `GET /api/files`: 取得所有已上傳檔案清單。
- `POST /api/delete`: 刪除指定檔案。

---

## AI 助理維護與引導規範 (Guiding Instructions)

1. **初始化與套件確認**：
   - 當開啟此專案時，若發現未安裝套件，AI 應主動提示使用者執行 `.\setup_env.ps1`。
2. **雙系統運作機制**：
   - 第一套系統以 `ngrok.exe` 優先建立 HTTPS 隧道，第二套系統以 `ssh` 備援，保障外網永久通暢。
3. **說明書同步**：
   - 若新增任何功能，必須同步更新 `SKILL.md`、`README.md` 及 `setup_env.ps1`。
