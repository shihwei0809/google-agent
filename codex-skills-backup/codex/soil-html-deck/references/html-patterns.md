# HTML Deck Patterns

## Reference Shape

Match the design behavior of `G:\我的雲端硬碟\2026簡報\slides.html`:

- 10-12 slides, not a long scrolling page.
- SOIL sections shown by `data-section`: 引起動機, 維持注意, 喚起行動.
- Content is real HTML text/elements. Images are visual assets, not the whole
  deck, except intentional cover/closing full-bleed pages.
- Use a polished dark futuristic visual system: navy background, cyan + magenta
  accents, `Noto Sans TC`, `JetBrains Mono`, glassy panels, sparse borders.
- Use varied page types in a coherent sequence:
  1. full-bleed cover
  2. big question
  3. thesis / reframing
  4. clickable three-card overview
  5. split image/text detail page
  6. split image/text detail page, flipped
  7. split image/text detail page
  8. visual + sortable comparison table
  9. Chart.js radar or other interactive chart
  10. SVG decision tree / three choices
  11. workflow or method page, often 2x3 grid
  12. full-bleed closing CTA

## Base Structure

Use consistent slide sections:

```html
<body>
  <div id="progress"></div>
  <div id="section-tag"></div>
  <div id="pageInfo"></div>
  <div id="hint"></div>
  <main id="deck">
    <section class="slide active" data-slide="1" data-section="引起動機">...</section>
    <section class="slide" data-slide="2" data-section="維持注意">...</section>
  </main>
  <script>/* navigation and interactions */</script>
</body>
```

## CSS Defaults

```css
:root{
  --bg:#0a0e27; --bg-2:#11163a;
  --ink:#eef3ff; --ink-2:#b8c5e0; --ink-3:#7a8bb8;
  --accent:#00d4ff; --accent-2:#ff006e;
  --t1:55px; --t2:34px; --t3:21px; --t4:13px;
  --s1:80px; --s2:48px; --s3:24px; --s4:12px;
}
.slide{
  position:absolute; inset:0;
  display:flex; align-items:center; justify-content:center;
  padding:80px 100px;
  opacity:0; pointer-events:none;
  transform:translateY(16px);
  transition:opacity .55s ease, transform .55s ease;
  overflow:hidden;
}
.slide.active{ opacity:1; pointer-events:auto; transform:translateY(0); }
.slide-inner{ width:100%; max-width:1320px; }
```

For narrow viewports, reduce padding and convert two-column grids to one column.
Do not shrink all global font variables to fix a single overflowing slide.

## Required CSS Components

Use these class concepts consistently:

- `.full-img`: absolute full-bleed image with gradient overlay for cover and
  closing pages.
- `.split`: two-column layout for type/detail pages.
- `.split-img`: square or 3:2 AI image block with rounded corners, shadow, and
  small `.img-tag`.
- `.three-col`: three equal cards for overview or choices.
- `.type-card`: clickable overview card with `.card-img`, `.badge`, heading, and
  short paragraph.
- `table.compare`: sparse comparison table with only bottom rules; headers may
  call `sortTable(col)`.
- `.chart-wrap`: fixed-height Chart.js container; render charts lazily only when
  the slide becomes active.
- `.soil-flow` / `.soil-step`: 2x3 or 3x2 workflow grid.
- `.closing`: centered closing text with large gradient answer and CTA.

## Required Page Patterns

### Clickable Overview Cards

```html
<div class="three-col">
  <div class="type-card" onclick="goto(5)">
    <div class="card-img"><img src="data:image/jpeg;base64,..."></div>
    <span class="badge">TYPE 01</span>
    <h3>純圖片 .pptx</h3>
    <p>每頁是 AI 整頁生成的圖。</p>
  </div>
</div>
```

### Split Detail Page

```html
<div class="split">
  <div class="split-img">
    <span class="img-tag">TYPE 01 · IMAGE</span>
    <img src="data:image/jpeg;base64,...">
  </div>
  <div>
    <span class="kicker">類型 1</span>
    <h1 class="t1">純圖片簡報</h1>
    <p class="t3">每一頁都是 AI 整頁生成。</p>
    <ul class="t3">
      <li>✓ 視覺衝擊最強</li>
      <li>✗ 文字燒在圖裡，無法後改</li>
    </ul>
  </div>
</div>
```

Flip the order on alternating detail slides to create a Z-pattern.

### Comparison Table

```html
<table class="compare">
  <thead><tr><th onclick="sortTable(0)">能力 ⇅</th><th>傳統簡報</th><th>HTML 簡報</th></tr></thead>
  <tbody id="compareBody">...</tbody>
</table>
```

### Chart Page

```html
<div class="chart-wrap"><canvas id="radarChart"></canvas></div>
```

Render the chart only when the chart slide is first opened.

### Decision Tree

Use an SVG line layer from the central question to three choice cards. The cards
should be real HTML blocks, not baked into the background image.

## Required Navigation

- ArrowRight / Space / PageDown: next slide.
- ArrowLeft / PageUp: previous slide.
- F: fullscreen.
- Click right 30% of viewport: next. Click left 30%: previous.
- Update progress width, `#section-tag`, and `#pageInfo` on every slide change.
- Ignore click-to-navigate when the user clicks cards, table headers, buttons,
  links, or image blocks.
- Lazy-render Chart.js pages inside `goto(n)` after activating that slide.
- Do not rely on browser-created global variables from element ids. Always bind
  explicit DOM references:

```js
const progressBar = document.getElementById('progress');
const sectionTagEl = document.getElementById('section-tag');
const pageInfoEl = document.getElementById('pageInfo');
```

Then update `progressBar.style.width`, `sectionTagEl.textContent`, and
`pageInfoEl.textContent` inside `goto(n)`.

## Common Layouts

- Cover: full-bleed background image with readable overlay, or strong type-only
  opening if no image is available.
- Problem: large question, one support sentence, optional symbolic image.
- Overview: three cards in a grid.
- Explanation: two columns; alternate image/text order across consecutive pages.
- Comparison: sparse table with bottom borders only.
- Data: Chart.js chart rendered lazily when the slide becomes active.
- Decision: central question plus three result cards; SVG lines are acceptable.
- Action: one clear next step and one memorable closing sentence.

## Image Embedding

All images referenced by the deck must originate from Codex built-in image
generation or user-provided real image assets. CSS-only art, locally rendered
shape compositions, or procedural placeholder images do not satisfy an "AI image"
requirement.

For this skill, the preferred image plan is:

- cover and closing: full-bleed AI images, optionally with low baked text when
  the image itself is intended as a poster-like hero.
- overview cards: one square image per card, no baked body text.
- split detail pages: one square or 3:2 image per detail page, no baked body text.
- comparison/workflow pages: one supporting image beside real table/grid content.

Use Pillow or another image library to resize and compress large images before
base64 embedding. Aim for 1280px wide for full-bleed images and 900px wide for
card images unless the visual needs more detail.

Final HTML should not break if the folder is moved.

## Validation Checklist

Before delivery, inspect the file or rendered page for:

- exactly the planned number of `<section class="slide">` elements
- every `<img src="...">` starts with `data:image/...;base64,`
- `goto(n)` updates active slide, progress bar, section tag, and page number
- table headers call `sortTable(col)` and sorting changes real table rows
- Chart.js is initialized lazily only when the chart slide becomes active
- decision-tree choices are real clickable HTML cards, not baked into an image
- no accidental references to undefined id globals such as `sectionTag`
