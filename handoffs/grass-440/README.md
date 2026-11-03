# #440 Grass fields the AAA way: phase A (i5, 2026-11-03)

Owner (Alien, 12:40): "take the grassfield study and research and use it ... rearrange the scene ... keep an eye for the
roads no grass on them ... correct colors and scale and layout ... AAA methods". Research: `../grass-mountain-research/RESEARCH.md`.

## What was wrong (audit, `analyze_grass.py` on `grass_dump.csv`)
The castle grass is instanced on 3 actors: `Env_GrassTall` (23,095), `Env_BaseRubble` (500 grass + 2,262 rocks) and
2 x `Meadow351` (9,459 grass, 17,199 flowers, 1,614 bushes), 54,129 instances in total.
| Problem | Data |
|---|---|
| grass on roads | all 500 Env_BaseRubble grass clumps on roads; 7,502 Env_GrassTall blades (32 %) on or in the castle zone; Meadow351: 379 grass + 1,321 flowers + 65 bushes |
| too tall | Env_GrassTall p50 76 cm, p90 110 cm; 59 % of all grass is over 60 cm (real meadow 25-45 cm, grazed apron shorter) |
| flowers | 17,199 flowers vs 9,459 grass in Meadow351 (a real meadow is mostly grass) |
| layout | a dense 40 m ring (1.5 / m2), then 0.08 / m2: a hard edge, not a landscape |
| colour | grass MIs: dark olive Base Color Tint (0.27, 0.30, 0.19), colour variation toward rust and **purple-red** |
| ground | base colour of the meadow ground ~35 sRGB (KB: bare soil ~100, grass ~127 sRGB). Not the worn decal (tested). |

## Phase A (this hand-off)
- `relayout.py` -> `plan.csv`: one action per instance (offline, deterministic, seed 440):
  - **roads bare** (GateMudPath, the YW paths, PortalRoads, the gate band). Verges 0-1.5 m keep short trampled grass, 1.5-3 m shorter, no flowers.
  - **courtyard**: packed earth, 10 % short weeds.
  - **worn apron** (`Env_WornGround_Decal`): 70 % kept, 12-25 cm. It is not treated as road; that would have stripped the whole approach.
  - **heights from noise patches**: lush 45-60 / normal 28-42 / thin 15-25 cm. Only Z changes; the clump keeps 80-100 % of its width, so no bare gaps.
  - **altitude bands**: tussock 20-35 cm above 15 m, dwarf 6-14 cm above 50 m.
  - **clumping**: 12 m noise, density 0.55-1.0.
  - **flowers**: only in their species patches, about 1 in 6 kept.
  - Result: 54,129 -> 29,577 instances (cheaper to render).
- New MIs `/Game/CastleDefender/Environment/Foliage/Grass440/MI_vczndjqja_440`, `MI_vlkhcbxia_440`:
  - children of the scan MIs, with a lighter summer tint;
  - variation colours straw / yellow-green / dry olive-brown (no purple);
  - a dry-tip health overlay. Saved on i5; they reach the Master with the session or this zip.
- Before/after (base colour, i5, gate region): `../gpt-review-polish/shots/g440_AB.png` (SCREENSHOTS, card 440).
- **Lesson:** i5's live test was reverted 4 minutes later by a Multi-User rejoin (it reloaded the map packages). Only the Master's save makes this real.

## Apply (i9, Master, Alien not in Play)
1. `git pull`. All files are in `handoffs/grass-440/` (`grass_dump.csv`, `plan.csv`, scripts).
2. `py grass440_ue.py mats`: the 2 new MIs (skip if they came with the session).
3. `py grass440_ue.py apply --dry-run`: expect `skipped_mismatch: 0`.
   - i5 got `remove 24552, scale 22742, keep 3373, comps 87`.
   - If anything is skipped, the Master's grass differs from i5's: run `grass_dump_ue.py` then `relayout.py` on the Master and dry-run again.
4. `py grass440_ue.py apply`: backs up all 87 components to `backup/`. Look from the gate and the wall, then **save the map**.
5. Revert any time before or after saving: `py grass440_ue.py revert`.

Test list:
- the gate road and the yard paths have no grass, and the verges are short;
- the field is patchy: lush patches, thin patches, no even carpet;
- there are no purple clumps;
- frame time is the same or better (24.5k fewer instances).

## Next (phase B, i5)
1. **Ground colour.**
   - The landscape (`M_MountainBackdrop` via `MI_MountainBackdrop_Near`) is driven by the parent `Landscape` actor. Proxies ignore a per-proxy material set from Python.
   - A runtime GrassTint / ForestTint test showed no change on the meadow ground. The ground there is probably the Soil layer (`T_vb2qdgwew`, untinted) or a parameter not exposed.
   - Needs the material graph read (a node export of `M_MountainBackdrop`) and then a new MI on the Landscape actor.
2. **Feather the meadow edge outward:** new tapered grass 55-75 m from the castle (traced placement, as #351) instead of the hard ring.
3. **Grass hue:** the measured tufts are R about equal to G (straw-olive). Living grass has G clearly above R. Adjust the _440 tint after the Master's lit check.
4. **MWAM grass** (`MTL_MWAM_PlantsGrass`, 8 components) still has its old colour.
