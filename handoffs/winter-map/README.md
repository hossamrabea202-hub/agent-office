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
3b. **NEW (polish v2):** `py S --step meshes`. It imports the 9 winter meshes (`assets/out/fbx`, Nanite on) and 27 textures
   (`assets/out/tex`) to `/Game/CastleDefender/WinterKeep/Meshes` and `/Textures`, and makes 9 `MI_WK_*` instances of
   M_WK_SnowProp (SnowAmount per slot, needles two-sided, ORM gets Composite Texture = its normal map). Every line should
   say `OK`. Then open **SM_WK_Spruce_A** once: snow clumps sit on top of the branches only, needles are dark green.
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
6b. **NEW:** `py S --step props --dry-run`, then `py S --step props`. It places **WK_Bridge** (one 46 m stone arch over the
   gorge, deck 6.5 m at the road height, walkable), **WK_IceFalls** (the frozen waterfall on the 13.6 m rock step) and
   **WK_Farm_East / WK_Farm_Road / WK_Farm_North** (half-buried log farmsteads, drift on the SE lee side). Re-running
   replaces only these actors. `SM_WK_Icicles_3m` is a 3 m eave strip: drag copies onto castle eaves by hand (pivot = eave line).
6c. **NEW (snow trails):** `py S --step trails`, then the BPVar lines and graph paste in **BPC_SnowTrails**. Exact steps
   and tests: [trails/README.md](trails/README.md).
6d. **NEW (snow VFX):** falling snow and ground drift come with steps 3 and 6c. The ridge spindrift needs one Niagara system
   made by clicks, then `py S --step drift`: [vfx/README.md](vfx/README.md).
7. `py S --step dress --dry-run`. Check the counts and the chosen meshes. Then run `py S --step dress`.
   - It makes one HISM actor per 256 m World Partition cell. After `--step meshes` it uses our own SM_WK_Spruce_A/B,
     SM_WK_Birch_A and SM_WK_Rock_A/B (the log says which mesh each kind got).
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

## Tests (polish v2 additions first)

- A1. Bridge: walk across the deck; the road meets both ends with no step. Snow cushions on the parapets, icicles under
  the string course, voussoir blocks proud of the face. Nothing floats; the abutments vanish into the gorge sides.
- A2. Frozen falls: from the river ice below, the curtain has an irregular outline (no square slab), white-blue bubbly
  ice with clear streaks, an ice cone at the foot. No dark gaps between the ice and the rock.
- A3. Farmsteads: snow load on the roof (thin on the NW side, deep with a cornice on the SE side), drift to the eaves on
  the SE side, a dug-out trench to the door, icicles on the NW eave.
- A4. Trees: no square or flat-plate look; snow only on top of branches; WPO is off, shadows Rigid (no VSM cost).
- A5. Snow is never clipped white under the overcast preset (BC p50 230 sRGB = 0.80 linear).


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

## Polish v2 (2026-11-01): real assets instead of stand-ins

Built by `assets/build_wk_assets.py` (Blender 4.5, procedural, seeds fixed): `blender -b --factory-startup -P assets/build_wk_assets.py`.

| Mesh | What | Tris | Slots |
|---|---|---|---|
| SM_WK_Spruce_A / B | snow-loaded Norway spruce, 21 m / 10 m: branch whorls, drooping fronds, hanging branchlets, snow cushions on top of every branch | 63k / 33k | SpruceBark, Needles, Snow |
| SM_WK_Birch_A | bare silver birch 14 m: white bark, dark fissured base, weeping fine twigs, snow lines on limbs | 63k | BirchBark, BirchDark, Snow |
| SM_WK_Rock_A / B | glacial boulders 4.4 m / 1.2 m: fractured planes + modelled snow cap | 7k | Rock, Snow |
| SM_WK_Icicles_3m | eave strip, heavy-tailed lengths, ripple rings | 3k | Ice |
| SM_WK_IceFalls | frozen waterfall 18 m: organ-pipe columns, lip, spray cone, leans up the rock step | 33k | Ice |
| SM_WK_Bridge | 76 m stone bridge, one 46 m arch (14th-c. Céret type), voussoirs, parapets, deck snow with ruts | 28k | Stone, Snow, Ice |
| SM_WK_Farmstead | log house 12 x 7 m, interlocked corners, roof snow load + cornice, drift field, door trench, woodpile, fence | 25k | Wood, Stone, Snow, Ice |

**Textures** (`assets/out/tex`, 1024², BC sRGB / ORM linear / N OpenGL 16-bit): all 9 BC/ORM pairs pass `pbr_check`
(`assets/out/pbr_check.txt`). Albedo: snow 0.80 (p50 230 sRGB), needles p50 55, spruce bark 76, birch 186, stone 116,
logs 98, rock 74. Nothing is 1.0 white, no AO baked into BC.

**Terrain fix:** the old "gorge" under the bridge was the road embankment (a 30 m fill with 1 m walls and 46 m spikes).
`gen_terrain.py` now never fills the gorge (the bridge spans it), despikes the bridge area and lets a short stone
causeway meet the deck. Spot heights: bridge deck 5247 cm (unchanged), river ice under it about 2180 cm.

**Lookdev:** `lookdev/render_winterkeep.py` now uses the real meshes and the exact `scatter.json` instances UE gets,
textured snow with glints (random-facet sparkle), box-projected rock texture, multiple scattering in the blizzard fog,
and 3 new shots: `--shot bridge|farm|falls`. `lookdev/render_assets.py` renders the asset lineup with the grey and chrome
balls. Old shots are in `lookdev/shots/before/`.

## Not done yet (next session, in this order)

1. ~~Footprints and tracks~~ **done 2026-11-01:** [trails/README.md](trails/README.md) (RT mask, own POM, BPC_SnowTrails).
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
