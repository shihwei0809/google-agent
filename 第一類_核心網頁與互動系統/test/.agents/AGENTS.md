# Workspace Customization Rules

## 1. 專案說明書與手冊備份規則
*   **規則描述**：往後當建立、修正、或產出系統內部的設計手冊、操作手冊、說明書等 `.md` 格式之 Artifacts 時，**除了在系統預設路徑產生外，必須同時在本地專案目錄（`D:\GOOGLE ANGET\test\...`）中對應的子資料夾下多產生/複製一份**。
*   **目的**：以利使用者能直接在本地目錄中打包，並上傳至雲端硬碟進行備份。
*   **範例**：
    *   在 `.gemini/antigravity/brain/.../manual.md` 產出時，需同步在 `D:\GOOGLE ANGET\test\manual.md`（或其子目錄）下產生/複製一份。
