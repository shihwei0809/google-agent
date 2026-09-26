---
name: soil-html-deck
description: >
  Create a SOIL-style HTML presentation as a single portable .html file.
  Use when the user asks for HTML slides, web slides, interactive slides,
  online/shareable slides, livestream slides, Chart.js or clickable-table slides,
  or a presentation that should not be limited by PowerPoint. Output should be
  a standalone HTML file with inline CSS/JS and base64-embedded images whenever
  images are used.
metadata:
  short-description: SOIL HTML interactive slide deck
---

# SOIL HTML Deck

Use this skill to create a single `.html` presentation with SOIL teaching logic,
responsive full-screen slides, AI-generated bitmap visuals used as page assets,
and real HTML/CSS/JS content and interactions.

The target quality bar is the local Claude reference deck
`G:\我的雲端硬碟\2026簡報\slides.html`: a 10-12 page SOIL web deck with
full-bleed hero pages, clickable type cards, alternating split image/text pages,
sortable comparison tables, lazy Chart.js charts, an SVG decision tree, a SOIL
workflow page, and a closing CTA.

## Output Contract

- Produce one portable HTML file, usually `slides.html`.
- Inline CSS and JS in the file. CDN is acceptable for Chart.js and fonts.
- If images are used, embed them as `data:image/...;base64,...`; do not rely on
  relative image paths in the final HTML.
- Every visual image, background image, illustration, card image, cover image,
  or section visual must be generated with Codex's built-in image generation
  capability first. Do not replace image-generation steps with local shape
  rendering, procedural drawing, CSS-only art, or placeholder panels unless the
  user explicitly asks for a prototype without AI images.
- Use a browser-openable file. Do not create a React/Vue project unless the user
  explicitly asks for an app.
- Report the final absolute file path.
- Do not turn the deck into an image slideshow. Except for intentional full-bleed
  hero/closing pages, titles, paragraphs, cards, tables, charts, decision nodes,
  labels, and CTA text must be real HTML text/elements.

## Workflow

1. Read the user's material and choose 10-12 slides unless a page count is given.
2. Draft a concise slide plan using the reference sequence in
   `references/html-patterns.md`: cover, question, thesis, overview cards,
   2-3 split detail pages, comparison table, chart, decision tree, workflow, CTA.
   If the user asked to proceed directly, continue without waiting.
3. Build the deck using the structure and rules in
   `references/html-patterns.md`.
4. Generate every needed visual with the built-in image generation skill. Use
   text-free images for card/split/table/workflow visuals; full-bleed hero images
   may include light baked text only if the slide design calls for it.
5. Convert final images to base64 before embedding.
6. Verify the HTML at desktop and smaller preview sizes. Check that text fits,
   slide navigation works, progress/page labels update, all `<img>` sources are
   base64 data URIs, and charts initialize only when needed.

## Design Rules

- Follow the SOIL rhythm: 引起動機 -> 維持注意 -> 喚起行動.
- Each slide has one core message.
- Page titles should be no more than 10 Chinese characters when possible.
- Use type hierarchy based on 55 / 34 / 21 / 13.
- Use only 1-2 strong accent colors.
- Include a top progress bar, section label, and page number.
- Use Z-pattern alternation for repeated explanation slides.
- Use images as designed assets: `.full-img` for cover/closing, `.card-img` for
  overview cards, `.split-img` for detail pages, and supporting visuals beside
  tables/workflow pages.
- Include at least two real interactions beyond slide navigation when content
  permits: clickable cards that jump to detail slides, sortable table columns,
  lazy Chart.js rendering, feature buttons, or a clickable decision tree.
- Avoid fixed 1920x1080 stages with `transform: scale(...)`; use full viewport
  slides with `position:absolute; inset:0`.

## When To Read References

- Read `references/html-patterns.md` before implementing a deck.
- If the deck includes charts, tables, decision trees, or slide navigation, use
  the implementation patterns in that reference.
- If the task resembles the AI Agent three-format deck, reuse or adapt
  `scripts/build_type3_html_v3_soil_skill.py` instead of rebuilding the same
  navigation, base64 embedding, table sorting, chart, and decision-tree code
  from scratch.

## Codex Notes

- Use PowerShell examples in user-facing instructions.
- If using the in-app browser is available and the user wants preview/testing,
  open the local HTML there for inspection.
- If generated images must be saved to local files for packaging, use a workflow
  that preserves the actual image-generation outputs. Do not silently substitute
  locally rendered graphics.
