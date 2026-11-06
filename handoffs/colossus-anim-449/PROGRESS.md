# #519 zombie animations, colossus first (live progress log)

Owner order (2026-11-06, to `adjustedfilm (Claude)` on the i5): *"i want to enhance zombies animations accordingly ...
specially clossals"* (accordingly = the #449 brute method). Pushed at every checkpoint so another agent can pick it up.

Seat: `adjustedfilm (Claude)`, i5 laptop (`C:\Users\hossam.rabea`). Private work: `C:\Users\hossam.rabea\ckw\ztools`
(tools, UE exports of the originals, the licensed `fbx_mesh/SK_Zombie.fbx`, `authored/`, `preview/`) and the scratch UE 5.8
project `ckw\zlab` (a copy of `Content/CastleDefender/Characters/Enemies/Zombie` from the i5 copy of the game at
`C:\UnrealProjects\Castle Defender 5.8`). Never committed (licensed mesh). Tool copies: `tools/`.

## Plan

| Stage | What | State |
|---|---|---|
| 1 | Colossus: giant walk (into A_Walk + stomp notifies), smash (drop-in for A_Attack in the breaker), giant death | **done, handed off** (install script tested in the lab) |
| 2 | Wiring paste: smash pin, death override for the breaker (needs export #518) | waiting on #518 |
| 3 | The walkers: BS_Zombie_Locomotion clips at their measured speeds (ZA_Idle_A 0 / ZA_Walk_A 113 / ZA_Run_A 249 / A_Run 350), hits, deaths | next |

## Pipeline (how to continue)

Same shape as the brute's (`../brute-creature-449/stage2/PROGRESS.md`), rig-specific parts rewritten:

| File (`tools/`) | What |
|---|---|
| `zrig.py` | Blender: `load_rig(clip.fbx)` (a UE CLIP export is the authoring rig), `key()`, `export_anim()` (exact round-trip settings) |
| `zpose.py` | world-axis bone rotation, pelvis ops on the armature OBJECT, analytic 2-bone leg IK (`UpLeg -> Leg -> Foot`), finger curl about the finger's local X |
| `zperform.py` / `zperf.py` / `zoneshot.py` | pose-to-pose engine (per-channel curves, eases, lags x1.6 for the giant, tremble), the key poses (smash, death), the one-shot author |
| `zwalk.py` | the gait engine, defaults = the colossus walk (`Z_OVR` JSON overrides, `Z_NAME`) |
| `zprobe.py`, `zmeasure.py`, `zl_roundtrip.py` | UE clip/notify/blend-space probe; per-clip ground / hips / blow-frame measure from the FBX; the round-trip test |
| `ue_import_anims.py`, `export_fbx.py`, `ue_compare.py`, `ue_pops.py`, `run_headless.sh` | UE side (env `Z_IMPORT`, `Z_DEST`, `Z_CLIPS`, `Z_OUT`, `FB_A`/`FB_B`) |
| `zrender.py` | before/after on the real mesh (views `threeqS`, `frontS`, `side`, `sideq`, ...; frames or mp4). **Only from UE re-exports** |

Loop to make or tweak a clip: edit `zperf.py` / `zwalk.py` -> author (Blender, read the PERF line: snaps < ~15 deg/frame except
strikes, knees never ~180) -> `ue_import_anims.py` (into `Anims_Colossus`) -> `export_fbx.py` (`Z_CLIPS=Anims_Colossus/<clip>`)
-> `zrender.py`. Then copy to `fbx/` and push.

## Rig facts (measured)

- `SK_Zombie`: 73 bones, Mixamo names (`Hips`, `Spine/1/2`, `Neck`, `Head`, `Left/RightShoulder/Arm/ForeArm/Hand` + 15 finger
  bones per hand, `UpLeg/Leg/Foot/ToeBase/Toe_End`, `Back/FrontCloth1-4`). Faces -Y, Z up, +X is its LEFT (same as the brute).
- **Blender gotcha:** UE's FBX export makes the root bone `Hips` the ARMATURE OBJECT. In a clip export the armature is
  parentless, scale 0.01, location in METRES; the pelvis animation is the object's `location` / `rotation_euler`, so the
  brute's loader (which strips object keys) loses the hips. In the MESH export the same armature sits under an empty
  `SK_Zombie` (scale 0.01) with its location in cm. Authoring is done on a clip armature; `zrender.py` frees the mesh's
  armature from the empty before putting a clip on it.
- Bind pose: T-pose (arms along +-X), legs straight, hips at z 1.167 m, ankle 14.5 cm up, toes on z = 0. The original
  `A_*` clips sit on z = 0; the retargeted `ZA_*` clips have their toes 5-13 cm under it.
- Finger curl = **positive** rotation about the finger's local X (tested both signs on the mesh).
- `A_Attack`: 79 frames, the blow (hands at 5.7 m/s) on frame 26. `A_Walk`: 121 frames, 1.2 m steps at scale 1, two
  `AN_ColossusStomp` notifies. `A_Death` 89 frames. `A_Run` 24 frames (0.8 s).
- Breaker (export 11-03): `BP_Walk` PlayAnimation A_Walk (loop) -> ... smash: `SM_Face` -> `SM_Rate` (GlobalAnimRateScale
  **0.45**) -> `SM_Anim` PlayAnimation A_Attack -> `SM_D1` delay -> ... `SM_D2` -> `SM_Rate2` -> `SM_Walk` (A_Walk again).
  Capsule 45 / GiantScale (#317), smash within 380 cm. GiantScale 3.9-5.8, MaxWalkSpeed 90.
- UE 5.8 Python has no `AnimationLibrary.get_frame_rate` and no notify trigger-time getter; notify names and classes read fine.

## Log

- **08:20** Found the targets: the colossus = `BP_ZombieWallBreaker` (child of `BP_Zombie`, the zombie rig at GiantScale
  3.9-5.8, MaxWalkSpeed 90, PlayAnimation A_Walk / A_Attack at rate 0.45). The walkers run `ABP_Zombie` + `BS_Zombie_Locomotion`.
  Request **#518** filed for fresh exports of BP_ZombieWallBreaker + BP_Zombie (the repo copies are from 11-03, before the
  C++ `AZombieBase` reparent). Scratch lab `ckw\zlab` built from the i5 copy of the game; 16 original clips + the mesh exported.
- **08:30** Round-trip proven on `ZA_Walk_A`: worst **0.00007 deg / 0.002 cm** (after fixing the Hips-as-object gotcha above).
  Blender writes one key more than UE's interval count, as with the brute.
- **08:35** `zwalk.py` -> **CZ_Walk_Colossus**: 78 intervals (2.6 s, a step every 1.3 s = sqrt(4.85) x a human step), feet
  matched to 90 cm/s at x4.85 (18.6 cm/s at scale 1), skate error 0.01 cm/s, knees 109-129, worst 4.4 deg/frame. Stance 66 %,
  lift 7 cm, crouch 12 cm, dip 4.5 cm with a 0.12 s drop / 0.30 s recovery, sway 6 cm, yaw 8, roll 6, lean (16, 13, 10),
  arms hang 70 deg from the T-pose with 32 deg elbows, swing 10 lagging 0.12 of a cycle, claws 18. v1 was too upright with the
  head up; v2 hunched it and looks down at the prey. In game the giant is x4.85: 30 cm sway, 1.6 m steps.
- **08:40** `zperf.py` -> **CZ_Attack_Smash** (79 frames, blow at 26 like A_Attack): v1 spread the arms overhead and swept
  the hands behind the knees; v3 gathers the arms together overhead (arm_in 72) and lands the blow horizontal-forward
  (arm_sw 95, the wall face), 36.9 deg/frame on the blow only. **CZ_Death_Colossus** (121 frames, 4 s): v1 ended kneeling-prone;
  v2 stretches the legs behind (feet -0.34 / -0.28 m, hips 0.40 m forward, 0.72 m down) into a flat sprawl. 14.2 deg/frame.
- **08:45** Finger curl sign tested on the mesh (`CZ_Test_Claw`: +50 hyper-extends, -50 grasps) -> curl is +X local; fixed
  in `zperform` and `zwalk`. mp4 previews rendered (walk, smash, death; before | after on the real mesh).
- **08:50** Install script `cz_colossus_ue.py` (dry-run / install / restore) tested in the lab: 3 imports, `A_Walk <-
  CZ_Walk_Colossus` with `max_diff_deg 0.0`, notifies `[AN_ColossusStomp, AN_ColossusStomp]` at 0.0 / 1.3 s on a `Stomp` track.
  Restore: see the next line. Card **#519** opened and claimed.
- **08:50** Restore tested: `--restore` puts `A_Walk` back (121 frames, 4.033 s, worst 0.0003 deg vs the backup, notifies
  back); a second install matches the authored clip to 0.00006 deg. **Handed off** (script + README + 3 FBX + 3 mp4).
- Next: stage 3, the walkers (probe `BS_Zombie_Locomotion` speeds vs the clips' natural speeds, then author idle / walk /
  run / hits / death the same way), and the smash + death wiring when #518 lands.
- **09:15 Stage 3 started (the walkers).** Pops measured in UE (`tools/zpops_all.py`): ZA_Taking_Damage_A-F pop 90-173 deg/frame
  on 38-43 bones in frames 1-3; ZA_Run_A / A_Run pop the toes 37-39 deg with the feet 13 cm under z = 0; A_Death 45 deg;
  ZA_Attack_D 46 bones. The blend space samples (0 / 113 / 249 / 350) already match the clips natural speeds (i9, 11-02).
  Strike frames: A_Attack 26, ZA_Attack_D 16 (hands fastest). Ground for the walkers = -0.05 (the ZA idle's toes).
- **09:30** `zwalk.py` got GROUND, ARM_SW_BASE (constant reach), LIMP (the right leg drags: 25 % lift, 2.2x drop, a hip
  hitch, the toe stays down) and LOLL. `zidle.py` = the walkers' idle. v1 of the walk/run/sprint used a too-long stride
  (the cadence was too slow for the speed: D = speed x cycle x stance must stay under about 0.7 m or the knee locks at 178):
  v2 cadences 1.0 / 0.67 / 0.53 s -> knees 100-140 / 83-156 / 76-152, 0.00 cm/s skate, worst turn 11.5 / 21 / 29.
- **09:40** `zperf_walkers.py` (hits x4, death, attacks x2) authored with `zoneshot.py` (lag scale 1.0 for a human body).
  Renders: the claw rake first spread both arms sideways at the blow (the chest twist takes the trailing arm out); made it a
  deliberate one-arm rake (left arm winds up behind, 0.92 m ahead at frame 30, the right arm low). The bite first raised the
  hands overhead (arm_sw 78 in world with the torso bent 60 deg forward points up): 55 / arm_in 84 grabs at chest height.
- **09:50 STAGE 3 DONE.** 11 clips in `fbx/`, 11 mp4s in `preview/`. `zw_walkers_ue.py` tested in the lab: dry-run, install
  (14 targets written, every `max_diff_deg` 0.0, `ZA_Walk_A` with 2 stomps), restore (0.00005 deg vs the backups), reinstall.
  Handed off. Open: the smash pin + death wiring for the breaker (export #518 not landed yet); the 11 burst-based death picks.
- **10:05 Export #518 landed** (BP_ZombieWallBreaker, BP_Zombie, ABP, BS; 09:24). Breaker graph unchanged since 11-03 except
  the #317 merge. Two findings: (1) the breaker sets **GlobalAnimRateScale 0.2** at BeginPlay (BP_Rate) and after each
  smash (SM_Rate2): the human A_Walk was slowed 5x to hide its 1.2 m steps; (2) **MaxWalkSpeed = 30 x GiantScale**
  (117-174), not 90. So CZ_Walk_Colossus is re-authored at **30 cm/s at scale 1** (the feet then match at every size at
  rate 1): 5.1 deg/frame, knees 106-133, 0.01 cm/s skate; fbx + mp4 replaced. BP_Zombie now parents the C++ ZombieBase;
  its death runs inside the AnyDamage handler: SetAnimationMode(AnimationBlueprint) + one of 12 Montage_Play (CX_123
  picks), and the C++ candle melt hides the mesh ~2.3 s after death (cd.Zombie.CandleMelt).
- **10:20 Wiring paste built** (`gen_cz519.py` on bpkit): rate 1.0 after BP_Rate and after SM_D2 (replacing the 0.2),
  PlayAnimation(CZ_Attack_Smash) between SM_Rate and SM_D1, and an AnyDamage override (Parent -> if Dead and not
  GiantDead -> GiantDead = true, rate 1.0, PlayAnimation(CZ_Death_Colossus); PlayAnimation puts the mesh back in
  single-node mode so the giant death replaces the montage from frame 0). New var GiantDead (VARIABLES.md). Pre-checks:
  fix_impure (no change), applyall merge on the #518 EventGraph (`t3d_eventgraph.js` flattens a whole-BP export into
  the clipboard layout applyall reads): Validation OK, 24 nodes, 6 rewires, +54 link entries as expected
  (`merged_cz519.t3d`). Handed off. Tool: `tools/t3d_nodes.js` lists any export's nodes with their links.
- **10:50 Stage 4: real deaths.** Owner: "start 1 and 2". (2) ZA_Attack_A/B/C are played by no Blueprint (only A_Attack and
  ZA_Attack_D are), so nothing to fix there. (1) Three more deaths authored (`zperf_walkers.py`: ZW_Death_Back / Side /
  Crumple, 89 frames each; 20-40 deg/frame on the snaps only). The parent's death pick: 12 `Montage_Play` nodes behind
  an if-chain (CX_123..CX_165 -> K2Node_CallFunction_10..21 -> ZB76); 11 of them play blob-rise clips. Tried re-pointing
  the montages by script: the montage keeps its old length (SequenceLength is read-only from Python) and headless
  `delete_asset` / `consolidate_assets` do not persist, so that road is dropped. Instead: `zw_deaths_ue.py` creates 4 new
  montages with the factory (correct length, DefaultSlot; new assets only) and `gen_zd519.py` makes a BP_Zombie paste
  that bypasses the 11 old nodes with new ones (manifest_zd519.json: 11 nodes, 33 rewires; merge on the #518 EventGraph
  via `t3d_eventgraph.js`: Validation OK, +44 entries as expected, `merged_zd519.t3d`). Lab: montages built from the right
  clips (2.97 s each). Handed off.
- **11:40 Stage 5: crawlers, the spawn rise, the knock-down** (owner: "fix 1"). Measured: the crawl loops' planted hands
  move about 50 cm/s against MaxWalkSpeed 45 (CX_320), and pop 21-27 deg; the spawn rise is `ZA_Burst_H` played by
  Ps_CX_428 / Ps_CX_446 at GlobalAnimRateScale 0.5 with a 5.4 s / 2.8 s wait: the clip pops from the rest pose onto the
  ground in 5 frames and then lies MOTIONLESS for 85 (the "dead pause" of #164). The other bursts (A-K) are only death
  montages. `ZA_Laying_Idle_A` (after LaunchCharacter) pops 124 deg. `zpose.py` got `arm_ik` / `chain_ik`; `zcrawl.py`
  places the hands by IK and matches 45 cm/s exactly (0.00 skate; REACH 0.84 keeps the IK inside the arm's reach);
  `ZW_Crawl_B` is a one-arm-drag variant. `ZW_Rise` (90 f, pose-to-pose from a PRONE base): head lifts -> push-up ->
  one knee, the foot plants -> standing by frame 78 (x0.5 in game = 5.2 s). `ZW_Laying_Stunned` (180 f). Install
  `zw_crawl_rise_ue.py` writes the 4 clips into ZA_Belly_Crawling_A/B, ZA_Burst_H, ZA_Laying_Idle_A (lab: 4 x 0.0 deg,
  restore 0.00004 deg). No paste. Handed off.
