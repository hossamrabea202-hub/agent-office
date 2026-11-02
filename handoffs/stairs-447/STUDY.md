# Stairs study (card #447 and the stair rebuild), i5, 2026-11-02

Read-only study of `ThirdPersonMap` on i5, after sync zips b–h. Nothing was saved. Raw data lives in
`C:\Users\hossam.rabea\ckw\stairs\` on i5:
- `castle_pieces.json`: every castle stone piece, with world transform
- `flights.json`: every flight with its pieces
- `refs.json`: material parameters
- `refs/*.fbx`: the building-block meshes

## How the stairs are built today

Every stair is a **pile of separate boxes**, about 794 actors for 19 flights:

| Piece | Mesh (size in cm) | Material | Count |
|---|---|---|---|
| Tread block | `SM_StairTread` 32.3 × 230 × 20.2, bevel ≈ 0.5 cm, 176 tris | `MI_Castle_StoneWall_World` | 199 |
| Tread cap ("coating") | `Cube` scaled to a **1 cm plate** on top of each tread | `MI_Castle_StepCap` (limewash 0) | 304 |
| Body / support blocks | `SM_Cube_Nanite` / `Cube` (no bevel, 100 cm cube scaled) | `MI_Castle_StoneWall_World` | ~150 |
| Side stepping blocks | `SM_StoneModule` 100 cm, bevel ≈ 0.2 cm | `MI_Castle_Trim_World` | ~40 |
| Landings | `SM_WalkSlab` 200 × 500 × 32, `Cube` | `MI_Castle_WalkFlag_World` | ~50 |
| Walking collision | invisible `Collision/StairRamps` ramps | BasicShapeMaterial | 9 |

Problems a single asset fixes:
- Z-fighting and seams where boxes overlap.
- The 1 cm cap plates float.
- Body cubes have no bevel at all.
- The `SM_StoneModule` side blocks step beside the stair. These are the #447 "strange stepped edges".
- About 800 draw calls.
- The limewash and tone break at every box boundary.

All the stone materials are **world-aligned** (`M_Castle_StoneWall_World`, TileSize in cm), so the boxes have no real
UVs.

## The 19 flights (the two Tower9 spiral stairs are already single meshes: `SM_Tower09_Stairs`, 2808 tris)

Rise and run are in cm. "Up" is the direction you climb.

| Flight | Where (world min → max, cm) | Steps | Up | Width | Rise | Run | Pair |
|---|---|---|---|---|---|---|---|
| F2 / F3 | courtyard to wall-walk, (1250,495,0)→(2338,725,680) / y 2775 | 34 | +X | 230 | 20 | 32 | mirror pair (#447 spot) |
| F0 / F1 | west wall-walk, (-35,700,680)→(165,1121,980) / y 2379 | 15 | ±Y | 200 | 20 | 28 | mirror pair |
| F4 / F5 | north/south wall-walk, (1910,-15,680)→(2690,175,1070) / y 3325 | 20 | +X | 190 | 20 | 38 | mirror pair |
| F14 / F15 | east wall-walk, (2985,310,680)→(3175,1090,1070) / y 2410 | 20 | ±Y | 190 | 20 | 38 | mirror pair |
| F17 | (3577,3285,680)→(4357,3475,1070) | 20 | +X | 190 | 20 | 40 | |
| F18 | (4700,295,698)→(4820,895,1051) | 20 | −Y | 120 | 19 | 30 | |
| F10 + F9 + F11 | keep interior, (2400,1380,538)→(2735,2071,1042) | 22 + 6 + 7 | | 120 | 19 | 27 | one dog-leg stair |
| F12 + F13 | keep, (2560,1575,231)→(2832,1842,500) | 8 + 5 | | 100 | 20 | 34 | one dog-leg stair |
| F6 / F8 / F7 | keep shell steps, (2290,1040,26)→(2400,1280,202), y 2190–2460 | 8 / 5 / 3 | | 110 | 25 | 15–30 | small pairs |
| F16 | bailey to keep, (3030,1850,26)→(3230,1970,202) | 8 | −X | 120 | 25 | 26 | |

All are axis-aligned (yaw 0/90/180). The mirrored pairs mean about **11 unique assets** cover all 19 flights.

## Tones to keep (current material values)

- **Treads (`MI_Castle_StepCap`):**
  - Tint 0.66 / 0.58 / 0.48
  - TileSize 140 cm, texture set tinifauaw (2K B/ORM/N)
  - Crack 0.3, no dirt, no moss, limewash 0
- **Bodies (`MI_Castle_StoneWall_World`):**
  - Tint 0.86 / 0.83 / 0.78
  - TileSize 320 cm, texture set vdbhdju
  - Dirt 1, moss 1 (height 650), crack 1, **limewash 0.5**
- **Side trim (`MI_Castle_Trim_World`):**
  - Tint 0.70 / 0.62 / 0.52
  - TileSize 160 cm, texture set tinifauaw
  - Limewash 0 (i9 turned it off in zip h)
- **Landings (`MI_Castle_WalkFlag_World`):**
  - Tint 0.62 / 0.55 / 0.47
  - TileSize 230 cm, limewash 0

## Rebuild plan (AAA hero-asset workflow)

1. **Blockout from data.** A Blender script builds each flight from `flights.json`: exact tread top heights, nosing
   line, width, run, side wall and landing. It sits on the same world transform, so the existing grime and contact decals
   and the invisible StairRamps collision still line up.
2. **High poly (Blender).** Real masonry, not boxes:
   - one stone per tread, slightly irregular lengths, 3–6 mm mortar joints
   - 1.5–3 cm chamfered edges and a rounded, worn nosing, with a foot-wear dip in the middle third of each tread
   - chips on outside corners
   - a stringer wall built from coursed ashlar blocks, so the #447 stepped side blocks are gone
   - procedural noise kept under the Nyquist limit (KNOWLEDGE_LOG 10-30)
3. **Low poly.** One watertight, closed manifold per flight: treads, risers, sides and the underside closed (Lumen-safe,
   walls ≥ 10 cm). About 0.5–2k tris per flight, chamfers kept only on the nosing silhouette. Two material slots:
   tread tops, everything else.
4. **UVs.** UV0 unique at ~512 px/m (2K, or 4K for the 34-step flight). UV1 for the lightmap.
5. **Bake.** High → low, cage, 16-bit normal (MikkTSpace), AO, curvature, plus an ID mask (tread / riser / side / wear
   path). Reuse the office bake runner hygiene: delete the raw EXRs after `finish`.
6. **Material.** A **new** `M_Castle_StairBaked`, so live materials stay untouched (decal rule):
   - the same world-aligned stone textures and the same tints as above, with the tread tone on slot 0 and body tone + limewash on slot 1
   - the baked normal blended over the world normal (RNM)
   - AO for cavities, curvature for edge wear and the polish on the worn path
   - `pbr_check.py` before hand-off
7. **UE import and swap.** New assets go in `/Game/CastleDefender/Environment/Castle/StairsBaked/`.
   `place_stairs447_ue.py` has `--dry-run` / `--apply` / `--revert`:
   - spawns each new flight at its transform
   - **hides** the old pieces into a `Stairs_Old_447` folder, without deleting them
   - keeps the StairRamps collision

   i9 saves the map.
8. **Check.** Lookdev before/after shots at 960×540 below the clouds (i5 GPU rule), then a Play test on the Master.

**Pilot: F2/F3**, the courtyard 34-step pair where #447 was reported. After the owner's OK, roll out to the other 9
assets.
