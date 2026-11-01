# #390 WinterKeep: a new 2 × 2 km winter map (hand-off)

By `adjustedfilm (Claude)`. Start with [DESIGN.md](DESIGN.md) (one page and the map), then [RESEARCH.md](RESEARCH.md).
This is a **new level only**. ThirdPersonMap, the bubble, decals and live materials are not touched. Everything new is
under `/Game/CastleDefender/WinterKeep/` and `/Game/CastleDefender/Maps/WinterKeep`.

Script: `S = <repo>/handoffs/winter-map/ue/winterkeep_ue.py`. Each run writes `ue/wk390_log.txt`; push it back.

## Steps (Master)

1. `git pull`. Then `py S --dry-run`. Every line should say `OK`. Push `wk390_log.txt` if anything says `MISS`.
2. `py S --list`. This is read-only and lists the conifers, birches, rocks and shrubs in the project used for dressing.
3. `py S --step assets`. It builds:
   - T_WK_MacroNoise, T_WK_SnowRipple_N and T_WK_DefaultORM
   - **M_WK_Landscape** (8 paint layers)
   - **MF_WK_SnowCover** (top-mask snow plus windward rime, for any prop)
   - **M_WK_SnowProp** and **MI_WK_DriftSnow**
   
   Open M_WK_Landscape once; it must compile with no errors.
4. `py S --step level`. This creates and opens **WinterKeep** (a World Partition level) and removes the template's small
   landscape.
5. **Landscape import. Python can't create a sized landscape in 5.3, so use these clicks.** Landscape mode (Shift+2),
   then **Manage**, then **New**, then **Import from File**:
   1. **Heightmap File:** `<repo>/handoffs/winter-map/terrain/out/WinterKeep_Height_2017.png`
   2. **Material:** `M_WK_Landscape`
   3. **Location:** X **-100800**, Y **-100800**, Z **20200**
   4. **Scale:** X **100**, Y **100**, Z **78.125**
   5. **Section Size** 63×63 quads, **Sections Per Component** 2×2, **Number of Components** 16×16. Overall resolution
      must read **2017 × 2017**.
   6. **Layers list (8 rows).** For each row:
      - click the **+** icon, then **Weight-Blended Layer (normal)**, then save it in `/Game/CastleDefender/WinterKeep/Layers`;
      - then pick its file `terrain/out/WL_<LayerName>.png`.
      
      The rows are Snow_Fresh, Snow_Packed, Rock_Scoured, Ice, FrozenMud, ForestFloor, Road, RealmMelt.
   7. Click **Import**. Then save with **File, Save All**.
