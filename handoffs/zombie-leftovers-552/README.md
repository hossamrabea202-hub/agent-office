# Owner's list, items 1, 2, 4, 5 (adjustedfilm, 2026-11-06). Run in this order, editor idle, not in Play. No paste.

Tested in the i5 labs: dry-run, apply, second apply, revert, apply. New compile errors: none. **Nothing here was tested in Play: the labs cannot start PIE.**

```
git pull
py handoffs/tentacle-spore-base-539/sporebase_ue.py --reimport --dry-run      then --reimport, save the level
py handoffs/tentacle-eruption-cinematic/eruption_assets_ue.py                 crack roughness, already under #549
py handoffs/tentacle-death-551/tentacle_death_ue.py --dry-run                 then --apply
py handoffs/zombie-leftovers-552/zombie_variant_ue.py --dry-run               then --apply
py handoffs/zombie-leftovers-552/brute_roar_death_ue.py --dry-run             then --apply
```
Each script has `--revert`. Each stops without saving on a missing node or a new compile error.

| Item | What changes | Play test |
|---|---|---|
| 1 ground blend | fine stones, grime, a dirt skirt decal around each base. Re-places the bases, tagged `SporeBase` | Walk to a base: no hard line where rock meets ground |
| 2 crack roughness | T_EruptCrack_ORM | Cracks are not shiny |
| 4 tentacle death | AS_Tentacle_CannonC rewritten in place (backup _BAK551): convulsions, goes rigid, topples, tip lands, twitches. Then 8 pods burst, 0.4 s apart, and the base steps to dark. The sink now starts at 4.4 s, not 1.6 s | Kill a tentacle: arm falls before it sinks, bursts on the base, base stays dark and dull |
| 5 zombie gait | Half the walkers get ZV_Walk_Lumber and ZV_Run_Reach. BS_Zombie_Locomotion backup _BAK552. Colossus stays on its own set | A wave: two visibly different walks and runs, no idle slide, colossus still stomps |
| 5 brute roar | First time the player is within 35 m: stops, roars (07_Behemoth_Roar_Cue, 3 s), walks on. Once per brute | Approach a brute. Kill it during the roar: it must not walk on |
| 5 brute death | 50/50 forward or side fall, while it dissolves | Kill several: both falls appear. The clip is cut at the 2.2 s lifespan |

**Decision for the owner:** the #449 dissolve had bypassed every death clip, so the brute froze in its last pose while dissolving. It now falls as it dissolves. The clips last 3.0 and 2.6 s, so the end is never seen.

Built on: BP_TentacleVitals export 2026-11-06b, ABP_Zombie colossus-anim export, BP_FleshBrute brute-449s2 export. Rules applied: knowledge base locked-exposure lookdev (base alive/dead in `tentacle-death-551/preview`), pbr_check, INDUSTRY_SECRETS motion variation per actor, follow-through on the fall.
