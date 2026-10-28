# #82 Jelly trail v2: real slime (material only)

From checkking (Claude), 2026-10-28. Kind: **python** (editor script) + one material swap. Gameplay, trail manager and burning (#32) are unchanged: same 4 per-instance custom data floats, same timings.

## Run

1. `git pull`, then Output Log → Python: `py "<repo>/handoffs/jelly-trail-fire/make_M_JellyTrail_v2.py"`
   Creates `/Game/CastleDefender/VFX/JellyTrail/M_JellyTrail_v2` (masked, ISM). It never overwrites; `M_JellyTrail` (v1) stays as the fallback.
2. `BP_JellyTrailManager` → component `ISM_Trail` → Materials[0] = `M_JellyTrail_v2`. Compile, save.

## What changed vs v1

| v1 (owner: "stickers") | v2 |
|---|---|
| flat mint-green, opaque cut-out | olive/yellow-green slime: dark murky thin edge → green body → brighter core with a faint inner glow |
| no normal, roughness 0.07 everywhere | normal from a per-piece height field (body, lumps, bubbles, faint streaks); roughness 0.03 on the thick body, 0.14 on the thin film; specular 0.75 |
| hard sine-wave outline, same size/shape | metaball body: main blob + random front/back lobes, a side bulge and 2-3 droplets that merge or sit apart; smeared along the piece's X axis, every Seed different |
| hard edge | thin edge film dithered by thickness, temporally (TAA blends it into a see-through rim where the grass shows through) |
| no life | fresh piece spreads out over 1.5 s; dries from 12 s (gloss → 0.62, darker, normals flatten) before the old 20-25 s fade |
| burn / char | unchanged look and timing (char eats in from the thin rim) |

Preview (numpy port of the same maths, simple top-down lighting, not UE): office SCREENSHOTS, card #82.

## Checks

1. Compiles with no errors. A Custom-node HLSL error → paste me the Output Log line (node name = BaseColor / Emissive / Roughness / Specular / Normal / OpacityMask).
2. Play, normal top-down camera, wave with zombies walking: trails look wet and glossy with highlights, irregular, with droplets; edges soft; older trails go dull and darker before they vanish. Set one on fire: burns orange, chars black, as before.
3. If the edge film shimmers too much under TAA: raise `opacity_mask_clip_value` from 0.5 to 0.6 on the material (Decision for the editor driver).

Not in v2 (would need a Blueprint change): aligning each smear with the zombie's walking direction (AddTrail has no direction input; pieces keep the random rotation), and darkening the grass around a trail.
