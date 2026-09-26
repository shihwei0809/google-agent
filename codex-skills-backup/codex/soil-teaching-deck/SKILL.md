---
name: soil-teaching-deck
description: >
  Create, analyze, or improve SOIL-style teaching PowerPoint decks. Use when the
  user asks for teaching slides, classroom slides, lesson-material-to-slides,
  SOIL slides, instructional presentation design, or a review of an existing
  teaching deck's cognitive load and teaching flow. Produces editable .pptx
  slides with PowerPoint text objects, optional AI illustrations, optional
  geometry diagrams, and a SOIL teaching structure.
metadata:
  short-description: SOIL editable teaching PPTX deck
---

# SOIL Teaching Deck

Use this skill for editable instructional PowerPoint decks. The goal is teaching
clarity first, visual design second, and file correctness last.

## Output Contract

- Produce an editable `.pptx` unless the user asks only for diagnosis or style.
- Text should remain PowerPoint text objects.
- Default to an editable mixed-object deck for business, SOP, training, travel,
  and teaching requests. Do not export each slide as one flattened bitmap image.
- Keep diagrams, timelines, flow charts, KPI cards, labels, tables, callouts,
  and content blocks as editable PowerPoint shapes/text whenever practical.
- Use GPT image2 images as inserted picture objects only for scenario visuals,
  backgrounds, illustrations, product/place photos, or character images; do not
  bake all slide text and structure into those images unless the user explicitly
  asks for an image-only deck.
- Do not force every deck to be 10 slides. Choose slide count from content
  density, lesson duration, and audience need. Use 10 slides only when the user
  asks for 10 pages or the content naturally fits that length.
- Every non-geometric visual image, including cover visuals, background images,
  illustrations, section-divider images, and card images, must be generated with
  GPT image2 (`gpt-image-2`) through Codex's built-in image generation
  capability first. Do not substitute local shape rendering or procedural
  placeholder images for AI images.
- For math symbols in PowerPoint, use the two-layer text-box approach when needed:
  keep readable surrounding text editable, and isolate symbols/formulas in
  separate boxes or rendered image snippets if PowerPoint text handling is weak.
- Report the final absolute file path.

## Mode Selection

Choose the path from the user's request:

- Material to deck: run SOIL engines 1-6.
- Topic only: first expand a minimal teaching outline, then run engines 1-6.
- Existing deck review: inspect the deck, run cognitive diagnosis, then propose
  or implement fixes.
- Style definition: run only the style engine and output a reusable style spec.

If the user has already provided enough detail, do not stop for a long interview.
Ask only the next missing detail that affects the work, usually audience and
lesson duration.

## Core Workflow

1. Concept positioning: identify the one big idea, three sub-ideas, common
   misunderstandings, takeaway sentence, minimal fact pack, and slide-vs-talk
   split. See `references/soil-engines.md`.
2. Context positioning: arrange 引起動機 -> 維持注意 -> 喚起行動.
3. Page architecture: choose page roles, one core point per page, layout recipe,
   and any `visuals` or `geometry` needs. See `references/layout-recipes.md`.
4. Cognitive editing: reduce noise, chunk, add information, structure, sequence,
   and step the content.
5. Style construction: define palette, fonts, title/body scale, motif, and image
   policy.
6. Build and verify the PPTX using the local presentation workflow. Prefer the
   available Presentations skill when it is active; otherwise use
   `python-pptx` patterns consistent with the repo. Insert GPT image2 assets as
   pictures, then build text and information design as editable PPT objects.

## Design Rules

- Use a 16:9 wide deck.
- Type scale: cover title 72-84pt, slide title 44-56pt, subtitle 28-34pt,
  body 18-21pt, muted 14-16pt.
- Use Microsoft JhengHei / 微軟正黑體 for all editable PowerPoint text by
  default, including titles, subtitles, body text, tables, chart labels, flow
  nodes, KPI cards, captions, callouts, notes, and placeholders. Do not switch
  to another Chinese font unless the user explicitly provides a brand font.
- Keep page titles short, ideally <= 10 Chinese characters.
- Use fixed alignment grids and consistent margins.
- Avoid pure text pages, simple bullet-only pages, simple rectangles, one-image
  plus text pages, and repeated same-layout pages.
- Every content page must combine at least 3 visual elements; prefer 3-5 when
  the topic supports it. Valid elements include timeline, flow chart, statistic
  chart, infographic card, KPI card, map, character figure, before/after
  comparison, scenario image, image collage, step cards, FAQ block, and emphasis
  tags.
- Every page should include at least one GPT image2-generated or GPT image2-edited
  bitmap visual unless the user explicitly asks for a non-AI/local prototype.
  Pair the main visual with smaller visuals, icons, labels, diagrams, charts, or
  cards rather than using one full-page image.
- For editable decks, do not place a generated full-slide screenshot as the only
  slide object. A slide should contain separate editable text boxes and shapes
  plus one or more image objects.
- If a prior output was flattened but the user expects editable圖文, rebuild it
  as a mixed-object PPTX instead of only resizing or replacing the bitmap.
- Vary slide layouts intentionally. For a 10-slide deck, use this default role
  sequence unless content requires a better order: cover with big image and
  title; timeline; flow chart; infographic cards; KPI/dashboard; image plus
  explanation; before/after comparison; FAQ; infographic synthesis; closing
  summary.
- Use only 1-2 accent colors.

## References

- Read `references/soil-engines.md` for SOIL planning outputs.
- Read `references/layout-recipes.md` before building slides.
- Read `references/visual-assets.md` when AI illustrations or background images
  are needed.
- Read `references/geometry.md` for math diagrams.
- Read `references/validation.md` before final delivery.

## Codex Conversion Notes

- Do not use Claude-only paths such as `/home/claude`, `/mnt/skills`, or
  `.claude/skills/draw/draw.py`.
- Use PowerShell in commands and user-facing examples.
- Use GPT image2 (`gpt-image-2`) via Codex built-in image generation for every
  bitmap visual image. Only precise math/geometry diagrams are exempt; those
  should be deterministic SVG/Python drawings for correctness.
- Preserve editability as the default: PowerPoint users must be able to click
  and edit titles, captions, bullet text, flow boxes, KPI numbers, emphasis
  tags, and basic diagrams independently from the AI images.
- When saving a `.pptx`, set both run-level fonts and theme/default fonts to
  Microsoft JhengHei / 微軟正黑體 so newly edited text in PowerPoint continues to
  use the same font.
- Keep AGENTS.md clean; progress and teaching notes belong in Obsidian if the
  user asks for project synchronization.
