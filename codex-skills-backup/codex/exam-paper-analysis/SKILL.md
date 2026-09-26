---
name: exam-paper-analysis
description: Download official past exam papers, extract text, analyze recurring topics and unit frequency, summarize yearly patterns, and generate study strategies plus infographic outputs. Use when the user asks to analyze 歷屆試題、會考試題、學測試題、分科試題、模考題本, especially when the task includes searching official sources, downloading PDFs, counting topic frequency, or producing visual study summaries.
---

# Exam Paper Analysis

Use this skill to turn official past papers into a reusable analysis package.

## Workflow

1. Confirm the exam scope from the user request or infer it from context:
   - exam type
   - organizer / official source
   - year range
   - required outputs such as summaries, frequencies, strategies, or infographics
2. Prefer official sources first. When searching, use the web tool and search engines, then download only the files needed into the user's workspace.
3. Extract PDF text with `scripts/extract_pdf_text.py` when the source is PDF and the analysis needs per-question review.
4. Build the analysis around these deliverables:
   - exam file inventory
   - yearly highlights
   - topic or unit frequency table
   - preparation strategies tied to the target score band
5. Produce visual outputs when requested. Use `scripts/render_infographic.py` to render one SVG per infographic from a JSON spec.

## Output Pattern

For exam-analysis requests, default to these artifacts unless the user asks for something narrower:

- one Markdown summary file
- one HTML index page if there are multiple infographic files
- one infographic for historical focus / frequency
- one infographic for overall preparation strategy
- one infographic for lower-band improvement plan
- one infographic for higher-band improvement plan

## Topic Classification

Use one primary topic per question for frequency counting. For the default Taiwan high-school math taxonomy, read [references/topic-taxonomy.md](references/topic-taxonomy.md).

If a question spans multiple chapters, classify it by the main bottleneck skill needed to solve it.

## Practical Notes

- Prefer UTF-8 reads and writes for Chinese content.
- If the PDF text extract is noisy, still use it as a question locator and verify ambiguous items against the PDF itself.
- State the counting rule in the final summary so the frequency table is interpretable.
- If the user says `會考` but the downloaded papers are actually `學測` or another exam, call that out explicitly and continue based on the confirmed or inferred scope.

## Scripts

- `scripts/extract_pdf_text.py`
  - Extract all matching PDFs in a folder to UTF-8 text files.
- `scripts/render_infographic.py`
  - Render one SVG infographic from a JSON spec.

## Minimal Procedure

1. Search official source pages.
2. Download PDFs into the requested folder.
3. Extract question text if needed.
4. Read enough questions to map recurring units.
5. Write the Markdown analysis.
6. Render infographic SVG files from JSON specs.
7. Create a simple HTML index page when there are multiple visual outputs.
