---
name: build-codex-task-pet
description: Create, repair, validate, package, and install custom Codex task pets from character references or generated raster artwork. Use when a user asks to make a Codex desktop/task pet, convert character art into the v2 8x11 animation atlas, generate task-state animations and 16 mouse-look directions, diagnose sprite problems, or install a pet under CODEX_HOME/pets.
---

# Build Codex Task Pet

Create a reproducible pet project. Preserve source references separately from distributable output and never imply that image generation resolves third-party character rights.

## Workflow

1. Confirm the character, visual reference priority, intended use, pet id, and output directory.
2. Read `references/atlas-contract.md` before generating or assembling frames.
3. Use the `imagegen` skill for raster generation or editing. Prefer compact reference sheets and chroma-key green when transparent generation is unreliable.
4. Generate one animation row at a time. Keep framing, scale, costume, palette, lighting, and ground contact stable.
5. Extract cells, remove chroma key, suppress green spill, and assemble the atlas.
6. Build all 16 look directions clockwise. Treat 000/up, 090/right, 180/down, and 270/left as hard semantic gates.
7. Run three isolated blind direction reviews. Repair any failed cardinal direction; retain intermediate ambiguity only as an explicit review warning.
8. Run `scripts/validate_pet.py <pet-folder>` and inspect a labeled contact sheet visually.
9. Install only after validation by copying `pet.json` and `spritesheet.webp` to `${CODEX_HOME:-~/.codex}/pets/<id>/`.
10. For public distribution, keep third-party source references out of the repository, add an asset-rights notice, and distinguish the code license from artwork permissions.

## Required states

Use rows 0 through 8 for idle, running-right, running-left, waving, jumping, failed, waiting-for-input, running-task, and reviewing-result. Use rows 9 and 10 for 16 clockwise look directions. Empty unused standard-state cells must remain transparent.

## Acceptance gates

- Require a 1536x2288 RGBA WebP atlas arranged as 8 columns by 11 rows.
- Require `spriteVersionNumber: 2` and `spritesheetPath: spritesheet.webp`.
- Reject opaque backgrounds, chroma-key residue, clipped silhouettes, missing used cells, or reversed cardinal directions.
- Record continuity and intermediate-direction issues as warnings when cardinals and package structure pass.
- Compare installed and packaged sprite hashes after copying.

## Resources

- Read `references/atlas-contract.md` for exact row and direction mappings.
- Run `scripts/validate_pet.py` for deterministic package checks. It requires Pillow.
