---
name: remove-pdf-handwriting
description: Remove handwritten answer marks from PDFs, especially worksheet/test PDFs containing red, blue, or black pen handwriting, answer annotations, hand-drawn lines, handwritten letters/numbers, checkmarks, and residual colored marks. Use when Codex needs to clean a PDF by removing student/teacher handwriting and output a clean copy while preserving printed exam text, formulas, tables, and diagrams.
---

# Remove Pdf Handwriting

## Overview

Use this skill to produce a clean PDF from a marked-up worksheet/test PDF. The bundled script performs raster cleanup: it renders each page, removes colored handwriting by color thresholding, optionally erases user-specified black handwriting rectangles, then rebuilds a PDF. The cleanup goal is to remove handwriting while preserving printed exam text, formulas, tables, graphs, axes, grid lines, and diagrams.

## Workflow

1. Inspect the PDF first by rendering a few pages to PNG previews.
2. Run `scripts/clean_pdf_handwriting.py` with the input PDF and output path.
3. For colored handwriting, rely on automatic color cleanup first.
4. If automatic color cleanup removes original colored artwork, diagrams, or option figures, add tight original-image restore rectangles with `--restore-json`.
5. For black handwriting, avoid full-page black deletion because printed text is also black. Add targeted page rectangles with `--erase-json`.
6. Inspect preview images in the generated preview directory, especially pages with black marks, diagrams, charts, colored figures, or grid backgrounds.
7. If an erase rectangle damages printed content, shrink it, split it into smaller rectangles, or remove it. If a restore rectangle brings back handwriting, shrink it, split it around the printed colored object, or add a later tight erase rectangle.
8. Rerun until the preview balances handwriting removal with printed-content preservation.

## Script Usage

Basic colored-handwriting cleanup:

```powershell
python .codex\skills\remove-pdf-handwriting\scripts\clean_pdf_handwriting.py `
  --input a.pdf `
  --output a_clean.pdf
```

Include targeted black handwriting masks:

```powershell
python .codex\skills\remove-pdf-handwriting\scripts\clean_pdf_handwriting.py `
  --input a.pdf `
  --output a_clean.pdf `
  --erase-json erase_rects.json
```

Restore original colored worksheet content that automatic cleanup removed:

```powershell
python .codex\skills\remove-pdf-handwriting\scripts\clean_pdf_handwriting.py `
  --input a.pdf `
  --output a_clean.pdf `
  --restore-json restore_rects.json
```

The JSON files map 1-based page numbers to pixel-space rectangles at the selected DPI:

```json
{
  "4": [
    [1825, 2430, 2115, 2540],
    [1035, 2550, 1355, 2640]
  ]
}
```

Useful options:

- `--dpi 220`: rendering resolution. Higher values improve quality but increase runtime and file size.
- `--preview-dir clean_preview`: write cleaned PNG previews for review.
- `--no-color-clean`: only apply rectangle erasures.
- `--restore-json restore_rects.json`: after color cleanup and before erase rectangles, copy specified regions from the original render back into the cleaned page.

## Colored Handwriting Guidance

Automatic color cleanup is intended for colored handwriting and residual colored marks, including:

- Red, orange, and pink marks.
- Blue and light-blue marks.
- Yellow highlighter-like marks.
- Green marks.
- Pale ghosts left by antialiasing or compression.

Use the automatic pass first. If colored marks remain, inspect whether they are truly handwriting. Do not expand thresholds so aggressively that printed colored diagrams, chart elements, or photos are removed. If a colored handwritten mark overlaps a printed colored graphic, prefer preserving the printed graphic unless the user explicitly accepts damage.

## Printed Colored Content Recovery

Automatic color cleanup can remove original worksheet content when the source includes colored option figures, diagrams, chart keys, or highlighted printed shapes. Handle this as a restore workflow:

- Render and compare original and cleaned previews side by side.
- Identify colored content that belongs to the original worksheet, not the handwriting.
- Add small `--restore-json` rectangles around only the printed colored object.
- Avoid including answer blanks, question text endings, or nearby handwritten answer marks in restore rectangles.
- If one broad restore rectangle brings back red/blue handwriting, split it into smaller rectangles around the printed shapes or add a tight `--erase-json` rectangle for the restored handwriting.
- After restore, re-run colored-residual checks. A remaining colored component may be legitimate printed artwork; confirm its location before erasing it.

When a page contains both printed red content and red handwriting, do not treat "any red pixel" as handwriting. Preserve printed red shapes by restore rectangles, then remove isolated handwritten red marks in nearby blanks with tight erase rectangles.

## Residual Color Checks

After generating a candidate clean PDF, it is useful to scan the cleaned preview images for remaining saturated red, blue, green, or yellow connected components:

- Large or structured components inside printed diagrams may be original worksheet content.
- Small components near answer blanks, margins, or question-ending parentheses are often residual handwriting.
- If residual color is near restored artwork, inspect at original resolution before erasing.
- Final validation should include both automated component detection and visual inspection; component detection is a guide, not a substitute for page review.

## Black Handwriting Guidance

When removing black handwriting:

- Render the page preview and identify only the handwritten regions.
- Use small rectangles around black handwritten lines, letters, and numbers.
- Prefer rectangles in blank margins, answer spaces, or open white areas.
- Do not erase large blocks that overlap printed text, formulas, tables, graphs, axes, grid lines, or diagrams.
- If a large hand-drawn mark crosses printed content, use several smaller rectangles around the handwritten strokes instead of one broad rectangle.
- Re-check the affected page preview after every rectangle adjustment.

## Overlap Policy

When handwriting overlaps original worksheet content, prioritize preserving the original content:

- Do not use a white rectangle if it would remove printed question text, formulas, labels, graph axes, grid lines, or diagram strokes.
- For black handwriting directly on top of black printed content, default to leaving that residual mark in place unless there is a safe small rectangle that removes handwriting without damaging the printed content.
- For handwriting near but not touching printed content, use tight rectangles and verify the preview.
- For handwriting on charts or coordinate grids, avoid broad cleanup that breaks the grid; remove only marks in blank regions or clearly outside the required graph content.
- It is acceptable to deliver a PDF with small residual handwriting where removing it would make the worksheet less readable. Mention that tradeoff in the final response.

## Quality Checks

Before delivering:

- Confirm the output PDF opens and has the same page count as the input.
- Inspect all pages that had erase rectangles.
- Spot-check pages with colored diagrams, photos, charts, or grid backgrounds for accidental removal.
- Verify no large blank boxes cut through printed questions or diagrams.
- If residual marks remain because they overlap printed content, state that they were intentionally preserved to avoid damaging the original worksheet.

## Dependency Notes

The script requires `pymupdf` and `Pillow`. This skill includes those dependencies under `vendor/` and loads that directory first, so the skill remains usable if the project root is cleaned and only `.codex` is kept. If `vendor/` is removed or incompatible with the active Python version, reinstall `pymupdf` and `Pillow` or restore the `vendor/` directory.
