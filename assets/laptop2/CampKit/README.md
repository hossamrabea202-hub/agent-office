# Camp kit: TorchPost, Campfire, HayBale, Well, HandCart, MarketStall, Anvil

Made 2026-10-30 by `hossam gmail laptop2 (Claude)` to the knowledge-base standard (`handoffs/knowledge`). Original,
procedural, no third-party assets. Low poly + 2K bakes from high polys. Stone (fieldstone with lichen, moss low down,
soot), mortar, straw, calibrated iron, the shared plank / bark / rope.

| Prop | Mesh | Size | What |
|---|---|---|---|
| **TorchPost** | `SM_Camp_TorchPost` | 2.0 m | Log post with an iron ring bracket and a pitch-wrapped torch; the embers glow (Emissive). The flame itself is a Niagara: spawn it at `flame` in `camptorchpost_meta.json` (≈ x 0.26, z 2.0) with an orange point light, 1700–1900 K, 600 cd, flicker |
| **Campfire** | `SM_Camp_Campfire` | 1.3 m | 14 sooted stones, ash bed, glowing coals, five half-burnt logs, two spare. Fire Niagara at z 0.08 + point light 1800 K, 900 cd. No collision (walkable), damage volume optional |
| **HayBale** | `SM_Camp_HayBale` | 0.9 × 0.5 × 0.4 m | Rectangular straw bale, two twine bands, grey on top, damp at the bottom. Stack 2–3 high, rotate each |
| **Well** | `SM_Camp_Well` | 2.1 × 1.7 × 2.4 m | Stone well head, windlass with crank, rope and bucket, planked roof. Add a water plane at z 0.25 inside (`water_z`) |
| **HandCart** | `SM_Camp_HandCart` | 3.1 × 1.3 × 1.05 m | Two-wheel hand cart on its front legs, shafts toward +X. Put sacks / hay / crates on the bed |
| **MarketStall** | `SM_Camp_MarketStall` | 2.9 × 2.1 × 2.4 m | Vesna's shop stall (#31 / #144): log posts, plank counter (top at `counter_z` 0.945), low shelf, striped canvas awning with a valance, hook bar with 4 iron hooks (`hooks` in the meta: hang shields there). Goods are placed by hand |
| **Anvil** | `SM_Camp_Anvil` | 0.62 × 0.38 × 0.8 m | Iron anvil on an oak stump with a hammer; `work_point` for a smith's hammer animation / sparks Niagara |

All stand on z 0 with the pivot at the base centre; box collision except the campfire. Sink each 1–3 cm into the ground
and add grass / dirt decals at the contact. Group them: the well in the courtyard, carts and bales by the barracks,
torch posts every ~12 m along paths and at the gates (they are the night lighting), campfires at the soldiers' camp.

## Unreal

`py "<repo>/assets/laptop2/CampKit/import_kit_ue.py" [TorchPost ...]` → `/Game/CastleDefender/Environment/Camp/<Prop>/`
with an MI of the shared `M_LP2Weapon` (Tint, Wetness, EmissiveBoost / EmberPulse for the torch and the fire). 3 LODs.
`source/` rebuilds everything (`build_camp.py` with VARIANT, `campmat.py`, the staged bake).
