# i5 core pick-up (2026-11-03 ~22:35), adds to PICKUP_i5_2026-11-03_night.md

The crowd session (local_d16f7c8b) still holds the seat and desk ticks. Nothing below is in the game until i9 confirms it.

## Handed to i9 tonight, no confirmation yet
| Card | What | File | Tested |
|---|---|---|---|
| #461 | Harmony v2: 4 stone MIs become children of one new MI, copying i9's live look | `castle-harmony-461/harmony461_ue.py` | i5, in memory, older MI values; apply + revert OK |
| #440 | Ground colour via the Landscape's own MI | `grass-440/land440b_ue.py` | dry run on an empty level only; values calculated |
| Track L | Read-only after-save check | `castle-harmony-461/aftersave_health_ue.py` | empty level only; the actor loop has not seen real pieces |

Also still unconfirmed: #470, #469 stairs, #455, F11 Muster v2, Think stagger. The "applied yes / no" question went out in chat 1287 and got no answer; ask again.

## Next
1. #477 handed to i9 as scripts: compiles clean on a temp copy, never played. Wait for the result + a 4/4 screenshot to place the badge. Player rebinding only after the owner OK.
2. After i9 re-runs `castle_scan_ue.py`: keep tint A/B, recheck `STONE_SIZES_469.md`. Tower9 1.2 x 1.2 x 1.0 owner asked again in 1292.
3. #440 edge feathering handed to i9 (never run on a map); grass hue open. #458, #453 wait for exports. #450 / #457 are with the crowd session (chat 1296).
4. Cleanup: 188 hidden pieces need Alien's OK. `Castle_WallWalk_EMPTY` has 0 instances: draws nothing, no fix needed.
5. Report for Alien posted in the fast chat; post an update in the morning with what i9 applied.

## Lessons
- Read the chat right before posting a hand-off. v1 of harmony461 would have undone i9's tone pass (1286), posted 40 s earlier.
- Prefer live values over hard-coded ones when someone else may tune the same assets.
- `data.js` captions: no apostrophes; run `node --check data.js` after any edit.
- i5 editor may be on the empty Entry level after a crash; check the world name before trusting a capture. MI re-parenting shows only after a tick, so capture in a separate script.
- i5 editor runs inside the Multi-User sandbox: creating and deleting temp assets there tripped a non-fatal ensure at 22:41 (mine). The fatal one at 22:45 was the crowd session's temp copy. Don't create or delete temp assets in it.
- UE 5.8 Python can edit graphs (`unreal.BlueprintGraphEditor`), so i5 can compile a Blueprint fix on a temp copy before hand-off. Runners: `aaa-472/ops/graph_ops_ue.py`, `obsidian-skill/ember_ops_ue.py`. Use a new folder per test, never delete a copy in the same editor session. `/Game/_i5tmpE` and `/Game/_i5tmp472` are test copies: delete after the next restart. Graph changes to BP_Zombie, BP_ZombieWaveManager, BP_SoldierSword stay with the crowd session until i9 has applied `aaa-472/ops`.
