## 2026-09-24 交接紀錄
- **完成項目**：
  - 鴻勝（桌機版/網頁版）：新增「出貨區」欄位，支援貼上自動判定「崙尾」或「彰濱二廠」，並與「地點」交叉比對自動帶出對應的特殊料號（L12C53162 等）。
  - 勝一（桌機版/網頁版）：於地點代號對照表新增「品名」直行欄位（如 IPA, EBR），並在介面上新增自動帶出對應特殊料號功能。
  - 網頁版 index.html 與後端 server.py 已完全同步最新邏輯。
  - 修復無資料時的預設料號硬碼問題，改為完全依賴 Excel 對照表。
- **待辦項目**：無。系統已正式升級為 v2.2.0。

## 2026-09-23 交接事項 (最新同步)
- QC_Samples (QC系統客製化電子化工廠)：新增 PWA 獨立列印設定介面，可保存列印偏好並一鍵出單，免除重複確認視窗。
- 專案大廳 (agent-portal)：因 Cloudflare Git 整合建置失敗，改由 wrangler pages deploy 直接上傳發布，已確認更新上線。
- 修正 TSMC eCOA 上傳問題：將 CSV 存檔編碼改為 Big5 以解決 BOM 導致的 SchemaName 判讀錯誤。
- 取消 CSV 檔不必要的全行逗號填充，改為精準補齊，符合台積電解析規範。
- 修復廠區代號擷取邏輯，改用 Regex 正則表達式抓取英數字，解決 18P3A 遭誤切斷為 8P3A 的問題。

## 2026-09-21 交接事項
- 修正「三合一單自動產生器」與「三合一單網頁架構伺服器」的 COA 檔案重新命名邏輯。
- 統一改為嚴謹格式：[原始產品前綴] [月日MMDD] [廠區代號]_[批號].xlsx。

## 2026-09-19 交接事項
- 修正勝一系統 (本機與伺服版) T1 批號驗證邏輯 (嚴格比對大寫 T1，並加寬槽號顯示欄位)。
- 修正鴻勝系統 (本機與伺服版) 嚴格限制批號長度為 10 碼 (移除 10~11 碼殘留)，並修正 COA 命名加日期的 Bug。
- 改善伺服版 COA 及生產履歷上傳之 UI 體驗，將比對訊息獨立顯示於排程表格下方，避免覆蓋地點對照表狀態。
- 為勝一、鴻勝的本機與伺服版，全面補上生產履歷載入時的「批號比對」預覽功能，協助提早發現漏打或錯打的批號。

## 2026-09-25 收工交接
- **今日完成事項**:
  1. 針對先前的三大更新 (Gemini 3.8 Flash, Pollinations.ai 自動生圖, Cloudflare 一鍵部署)，全面補齊並更新了對應的操作手冊說明。
  2. 修改了 sop_generator 目錄下的 SOP操作說明書.md (及其 HTML/TXT 衍生檔)。
  3. 修改了 sop_generator\index.html 內嵌的 README.md 模板，確保未來使用者打包教材時能獲取最新版「方案 D：Cloudflare 一鍵上雲端」教學。
- **遺留問題 / 待確認**:
  - 目前系統操作手冊已對齊最新進度，無特殊遺留問題。

### 📂 跨專案異動掃描 (今日所有更新檔案)
- **[專案根目錄]**
  - HANDOVER.md
  - check_readme.py
  - check_readme2.py
  - check_readme_end.py
  - convert_manuals.py
  - rewrite_md.py
  - update_index_readme.py
  - update_index_readme2.py
  - update_index_readme3.py
  - update_index_readme4.py
  - update_index_readme5.py
  - verify_readme.py
  - verify_readme2.py
  - verify_readme3.py
  - verify_readme4.py
