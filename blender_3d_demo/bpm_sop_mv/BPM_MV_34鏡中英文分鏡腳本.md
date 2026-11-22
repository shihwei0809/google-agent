# BPM 一般費用報銷單（私車公用）AI MV 級 34 鏡中英文分鏡腳本

> 借鏡 AI MV《已讀不懂》流水線：全片拆為 **34 個 2.5~5 秒微鏡頭**，景別快速交替（遠景/中景/特寫/POV/UI推近）。
> **單鏡替換成真 AI 影片方式**：用下方任一鏡的英文 Prompt 在 Google Flow / MiniMax H3 生成 3~5 秒影片後，存成 `mXX_flow.mp4` 放入 `bpm_sop_mv/flow_clips/`，再重跑 `python build_bpm_mv_video.py --only mXX` 即可秒換！

## 第一篇｜行前佐證三寶

### M01｜`000.0s - 003.6s` (3.6s)｜遠景・跟拍
- **中文旁白**：私車公用報銷，出差前先備齊三樣佐證。
- **畫面字幕**：私車公用報銷｜出發前先備齊 3 樣關鍵佐證
- **首幀素材**：`bpm_sop_mv/keyframes/m01_highway.png`
- **Google Flow / MiniMax 英文 Prompt**：
```text
Photorealistic commercial film, smooth low-angle tracking shot following a sleek metallic silver sedan cruising along a sunlit Taiwan multi-lane highway, green mountains in background, natural daylight, 35mm cinema lens, 4K, 3 seconds, steady fluid motion, no text.
```

### M02｜`003.6s - 007.0s` (3.5s)｜特寫・門架
- **中文旁白**：高速公路通行紀錄，決定你的過路費憑證。
- **畫面字幕**：高速公路 eTag 通行紀錄＝過路費報銷依據
- **首幀素材**：`bpm_sop_mv/keyframes/m01_highway.png`
- **Google Flow / MiniMax 英文 Prompt**：
```text
Dynamic low-angle upward tracking shot as a silver sedan passes underneath a modern steel overhead ETC electronic toll gantry on a sunny highway, subtle blue sensor glow, crisp asphalt motion blur, 35mm cinema lens, 4K, 3 seconds.
```

### M03｜`007.0s - 010.2s` (3.1s)｜中景・抵達
- **中文旁白**：第一，確認本人出差登記單已經核准。
- **畫面字幕**：佐證 1｜本人已核准之「出差登記單」
- **首幀素材**：`bpm_sop_mv/keyframes/m03_plant_gate.png`
- **Google Flow / MiniMax 英文 Prompt**：
```text
Photorealistic corporate film, smooth dolly-in as a silver executive sedan arrives at a modern chemical manufacturing plant entrance gate, glass guardhouse, red-and-white boom barrier arm rising smoothly in bright daylight, 4K, 3 seconds.
```

### M04｜`010.2s - 014.0s` (3.8s)｜UI聚焦・去回程
- **中文旁白**：第二，用 Google 地圖截下當次實際去回程路線。
- **畫面字幕**：佐證 2｜Google 地圖去／回程實際路線截圖（個資可遮蔽）
- **首幀素材**：實務 UI 截圖 (`['fig07_route_go.jpg', 'fig08_route_back.jpg']`)
- **Google Flow / MiniMax 英文 Prompt**：
```text
POV close-up inside a modern car interior, a hand holding a smartphone displaying a clean GPS navigation route map from start to destination, finger tapping to capture screenshot, warm natural window light, 4K, 3 seconds.
```

### M05｜`014.0s - 017.5s` (3.6s)｜UI特寫・里程
- **中文旁白**：跑幾公里就按個人實際里程與公司單價計算。
- **畫面字幕**：里程原則｜依個人實際公里數 × 公司核定單價計算
- **首幀素材**：實務 UI 截圖 (`fig07_route_go.jpg`)
- **Google Flow / MiniMax 英文 Prompt**：
```text
Macro close-up pushing smoothly toward a glowing smartphone map screen highlighting total driving distance kilometers on a route summary bar, crisp shallow depth of field, corporate explainer style, 4K, 3 seconds.
```

### M06｜`017.5s - 023.2s` (5.7s)｜UI特寫・專用章
- **中文旁白**：第三，下載含遠通專用章的 eTag 官方扣款明細，不能只截線上畫面。
- **畫面字幕**：佐證 3｜遠通官方 PDF 明細（須含「遠通電收電子憑證專用章」）
- **首幀素材**：實務 UI 截圖 (`fig06_etag_official_pdf.png`)
- **Google Flow / MiniMax 英文 Prompt**：
```text
Macro top-down camera push-in on an official printed highway electronic toll statement paper resting on a desk, focusing sharply on a crisp official circular stamp at the bottom corner, warm office daylight, 4K, 3 seconds.
```

