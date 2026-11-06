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
