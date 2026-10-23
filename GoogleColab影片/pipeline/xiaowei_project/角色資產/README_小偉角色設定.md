# 角色資產設定檔：小偉 (Xiaowei) — 43 歲台灣男性（寫實風格）

> **核心防走鐘規則**：
> 1. 「小偉_正式版」與「小偉_休閒版」共用**完全一模一樣的臉部與髮型英文鎖定詞 (Core Face & Hair Anchor)**，僅更換下半段的服裝描述，確保不管換穿西裝或休閒服，生出來的都是同一張臉、同一副眼鏡。
> 2. 每次生分鏡首幀時，**直接整段複製下方的「完整鎖定外觀提示詞」**，切勿臨時自己重寫外觀描述。

---

## 一、核心臉部與髮型鎖定詞（兩套服裝絕對共用，一字不改）

```text
43-year-old Taiwanese East Asian man, mature composed oval face with clean jawline, neat clean side-parted short black hair with a natural subtle sheen, wearing sleek dark titanium-framed rectangular eyeglasses, warm and steady eyes
```

---

## 二、兩套造型的「完整鎖定外觀提示詞 (Locked Appearance Prompts)」

### 👔 造型 A：`小偉_正式版`（商務／簡報／專業教學場景）
- **對應資料夾**：`角色資產/小偉_正式版/`
- **本地單張定妝照路徑**：`chars/xiaowei_formal.png`
- **完整鎖定外觀提示詞（生首幀時直接複製）**：
```text
43-year-old Taiwanese East Asian man, mature composed oval face with clean jawline, neat clean side-parted short black hair with a natural subtle sheen, wearing sleek dark titanium-framed rectangular eyeglasses, wearing a tailored charcoal navy business suit jacket over a crisp white button-down dress shirt (no tie, top button neatly fastened), dark tailored trousers, black leather dress shoes
```

### 👕 造型 B：`小偉_休閒版`（日常／工作坊／輕鬆分享場景）
- **對應資料夾**：`角色資產/小偉_休閒版/`
- **本地單張定妝照路徑**：`chars/xiaowei_casual.png`
- **完整鎖定外觀提示詞（生首幀時直接複製）**：
```text
43-year-old Taiwanese East Asian man, mature composed oval face with clean jawline, neat clean side-parted short black hair with a natural subtle sheen, wearing sleek dark titanium-framed rectangular eyeglasses, wearing a smart-casual olive-grey lightweight bomber jacket over a clean fitted plain white crew-neck t-shirt, dark navy chinos, clean minimalist white-sole leather sneakers
```

---

## 三、【做法 1】給雲端生圖（ChatGPT / Gemini / OpenAI Image 2.5）生「角色三表」的複製即用提示詞

如果你要用 GPT-4o / Gemini / Image 2.5 先把「小偉」的完整三表（`01_定妝照.png`、`02_轉面圖.png`、`03_表情表.png`）生出來存進資料夾，直接複製以下提示詞：

### 1. 生成【小偉_正式版】三表

#### 📌 `角色資產/小偉_正式版/01_定妝照.png`（全身正面 + 正面近照 + 3/4 側臉近照）
```text
Character reference sheet divided into 3 vertical panels side-by-side on a plain neutral grey studio background (#BFBFBF), photorealistic DSLR photography, 85mm lens, soft studio lighting, exact same person across all 3 panels:
- Left panel: full-body frontal standing pose, hands relaxed naturally at sides, showing complete suit, trousers, and shoes.
- Middle panel: close-up frontal chest-up portrait facing camera directly, calm confident slight smile.
- Right panel: close-up 3/4 side profile portrait looking slightly right.
Character description: 43-year-old Taiwanese East Asian man, mature composed oval face with clean jawline, neat clean side-parted short black hair with a natural subtle sheen, wearing sleek dark titanium-framed rectangular eyeglasses, wearing a tailored charcoal navy business suit jacket over a crisp white button-down dress shirt (no tie), dark tailored trousers, black leather dress shoes. No text, no watermarks.
```

#### 📌 `角色資產/小偉_正式版/02_轉面圖.png`（正面／左側／背面／3/4 全身）
```text
Character turnaround sheet with 4 full-body standing views side-by-side on a plain neutral grey studio background (#BFBFBF): (1) front view, (2) left side profile view, (3) back view, (4) 3/4 view. Photorealistic photography, exact same person and outfit across all 4 views: 43-year-old Taiwanese East Asian man, mature composed oval face with clean jawline, neat clean side-parted short black hair, wearing sleek dark titanium-framed rectangular eyeglasses, wearing a tailored charcoal navy business suit jacket over a crisp white button-down dress shirt (no tie), dark tailored trousers, black leather dress shoes.
```

#### 📌 `角色資產/小偉_正式版/03_表情表.png`（6 格表情特寫）
```text
2x3 grid of 6 close-up chest-up headshot expressions of the exact same man on a plain neutral grey studio background (#BFBFBF), photorealistic photography:
(1) Top-left: calm warm professional smile
(2) Top-middle: serious focused explaining expression
(3) Top-right: helpless wry smile / sigh ("here we go again")
(4) Bottom-left: surprised raised eyebrows
(5) Bottom-middle: deep in thought, nodding slightly
(6) Bottom-right: hearty cheerful laugh
Character description: 43-year-old Taiwanese East Asian man, mature composed oval face with clean jawline, neat clean side-parted short black hair, wearing sleek dark titanium-framed rectangular eyeglasses, wearing a tailored charcoal navy business suit jacket over a crisp white button-down dress shirt.
```

