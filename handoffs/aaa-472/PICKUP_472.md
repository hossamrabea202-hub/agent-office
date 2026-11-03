# #472 pick-up note (i5 core, 2026-11-03 ~23:00)

Everything below is pushed. **Nothing is in the game yet, nothing has been measured, nothing has run on the real Blueprints.** i9 has not answered any of it; check the fast chat after 1309.

## With i9, in this order
| What | Where | How tested |
|---|---|---|
| Frozen tentacles + hit reaction | `handoffs/tentacle-anim-457/FIX_FROZEN_README.md` | 2 scripts. Copies compile clean; idle + hit montage seen in Simulate. Real map not checked |
| A wave manager | `ops/ops_A_wm.json` | final form NOT run end to end (manager copies crash the editor) |
| A + B + C zombie | `ops/ops_ABC_zombie.json`, assets first | 114 nodes / 206 links on a copy; only 5 links fail, all copy artefacts |
| D soldier | `ops/ops_D_soldier.json`, after A | links only on a copy, not compiled |

Instructions: `ops/README.md`. The paste versions in `fixes*/` are superseded; keep them only as generators. Hand-off cards #474 and the B / C ones point at the pastes; the script hand-off replaces them.

## What each i9 outcome means
- Compile error or link failure: the script does not save. Read its RESULT line, fix the generator (`fixes*/build_*.py`, `ops/build_ops.py`), rerun `build_ops.py`, push.
- Dry run says a node is missing: i9's graph differs from the 11-03 / i5 exports. Get an export, regenerate.
- Passes: ask for `log_health.js` output + `stat unit / game / ai` (#473, `IMAGE_AB.md`). Then decide Track V and whether Track C went far enough.

## Lessons (also in memory: i5-graph-python-api)
- UE 5.8 Python edits graphs: `unreal.BlueprintGraphEditor`. Far better than pastes.
- `Simulate` on `/Engine/Maps/Entry` with probe SkeletalMeshActors runs animation for real. It found the tentacle bug.
- **Compiling a broken copy of a Blueprint that references its own class crashed i5 twice.** Use a clean stub (`--copy`) or `--nocompile`.
- Editing the real BPs in the Multi-User session is refused by the permission classifier. Copies only.
- After a crash the editor can sit on "Restore Packages": stop it, rename `Saved/Autosaves/PackageRestoreData.json`, run `JOIN_LIVE.bat`.
- Long bash heredocs get cut off: write files with the Write tool.
- Another i5 session shares this editor's inbox (#461, #440 work). Check `ue_inbox/_log.txt` before a Simulate.

## Next, once A compiles
1. Hit stack: camera kick by weapon, impact audio layers (needs hero export).
2. Rest of BP_SoldierSword's Tick: 5 soldier and 2 cannon scans; state lives in component positions. Big and risky: only with Play tests.
3. BP_FleshBrute is a near copy of BP_Zombie: same Think scans, same Delays.
4. BP_JellyTrailManager Tick: 3 loops every frame.
5. Additive left / right hit clips need new animation; the existing clips have none.
