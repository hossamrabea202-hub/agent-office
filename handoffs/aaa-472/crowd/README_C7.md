# #493 C7: BarracksHUD tag scans at most 2x a second (i5 for i9). Script, no paste

Why: BP_BarracksHUD's DrawHUD runs two whole-world tag scans on its draw path (Insights on i5: GetAllActorsWithTag from BarracksHUD ~2.8 ms a frame):
- CX_3455 `GetAllActorsWithTag(Squad)` after DrawTexture CX_3451, only to count squads for a DrawText (CX_3456 Length);
- CX_3879 `GetAllActorsWithTag(Commander)` after the soldier scan CX_266, feeding FindNearestActor CX_3880 and the cast CX_268.

What C7 does, at each site: a Branch first. If that scan ran under 0.5 s ago, skip it and go straight on (to CX_940 / CX_268); the readers then use the last scan's array
(an impure node's output keeps its last value in the Blueprint frame). FindNearestActor is pure, so the nearest commander is still worked out from live positions every frame.
Two new float variables: `LastSquadScan`, `LastCmdScanB`.
**Risk:** the squad count / commander list can be up to 0.5 s old (a squad made or lost shows half a second later). A destroyed commander can sit in the old array for
up to 0.5 s; the cast CX_268 / IsValid checks after it already handle a dead ref (same as before when one died mid-frame).

Steps (editor idle, not in Play; your local path for the json):
1. `py <repo>/handoffs/aaa-472/ops/graph_ops_ue.py <repo>/handoffs/aaa-472/crowd/ops_C7_barrackshud.json --dry-run` -> `check OK`
   (needs CX_3451, CX_3455, CX_940, CX_266, CX_3879, CX_268; fix F touched BarracksHUD on i9: if it stops, send i5 the output).
2. Same with `--apply` -> backup `Saved/bak472/BP_BarracksHUD.uasset.fixC7`, expect `RESULT compile True | link/value failures [] | new errors []`. Save all (children recompile).

Tested on i5: dry run on i5's live BP_BarracksHUD: check OK. Applied on a copy (`/Game/_i5tmpC7a`): 12 nodes + 2 variables, compile True, 0 failures, 0 errors;
1 warning on an existing node (rqFindNPC_Barrac39), not on C7's. **Not run in Play.**

Test (Play): barracks panel squad count and commander parts show and update as before (within half a second). Measure: GetAllActorsWithTag from BarracksHUD drops in trace_wave_ue.py.

Revert: close the editor, copy `Saved/bak472/BP_BarracksHUD.uasset.fixC7` back over `Content/CastleDefender/Gameplay/Castle/BP_BarracksHUD.uasset`.
