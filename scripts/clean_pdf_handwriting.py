"""Remove colored handwriting and targeted black marks from a PDF.

This script renders pages to images, removes red/blue handwriting by pixel
thresholds, applies optional page-specific white rectangles for black handwriting,
optionally restores original regions that contain printed colored artwork, then
rebuilds a raster PDF.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Iterable


def add_local_import_paths() -> None:
    script_path = Path(__file__).resolve()
    skill_root = script_path.parents[1]
    candidates = [
        skill_root / "vendor",
        Path.cwd() / "pylibs2",
        Path.cwd() / "pylibs",
        script_path.parents[4] / "pylibs2" if len(script_path.parents) > 4 else None,
        script_path.parents[4] / "pylibs" if len(script_path.parents) > 4 else None,
    ]
    for candidate in candidates:
        if candidate and candidate.exists():
            sys.path.insert(0, str(candidate))


add_local_import_paths()

try:
    import fitz
    from PIL import Image, ImageDraw
except ImportError as exc:
    raise SystemExit(
        "Missing dependency. Install pymupdf and Pillow, or place them in a local "
        f"pylibs/pylibs2 directory. Original error: {exc}"
    ) from exc


Rect = tuple[int, int, int, int]


def is_mark_pixel(r: int, g: int, b: int) -> bool:
    """Detect colored handwriting, including pale ghosts."""
    mx = max(r, g, b)
    mn = min(r, g, b)
    saturation = mx - mn

    light_red_ghost = r > 190 and g > 165 and b > 165 and r - g > 8 and r - b > 8
    light_blue_ghost = b > 190 and r > 165 and g > 165 and b - r > 8 and b - g > 6
    light_yellow_ghost = r > 190 and g > 175 and b < 165 and r - b > 35 and g - b > 25
    light_green_ghost = g > 175 and r < 190 and b < 190 and g - r > 25 and g - b > 20
    if light_red_ghost or light_blue_ghost or light_yellow_ghost or light_green_ghost:
        return True

    if saturation < 45 or mx < 95:
        return False

    red = (
        r >= 145
        and r > g * 1.28
        and r > b * 1.18
        and g < 170
        and b < 170
    )
    blue = (
        b >= 120
        and b > r * 1.18
        and b > g * 1.08
        and r < 175
        and g < 190
    )
    yellow = (
        r >= 170
        and g >= 145
        and b < 145
        and r > b * 1.35
        and g > b * 1.25
    )
    green = (
        g >= 130
        and g > r * 1.15
        and g > b * 1.10
        and r < 190
        and b < 190
    )
    return red or blue or yellow or green


def clean_colored_marks(img: Image.Image, radius: int) -> tuple[Image.Image, int]:
    rgb = img.convert("RGB")
    pixels = rgb.load()
    width, height = rgb.size
    mask = bytearray(width * height)
    count = 0

    for y in range(height):
        row = y * width
        for x in range(width):
            r, g, b = pixels[x, y]
            if is_mark_pixel(r, g, b):
                mask[row + x] = 1
                count += 1

    expanded = bytearray(mask)
    for y in range(height):
        row = y * width
        for x in range(width):
            if not mask[row + x]:
                continue
            for yy in range(max(0, y - radius), min(height, y + radius + 1)):
                base = yy * width
                for xx in range(max(0, x - radius), min(width, x + radius + 1)):
                    expanded[base + xx] = 1

    for y in range(height):
        row = y * width
        for x in range(width):
            if expanded[row + x]:
                pixels[x, y] = (255, 255, 255)

    return rgb, count


def load_erase_rects(path: str | None) -> dict[int, list[Rect]]:
    if not path:
        return {}
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    result: dict[int, list[Rect]] = {}
    for page_key, rects in raw.items():
        page_number = int(page_key)
        parsed: list[Rect] = []
        for rect in rects:
            if len(rect) != 4:
                raise ValueError(f"Invalid rectangle on page {page_key}: {rect}")
            x1, y1, x2, y2 = (int(v) for v in rect)
            parsed.append((x1, y1, x2, y2))
        result[page_number] = parsed
    return result


def load_restore_rects(path: str | None) -> dict[int, list[Rect]]:
    return load_erase_rects(path)


def apply_erase_rects(img: Image.Image, rects: Iterable[Rect]) -> None:
    draw = ImageDraw.Draw(img)
    width, height = img.size
    for x1, y1, x2, y2 in rects:
        x1 = max(0, min(width, x1))
        x2 = max(0, min(width, x2))
        y1 = max(0, min(height, y1))
        y2 = max(0, min(height, y2))
        if x2 > x1 and y2 > y1:
            draw.rectangle((x1, y1, x2, y2), fill=(255, 255, 255))


def apply_restore_rects(img: Image.Image, original: Image.Image, rects: Iterable[Rect]) -> None:
    width, height = img.size
    for x1, y1, x2, y2 in rects:
        x1 = max(0, min(width, x1))
        x2 = max(0, min(width, x2))
        y1 = max(0, min(height, y1))
        y2 = max(0, min(height, y2))
        if x2 > x1 and y2 > y1:
            box = (x1, y1, x2, y2)
            img.paste(original.crop(box), box)


def rebuild_pdf(
    input_pdf: str,
    output_pdf: str,
    preview_dir: str,
    dpi: int,
    radius: int,
    erase_rects: dict[int, list[Rect]],
    restore_rects: dict[int, list[Rect]],
    color_clean: bool,
) -> None:
    os.makedirs(preview_dir, exist_ok=True)
    src = fitz.open(input_pdf)
    out = fitz.open()

    for page_number, page in enumerate(src, start=1):
        pix = page.get_pixmap(dpi=dpi, alpha=False)
        original = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        img = original.copy()

        removed = 0
        if color_clean:
            img, removed = clean_colored_marks(img, radius=radius)
        else:
            img = img.convert("RGB")

        apply_restore_rects(img, original, restore_rects.get(page_number, []))
        apply_erase_rects(img, erase_rects.get(page_number, []))

        preview_path = os.path.join(preview_dir, f"page_{page_number:02d}.png")
        img.save(preview_path, "PNG")

        rect = page.rect
        new_page = out.new_page(width=rect.width, height=rect.height)
        pix_clean = fitz.Pixmap(fitz.csRGB, pix.width, pix.height, img.tobytes(), False)
        new_page.insert_image(rect, pixmap=pix_clean)

        erase_count = len(erase_rects.get(page_number, []))
        restore_count = len(restore_rects.get(page_number, []))
        print(
            f"Page {page_number}/{src.page_count}: "
            f"removed {removed} colored pixels, applied {erase_count} erase rectangles, "
            f"restored {restore_count} rectangles"
        )

    out.save(output_pdf, deflate=True, garbage=4)
    out.close()
    src.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Remove red/blue handwriting and targeted black marks from a PDF."
    )
    parser.add_argument("--input", required=True, help="Input PDF path.")
    parser.add_argument("--output", required=True, help="Output cleaned PDF path.")
    parser.add_argument("--dpi", type=int, default=220, help="Render DPI. Default: 220.")
    parser.add_argument("--radius", type=int, default=2, help="Color mask expansion radius.")
    parser.add_argument(
        "--preview-dir",
        default="clean_preview",
        help="Directory for cleaned page PNG previews.",
    )
    parser.add_argument(
        "--erase-json",
        help="JSON mapping 1-based page numbers to pixel-space erase rectangles.",
    )
    parser.add_argument(
        "--restore-json",
        help=(
            "JSON mapping 1-based page numbers to pixel-space rectangles copied "
            "back from the original render after cleanup."
        ),
    )
    parser.add_argument(
        "--no-color-clean",
        action="store_true",
        help="Skip automatic red/blue cleanup and only apply erase rectangles.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    erase_rects = load_erase_rects(args.erase_json)
    restore_rects = load_restore_rects(args.restore_json)
    rebuild_pdf(
        input_pdf=args.input,
        output_pdf=args.output,
        preview_dir=args.preview_dir,
        dpi=args.dpi,
        radius=args.radius,
        erase_rects=erase_rects,
        restore_rects=restore_rects,
        color_clean=not args.no_color_clean,
    )
    print(f"Saved: {args.output}")
    print(f"Preview images: {args.preview_dir}")


if __name__ == "__main__":
    main()
