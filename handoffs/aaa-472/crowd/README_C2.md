# #493 C2: wave-start and swarm spawns respect the zombie limit (i5 for i9). Script, no paste

Why: BP_ZombieWaveManager's steady spawn already stops at 45 alive zombies (WV_29: Length(alive) < 45). Two other spawn paths skip any limit:
- wave start: WV_110.then -> SpawnActor WV_114 (inside WV_92, a For Each over all 6 wave managers),
- swarm burst: For Loop CX_26 -> SpawnActor CX_30 (up to 4 per manager, every 3rd wave from wave 2, managers near the gate).
With 6 managers these stack on top of the 45. Every alive zombie costs ~0.8-1 ms of game thread on i5 (crowd/CROWD_PLAN.md), so the count must have a ceiling.

What C2 does, at both sites: count alive BP_Zombie (one GetAllActorsOfClass, only at those rare moments). If fewer than **60**, spawn as before.
If not, `ToSpawn = ToSpawn + 1` instead: the steady path spawns it later, when the count is under 45 again.
After WV_114 / CX_30 only the new zombie's own setup runs (ZType, Runner, speed, scale, materials, HP), so a skipped spawn skips nothing else.
**Decision / gameplay change:** an overflow zombie comes back later as a normal steady-path zombie, not the wave-start / swarm variant. Waves feel a little longer and thinner at peak. Cap 60 is a pin value (the two Less_IntInt B pins).

Steps (editor idle, not in Play). Use your local path for the json (your runner rewrites paths in scripts, not in args):
1. `py <repo>/handoffs/aaa-472/ops/graph_ops_ue.py <repo>/handoffs/aaa-472/crowd/ops_C2_wavecap.json --dry-run` -> `check OK`.
   It needs WV_110, WV_114, CX_26, CX_30 by name. If your manager differs after fix A, it stops and changes nothing: send i5 the output.
2. Same with `--apply` -> backup `Saved/bak472/BP_ZombieWaveManager.uasset.fixC2`, expect `RESULT compile True | link/value failures [] | new errors []`, saved.

Tested on i5: dry run on i5's live BP_ZombieWaveManager: check OK. Applied on a real copy (`--copy /Game/_i5tmpC2a --wmcopy`): 14 nodes, 18 links, 0 link failures, 0 new errors.
The copy shows compile False only from 6 errors that were there before the change (WV_92, WV_95, WV_105, CX_14, CX_55, CX_57: a copied manager's loops are typed to the real class).
**i5's manager is older than i9's (no fix A). Not run in Play.**

Test (Play, editor in front): force waves 1-6 (swarm from wave 2 every 3rd). Alive BP_Zombie never goes far above 60; waves still end (ToSpawn drains to 0); special wave-start zombies still appear while under the cap.
Measure: `measure_split_ue.py` at the peak of wave 5-6, before and after.

Revert: close the editor, copy `Saved/bak472/BP_ZombieWaveManager.uasset.fixC2` back over `Content/CastleDefender/Gameplay/Castle/BP_ZombieWaveManager.uasset`.
