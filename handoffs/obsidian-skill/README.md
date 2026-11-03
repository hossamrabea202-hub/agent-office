# #477 Obsidian complete set as a skill (i5, 2026-11-03)

**Not in the game. Never played.** It compiles clean on a temp copy of BPC_ObsidianSet on i5 (`compile True`, 0 failures, 0 errors, 0 warnings). i5's copy has the same 689 nodes as the 20:05 export.

What it does with the full available set (3/4 today, because the Helm has no art; see `ember2_ue.py`): press 7, a shockwave fires (80 damage, 6 m, 15 s cooldown). It no longer fires by itself when you are hit. A round badge shows the cooldown sweep and the key name, and a refused press flashes red with a fail sound. Damage reduction and embers stay always-on. Below that nothing shows. When the helmet ships, set `EmberMinTier` to 4: the skill moves to 4/4 and tier 3 gets its automatic shock back. The save format is unchanged. Design: `DESIGN.md`.

**Player key rebinding is NOT in this step.** The game has no rebinding system at all. Here the key is one class default (`EmberKey`).

## Steps for the Master (editor open, not in Play, `git pull` first). No paste
1. `py setup_ember_ue.py --dry-run`, then `--apply` (variables, icon, defaults; backup `BPC_ObsidianSet_bak477`).
2. `py ember_ops_ue.py --dry-run`: must print `check OK`. A `STOP` line changes nothing: send it to i5.
3. `py ember_ops_ue.py --apply`, then `py ember2_ue.py --dry-run`, `--apply`: each must print `RESULT compile True | link/value failures [] | new errors []`, then `saved True`.

Any failure: it does not save. Restart without saving and send i5 the output, don't debug it.
Revert after a save: close the editor, copy `Saved/bak472/BPC_ObsidianSet.uasset.fix477` over `Content/CastleDefender/Gameplay/Castle/BPC_ObsidianSet.uasset`. Backup copies are `..._bak477`.

If set v4 (#453) lands first, it still works as long as the live node names in `ember_ops.json` exist; the dry run checks that.
`ember_paste.txt` / `ember_manifest.json` are only the generator's intermediate step: don't paste them.

## Test list (all available pieces worn, 3/4 today, new game)
- The badge shows; check its place (`EmberX` / `EmberY` are a first guess, no screenshot yet).
- 7 fires: zombies within 6 m take damage and are pushed, flare shows, sweep runs 15 s. 7 again: refused.
- Being hit no longer fires the shock.
- Take a bundle off: badge gone, on-hit shock back, cooldown kept.
- Open Vesna or the Book of Skills (T): 7 does nothing.
- Save and reload: same pieces, old save loads.

Checked on i5: full setup + ops on a temp copy, compile clean. Not checked: the badge on screen, the key in Play, damage, feel. The 15 s / 80 / 6 m numbers, the badge position and the icon (generated placeholder) are first guesses.
