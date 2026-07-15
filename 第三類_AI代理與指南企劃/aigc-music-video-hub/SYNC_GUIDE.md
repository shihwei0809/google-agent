# 跨電腦雙向同步指南 (Git + Google Drive 混合工作流)

本專案結合了 **Git (GitHub)** 與 **Google Drive** 來實現兩台電腦之間的完美同步：
* **程式碼與文字設定** (小檔案，變動頻繁)：透過 **GitHub** 進行版本控制與同步。
* **影音與圖片多媒體** (大檔案，不適合 Git)：透過 **Google Drive 電腦版** 同步，並配合腳本一鍵導入/導出。

---

## 🛠️ 事前準備

1. **兩台電腦皆需安裝**：
   * [Git](https://git-scm.com/)
   * [Python 3.10+](https://www.python.org/downloads/)
   * [Google 雲端硬碟電腦版](https://www.google.com/intl/zh-TW/drive/download/) (確保 G 槽已掛載，或有同步 `aigc-music-video-hub` 資料夾)。

2. **在 GitHub 上建立一個 Repository**：
   * 建議建立一個 **Private (私有)** 儲存庫（因為包含專案敏感內容）。
   * 命名為 `aigc-music-video-hub`。

---

## 💻 電腦 A (當前開發電腦) 設定

若您尚未將此專案推送至 GitHub，請在終端機執行以下步驟：

```bash
# 1. 建立 Git 追蹤並新增所有程式碼檔案（排除 .gitignore 內定義的 MP3/MP4）
git init
git add .
git commit -m "feat: init project with GDrive sync scripts and grouped dashboard"

# 2. 關聯到您的 GitHub 儲存庫並推送
git branch -M main
git remote add origin https://github.com/您的帳號/aigc-music-video-hub.git
git push -u origin main
```

* **備份大檔案到 Google Drive**：
  在電腦 A 執行以下指令，將 MP3、影片與圖片同步上傳至 Google Drive 備份：
  ```bash
  python sync_to_gdrive.py
  ```

---

## 💻 電腦 B (第二台電腦) 設定

當您在第二台電腦上時，請依序執行以下步驟：

### 1. 複製 GitHub 程式碼
開啟終端機並切換至您想要放置專案的目錄，執行：
```bash
git clone https://github.com/您的帳號/aigc-music-video-hub.git
cd aigc-music-video-hub
```

### 2. 下載 Google Drive 大檔案
1. 確保電腦 B 的 Google 雲端硬碟電腦版已登入，且 `aigc-music-video-hub` 資料夾已同步到本地（預設為 `G:\我的雲端硬碟\aigc-music-video-hub`）。
2. 在電腦 B 專案目錄下執行下載同步腳本：
   ```bash
   python sync_from_gdrive.py
   ```
   *此腳本會自動將雲端硬碟上的 `創作庫` (包含 MP3、MVs、圖片等) 下載並同步至電腦 B 的本機資料夾中。*

---

## 🔄 日常開發同步工作流

當您在**電腦 A** 修改並生成了新歌后：
1. **同步程式碼與歌詞**：
   ```bash
   git add .
   git commit -m "Update new songs lyrics and configs"
   git push
   ```
2. **同步大檔案**：
   ```bash
   python sync_to_gdrive.py
   ```

當您要在**電腦 B** 繼續工作時：
1. **更新程式碼與歌詞**：
   ```bash
   git pull
   ```
2. **更新大檔案**：
   ```bash
   python sync_from_gdrive.py
   ```
