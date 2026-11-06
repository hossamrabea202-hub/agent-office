# #546: what was tested, and how

Lab = `ckw/zlab`, GUI editor, **Simulate** on an empty map with a test floor and wall. Animation really ticked and shaders really compiled. Hits were real `ApplyDamage` calls from a script.

## Passed in the lab

| Check | Result |
|---|---|
| Install script, no stubs | compile True, 0 errors, 1012 nodes, saved |
| Install with stand-in sounds and FX, so those nodes exist | compile True, 0 errors, 1045 nodes |
| `--dry-run`, then apply with a forced spot (`--at`), then `--revert` | nothing changed / placed 1 / removed 1 |
| Melt, skin, iron, pool and streak shaders | compiled and rendered in Unreal, no shader errors in the log |
| First hit | State 0 -> 1, chain 0 cut, `AM_CH_Slice_L`, then `AM_CH_Free_L` |
| Second hit | State 1 -> 2, `AM_CH_Death_L`, melt 0 -> 1 in 8.5 s, wrist chains let go at 0.30, ankle chains at 0.82, then State 3 |
| Third hit | ignored |
| Right arm | State 1, `AM_CH_Slice_R`, `AM_CH_Free_R`, `AM_CH_Death_R` all played |
| Chain link spacing against the real 8.6 cm pitch | 7.8-11.2 cm across the whole story |
| Runtime errors in the final left-arm runs | none (no Accessed None) |
| Loose cuff | lands at z 5 and stays |
| Arm spread in the thrash loop | avg 72 / 73 deg from hanging; 90 = T-pose, so 80 % |
| Worst joint speed | 36 deg/frame in the thrash; up to 80 deg/frame on the fast free-arm strikes |

## Not tested

- **It has never run in Play, and never on the real level.** The wall and floor traces, the placement in the room and the anchors on real stone have not been run.
- **Never hit by the real sword.** The Hit capsule uses the Pawn profile, and the hero's Sword overlaps Pawn on the i5 copy of the game, which is older than the i9. The hit logic was only driven by script.
- **The claw** on the hero, and all hero-distance logic: Simulate has no pawn.
- **Real sounds, sparks, smoke, blood:** the lab has stand-ins, so these have never played, and volumes are unjudged. The slash wound was built and compiled, but was not checked by eye.
- **The chain break on the right arm.** The right-side clips and states ran; the right-arm chain cut itself only ran on the left (the same code, indexed by side). In the one right-side run, the test harness itself broke the actor's arrays by editing a variable live, which produced Accessed None errors and froze the chains; that came from the harness, not the actor, and no clean right-side run followed.
- **The i9's skin.** The lab's `M_Zombie_Skin_AAA` has no `MF_CD_CandleMelt`. The i9's duplicate will still hold it, unused for WPO, and it could react: Play test 8.
- **Brightness in the room.** Lab light is not game light. `MeltGlow` and `HeatLight` are starting values, and in the lab captures the melt still looks too bright: Play test 9.
- **Frame cost** (`stat unit`).
