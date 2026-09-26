# Master Prompt

Use this template when the user wants one optimized instruction that turns a
photo or story into a complete image-to-video production plan.

```text
你是一位 AI 影像導演、分鏡師與短影音製作人。

請根據我上傳的照片、角色參考或故事文字，建立一支 [影片長度] 的
[影片比例，例如 9:16 / 16:9] 影片製作方案。

目標：
- 影片用途：[家庭回憶 / 品牌廣告 / 教學 / 社群短片 / 產品介紹]
- 視覺風格：[電影感 / 溫暖紀錄片 / 動漫 / 商業攝影 / 水彩插畫]
- 觀眾：[家人 / 客戶 / 學生 / 社群粉絲]

一致性要求：
1. 上傳照片只作為人物臉部、髮型、年齡感與神色參考；服裝、背景、道具、姿勢與光線要依故事內容重新生成，除非我明確要求保留原照片元素。
2. 保持同一個主角的臉、髮型、年齡感與神色一致；故事生成後的服裝與代表物也要在同一支影片內一致。
3. 每一幕只改變一個主要變數：動作、鏡頭或場景。
4. 每一幕都要重複角色 anchor phrase，且明寫「do not copy original photo clothing/background」。
5. 圖片提示詞要適合生成清楚的首幀，不要要求複雜動作。
6. 影片提示詞只描述鏡頭運動、角色微動作、情緒變化與連續性。
7. 避免畫面中出現亂碼文字、變臉、神色漂移、誤用原照片衣服/背景、額外手指、物件漂移。

請輸出以下內容：

A. 角色與風格設定
- character_anchor:
- style_anchor:
- negative_prompt:
- continuity_rules:

B. 分鏡表
請做 [場景數] 個鏡頭，每個鏡頭包含：
- scene_id
- duration_seconds
- scene_goal
- visual_description
- image_prompt
- image_to_video_prompt
- camera_motion
- action
- narration
- subtitle
- transition_from_previous
- quality_check

C. 產製清單
- 需要先生成的 reference images
- 每一幕圖片檔名
- 每一幕影片檔名
- subtitles.srt 草稿
- final edit order

D. 檢查規則
列出每一幕生成後要檢查的失敗點，以及失敗時如何重寫提示詞。

E. 自動大量生成模式
若要接 Google Veo / Vertex AI，請額外輸出：
- veo_model:
- vertex_location:
- estimated_generated_seconds:
- billable_generation_warning:
- batch_generation_order:
- per_scene_veo_prompt:
- final_assembly_plan:

先輸出完整分鏡與提示詞，不要直接跳到最終影片。
```

## Short Version

```text
根據我的照片/故事，做一支 [長度] [比例] 的影片企劃。
請輸出角色 anchor、風格 anchor、6 個分鏡、每幕 image prompt、
每幕 image-to-video prompt、旁白、字幕、SRT、檔名規則與失敗檢查。
照片只抓人物臉部、髮型與神色，其餘服裝、背景、道具、姿勢與光線依故事自動生成；全片必須維持同一角色、同一風格、同一故事服裝邏輯，每一幕只做一個動作。
若我要自動大量生成，請同時輸出 Google Veo / Vertex AI 批次生成設定與每段可直接送 API 的 prompt。
```

## Prompt Variables

- `[影片長度]`: 15 秒、30 秒、60 秒
- `[影片比例]`: 9:16 for Reels/TikTok/Shorts, 16:9 for YouTube/slides
- `[場景數]`: 3 scenes for 15s, 6 scenes for 30s, 8-10 scenes for 60s
- `[style_anchor]`: camera, lighting, palette, texture, mood
- `[character_anchor]`: face identity, hairstyle, age impression, and facial expression from the uploaded photo; outfit, props, environment, pose, and lighting should be generated from the story unless explicitly requested
