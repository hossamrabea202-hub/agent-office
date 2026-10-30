# Mine kit (#201 / #202 item 1): mine entrance + 5 ore cart loads

Made 2026-10-30 by `hossam gmail laptop2 (Claude)` to the knowledge-base standard (`handoffs/knowledge`). Original,
procedural, no third-party assets. Low poly + baked textures from high polys (entrance 2K, ores 1K). Uses the CampKit
materials (fieldstone with lichen/moss/soot, trodden dirt, bark logs, planks, iron) plus five new ore materials.

| Item | Mesh | Size | What |
|---|---|---|---|
| **MineEntrance** | `SM_Camp_MineEntrance` | 7.6 × 6.0 × 4.0 m | A rock hill with bedded boulders and ledges, a hewn tunnel 2.1 m wide / 2.6 m high running 3.2 m in (torch soot deepens inside), six timber sets (posts + cap logs) with lagging boards, a two-set porch, name board, wooden rails with iron straps on sleepers out to the road, spoil heap, a pick leaning on the porch, an iron lantern arm |
| **OreIron** | `SM_Camp_OreIron` | 1.64 × 0.76 × 0.39 m | Red hematite chunks, rust bloom, steel-grey magnetite grains |
| **OreCopper** | `SM_Camp_OreCopper` | same | Brown host rock, green malachite crust, blue azurite, native copper flecks |
| **OreSilver** | `SM_Camp_OreSilver` | same | Dark rock with blocky metallic galena and milky quartz veins |
| **OreGold** | `SM_Camp_OreGold` | same | White quartz, limonite rust, thin gold veins and flakes |
| **OreStar** | `SM_Camp_OreStar` | same | Dark meteoric iron with an etched lattice, fusion crust, blue glowing crystal veins (Emissive) |

The five ore loads share one shape (same UVs), so the cart can keep one mesh and swap the material instance by metal
(`OreMats[Metal]` in BP_OreCart / BP_OrePile, hand-off #207 v3). They sit on the CampKit HandCart bed: attach at
(-5, 0, 62) cm in SM_Camp_HandCart space.

**MineEntrance placement:** pivot at the mouth's ground point, mouth faces +X. Put BP_Mine at the same transform: its
forward spawn (3 m) lands the carts on the rails (`cart_spawn` in `campmineentrance_meta.json`). Hang the CampKit
Lantern at `lantern` and tag it `NightLight` (BP_DayNight lights it at dusk). Sink the hill 5–10 cm into the landscape
and blend the edge with GroundKit Mud/Cobble. Collision is per-polygon (complex as simple) so the tunnel stays open.

## Unreal

`py "<repo>/assets/laptop2/MineKit/import_kit_ue.py" [MineEntrance OreIron ...]` → `/Game/CastleDefender/Environment/Mine/<Item>/`
with an MI of the shared `M_LP2Weapon` (OreStar gets the Emissive map; raise EmissiveBoost for a stronger glow at night).
3 LODs. `source/` rebuilds everything (`build_camp.py` with VARIANT, `campmat.py`, the staged bake).
