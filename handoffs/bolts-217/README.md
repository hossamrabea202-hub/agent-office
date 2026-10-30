# #217 Bolts stay stuck in the air (fix)

By `checkking (Claude)`, 2026-10-30 night. Built on `handoffs/exports/master/2026-10-30b/BP_CrossbowBolt.T3D` (EventGraph).
Dry-run merge: **Validation OK** (9 nodes, +8 links).

**Cause.** On a hit, BP_CrossbowBolt stops, sets its lifespan to 8 s (CX_16) and attaches to what it hit. When that
zombie despawns (or dies and gets cleaned up), the bolt is detached and hangs in the air for the rest of the 8 s.

**Fix.** After `CX_14` (SetCollisionEnabled) the chain now runs:
- `SetLifeSpan 5` (instead of 8)
- a looping 0.2 s timer, `BoltCheckParent`
- then on to `CX_21` as before

`BoltCheckParent` destroys the bolt as soon as it has no attach parent. Bolts in walls and the ground keep their parent,
so they stay for 5 s and then go.

**Steps.**
1. Export BP_CrossbowBolt's EventGraph.
2. Run `applyall.py merge --live live.t3d --manifest handoffs/bolts-217/manifest_crossbowbolt.json --out merged.t3d`.
3. Paste, Compile and Save.

**Check.** Shoot a zombie, then let it die and despawn: the bolt vanishes with it. Bolts in walls disappear after 5 s.
Nothing floats.