## 第二篇｜進入系統選單號

### M07｜`023.2s - 026.6s` (3.4s)｜中景・工作站
- **中文旁白**：回到座位，打開電腦進入鼎新 BPM 系統。
- **畫面字幕**：PART 2｜回到座位開啟鼎新 BPM 系統
- **首幀素材**：`bpm_sop_mv/keyframes/m07_office_laptop.png`
- **Google Flow / MiniMax 英文 Prompt**：
```text
Medium cinematic shot in a sunlit modern Taiwan corporate office, a young office worker in smart casual attire sits smoothly at a walnut desk and opens a sleek silver laptop, natural window light, 35mm lens, 4K, 3 seconds.
```

### M08｜`026.6s - 030.2s` (3.6s)｜特寫・系統入口
- **中文旁白**：點擊左側選單的 EPM，開啟一般費用報銷單。
- **畫面字幕**：路徑｜鼎新 BPM ➔ EPM ➔ 一般費用報銷單
- **首幀素材**：`bpm_sop_mv/keyframes/m08_bpm_portal.png`
- **Google Flow / MiniMax 英文 Prompt**：
```text
Smooth slow dolly-in toward an ultrawide curved monitor on an executive desk, soft ambient blue office lighting, clean enterprise portal UI glowing softly as a cursor glides to click a blue menu card, 4K, 3 seconds.
```

### M09｜`030.2s - 034.3s` (4.1s)｜UI特寫・EPM
- **中文旁白**：進表單後先核對表頭的公司別、部門跟申請日期。
- **畫面字幕**：步驟 1｜確認表頭公司別、申請部門與日期無誤
- **首幀素材**：實務 UI 截圖 (`fig01_entry_epm.png`)
- **Google Flow / MiniMax 英文 Prompt**：
```text
Over-the-shoulder close-up of a crisp office monitor displaying a modern enterprise expense portal as a mouse cursor clicks the General Expense Claim button, soft depth of field, 4K, 3 seconds.
```

### M10｜`034.3s - 038.5s` (4.2s)｜UI特寫・查詢鈕
- **中文旁白**：接著在費用明細點選「出差登記單號」旁的查詢鈕。
- **畫面字幕**：步驟 2｜點擊「出差登記單號」旁放大鏡查詢鈕
- **首幀素材**：實務 UI 截圖 (`fig02_trip_selector.jpg`)
- **Google Flow / MiniMax 英文 Prompt**：
```text
Macro close-up of a hand moving an ergonomic mouse and clicking cleanly, monitor glow reflecting softly on the walnut desk surface, crisp 35mm commercial film, 4K, 3 seconds.
```

### M11｜`038.5s - 042.8s` (4.2s)｜UI特寫・清單勾選
- **中文旁白**：從清單選出你這趟實際出差的單號，千萬別選錯張。
- **畫面字幕**：步驟 3｜精準勾選「本人當次」出差單號（勿誤選他筆）
- **首幀素材**：實務 UI 截圖 (`fig02_trip_selector.jpg`)
- **Google Flow / MiniMax 英文 Prompt**：
```text
Close-up cinematic screen view as a clean translucent modal list appears and highlights a verified business trip row with a soft emerald checkmark glow, steady push-in, 4K, 3 seconds.
```

### M12｜`042.8s - 047.0s` (4.2s)｜UI特寫・憑證日期
- **中文旁白**：特別注意右上角的憑證日期，一定要改成實際出差日。
- **畫面字幕**：會計重點｜右上角「憑證日期」務必修改為實際出差日！
- **首幀素材**：實務 UI 截圖 (`fig03_a05_mileage.jpg`)
- **Google Flow / MiniMax 英文 Prompt**：
```text
Sharp macro focus rack on a sleek computer monitor corner showing a date picker field updating smoothly with a warm golden highlight ring, clean corporate aesthetic, 4K, 3 seconds.
```

## 第三篇｜雙軌分流登打

### M13｜`047.0s - 051.8s` (4.8s)｜3D全息・分流
- **中文旁白**：登打明細的核心鐵律，就是私車里程跟過路費「分開列示」。
- **畫面字幕**：PART 3 核心鐵律｜A05 私車里程 與 A07 eTag 絕不合併！
- **首幀素材**：`bpm_sop_mv/keyframes/m13_dual_track.png`
- **Google Flow / MiniMax 英文 Prompt**：
```text
High-end 3D corporate motion graphics in a sleek dark boardroom, slow smooth orbital camera around a holographic glass visualization splitting into a glowing cyan left track and an emerald green right track, Apple keynote style, 4K, 3 seconds.
```

