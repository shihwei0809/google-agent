# 🤖 Google Agent 專案 AI 規則與範本庫 (google-agent-rules)

本倉庫用於同步與套用專案開發的 AI 規則，讓不同電腦上的 AI 助理（如 Antigravity / Claude Code）皆能遵循相同的專案引導與一鍵安裝規範。

## ⚙️ 如何在公司或新電腦上套用規則？

1. **下載此規則倉庫**：
   ```bash
   git clone https://github.com/shihwei0809/google-agent-rules.git
   ```
2. **一鍵套用規則**：
   進入資料夾，以管理員權限開啟 PowerShell 並執行：
   ```powershell
   powershell -ExecutionPolicy Bypass -File apply_rules.ps1
   ```
   *這會自動將 `AGENTS.md` 規則複製到全域的 `C:\Users\<您的用戶名>\.gemini\config\` 下，讓所有專案無縫套用。*

## 📝 專案範本標準

每個新專案在建立時，請在該專案根目錄下附帶：
- **`SKILL.md`**：描述專案依賴與執行指令。
- **`setup_env.ps1`**：一鍵安裝專案環境依賴套件。
