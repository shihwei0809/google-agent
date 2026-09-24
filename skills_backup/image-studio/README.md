# 影像創作工作室專案 (image-studio)

本專案將「生8張圖」、「極簡生圖機器人」與「空拍/運鏡控制」三大 Gem 升級整合為一條可重複執行的影像創作工作流。

**固定的是流程＋規格（凍在 Skill / 本檔 / scripts），浮動的是材料（每次丟 `input/`）。**

## 固定偏好（每次套用）
- 回應一律用繁體中文。
- 專注於影像的生成，不輸出多餘文字或解釋（極簡規則）。
- 當有上傳圖片在 `input/` 時，將其作為視覺基底（Visual Baseline），精確鎖定人物的面部特徵、髮型、瞳色、服裝等。
- 生圖輸出位置：`output/`。

## 怎麼用
1. 將基底參考圖與風格/運鏡要求（以文字描述，如 `environment.txt`）丟進 `input/`。
2. 執行對應的運鏡/生圖工作流：
   - `/image-studio` : 依基底參考圖生成與環境融合的單張高階影像。
   - `/eight-shots` : 根據參考圖依序生成 ECU, CU, MCU, Full Body Action, High Angle, Low Angle, Long Shot, Candid 8 張連貫動作影像。
   - `/drone-effect` : 將輸入圖片轉化為高空、廣角的空拍視角（可選 Orbit, Push In, Pull Out 運鏡）。
3. 到 `output/` 目錄取回您的影像。
