# #493 C3: soldiers fight from a near-zombies list (i5 for i9). Script, no paste. Needs fix D (applied on i9); K (#492) is independent

Why (measured on i5): BP_SoldierSword's Tick costs ~15 ms per soldier per frame at 142 zombies and grows with every zombie, because its fight loop CX_145 walks
every zombie every frame. Soldier tick off saved ~34 ms with only 2 soldiers at 314 zombies.

What C3 does:
- New component `/Game/CastleDefender/Gameplay/Crowd/BPC_NearZombies`, added to BP_SoldierSword (BP_SoldierXbow inherits it). 5 times a second (start staggered):
  one native SphereOverlapActors, 12 m, object type Pawn, class BP_Zombie -> cast -> `NearZombies` (array of BP_Zombie).
- The fight loop CX_145 reads `NearZombies` instead of the manager's ZombieReg (fix D's input). Nothing else in the soldier changes.
- Why 12 m is safe: the loop's conditions only act on zombies within 1.75 m (engage flag), 2.4-4.5 m and 7 m (chase / attack). Zombies farther than that were walked
  through and skipped every frame. Other soldier logic (formation, FindNearestActor, the release loop CX_454) still uses its old inputs.
- Expected: the loop walks ~0-15 zombies instead of all of them: soldier cost from ~15 ms to ~1-2 ms each in a big wave (G: estimated, not measured).

Steps (editor idle, not in Play):
1. `py C:/Users/hossam.rabea/agent-office/handoffs/aaa-472/crowd/crowd_near_c3_ue.py --dry-run` -> `C3: CX_145 reads Get ZombieReg ...` and `dry run`.
   If it says CX_145 is missing or reads something else, stop and send i5 the output.
2. `py .../crowd_near_c3_ue.py --apply` -> backup `Saved/bak472/BP_SoldierSword.uasset.fixC3`, makes BPC_NearZombies (expect `RESULT compile True | link/value failures []`),
   attaches it as `NearZombies`, rewires CX_145 (expect a second `RESULT compile True ... new errors []`), saves both.
3. Save all (BP_SoldierXbow recompiles).

Tested on i5: on a copy of the soldier with fix D and fix K applied (`/Game/_i5tmpK487a/X472c`), component in `/Game/_i5tmpC3b`:
component compile True, 0 failures; soldier compile True, 0 failures, 0 new errors, 0 warnings; CX_145.Array <= Get NearZombies; a second run refuses.
**Not run in Play.** Not tested on i9's graph (the dry run checks it).

Test (Play, editor in front, forced wave):
- Soldiers still engage zombies that come near, chase within ~7 m, attack, kill; zombies engaged by a soldier still stop and fight back.
- A zombie that runs past a soldier is still picked up (list refreshes 5 x a second).
- Measure before / after: `py .../profile/trace_wave_ue.py`, then `node profile/insights_bp_callers.js` on the export: `BP_SoldierSword.ReceiveTick` should fall several times.

Revert: close the editor, copy `Saved/bak472/BP_SoldierSword.uasset.fixC3` over `Content/CastleDefender/Characters/Knight/BP_SoldierSword.uasset`, reopen.
Tune: radius `1200` and `0.2` s are pin values in BPC_NearZombies.
