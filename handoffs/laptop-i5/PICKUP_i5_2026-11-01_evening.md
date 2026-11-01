# i5 core pick-up note (2026-11-01, ~19:45, context 80 %)

Seat `adjustedfilm (Claude)`, chat name **i5**. i9 (Master) left for Alien's VIP project; **i5 is the only editor seat**.
Session: Multi-User **CastleDefender3** on the Master PC (server + duo chat keep running there). Card **#412** = i9's hand-off.

## Owner rules learned today (also in memory)
- Final results only: finish, Play-test, swap in with a backup, then show Alien. Live swaps of shared assets still need
  the owner's OK **in the Claude window** (the permission check blocks relayed chat approvals).
- Tiny steps on i5 (2 GB GPU, 16 GB RAM): no heavy rebuilds, no force-deleting referenced assets, no whole-graph pastes
  of huge BPs. Answer the chat first (bubble red count = stop and reply). Names: Alien (owner), i9, i5.
- NEVER use computer-use `open_application` for Unreal: it spawns empty 3.6 GB editors. Focus the CastleDefender window
  with user32 ShowWindow + SetForegroundWindow. Avoid `|` in editor console one-liners (it splits commands): use a .py.

## Done today by i5 (in game)
#372 #373 #238 #234-236 · #383 bounce · #370 quests (8/10, hero attach done by i9) · #357 torches · blood (BP_BloodBurst
droplets, backup BP_BloodBurst_BACKUP337) · tentacle bio-shield stretch (M_TentacleJellyShell_Smooth on 10 shells,
--revert in tentacle-skin-366/shell_smooth_ue.py) · #389 jelly (M_JellyBlob_Real) · #259 gate tag FarmGate re-added ·
#237 courtyard rock (BreachSpot_A unwalkable) · #368 knight pose dump · #374 setup (i9 finished the graph) · chat bubble app.

## Next, in order
1. **#242 ore shed:** anchor = `Mine_01` (surface mine entrance, SM_Camp_MineEntrance_Split) at (94, -2401, -122), yaw 160.
   Put SM_OreShed ~8-9 m beside the entrance, open front facing the cart road; trace to the ground for Z; look at it
   (castle-area camera is OK on i5), nudge, save. Script: handoffs/props-242-246/place_242_246_ue.py
   (`--at OreShed X Y Z YAW --apply`, `--remove --apply` undoes).
2. **#246 signs:** Smith → `Forge_01` (SM_Camp_Forge, 6 m camp) at (4021, 3159, 3) yaw -90: on a post/beam of the forge.
   **No tavern building exists** and Vesna (`NPCFill_Vesna`, 715,3195) has no stall structure: Decision needed from
   Alien (or place tavern/shop signs on the nearest wall by the well fire / Vesna). Ask in the chat.
3. **Shop:** Emberoath row in the weapon table; shields (Heater/Round/old gold SM_Shield/wood) with a block stat
   (reuse the Obsidian shield slot); Obsidian pieces (forearms, thighs, waist, upper arms) as table rows + attach.
   Hero/HUD pastes are big: small steps, one Blueprint at a time.
4. #411 castle-scroll HUD, #410 wet rain swap (wet410_ue.py --swap after a lookdev check), #325 zombie towers (big).
5. Play checks still owed: #259 farmers pass the gate (60 s, plots Stage 1), jelly look, tentacle shell look.

TGA: told to finish #367 Yellow Eagle (pose dump is in exports/master/knight_refpose.txt), then #416 Skill Tree HUD.
