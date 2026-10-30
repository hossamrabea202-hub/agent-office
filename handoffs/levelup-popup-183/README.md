# #183 Remove the "LEVEL UP!" pop-up — fix

From: hossam gmail laptop2 (Claude), 2026-10-30. Target: `BP_ZombieHUD` EventGraph (1 rewire, no paste, no variables).

**Where it is:** in the HUD draw chain, after the XP bar texture, a branch (`K2Node_IfThenElse_H296`) checks
"0.1 s < time since LevelUpAt < 2.5 s" and draws the big "LEVEL UP!" text (`K2Node_CallFunction_H297`), then
carries on to the sparkle block (`K2Node_CallFunction_H2128`, GetAllActorsOfClass).

**Fix:** connect the branch's True pin straight to the sparkle block, so the DrawText node is skipped.
The node stays in the graph unlinked (delete it by hand if you like). The level-up timer, XP bar and #184 sparkles
are untouched.

**Master steps:**
1. `python tools/applyall/applyall.py merge --live <BP_ZombieHUD EventGraph export> --manifest handoffs/levelup-popup-183/manifest.json --out merged.t3d`
   (dry-run on 2026-10-30b: Validation OK) — or just drag the wire by hand: `H296 True → H2128 execute`.
2. Compile. Test: gain a level — no "LEVEL UP!" text, XP bar still fills.
