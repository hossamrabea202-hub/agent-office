# #488 carved merlon kit, for i9 (i5, 2026-11-04)

Every stone is real geometry, one mesh per module, no bake and no world projection. Each stone face has one joint-free patch of T_vdbhdju on UV0 (32 patches, drawn in `renders/patches_on_scan.png`). Vertex colour: R tone, G damp, B cavity, as M_CastleAshlarWeathered2 expects.
No new textures. Nothing is placed; you place.

## Sizes: what I measured
From the vertices of `SM_CastleStones_1_-1_7`, `_2_0_11` and `_1_1_9` (read-only). They match your deck, sill and top numbers.

| | Today | Kit | Real castles |
|---|---|---|---|
| Pitch (merlon centre to centre) | **240** | 240 | |
| Merlon width | 140 (cap 146) | 140 (coping 150) | 150-200, so narrow; kept |
| Crenel gap | 100 | 100 | 50-100 |
| Sill above deck (z 680) | 75, flat | 75 on the walk side, 69 on the outer side | |
| Top above deck | 190, flat cap | 190 at the ridge, about 178 at the eaves | 180-220 |
| Thickness | body 50, parapet below 46, cap 58 | 50, coping 60 | |

**Cover heights, gameplay:** ridge and walk-side sill are unchanged. Two things do change: the outer edge of the sill is 6 cm lower, and the coping edges are about 12 cm lower than today's flat cap. Stone faces also bulge up to about 2 cm.

## Modules (`fbx/`), pivot and triangles
1 unit = 1 cm. Mesh +X runs along the wall, +Y points to the walk, Z is up. Pivot: bottom centre of the outer face, z 0 = deck top.

| Module | Tris | Stones | Bbox x | y | z (y moves about 1 cm between builds) |
|---|---|---|---|---|---|
| SM_Merlon488_A | 52,654 | 25 | ±86 | -5..55 | 0..189.5 |
| SM_Merlon488_B | 50,885 | 18 | ±86 | -5..55 | 0..189.5 |
| SM_Merlon488_C | 53,171 | 25 | ±86 | -5..55 | 0..189.5 |
| SM_Merlon488_D | 52,528 | 23 | ±86 | -5..55 | 0..189.5 |
| SM_CrenelSill488_A | 14,889 | 4 | ±59 | -3.5..52 | 0..75 |
| SM_CrenelSill488_B | 14,848 | 5 | ±59 | -3.5..52 | 0..76 |
| SM_MerlonCorner488 | 71,018 | 25 | -6.5..140 | -5..142 | 0..189.5 |
| SM_InnerParapet488_A | 45,250 | 15 | ±135 | -4..44 | 0..104.5 |
| SM_InnerParapet488_B | 45,819 | 15 | ±135 | -4..44 | 0..104.5 |

The low courses stick out past the body on purpose (merlon base course ±85, second course ±62, sill the inverse), so a row has no straight joint between merlon and sill. These overlaps are planned, so space by the grid below, not by the bbox.

## Placing
**Yaw** (mesh +Y to the walk): outer face south (-Y) 0, north 180, east (+X) 90, west (-X) -90. Scale is always 1.

**Outer row:** put pivot y on your wall's outer face (the parapet sits over the outer half) and z = 680.
- Merlons at `U0 + k*240`, sills at `U0 + 120 + k*240`, along the wall.
- Mix A B C D and sill A B with no pattern. For more variation, a merlon can turn 180 with its pivot moved in by 50. Sills can't: their drip faces outward.
- End a row inside a tower or on a corner. The module ends are mostly mortar, not finished faces.

**Corner:** the pivot is the bottom of the **outer corner**, and the arms run along +X and +Y.
- Yaw: SW corner 0, SE 90, NE 180, NW -90.
- On both arms the first sill centre is 175 from the corner, the next merlon centre 295, then the 240 grid.
- Outer (convex) corners only. There is no inner-corner module.

**Inner parapet** (courtyard edge, 104.5 high, 40 thick): pivot on the courtyard face, +Y to the walk, one every 240 along the wall.
- South wall: yaw 180 at wall outer face + 245 (195 on front and bailey east). North wall is the mirror.
- Courses run ±14 past the module ends so neighbours interlock. The coping meets at ±120.

**If your wall top is below z 680:** the old merlons started at z 680 while the old corbel top was 672.5, and the kit has no footing below the pivot. If you see a gap, tell me the height and I rebuild; a full build takes about a minute.

**Old merlons:** they sit inside the merged `SM_CastleStones_*` meshes with other pieces, including tower-top merlons at z 1070-1260. You can't hide them one by one, so check what else each merged mesh holds first.