6. `py S --step check`. It verifies location and scale (it fixes them if they're off) and the material, and prints spot
   heights. **Expected:** castle about 6200, lake about 365, bridge about 5250 cm.
7. `py S --step dress --dry-run`. Check the counts and the chosen meshes. Then run `py S --step dress`.
   - It makes one HISM actor per 256 m World Partition cell.
   - Expect about 13.6k spruce, 2.4k young spruce, 1.0k birch, 6.1k rocks, 1.6k dead shrubs and 600 drift mounds.
8. `py S --step light --preset overcast`. Other presets: `lowsun`, `blizzard`, `night`. Each one sets the sun, sky,
   fog and an unbound post process with **locked exposure** (Histogram, Min EV100 = Max EV100):

   | Preset | EV100 | Sun |
   |---|---|---|
   | overcast | 12 | 15k lux, 6500 K, soft |
   | lowsun | 14.5 | 100k lux, 9°, 3600 K |
   | blizzard | 11 | fog 0.22 |
   | night | −2.5 | moon 0.26 lux, 4000 K |

9. Screenshots from the **first view**: the wall-walk over the gate, looking SE to the bridge. Take one per preset and
   post them with `shot.js --card 390`.

**Undo:** `py S --step remove` deletes only the actors tagged WK390 in WinterKeep. The level itself is new, so deleting
it removes everything.

## Tests

1. The landscape is 2017², and the gate road and river match the design map. There are no seams or clipped peaks.
2. Snow is never pure white. Under the overcast preset, compare snow on the grey ball: snow should be about 4.5× the 0.18
   ball, not clipped.
3. The NW faces of the ridge are dark rock. The SE lee sides are smooth and drifted.
4. Lake ice is dark and glossy. The realm ring is black and wet with no snow.
5. Trees and rocks sit on the ground, with no floating instances. Nothing grows on the road, the river, the lake or the
   realm.
6. FPS from the wall-walk is about the same as in ThirdPersonMap (see the budget below).

## Performance budget (World Partition)

- **WP grid:** 256 m cells, loading range 768 m (World Settings, then Runtime Partitions).
- **HLOD:** one HLOD layer, Instanced, for the trees and rocks. Build it with **Build, then Build HLODs** after step 7.
- **Culls:**

  | What | Fade starts | Gone at | Shadows |
  |---|---|---|---|
  | spruce | 250 m | 600 m | yes |
  | birch | 150 m | 400 m | yes |
  | big rocks | 300 m | 800 m | yes |
  | small rocks | 60 m | 120 m | no |
  | shrubs | 40 m | 90 m | no |
  | drift mounds | 200 m | 500 m | yes |

- **Collision:** only spruces and big rocks have it.
- **Frame budget (target 60 fps):**

  | Area | Budget |
  |---|---|
  | GPU total | 16.6 ms |
  | Lumen | 4 ms |
  | VSM shadows | 2.5 ms (trees: use the WPO disable distance and Shadow Cache Invalidation = Rigid, INDUSTRY_SECRETS §4.4) |
  | base pass | 4 ms |
  | fog and volumetrics | 1.5 ms |
  | post | 1.5 ms |

  If shadows go over budget, first drop spruce shadows beyond 300 m.

## Not done yet (next session, in this order)

1. **Footprints and tracks:** a player-centred render-target trail mask plus POM in M_WK_Landscape (decision in
   RESEARCH.md §4). Writing it needs a small Blueprint (BPC_SnowTrails).
2. **Blowing-snow VFX:** Python can't author Niagara. Duplicate the rain Niagara from the weather system (#226), make it
   snow, and add ground drift. Exact steps will follow.
3. **Missing winter assets:**
   - snow-loaded spruce
   - icicles
   - the frozen-waterfall mesh
   - the bridge
   - farmsteads
   
   The owner said all of this is my job, so I'll model them in Blender or use project kits. The dressing runs with
   whatever `--list` finds until then.
4. Rime and SSS sparkle tests in lookdev (marked [UNVERIFIED] in RESEARCH.md).

## Files

| Path | What |
|---|---|
| `terrain/gen_terrain.py` | builds the heightmap, 8 weight maps, masks and layout.json (seed 390, about 70 s) |
| `terrain/gen_scatter.py` | builds the dressing (`scatter.json`, by rules, per cell) and 3 small textures |
| `terrain/out/WinterKeep_Height_2017.png` / `.r16` | the 16-bit heightmap |
| `terrain/out/WL_*.png` | 8 weight maps (8-bit, sum 255) |
| `terrain/out/M_*.png` | dressing masks |
| `ue/winterkeep_ue.py` | the editor script (UE 5.3) |
| `lookdev/render_winterkeep.py` | Blender lookdev: `--preset overcast\|lowsun\|blizzard\|night --shot aerial\|gate\|top\|lake` |
| `design/design_map.py` | the design map (sight lines computed from the terrain) |

**pbr_check:** the only textures are a linear macro mask, a normal map and a 4×4 ORM default. There's no BaseColor
texture: all albedo and roughness values are calibrated constants in the material (RESEARCH.md), so `pbr_check` has
nothing to check.

**Rules applied (INDUSTRY_SECRETS §0):**
- 1: calibrated values and locked exposure.
- 2: roughness differs per layer.
- 3: every layer has a physical cause (wind, slope, water).
- 4: the stand-in castle is limewashed.
- 10: one wind drives drifts, rime and ripples.
