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
| 2 | Threat roar, charge/run, 2 attacks | todo |
| 3 | 3 hits (front / left / right), 2 deaths (forward slam, side collapse) | todo |
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
