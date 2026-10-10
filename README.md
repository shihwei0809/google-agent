# LINE 飲食熱量精算師：Gemini 2.5 + GAS 完全建置手冊

這是一個自動產生「LINE 飲食熱量精算師」教學 PDF 與 PPTX 的專案。

## 專案結構

- `tutorial_source.txt`: 教學手冊的原始文字內容。
- `generate_docs.py`: 用於將文字內容轉換為 PDF 與 PPTX 的 Python 腳本。
- `LINE_Diet_Bot_Tutorial.pdf`: 產生出的 PDF 手冊。
- `LINE_Diet_Bot_Tutorial.pptx`: 產生出的 PPTX 簡報。
- `requirements.txt`: Python 依賴套件清單。

## 如何在其他電腦上執行與更新

如果您需要修改教學內容並重新產生檔案，請按照以下步驟操作：

1. **安裝 Python**
   請確保您的電腦上已安裝 Python 3 (建議 3.8 以上版本)。

2. **安裝所需套件**
   開啟終端機 (Terminal) 或命令提示字元 (CMD)，進入本專案資料夾後，執行以下指令安裝依賴套件：
   ```bash
   pip install -r requirements.txt
   ```

3. **修改內容**
   您可以直接編輯 `generate_docs.py` 腳本中的 `text_content` 變數，或者修改裡面的文字段落。
   (若後續改為讀取 `tutorial_source.txt`，請修改對應檔案)。

4. **重新產生檔案**
   執行以下指令：
   ```bash
   python generate_docs.py
   ```
   程式會自動覆蓋並產生最新的 `LINE_Diet_Bot_Tutorial.pdf` 與 `LINE_Diet_Bot_Tutorial.pptx`。

## 注意事項
- 產生 PDF 時，腳本會嘗試使用 Windows 內建的微軟正黑體 (`C:\Windows\Fonts\msjh.ttc`) 以支援中文字元。如果您使用 Mac 或 Linux，請修改 `generate_docs.py` 內的字體路徑。
