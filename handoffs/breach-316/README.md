# #316 The breach made dramatic: part A (trigger, dust, shake, sound, nothing floating)

By `adjustedfilm (Claude)`, 2026-10-31. Owner `W:`: *"the breach isnt dramatic and some roof stones hanging in air, and too much
natural stones rather than gate explosion animation like!"*

- **Part A (here):** BP_BreachFX.
- **Part B (TGA, #327):** the baked masonry collapse. It plugs in here through `CollapseClass`; nothing else changes.

## Pre-checks (done)

- `fix_impure` makes no changes, and `applyall check` is OK (82 nodes, 101 links).
- No existing Blueprint changes: BP_BreachFX watches every BP_WallBreachSpot's parts **by name** (`Rubble*`, `Brk*`, as
  the Master listed them on #316).
- The read-only breach dump (request filed) is used to confirm those names. If they differ, it's a one-string fix in the
  graph's two `StartsWith` nodes.

## What the player gets

- **The natural boulders are gone:** every `Rubble*` part of every breach spot is hidden, and its collision is off.
- **The moment a spot breaks** (its `Brk*` stones appear):
  - **the sound:** a deep blast, a long masonry rumble, stone impacts settling, then a grit trickle (4.2 s, synthesised
    and licence-free);
  - **dust:** 5 bursts (`P_Smoke_Burst`, random sizes) staggered over 0.6 s around the hole;
  - **camera shake:** `BP_CannonShake_Impact`, felt within 15–60 m;
  - **the stones:**
    - now: every `Brk*` stone switches to physics, so it falls and settles instead of hanging in the air;
    - with TGA's baked collapse (#327): the collapse plays at the spot, and the `Brk*` stones are hidden.

## Steps (Master)

1. Run `py "<repo>/handoffs/breach-316/setup_breach316_ue.py" --dry-run`, then without `--dry-run`. It imports
   SFX_WallBreach and makes BP_BreachFX in `/Game/CastleDefender/Gameplay/Siege/Breach`.
2. Open BP_BreachFX. Paste the 7 lines of `VARIABLES_BPVar.txt`, then Compile. Paste `BP_BreachFX_graph.txt` into the
   EventGraph, then Compile and save.
3. Run `py ".../setup_breach316_ue.py" --place`. It places one **BreachFX** in ThirdPersonMap.
4. Later, when #327 lands: set **CollapseClass** on the placed BreachFX to TGA's collapse actor. That's a one-minute
   change.

## Tests (Play)

1. At the start: no round boulders in the courtyard by the breach spots.
2. Break a wall (colossus, wave 4): you hear a deep crash, dust bursts at the hole and the camera shakes.
3. The broken stones fall and settle on the ground. **Nothing hangs in the air.**
4. The other spots don't react until they break.
