---
name: image-story-video
description: Create a reusable image-to-video production workflow from user photos, a short story, personal memory, brand idea, or script. Use when the user wants one master prompt or automation plan that turns uploaded photos or text into consistent character images, image-to-video prompts, storyboard tables, narration, subtitles, production folders, Google Veo/Vertex AI batch video generation, downloaded clips, and a final assembled video.
---

# Image Story Video

Use this skill when the user wants to turn a personal photo, character reference,
short story, product idea, or small script into a repeatable image-to-video
workflow.

The skill does not pretend that a single text prompt can upload files, generate
images, generate clips, and edit video by itself. Instead, produce one master
instruction plus structured artifacts that can drive the available tools:

1. analyze input photos/story, using photos only for face identity and expression unless the user explicitly asks otherwise
2. define a stable character/style anchor
3. write a storyboard
4. write image prompts
5. write image-to-video prompts
6. write narration, subtitle, and shot metadata
7. package folders for images, clips, subtitles, and final editing
8. when requested and credentials are available, submit stills to Google Veo on Vertex AI in batch mode and assemble the returned clips

## Quick Output Contract

Default outputs:

- `storyboard.csv`
- `prompts.json`
- `narration.txt`
- `subtitles.srt`
- `production-notes.md`
- folders: `reference/`, `images/`, `video-clips/`, `audio/`, `final/`
- optional Veo automation files: `veo-batch/`, `video-clips/*-veo.mp4`, `final/*-veo.mp4`

When the user only asks for a prompt, output the optimized master prompt from
`references/master-prompt.md` customized to their request.

When the user asks to make this operational, run
`scripts/create_story_video_plan.py` to scaffold the production files.

When the user asks for automatic bulk generation, dynamic video, Veo, Vertex AI,
or "not just image projection", read `references/veo-vertex-ai.md` and use
`scripts/veo_batch_generate.py` after still images exist.

## Core Workflow

1. **Collect inputs**
   - photo references: use uploaded person photos only for face identity, facial expression, age impression, and hairstyle; do not preserve the original clothes, background, lighting, pose, or setting unless the user explicitly asks
   - story text: memory, concept, sales script, lesson script, or campaign idea
   - output target: 15s, 30s, 60s, 9:16, 16:9, social, lesson, ad, family video
   - desired style: documentary, cinematic, anime, commercial, watercolor, etc.

2. **Build anchors**
   - character anchor: face, age impression, hair, and facial expression from the photo; outfit, key props, pose, environment, and lighting are story-generated
   - style anchor: camera, color palette, lighting, medium, texture
   - continuity anchor: same character, same outfit, same location logic
   - negative anchor: no face change, no expression drift, no accidental reuse of original photo clothing/background, no extra limbs, no text

3. **Create the scene plan**
   - default to 6 scenes for 30 seconds
   - keep each scene to one action and one camera move
   - make scene durations equal unless the story needs emphasis
   - write the transition from the previous shot into each video prompt

4. **Write per-scene prompts**
   - image prompt: make a still image suitable as image-to-video input
   - video prompt: describe only motion, camera, and continuity constraints
   - narration: short, spoken, emotionally clear
   - subtitle: shorter than narration, readable on mobile

5. **Generate and iterate**
   - generate an enhanced character mother image first, preserving only the face identity and facial expression from the uploaded photo while regenerating clothing, background, props, and lighting from the story
   - generate scene stills from the same anchor phrase
   - use the previous clip's final frame as the next clip reference when possible
   - reject clips with face drift, expression drift, accidental original-photo clothing/background reuse, hand artifacts, text artifacts,
     unstable background, or camera motion that ignores the shot plan

6. **Assemble**
   - sort clips by `scene_id`
   - add narration and subtitles
   - use simple cuts or soft dissolves unless the story calls for stylized edits
   - output final video plus a reproducible prompt manifest

7. **Automatic bulk video generation**
   - use this only after scene stills exist in `images/`
   - confirm the user accepts Google Cloud / Veo billing before submitting jobs
   - prefer Google Veo on Vertex AI when the user wants true motion and local ADC is configured
   - generate each scene as a separate short clip, then combine clips into `final/`
   - store redacted request/status JSON under `veo-batch/`; never print access tokens or base64 video bytes
   - if Veo returns permission, quota, location, or billing errors, report the exact blocker and stop

## Master Prompt

Read `references/master-prompt.md` when the user wants an optimized single
prompt or a reusable prompt template.

