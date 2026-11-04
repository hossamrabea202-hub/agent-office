# #487 fix K: BP_SoldierSword AI at 15 Hz on screen (i5 for i9). Script, no paste

Why: measured on i5 (`profile/MEASURE_i5_2026-11-04.md`), BP_SoldierSword's Tick is the biggest Blueprint cost in a wave: ~15 ms per soldier per frame with 142 zombies,
because every frame each soldier loops over all zombies. Fix D slows soldiers only when they are beyond 30 m AND not rendered; in a gate battle they are on screen,
so D picks 0 s (every frame). K changes that 0 s to 1/15 s.

What K does (needs fix D, already on i9):
1. D's rate select (SelectFloat B = 0.2 feeding SetActorTickInterval): A 0.0 -> 0.066667. The script finds it by wiring, not by name.
2. Two counters stepped per tick, which would run 4x slower at 15 Hz (they already run at different speeds on fast and slow PCs), now step per second:
   CX_176 `X - 6` -> `X - 6 x 60 x DeltaSeconds`; CX_579 `Y + 1` -> `Y + 60 x DeltaSeconds`. Same speed as now at 60 fps.
   **Decision:** I assumed the author tuned them at 60 fps (UE's default target; the CSV says targetframerate 60). At today's 3-4 fps these counters now run at their 60 fps speed, which is faster than what you see now.
CharacterMovement is untouched (D keeps it at full rate on screen), so walking stays smooth; Set Actor Rotation in the fight updates 15 x a second.

Steps (editor idle, not in Play):
1. `py C:/Users/hossam.rabea/agent-office/handoffs/aaa-472/ops/soldier_rate_K_ue.py --dry-run` -> must print `fix D rate select: ...` and `check OK`.
2. `py .../soldier_rate_K_ue.py --apply` -> backup `Saved/bak472/BP_SoldierSword.uasset.fixK`, compile, saves only if no new errors. Expect `RESULT compile True | link/value failures [] | new errors []`.
3. Save all; child classes (BP_SoldierXbow) recompile.

Tested on i5: on a copy (`/Game/_i5tmpK487a/X472c`), fix D then fix K, both `--apply --nosave --nobackup`: compile True, 0 failures, 0 new errors, 0 warnings.
Values checked after: select A = 0.066667, CX_176.B = (DeltaSeconds x 60) x 6, CX_579.B = DeltaSeconds x 60. A second run refuses ("K looks applied already").
On i5's real soldier (no D) the script stops and changes nothing. **Not tested on i9's graph and not tested in Play.**

Test (Play, editor in front):
- Soldiers still find, chase and hit zombies, hold formation, man the cannons, go through the sally port.
- Fight facing looks fine (rotation now 15 Hz).
- Whatever CX_176 / CX_579 time (in the fight loop and the formation code): watch that attack rhythm and formation moves look normal.
- Measure: `py .../profile/trace_wave_ue.py` in a wave, before and after; `BP_SoldierSword ReceiveTick` should drop by about half at 30 fps. **No gain while frames are slower than 66 ms.**

Revert: close the editor, copy `Saved/bak472/BP_SoldierSword.uasset.fixK` over `Content/CastleDefender/Characters/Knight/BP_SoldierSword.uasset`, reopen.
Change the rate without reverting: `--rate 0.05` (20 Hz) on a fresh K, or set the select's A pin by hand.
