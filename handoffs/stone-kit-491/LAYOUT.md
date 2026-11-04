# #491 layout: walls -> kit placements (i5 core, 2026-11-04)

`python layout_kit491.py` (plain Python 3, 2 s) reads `curtain_specs.json`, `keep_specs.json`, `mason2_specs.json` and writes
`layout/<specs>_layout.json` plus `layout/report.json`. `layout_preview.py` draws one wall's face as an elevation
(`layout/preview_WallSouthL_outer.png`: grey = kit stones, brown = corner stones).

## JSON, per wall (`walls[]`)
- `name`, `size_cm`: the spec box (same name as the mesh it replaces).
- `blocks[]`: `kit` (`SM_Kit_H<cm>_L<cm>_V<1|2>`), `role` (`face` or `quoin` = corner stone, the same kit block), `face` (`-y +y -x +x`),
  `c` centre in metres, **wall-local, UE axes, origin = the box pivot (its centre)**, `yaw` (deg, 0 = length along +x, +180 when
  `flip`), `scale` [along, depth, height], `len_m` / `h_m` / `d_m` = the placed size.
- `special[]`: what the kit can't do; the old mesh or another part stays. Roles: `cap` (walk / top inside the faces, 0.2 m),
  `soffit` (under a lintel), `closer` (cut stone shorter than the kit), `single`, `thin`, `pier`, `slab`, `trim` (not coursed wall).
- `unfit[]`: notes. `overlaps`: block pairs that intersect (shrunk by 2 mm).

## Result
| Specs | Walls | Kit blocks | Special | Worst scale | Unfit | Overlaps |
|---|---|---|---|---|---|---|
| curtain | 25 | 6,653 | 25 (24 caps) | 7.9 % | 0 | 0 |
| keep | 109 | 673 | 122 | 8.0 % | 4 (40 cm walls as through-stones, depth scale 5 %) | 0 |
| mason2 | 49 | 3,252 | 49 | 8.0 % | 0 | 0 |

40 kit names in use (4 heights x 5 lengths x 2 variants); counts per name in `report.json`, so TGA_PC can model the most used first.

## Decisions (tell i5 if you want otherwise)
- **Kit length 0.85 m added** to the 4 in README. Walls 1.6 m thick have 0.84 m ends between the two skins; with only 0.45/0.60/0.75/0.95
  they need 9.1 % scale (48 courses). With 0.85: 0 unfit. Run `KIT_L=0.45,0.60,0.75,0.95 python layout_kit491.py` for the 4-length set.
- **No separate quoin mesh needed:** every kit stone is a closed block, so its end face is finished. Corner stones are ordinary kit
  blocks marked `role: quoin`.
- Each course is filled from kit lengths and scaled once (max 8 %) to close the span, instead of random lengths snapped to the kit.
  Vertical joints keep 0.1 m off the joints of the course below where possible.
- Randomness is seeded by the spec seed but is not gen_boxmason's own sequence (its draws depend on its geometry and on
  `texrects.json`, which is only on i9's PC), so stones won't match today's meshes one for one.
- Boxes that are not coursed wall (trim, string courses, thin skins, single carved stones) are `special`, never forced into kit blocks.

## Not done / not checked
- Copings and the parapet: the curtain specs have no coping, and the #488 merlon kit covers the parapet. Ask i9 where one ends and the
  other starts.
- Nothing in UE. The HISM spawner is i9's (README). Wall-local to world = the replaced mesh actor's transform.
