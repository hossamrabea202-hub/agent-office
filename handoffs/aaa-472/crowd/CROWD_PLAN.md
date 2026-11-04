# #493 Crowd reshape: 30 fps in battle on i9 (i5 core, 2026-11-04)

Owner's order: "use all of this and reshape the system to be able to operate 30fps on laptop i9".
Target: game thread under 33 ms in a full wave on i9. GPU must fit too (i9 has a T1000; GPU is unmeasured there; on i5 it is 42-75 ms, so GPU is the next wall after the game thread).

**Decision:** the project has no C++ module and no Mass plugins, so Unreal's Mass crowd system (C++) is not used now. Everything below is Blueprint + engine settings,
in small pre-checked scripts for i9. C++ / Mass stays an option for later if i9 has Visual Studio.

## What a zombie costs (measured on i5, Play, editor in front, CSV game-thread groups)
Frame grows in a straight line with the zombie count: 161 ms at 142, 175 at 229, 250 at 314, 380 at 480 (waves kept spawning in Play: **no cap on alive zombies**).
At ~314 zombies, 2 soldiers (each test run between two base runs, everything put back):

| Test | Group change | Saved |
|---|---|---|
| Zombie mesh collision off (all) | movement 47 -> 19, physics wait 21 -> 0, animation 17 -> 6, sync 5 -> 1 | **~92 ms** |
| Mesh collision off only beyond 15 m of player and soldiers (291 of 480) | movement 62 -> 37, physics wait 30 -> 8.5, sync 8 -> 4 | **~55 ms** (at 480) |
| Soldier tick off (2 soldiers) | actor ticks 70 -> 36 | **~34 ms**, grows with zombies |
| HUD not drawn | UI 24 -> 12 | ~12 ms |
| Zombies in NavWalking | unclear (zombie count rose during the run) | ? |
| Mesh overlap events off | already off | 0 |
| Movement / animation tick at 10-15 Hz for far zombies | none: at 6 fps every frame is longer than the interval; and in a gate battle 92 of 162 zombies are near or on screen | 0 now |

Still unmeasured by test but big in the trace: zombie Think timers + zombie Tick (TimerManager 16 -> 89 ms and part of actor ticks as zombies go 160 -> 480).

**Lesson:** "tick less often" does not help until the game is already fast. First cut work that runs every frame for every zombie: collision, soldier loops, Think, HUD.

## Who needs the zombie mesh collision (from the exports)
Bone hits are read by BP_Crossbow, BP_Cannonball, BPC_WeaponKit, BPC_CannonBreak, BP_SoldierSword, BP_HalfHorseZombie, BP_TentacleVitals.
So a zombie the player can see, or one near a soldier, must keep it. Rule: **mesh collision on = on screen (recently rendered) OR within 15 m of the player or a soldier; else off.**

## The budget on i9 (G: i9's CPU is maybe 1.3-2x i5's per core; replace with i9 numbers once measured with the editor in front)
| Item | Now (i5, 140-160 zombies) | Goal |
|---|---|---|
| Soldier AI | ~15 ms per soldier | < 1 ms per soldier |
| Zombie collision + movement + physics | ~40 ms | < 12 ms |
| Zombie Think + Tick | ~25 ms | < 6 ms |
| HUD | ~12-20 ms | < 3 ms |
| Animation | ~9 ms | < 4 ms |
| Everything else | ~20 ms | < 8 ms |
| **Game thread** | **~160 ms** | **< 33 ms** |

## The plan, in order (each step = one script, dry-run, compiled on an i5 copy, handed to i9, measured after)
1. **Done, handed (#492): fix K** soldier AI 15 Hz on screen. Pays once frames are under 66 ms.
2. **Handed (C1, README_C1.md): BPC_CrowdTier** (new component on BP_Zombie and BP_FleshBrute, 4 checks a second, staggered): mesh collision rule above; far + unseen zombies also get movement 4 Hz, animation 2 Hz, health bar hidden. Expected ~40-60 ms at 150-300 zombies.
3. **Handed (C2, README_C2.md): alive-zombie cap on the 2 uncapped spawn paths.** Was: in the wave manager: at most N fully alive (start 120); extra spawns wait their turn at the spawn point. Keeps the frame from growing without limit (480 seen). Changes gameplay a little: owner sees it first.
4. **Handed (C3, README_C3.md): soldier near-zombies list:** every 0.2 s each soldier keeps the zombies within 20 m (from the registry); the per-frame fight loop walks that list, not all zombies. Expected: soldier ~15 ms -> ~1-2 ms.
5. **C4 zombie Think spread:** Think timers get a random start and a lower rate when far / unseen.
6. **Handed part (C5, README_C5.md): ZombieHUD LineOfSightTo -> WasRecentlyRendered.** Still open: early-outs for closed panels; cache the tag scans.
7. **C6 cheaper bodies:** simpler physics asset for the zombie (fewer bodies), CharacterMovement tuning (NavWalking test again with a fixed zombie count), crowd LODs (`profile/crowd_lods_ue.py`, built, not applied).
8. **C7 far crowd as pictures** (only if still short): vertex-animation instanced zombies for the far crowd, real characters only near. Big job.

Measure after each step on i9 with the editor in front: `profile/measure_split_ue.py` and `profile/trace_wave_ue.py`.

## Test rule for every step
Forced wave, fixed camera at the gate, editor in front, note zombie and soldier counts. Compare CSV game-thread groups (`profile/csv_split.js`), not only fps:
the zombie count changes during a run, the groups show where the change came from.

## C2 findings (i5, 11-04 15:40, read-only, i5's older BP_ZombieWaveManager)
- The steady spawn (WaveTick WV_22 > ToSpawn > 0 > WV_26 GetAll zombies > **WV_29: alive < 45** > SpawnActor WV_35) already has a cap of 45 alive BP_Zombie.
- Two spawn paths skip it: wave start WV_114 (inside WV_92 For Each over WV_91 GetAllActorsOfClass, after Set Wave WV_95 / Set ToSpawn WV_105) and the swarm burst CX_30
  (For Loop CX_26, up to Min(...,4) per manager, gate CX_22: near the gate point and every 3rd wave from wave 2). With 6 wave managers these add up.
- **Correction:** the 300-480 zombie runs in my tests came partly from my own ForceNextWave calls on all 6 managers stacking wave starts. Real battles on i9 had ~84.
  Per-zombie costs above still hold; the totals at 300+ overstate a normal battle.
- C2 plan: put the same "alive < cap" check (one shared cap, e.g. 60-80) in front of WV_114 and CX_30; extra spawns go into ToSpawn so the steady path releases them as zombies die.
  Build on i9's current graph (fix A replaced some GetAll with ZombieReg): needs a fresh export or a dry run on i9 first.
