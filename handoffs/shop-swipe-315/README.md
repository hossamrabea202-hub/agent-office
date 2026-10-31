# #315 Vesna's shop: A / D (and the arrow keys) swipe between weapons

By `adjustedfilm (Claude)`, 2026-10-31. Owner: *"when buying weapons from venessa A and D and arrows can also swipe weapons
in the shop interface"*.

**Found:** the trade carousel (MPC_SkillTree `Trade`) **already flips on the Left / Right arrow keys** while the shop is
open, as well as on the on-screen arrows (10-30b BP_SkillTreeHUD: `CX_1375` Left, `CX_1379` Right). So only **A** and **D**
are new. A goes next to Left and D next to Right, on the same "shop fully open" gate (`CX_1373`), with the same sound and
the same wrap-around.

**Pre-checked:** `fix_impure` makes no changes, `applyall check` is OK, and a dry-run merge on the 10-30b BP_SkillTreeHUD
export is **OK** (6 rewires). No re-paste of the 5,400-node HUD.

## Steps (Master: 4 nodes, 6 links, about 2 minutes)

1. Open **BP_SkillTreeHUD** → EventGraph, and paste `SkillTreeHUD_SwipeAD_graph.txt` (4 nodes) in an empty spot.
2. Make the links:

| # | From | To |
|---|---|---|
| 1 | `CX_14` (Get Player Controller) ReturnValue | **SwipeKeyA**.Target |
| 2 | `CX_14` ReturnValue | **SwipeKeyD**.Target |
| 3 | `CX_1375` (Was Input Key Just Pressed **Left**) ReturnValue | **SwipeOrA**.A |
| 4 | **SwipeOrA**.ReturnValue | `CX_1376` (OR).**B** (replaces the link from CX_1375) |
| 5 | `CX_1379` (… **Right**) ReturnValue | **SwipeOrD**.A |
| 6 | **SwipeOrD**.ReturnValue | `CX_1380` (OR).**B** (replaces the link from CX_1379) |

3. Compile and save. Or use `applyall.py merge` with `manifest_skilltreehud_swipe.json` on a fresh export.

## Tests

1. Open Vesna's shop. Press **D**, then **Right**: each step shows the next item, with the flip sound.
2. Press **A**, then **Left**: each step shows the previous item.
3. Mouse clicks on the on-screen arrows still work.
4. Outside the shop, A and D move the hero as before. The shop pauses the game, so the hero doesn't walk while you browse.
