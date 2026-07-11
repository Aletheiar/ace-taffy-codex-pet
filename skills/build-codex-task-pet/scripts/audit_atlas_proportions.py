#!/usr/bin/env python3
"""Measure per-frame scale and coarse body-proportion consistency."""

import argparse
import json
import statistics as stats
from pathlib import Path

from PIL import Image

CELL_W, CELL_H = 192, 208
USED = [7, 8, 8, 4, 5, 8, 6, 6, 6, 8, 8]
NAMES = ["idle", "running-right", "running-left", "waving", "jumping", "failed", "waiting", "running-task", "review", "look-a", "look-b"]


def occupied_width(alpha: Image.Image, y0: int, y1: int) -> int:
    box = alpha.crop((0, max(0, y0), CELL_W, min(CELL_H, y1))).getbbox()
    return 0 if box is None else box[2] - box[0]


def frame_metrics(cell: Image.Image, col: int) -> dict:
    alpha = cell.getchannel("A")
    bbox = alpha.getbbox()
    if not bbox:
        return {"column": col, "empty": True}
    left, top, right, bottom = bbox
    height, width = bottom - top, right - left
    # Coarse normalized bands: head/hair, torso/arms, skirt/legs. These are
    # diagnostics, not anatomical segmentation.
    head_w = occupied_width(alpha, top, top + round(height * 0.45))
    torso_w = occupied_width(alpha, top + round(height * 0.40), top + round(height * 0.68))
    lower_w = occupied_width(alpha, top + round(height * 0.62), bottom)
    histogram = alpha.histogram()
    visible = sum(histogram[1:])
    return {
        "column": col,
        "bbox": list(bbox),
        "width": width,
        "height": height,
        "visible_pixels": visible,
        "bottom": bottom,
        "head_band_width": head_w,
        "torso_band_width": torso_w,
        "lower_band_width": lower_w,
        "head_to_height": round(head_w / height, 4),
        "torso_to_height": round(torso_w / height, 4),
        "lower_to_height": round(lower_w / height, 4),
    }


def median(values):
    return round(stats.median(values), 2)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("atlas", type=Path)
    parser.add_argument("--json-out", type=Path, required=True)
    args = parser.parse_args()
    atlas = Image.open(args.atlas).convert("RGBA")
    rows = []
    for row, (name, count) in enumerate(zip(NAMES, USED)):
        frames = []
        for col in range(count):
            box = (col * CELL_W, row * CELL_H, (col + 1) * CELL_W, (row + 1) * CELL_H)
            frames.append(frame_metrics(atlas.crop(box), col))
        summary = {}
        for key in ("width", "height", "visible_pixels", "bottom", "head_to_height", "torso_to_height", "lower_to_height"):
            values = [f[key] for f in frames]
            summary[f"median_{key}"] = median(values)
            summary[f"range_{key}"] = [min(values), max(values)]
        rows.append({"row": row, "name": name, "summary": summary, "frames": frames})

    idle = rows[0]["summary"]
    warnings = []
    upright_rows = {3, 6, 7, 8, 9, 10}
    for row in rows:
        summary = row["summary"]
        summary["height_vs_idle"] = round(summary["median_height"] / idle["median_height"], 4)
        summary["width_vs_idle"] = round(summary["median_width"] / idle["median_width"], 4)
        summary["area_vs_idle"] = round(summary["median_visible_pixels"] / idle["median_visible_pixels"], 4)
        if row["row"] in upright_rows and not 0.97 <= summary["height_vs_idle"] <= 1.03:
            warnings.append(f"{row['name']} median height differs from idle by more than 3%")
        if max(f["bottom"] for f in row["frames"]) - min(f["bottom"] for f in row["frames"]) > 2:
            warnings.append(f"{row['name']} baseline varies by more than 2 px")

    # Adjacent look directions must not jump sharply in visible area.
    looks = rows[9]["frames"] + rows[10]["frames"]
    transitions = []
    for index, current in enumerate(looks):
        nxt = looks[(index + 1) % len(looks)]
        ratio = round(max(current["visible_pixels"], nxt["visible_pixels"]) / min(current["visible_pixels"], nxt["visible_pixels"]), 4)
        transitions.append({"from": index, "to": (index + 1) % 16, "area_ratio": ratio})
        if ratio > 1.22:
            warnings.append(f"look {index:02d}->{(index + 1) % 16:02d} area ratio {ratio} exceeds 1.22")

    result = {"ok": not warnings, "warnings": warnings, "rows": rows, "look_transitions": transitions}
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": result["ok"], "warnings": warnings}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