- **IPA 專用動態生產排程與進耗存整合系統/**
  - 2_PWA_App版/.wrangler/tmp/pages-2uBUv8/_routes-0.24369488375626058.json
  - 2_PWA_App版/.wrangler/tmp/pages-2uBUv8/functions-filepath-routing-config-0.11135523352439725.json
  - 2_PWA_App版/.wrangler/tmp/pages-2uBUv8/functionsRoutes-0.6381418117059428.mjs
  - 2_PWA_App版/.wrangler/tmp/pages-2uBUv8/functionsWorker-0.16342217756541644.js
  - 2_PWA_App版/.wrangler/tmp/pages-bdL8wo/_routes-0.11651751059675164.json
  - 2_PWA_App版/.wrangler/tmp/pages-bdL8wo/functions-filepath-routing-config-0.6340808475614842.json
  - 2_PWA_App版/.wrangler/tmp/pages-bdL8wo/functionsRoutes-0.435697652426302.mjs
  - 2_PWA_App版/.wrangler/tmp/pages-bdL8wo/functionsWorker-0.6732048250519167.js
  - 2_PWA_App版/public/icons/icon-192.png
  - 2_PWA_App版/public/icons/icon-512.png
  - 2_PWA_App版/public/index.html
  - HANDOVER.md
- **QC-系統客製化電子化工廠/**
  - .video_demo/QC_排程匯入示範_合成資料.xlsx
  - .video_demo/desktop-check-2.png
  - .video_demo/desktop-check.png
  - .video_demo/frames/01-initial.png
  - .video_demo/frames/02-schedule-imported.png
  - .video_demo/frames/03-schedule-selected.png
  - .video_demo/frames/04-sample-form-ready.png
  - .video_demo/frames/05-sample-pending.png
  - .video_demo/frames/06-pending-visible.png
  - .video_demo/frames/07-judge-preview.png
  - .video_demo/frames/08-completed-visible.png
  - .video_demo/index.html
- **三合一單網頁架機伺服器/**
  - static/index.html
- **三合一單自動產生器/**
  - last_generated_session.json
- **勝一三合一單網頁架機伺服器/**
  - static/index.html
- **教育訓練教材/**
  - .build/build_deck.mjs
  - .build/manual_render/page-1.png
  - .build/manual_render/page-2.png
  - .build/manual_render/page-3.png
  - .build/manual_render/page-4.png
  - .build/slide_render/slide-1.png
  - .build/slide_render/slide-2.png
  - .build/slide_render/slide-3.png
  - .build/slide_render/slide-4.png
  - .build/slide_render/slide-5.png
  - .build/slide_render/slide-6.png
  - .build/slide_render/slide-7.png
  - .build/slide_render/slide-8.png
  - .build_manual.py
  - .capture_qc_frames.py
  - .codex-finalizer/candidate-training-comparison.pptx.inspect.ndjson
  - .codex-finalizer/training-comparison.validation.json
  - .make_qc_demo.py
  - deliverables/AI教育訓練平台操作手冊.docx
  - deliverables/QC系統提案改善書.docx
  - deliverables/QC系統提案改善書_人工流程版.docx
- **本地三合一/**
  - 2_PWA_App版/index.html
  - 2_PWA_App版/manifest.json
  - 2_PWA_App版/run_server.py
  - 2_PWA_App版/sw.js
  - 2_PWA_App版/啟動PWA本機測試.bat
  - 3_Cloudflare_D1版/.wrangler/cache/pages.json
  - 3_Cloudflare_D1版/.wrangler/cache/wrangler-account.json
  - 3_Cloudflare_D1版/.wrangler/tmp/pages-2kB2EF/_routes-0.42288012011267906.json
  - 3_Cloudflare_D1版/.wrangler/tmp/pages-2kB2EF/functions-filepath-routing-config-0.2289856392969386.json
  - 3_Cloudflare_D1版/.wrangler/tmp/pages-2kB2EF/functionsRoutes-0.49189939126182214.mjs
  - 3_Cloudflare_D1版/.wrangler/tmp/pages-2kB2EF/functionsWorker-0.30288219963086094.js
  - 3_Cloudflare_D1版/.wrangler/tmp/pages-D9h6LY/_routes-0.40199050355478094.json
  - 3_Cloudflare_D1版/.wrangler/tmp/pages-D9h6LY/functions-filepath-routing-config-0.09817831580885605.json
  - 3_Cloudflare_D1版/.wrangler/tmp/pages-D9h6LY/functionsRoutes-0.4208542203847011.mjs
  - 3_Cloudflare_D1版/.wrangler/tmp/pages-D9h6LY/functionsWorker-0.26644077462404325.js
  - 3_Cloudflare_D1版/.wrangler/tmp/pages-kMOhxu/_routes-0.30122957041197473.json
  - 3_Cloudflare_D1版/.wrangler/tmp/pages-kMOhxu/functions-filepath-routing-config-0.8819689435238733.json
  - 3_Cloudflare_D1版/.wrangler/tmp/pages-kMOhxu/functionsRoutes-0.09722753810348062.mjs
  - 3_Cloudflare_D1版/.wrangler/tmp/pages-kMOhxu/functionsWorker-0.27590176441722736.js
  - 3_Cloudflare_D1版/functions/api/save.js
  - 3_Cloudflare_D1版/public/index.html
  - 3_Cloudflare_D1版/public/manifest.json
  - 3_Cloudflare_D1版/public/sw.js
  - 3_Cloudflare_D1版/schema.sql
  - 3_Cloudflare_D1版/setup_env.ps1
  - 3_Cloudflare_D1版/wrangler.toml
  - 3_Cloudflare_D1版/一鍵部署至Cloudflare.bat
  - generate_cf.py
  - generate_pwa.py
- **第一類_核心網頁與互動系統/**
  - 員工教育訓練測驗系統/sop_generator/SOP操作說明書.html
  - 員工教育訓練測驗系統/sop_generator/SOP操作說明書.md
  - 員工教育訓練測驗系統/sop_generator/SOP操作說明書.txt
  - 員工教育訓練測驗系統/sop_generator/index.html
