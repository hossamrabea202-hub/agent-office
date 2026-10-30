# Barracks props (#14): Crate, Barrel, Sack, WeaponRack

Made 2026-10-30 by `hossam gmail laptop2 (Claude)` to the knowledge-base standard. Original, procedural. Low poly + 2K
bake from high polys (plank grain, splits, water rot, hammered iron, burlap weave, cloth folds).

| Prop | Mesh | Tris | Size | What |
|---|---|---|---|---|
| **Crate** | `SM_Barracks_Crate` | 1.4k | 0.7 × 0.5 × 0.45 m | Plank crate, iron corner straps, lid nailed on (one board lifted) |
| **Barrel** | `SM_Barracks_Barrel` | 4.3k | Ø 0.62 × 0.9 m | 20-stave oak barrel, 4 riveted hoops, bung |
| **Sack** | `SM_Barracks_Sack` | 1.2k | 0.9 × 0.6 × 0.6 m | Two burlap grain sacks tied with twine, one spilling |
| **WeaponRack** | `SM_Barracks_WeaponRack` | 6.8k | 1.8 × 0.6 × 1.7 m | Log A-frame with lashed rails, 7 pegs and a shelf (hang the game's swords and crossbows on the pegs) |

All stand on z 0 with the pivot at the base centre; box collision. Group them: crates stacked two high against a wall,
barrels in threes, sacks leaning on crates, the rack beside the barracks door. Sink each 1 to 3 cm into the ground.

## Unreal

`py "<repo>/assets/laptop2/BarracksProps/import_kit_ue.py" [Crate ...]` → `/Game/CastleDefender/Environment/Barracks/<Prop>/`
with an MI of the shared `M_LP2Weapon` (Tint, Wetness). 3 LODs, box collision. `source/` rebuilds everything.