### M14｜`051.8s - 056.0s` (4.1s)｜UI特寫・選A05
- **中文旁白**：第一筆費用類別選 A05 私車公用，稅別碼為免稅。
- **畫面字幕**：第一筆明細｜選取「A05 私車公用」（稅別碼：T05 免稅）
- **首幀素材**：實務 UI 截圖 (`fig03_a05_mileage.jpg`)
- **Google Flow / MiniMax 英文 Prompt**：
```text
Clean close-up on a dark-framed desktop monitor as a sleek dropdown menu opens and selects a blue highlighted category option smoothly, modern office lighting, 4K, 3 seconds.
```

### M15｜`056.0s - 059.1s` (3.1s)｜特寫・敲鍵盤
- **中文旁白**：輸入你依實際公里數算出的報銷金額。
- **畫面字幕**：金額登打｜輸入依個人實際里程算出的報銷金額
- **首幀素材**：`bpm_sop_mv/keyframes/m15_keyboard_typing.png`
- **Google Flow / MiniMax 英文 Prompt**：
```text
Dramatic macro close-up of fingers typing briskly on the numeric keypad of a sleek modern office keyboard, warm desk lamp glow, blurred monitor light in background, shallow depth of field, 35mm lens, 4K, 3 seconds.
```

### M16｜`059.1s - 063.1s` (4.0s)｜UI特寫・車號備註
- **中文旁白**：右下角費用說明，務必填上你實際駕駛的車牌號碼。
- **畫面字幕**：必填欄位｜費用說明欄務必備註「實際車牌號碼」
- **首幀素材**：實務 UI 截圖 (`fig03_a05_mileage.jpg`)
- **Google Flow / MiniMax 英文 Prompt**：
```text
Close-up tracking pan across a clean digital form notes field as crisp characters appear swiftly, soft amber highlight glow along the border, 4K, 3 seconds.
```

### M17｜`063.1s - 067.0s` (3.9s)｜UI特寫・新增列
- **中文旁白**：A05 存好後，另外新增第二筆明細報過路費。
- **畫面字幕**：新增第二筆｜A05 確認入列後，再新增獨立一筆過路費
- **首幀素材**：實務 UI 截圖 (`fig04_a05_list_check.jpg`)
- **Google Flow / MiniMax 英文 Prompt**：
```text
Clean macro UI shot of a bright blue plus button being clicked on a crisp enterprise web table, triggering a smooth new row expansion animation, 4K, 3 seconds.
```

### M18｜`067.0s - 070.1s` (3.1s)｜UI特寫・選A07
- **中文旁白**：第二筆類別選 A07 高速公路通行費。
- **畫面字幕**：第二筆明細｜選取「A07 高速公路通行費 (eTag)」
- **首幀素材**：實務 UI 截圖 (`fig05_a07_etag.jpg`)
- **Google Flow / MiniMax 英文 Prompt**：
```text
Smooth macro zoom onto a sleek emerald green tag badge pulsing gently on a clean corporate dashboard screen, crisp 4K lighting, 3 seconds.
```

### M19｜`070.1s - 074.6s` (4.5s)｜UI特寫・實扣金額
- **中文旁白**：照遠通官方明細的實際扣款金額填報，絕不跟里程混算。
- **畫面字幕**：分列鐵律｜依遠通官方 PDF 實扣金額獨立填報
- **首幀素材**：實務 UI 截圖 (`fig05_a07_etag.jpg`)
- **Google Flow / MiniMax 英文 Prompt**：
```text
Close-up of two neatly separated glowing glass cards floating side by side in a dark studio, cyan on left and emerald on right, gently pulsing to emphasize separation, 4K, 3 seconds.
```

## 第四篇｜高鐵與停車費

### M20｜`074.6s - 078.0s` (3.4s)｜中景・高鐵進站
- **中文旁白**：如果出差改搭高鐵，費用類別請選 A01。
- **畫面字幕**：PART 4 其他交通｜搭高鐵選「A01 高鐵車資」
- **首幀素材**：`bpm_sop_mv/keyframes/m20_hsr_train.png`
- **Google Flow / MiniMax 英文 Prompt**：
```text
Photorealistic commercial shot, warm morning sunlight streaming through a modern glass-canopy high-speed rail platform as a sleek white-and-orange bullet train glides smoothly into the station, horizontal tracking pan, 35mm lens, 4K, 3 seconds.
```

