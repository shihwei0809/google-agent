# BPM 一般費用報銷單（私車公用）Google Flow 中英文分鏡腳本

> **Google Flow (Veo) 實測高成功率心法：**
> 1. **英文 Prompt 為主**：Flow 對英文運鏡動詞（`smooth tracking shot`、`dolly in`、`barrier arm rises`）理解最精準。
> 2. **避免讓 AI 在影片裡生中文字**：畫面中文字留給後製字幕，Prompt 專注在**物理動態、運鏡、光影**，畫面才不會糊或出現亂碼。
> 3. **建議模式**：`Frames to Video`（首尾幀）或 `Image to Video`（單張首幀 + 英文動態 Prompt），**單張首幀通常比硬塞兩張反差太大的首尾幀更自然、不變形**。

---

## 鏡次 C01｜行前準備：國道 eTag 出差 ➔ 抵達廠區
* **配音時長**：約 18.8 秒（Flow 建議產出 8~10 秒循環/慢動作）
* **搭配首尾幀**：
  * 首幀：`bpm_sop_plan_c/flow_frames/bpm_c01_first.png`
  * 尾幀：`bpm_sop_plan_c/flow_frames/bpm_c01_last.png`
* **中文畫面說明**：
  * 晴朗白天，一台銀色商務房車平穩行駛於台灣多線道高速公路，攝影機低角度平穩跟拍，車輛順暢穿過上方銀色鋼構 eTag 電子收費門架，遠方為翠綠山巒；鏡頭順暢推近轉場至車輛抵達現代化工廠大門警衛室，道閘緩緩升起。
* **Google Flow 英文 Prompt（直接複製）**：
```text
Photorealistic commercial film, smooth low-angle tracking shot following a sleek metallic silver sedan cruising steadily along a sunlit multi-lane Taiwan highway. The car glides cleanly underneath an overhead steel ETC electronic toll gantry with subtle blue indicator lights. Lush green mountains and clear blue sky in the background, crisp asphalt motion blur, natural daylight, 35mm cinema lens, steady fluid camera movement, ultra-sharp 4K, no text overlays, no distortion.
```
* **（若要用首尾幀轉場至廠區大門，改用這版）**：
```text
Photorealistic corporate commercial, smooth continuous camera transition. Starting with a silver executive sedan driving smoothly underneath a highway steel electronic toll gantry in bright daylight, seamlessly gliding forward as the scene transitions to the silver sedan pulling up smoothly to a modern industrial plant entrance gate with a glass guardhouse and a rising boom barrier arm. Natural sunlight, crisp 4K architectural detail, steady gimbal movement, no text distortion.
```
* **中文旁白**：
  > 歡迎收看 BPM 私車公用報銷快速導覽！開車出差報帳前，先備好三樣資料：第一是本人核准的出差登記單，第二是用 Google 地圖截下當次實際去回程路線圖，看實際跑了多少公里就依實際里程計算，第三則是遠通 eTag 實際扣款明細。

---

## 鏡次 C02｜系統入口：進入 EPM 一般費用報銷單並選取出差單
* **配音時長**：約 19.6 秒
* **搭配首幀**：`bpm_sop_plan_c/flow_frames/bpm_c02_first.png`
* **中文畫面說明**：
  * 質感現代辦公桌前，攝影機緩緩向曲面寬螢幕推進（Slow Dolly-In），螢幕上企業報銷系統介面微微發光，滑鼠游標平滑移動並點擊選取出差紀錄卡片，柔和藍色環境光流動，呈現專業數位系統操作氛圍。
* **Google Flow 英文 Prompt（直接複製）**：
```text
Photorealistic corporate tech commercial, slow smooth dolly-in camera shot toward a sleek ultrawide curved monitor on a dark walnut executive desk in a modern dimly lit office. Soft ambient blue desk lighting illuminates the workspace. On the glowing monitor screen, a clean enterprise web dashboard interface subtly animates as a sleek cursor glides smoothly and clicks a highlighted card, triggering a gentle cyan confirmation glow. Shallow depth of field, crisp reflections, 35mm lens, steady cinematic motion, 4K, no garbled text.
```
* **中文旁白**：
  > 接著進到鼎新 BPM，點開 EPM 裡面的「一般費用報銷單」，確認表頭的公司別、部門跟日期。然後到費用明細點選「出差登記單號」旁邊的查詢鈕，從清單裡選出你這趟實際出差的單號，讓系統自動帶入日期、地點跟出差事由，千萬別選錯張喔！

