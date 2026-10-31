# #337 blood splat decals (part 1 of the blood rebuild)

By `adjustedfilm (Claude)`, 2026-10-31. These are procedural (`source/make_splats.py`), built by the rules in
`handoffs/gore-337/RESEARCH.md`. No licensed content.

## The 8 splats (4 × 2 atlas, one splat = 40 cm)

| Index | Shape |
|---|---|
| 0 | vertical drop pool with a crown |
| 1 | small drop |
| 2 | 30° impact |
| 3 | 50° impact: exclamation tail and tadpoles |
| 4 | cast-off line from a swung blade |
| 5 | drip trail from a walking wound |
| 6 | merged pool |
| 7 | slash spray fan |

**Shapes:** distance fields with domain warp, tapered spines, satellites with a tail on the leading side, and log-normal
fine mist. This replaces the first round's round blobs and bead chains, which looked cartoonish.

**Colour and finish:**
- Wet: thick core 60,18,12 sRGB and thin-film edges 110,20,14, with a darker dried rim. The core sits at 60 instead of
  the measured 50 because of the KB floor of 30 luminance; pbr_check gives p50 32.
- Dry 0 → 1 over 30 s:
  - roughness 0.08 → 0.7;
  - colour towards 45,30,20;
  - flatter normal.
- Specular 0.28 (blood IOR 1.35), never emissive.

Note on pbr_check: it measures every texel, including the transparent background (core colour). So its "roughness flat"
flag is about the empty area. The roughness lives in the material: thickness and drying.

**Lookdev** (`renders/`): ground, a 0.18 grey ball, a 1800 K torch key, a cool moon rim, and locked exposure (AgX, 0 EV).
- `lookdev_dry0.jpg`: fresh. Dark and wet with sharp highlights.
- `lookdev_dry1.jpg`: after 30 s. Dark brown and matte.

## Editor (Master, when the gore hand-off comes)

`py "<repo>/assets/adjustedfilm/Blood337/import_blood337_ue.py" --dry-run`, then run it without `--dry-run`. It makes the
3 textures, `M_BloodDecal_337` (deferred decal, Translucent, so DBuffer is not needed) and `MI_BloodDecal_337`. Nothing
live is touched. The gore Blueprint (part 2, after the BP_Zombie export) spawns 1–3 of these per hit, with
Index / Dry / Fade set per decal and a world cap of 48.

Rules applied (INDUSTRY_SECRETS): §0 rule 1 (calibrated values), §1 (measured blood optics), §3.5 (gore without C++),
§4 (VFX: lit, wet, no glow). KB: lookdev with locked exposure, real light behind every highlight.
