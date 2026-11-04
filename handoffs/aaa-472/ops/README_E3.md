# #487 E3: mines, tentacles, chandeliers tick less (i5 core, 2026-11-04)

Audit rows A13, A14, A19, A21 (`handoffs/vram-482/BP_AUDIT.md`). Each script adds one `SetActorTickInterval` at the top of the
actor's Tick. Nothing else in the graph changes.

| Blueprint (placed) | Today | Fix | Behaviour |
|---|---|---|---|
| BP_BlobMine (22) | ticks every frame only to count to 0.2 s, then one distance check | tick every 0.19 s | the same 5 checks a second |
| BP_TentacleVitals (10) | every frame: camera line trace, HP bar text, regen, sword-hit test | full rate within 20 m of the player, else 10 per second | close up identical (sword hits); from afar the HP bar updates 10x a second; regen uses the frame time, so it is unchanged |
| BP_JellyBlob, and BP_JellyMine through it (19 + spawned) | every frame: wobble, trigger check, material reads | full rate when on screen OR within 20 m, else 5 per second | what you see and can touch is identical; off screen and far away it wobbles 5x a second |
| BP_SwayChandelier (5) | every frame: world search, material parameter read/write, sway | full rate when on screen, else 5 per second | sway is computed from game time, so it is right whenever it is seen; the gate-hit sway may start up to 0.2 s later |

Gain: unmeasured. At 60 fps, about 1,700 fewer Blueprint ticks a second from the mines alone (22 x 55), plus 10 line traces a
frame from the tentacles when you are not next to them. Game thread only; check with `stat game` on a strong PC.

## Steps (i9, editor idle, not in Play, `git pull` first)
For each of `blobmine`, `tentaclevitals`, `jellyblob`, `chandelier`:
```
py <repo>/handoffs/aaa-472/ops/graph_ops_ue.py <repo>/handoffs/aaa-472/ops/ops_E3_blobmine.json --dry-run
py <repo>/handoffs/aaa-472/ops/graph_ops_ue.py <repo>/handoffs/aaa-472/ops/ops_E3_blobmine.json --apply
```
Expect `check OK`, then `RESULT compile True | link/value failures [] | new errors []` and `saved True`. After jellyblob, check
BP_JellyMine compiles (its child). Anything else: don't save, restart without saving, send i5 the output.

## Tested on i5 (no live session: the server dropped at 12:59, so on i5's own copies of the assets)
- `--dry-run` on all 4 real Blueprints: check OK.
- On copies (/Game/_i5tmpE3a, b, c): `compile True`, 0 failures, 0 new errors, 0 warnings. Not saved.

**Not tested:** Play.

## Play test
- Walk into a blob mine: it bursts as before. Jelly mines wobble and trigger as before.
- Look at a tentacle from far away: its HP bar still shows and counts. Hit one with the sword up close: hits register as before.
- Hit the gate: the chandeliers in view sway.
- `stat game` before and after if you can.

## Revert
The runner copies each .uasset to `Saved/bak472/` (`*.uasset.fixE3`) before `--apply`. Close the editor, copy it back, reopen.
