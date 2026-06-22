# remove-pdf-handwriting

A Codex skill for removing handwritten marks from worksheet and test PDFs while preserving printed content.

## What it does

- Removes colored handwriting such as red, blue, green, and yellow marks.
- Supports targeted erase rectangles for black handwriting.
- Supports restore rectangles for printed colored figures that automatic cleanup may remove.
- Rebuilds a clean raster PDF and writes page preview PNGs for review.

## Main files

- `SKILL.md`: skill instructions and workflow
- `scripts/clean_pdf_handwriting.py`: cleanup script
- `agents/openai.yaml`: skill agent metadata
- `vendor/`: bundled `pymupdf` and `Pillow` dependencies

## Basic usage

```powershell
python .\scripts\clean_pdf_handwriting.py `
  --input sample.pdf `
  --output sample_clean.pdf `
  --preview-dir clean_preview
```

With black-handwriting erase rectangles:

```powershell
python .\scripts\clean_pdf_handwriting.py `
  --input sample.pdf `
  --output sample_clean.pdf `
  --erase-json erase_rects.json
```

With printed-color restore rectangles:

```powershell
python .\scripts\clean_pdf_handwriting.py `
  --input sample.pdf `
  --output sample_clean.pdf `
  --restore-json restore_rects.json
```

## Notes

- Rectangle coordinates are 1-based page mappings to pixel-space boxes at the selected DPI.
- The script is conservative about black handwriting because printed worksheet text is usually black too.
- Review the generated preview images before delivering the final PDF.
