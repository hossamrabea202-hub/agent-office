# Ground kit: seamless 2 m tiles (Cobble, Mud, GrassDirt, Corrupt)

Made 2026-10-30 by `hossam gmail laptop2 (Claude)` to the knowledge-base standard. Original, procedural, no scans: a
periodic heightfield (1024² high poly) baked onto a flat tile, colour from seamless 4D-torus noise. Each set:
`T_Ground_<Set>_BaseColor` (sRGB), `_ORM` (AO / Roughness / Metallic 0), `_Normal_DirectX`, `_Height` (16-bit, for
layer blending and displacement); `Corrupt` also has `_Emissive` (the glowing fissures and veins). 2K, tiles every 2 m.

| Set | What | Where |
|---|---|---|
| **Cobble** | River cobbles in packed earth, worn tops, moss and puddles in the joints | Castle courtyard, the road through the gate, around the well |
| **Mud** | Trodden mud with a winding pair of cart ruts, boot prints, standing water in the low spots | Outside the gate, the barracks yard, along the border walls |
| **GrassDirt** | Worn meadow: grass patches (short; real grass is the foliage), bare paths, pebbles | Fields outside the castle, under the flora kit |
| **Corrupt** (realm) | Dead crust with crack network, raised flesh veins, blisters; cracks and veins glow | Inside the #29 east gate (the tentacle realm), under the realm flora |

## Unreal

`py "<repo>/assets/laptop2/GroundKit/import_ground_ue.py"` → `/Game/CastleDefender/Environment/Ground/<Set>/` with
`M_LP2Ground` (world-aligned UVs, `TilingMetres` 2, `WetnessBoost`, `EmissiveBoost`, `HeightScale`) and `MI_Ground_<Set>`.
Landscape: one layer per MI, blend by height (`_Height`) so cobbles poke through the mud. Break the tiling at distance
with a macro variation (the master's noise slot is left for it) and the decals (next kit).
