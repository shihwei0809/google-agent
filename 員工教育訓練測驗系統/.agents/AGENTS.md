# Workspace Rules

## Gemini API — 正確呼叫格式（已踩過坑，禁止再犯）

### ✅ 文字生成 (generateContent)
```
POST https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}
Content-Type: application/json

{
  "contents": [{"parts": [{"text": "...prompt..."}]}]
}
```

### ✅ TTS 語音生成 (Gemini TTS)
```
POST https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}
Content-Type: application/json

{
  "contents": [{"parts": [{"text": "...要朗讀的文字..."}]}],
  "generationConfig": {
    "responseModalities": ["AUDIO"],
    "speechConfig": {
      "voiceConfig": {
        "prebuiltVoiceConfig": {
          "voiceName": "Zephyr"
        }
      }
    }
  }
}
```
- 音訊回傳在 `candidates[0].content.parts[0].inlineData.data`（base64）
- mimeType 若為 `audio/L16` 需用 `pcm_to_wav()` 包成 WAV；若為 `audio/wav` 直接存檔

### ❌ 禁止用以下格式（舊的/錯誤的）
- `POST /v1beta/interactions` — 不存在此端點
- payload 用 `"input"`, `"response_format"`, `"generation_config"` 等欄位 — 這是 OpenAI 格式，Gemini 不接受
- header 用 `x-goog-api-key` + `Api-Revision` — 這是另一個不同 API 的格式

### TTS 可用模型（2026-07）
| 名稱 | API model name |
|------|---------------|
| Gemini 2.5 Flash TTS | `gemini-2.5-flash-preview-tts` |
| Gemini 3.5 Flash TTS | `gemini-3.5-flash-preview-tts` |

### 模型 fallback 原則
呼叫 Gemini 時永遠要有 fallback：選定的 model 失敗 → 自動往下一個 model 重試 → 全失敗才回傳錯誤。

---

## 收工規則（使用者說「收工」時必須執行）

每次使用者說「收工」，必須按以下順序完成：

1. **顯示今日完成項目表格**，格式如下：

| # | 功能 | 狀態 |
|---|------|------|
| 1 | xxx  | ✅   |

2. **自動執行 git add + commit + push**，將本次所有修改推上 GitHub。
   - commit message 格式：`feat/fix(模組名稱): 簡短說明`，body 列出所有變更項目
   - 只 add 有實際修改的核心檔案，排除 log、暫存腳本（*.log, patch_*.py, fix_*.py, test_*.py）

3. **顯示 GitHub 推送結果**，包含：
   - ✅ Commit hash（短版）
   - 🔗 GitHub repo 連結（可點擊的 markdown 連結）
   - 📁 推送的分支名稱

範例格式：

✅ Commit `63c87fd` 已推送至 [shihwei0809/google-agent](https://github.com/shihwei0809/google-agent) — `main` 分支
