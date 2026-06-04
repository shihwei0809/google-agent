# 大阪冒險之旅電子書 - 語音校正紀錄檔 (Manga E-book Voice Update Record)

## 📌 更新概述 (Overview)
* **修復項目**：修正「微軟原生 台灣國語」語音來源模式下，主角弟弟「小融 (Taiga)」錯誤使用女生發音的問題。
* **更新日期**：2026年6月4日
* **修復人員**：Antigravity AI 助理

---

## 🔍 問題診斷 (Diagnostic & Root Cause)
1. **設定對齊**：
   在 `generate_neural_audio.py` 中，小融（`taiga`）的發音人已被設定為微軟原生的台灣男聲：
   * 語音模型：`zh-TW-YunJheNeural` (Male)
   * 音高微調：`+35Hz` (將男聲調高，模擬小男孩的聲音)
   * 語速微調：`+15%` (加速模擬活潑小男童的口吻)
2. **根本原因**：
   先前步驟中雖然修改了 python 腳本中的配置，但**並未重新執行腳本生成音檔**，因此 `assets/audio/ms_*.mp3` 仍是使用舊版配置（`zh-TW-HsiaoChenNeural` 女聲）所產生的舊音檔。

---

## 🛠️ 執行修復 (Implementation)
1. **忽略大檔案 (避免 Git 溢出)**：
   在 `test` 目錄下建立 `.gitignore` 檔案，明確忽略 Kokoro 模型目錄 (`kokoro-multi-lang-v1_1/`)，防止 325MB 的 `model.onnx` 等大檔案進入 Git。
2. **重新生成音檔 (Audio Regeneration)**：
   執行語音生成腳本：
   ```bash
   python generate_neural_audio.py
   ```
   腳本已重新連接 Microsoft TTS 伺服器並更新所有微軟原生音檔（`ms_*.mp3`），小融的所有台詞已被覆寫為修正後的男童聲線。
3. **已更新的對話音檔清單**：
   * `ms_p1_p2_d1.mp3`
   * `ms_p1_p3_d1.mp3`
   * `ms_p2_p2_d1.mp3`
   * `ms_p2_p3_d1.mp3`
   * `ms_p3_p1_d1.mp3`

---

## 🧪 驗證與結果 (Verification)
* 經檢查，上述小融音檔的檔案大小均已改變（例如 `ms_p1_p2_d1.mp3` 從 `41.3 KB` 更新為 `38.8 KB`），表示音檔內容已被重新編碼並寫入。
* 目前在微軟原生語音來源模式下，點選「試聽小融」或播放相關四格漫畫對話，小融發出的即是調高音高的自然台灣男童音。

---

## 💡 溫馨提醒 (Tips)
* **瀏覽器快取**：由於瀏覽器快取機制可能導致網頁持續播放舊的音檔，測試時請按 **`Ctrl + F5`** (Windows) 或 **`Cmd + Shift + R`** (Mac) 進行網頁**強制重整**。
