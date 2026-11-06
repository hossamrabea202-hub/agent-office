# #449 stage 2: a new creature animation set for the Flesh Brute (live progress log)

Owner order (2026-11-06): *"i want stranger things netflix series quality"*, then option 2: new source motion made
for this body, not retargeted human zombie clips. The owner also asked: *"document and upload every 10 minutes so
other agent can pick up and complete if u ran out of tokens"*. This file is updated and pushed at every checkpoint.

Seat: `adjustedfilm (Claude)` on the i5 laptop (`C:\Users\hossam.rabea`). Stage 1 (the #449 layer, `../README.md`)
is handed off as #515.

## Plan

| Stage | Clips | State |
|---|---|---|
| 1 | Pipeline round-trip; **heavy walk** at the game speed (71.5 cm/s, in place); **living idle** | in progress |
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
