# 📱 家庭手機跨裝置檔案傳輸中心 (Family File Hub)

> 讓家人從各自的手機，不論是在家連 Wi-Fi，或是在外用 4G/5G 行動網路，都能輕鬆建立各自的專屬資料夾並原圖上傳照片、影片與檔案到您的電腦！免安裝 App、免登入、掃碼即用！

---

## 🌟 核心功能亮點

- 🌐 **雙套自動外網隧道 (Ngrok + SSH Dual Tunnel System)**：
  - **第一套系統 (Ngrok)**：原生支援 `ngrok.exe`，自動產生高穩定 `https://xxxx.ngrok-free.app` 網址。
  - **第二套備援系統 (SSH Reverse Tunnel)**：自動備援生成 `https://xxxx.lhr.life`，100% 避免 Cloudflare Error 1033。
- ⚙️ **自訂固定外網網址 (config.txt)**：支援設定您專屬的固定網域、DDNS 或 Tailscale IP！
- 📂 **線上自訂建立資料夾**：點擊「`+ 建立新資料夾`」即可線上新增目錄（如：`2026旅遊照片`、`媽媽工作檔`），並可切換特定資料夾進行檔案瀏覽。
- 🛡️ **100% 原圖無損直傳**：無任何圖片壓縮與轉碼，完整保存原圖高解析度與 EXIF 拍攝參數。
- 📱 **手機端極致 UI (Modern Glassmorphism)**：專為智慧型手機優化，極致美觀深色玻璃擬態介面與相機直拍支援。

---

## 🛠️ 自訂固定外網連線設定教學 (4 種方法)

如果後續您希望設定**固定不變**的外網網址（讓家人手機不必每次掃描新 QR Code），可以採用以下 4 種方式：

### 方法一：綁定您的自訂固定網址/DDNS (最簡單)
1. 開啟專案資料夾內的 `config.txt`。
2. 將您的固定網址填入，例如：
   ```text
   CUSTOM_WAN_URL=https://your-custom-domain.com:8080
   ```
3. 儲存後重啟 `一鍵啟動.bat`，系統就會自動以該固定網址產生外網 QR Code！

---

### 方法二：綁定自己的 Ngrok 免費/付費固定帳號 (AuthToken)
若您有申請 Ngrok 帳號，可以在主控台取得專屬 AuthToken：
1. 開啟 CMD 或 PowerShell 視窗，切換至本專案資料夾。
2. 執行指令綁定金鑰：
   ```cmd
   .\ngrok.exe config add-authtoken <您的Ngrok_AuthToken>
   ```
3. 綁定後，Ngrok 即可解除連線時間限制，並支援固定子網域！

---

### 方法三：使用 Tailscale / ZeroTier 虛擬私有網 (極高安全性)
1. 在您的電腦與家人手機安裝免費的 [Tailscale](https://tailscale.com/) 並登入同一帳號。
2. 取得電腦的 Tailscale 固定 IP (例如 `100.110.120.130`)。
3. 在 `config.txt` 設定：
   ```text
   CUSTOM_WAN_URL=http://100.110.120.130:8080
   ```
4. 家人手機即便在戶外使用 4G/5G，也能直接連線至此固定 IP 上傳檔案！

---

### 方法四：路由器 Port Forwarding (埠號轉發 + DDNS)
1. 在家用 Wi-Fi 路由器設定 Port Forwarding，將外網 Port `8080` 轉發至電腦本機 IP。
2. 在 `config.txt` 填入您的對外固定 IP 或 DDNS 網址：
   ```text
   CUSTOM_WAN_URL=http://your-home-ddns.net:8080
   ```

---

## 📂 檔案目錄結構 (File Tree)

```text
family-file-hub/
├── README.md               # [人類閱讀] 專案說明文件
├── SKILL.md                # [AI助理閱讀] 技能規範說明
├── config.txt              # [自訂設定] 自訂固定外網網址設定檔
├── setup_env.ps1           # [一鍵安裝] PowerShell 自動環境部署腳本
├── app.py                  # [後端核心] Python Flask 伺服器、Ngrok+SSH 雙外網隧道引擎
├── ngrok.exe               # [第一外網] Ngrok 外網隧道執行檔
├── cloudflared.exe         # [備用外網] Cloudflare Tunnel 執行檔
├── templates/
│   └── index.html          # [前端介面] 響應式手機 UI
├── uploads/                # [檔案儲存區] 家人上傳之檔案目錄
├── 一鍵啟動.bat             # [一鍵啟動] Windows 雙擊啟動檔 (ANSI 編碼)
├── start_server.bat        # [純英啟動] 英文檔名備用啟動檔
├── 一鍵開啟電腦儲存資料夾.bat # [一鍵開啟] 自動開啟實體檔案總管
└── open_folder.bat         # [純英開啟] 英文檔名備用開啟檔
```