---

### 2. 生成【小偉_休閒版】三表
> 💡 **技巧**：在 ChatGPT / Gemini / Image 2.5 先生成上面的「正式版 `01_定妝照.png`」後，**把那張圖上傳作為參考圖 (Reference Image)**，再貼上下方提示詞，就能 100% 鎖住同一張臉只換成休閒服！

#### 📌 `角色資產/小偉_休閒版/01_定妝照.png`（全身正面 + 正面近照 + 3/4 側臉近照）
```text
Keep the exact same person's face, facial structure, neat side-parted short black hair, and sleek dark titanium-framed rectangular eyeglasses from the reference image.
Generate a 3-panel vertical character reference sheet on a plain neutral grey studio background (#BFBFBF), photorealistic DSLR photography:
- Left panel: full-body frontal standing pose.
- Middle panel: close-up frontal chest-up portrait facing camera directly, relaxed warm smile.
- Right panel: close-up 3/4 side profile portrait.
New Casual Outfit: wearing a smart-casual olive-grey lightweight bomber jacket over a clean fitted plain white crew-neck t-shirt, dark navy chinos, clean minimalist white-sole leather sneakers.
```

#### 📌 `角色資產/小偉_休閒版/02_轉面圖.png`（正面／左側／背面／3/4 全身）
```text
Keep the exact same person's face, neat side-parted short black hair, and sleek dark titanium-framed rectangular eyeglasses from the reference image.
Character turnaround sheet with 4 full-body standing views side-by-side on a plain neutral grey studio background (#BFBFBF): (1) front view, (2) left side profile view, (3) back view, (4) 3/4 view. Photorealistic photography, wearing a smart-casual olive-grey lightweight bomber jacket over a clean fitted plain white crew-neck t-shirt, dark navy chinos, clean minimalist white-sole leather sneakers.
```

---

## 四、【做法 2】用本專案 `local/gen_image.py` (Qwen-Image) 生「單張定妝照」指令

> ⚠️ 提醒：本地 Qwen-Image-Edit 生首幀時**只能餵「單張一人半身照（1024×1024）」**，不可餵三格合成圖。

1. **先用 `Qwen-Image` 抽出「小偉_正式版」單張正面半身定妝照**：
```powershell
python local/gen_image.py `
  --model qwen `
  --prompt "Studio portrait on a plain neutral grey background, waist-up frontal view, facing camera directly, calm composed expression, 43-year-old Taiwanese East Asian man, mature composed oval face with clean jawline, neat clean side-parted short black hair with a natural subtle sheen, wearing sleek dark titanium-framed rectangular eyeglasses, wearing a tailored charcoal navy business suit jacket over a crisp white button-down dress shirt, no tie, soft even studio lighting, sharp focus, photorealistic DSLR photography, single person only" `
  --width 1024 --height 1024 `
  --seed 4301 `
  --output pipeline/xiaowei_project/chars/xiaowei_formal.png
```

2. **再用 `Qwen-Image-Edit` 以「正式版定妝照」為參考圖，原臉換裝生出「小偉_休閒版」定妝照（確保兩張臉 100% 同一個人）**：
```powershell
python local/gen_image.py `
  --model qwen-edit `
  --ref pipeline/xiaowei_project/chars/xiaowei_formal.png `
  --prompt "Keep the exact same man's face, facial features, neat side-parted short black hair, and dark titanium-framed rectangular eyeglasses from <image1>. Studio portrait on a plain neutral grey background, waist-up frontal view, facing camera directly, change his outfit to a smart-casual olive-grey lightweight bomber jacket over a clean fitted plain white crew-neck t-shirt, soft even studio lighting, photorealistic photography, single person only" `
  --width 1024 --height 1024 `
  --seed 4302 `
  --output pipeline/xiaowei_project/chars/xiaowei_casual.png
```

---

## 五、小偉的「沉穩男聲」參考音 (`voices/ref_xiaowei.wav`)

- **聲音定位**：43 歲台灣成熟男性，中低音域（Baritone）、語氣沉穩內斂、咬字清晰自然、不浮誇、像資深顧問或可靠主管娓娓道來的台灣國語。
- **Breeze TTS 2 聲音設計詞 (`voice_design`)**：
  `A 43-year-old Taiwanese man with a calm, steady, warm low-baritone voice, natural Taiwanese Mandarin accent, composed and trustworthy tone, speaking at a measured and clear pace.`
- **範例台詞 (`voice_sample`)**：
  `大家好，我是小偉。很多事情不用急著一次做完，先把核心流程理清楚，後面就會順很多。`
- **一鍵生成參考音指令**：
```powershell
python local/breeze_batch.py --manifest pipeline/xiaowei_project/film.json --mode design-refs
```
