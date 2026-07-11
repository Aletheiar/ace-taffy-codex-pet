#!/usr/bin/env python3
import argparse
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image

EXPECTED_SIZE = (1536, 2288)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a Codex v2 task pet package.")
    parser.add_argument("pet_folder", type=Path)
    args = parser.parse_args()
    folder = args.pet_folder.resolve()
    errors = []

    manifest_path = folder / "pet.json"
    sprite_path = folder / "spritesheet.webp"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        manifest = {}
        errors.append(f"invalid pet.json: {exc}")

    for field in ("id", "displayName", "spriteVersionNumber", "spritesheetPath"):
        if field not in manifest:
            errors.append(f"missing manifest field: {field}")
    if manifest.get("spriteVersionNumber") != 2:
        errors.append("spriteVersionNumber must be 2")
    if manifest.get("spritesheetPath") != "spritesheet.webp":
        errors.append("spritesheetPath must be spritesheet.webp")

    image_info = {}
    try:
        with Image.open(sprite_path) as image:
            image.load()
            image_info = {"format": image.format, "mode": image.mode, "size": image.size}
            if image.format != "WEBP":
                errors.append("spritesheet must be WebP")
            if image.mode != "RGBA":
                errors.append("spritesheet must decode as RGBA")
            if image.size != EXPECTED_SIZE:
                errors.append(f"spritesheet size must be {EXPECTED_SIZE[0]}x{EXPECTED_SIZE[1]}")
            if image.mode == "RGBA" and image.getchannel("A").getextrema()[0] != 0:
                errors.append("spritesheet has no transparent pixels")
    except Exception as exc:
        errors.append(f"invalid spritesheet.webp: {exc}")

    digest = hashlib.sha256(sprite_path.read_bytes()).hexdigest() if sprite_path.is_file() else None
    result = {"ok": not errors, "errors": errors, "manifest": manifest, "image": image_info, "sha256": digest}
    print(json.dumps(result, ensure_ascii=False, indent=2, default=list))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
