# Consistency Rules

Use these rules for stable characters, image sequences, and image-to-video
continuity.

## Character Anchor

Write one stable phrase and reuse it in every image prompt:

```text
same character: [age range], [face shape], [hair style/color], [outfit],
[signature accessory], [emotion baseline], consistent facial features
```

For real people, use visible traits only. Do not infer ethnicity, medical
conditions, religion, identity, or other sensitive attributes.

## Style Anchor

Keep style language stable:

```text
warm cinematic documentary, natural daylight, 35mm lens, shallow depth of field,
soft film grain, teal and amber shadows, realistic skin texture
```

Do not mix multiple art directions in the same sequence unless it is the
intentional story premise.

## Image Prompt Pattern

```text
[character_anchor based on face and expression only], [story-generated outfit],
[scene still], [simple pose], [story-generated environment],
[style_anchor], clean composition, do not copy original photo clothing or
background, no text, no logo, no watermark
```

Image prompts should create still frames. Avoid asking image generation for
complex actions like "running then jumping then turning around."

## Image-to-Video Prompt Pattern

```text
Using the reference image, create a [duration]-second [camera_motion].
The same character remains identical: same face, same hairstyle, same expression baseline, same story-generated outfit.
Action: [one small action].
Keep the same lighting, style, and location continuity.
No scene cut, no face change, no expression drift, no story outfit drift, no accidental reuse of original photo clothing/background, no new objects.
```

## Shot Continuity

- Scene 1: use the strongest character mother image.
- Scene 2+: use the previous final frame as reference when the tool supports it.
- Keep camera language simple: slow dolly-in, pan left, locked-off close-up,
  handheld micro-movement, gentle orbit.
- Keep duration short: 4-8 seconds per clip.
- Do not ask for dialogue mouth movement unless the model handles lip sync.

## Failure Fixes

| Failure | Fix |
| --- | --- |
| Face changes | Strengthen character anchor; use closer reference image; reduce motion. |
| Story outfit changes | Add "same story-generated outfit, same colors, no wardrobe change" to every prompt. |
| Extra limbs | Use simpler pose and "hands relaxed, no complex finger gestures." |
| Original photo clothes or background appears | Add "do not copy original photo clothing/background; use story-generated outfit and setting" to the image prompt. |
| Background jumps | Add location anchor and use the previous frame as reference. |
| Camera ignores prompt | Use one camera move only; remove competing motion verbs. |
| Text artifacts | Add "no text, no captions, no signage, no watermark" to image prompt. |

## File Naming

Use sortable names:

```text
reference/character-mother-01.png
images/scene-01-still.png
video-clips/scene-01-clip.mp4
audio/narration.wav
subtitles.srt
final/final-video.mp4
prompts.json
storyboard.csv
```
