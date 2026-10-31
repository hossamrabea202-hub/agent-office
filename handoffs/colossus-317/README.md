# #317 The colossus stands outside: fix for BP_ZombieWallBreaker

From TGA (Claude), 2026-10-31. Owner W: "clossal standing outside".

## Cause (read from the 10-30b export)

- **Too wide:** BeginPlay scales the breaker **×3.9–5.8** but keeps the capsule radius at **32 cm**, so in the world the breaker is **125–186 cm wide**.
- **Can't smash:** BreakerThink only smashes within **380 cm** (2D) of its spot's `AttackPoint`. A capsule that fat stops against the wall or the rubble before it gets that close, so it walks in place outside forever.
- **Can't get in:** after a breach, the same fat capsule can't fit through the hole, so it never comes in.

## Fix (paste + manifest, no other Blueprint touched)

| File | |
|---|---|
| `BP_ZombieWallBreaker_Fix317_graph.txt` | 24 nodes. fix_impure + an applyall dry-run merge on the 10-30b export: **Validation OK** (+58 links, 6 rewires). |
| `manifest_wallbreaker.json` | Wiring for the paste (6 rewires). |
| `gen317.py` | Regenerates both files. |

1. **Capsule radius = 45 / GiantScale:** a 45 cm radius in the world at any size. The big body may clip the wall edge a little, which reads fine on a giant.
2. **Stuck watchdog:**
   - In BreakerThink's "still far" branch, if the breaker moves slower than 20 cm/s for 8 ticks (4 s), it is teleported 300 cm short of the AttackPoint, on its own side and at its own height. The smash then starts.
   - While it's moving, the counter resets.

## Master steps

1. Add the variable from `VARIABLES.md` to BP_ZombieWallBreaker, then compile.
2. Export its EventGraph to `live.t3d`.
3. Merge:
   ```
   python tools/applyall/applyall.py merge --live live.t3d --manifest handoffs/colossus-317/manifest_wallbreaker.json --out merged.t3d
   ```
4. Paste, Refresh All Nodes, compile.

The manifest uses the 10-30b node names (`BP_CapS`, `TK_IfFar`, `MV_Go`, `TK_APL`). If they've changed, tell me the new ones.

## Test list

1. **Colossus wave:** set `ColossusFromWave` 1 and `ColossusEvery` 1 on BP_BattleDirector, then ForceNextWave. The colossus walks to its breach spot and starts smashing within a few seconds. If it snags on the way, it pops forward to the wall after 4 s.
2. **After the breach:** it walks through the hole into the courtyard and chases the hero or soldiers, the normal zombie Think.
3. **If it still stops at the hole:** the NavMesh may not be updating at runtime. In Project Settings → Navigation Mesh, Runtime Generation must be `Dynamic` (or `Dynamic Modifiers Only`, if the breach removes a nav modifier) so paths open through new breaches. Tell me which it is.
