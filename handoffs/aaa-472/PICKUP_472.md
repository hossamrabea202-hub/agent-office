# #472 pick-up note (i5 core, 2026-11-04 ~06:15)

Everything below is pushed.

## Applied by i9 on the real Blueprints (chat 1332-1339, 11-03 night)
Tentacle fix + hit reaction, A + B + C, D: all `compile True`, 0 failures, saved, child classes up to date. **Log: 0 Blueprint runtime errors, AnimBP-mode warnings 678 -> 1.**
**FPS did NOT improve:** 3.9 fps / 85 zombies before; 3.6 and 4.3 after. Correct what I said earlier: the logic work fixed errors and bugs, not frame rate.

## Not confirmed applied: asked i9 in chat 1449
- E brute (`ops/ops_E_brute.json`), F never-made wires (`ops/README_F.md`).
- Tentacle 4: `tentacle_anim_ue.py swap --only Env_CorruptedTentacle_4`.

## FPS: where it stands
i9 calls it GPU-bound on the T1000; that is **not measured yet**. Waiting on i9:
1. `profile/wave_sweep_ue.py` in Play (request filed, chat 1449): each feature off in turn, frame time, plus ProfileGPU table. Only tested on an empty map on i5.
2. Then `profile/crowd_lods_ue.py --apply`, sweep again for before / after. On i5 copies: zombie 7447 verts -> 2232 / 1279 / 747, brute 33724 -> 10028 / 5518 / 3004, knight 37575 -> 10539 / 5777 / 3283. All 3 crowd meshes had ONE LOD. Not applied, not looked at in Play.

Read from the assets (`profile/mesh_stats_ue.py`): zombie material is masked + subsurface profile, 463 PS instructions, 2 sections; knight 5 sections, masked, two-sided, ~345 PS, and each soldier has 30 components. Those are the next suspects, sweep decides.

## #457 tentacles: answered from bone tracks (`tentacle-anim-457/clip_motion_ue.py`)
- No stretch: arm length is 11039 in every clip.
- 02 / 04 / 05's far moves fit their idle clips (i9's numbers are at or near the idle's own limit; 05 is 15 % over, probably sampling). Not strikes, as far as these numbers show.
- Tentacle 4 is frozen because its clip Ripple_Sway000 has zero motion.
- The stretch Alien saw is not explained by bones: if he still sees it now, suspect skin / material (#366) or the strike's FABRIK. Needs his eyes or a camera.
- Polished clips A / B / C still wait for Alien's OK: `tentacle_anim_ue.py swap --dry-run`, `--apply`.

## Lessons (also in memory: i5-graph-python-api)
- UE 5.8 Python edits graphs: `unreal.BlueprintGraphEditor`. Far better than pastes.
- `Simulate` on `/Engine/Maps/Entry` with probe SkeletalMeshActors runs animation for real. It found the tentacle bug.
- **Crash at 22:45 (stack read by the other i5 session):** deleting a temp BP and then calling `ListAvailableNodes` touches its dead class. Fatal. Use a new folder, never delete + rerun in one editor session. The 22:05 crash also followed a temp-copy delete; its exact call is unknown.
- Editing the real BPs in the Multi-User session is refused by the permission classifier. Copies only.
- After a crash the editor can sit on "Restore Packages": stop it, rename `Saved/Autosaves/PackageRestoreData.json`, run `JOIN_LIVE.bat`.
- **Simulate with a broken temp BP loaded = a compile-error modal nobody can click; it froze the editor and dropped Multi-User (23:07).** Delete temp copies and check they are gone first.
- Scanner: `node handoffs/aaa-472/t3d_orphans.js <exports>`, exports via a script of AssetExportTask with a .T3D filename. Unwired impure node = None at runtime, compile only warns (micro-test 23:20). Worth running after big pastes.
- Long bash heredocs get cut off: write files with the Write tool.
- Another i5 session (`local_34eb18ca`) shares this editor's inbox and holds #461, #469, Obsidian skill, #458, #440, #453 + the after-save health check. This session holds the seat ticks, BP_Zombie, BP_ZombieWaveManager, ABP_Zombie. Check `ue_inbox/_log.txt` before a Simulate.

## Editor state
i5 editor restarted 06:00, /Game/_i5tmp472 cleaned. Only temp mesh copies are left there (L1, L2), no Blueprints, so they can't trigger the compile modal. Delete them after the next restart.

## Next, after the sweep
1. Hit stack: camera shake and SC_SwordHit already exist in BP_ZombieHUD; impact layers and hit-stop are in fix C. Left: shake scaled by weapon (HUD is the other session's for #458), physical-animation pulse on the hit bone.
2. Rest of BP_SoldierSword's Tick: 5 soldier and 2 cannon scans; state lives in component positions. Big and risky: only with Play tests.
3. Read the first Play log (`log_health.js`) and profile: they decide what is next. BP_JellyTrailManager checked: it only works while something burns, no fix needed.
5. Additive left / right hit clips need new animation; the existing clips have none.
