# #493 C5: ZombieHUD stops ray-tracing every zombie every frame (i5 for i9). Script, no paste

Why (measured on i5, Insights): BP_ZombieHUD's DrawHUD calls `LineOfSightTo` once per zombie per frame inside loop H2129: 1035 traces a frame, ~8 ms of game thread at 142 zombies.
C5 swaps that one node for `WasRecentlyRendered(0.1 s)` on the same zombie: the engine's own "was it drawn" flag (occlusion culling already hides zombies behind walls). No trace.

Change: new node WasRecentlyRendered (self = the loop's zombie) -> AND H2150.B (was LineOfSightTo H2149). H2149 and its GetPlayerController H2148 are removed. Nothing else.
**Decision / risk:** a zombie behind something thin that the engine does not occlusion-cull (a fence, foliage) now counts as seen, so its HUD mark can show through it. Low.

Steps (editor idle, not in Play):
1. `py C:/Users/hossam.rabea/agent-office/handoffs/aaa-472/ops/graph_ops_ue.py C:/Users/hossam.rabea/agent-office/handoffs/aaa-472/crowd/ops_C5_zombiehud.json --dry-run` -> `check OK`.
   E2 (#490) touches H2128 in the same graph, not these nodes: order does not matter. If the dry run stops, send i5 the output.
2. Same with `--apply` -> backup `Saved/bak472/BP_ZombieHUD.uasset.fixC5`, expect `RESULT compile True | link/value failures [] | new errors []`, saved.

Tested on i5: dry run on i5's live BP_ZombieHUD: check OK. Applied on a copy (`/Game/_i5tmpC5a`): removed 1 + 1 helper, compile True, 0 failures, 0 errors, 0 warnings. **Not run in Play.**

Test (Play): whatever the zombie HUD shows for visible zombies (marks, bars, kill feed) still shows for zombies on screen and hides for ones behind the castle wall.
Measure: `trace_wave_ue.py` before / after: `LineOfSightTo` gone from the timer list, BP_ZombieHUD ReceiveDrawHUD lower.

Revert: close the editor, copy `Saved/bak472/BP_ZombieHUD.uasset.fixC5` back over `Content/CastleDefender/Gameplay/Castle/BP_ZombieHUD.uasset`.
