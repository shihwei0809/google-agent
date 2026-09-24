# 孟菲斯風格簡報策劃專案 (memphis-slide-planner)

本專案升級自 `ppt策劃` Gem，旨在將純文字的指令、教案大綱或工作大綱，自動化轉譯並輸出為極具活力的「孟菲斯波普風格（Memphis Design & Pop Art）」簡報投影片（`.pptx` 或 Reveal.js 的 `.html` 格式）。

**固定的是流程＋規格（凍在 Skill / 本檔 / scripts），浮動的是材料（每次丟 `input/`）。**

## 固定偏好（每次套用）
- 回應一律用繁體中文。
- 嚴格遵守孟菲斯波普美學規範：
  * **背景底色**：淺奶油色 `#FFFDF0`。
  * **字體搭配**：標題使用普惠體 (`Alibaba PuHuiTi 3.0 Extra Bold`)，內文使用霞鶩文楷 (`LXGW WenKai`)。
  * **配色組合**：主體字為炭黑色 `#1A1A1A`，強調色為電力黃 `#FFE000`、珊瑚紅 `#FF4D4D` 與電光藍 `#2E5BFF`。
  * **視覺細節**：粗重黑色輪廓線、幾何拼貼塊、半色調網點 (Halftone Dots) 及故意偏移的色塊。
  * **比例規格**：嚴格保持 16:9。

## 怎麼用
1. 將簡報大綱、文字材料或大綱說明放入 `input/slide_outline.txt`。
2. 執行計算與生成工作流：
   - `/memphis-ppt` : 根據材料大綱生成對應孟菲斯風格的 PowerPoint (`.pptx`) 簡報。
3. 到 `output/` 目錄取回您的簡報成品。
