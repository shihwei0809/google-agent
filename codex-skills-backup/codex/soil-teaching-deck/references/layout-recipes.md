# Layout Recipes

Use a 16:9 canvas. Keep margins at least 0.5 inches unless a full-bleed slide is
intentional.

## Page Roles

| Role | Layout |
|---|---|
| 封面 | Large title, subtitle, presenter/date, optional full-bleed or half-bleed visual |
| 問題引入 | One large question plus one support line |
| 迷思澄清 | Two columns: 誤解 vs 正確理解 |
| 比較 | Two-column or table with minimal borders |
| 流程 | 3-5 steps with arrows or timeline |
| 分類 | 2x2 or 2x3 grid |
| 案例 | Scenario visual plus short interpretation |
| 數據 | One big number or one chart, not a dense table |
| 總結 | Three takeaways and the one-sentence core |
| 行動 | Clear next step and closing sentence |
| 過渡 | Full color/image slide with one line |

## Grid Defaults

- Left margin: 0.6-0.7 inch.
- Right column starts around 6.7 inch for half-half layouts.
- Three cards: x positions around 0.6, 4.85, 9.1.
- Use consistent title y across standard content slides.

## Image Plate + Editable Text Layout

For Claude-level "image + editable text" decks, do not build a generic dark
text panel over any image. First decide the text region, then generate a
text-free AI plate with that region already calm enough for text.

Preferred compositions:

- left 42-45% text region, visual action on right
- right 42-45% text region, visual action on left
- top-left title region plus lower cards or workflow objects
- center-left closing text region with a strong visual on the right

Avoid these failure modes:

- a full-slide dark overlay that makes the AI image disappear
- a big rectangle that blocks the main subject
- transparent masks stacked on top of already dark images
- duplicate text boxes used only as shadows, which makes editing tedious
- placing long bullet lists over busy detailed scenery

## Text Hierarchy

- Cover title: 72-84pt.
- Slide title: 44-56pt.
- Subtitle: 28-34pt.
- Body: 18-21pt.
- Note/muted: 14-16pt.
- Badge: 18-22pt.

## Math Text In PowerPoint

PowerPoint editable text is not the same as Word OMML. For formulas:

- Keep normal Chinese explanation in editable text boxes.
- Put formula parts in separate text boxes when the font or baseline needs
  different handling.
- For complex notation, render the formula as a small transparent image and
  place it beside editable labels.
- Avoid a single mixed text box containing long Chinese text and fragile formula
  notation.
# Editable Object Rule

For training, SOP, business, teaching, and travel decks, build slides as mixed
PowerPoint objects by default:

- Titles, section labels, bullets, captions, and emphasis text are editable text
  boxes.
- Timeline nodes, flow chart boxes, KPI cards, FAQ blocks, badges, and callouts
  are editable PowerPoint shapes.
- Charts should be editable chart objects when data is simple; otherwise use
  grouped shapes that can still be edited.
- GPT image2 outputs are inserted as picture objects for scenario visuals,
  character scenes, backgrounds, or supporting image cards.
- Avoid full-slide flattened PNG/JPEG pages unless the user explicitly asks for
  image-only, poster, baked, livestream, or social-share output.
