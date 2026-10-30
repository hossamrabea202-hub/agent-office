# #230 Deploy cannon: order a cannon, a cart convoy brings it, it deploys on a wall pad

By `checkking (Claude)`, 2026-10-30 night. UE 5.3, Blueprint only. Both graphs pass `applyall check` (Validation OK).
Following the Master's rules:
- every cast, actor lookup and GetAllActors call is in the exec chain;
- variables come as **BPVar lines** (`VARIABLES_BPVar.txt`), not Python.

## What the player gets

1. **Ordering.** At the artillery yard (a `BP_CannonOrder` placed in the courtyard), walking in shows
   "Artillery yard – press O to order a cannon". **O** with enough gold (`Price` 800) does three things:
   - takes the gold from `BP_ZombieHUD.Gold`;
   - reserves the next free cannon pad on the walls (an actor tagged `CannonPad`; its tag becomes `CannonPadUsed`);
   - sends a cart and says "Cannon ordered – the crew is on the way".
2. **The convoy.** `BP_CannonConvoy` (the CampKit cannon cart) walks the NavMesh to the pad:
   - **two BP_SoldierSword crew** walk beside it (re-ordered every second to stay 2.2 m left and right of the cart);
   - the wheels `WheelL` / `WheelR` roll by distance travelled (55.4 cm radius, from `cannoncart_meta.json`).
3. **Zombies.** While it travels, every second any zombie within 15 m is sent at the cart (`SimpleMoveToActor`). The cart
   has **400 HP** and takes any damage. At 0 HP: "The cannon cart was destroyed".
4. **Deploying.** Within 2.2 m of the pad the cart stops, **spawns `BP_Cannon` at the pad with the pad's rotation**, says
   "Cannon deployed on the wall" and removes itself. The crew stay as soldiers.
5. **Failures.** No gold: "Not enough gold for a cannon". No free pad: "No free cannon pad on the walls". Nothing is
   charged in either case.

All messages go through `BP_NoticeHUD.PushNotice(Text, Tier)`, the #31 rolled banner.

## Master steps

**A. BP_CannonOrder.** New Blueprint, parent **Actor**, in `/Game/CastleDefender/Gameplay/Castle/`.
- Components: a Box (or Sphere) collision about 4 m (Overlap All Dynamic, Generate Overlap Events), plus optionally a
  sign mesh (a CampKit Banner works). The cart spawns 3 m along the actor's **forward (X) arrow**.
- Variables: paste the 2 BPVar lines under `# BP_CannonOrder` from `VARIABLES_BPVar.txt`, one at a time, on the
  VARIABLES header.
- Paste `BP_CannonOrder_graph.txt` into the EventGraph (delete the default BeginPlay / Overlap stubs first), Refresh All
  Nodes, Compile.

**B. BP_CannonConvoy.** New Blueprint, parent **Character** (like BP_OreCart).
- Components:
  - StaticMesh **`Body`** = `SM_Camp_CannonCart_Body`;
  - StaticMesh **`WheelL`** at (0, −62, 55) cm and **`WheelR`** at (0, 62, 55) cm (`SM_Camp_CannonCart_WheelL` /
    `_WheelR`, from `assets/laptop2/CampKit/CannonCart`);
  - optionally a cannon barrel mesh at the cradle (0, 0, 75).
- Capsule radius about 120, half height about 90; leave the skeletal Mesh empty.
- Class defaults: Auto Possess AI = Placed in World or Spawned, AI Controller = AIController,
  CharacterMovement Max Walk Speed 200, Use RVO Avoidance on.
- Variables: paste the 6 BPVar lines under `# BP_CannonConvoy`.
- Paste `BP_CannonConvoy_graph.txt` (delete the AnyDamage stub if present), Refresh All Nodes, Compile.

**C. Level.**
- Place one BP_CannonOrder in the courtyard, arrow toward the gate road.
- Put Actor tag **`CannonPad`** on 2–4 empty spots on the wall walk (plain Target Point actors are fine), rotated the way
  the cannon should face. The NavMesh must reach them.
- Save the map.

## Test

1. With 2,000 gold, stand in the yard: the banner shows. Press O: −800 gold, and a cart with 2 soldiers appears and walks
   to a pad with the wheels turning.
2. At the pad, a BP_Cannon appears facing the pad's direction, the cart is gone, and the banner says "Cannon deployed".
   Press O again: the next pad is used.
3. With all pads used: "No free cannon pad", and no gold is taken. With 0 gold: "Not enough gold".
4. During a wave, zombies near the cart run at it. Let them wreck it: "destroyed", and the cart is gone. (That pad stays
   reserved; reset its tag by hand if you want it back. v2 would free it.)
5. Two minutes of Play with no new runtime errors.

## Decisions

- **BPC_ConvoyJob50 (Codex) isn't driven by this v1.** The convoy needs only travel, HP, wheels and a deploy handshake,
  and those are here, in the same order as #50's lifecycle (ordered → travelling → deployed / lost).
  `ShouldTargetConvoy` is the 15 m lure. Wiring ConvoyJob50's two-crew readiness can come next if the owner wants crew
  deaths to stall the cart.
- **The key is O.** C is the commander panel, T the tree, I the pack, E the order wheel.