---

## 鏡次 C03｜雙軌分流：私車里程 (A05) 與 eTag 通行費 (A07) 分開列示
* **配音時長**：約 20.4 秒
* **搭配首幀**：`bpm_sop_plan_c/flow_frames/bpm_c03_first.png`
* **中文畫面說明**：
  * 現代深色商務會議室內，桌上浮現極簡 3D 玻璃光流視覺化：中央一道亮光節點流暢地分岔為左右兩條平行發光軌道——左側青藍色光軌代表私車里程，右側翡翠綠色光軌代表高速公路 eTag 通行費，兩塊毛玻璃立體卡片平穩懸浮並微幅漂浮，攝影機緩慢環繞運鏡。
* **Google Flow 英文 Prompt（直接複製）**：
```text
High-end 3D corporate motion graphics film in a sleek dark modern boardroom. Slow smooth orbital camera movement around a clean holographic glass visualization floating above a conference table. A central stream of soft white light smoothly splits into two distinct parallel luminous tracks: a glowing cyan glass pathway on the left with a minimalist 3D car silhouette, and a glowing emerald green glass pathway on the right with a minimalist toll gantry arch. Soft volumetric studio lighting, frosted glass reflections, ultra-clean Apple keynote aesthetic, smooth fluid motion, 4K, no messy text.
```
* **中文旁白**：
  > 填費用明細時，最重要的原則就是「分開列示」！私車公用里程費選 A05，依你自己實際跑的公里數與公司核定單價計算登打，並備註實際車牌號碼；而高速公路的 eTag 通行費一定要另外新增一筆 A07，照遠通實際扣款金額填報，絕不能跟里程費混在一起。

---

## 鏡次 C04｜非私車情境：高鐵 (A01) 與停車費 (A06)
* **配音時長**：約 16.8 秒
* **搭配首尾幀**：
  * 首幀：`bpm_sop_plan_c/flow_frames/bpm_c04_first.png`
  * 尾幀：`bpm_sop_plan_c/flow_frames/bpm_c04_last.png`
* **中文畫面說明**：
  * 晨光灑落的現代玻璃帷幕高鐵站月台，橘白塗裝流線型高鐵列車平穩滑行進站停靠；接著順暢轉場至明亮的地下智慧停車場出口，車側自動繳費機螢幕亮起綠色確認燈號並吐出紙本發票，前方 LED 道閘桿平穩升起。
* **Google Flow 英文 Prompt（直接複製｜單純高鐵段）**：
```text
Photorealistic commercial cinema shot, warm morning sunlight streaming through a modern glass-canopy high-speed rail station platform. A sleek streamlined white-and-orange bullet train glides smoothly along the tracks and decelerates gently beside the platform. Subtle dust motes in sunbeams, clean architectural reflections on polished stone floor, smooth horizontal tracking pan, 35mm cinema lens, crisp 4K, realistic motion, no artifacts.
```
* **（首尾幀轉場：高鐵 ➔ 停車場道閘升起）**：
```text
Photorealistic commercial video with a seamless cinematic transition. Starting at a sunlit modern glass high-speed rail platform as a sleek white-and-orange bullet train glides in smoothly, the camera sweeps forward and transitions cleanly into a modern underground smart parking garage exit lane with linear LED ceiling lights. A sleek brushed-aluminum payment kiosk glows green as a paper receipt slides out, and the illuminated green LED boom barrier gate rises smoothly open. Crisp 4K, steady gimbal movement, realistic lighting.
```
* **中文旁白**：
  > 如果你這趟出差改搭高鐵，或是有產生額外的停車費，記得要選 A01 高鐵或 A06 停車費。而且畫面上的數字都只是範例，報銷時請一律依照手中車票、電子發票或停車收據上的實際金額與發票號碼來登打喔！

