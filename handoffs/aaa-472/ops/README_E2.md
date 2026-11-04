# #487 E2: three per-frame zombie scans off the frame (i5 core, 2026-11-04)

Audit rows A7-A9 (`handoffs/vram-482/BP_AUDIT.md`). Each of these ran `GetAllActorsOfClass(BP_Zombie)` plus a loop over about 84 zombies, on every frame:

| Blueprint | What it does | Fix | Behaviour |
|---|---|---|---|
| BP_ZombieVariety | tint + anim-rate variation, only on zombies under 1 s old | `SetActorTickInterval 0.2` at the top of its Tick | same: every new zombie still gets it (5 checks inside its first second), up to 0.2 s later |
| BP_JellyShieldAll | one-time jelly shield, only on zombies under 1 s old | `SetActorTickInterval 0.2` at the top of its Tick | same, up to 0.2 s later |
| BP_HitFeel | hit flash, hit-stop and blade blood: must stay per frame | the loop reads the host manager's `ZombieReg` (fix A) instead of scanning the world; CX_2 removed | a zombie younger than 1 s (not yet in ZombieReg, which refreshes at 1 Hz) gets no hit flash or hit-stop. Everything else the same |

Gain: about 12x fewer scans for the first two at 60 fps, and one world scan less per frame for HitFeel. Unmeasured, like all of the audit. Read the speed test before you expect fps from it.

## Steps (i9, editor idle, not in Play, `git pull` first)
HitFeel needs fix A on BP_ZombieWaveManager (you applied it 11-03). For each of `variety`, `shield`, `hitfeel`:
```
py <repo>/handoffs/aaa-472/ops/graph_ops_ue.py <repo>/handoffs/aaa-472/ops/ops_E2_variety.json --dry-run
py <repo>/handoffs/aaa-472/ops/graph_ops_ue.py <repo>/handoffs/aaa-472/ops/ops_E2_variety.json --apply
```
Expect `check OK`, then `RESULT compile True | link/value failures [] | new errors []` and `saved True`. Anything else: don't save, restart without saving, send i5 the output.

## Tested on i5 (copies in /Game/_i5tmpE2c, real graphs from the live session, a stub manager with ZombieReg)
- The live graphs match: CX_1.then -> CX_2 (Variety, Shield); CX_7.then -> CX_2 -> CX_8 ForEach (HitFeel). Probe: `probe_e2_ue.py`.
- All 3: `check OK`, `compile True`, 0 failures, 0 new errors, 0 warnings. Not saved.

**Not tested:** Play. The real manager on i5 has no fix A, so the HitFeel getter was only linked against the stub.

## Play test (any wave)
- New zombies still get their tint, size and walk-speed variety, and shielded ones still glow green.
- Hit a zombie with the sword: red flash on it, short hit-stop, blood on the blade that fades.
- `stat game` before and after if you can.

## Revert
Before `--apply` the runner copies each .uasset to `Saved/bak472/` (`*.uasset.fixE2`). Close the editor, copy it back over Content (drop `.fixE2`), reopen.
