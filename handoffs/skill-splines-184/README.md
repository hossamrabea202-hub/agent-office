# #184 Skill-point gain: flying sparkles to the skill-tree icon

From: hossam gmail laptop2 (Claude), 2026-10-30. Target: `BP_SkillTreeHUD` EventGraph (one paste + 5 rewires, 3 variables).

**What the player sees:** on a level-up (= skill point), six glowing sparkles (the XP glow sprite, tinted violet-blue)
fly from the hero on an arc to the skill-tree icon over 1.4 s, shrinking as they go. Same sprite as the XP effect,
different colour and destination.

**Master steps (tools/applyall):**
1. Add the 3 variables from `VARIABLES.md` (`SPT` float 0, `SPN` int 0, `SPPrevLevel` int 0).
2. Export the live EventGraph of BP_SkillTreeHUD (or use today's `handoffs/exports/master/2026-10-30b/BP_SkillTreeHUD_EventGraph.txt`).
3. `python tools/applyall/applyall.py merge --live live.t3d --manifest handoffs/skill-splines-184/manifest.json --out merged.t3d`
   (dry-run on today's export: Validation OK, +131 nodes, 204 links, 5 rewires).
4. Ctrl+A, Delete, paste, File > Refresh All Nodes, compile, save.
5. Test: gain a level → sparkles from the hero to the skill-tree icon. Also do #183 while there: the achievement-style
   pop-up on skill gain can be unhooked (its PushNotice call for skill gain) — the sparkles replace it.

Tuning: tint on each `Glow` node's TintColor; arc height = the `Multiply_DoubleDouble` default 120 (per sprite 120 → 60);
duration 1.4 s in the `Less_DoubleDouble` default; sprite size 28 → 14 px.
