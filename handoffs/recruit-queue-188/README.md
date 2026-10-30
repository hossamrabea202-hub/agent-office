# #188 Recruit queue + loading bar above the barracks NPC

From: hossam gmail laptop2 (Claude), 2026-10-30. Target: `BP_BarracksHUD` EventGraph (one paste + 8 rewires, no new Blueprint).

**What the player sees:** after clicking a recruit, a thin faded-white bar appears above the barracks NPC and fills
while the recruit loads; the fill colour says what is coming (gold = sword, steel-blue = crossbow, crimson = commander).
Up to 3 recruits can be ordered; the next ones wait as small white ticks right of the bar and start one after the other.
Commander takes 3× a soldier's time and goes through the same queue (no more instant commander).

**Master steps (tools/applyall):**
1. Add the 4 variables from `VARIABLES.md` to BP_BarracksHUD (My Blueprint → paste each `BPVar` line, or add by hand:
   `RQ` int array, `RQStart` float 0, `RQDur` float 0, `RecruitSeconds` float 6).
2. Export the live EventGraph (Ctrl+A, Ctrl+C) to `live.t3d`.
3. `python tools/applyall/applyall.py merge --live live.t3d --manifest handoffs/recruit-queue-188/manifest.json --out merged.t3d`
   (dry-run against the 2026-10-28 export: Validation OK, +70 nodes, 84 links, 8 rewires).
4. Ctrl+A, Delete, paste `merged.t3d`, compile, save. If a node is red (SelectColor, Project, DrawRect): Refresh Node.
5. Test: order 3 soldiers fast → bar fills three times in a row, ticks count down; order a commander → bar crimson, 18 s.

Tuning: `RecruitSeconds` on the HUD (default 6). Bar size: `Track` node ScreenW 120 / ScreenH 8; height above the
NPC: the `Add_VectorVector` default (0, 0, 230).
