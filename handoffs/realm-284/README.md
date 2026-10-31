# #284 Realm bubble v1: cannon shots bounce off, only troops inside kill the tentacles, the realm collapses

From TGA (Claude), 2026-10-31. Owner whiteboard task:

> the realm wobbly bubble reflects cannons shots on ground. to destroy the tentacles inside you must get troops inside.
> the realm disappears when those two tentacles are killed.

| File | Target | Check |
|---|---|---|
| `Cannonball_RealmBounce_graph.txt` + `manifest_cannonball.json` | **BP_Cannonball** EventGraph (28 nodes, 6 rewires) | fix_impure + Validation OK. Dry-run **OK (+66 LinkedTo)** on the 10-30b export with its broken CX_99 links stripped (see note) |
| `BP_RealmDirector_graph.txt` | new **BP_RealmDirector** (115 nodes) | fix_impure + Validation OK |
| `setup_realm284_ue.py` | tags + creates and places the director | DRY_RUN switch |

`gen284.py` regenerates everything, using the #223 helpers.

## What it does

1. **Cannon shots bounce off the bubble.** When a cannonball's Event Hit is the dome (actor tag `RealmBubble`), the ball does not explode.
   - It is **mirrored on the hit normal at half speed and forced downward** (−200 cm/s or more), so it lands outside the realm.
   - A **flash** plays on the dome where it hit.
   - The ball then explodes on the ground as usual. It bounces once only (`Bounced`).
   - Projectile movement stops itself after a blocking hit, so the bounce is re-armed 0.02 s later:
     SetUpdatedComponent(Ball) → Velocity → Activate.
2. **Only troops inside hurt the tentacles.** The dome turns cannon fire away. Every second, `BP_RealmDirector` checks each soldier (`BP_SoldierSword` and children) **inside the dome**:
   - it **marches on the nearest living tentacle** (`BP_TentacleVitals`)
   - within **4.5 m** it takes **25 Health per second** off it, per soldier
3. **A tentacle at 0 falls.** It is hidden with its collision off, a burst plays, and a notice shows "A TENTACLE FALLS (1 / 2)".
4. **Both down: the realm collapses.**
   - A notice shows "THE REALM COLLAPSES! The land is free again." (tier 3), with a big burst.
   - The **dome shrinks to nothing over 4 s**.
   - Every realm actor (tag `laptop2_realm`: walls, towers, gate, plants, mines, eggs, lights) is **hidden with its collision off**.
   - **PPV_Realm is removed**, and the land looks normal again.

**Decision (numbers, TGA):** each soldier deals 25 HP/s within 4.5 m, the collapse needs 2 tentacles, the shrink takes 4 s, and a bounce keeps half speed. All are variables on BP_RealmDirector.

## Master steps

1. **Cannonball variables:** add `Bounced` (bool) and `BounceVel` (vector) to **BP_Cannonball** from `VARIABLES.md`, then compile.
2. **Cannonball merge:**
   1. Export BP_Cannonball's EventGraph to `live.t3d`.
   2. Run:
      ```
      python tools/applyall/applyall.py merge --live live.t3d --manifest handoffs/realm-284/manifest_cannonball.json --out merged.t3d
      ```
   3. Paste, Refresh All Nodes and compile.
   - It hooks the ball's **Event Hit (`CX_1`)** before its old first branch (`CX_255`). If those names changed in your Blueprint, tell me the new ones.
3. **Setup:** run `py ".../handoffs/realm-284/setup_realm284_ue.py"` with the game level open (DRY_RUN first).
   - It tags `Realm_Dome` → `RealmBubble` and `PPV_Realm` → `RealmPPV`.
   - It creates `BP_RealmDirector`.
4. **Director:** add the director's `VARIABLES.md` lines, paste `BP_RealmDirector_graph.txt`, then compile.
5. **Place it:** run the setup script again. It places `Realm_Director` at the dome. Save the level.
6. **Dome collision:** the dome (`Realm_Dome`) must **block** the cannonball (its collision is on: laptop2 placed it last for exactly that reason). It must **not block soldiers' pawns** (Pawn channel = Ignore or Overlap), so troops can walk in through the gate or breach.

## Test list

1. **Cannon at the realm:** fire a cannon at the bubble. The ball bounces off downward with a flash at the hit point, lands outside and explodes there. The tentacles take no damage.
2. **Soldiers inside:** order soldiers in through the realm gate or breach. They walk to the nearest tentacle, and its health bar (BP_TentacleVitals) drops while they stand at it.
3. **First tentacle:** it disappears with a burst and the "A TENTACLE FALLS (1 / 2)" notice. The soldiers move on to the second.
4. **Second tentacle:** the collapse notice and a big burst play, and the dome shrinks away over 4 s. Walls, towers, plants, the gate and the pink post-process all disappear, and walking through the old realm area is free.
5. **Soldiers outside the dome** are not affected or redirected.

## Notes

- **Broken export:** the 10-30b BP_Cannonball export is **missing node `CX_99`** (applyall `check` fails on the export itself), so the dry-run was done on a copy with only those dangling links removed. My rewires don't touch CX_99. A fresh export is requested in **#287**.
- **Tentacle health:** the director subtracts soldier damage from `BP_TentacleVitals.Health` (the value its health bar shows). If your tentacles keep their real HP elsewhere (`BPC_TentacleStrike` or the tentacle actor), tell me or answer #287 and I'll point it there. The tentacle's own death animation, if any, still plays from its own code; the director hides it at 0.
- **Other projectiles:** crossbow bolts are not bounced, but they hit the dome and do nothing to the tentacles anyway.
