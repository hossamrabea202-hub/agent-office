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

## Owner order 2026-11-03 night (card #482): "work nonestop until our game quality becomes AAA (dont add new features rather enhance existing ones)"
- Decision: polish only. Player key rebinding and the #453 Gothic set are parked as new features.
- In the game (saved by i9): #470 crack removal, #461 harmony v2 + i9's floor overrides. i9 runs the rest in the order of chat 1316.
- #458: my ORE/FOOD collision note is probably stale, #411's scroll replaced that text (chat 304). Don't build it without a current screenshot.
- Load-error audit of the i5 log found only 2 harmless missing packages, not worth a fix.
- Blocked on i9's queue: profiled wave (#473, decides the crisp image A/B), fresh castle scan (keep tint), HUD screenshots, 4/4 screenshot (badge).
- Needs the owner: delete the 188 hidden old pieces (648k tris).
- 23:45: #477 v1 + #440 ground + feathering applied by i9; #477 fix 2 (`ember2_ue.py`, helm has no art) sent in chat 1340. Temp copy `/Game/_i5tmpE2` on i5: delete after the next restart. #472 A-D in the game: errors 0, but no fps gain on i9's T1000 (3.9 -> 4.3 fps, GPU limit).
- 00:00: after-save health run by i9: DEFAULT_MAT 0, OVERRIDE 0, STRETCH 4 (Tower9; shapes need TGA_PC, textures fixed by i9), NO_MESH 129 harmless, HIDDEN_BLOCK 275: reviewed, `hidden_collision_ue.py` sent (chat after 1344). Waiting: its dry-run output, `ember2_ue.py` result, BaseColor shot for #440. Ground shader layers on top of the tints: corrupted earth around 10 tentacles (intentional), killing-field mud, road, tyre-track comments in M_MountainBackdrop: check whether ruts read modern.
