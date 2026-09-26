# Image Prompt Guidance

All image assets for `soil-image-deck` must come from GPT image2
(`gpt-image-2`) through Codex built-in image generation. Do not replace any
image-generation step with local rendering.

## GPT Image2 Defaults

- Model intent: use GPT image2 for both image generation and image editing.
- Consistency: carry one shared visual bible across all prompts: subject
  identity, environment, camera/lens, palette, lighting, material style, UI motif,
  and negative prompt.
- Photo reference: when a user uploads a person photo, preserve only the face,
  expression, age impression, and key identity cues requested by the user; create
  clothing, PPE, background, props, and action from the story or slide content.
- Editable deck mode: generate text-free images and add all dense Chinese text
  in PowerPoint. Use baked Chinese text only for short cover titles or poster
  slides when specifically requested.
- Failure rule: if GPT image2 outputs cannot be persisted into local files, stop
  and report the limitation instead of falling back to local placeholders.

## Prompt Parts

Build each image prompt from:

1. Layout hint.
2. Image content brief.
3. On-image text, only for `baked` mode.
4. Shared style tokens from `image_policy`.
5. Negative prompt.

Example:

```text
左文右圖。圖像內容：Q版數學老師站在發光黑板前，黑板有幾何圖形與簡潔符號。
圖上文字：標題「看見比例」。
風格：扁平向量插畫，16:9 橫版，深夜藍背景，亮青藍主色，金黃點綴。
避免：逼真照片、雜亂背景、亂碼、英文字。
```

## Plate Mode

For `plate`, the image must be text-free:

```text
整張圖不要任何文字、不要英文字母、不要符號、不要 logo。
左側 40% 留深色乾淨空白區供 PowerPoint 文字疊加。
圖像內容：...
風格：...
```

## Suggested Sizes

- Full slide: `1536x1024`.
- Square card or icon image: `1024x1024`.
- Vertical side panel: `1024x1536`.

## Quality

- Default low quality is enough for drafts and most teaching slides.
- Upgrade cover, section divider, and closing/action slides when they are the
  visual anchor of the presentation.
