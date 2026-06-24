# Claude HTML Slide Builder - 操作說明書

> 🔗 **GitHub 專案庫**：[shihwei0809/google-agent](https://github.com/shihwei0809/google-agent)


## 專案簡介
此工具為專門設計給 Claude Code/Antigravity 使用的 Skill，能將純文字教材或教學大綱，自動重構並轉換為 Reveal.js 的互動式網頁簡報。

## 主要功能特色
- **Reveal.js 簡報框架**：自動配置翻頁動畫、程式碼高亮、與響應式排版。
- **動態文字雲**：整合 wordcloud2.js 渲染即時問卷結果。
- **GitHub Actions 自動部署**：簡報產出後，可自動打包並發布至 GitHub Pages。

## 技術棧
- Python 3, Reveal.js, wordcloud2.js

## 操作步驟
1. 將純文字教材放入 `input.txt`。
2. 執行 Python 簡報建置腳本：
   ```bash
   python build_slides.py
   ```
3. 產出的簡報檔案為 `index.html`，可直接使用瀏覽器播放。
