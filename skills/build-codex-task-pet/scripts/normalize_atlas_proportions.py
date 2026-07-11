#!/usr/bin/env python3
"""Apply bottom-anchored per-cell scale corrections to a Codex v2 atlas."""

import argparse
from pathlib import Path

from PIL import Image

CELL_W, CELL_H = 192, 208


def resize_cell(cell: Image.Image, target_h=None, x_boost=1.0, uniform_scale=None) -> Image.Image:
    bbox = cell.getchannel("A").getbbox()
    if not bbox:
        return cell.copy()
    subject = cell.crop(bbox)
    if uniform_scale is not None:
        sy = sx = uniform_scale
    else:
        sy = target_h / subject.height
        sx = sy * x_boost
    width = max(1, round(subject.width * sx))
    height = max(1, round(subject.height * sy))
    subject = subject.resize((width, height), Image.Resampling.LANCZOS)
    out = Image.new("RGBA", (CELL_W, CELL_H))
    x = (CELL_W - width) // 2
    bottom = min(CELL_H - 5, bbox[3])
    y = bottom - height
    if x < 0 or y < 0 or x + width > CELL_W or y + height > CELL_H:
        raise ValueError(f"scaled subject does not fit: bbox={bbox}, size={width}x{height}, at={x},{y}")
    out.alpha_composite(subject, (x, y))
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    atlas = Image.open(args.input).convert("RGBA")
    if atlas.size != (1536, 2288):
        raise SystemExit(f"unexpected atlas size: {atlas.size}")
    repaired = atlas.copy()

    # Task-running: slight scale compensation without changing pose semantics.
    for col in range(6):
        box = (col * CELL_W, 7 * CELL_H, (col + 1) * CELL_W, 8 * CELL_H)
        repaired.paste(resize_cell(atlas.crop(box), target_h=198, x_boost=1.04), box[:2])

    # Look rows: normalize full height and add horizontal compensation. The
    # stronger boost on row 10 closes the 157.5 -> 180 and 337.5 -> 000 scale gap.
    for col in range(8):
        box9 = (col * CELL_W, 9 * CELL_H, (col + 1) * CELL_W, 10 * CELL_H)
        box10 = (col * CELL_W, 10 * CELL_H, (col + 1) * CELL_W, 11 * CELL_H)
        repaired.paste(resize_cell(atlas.crop(box9), target_h=198, x_boost=1.06), box9[:2])
        repaired.paste(resize_cell(atlas.crop(box10), target_h=198, x_boost=1.10), box10[:2])

    # Failure frames 4-5 were generated at a noticeably larger character scale.
    for col in (4, 5):
        box = (col * CELL_W, 5 * CELL_H, (col + 1) * CELL_W, 6 * CELL_H)
        repaired.paste(resize_cell(atlas.crop(box), uniform_scale=0.90), box[:2])

    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Clear hidden RGB before encoding so transparent pixels remain deterministic.
    pixels = list(repaired.getdata())
    repaired.putdata([(0, 0, 0, 0) if a == 0 else (r, g, b, a) for r, g, b, a in pixels])
    if args.output.suffix.lower() == ".webp":
        repaired.save(args.output, lossless=True, quality=100, method=6, exact=True)
    else:
        repaired.save(args.output)
    print(args.output.resolve())


if __name__ == "__main__":
    main()
