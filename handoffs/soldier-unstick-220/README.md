# #220 Soldier unstick redo (#205 / #181)

By `checkking (Claude)`, 2026-10-30 night. Built on `handoffs/exports/master/2026-10-30b/BP_SoldierSword.T3D` (EventGraph).
Dry-run merge: **Validation OK** (28 nodes, +35 links).

**Why the old paste failed.** #205 treated `Goal` as an Actor. Here it's a SceneComponent: its RelativeLocation is a
formation offset.

**What this does instead.** It reads the real move target: the vector `CX_86` that the soldier's own order sends to
`SimpleMoveToLocation` (`CX_399`). It comes in through a reroute knot, and the controller is the same one CX_399 uses
(`K2Node_CallFunction_2`). The behaviour is the same as #205:
- Each Tick: if the target is more than 1.5 m away and speed is under 15 cm/s, `StuckT` counts up; otherwise it resets.
- After 1.5 s stuck: a 60 cm swept nudge toward the target (+10 cm up for the door sill), the move to the target is
  re-issued, and `StuckT` resets.
- BP_SoldierCommander inherits it.

`StuckT` and RVO avoidance are already in, from #205.

**Steps.**
1. Export BP_SoldierSword's EventGraph.
2. Run `applyall.py merge --manifest handoffs/soldier-unstick-220/manifest_soldiersword.json`.
3. Paste, Compile and Save. Delete the failed #205 nodes if any are left.

**Check.** Order 20 soldiers out through the gate: nobody spins in the opening, and stragglers get nudged through within
about 2 s.
