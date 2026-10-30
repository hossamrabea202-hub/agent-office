# #181 Soldiers stuck at the gate (spinning / jumping) — fix

From: hossam gmail laptop2 (Claude), 2026-10-30. Target: `BP_SoldierSword` EventGraph (paste + 3 rewires, 1 variable).
`BP_SoldierCommander` is a child of BP_SoldierSword, so it gets the fix too.

**What it does:** a stuck detector at the top of Tick. While a soldier has a Goal that is still > 1.5 m away but its
speed is under 15 cm/s, a timer counts up; after 1.5 s the soldier is nudged 60 cm toward the goal (swept, 10 cm up so
it steps over the door sill) and its move order is re-issued. Moving normally resets the timer every frame.

**Master steps:**
1. Add `StuckT` (float, default 0) to BP_SoldierSword.
2. `python tools/applyall/applyall.py merge --live <BP_SoldierSword EventGraph export> --manifest handoffs/gate-jam-181/manifest.json --out merged.t3d`
   (dry-run on 2026-10-30b: Validation OK), paste, Refresh All Nodes, compile.
3. **Also set, by hand, on BP_SoldierSword and BP_SoldierCommander → CharacterMovement:** `Use RVO Avoidance` = on,
   `Avoidance Consideration Radius` = 200. Twenty soldiers in a 6 m opening shove each other without it.
4. Test: order 20 soldiers out; all pass, none spin in the opening. If some still catch on the door leaves, raise the
   nudge (the `Multiply_VectorFloat` B default 60 → 90).

Not touched: the gate's ZombieStop volume (it blocks zombies only) and the NavMesh.
