# Flora kit: meadow flowers + realm flora + corrupted ground

Made 2026-10-30 by `hossam gmail laptop2 (Claude)` to the knowledge-base standard (`handoffs/knowledge`). Original,
procedural, no third-party assets. Real geometry (no alpha cards), two-sided foliage with subsurface, wind in the
material, 2K bakes from high polys with veins, ruffled edges and serrations.

| Species | Mesh | Tris | Height | What |
|---|---|---|---|---|
| **Daisy** | `SM_Flora_Daisy` | 4.6k | 0.5 m | Oxeye daisy, 3 heads, 44 petals each in two whorls |
| **Poppy** | `SM_Flora_Poppy` | 1.2k | 0.55 m | Red poppy, 2 open heads + 1 bud, crumpled petals |
| **Foxglove** | `SM_Flora_Foxglove` | 1.3k | 1.1 m | Spire of 24 pink bells |
| **Bloodcap** (realm) | `SM_Flora_Bloodcap` | 1.2k | 0.6 m | Fleshy cup flower, veined dark petals round a glowing core |
| **SporeStalk** (realm) | `SM_Flora_SporeStalk` | 1.6k | 1.4 m | Stalk with 9 hanging bioluminescent spore sacs |
| **TentacleFern** (realm) | `SM_Flora_TentacleFern` | 4.7k | 0.7 m | 7 curling fronds, tips glow |
| **CorruptPatch** (realm) | `SM_Flora_CorruptPatch` | 1.3k | 2 m wide | Cracked, veined flesh-earth with glowing fissures and 5 bulbs |
| **BlobMine** (realm) | `SM_Flora_BlobMine` | ~3k | 0.5 m | Bio land mine: membrane sac on a flesh skirt, 4 glowing pustules (the trigger), 6 tendrils. Realm card #154: bursts into blobs when stepped on or shot |
| **EggCluster** (realm) | `SM_Flora_EggCluster` | ~4k | 0.7 m | Nine translucent eggs half sunk in a flesh mound, two hatched. Insect swarm spawner (#156) |

Nature is never only grass: scatter the meadow three by hand or with the foliage tool in the fields outside the castle
(daisy 60 %, poppy 25 %, foxglove 15 %, in clumps of 3 to 9, never a uniform spray). The realm three go inside the
tentacle zone, denser near the tentacles; the patches under them and along the blob paths (sink the patch 2 cm).

## Unreal

`py "<repo>/assets/laptop2/FloraKit/import_flora_ue.py" [Daisy ...]` → `/Game/CastleDefender/Environment/Flora/<Species>/`
with `M_LP2Foliage` (Two Sided Foliage: subsurface from BaseColor × `SubsurfaceAmount`, `SimpleGrassWind` with
WindIntensity/Weight/Speed), `M_LP2FoliageGlow` for the realm plants (+ `Emissive`, `EmissiveBoost`, slow pulse) and
`M_LP2CorruptGround` for the patch. 3 LODs, no collision. Textures: BaseColor, ORM, Normal_DirectX (+ Emissive).

`source/` rebuilds everything (`build_flora.py` with VARIANT, `floramat.py`, the staged bake).
