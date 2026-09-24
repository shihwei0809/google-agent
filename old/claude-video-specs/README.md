# claude-video-specs

> 三類影片製作規範 + 自動 bootstrap 流程，給 AI agent 和創作者用。
> **AI agent 讀本 repo 後請立即跑 [AGENTS.md](AGENTS.md) 的 5 階段流程。**

---

## 一句話總結

把「我想做一支影片」這句話，自動分流到三類規範之一，依規範跑完整工作流，最後可打包成可重複呼叫的技能。

---

## Repo 內容

```
claude-video-specs/
├── README.md                    ← 本檔（人類入口）
├── AGENTS.md                    ← AI agent 入口，5 階段 bootstrap
├── GOTCHAS.md                   ← 踩坑筆記（開工前必讀）
├── LICENSE
├── specs/                       ← 三類影片規範（核心）
│   ├── 01-活動紀錄影片.md
│   ├── 01-活動紀錄影片.html     ← 規範視覺化版
│   ├── 02-教學影片.md
│   └── 03-社群科普影片.md
├── examples/                    ← 三個 HTML 範本可 fork
│   ├── 01-marathon-light/
│   ├── 02-factors-multiples/
│   └── 03-ai-context/
└── install/                     ← 自動安裝工具
    ├── check_env.sh
    ├── install_fonts.sh         ← 源石黑體（從 ButTaiwan 下載）
    ├── setup_playwright.sh
    ├── pack_skill.sh            ← 打包成 Claude Skill
    └── install_all.sh           ← 一鍵裝全部 optional 元件
```

**不含任何 binary 素材**（mp4、mp3、png、字體）— 全部透過 bootstrap 動態取得。

---

## 三類影片速覽

| # | 類型 | 片長 | 核心元素 |
|---|------|------|---------|
| **01** | 活動紀錄影片 | 60–180s | 口白 + 大字卡 + BGM 過場 |
| **02** | 教學影片 | 4–8 min | SOIL 教學脈絡 + 動畫 + Edge-TTS |
| **03** | 社群科普影片 | 2–3 min | 強 Hook + 多版面 + 照片佐證 |

完整規範在 [`specs/`](specs/)。

---

## 給 AI Agent 用

當你（AI agent）看到這個 repo：

1. 開啟 [AGENTS.md](AGENTS.md)
2. **先讀階段 0 確認自己的相容性**
3. 從**階段 1 環境檢查**開始
4. 每個階段都要**主動詢問使用者**再進下一步
5. 不要悶頭做，每完成一個里程碑就回報

### 已測試 / 相容性

| Agent | AGENTS.md | Skill 路徑 | 狀態 |
|-------|-----------|----------|------|
| **Claude Code**（CLI + Desktop）| ✅ 原生 | `~/.claude/skills/` | 完整支援 |
| **GPT Codex**（CLI）| ✅ 原生 | `~/.agents/skills/` | 完整支援 |
| **OpenCode**（CLI）| ✅ 透過 `opencode.json` 引導 | `~/.config/opencode/skills/` | 已附 opencode.json |
| **Antigravity**（Desktop）| ⚠️ 部分 | `~/.gemini/antigravity/skills/` | 可能需手動匯入 |
| **Web-only agents** | ❌ 無 shell | n/a | 只能參考 specs，無法跑 install |

---

## 給人類用

```bash
# 1. clone
git clone https://github.com/mathruffian-dot/claude-video-specs.git
cd claude-video-specs

# 2. 環境檢查 + 安裝（任選一個跑法）
#  選項 A：bash（macOS / Linux / Windows Git Bash）
bash install/check_env.sh && bash install/install_all.sh

#  選項 B：PowerShell（Windows 沒裝 Git Bash 的用）
powershell -ExecutionPolicy Bypass -File install/install_all.ps1

#  選項 C：Python（全平台通用，無需 bash）
python install/setup.py check
python install/setup.py all

# 3. 對你的 Claude / Codex / OpenCode / Antigravity 說：
#    「啟動 claude-video-specs」
#    或直接：「我要做一支教學影片」

# Agent 會自動依 AGENTS.md 5 階段流程進行
```

### 打包成技能（任一 agent）

```bash
# Bash 版
bash install/pack_skill.sh my-video 02 --target=claude
bash install/pack_skill.sh my-video 02 --target=codex
bash install/pack_skill.sh my-video 02 --target=opencode
bash install/pack_skill.sh my-video 02 --target=antigravity

# Python 版（同樣四個 target）
python install/setup.py pack my-video 02 --target=claude
```

---

## 設計依據

- **SOIL 教學心法**（李俊儀教授）— spec 02 骨架
- **林長揚 30 原則** — 字級階、配色、留白規則
- **林長揚 #7**「字體選黑體粗體」— 為何選源石黑體
- **林長揚 #1**「黃金比例 55/34/21/13」— 字級階梯

---

## 授權

- 程式碼與規範：**MIT License**
- 字體：源石黑體 SIL Open Font License
- 範例會用到的 Unsplash 照片：Unsplash License

---

## 致謝

[李俊儀教授](https://www.facebook.com/profile.php?id=100007283099373) · [林長揚](https://www.facebook.com/changyanglin) · [ButTaiwan/genseki-font](https://github.com/ButTaiwan/genseki-font) · [Unsplash](https://unsplash.com) · [edge-tts](https://github.com/rany2/edge-tts)
