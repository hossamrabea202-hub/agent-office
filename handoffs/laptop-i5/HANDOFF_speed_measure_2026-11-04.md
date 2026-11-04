# Hand-off: find where the battle frame time goes, then fix the biggest cost (i5, 2026-11-04 ~13:45)

You are i5 core on laptop-i5 (i5-1235U, 2 GB MX570), Castle Defender, UE 5.8.4. Repo: C:\Users\hossam.rabea\agent-office.
Seat `checkking (Claude)`, chat name `i5 (checkking)`. Owner: Alien. Master editor: i9 (applies and saves; nothing is in the game until i9 says so).

## Read first
- `AGENTS.md` (office rules: tick your desk, card first, hand-offs as scripts with --dry-run / --apply / revert).
- This file, then `handoffs/vram-482/OPTIMIZE_PLAN.md` and `handoffs/vram-482/BP_AUDIT.md` (the speed plan and the Blueprint audit).
- `handoffs/aaa-472/ops/README_E2.md`, `README_E3.md` (what this session already handed to i9).
- Fast chat: http://100.87.149.123:8765 (`/read?after=N`; POST `/say` with "From: i5 (checkking): ..."). Last line read: 1621.
  At 13:40 the chat server stopped answering (timeouts): i9 may be swapping in the new 24 h / archive version. Retry; if it stays down, use the cafeteria (GitHub issue #25) and tick `--ask`.

## The goal (Alien's order, card 487)
"go through codes and game system we built and find out how to optimize to reach AAA ms levels". Target 33.3 ms (30 fps), then 16.7 ms.
Known numbers, all from i9's PC (CPU 91-98 C, so throttling may be in every number):
- battle, about 84 zombies: 250-330 ms a frame (3-4 fps)
- no wave: about 64 ms (15.7 fps)
So a wave adds about 200 ms and NOBODY KNOWS WHICH PART. Fixes A-D, LODs and E2/E3 are game-thread work; none was measured.

## Your task
1. **Measure on i5** (i9 never ran the speed test):
   - Editor must be running and responsive. Launch: rename `C:\UnrealProjects\Castle Defender 5.8\Saved\Autosaves\PackageRestoreData.json` if present, then
     `Start-Process cmd -ArgumentList '/c','"C:\UnrealProjects\Castle Defender 5.8\JOIN_LIVE.bat"' -WindowStyle Hidden`.
     Run editor Python with `sh handoffs/laptop-i5/ue_run.sh <script.py> [args]`. The watcher only runs scripts while Multi-User is CONNECTED;
     scripts whose file name starts with `nomu_` run without the session (copy a script to the scratchpad under a `nomu_` name).
     The Multi-User server dropped at 12:59 and i5 was still trying to rejoin. If scripts don't start, focus the editor:
     `handoffs/laptop-i5/ue_windows.ps1 -Focus 'CastleDefender - Unreal Editor'` (NEVER -CloseExtra, never WM_CLOSE on UE windows).
     Load the map after a (re)join: `handoffs/laptop-i5/_loadmap.py`.
   - Start Play (see `handoffs/laptop-i5/pie_ue.py`), then run `handoffs/aaa-472/profile/wave_sweep_ue.py` (read-only, ~2 min, forces a wave if
     under 60 zombies, writes sweep_<time>.json/.txt). Also take `stat unit` (Game / Draw / GPU / RHIT ms) with no wave and in a full wave.
     Use `stat game` and, if you can, a short `stat startfile` / `stat stopfile` or Unreal Insights trace during the wave to name the top Blueprints / systems.
   - On i5 the GPU number is not representative (2 GB MX570). The GAME THREAD number is: it is CPU logic. If Game ms jumps by ~200 ms in a wave,
     the cost is gameplay logic and fixable by us; if Game stays low and only GPU/Draw jumps, it is rendering (crowd skeletal meshes, overdraw, FX).
   - Small steps only (owner rule for i5). Stop Play after the measurement. Never Simulate with a broken temp Blueprint loaded.
2. **Report the split to Alien in plain words** in the chat (Game / Draw / GPU ms, no wave vs wave, top 5 costs), and write it to
   `handoffs/aaa-472/profile/MEASURE_i5_<date>.md`.
3. **Fix the biggest measured cost first**, same method as E2/E3: live-graph ops through `handoffs/aaa-472/ops/graph_ops_ue.py`
   (ops JSON, `--dry-run`, then on copies with `--apply --nosave --nobackup` via `e2_testcopy_ue.py <new /Game/_i5tmpXXX folder> <tag>`),
   compile clean, push, hand to i9 (`node tools/office.js handoff ...`) and post in the chat. Prime suspects from BP_AUDIT section A/E:
   BP_SoldierSword (each soldier runs 162 exec nodes every frame, FocusCheck tag scan), the 11-level HUD chain DrawHUD (~330 exec nodes always),
   BP_HalfHorseZombie / BP_RealmWasp Think every frame (needs the intended numbers), FX spawns with no pooling, the CharacterMovement of 84 zombies.

## Traps on i5 (learned the hard way)
- No material-instance edits on i5 (Multi-User autosave re-entered ticks and froze the editor).
- Never delete a temp Blueprint and then call ListAvailableNodes in the same editor session (fatal crash). New temp folder per test.
  Temp copies to delete only right after a restart: /Game/_i5tmpC1, _i5tmpK1, _i5tmpF1, _i5tmpE2, _i5tmp472, _i5tmpE2c, _i5tmpE2d, _i5tmpE3a, _i5tmpE3b, _i5tmpE3c.
- In Multi-User, saved assets go to the session sandbox, not Content: use `--nobackup` for temp copies.
- i5's map is NOT i9's map: i9 works offline and saves on his PC. Compile/link tests on i5 prove the graph edit, not the result in i9's game.
- Windows: a second python HTTP server can bind a port that is already in use (test servers on 8799 doubled up). Stop old ones first.
- Grass speed work: the owner said no. Don't restart it. Real carved castle stone stays; never bake it back for fps.

- **Temp test copies + live session = crash (11-04 18:09).** When i9 saves a Blueprint (BP_SoldierSword, BP_Zombie), the session makes i5 ReloadPackage it; temp copies of it on i5 (/Game/_i5tmp*, copies made by graph_ops --copy, Zc0/Zc1, X472c) cannot be re-linked and the editor crashes in CoreUObject. After a pre-check: restart the editor and move the _i5tmp* folders out of Content (they are in C:/UnrealProjects/CD58_i5_temp_tests_moved_1104 now). Better: make test copies only while NOT joined to the session.

## Waiting on i9 (not your task, but don't redo it)
E2 (5 scripts, GitHub hand-off 490) and E3 (4 scripts, hand-off 491) to apply; #488 merlons (waiting for Alien's look OK); #491 stone kit
`dump_wall_xforms_ue.py` then `layout_kit491.py --xforms wall_xforms.json --deck 680`; the chat server swap
(`/files/124517_duo_chat_24h_archive_i5.py`). The E3 chat post may not have gone out (server down): repost it if the chat is back.

## Done looks like
A measured split (Game / Draw / GPU, no wave vs wave) posted for Alien, the top costs named, and at least the biggest one fixed as a
pre-checked script handed to i9, with the expected and (after i9 applies) the measured ms gain. Tick the desk on start / done / blocked.
