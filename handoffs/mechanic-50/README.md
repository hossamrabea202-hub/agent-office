# #50 Mechanic: art + BP spec (laptop2, 2026-10-30)

Art (CampKit, bakes landing this afternoon; meshes and pivots are final now, `source/build_camp.py` rebuilds them):

| Piece | Mesh | Notes |
|---|---|---|
| Cannon cart | `SM_Camp_CannonCart_Body`, `_WheelL`, `_WheelR` | wheel pivots on the axle (`cannoncart_meta.json`: `pieces`, `wheel_radius_m` 0.554, `cradle_socket` for the barrel, `pull_handle` at the front, `push_handle` at the back) |
| Workbench | `SM_Camp_Workbench` | leg vice, hammer/tongs/file on top, toolbox below; `work_point` for the repair animation |
| Grindstone | `SM_Camp_Grindstone` | crank on +Y; `work_point` |
| Anvil | `SM_Camp_Anvil` (already in the repo) | |
| Mechanic badge | decal `T_Decal_MechanicBadge` (next) | gear-and-hammer on a leather disc, put on the soldier's chest or shoulder |

## BP spec (for Codex or the Master, Blueprint-only)

**Mechanic (2 per workshop)**: `BP_Soldier` child `BP_Mechanic`. Tint the cloth material **ochre (0.55, 0.35, 0.10)** with a
dark leather apron; the badge decal on the left shoulder. Recruited at the barracks like soldiers (cost 60 gold) but
only 2 exist; they stay at the workshop (`Realm`-style TargetPoints `Workshop_Idle_0/1`).

**Workshop NPC + shop**: a `BP_WorkshopStall` (reuse the market stall mesh `SM_Camp_MarketStall` + workbench + anvil +
grindstone grouped). E opens the Vesna-style shop list: *Cannon (400 gold)*, *Repair gate (80)*, *Repair cannons (50 each)*,
*Gate upgrade: iron bands (300) → gilded (800)* (swap the gate MI tint: iron grey, then `Gold` 1.0 metallic).

**Buying a cannon**: a placement ghost (translucent cannon mesh, green when the spot is valid: on NavMesh, ≥ 3 m from
walls, not in the realm; red otherwise). Confirm with click. Then:
1. `BP_CannonCart` spawns at the workshop with the cannon barrel attached at `cradle_socket`.
2. Mechanic A takes `pull_handle` (front, walks forward), Mechanic B takes `push_handle` (back). Both use `MoveTo` on
   the cart's path; the cart follows the midpoint of the two at their speed (300 cm/s).
3. Every tick: `dist += |velocity| * dt`; `WheelL/WheelR.AddLocalRotation(pitch = -dist / wheel_radius_cm * 57.3)`
   (reset `dist` after each full turn to avoid float drift). Wheels only turn while the cart moves.
4. Zombies within 25 m switch target to the cart with top priority (`Priority 100` in the #48 target scorer); the cart
   has 300 HP; if it dies the cannon is lost (gold not refunded) and the mechanics run back.
5. On arrival: the barrel detaches, `BP_Cannon` spawns at the ghost spot, the empty cart returns to the workshop.

**Repairs**: a repair order sends one mechanic to the gate / each damaged cannon with the toolbox (`SM_Camp_Workbench`'s
toolbox is a separate mesh to attach to the hand). Repair = 25 HP/s while within 2 m, hammer animation, sparks Niagara at
the `work_point`.

Everything above lives in new Blueprints; nothing existing is rewired except the shop list and the target scorer.
