# Yellow Eagle Knight: Greaves L + R (#367), v1

Made by TGA (Claude) on 2026-11-01 from Codex sheet 11 (`handoffs/knight-set-yellow/sheets/11_Greaves.jpg`). Original and procedural.
- **Rebuild:** `tools/tga/knightset/build_greaves.py`, then `tex_gauntlets.py` with `PIECE=Greaves`, then `lookdev_gauntlets.py` with `PIECE=Greaves`.
- **One recipe for the whole set:** the texture and lookdev scripts are shared by every piece. The gauntlets' steel, brass and leather recipe is reused unchanged.

**Status: fitted to the knight on 2026-11-01** (`fbx_knight/`, see `../README.md`). Not imported yet. `renders/greaves_vs_sheet.jpg` shows the sheet above the model.

## What it is
- **Built to the sheet:** 37 cm tall, about 17 / 14 / 10.5 cm across the calf top, mid-calf and ankle. The silhouette is a little slimmer, to match the sheet's views.
- **Shape:**
  - the top cut slopes down from the knee;
  - an arched ankle cut-out at the front, with the ankle flared;
  - the calf bulges at the back.
- **Steel front plate** wrapping round to an **open back**:
  - a centre ridge down the shin;
  - a **knee chevron** with a domed rivet at its point;
  - brass-bound rolled rims on the top, the ankle and both back edges;
  - rows of domed rivets under the top rim, over the ankle, down the back edges and on the side seams.
- **Leather:** a padded liner showing through the open back, and **3 straps with brass buckles** (4 × 3.2 cm, as the sheet).
- **Size:** 17.9k tris per leg at LOD0; LOD1–3 are 9.0k / 4.5k / 2.1k.
- **Right leg:** an exact mirror of the left, sharing its UVs and textures.
- **Textures:** 2K `T_EagleGreaves_BC` / `_ORM` / `_N` (DirectX), the same blackened steel recipe as the gauntlets v2.
  - The mud sits low at the ankle instead of on the fingertips.
  - pbr_check OK: non-metal p50 54 sRGB, metal 17 % of texels (p50 179).

## Frame and fit (next)
- **Canonical LEFT-leg frame:**
  - the bottom of the ankle flare is at the origin;
  - up is +Z;
  - the shin faces −Y;
  - the outer side faces +X;
  - units are metres.
- The fit to `calf_l` / `calf_r` waits on the knight ref-pose dump (#368), the same as the gauntlets.

## Known gaps vs the sheet
- The sheet's plates have a warm bronze wash and etched lines. That's the same open point as the gauntlets: a film tint, for after the owner's look.
- The back liner is lighter than the sheet's dark leather. The sheet's straps also carry punched holes.
