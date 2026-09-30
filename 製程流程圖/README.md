# ChemFlow Pro 雲端版

*   **核心功能**：工業製程動態流向編輯、Cloudflare D1 雲端存檔、AI 助手問答、AI 設備建圖生成。
*   **檔案結構**：
    *   `public/`: PWA 與前端靜態檔案 (包含主程式 index.html)。
    *   `functions/api/`: Cloudflare Pages Functions 後端 (儲存與 AI)。
    *   `schema.sql`: D1 資料庫結構。
*   **部署方式**：執行 `setup_env.ps1` 進行一鍵安裝與 Cloudflare 部署。