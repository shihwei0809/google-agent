# Plate Mode Spec Format

Use `spec.yaml` when images are clean backgrounds and PowerPoint text should
remain editable.

```yaml
style:
  palette:
    bg: "#0D1B2A"
    primary: "#00C6FF"
    highlight: "#FFD700"
    text: "#FFFFFF"
    muted: "#A5B4CB"
    card: "#1E3A5F"
  font: "Microsoft JhengHei"
  title_font: "Microsoft JhengHei"
  body_font: "Microsoft JhengHei"

pages:
  - page: 1
    image: page_01
    img_x: 0
    img_y: 0
    img_w: 13.333
    img_h: 7.5
    bg: bg
    blocks:
      - type: badge
        text: "EP15"
        x: 0.7
        y: 0.7
        w: 2.2
        h: 0.5
        bg: primary
        color: bg
        size: 14
      - type: title
        text: "把生圖\n放進簡報"
        x: 0.7
        y: 1.6
        w: 6.5
        h: 2.5
        size: 48
        color: text
        bold: true
      - type: subtitle
        text: "gpt-image × SOIL 工作流"
        x: 0.7
        y: 4.75
        w: 6.5
        h: 1
        size: 22
        color: primary
```

## Block Types

- `title`, `subtitle`, `body`, `muted`, `highlight`: editable text.
- `badge`: rounded label with background color.
- `card`: rounded visual area without text.
- `bar`: thin separator bar.
- `progress`: progress bar with `current` and `total`.

Coordinates use PowerPoint inches on a 16:9 canvas: `13.333 x 7.5`.
# Editable Plate Requirement

When a deck must remain editable, `plate` mode is required:

- GPT image2 creates only text-free backgrounds, scenes, characters, or image
  cards.
- `spec.yaml` must define editable PowerPoint text boxes for titles, bullets,
  captions, labels, and callouts.
- Do not use baked mode for training, SOP, business, travel, or teaching decks
  unless the user explicitly requests image-only slides.
