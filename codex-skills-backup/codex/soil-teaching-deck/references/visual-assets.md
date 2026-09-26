# Visual Assets

Use visuals only when they teach, orient, or create attention.

Every visual image in this reference must be generated with GPT image2
(`gpt-image-2`) through Codex's built-in image generation capability unless it is
a real user-provided asset. Local rendering with shapes, CSS, Pillow, SVG art, or
placeholder panels is not an acceptable substitute for AI-generated visuals.

## GPT Image2 Policy

- Use GPT image2 as the default image model for slide visuals.
- Generate or edit one consistent visual system per deck: same lens/style,
  lighting, palette, UI motif, character age/clothing, and environment logic.
- For user-provided photos, use the photo only for face, expression, pose, or
  identity reference when requested; regenerate clothing, background, props, and
  scene details from the story or slide content.
- Prefer text-free images for editable PPTX decks. Add Chinese text as
  PowerPoint text objects unless the user explicitly asks for baked image text.
- If GPT image2 output cannot be saved to local files in the current execution
  environment, pause and report that limitation instead of silently replacing it
  with local-rendered placeholders.

## Visual Roles

| Role | Use | Suggested Placement |
|---|---|---|
| illustration | concept or scenario image | right column or inset |
| background | cover/action/section visual | full bleed with overlay |
| hero | strong half-slide visual | right half |
| side_panel | decorative but meaningful strip | left or right edge |
| section_divider | chapter transition | full bleed |
| accent | small supporting icon/object | near the relevant text |

## Prompt Rules

- Include a consistent style token from the style engine.
- Ask for no readable text unless text must be baked into the image.
- Reserve clean space for text overlays on backgrounds.
- For editable-text image plates, generate the plate around the final text
  layout. Ask for a calm dark or light text zone in the exact side/region where
  PowerPoint text will sit, instead of adding a large overlay panel afterward.
- Use `low` quality for drafts and most illustrations; upgrade cover, key
  scenario, section divider, and closing/action pages when they anchor the deck.

## Editable Plate Rules

Use these rules when the output is "AI image + editable PowerPoint text":

- Generate fresh text-free plate images for the deck instead of trying to fix a
  busy image with opaque masks.
- Insert plate images as picture objects; add all titles, subtitles, bullets,
  labels, diagram text, KPI numbers, and callouts as editable PowerPoint objects.
- Do not flatten the entire completed slide into one bitmap for normal teaching
  or training decks.
- Treat the image as the designed page background: it should already include
  quiet negative space, edge framing, or a natural empty panel for text.
- Do not cover more than about 35-45% of the image with a post-added rectangle
  or translucent mask. If text does not read, regenerate the image with better
  reserved space.
- Keep overlay text to one editable PowerPoint text object per phrase. Avoid
  duplicate shadow text layers unless the user explicitly prefers visual polish
  over easy editing.
- If a slide needs dense bullets, split the slide or redesign the image plate;
  do not solve it by darkening the whole page.

## Final Deck Rule

Do not embed relative paths that will break after moving the deck folder. Insert
images into the PPTX file itself.
