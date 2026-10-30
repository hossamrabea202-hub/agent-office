# Decal kit: blood, mud, moss, scorch, crack (10 decals, 1K)

Made 2026-10-30 by `hossam gmail laptop2 (Claude)`. Original, generated (numpy). Each decal: `T_Decal_<Name>_BaseColor`
(alpha = opacity), `_ORM`, `_Normal_DirectX`. Knowledge-base standard: blood is deep red drying to brown with a glossy
wet centre (never black), mud 60–90 sRGB with matte dry rims and a gloss core, moss in clumps, scorch from soot to a tan
heat ring, the crack dark inside with a lip of displaced earth.

| Decal | Use | Size |
|---|---|---|
| BloodSplatA / B | under kills (BP: spawn at death, random yaw, fade 90 s); B is the older, drier one | 0.8–1.5 m |
| BloodDrips | on walls and the gate behind kills (drips run −Y = down: rotate the decal so its Y points down the wall) | 1 m |
| MudSplashA / B | road edges, the gate approach, barracks yard, around the well | 1.5–2.5 m |
| MossPatchA / B | north faces of walls, tower bases, the well stones, under the realm wall | 1–2 m |
| ScorchA | under the campfire, the brazier, burnt-out torches | 1.3 m |
| ScorchFlare | where fire spears / cannon balls land (BP: spawn on impact) | 1 m |
| GroundCrack | across courtyard cobbles and the realm crust (rotate freely, overlap 2–3) | 2–3 m |

## Unreal

`py "<repo>/assets/laptop2/DecalKit/import_decals_ue.py"` → `/Game/CastleDefender/Environment/Decals/<Name>/` with
`M_LP2Decal` (DBuffer colour + normal + roughness; `Opacity`, `Tint`, `NormalStrength`) and `MI_Decal_<Name>`. Place
with DecalActor (size X/Y = the table, Z 50 cm), sort order 1 for moss/mud, 2 for blood/scorch so they sit on top.
