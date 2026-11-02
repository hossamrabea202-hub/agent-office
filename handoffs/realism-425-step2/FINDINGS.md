# #425 step 2 (wood / stone / grass): audit + findings (i5 / adjustedfilm, 2026-11-02 14:10)

Read-only so far: nothing in the game was changed for step 2. Tools: `audit_mats_ue.py` → `audit.txt` (every
material on level meshes, grouped by surface, with use counts, textures and params), `export_tex_ue.py` (TGA export
for `tools/laptop2/pbr_check.py`).

## What the castle is made of (by use count)
| Surface | Material | Meshes using it |
|---|---|---|
| Castle stone | `MI_Castle_StoneWall_World` (Megascans Stone_Wall_vdbhdju 2K, world-Z moss/dirt) | **884** |
| Trim / step caps / walk flags | `MI_Castle_Trim_World`, `_StepCap`, `_WalkFlag_World` (same parent) | 329 + 304 + 205 |
| Courtyard paving | `MI_Castle_Paving_POM` | 139 |
| Rocks | `MI_Rock_01..08` (M_Master_Rock) | ~170 |
| Castle wood | `MI_Castle_Planks_World` (keep door, keep floors), `M_Castle_WorldWood`, `M_Castle_LocalWood`, `M_GateWood_Scratched` | ~10 |
| Grass | `MTL_MWAM_PlantsGrass` (meadow cover) | 8 actors (instanced) |

## Findings
1. **Castle stone, roughness is flat** (pbr_check: rough p5/p95 0.69/0.82, std 0.041). INDUSTRY_SECRETS rule 2:
   roughness carries the realism and is never flat. Albedo is fine (non-metal p5/p50/p95 = 68/126/162 sRGB; the MI tint
   (0.86, 0.83, 0.78) lowers it a little, still in the 30-240 range).
   **Proposal:** a new material copy `M_Castle_StoneWall_World_R` + MI with a roughness breakup: Composite Texture
   (§1.3) plus a large-scale world-space noise (0.55-0.9) and lower roughness in the mortar/cavities only where the
   world-Z dirt band is wet. Lookdev before/after on the grey-ball wall, then swap by script after the owner's OK.
   Note the decal rule: decals sit on this material, so the swap also needs a side-by-side check with a decal.
2. **Rule 4, castles were limewashed.** The castle is bare grey stone. A limewash variant (albedo 0.40-0.45, never
   white, weathered off at the base and under the drips) is the single biggest "real castle" change. **Owner decision**:
   look change on 884+ meshes. Can be an MI parameter set on the copy above (LimewashAmount).
3. **Keep planks use 8K textures** (`Wooden_Planks_vcznah3g/Raw/T_vcznah3g_8K_B/N/ORM`, ~240 MB on disk, ~250 MB GPU)
   for 3 meshes. Capping those 3 textures at 2048 (Maximum Texture Size, like the #267 cut) saves ~200 MB GPU with no
   visible loss at game distance. Low risk, reversible; proposed to i9/Alien with #267.
4. **Grass colour**: the texture is olive-yellow (linear p50 0.16 / 0.16 / 0.03, R = G). Measured grass is greener,
   0.105 / 0.133 / 0.041 (INDUSTRY_SECRETS 1.1). The MI's `MW_BaseColorCorrection` (0.11, 0.15, 0.03) may already
   correct it: needs a locked-exposure render of the meadow before deciding (next session).
5. **Tower9 rain-streak decals** (`Tower9_Decal_A_Streak_*`, `MI_Decal_RainStreakB`) read as solid black bars next to
   the Tower9 torches (shot `../contact-decals-425/cd425_36_nocards.png`). Real streaks are faint and lighter at the
   ends (Lagarde: "the exception"). Owner of Tower9: lower opacity / shorten. Not changed here (decal rule).

## Next (step 2 build, best in a fresh session; i5 editor needs memory)
- Grass render (locked exposure) → decide on finding 4.
- `M_Castle_StoneWall_World_R` copy with roughness breakup → lookdev on the grey-ball bay (`../contact-decals-425/lookdev_bay_ue.py`, use a
  NON-world-Z material for judging shape, or move the bay to castle height) → before/after on the card.
- Owner decisions: limewash yes/no (finding 2), 8K planks cap (finding 3).