---

## 鏡次 C05｜總額對齊、附件上傳與「先儲存再送出」
* **配音時長**：約 19.0 秒
* **搭配首幀**：`bpm_sop_plan_c/flow_frames/bpm_c05_first.png`
* **中文畫面說明**：
  * 現代玻璃會議桌上方的 3D 商務儀表板視覺：左側幾張發光半透明單據與地圖卡片整齊飛入並收納進金屬質感數位保險箱中；右側三個立體金屬質感圓角膠囊徽章（藍 ➔ 綠 ➔ 金）依序由左至右點亮並散發柔和光暈，象徵儲存、送出、核准完成。
* **Google Flow 英文 Prompt（直接複製）**：
```text
High-end 3D corporate explainer animation, slow smooth push-in shot over a sleek glass boardroom table. On the left, translucent glowing document cards glide neatly and stack smoothly into a brushed-steel digital vault with a soft blue light pulse. On the right, three sleek metallic 3D pill badges illuminate sequentially from left to right in blue, emerald green, and warm gold with gentle specular highlights. Clean studio lighting, shallow depth of field, refined corporate tech aesthetic, fluid motion, 4K, no garbled text.
```
* **中文旁白**：
  > 全部實際費用都新增完畢後，請先檢查所有明細加總是否等於表頭報銷總金額，再把出差單、路線截圖、eTag 與發票附件全部上傳，確認點得開。送簽前先按一次「儲存」確認沒有紅字提醒，再正式按下「送出」並留存 BPM 單號！

---

## 鏡次 C06｜正本繳交：申請人 ➔ 人事核對 ➔ 會計審核
* **配音時長**：約 17.5 秒
* **搭配首尾幀**：
  * 首幀：`bpm_sop_plan_c/flow_frames/bpm_c06_first.png`
  * 尾幀：`bpm_sop_plan_c/flow_frames/bpm_c06_last.png`
* **中文畫面說明**：
  * 柔和自然光灑落的胡桃木辦公桌上，商務人士的手將整齊裝訂好的報銷申請單與蓋有紅色印章的實體發票平穩歸位，一旁手機亮起綠色核准勾勾；鏡頭平滑拉遠並轉場至明亮現代玻璃辦公室，三座發光毛玻璃里程碑立柱由光束依序串聯點亮（申請人 ➔ 人事核對 ➔ 會計入帳）。
* **Google Flow 英文 Prompt（直接複製）**：
```text
Photorealistic corporate commercial film, warm natural morning sunlight across an executive walnut office desk. A smooth close-up overhead-angle pan shows neatly organized white printed expense claim forms and official paper receipts with crisp red verification stamps lying beside a modern smartphone displaying a glowing green checkmark. The camera glides smoothly upward and transitions into a bright sunlit modern glass corporate office where three frosted-glass 3D workflow pillars light up in sequence connected by a flowing golden-blue light beam. Warm professional lighting, 35mm lens, crisp 4K, steady fluid motion.
```
* **中文旁白**：
  > 最後提醒，線上送簽完成不代表結束喔！請把申請單印出來，連同實際發生的發票、收據正本、路線截圖與計算資料一起交給人事單位核對；等人事確認正本與線上內容無誤後，才會正式轉交給會計審核與撥款。

---

## 實測完替換影片的方式（超簡單）
你在 Google Flow 生出滿意的 `.mp4` 後，直接照對應檔名丟進：
`C:\GOOGLE ANGET\blender_3d_demo\bpm_sop_plan_c\flow_clips\`
- `c01_flow.mp4`
- `c02_flow.mp4`
- `c03_flow.mp4`
- `c04_flow.mp4`
- `c05_flow.mp4`
- `c06_flow.mp4`

放好後只要執行 `python build_bpm_plan_c_video.py`，就會自動套上台灣旁白與 1080p 字幕合出最終總片。
