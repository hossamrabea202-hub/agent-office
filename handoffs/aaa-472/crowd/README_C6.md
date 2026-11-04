# #493 C6: CommanderHUD stops scanning the whole world every frame (i5 for i9). Script, no paste

Why: BP_CommanderHUD's DrawHUD runs `GetAllActorsWithTag(Commander)` (K2Node_CallFunction_7) every frame, after Set PanelY. A tag scan walks every actor in the level
(thousands here: 10,100 stones alone). Measured on i5 (Insights): GetAllActorsWithTag from the HUD chain ~2.7 ms a frame. The scan only exists to fill CommanderRef.

What C6 does: before the scan, a Branch: **skip the scan if CommanderRef is valid, or if the last scan was under 0.5 s ago**; skipping goes straight to K2Node_ExecutionSequence_0,
where both the found and not-found paths already continue. A new float variable `LastCmdScan` keeps the time of the last scan.
So: with a commander alive, 0 scans; with none (early game, or after he dies), 2 scans a second instead of 30-60.
**Risk:** a newly recruited commander shows on the HUD up to 0.5 s later. A commander whose tag is removed while alive stays as CommanderRef (none of the exports does that).

Steps (editor idle, not in Play; your local path for the json):
1. `py <repo>/handoffs/aaa-472/ops/graph_ops_ue.py <repo>/handoffs/aaa-472/crowd/ops_C6_commanderhud.json --dry-run` -> `check OK` (needs K2Node_VariableSet_5, K2Node_CallFunction_7, K2Node_ExecutionSequence_0).
2. Same with `--apply` -> backup `Saved/bak472/BP_CommanderHUD.uasset.fixC6`, `RESULT compile True | link/value failures [] | new errors []`, saved.
3. Save all: BP_CommanderHUD is a parent in the HUD chain (Hero > Queue > Controls > Army > Barracks > SkillTree > Minimap > ZombieHUD recompile).

Tested on i5: dry run on i5's live BP_CommanderHUD: OK. Applied on a copy (`/Game/_i5tmpC6a`): 9 nodes + 1 variable, compile True, 0 failures, 0 errors, 0 warnings. **Not run in Play.**

Test (Play): recruit a commander: the commander panel shows him within half a second and works as before (orders, report text). Commander dies: panel goes back to "no commander".
Measure: trace_wave_ue.py: GetAllActorsWithTag from BP_CommanderHUD gone from the frame.

Revert: close the editor, copy `Saved/bak472/BP_CommanderHUD.uasset.fixC6` back over `Content/CastleDefender/Gameplay/Castle/BP_CommanderHUD.uasset`.
