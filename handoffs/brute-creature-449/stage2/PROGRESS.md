# #449 stage 2: a new creature animation set for the Flesh Brute (live progress log)

Owner order (2026-11-06): *"i want stranger things netflix series quality"*, then option 2: new source motion made
for this body, not retargeted human zombie clips. The owner also asked: *"document and upload every 10 minutes so
other agent can pick up and complete if u ran out of tokens"*. This file is updated and pushed at every checkpoint.

Seat: `adjustedfilm (Claude)` on the i5 laptop (`C:\Users\hossam.rabea`). Stage 1 (the #449 layer, `../README.md`)
is handed off as #515.

## Plan

| Stage | Clips | State |
|---|---|---|
| 1 | Pipeline round-trip; **heavy walk** at the game speed (71.5 cm/s, in place); **living idle** | **done, waiting on the owner's review** |
| 2 | Threat roar, charge/run, 2 attacks | **done** (owner: "Good, do stage 3") |
| 3 | 3 hits (front / left / right), 2 deaths (forward slam, side collapse) | **done, waiting on the owner's review** |
| 4 | Handoff: import script (new assets in `FleshBrute/Anims_Creature/`), blend-space and BP swap with dry-run and backup | todo |

After the import, the #449 layer (`../fb449_creature_ue.py`) can run on the new clips too (jaw, flesh, heft).

## Pipeline (how to continue on this laptop)

All private work is in `C:\Users\hossam.rabea\ckw\`. It is never committed, because the mesh is licensed:
- `fblab\`: a scratch UE 5.8 project with a COPY of `/Game/CastleDefender/Characters/Enemies/FleshBrute`. It is not the
  game. Headless: `UnrealEditor-Cmd.exe fblab.uproject -run=pythonscript -script=<py> -unattended -nop4 -nosplash -NullRHI -stdout -FullStdOutLogOutput`.
  In Git Bash, prefix with `MSYS_NO_PATHCONV=1` when env vars hold `/Game/...` paths.
- `fbtools\fbx_mesh\SK_FleshBrute.fbx`: the brute exported by UE. The skinned mesh needs the GUI editor:
  `UnrealEditor.exe fblab.uproject -ExecutePythonScript=export_mesh_gui.py`, because headless asserts on MeshObject.
- `fbtools\fbx_before\*.fbx`: the original clips, exported from `Anims_BAK449`.
- Blender 4.5: `C:\Program Files\Blender Foundation\Blender 4.5\blender.exe -b -P <script> -- args`.

Tools (copies in `tools/`; the working copies are in `ckw\fbtools\`):

| File | What |
|---|---|
| `bl_rig.py` | Blender: `load_rig(SK.fbx)`, `apply_anim_fbx(arm, anim.fbx)`, `export_anim(arm, out.fbx)` with the settings that round-trip exactly |
| `bl_roundtrip.py` | the round-trip test |
| `ue_import_anims.py` | UE: imports FBX clips onto `SK_FleshBrute_Skeleton` into `Anims_Creature/` (env `FB_IMPORT`, `FB_DEST`) |
| `ue_compare.py` | UE: compares two clips bone by bone (env `FB_A`, `FB_B`) |
| `export_fbx.py`, `dump_fb.py`, `analyze.py` | export clips to FBX, dump poses to JSON, measure jaw / flesh / bob / pops |
| `render_mesh.py` | Blender: before/after render on the real mesh (views `frontS`, `faceS`, `threeq`, `side`; `mp4` or frame list) |
| `calib_jaw.py` | jaw calibration renders (closed = 50°) |

## Rig facts (measured)

- 87 bones. `Monster_001` → `root` → `spine_01` (pelvis) … `spine_04` → `neck` → `head` → `jaw` → `tongue_03/02/01`.
  Flesh bones: `belly_C/L/R` and `side_L/R` on spine_01, `breast_L/R` on spine_04, `butt_L/R` on spine_01.
  Legs: `thigh_01/02`, `shin_01/02`, `foot`, `toe`. Arms: `shoulder`, `upper_arm_01-03`, `forearm_01-03`, `hand`, fingers.
- In the Blender import the armature object is scale 0.01 (bones in cm). The creature faces −Y and Z is up. Head height is
  about 1.75 m in the rest A-pose (2.28 m mesh).
- The jaw at rest is the showcase gape. It is closed at 50° of closing.
- Game: MaxWalkSpeed 71.5. The ABP blend space `Anim/BS_FleshBrute_Locomotion` has Speed 0–120. The clips are 30 fps, in place
  (no root motion).

## Log

- **07:32** Round-trip proven: UE FBX → Blender (`bl_rig`) → FBX → UE import. Worst error over every bone and frame is
  **0.0005° / 0.0004 cm**. Blender exports one more frame than UE had, so loops are authored with the last frame = the first.
  Next: the IK leg rig and body-space posing helpers in `bl_rig.py`, then the heavy walk.
- **07:58** Rig facts: the leg is a **dog-leg** chain (hip = thigh_01 head, knee = shin_01 head, a second lower segment
  shin_02, ankle = foot head 18 cm up and behind, toe on the ground). The FBX bone tails point back toward their parents, so
  **Blender's IK constraint is unusable (≈40 cm error)**. `bl_pose.leg_ik()` is an analytic two-bone IK on the real joints:
  0.0 cm error, zero toe drift, knees forward. `bl_pose.rot()` rotates a bone about a world axis; `+X` is the brute's left,
  `-Y` forward, `+Z` up. A positive rotation about `+X` leans forward.
- **08:05** `author_walk.py` → **CR_Walk_Heavy**: 46 frames = 1.53 s, in place, matched to 71.5 cm/s (planted-toe speed
  error 0.00 cm/s, so no skating). Stance 65 %, 12 cm lift, 9 cm crouch, 5.5 cm impact dip with a slow recovery, 5.5 cm sway,
  pelvis yaw 6° and roll 4°, chest counter-turn, lean 29°, heavy late arm swing, head stabilised. The jaw stays at rest on
  purpose, because the #449 layer drives it later. Imported into `fblab` `Anims_Creature/CR_Walk_Heavy` OK.
- **Preview gotcha:** a Blender-written FBX re-imported into Blender does NOT drive the UE-exported mesh correctly
  (different rest orientations). Preview only from a **UE re-export** (`export_fbx.py` with `FB_CLIPS=Anims_Creature/<clip>`
  `FB_OUT=...`), then `render_mesh.py`. `preview/walk_v1_sideq_006.png` is the first good frame.
- Next: an mp4 of the walk for the owner, then `author_idle.py` (the living idle), the same way.
- **08:20** `author_idle.py` → **CR_Idle_Hunt** (4 s loop): heavy 2 s breaths, a weight shift on planted feet, a slow scan, a
  head-tilt twitch (fast in, hold, slow out), a double sniff and a claw flex. v2 has a deeper crouch (35°) and the head
  levelled. Imported OK.
- `fb449_creature_ue.py` now takes `--src Anims_Creature`, so the #449 layer (jaw, tongue, flesh, heft) runs on the new
  clips too. Its blend-space edit only runs for the original `Anims` set. **For previews, run the layer first**: the rest
  pose is the showcase gape, so raw clips look like the brute screams at the sky. When re-authoring, delete
  `Anims_Creature_BAK449` first, or the layer bakes from the stale backup.
- **08:28** Walk v1 bug, found by the layer's de-pop and `ue_pops.py`: the knees snapped 34°/frame because the trailing
  leg locked straight (178°) in late stance. Fixed in **walk v2**: cycle 52 frames (1.73 s), stance 60 %, stride centred
  15 cm forward, crouch 12 cm, heel lift 12°. Checks printed by the script: knee angle 82–134° (never locked), worst bone
  turn **7.8°/frame** (target < 15), planted-toe speed error **0.00 cm/s**.
- Next: import walk v2 + idle v2, run the layer (`--src Anims_Creature`), re-export from UE, render the mp4s for the owner.
- **08:40 STAGE 1 DONE.** Walk v2 and idle v2 imported into `fblab` `Anims_Creature/`, the layer applied (`--src Anims_Creature`),
  re-exported from UE and rendered: `preview/CR_Walk_Heavy_v2_vs_FB_A_Run.mp4`, `preview/CR_Idle_Hunt_v2_vs_FB_ZA_Idle_A.mp4`.
  In UE (`ue_pops.py`) **0 bones over 12°/frame** in both, and the layer found two footfalls per walk cycle (frames 5, 31).
  Shown to the owner; next is stage 2 (roar, charge, 2 attacks) after the owner's feedback.
  **How to continue stage 2:** copy `author_idle.py` as the template (per-frame `pose_frame(f)` → `P.key`), keep the feet on
  `P.leg_ik`, check with the built-in knee/snap prints, import → layer `--src Anims_Creature` → `export_fbx.py` → `render_mesh.py`.
  Attacks: keep the strike readable, anticipation ≥ 0.4 s, strike 3–5 frames, a long settle (RESEARCH.md: Gilman).
- **08:55 Stage 2 started.** New `bl_perform.py`: pose-to-pose authoring with **per-channel curves** (a key only moves
  the channels it names; the first key is `BASE`, the idle's base pose), eases `smooth / in / in2 / out / inout / snap /
  linear`, per-group lags for overlap (head 0.09 s, elbows 0.10 s, hands 0.13 s, claws 0.16 s) and a 9–14 Hz tremble channel.
  `perf_stage2.py` holds the key poses; author with `author_oneshot.py -- <SK.fbx> roar|slam|swipe <out.fbx>`.
  - **CR_Roar_Threat** (3.0 s): gather (sink, curl, fists) → explode up (chest arched, arms flung wide, claws spread) → a
    trembling roar hold with a head sweep → settle to the base pose. Worst bone turn 9.3°/frame.
  - **CR_Attack_Slam** replaces FB_A_Attack: **same length 79 frames, hit at frame 26** (BP damage timing kept). Step in,
    arms overhead, a held breath, a 6-frame overhead slam, the mass keeps dropping on impact, a shudder, step back. The
    fastest bone is on the blow (35°/frame).
  - **CR_Attack_Swipe** replaces FB_ZA_Attack_D: **same length 60 frames, hit at frame 14**. The torso cocks right with
    the claws spread, a 5-frame whip across, a head lunge (bite), follow-through. 45°/frame on the strike.
  - Lessons: a cubic ease-in on the strike crams it into one frame (100°/frame = a pop) → use `in2` over 5–6 frames.
    Keys that did not name a channel used to freeze it (an 80° catch-up jump) → fixed by the per-channel curves.
  - TODO: the #449 layer must **skip de-pop and retime for CR_ clips** (they are authored; de-pop would flatten the strikes).
  - Next: CR_Charge (author_walk.py with the `CR_OVR` env JSON overrides + `CR_NAME`), then import all, layer, render.
- **09:10** **CR_Charge** (`CR_NAME=CR_Charge CR_OVR='{"SPEED":170,"N":32,"STANCE":0.42,"LIFT":0.15,"CROUCH":0.14,"FWD_BIAS":0.17,"DIP":0.08,"RISE":0.03,"SWAY":0.04,"YAW":9,"ROLL":5,"LEAN":[16,14,10],"COUNTER":0.6,"NOD":5,"ARM_IN":18,"ELBOW":38,"ARM_SWING":28,"ARM_LAG":0.08,"FORE_SWING":14,"FORE_LAG":0.13,"TOE_OFF":16}' author_walk.py`):
  1.07 s cycle at 170 cm/s, zero skate, knees 60–152°, worst 17°/frame (normal for a running knee).
- The layer now knows the new clips (`fb2_layer.classify`: roar → the roar jaw, charge → loco). **CR_ clips skip de-pop and
  retime.** All 6 CR clips imported into `fblab` `Anims_Creature/` and the layer run with `--src Anims_Creature`. Strike
  frames found: slam **26**, swipe **15** (as designed), so the jaw snaps on the blows. Footfalls found in the charge (13, 29)
  and the walk (5, 31).
- Note: `Anims_Creature/RT_Idle_A` is the round-trip test clip; **leave it out of the handoff**.
- **09:20 STAGE 2 DONE.** mp4s in `preview/` (slam, swipe, roar, charge), shown to the owner. Next: stage 3 (3 hits, 2 deaths) after the owner's review.
- **09:35 Stage 3 authored** (`perf_stage2.py`: `hit_front`, `hit_left`, `hit_right`, `death_fwd`, `death_side`; `author_oneshot.py`):
  - **CR_Hit_Front/Left/Right** (0.9 s): react from frame 0 with a 3-frame snap away from the blow, knees buckling, the
    head and arms whipping a beat later, and a heavy recovery to `BASE`. Worst 21–27°/frame (the old hit clips: up to 99°).
  - **CR_Death_Forward** (3.0 s): killing blow → knees buckle → a kneeling beat → topples onto the belly (an accelerating
    `in`) → slam with a tremble → a small rebound → a death twitch of the claws. It holds the last frame. 14°/frame.
  - **CR_Death_Side** (2.6 s): struck from the left → the legs give → topples onto its right side; the left leg lifts with
    the falling body. 35°/frame at the ground impact only.
  - New `foot_free` channel (1 = the feet go limp and follow the legs in falls). `bl_pose.leg_ik(n_hint=...)` keeps the
    knee plane turning with the pelvis, so a folded leg never flips.
  - **Metric fix:** the snap check reported quaternion sign flips as ~300°; it now uses min(a, 360-a).
- Next: import the 5 clips + run the layer (`--src Anims_Creature`), export from UE, render, push, show the owner; then
  stage 4 (the Master handoff: import script, BS/BP swaps with dry-run + backup, roar trigger).
- **09:55 STAGE 3 DONE.** All 5 imported into `fblab` `Anims_Creature/` and layered (hits get the slack jaw drop, deaths
  the slack open jaw). Side death v2: the top arm and leg flop down under gravity (v1 had a stiff arm pointing at the sky).
  Previews: `preview/CR_Hit_Front.mp4`, `CR_Hit_Left.mp4`, `CR_Death_Forward.mp4`, `CR_Death_Side.mp4`
  (CR_Hit_Right is the mirror of Left). Known tunable: in the side death the top leg still sprawls a little.
- **Clip set in `fblab/.../FleshBrute/Anims_Creature/` (11):** CR_Idle_Hunt, CR_Walk_Heavy, CR_Charge, CR_Roar_Threat,
  CR_Attack_Slam, CR_Attack_Swipe, CR_Hit_Front, CR_Hit_Left, CR_Hit_Right, CR_Death_Forward, CR_Death_Side
  (+ RT_Idle_A = the test clip, exclude). FBX sources: `ckw/fbtools/authored/CR_*.fbx`.
- **Next = stage 4, the Master handoff:** a script that imports the 11 FBX into the game's `FleshBrute/Anims_Creature/`
  (the FBX contain only skeleton animation and no licensed mesh, so they can live in the repo), runs the layer
  `--src Anims_Creature`, rebuilds `BS_FleshBrute_Locomotion` (Idle_Hunt 0 / Walk_Heavy 71.5 / Charge 170, with a backup)
  and swaps the BP's FB_* references to the CR clips (dry-run + backup; BP_FleshBrute EventGraph export needed for the
  hit/death/roar wiring).
- **10:20 STAGE 4 handoff built:** `stage2/fb449_stage2_ue.py` (dry-run / install / `--restore`) + `README.md` + `fbx/` (11 clips).
  It imports → layers → writes the CR clips INTO the FB_* clips the BP plays (13 targets, backups in `Anims_BAK449S2`)
  → blend space idle 0 / walk 71.5 / charge 170 (axis max 180, backup `BS_..._BAK449S2`).
  Tested in `fblab`: install 13/13 exact; restore exact (lengths too). **Bug found and fixed:** `get_num_frames` counts
  intervals (keys = n + 1); copies were one frame short and stage 1 never wrote the last key. Both scripts now read and
  write n + 1 keys and set the length. Stage 1 also gets a guard: it skips clips tagged `FB449S2` unless `--force`.
- Open: wiring CR_Roar_Threat (roar on first sight), CR_Death_Side (random death) and directional hits needs the
  BP_FleshBrute export (request filed).
