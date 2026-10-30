# #213 PRIORITY: clicking UNLOCK in the skill tree quits PIE (fix)

By `checkking (Claude)`, 2026-10-30 night. Built on `handoffs/exports/master/2026-10-30b/BP_ZombieHUD_EventGraph.txt`.
The dry-run merge passes: **Validation OK**, 15 nodes, +18 links.

## Cause (Master's diagnosis, confirmed)

The pause menu's Quit row in BP_ZombieHUD (x 0.27–0.73 W, y 0.715–0.80 H) keeps taking clicks while the skill tree is
open. Its draw path is gated by `IsGamePaused AND FTrunc(ShopV.X) >= 10`, and the tree pauses the game. The tree's
middle-column UNLOCK boxes sit inside that rect, so a click there also fires one of the three `QuitGame` branches
(IW2412, IW2578 and IW2874).

## Fix

Each Quit branch becomes `old condition AND NOT skill-tree-open`. The tree's own open flag is `MPC_SkillTree.St.R > 0.5`
(BP_SkillTreeHUD: CX_43 → CX_48.R → CX_55, the tree's main draw gate).

`GetVectorParameterValue` is an exec node in 5.3, so each guard is spliced into the exec path:
`DrawText.then → QStN → branch`.

## Steps

1. Export BP_ZombieHUD's EventGraph fresh and save it as `live.t3d`.
2. Run `python tools/applyall/applyall.py merge --live live.t3d --manifest handoffs/skilltree-quit-213/manifest_zombiehud.json --out merged.t3d`.
   Go on only if it prints `Validation: OK`.
3. Paste only the merged graph's new nodes plus the rewires. The manifest is small on purpose, because a full 4,700-node
   repaste crashes the editor.
   - If a full repaste is the only route, paste `merged.t3d` into the EventGraph (Ctrl+A, BackSpace, Ctrl+V).
   - Otherwise place the 15 nodes from `ZombieHUD_QuitGuard_graph.txt` and make the 12 links in the manifest by hand.
4. Compile and Save.

## Checks

1. Open the skill tree (T) and click UNLOCK and rank-up in all three columns: PIE keeps running.
2. Pause menu (Esc): Quit still quits.

## Not in this fix (next)

The layout: the gold "UNLOCK - 2 PTS" boxes overlap the aura names in the middle PASSIVE column. A follow-up manifest
for BP_SkillTreeHUD will move them.
