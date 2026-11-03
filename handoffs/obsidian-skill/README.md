# #477 Obsidian complete set as a skill (i5, 2026-11-03)

**Not in the game. Never compiled:** i5 cannot paste whole graphs, so the Master's compile is the first real test.

What it does at 4/4 Obsidian: press 7, a shockwave fires (80 damage, 6 m, 15 s cooldown). It no longer fires by itself when you are hit. A round badge shows the cooldown sweep and the key name, and a refused press flashes red with a fail sound. Damage reduction and embers stay always-on. Below 4/4 nothing shows, and tier 3 keeps its automatic shock. The save format is unchanged. Design: `DESIGN.md`.

**Player key rebinding is NOT in this step.** The game has no rebinding system at all. Here the key is one class default (`EmberKey`).

## Steps for the Master (editor open, not in Play)
1. Fresh export of BPC_ObsidianSet (it changed after the 20:05 export if anything was pasted). Then from this folder:
   `node ../faults-1205/t3d_to_graph.js <export> EventGraph live_EventGraph.txt`
   `python ../../tools/applyall/applyall.py merge --live live_EventGraph.txt --manifest ember_manifest.json --out ember_merged.txt` (must say `Validation: OK`).
2. `py setup_ember_ue.py --dry-run`, then `--apply` (backup `BPC_ObsidianSet_bak477`, variables, icon, defaults).
3. BPC_ObsidianSet EventGraph: Ctrl+A, BackSpace, Ctrl+V `ember_merged.txt`, Refresh All Nodes, compile, save.

Compile error: send it to i5, don't debug. Revert: paste the fresh export's `live_EventGraph.txt` back, compile, save. The extra variables do nothing.

If set v4 (#453) lands first, regenerate on that export: the paste is self-contained, only the manifest's live node names must still exist.

## Test list (4/4 worn, new game)
- The badge shows; check its place (`EmberX` / `EmberY` are a first guess, no screenshot yet).
- 7 fires: zombies within 6 m take damage and are pushed, flare shows, sweep runs 15 s. 7 again: refused.
- Being hit no longer fires the shock.
- Take a bundle off: badge gone, on-hit shock back, cooldown kept.
- Open Vesna or the Book of Skills (T): 7 does nothing.
- Save and reload: same pieces, old save loads.

Checked: applyall merge `Validation: OK` on the 20:05 export (+89 nodes, 112 links), fix_impure no change, hero `IsDead` reference same as the live potion graph, setup script on a throwaway Blueprint on i5. The 15 s / 80 / 6 m numbers and the icon (generated placeholder) are first guesses.
