# #461 Castle harmony scan: the Master map, 2026-11-03 16:54 (i5)

Owner (Alien): "all castle walls converted to the AAA method ... a scan for all castle elements to make sure they are in
harmony with each other". The scan is read-only, run by i9 on the Master (`castle_scan_ue.py`). It covers 2,204 actors,
2,471 mesh components and 185 materials. The analysis is `analyze_harmony.py`; full tables are below.

## Verdict
The new pieces are AAA: 9 wall modules, the gate, the keep entrance, the stairs and the keep masonry. Harmony is not
there yet, because **four different stone looks** sit side by side:

| Stone look | Where | Components |
|---|---|---|
| A `M_Castle_StoneWall_World` (old world-space, 5 MIs that disagree) | battlements 131, towers 30, walls 28, gate 20 | 219 |
| B `M_CastleAshlarWeathered2` (2 tints: warm 0.70/0.62/0.52 vs pale 0.86/0.83/0.78) | keep | 137 |
| C `M_KeepEntrance_Baked` (THE AAA family: baked stones + i9's tint x0.62, lime 0, rock detail layer) | 9 wall modules, keep entrance, gate | 11 |
| D `M_Castle_StairBaked` (should be C: see the fix below) | the 9 stair flights | 9 |

Weathering is also done two ways:
- the new modules weather **inside the material** (moss, grime band, cracks, soil);
- Tower9 still wears **387 flat grime cards** (`M_EdgeGrimeCard` 207, `M_WallBaseGrime` 180).

## Harmony plan (one stone family, one look, one weathering logic)
1. **Reference = family C** with i9's values. Every stone surface matches its albedo, tint, moss, grime band, cracks and stone size.
2. **Stairs (bug, i5):** the W2 look does not show on the 9 flights. `stair_baked451_ue.py swap` had written the old MIs as
   per-component overrides, and those win over the mesh slots. Fix: `stair_w2_ue.py mesh --apply` now also sets the
   flights' overrides. i9 re-runs it and saves.
3. **Battlements + old curtain/tower faces (219 components on look A):**
   - Short term: ONE new harmony MI on `M_Castle_StoneWall_World`, matched to C (moss, grime, cracks, dirt band and colour from C's values), swapped onto all A components by script. The 5 disagreeing variants go away.
   - Long term: baked modules per wall run.
4. **Keep (look B):** one tint, measured against the wall modules in a base-colour A/B at the keep/wall junction.
5. **Tower9 grime cards:** remove the 387 cards once Tower9's re-UV with per-stone weathering is in (i9, in progress).
   Cards and in-material weathering on the same tower double up.
6. **Old kit still visible: convert to baked modules.** Split:
   - **TGA_PC** (owns walls/towers the keep way): Bailey + Corner tower drums, the 8 + 8 cornices and their skirts; BaileyNorth curtain + SC + buttress + skirt (skipped: slab 135 cm off its courses); East/North/South string courses incl. the B138 breach `_Mid` pieces.
   - **i5:** keep turret + 6 crenels, keep door, gate landing cap, the 4 Tower9 gate-step cubes, the single courtyard floor slab, the timber drawbridge.
7. **Cleanup:**
   - `Castle_WallWalk_EMPTY` shows **WorldGridMaterial** (SM_Cube_Nanite at the origin): hide it or give it the stone.
   - 188 hidden old components (648k tris) are still loaded: delete them after the owner's OK (backups exist).
8. **Budget:** new maps at 2K max (i9's VRAM rule); baked modules use Tint x0.62 + LimewashAmount 0 (i9's look fix).

---


Source: `castle_scan.json` (2204 actors, 2471 mesh components, 185 materials).

## 1. What is AAA and what is still old kit (visible elements)

| Type | AAA | old kit | flat cards | other | hidden (still loaded) |
|---|---|---|---|---|---|
| battlement | 2 | 6 | 0 | 126 | 41 |
| gate | 1 | 6 | 2 | 37 | 88 |
| tower | 2 | 24 | 395 | 12 | 4 |
| keep | 134 | 3 | 0 | 6 | 0 |
| stairs | 9 | 0 | 2 | 0 | 9 |
| wall | 9 | 24 | 12 | 38 | 46 |
| floor | 0 | 1 | 1 | 9 | 0 |
| roof | 0 | 0 | 0 | 0 | 0 |
| prop | 13 | 134 | 594 | 346 | 335 |

## 2. Visible old kit pieces still in the castle (convert next)

- **tower** `Castle_BaileyTower_Cornice`: 8 pieces (e.g. Castle_BaileyTower_Cornice, SM_Bevel_019)
- **tower** `Castle_CornerTower_Cornice`: 8 pieces (e.g. Castle_CornerTower_Cornice, SM_Bevel_022)
- **battlement** `Castle_KeepTurret_Crenel`: 6 pieces (e.g. Castle_KeepTurret_Crenel5, SM_Bevel_023)
- **wall** `Castle_EastCurtain_StringCourse`: 4 pieces (e.g. Castle_EastCurtain_StringCourse, SM_Bevel_004)
- **wall** `Castle_BaileyNorthCurtain_SC`: 3 pieces (e.g. Castle_BaileyNorthCurtain_SC, SM_Bevel_011)
- **wall** `Castle_NorthCurtain_StringCourse_B138B_Mid`: 3 pieces (e.g. Castle_NorthCurtain_StringCourse_B138B_Mid, SM_Bevel_010)
- **wall** `Castle_SouthCurtain_StringCourse_B138A_Mid`: 3 pieces (e.g. Castle_SouthCurtain_StringCourse_B138A_Mid, SM_Bevel_009)
- **keep** `Castle_KeepTurret`: 2 pieces (e.g. Castle_KeepTurret, SM_Bevel_040)
- **tower** `Castle_BaileyTower`: 2 pieces (e.g. Castle_BaileyTower, SM_Bevel_018)
- **tower** `Castle_BaileyTower_Cornice_Skirt`: 2 pieces (e.g. Castle_BaileyTower_Cornice_Skirt, SM_Bevel_019)
- **tower** `Castle_CornerTower`: 2 pieces (e.g. Castle_CornerTower, SM_Bevel_018)
- **tower** `Castle_CornerTower_Cornice_Skirt`: 2 pieces (e.g. Castle_CornerTower_Cornice_Skirt, SM_Bevel_019)
- **wall** `StoneWallFountain`: 2 pieces (e.g. StoneWallFountain_2, Cylinder)
- **floor** `Castle_CourtyardFloor_Single`: 1 pieces (e.g. Castle_CourtyardFloor_Single, SM_Bevel_001)
- **gate** `Castle_GateLanding_Cap`: 1 pieces (e.g. Castle_GateLanding_Cap, Cube)
- **gate** `Castle_TimberDrawbridge`: 1 pieces (e.g. Castle_TimberDrawbridge, SM_Bevel_036)
- **gate** `Tower9_GateStep_A1_Cube`: 1 pieces (e.g. Tower9_GateStep_A1_Cube, Cube)
- **gate** `Tower9_GateStep_A2_Cube`: 1 pieces (e.g. Tower9_GateStep_A2_Cube, Cube)
- **gate** `Tower9_GateStep_B1_Cube`: 1 pieces (e.g. Tower9_GateStep_B1_Cube, Cube)
- **gate** `Tower9_GateStep_B2_Cube`: 1 pieces (e.g. Tower9_GateStep_B2_Cube, Cube)
- **keep** `Castle_KeepDoor`: 1 pieces (e.g. Castle_KeepDoor, SM_Bevel_046)
- **wall** `Castle_BaileyEastCurtain_B138C_Mid`: 1 pieces (e.g. Castle_BaileyEastCurtain_B138C_Mid, SM_Bevel_002)
- **wall** `Castle_BaileyEast_SC_B138C_Mid_Skirt`: 1 pieces (e.g. Castle_BaileyEast_SC_B138C_Mid_Skirt, SM_Bevel_003)
- **wall** `Castle_BaileyNorthCurtain`: 1 pieces (e.g. Castle_BaileyNorthCurtain, SM_Bevel_008)
- **wall** `Castle_BaileyNorthCurtain_SC_Skirt`: 1 pieces (e.g. Castle_BaileyNorthCurtain_SC_Skirt, SM_Bevel_009)
- **wall** `Castle_Bailey_NorthCurtain_Buttress`: 1 pieces (e.g. Castle_Bailey_NorthCurtain_Buttress, SM_Bevel_013)
- **wall** `Castle_NorthCurtain_B138B_Mid`: 1 pieces (e.g. Castle_NorthCurtain_B138B_Mid, SM_Bevel_008)
- **wall** `Castle_NorthCurtain_StringCourse_B138B_Mid_Skirt`: 1 pieces (e.g. Castle_NorthCurtain_StringCourse_B138B_Mid_Skirt, SM_Bevel_009)
- **wall** `Castle_SouthCurtain_B138A_Mid`: 1 pieces (e.g. Castle_SouthCurtain_B138A_Mid, SM_Bevel_008)
- **wall** `Castle_SouthCurtain_StringCourse_B138A_Mid_Skirt`: 1 pieces (e.g. Castle_SouthCurtain_StringCourse_B138A_Mid_Skirt, SM_Bevel_009)

## 3. Stone material families on visible structure (should be 1-2 families, one look)

| Base material | components | types | example MI |
|---|---|---|---|
| `M_Castle_StoneWall_World` | 219 | battlement 131, tower 30, wall 28, gate 20 | `MI_Castle_StoneWall_World` |
| `M_EdgeGrimeCard` | 209 | tower 207, gate 2 | `MI_EdgeGrime_StairContact` |
| `M_WallBaseGrime` | 182 | tower 180, wall 2 | `M_WallBaseGrime` |
| `M_CastleAshlarWeathered2` | 137 | keep 133, tower 2, battlement 2 | `MI_CastleAshlar` |
| `Iron_Torch___Baked_PBR_1K` | 32 | wall 28, tower 4 | `Iron_Torch___Baked_PBR_1K` |
| `M_KeepEntrance_Baked` | 11 | wall 9, keep 1, gate 1 | `M_KeepEntrance_Baked` |
| `M_CorruptionBubble` | 10 | gate 10 | `MI_CorruptionBubble_Zombie` |
| `M_Castle_StairBaked` | 9 | stairs 9 | `MI_StairBaked451_N13_Tread` |
| `M_Shadow` | 8 | gate 8 | `M_Shadow` |
| `M_AshenGate_Triplanar` | 6 | floor 4, tower 2 | `MI_AshenGate_Iron` |
| `M_AlgaeStain_Card` | 6 | wall 6 | `MI_AlgaeStain_Wall` |
| `M_TorchSoot` | 4 | tower 4 | `M_TorchSoot` |
| `M_TorchMountGrime` | 4 | tower 4 | `M_TorchMountGrime` |
| `M_ArchWeathering` | 3 | wall 2, gate 1 | `MI_ArchWeathering_Wall` |
| `M_FountainWater_SLW` | 3 | floor 3 | `MI_FountainWater_Crown` |
| `M_Castle_Paving_POM` | 2 | gate 1, floor 1 | `MI_Castle_Paving_POM` |
| `M_StoneFountain_AAA` | 2 | wall 2 | `MI_StoneFountain` |
| `M_FaucetStream` | 2 | wall 2 | `M_FaucetStream` |
| `M_BasinWater_SLW` | 2 | wall 2 | `M_BasinWater_SLW` |
| `M_FloorGrimeCard` | 2 | stairs 2 | `M_FloorGrimeCard` |
| `M_FountainCurtain` | 2 | wall 2 | `MI_FountainCurtain_Crown` |
| `WorldGridMaterial` | 1 | battlement 1 | `WorldGridMaterial` |
| `M_GateLever` | 1 | gate 1 | `M_GateLever` |
| `M_Prop_PBR_Detail` | 1 | gate 1 | `MI_GateLever` |
| `M_Drawbridge_Weathered` | 1 | gate 1 | `MI_Drawbridge_Deck` |
| `M_CourtyardFountain_Stone` | 1 | floor 1 | `MI_CourtyardFountain_Base` |
| `M_TreasureGlow` | 1 | floor 1 | `M_TreasureGlow` |

## 4. Same family, different look (tints / limewash / scale that do not match)

- **M_Castle_StoneWall_World** (5 MIs):
  - CrackAmount: 1.0 x3, 0.0 x1, 0.3 x1
  - CrackSize_cm: 900.0 x3, 750.0 x2
  - DirtAmount: 1.0 x4, 0.0 x1
  - DirtBand_cm: 85.0 x3, 150.0 x2
  - GrimeHeight_cm: 260.0 x4, 1.0 x1
  - LimewashAmount: 0.0 x3, 0.5 x2
  - MacroStrength: 0.45 x2, 0.35 x2, 0.25 x1
  - MossAmount: 0.0 x2, 1.0 x2, 0.2 x1
  - MossColor: [0.16, 0.17, 0.12, 1.0] x3, [0.055, 0.075, 0.025, 1.0] x2
  - MossHeight_cm: 420.0 x3, 650.0 x1, 500.0 x1
- **M_EdgeGrimeCard** (2 MIs):
  - Color: [0.05, 0.038, 0.026, 1.0] x1, [0.018, 0.014, 0.01, 1.0] x1
- **M_CastleAshlarWeathered2** (2 MIs):
  - MossHeight_cm: 650.0 x1, 500.0 x1
  - Tint: [0.86, 0.83, 0.78, 1.0] x1, [0.7, 0.62, 0.52, 1.0] x1
- **M_KeepEntrance_Baked** (11 MIs):
  - AntiTile_Amount: 0.85 x10, null x1
  - AntiTile_AvgLum: 0.16 x10, null x1
  - AntiTile_SatHi: 0.62 x10, null x1
  - AntiTile_SatLo: 0.38 x10, null x1
  - CrackAmount: 1.0 x10, null x1
  - CrackSize_cm: 750.0 x10, null x1
  - DetailRough: 0.6 x10, null x1
  - DetailSize_cm: 160.0 x10, null x1
  - DirtAmount: 1.0 x10, null x1
  - DirtBand_cm: 150.0 x10, null x1
- **M_AlgaeStain_Card** (4 MIs):
  - CardSizeCm: [96.0, 50.0, 0.0, 1.0] x1, [200.0, 170.0, 3.0, 1.0] x1, [180.0, 185.0, 21.0, 1.0] x1, [80.0, 180.0, 0.0, 1.0] x1
  - MossTileCm: 40.0 x2, 35.0 x2
  - MossTiling: 2.0 x3, 1.5 x1

## 5. Hidden old pieces still loaded: 188 components, 648348 tris (delete after the owner OK, or keep as backup)

- gate `Castle_GateSpandrel`: 47
- battlement `SM_WalkSlab`: 28
- gate `Castle_GateArch`: 13
- gate `JellyBubble_Gate`: 10
- gate `JellyMine_Gate`: 10
- stairs `StairRamp`: 9
- battlement `Castle_GateLever_NATIVE`: 8
- wall `Castle_SouthCurtain_StringCourse_B138A_R`: 3
- wall `Castle_SouthCurtain_Buttress`: 3
- wall `Castle_FrontRightCurtain_StringCourse`: 3
- wall `Castle_NorthCurtain_StringCourse_B138B_R`: 3
- wall `Castle_NorthCurtain_StringCourse`: 3
- wall `Castle_NorthCurtain_Buttress`: 3
- wall `Castle_SouthCurtain_StringCourse`: 3
- wall `Castle_BaileySouthCurtain_SC`: 3

## 6. Stretched stone (non-uniform scale > 1.6:1 => stones of different size side by side): 381 components

- tower `Tower9_LedgeGrime_B`: 64
- tower `Tower9_LedgeGrime_A`: 64
- battlement `SM_WalkSlab`: 36
- battlement `SM_StoneModule`: 29
- wall `StoneWallFountain`: 10
- wall `Castle_EastCurtain_StringCourse`: 9
- battlement `Castle_KeepTurret_Crenel`: 6
- floor `Castle_Flagpole`: 4
- gate `Castle_GateTowerRight_ArrowSlit`: 4
- gate `Castle_GateTowerLeft_ArrowSlit`: 4
- wall `Castle_BaileyNorthCurtain_SC`: 3
- wall `Castle_NorthCurtain_StringCourse_B138B_Mid`: 3
- wall `Castle_SouthCurtain_StringCourse_B138A_Mid`: 3
- keep `Castle_KeepBridge`: 2
- tower `Castle_CornerTower_Cornice_Skirt`: 2
