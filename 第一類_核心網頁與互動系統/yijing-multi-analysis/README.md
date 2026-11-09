# 易見｜多重命理分析 (`yijing-multi-analysis`)

以出生資料、生活情境與易經提問，產生可比較的個人參考報告。本公開測試版為**純前端瀏覽器計算**之繁體中文單頁式應用程式（SPA），不建立會員、不傳送或儲存任何個人出生資料至伺服器。

## 核心功能亮點

- **100% 前端隱私保護**：出生日期、十二時辰、出生地、性別、易經提問與財務情境全數在瀏覽器記憶體內完成計算，零遠端資料外洩。
- **多重情境動態重組**：支援 4 種收入來源、5 種投資項目、4 階段資產目標、3 級風險承受度、3 大研究方向與 3 種分析深度。切換任一選項皆會即時重組完整段落與行動建議。
- **易經提問與隨機六爻反思**：提供具體提問引導與視覺化六爻線條起卦提示，強調自我反思與風險邊界，摒棄宿命預言或迷信視覺。
- **列印與另存 PDF 支援**：內建 `@media print` 專屬排版樣式，點擊「列印／另存 PDF」即可隱藏表單與按鈕，輸出乾淨的 A4 分析報告。
- **無障礙與手機響應式設計**：支援 `375px` 手機窄螢幕單欄檢視與桌機雙欄／三欄排版，具備完整 ARIA 標籤與表單必填驗證。

## 檔案結構說明

```text
yijing-online-site/
├── public/
│   └── index.html      # 單頁式前端主程式（含視覺樣式、無障礙表單與 YIJING_CONFIG 分析引擎）
├── src/
│   └── worker.js       # Cloudflare Worker 靜態資源派送與資安標頭（nosniff / Referrer-Policy）
├── wrangler.jsonc      # Cloudflare Workers Static Assets 部署設定檔
└── README.md           # 專案架構與部署說明書
```

## 本機預覽與部署步驟

### 1. 本機直接預覽
可直接以瀏覽器開啟 `public/index.html`，或於專案根目錄執行 Wrangler 本機開發伺服器：

```bash
npx wrangler dev
```

### 2. 部署至 Cloudflare Workers Static Assets
確認已登入 Cloudflare 帳號後，於本目錄執行：

```bash
npx wrangler deploy
```