### M21｜`078.0s - 083.0s` (5.1s)｜UI特寫・13碼票號
- **中文旁白**：高鐵發票號碼填票面 13 碼票號，稅別 T02 登打含稅總額。
- **畫面字幕**：高鐵重點｜發票號碼填「13 碼票號」｜T02 填含稅總金額
- **首幀素材**：實務 UI 截圖 (`fig10_a01_hsr.png`)
- **Google Flow / MiniMax 英文 Prompt**：
```text
Macro close-up of a crisp high-speed rail ticket held in hand under bright daylight, shallow depth of field focusing sharply on the printed ticket number strip, 4K, 3 seconds.
```

### M22｜`083.0s - 086.5s` (3.5s)｜中景・停車場
- **中文旁白**：若有產生額外停車費，則選 A06 停車費。
- **畫面字幕**：停車費用｜類別選「A06 停車費」
- **首幀素材**：`bpm_sop_mv/keyframes/m22_parking.png`
- **Google Flow / MiniMax 英文 Prompt**：
```text
Photorealistic commercial shot of a modern underground smart parking exit lane with linear LED ceiling lights, a sleek automated payment kiosk glowing green as a receipt slides out and the LED barrier arm rises smoothly, 4K, 3 seconds.
```

### M23｜`086.5s - 091.7s` (5.2s)｜UI特寫・未稅含稅
- **中文旁白**：有發票時看清稅別：T01 填未稅金額，T02 填含稅總額。
- **畫面字幕**：稅別鐵律｜T01（外加5%）填未稅額 ｜ T02（內含5%）填含稅總額
- **首幀素材**：實務 UI 截圖 (`fig11_a06_parking.png`)
- **Google Flow / MiniMax 英文 Prompt**：
```text
Macro shot of a printed official receipt paper on an executive desk, a metallic pen pointing gently at the subtotal and tax lines, crisp warm lighting, 4K, 3 seconds.
```

### M24｜`091.7s - 095.7s` (4.1s)｜UI特寫・實報實銷
- **中文旁白**：畫面數字只是範例，一律依手中實際票據金額登打。
- **畫面字幕**：實報實銷｜畫面皆為範例，請依手中實際發票與里程登打
- **首幀素材**：實務 UI 截圖 (`fig09_multi_list.jpg`)
- **Google Flow / MiniMax 英文 Prompt**：
```text
Slow smooth pull-back over a neat corporate desk showing multiple neatly aligned travel receipts and a tablet calculator displaying verified totals, clean office daylight, 4K, 3 seconds.
```

## 第五篇｜防呆檢查送簽

### M25｜`095.7s - 099.3s` (3.5s)｜3D特寫・保險庫
- **中文旁白**：所有明細加總，務必等於表頭報銷總金額。
- **畫面字幕**：PART 5 防呆 1｜確認「明細合計 ＝ 表頭總金額」完全一致
- **首幀素材**：`bpm_sop_mv/keyframes/m25_vault_dashboard.png`
- **Google Flow / MiniMax 英文 Prompt**：
```text
High-end 3D corporate CGI close-up of glowing document cards gliding smoothly into a brushed-steel digital vault with a soft blue confirmation light pulse, dark glass boardroom table, 4K, 3 seconds.
```

### M26｜`099.3s - 104.0s` (4.7s)｜UI特寫・總額檢核
- **中文旁白**：接著把出差單、路線截圖、eTag 與發票全部上傳附件。
- **畫面字幕**：防呆 2｜完整上傳出差單、去回程路線圖、eTag PDF 與發票
- **首幀素材**：實務 UI 截圖 (`fig09_multi_list.jpg`)
- **Google Flow / MiniMax 英文 Prompt**：
```text
Close-up of a computer screen as three clean PDF and image icons drag and drop smoothly into a glowing digital upload dropzone, progress bars hitting 100 percent green, 4K, 3 seconds.
```

### M27｜`104.0s - 108.4s` (4.5s)｜UI特寫・開檔檢查
- **中文旁白**：上傳後記得親自點開檢查，確認每份附件都清晰可讀。
- **畫面字幕**：防呆 3｜上傳後務必「點開預覽」確認無破圖、印章清晰
- **首幀素材**：實務 UI 截圖 (`fig06_etag_official_pdf.png`)
- **Google Flow / MiniMax 英文 Prompt**：
```text
Over-the-shoulder close-up of an office worker reviewing a crisp PDF document preview on a bright monitor, nodding subtly in confirmation, soft natural daylight, 4K, 3 seconds.
```

