# 技能說明：勝一三合一單產生系統 (Shinyi TSMC 3-in-1 Dispatch Generator)

## 專案概要
以「勝一槽車排程 (SNXM101)」與台積電槽車出貨為核心的自動化桌面工具，全面支援勝一 5 大槽車品項（`CPNE4R`=`L2C9173`、`SEP73E4`=`L269100`、`SEP73E5`=`L2C9100`、`PMAHQ`=`L2C9501`、`PMAHQ(R)`=`L2R9501`）、52 筆全廠區指送地正規化、10~11 碼批號槽號提取、TGCM 動態公式、QR Code 生成、5 種不同結構 COA Key-Based 動態寫入，以及 12~16 欄多格式 `Chemical_Lorry` 單列生產履歷輸出。

## 依賴套件 (Requirements)
- python >= 3.10
- openpyxl >= 3.0.0
- qrcode >= 7.0
- pillow >= 9.0.0
- pytesseract >= 0.3.10
- python-docx >= 0.8.11
- pywin32 >= 300

## 執行與啟動指令
- **啟動主程式**：python main.py 或雙擊 啟動_勝一三合一單產生器.bat
- **產出圖文手冊**：python build_manual_doc.py 或雙擊 一鍵產生圖文手冊.bat
- **環境安裝**：執行 setup_env.ps1

## 操作手冊產出規範 (手冊鐵律)
1. **靜態素材庫**：手冊截圖一律使用 manual_assets/（image1.png ~ image6.png、image_coa.png），嚴禁使用即時 ImageGrab 抓圖。
2. **零 Emoji 政策**：手冊內嚴禁使用任何 Unicode Emoji 圖示（避免 Word 渲染出空心方框 □）。
3. **Word COM PDF**：手冊由 Word COM (win32com.client) 轉為純向量高解析 PDF。
