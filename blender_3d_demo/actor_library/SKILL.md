---
name: actor-library
description: 固定 AI 演員班底庫（25/35/45 歲台灣男女各 1 位），供 MV（mv_flow_runner.py）與企業 SOP 微電影（sop-cinema-video）重複調用。
---

# Actor Library Skill

## 使用時機
當使用者要製作新的 MV 或企業 SOP 微電影、需要指定固定男女主角（25 / 35 / 45 歲）時，優先讀取本目錄的 `actors.json` 與 `refs/<id>_ref.jpg`，不要重新從頭抽臉。

## 呼叫流程
1. 讀取 `actor_library/actors.json`，依題材或使用者點名的代號（`f25`/`m25`/`f35`/`m35`/`f45`/`m45`）取得 `ref_image` 與 `anchor_en`。
2. 產生鎖定關鍵影格（Nano Banana 2.1）或 Google Flow 影片時，務必附掛 `actor_library/refs/<id>_ref.jpg` 作為角色參考圖，並於英文 prompt 開頭加入該演員的 `anchor_en`。
3. 如更換某位演員的定裝照，執行 `python build_roster.py` 更新 `固定演員班底總覽圖.png`。

## 環境依賴
- Python 3.10+
- `pillow`（執行 `.\setup_env.ps1` 可自動安裝）
