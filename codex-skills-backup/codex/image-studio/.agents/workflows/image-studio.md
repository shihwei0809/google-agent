---
name: image-studio
description: 一鍵執行影像創作、8鏡頭序列生成或空拍運鏡處理
---

# /image-studio
請載入 `image-studio` Skill，執行基礎生圖流程：
1. 讀取 `input/` 的參考圖與 `input/environment.txt` 描述。
2. 呼叫 `scripts/image_process.py` 進行比例預處理。
3. 調用 Nano Banana Pro 融合生成新影像。
4. 儲存成品至 `output/`。

# /eight-shots
請載入 `image-studio` Skill，執行 8 鏡頭序列生成流程。
1. 依序產生 8 張（ECU, CU, MCU, Full Body Action, High Angle, Low Angle, Long Shot, Candid）人物一致性影像。
2. 儲存 8 張圖片至 `output/`。

# /drone-effect
請載入 `image-studio` Skill，執行空拍與運鏡處理。
1. 讀取 `input/` 原圖與運鏡命令（Orbit / Push In / Pull Out）。
2. 調用 Nano Banana Pro 生成對應的空拍廣角視角成品。
3. 儲存成品至 `output/`。