## Import
`py import_merlon_kit_ue.py --dry-run`, then `--apply`; undo with `--revert`. It aborts in PIE and creates assets only, in `/Game/CastleDefender/Environment/Castle/Battlements488`.
- 9 Nanite meshes plus `MI_CastleMerlon488`, a plain child of MI_CastleAshlar, so it follows your live stone values.
- Complex-as-simple collision.
- Slots: `MI_CastleMerlon488` and `M_CastleLimeMortar`, found by name. `--apply` stops if the mortar isn't in the project.
- Mortar sits 4 cm behind the stone face. Stone faces hidden behind it are deleted to save triangles, so a module is not watertight; the mortar boxes keep it opaque.

Regenerate with `blender -b --factory-startup -P build_merlon_kit.py -- build`, then `verify` and `render <scan_dir>`. All sizes are in `CFG`. `export_scan_488_ue.py` writes the scan PNGs the render needs.

## Tested
- FBX re-imported in Blender: bboxes and slots right, 100 % of stone UVs inside clean patches, vertex colours present (`kit_verify.json`).
- 6 renders made from the real FBX files (`renders/`), plus the patch sheet.
- `--dry-run` in the i5 editor passes, and the parent MI's BaseColor is T_vdbhdju. The API names `--apply` uses exist in 5.8.

## NOT tested
- **Nothing has been imported into UE.** `--apply` and `--revert` have never run. Check the first bbox it prints against the table: the axis mapping follows TGA_PC's wall export and I haven't tested it myself.
- **Look in UE:** Nanite build, real cost in a row, Lumen and M_CastleAshlarWeathered2 itself. The renders are Blender with a stand-in of that material and of the lime (I picked its colour; `M_CastleLimeMortar` isn't on i5). Judge in your lit A/B, not from these.
- **Collision:** complex-as-simple on Nanite should use the fallback mesh, which may be much coarser. `--apply` prints its tri count. Arrows, nav 8/8 and soldier fit at the crenels are all unchecked, and your old invisible colliders may overlap this.
- **Fit:** your rebuilt walls aren't on i5, and the corner has never been on a real corner.
- **Sharpness:** on i5 T_vdbhdju has max size 1024, so UE shows half the renders' texels (about 2.5 px/cm). Close up it may be softer.
- **Weathering:** moss and dirt in the MI go by world height (moss below z 650, dirt band 150), so they may not reach z 680+. The tops may read cleaner than the walls.

## Review fixes, v2 (2026-11-04, i5 core)
Owner's review: texture stretch on the copings, smeared sides, pillow-like stones, n-gons and overlaps (as on i9's stair curtain).
Measured by `verify` on the FBX files (`kit_verify.json`), before (v1) and after (v2):

| Check, all 9 modules | v1 | v2 |
|---|---|---|
| n-gons, degenerate faces, duplicate faces | 0 | 0 |
| Triangles crossing: inside a stone / stone on stone / next module | 0 / 0 / 0 | 0 / 0 / 0 |
| Texture density, worst 1 % of triangles (px/cm) | 1.84-3.06 | **3.18-3.57** |
| Worst stretch (anisotropy) | 2.8-10.5 | **2.0-8.3**, the 8.3 is a sliver 4 cm deep in a joint |
| Stretch, 99 % of triangles under | 1.32 | 1.33 |
| UVs inside a clean patch of the scan | 100 % | 100 % |

What changed in `build_merlon_kit.py`:
- **Smeared sides:** a bed or joint face whose hidden middle is culled is a ring round the stone. As one chart it spanned the whole stone (up to 27 x 202 cm) and fell to 1.5 px/cm. Rings are now cut into their strips. A chart may also turn 90 degrees to fit a patch. Low-density charts: about 30 to 2, worst 3.1 px/cm.
- **Coping stretch:** the two ridge slopes were separate charts, and the seam on the worn ridge folded the UVs (240x on the inner parapet ridge). Sides meeting at under 50 degrees now share one chart (two planes on a shallow fold flatten with no stretch). Worst there: 240 to 2.0.
- **Pillows:** every stone had the same soft bulge easing in from all edges. Now three dressings, like real ashlar: 55 % flat-dressed with a crisp arris and small bites; 30 % a tooled drafted margin (2-3.5 cm) round a rougher face; 15 % old rock-faced and rounded. The face tilt is a plane, not a cushion.
- `MERLON_DEBUG=1` prints low-density charts (build) and the worst-stretched triangles (verify).

Before / after: `renders/v2/ab_close_outer.png`, `renders/v2/ab_close_walk.png` (left v1, right v2), `renders/v2/*.png`. Blender stand-in material, same light and camera.
Rules applied: realism KB (real carved geometry, no bake, the real scan at a checked texel density). INDUSTRY_SECRETS rule 3 (dirt has a cause: vertex-colour damp rises from the base, cavity sits at edges and joints) and rule 10 (coherence: the MI is a child of the castle's own MI_CastleAshlar, so the kit follows i9's live stone values). **Not done:** rule 1, lookdev under the locked grey ball in UE (i5's 2 GB GPU); judge in i9's lit A/B. Rule 4 (limewash) is i9's call for the whole castle.

**Status:** ready for i9 to import and place, once Alien OKs the look. Same import script, same sizes and pivots as v1.
