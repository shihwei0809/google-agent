# 孟菲斯風格簡報策劃專案 (memphis-slide-planner)

本專案升級自 `ppt策劃` Gem，旨在將純文字的指令、教案大綱或工作大綱，自動化轉譯並輸出為極具活力的「孟菲斯波普風格（Memphis Design & Pop Art）」簡報投影片（`.pptx` 或 Reveal.js 的 `.html` 格式）。

**固定的是流程＋規格（凍在 Skill / 本檔 / scripts），浮動的是材料（每次丟 `input/`）。**

## 固定偏好（每次套用）
- 回應一律用繁體中文。
- 嚴格遵守孟菲斯波普美學規範：
  * **背景底色**：淺奶油色 `#FFFDF0`。
  * **字體搭配**：標題使用普惠體 (`Alibaba PuHuiTi 3.0 Extra Bold`)，內文使用霞鶩文楷 (`LXGW WenKai`)。
  * **配色組合**：主體字為炭黑色 `#1A1A1A`，強調色為電力黃 `#FFE000`、珊瑚紅 `#FF4D4D` 與電光藍 `#2E5BFF`。
  * **版面與視覺細節**：
    1. **Style A (開頭/大標)**：標題字後方設置粗邊框實心色塊（加黑底陰影），右下角點綴大圓與直角三角實心黑拼貼。
    2. **Style B (條列/對比)**：左側配置垂直的粗邊框實心色塊邊條，右上角重疊雙層不同色塊圓形，內容字體向右縮排避開裝飾。
    3. **Style C (總結/展望)**：底部配置全寬的雙層實心黑影裝飾條，右上角繪製懸浮立體菱形色塊。
  * **比例規格**：嚴格保持 16:9。

## 怎麼用
1. 將簡報大綱、文字材料或大綱說明放入 `input/slide_outline.txt`。
2. 執行計算與生成工作流：
   - `/memphis-ppt` : 根據材料大綱生成對應孟菲斯風格的 PowerPoint (`.pptx`) 簡報。
3. 到 `output/` 目錄取回您的簡報成品。

## 進階優化與更好的生成方式 (Better Slide Generation Workflows)

根據網路最佳實踐，有以下兩種比純程式碼繪製更高效、美觀的簡報生成方式：

### 1. 樣板優先工作流 (Template-First Workflow) - 視覺設計的首選方案
與其用 Python 代碼一筆一筆畫出幾何圖形和邊框（容易導致排版混亂與冗長的坐標計算），最好的做法是：
* **步驟一**：先在 PowerPoint 中手動設計一個包含 Slide Master（投影片母片）與 Placeholders（版面配置區）的孟菲斯風格樣板檔 `template.pptx`。
* **步驟二**：在 Python 腳本中載入該樣板：`prs = Presentation('template.pptx')`。
* **步驟三**：利用 `prs.slides.add_slide(prs.slide_layouts[x])` 新增投影片，並直接取代 `slide.placeholders[x].text` 中的文字。
* **優點**：視覺設計完全交給 PowerPoint 母片管理，Python 程式碼僅負責資料填入。若要更改設計，只需替換 `template.pptx`，無須修改任何 Python 程式碼。

### 2. Markdown 轉 PPTX 工具鏈 (Marp/Markdown to PPTX)
如果要開發高度靈活的純文字轉簡報系統，可以使用開源工具：
* **`marp2pptx` 庫**（或 `mdtopptx`）：這類庫可以讀取標準 Marp/Markdown 語法，並將其自動轉換為 PowerPoint 的原生幾何形狀與文字框（**非靜態圖片**，生成後仍可在 PowerPoint 中任意編輯）。
* **優點**：自動計算字型測量與換行折返（對繁體中文友善），程式碼極度精簡，適合由 AI 寫好 Markdown 後直接一鍵轉譯成簡報。