Use it as the top-level instruction for ChatGPT/Codex-style planning. Replace
the bracketed fields and preserve the required output sections.

## Consistency Rules

Read `references/consistency-rules.md` when the user needs stable characters,
same person across scenes, or image-to-video continuity.

Most failures come from changing too many variables at once. Keep the character face and expression anchor constant, but let clothing, props, setting, and lighting come from the story. Vary only one major dimension per scene: action, camera, or background.

## Veo / Vertex AI

Read `references/veo-vertex-ai.md` before running true dynamic video generation.
Use `scripts/veo_batch_generate.py` to submit `prompts.json` scenes to Veo,
download clips, and assemble a final MP4. This script expects:

- Google Cloud CLI installed
- `gcloud auth application-default login` completed
- a project with Billing enabled and Vertex AI API enabled
- scene stills named consistently with `prompts.json`

Example:

```powershell
python C:\Users\C606\.codex\skills\image-story-video\scripts\veo_batch_generate.py `
  --plan .\image-story-video-output\prompts.json `
  --root .\image-story-video-output `
  --project gen-lang-client-0002502333 `
  --location us-central1 `
  --model veo-3.1-fast-generate-001 `
  --duration 4
```

## Script

Use the scaffold script from a project folder:

```powershell
python C:\Users\C606\.codex\skills\image-story-video\scripts\create_story_video_plan.py `
  --story .\story.txt `
  --title "family-memory-video" `
  --scenes 6 `
  --duration 30 `
  --aspect 9:16 `
  --style "warm cinematic documentary" `
  --out .\image-story-video-output
```

The script is deterministic and does not call image or video APIs. It prepares
the plan files that can then be used with image generation, Runway, Pika, Kling,
Veo, CapCut, FFmpeg, or other tools.

## User-Facing Trigger Examples

- "用 image-story-video，把這張照片和故事做成 30 秒影片分鏡與提示詞。"
- "幫我產生一個總提示詞，上傳人像照後自動規劃圖片、影片、旁白和字幕。"
- "把這段品牌故事拆成 8 個 image-to-video 鏡頭，人物和風格要一致。"
- "根據我的家庭照片做一支 60 秒回憶影片的 storyboard、prompts.json 和 SRT。"
- "用 Veo 自動大量生成 6 段 image-to-video clips 並合成影片。"
- "不要圖片投影，直接用 Vertex AI 產生真正動態影片。"

## Manga Text & Layout Quality Rules (Comic/Manga Specific)

When rendering Traditional Chinese dialogues onto manga/comic panels, follow these layout and typesetting rules:

1. **Ellipse-Fitting Dynamic Font Sizing & Wrapping**:
   - Do not use static font sizes or linear height boundaries. Use an ellipse-fitting check: $(w_{txt}/W)^2 + (h_{txt}/H)^2 \le 0.82$ where $W, H$ are speech bubble dimensions, $w_{txt}$ is text block width, and $h_{txt}$ is text block height.
   - If a line of text is too long, dynamically wrap it into multiple columns (read right-to-left) of balanced lengths. This prevents tiny font sizes or vertical overflow.

2. **Clean Bubble Validation & Anti-Hallucination**:
   - Check the original template to ensure a detected shape is a real speech bubble. Do not draw text over background elements (like clouds, sky details, or clothing decorations) that are mistakenly detected as white bubbles.
   - If a detected bubble is empty and has no corresponding dialogue in the script, leave it empty or delete its configuration to keep the background clean.

3. **Bubble-to-Speaker Alignment**:
   - Ensure the bubble tail (or thought bubbles) points to the correct speaker.
   - If a character is sleeping or silent, do not place their thoughts or words in bubbles pointing to them. E.g., for airplane or bedroom scenes where other characters are asleep, ensure the thought bubble points to the awake character.

4. **Silent Dialogues Support**:
   - If a user requests a character to say something without voice generation, render the text vertically in the bubble on the image, but do not add the dialogue to the audio generator/subtitles source files (such as `story.json`).

## Delivery Notes

- Be explicit about which steps can be automated locally and which require an
  external image/video model.
- Do not claim that image/video files were generated unless the tool actually
  produced them.
- For real people's photos, preserve privacy and avoid inventing sensitive identity details. Use the photo only for visible face identity, age impression, hairstyle, and facial expression unless the user explicitly requests otherwise; regenerate clothes, background, props, and lighting from the story.
- Treat Veo/Vertex AI as billable. Confirm or rely on explicit user instruction
  before submitting jobs, and report output duration because billing is commonly
  tied to generated video seconds.