### M28｜`108.4s - 112.7s` (4.2s)｜3D特寫・先儲存
- **中文旁白**：送簽前，先按一次「儲存」，確認沒有紅字提醒。
- **畫面字幕**：防呆 4｜送出前「先按儲存」，確認無任何紅字欄位漏填
- **首幀素材**：`bpm_sop_mv/keyframes/m25_vault_dashboard.png`
- **Google Flow / MiniMax 英文 Prompt**：
```text
Macro 3D CGI shot of a sleek metallic blue Save Draft pill badge illuminating brightly with a gentle specular light sweep over a glass table, shallow depth of field, 4K, 3 seconds.
```

### M29｜`112.7s - 116.5s` (3.9s)｜3D特寫・按送出
- **中文旁白**：確認無誤後，再正式按下「送出」發起簽核。
- **畫面字幕**：步驟 5｜無錯誤提示後，正式按下「送出」發起線上簽核
- **首幀素材**：`bpm_sop_mv/keyframes/m25_vault_dashboard.png`
- **Google Flow / MiniMax 英文 Prompt**：
```text
Macro 3D CGI shot of an emerald green Submit pill badge lighting up sequentially next to a blue Save badge, emitting a crisp clean light ripple, 4K, 3 seconds.
```

### M30｜`116.5s - 120.2s` (3.7s)｜特寫・取得單號
- **中文旁白**：並到待辦區確認已成功產生正式 BPM 單號。
- **畫面字幕**：步驟 6｜至待辦區確認已產生正式 BPM 單號才算送出成功
- **首幀素材**：`bpm_sop_mv/keyframes/m30_desk_approved.png`
- **Google Flow / MiniMax 英文 Prompt**：
```text
Close-up of a sleek modern smartphone resting on a sunlit walnut office desk, screen illuminating with a crisp green checkmark Approved notification glow, warm morning light, 4K, 3 seconds.
```

## 第六篇｜實體正本交件

### M31｜`120.2s - 124.9s` (4.7s)｜中景・列印正本
- **中文旁白**：線上送完還沒結束！請把報銷申請單列印出來。
- **畫面字幕**：PART 6 實體交件｜線上送出後，請列印 BPM 報銷申請單正本
- **首幀素材**：`bpm_sop_mv/keyframes/m31_laser_printer.png`
- **Google Flow / MiniMax 英文 Prompt**：
```text
Medium close-up of a sleek modern corporate multifunction laser printer smoothly printing and sliding a crisp white expense report sheet into the output tray, bright clean office lighting, 35mm lens, 4K, 3 seconds.
```

### M32｜`124.9s - 129.6s` (4.8s)｜特寫・裝訂發票
- **中文旁白**：連同實體發票、收據正本、路線圖與 eTag 明細整齊裝訂。
- **畫面字幕**：裝訂正本｜報銷單 ＋ 發票／收據正本 ＋ 路線截圖 ＋ eTag 蓋章明細
- **首幀素材**：`bpm_sop_mv/keyframes/m32_stapler_receipts.png`
- **Google Flow / MiniMax 英文 Prompt**：
```text
Macro top-angle close-up on a warm walnut desk, hands pressing a sleek metallic stapler neatly onto a white corporate expense form aligned with official paper receipts bearing red circular stamps, crisp daylight, 4K, 3 seconds.
```

### M33｜`129.6s - 133.7s` (4.1s)｜中景・人事核對
- **中文旁白**：先親手交給人事單位核對正本與線上內容完全無誤。
- **畫面字幕**：交件順序 1｜申請人先交由「人事單位」核對正本無誤
- **首幀素材**：`bpm_sop_mv/keyframes/m33_hr_handover.png`
- **Google Flow / MiniMax 英文 Prompt**：
```text
Medium cinematic shot in a bright glass-walled corporate office, a Taiwanese employee politely hands a neat stack of stapled expense papers across a desk to a smiling HR specialist who raises a red verification stamp, natural sunlight, 4K, 3 seconds.
```

### M34｜`133.7s - 138.2s` (4.5s)｜全景・會計入帳
- **中文旁白**：最後由人事轉交會計審核入帳，零退件順利完成報銷！
- **畫面字幕**：交件順序 2｜人事轉交「會計審核入帳」➔ 零退件順利完成！
- **首幀素材**：`bpm_sop_mv/keyframes/m34_three_stage.png`
- **Google Flow / MiniMax 英文 Prompt**：
```text
Wide cinematic pull-back inside a sunlit modern glass corporate office showcasing three luminous frosted-glass workflow pillars lighting up in sequence connected by a flowing golden-blue light beam, warm professional film look, 4K, 4 seconds.
```
