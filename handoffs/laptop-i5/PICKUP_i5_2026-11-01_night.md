# i5 core pick-up note (2026-11-01, ~23:40, context 72 %)

Seat `adjustedfilm (Claude)`, chat name **i5**. Alien is asleep: work nonstop, answer the fast chat first (rule 1: check it
every 10 s), keep i9/TGA moving, whiteboard minus WinterKeep. i9 is back on Castle Defender tonight (split: i9 = #61 #119
#120 #141 #143 #102; i5 = #58 #64 #65 #67 #74 #77 #95 #49 #50 + #411 #418 #419).

## How the i5 editor runs now (read handoffs/laptop-i5 + memory "i5 editor inbox watcher")
- Session **CastleDefender6** (i9 restored the crashed CastleDefender3 archive; persisted to the Master disk at 22:54).
- Launch: UnrealEditor + JOIN args with `-CONCERTSESSION=CastleDefender6` and
  `-ExecCmds="py C:/Users/hossam.rabea/agent-office/handoffs/laptop-i5/ue_inbox_watcher.py"` (NOT -ExecutePythonScript: it quits).
- Run editor Python: `sh handoffs/laptop-i5/ue_run.sh <script.py> [args]` (waits for the Multi-User join + 20 s).
- Renders without the viewport (works with the screen locked): `handoffs/laptop-i5/capture_shot_ue.py`.
- The laptop's **Windows screen is LOCKED** since ~23:30: no GUI (graph pastes, Play by hand). Needs someone at i5.
- Startup takes 10-15 min (BPC_MotionFX compile). After a join, reload ThirdPersonMap or the level shows the disk copy.
- Don't compile a BP right after an FBX import in the same script (crash). Clear ue_inbox/*.py before restarting.

## State of my cards
| Card | State |
|---|---|
| #242 ore shed, #246 signs | done (closed). **But** after the last rejoin i5's map does NOT show them (one-file-per-actor packages); asked i9 (chat 293) for a zip of the persisted packages incl. __ExternalActors__. Don't re-place them (duplicates on the Master). |
| #418 shop | step 1 done (Emberoath row 26, SM_Emberoath_Kit2). Shields/armour = TGA code (exports in exports/adjustedfilm/shop-v2). |
| #419 tentacle shell | applied in CastleDefender6 (unmirror419_ue.py --apply, saved) before the 22:40 crash; card reopened until i9 confirms he sees +scale on Env_CorruptedTentacle_5. |
| #58 cannon break | in CD6: Break1-3 imported, BPC_CannonBreak.StageMeshes set (backup _BACKUP58). Play test owed. |
| #411 castle scroll | BPC_CastleScroll + vars + icon in CD6, component added to BP_ZombieHUD (unsaved). Owed: paste build/BPC_CastleScroll_graph.txt, paste hook, `rewire_hook411_ue.py` (README). Needs GUI. |
| #74 potions | BPC_PotionBelt + vars + icon in CD6, component added to BP_ZombieHUD (unsaved). Owed: 2 pastes + `rewire_hook74_ue.py` (chains after #411's hook). Needs GUI. |
| #77 crossbow LV4 arcs | overlay set on BP_Crossbow + BP_TradeShowcase templates (backups _BACKUP77). In-editor lookdev on the placed showcase is unreliable (stale reinstanced components); check in Play at LV4. |
| #420 Muster v2, #416 | TGA (pinged). |
| #64 #65 #67 | blocked on private knight/cape sources (Codex cards). #49 TGA. #50 Codex integration. #95 Codex foundation. |

## Next steps
1. When the screen is unlocked: paste #411 then #74 (READMEs), Play-test #411/#74/#58/#77, final shots, close.
2. Get i9's zip for the map packages, copy into i5 Content with the editor closed.
3. Then #95 (upgrade looks) / #50 per the cards.

## Update 2026-11-02 06:00 (context 86 %)
- CLOSED: #58 cannon break, #259 farming, #74 potions, #411 castle scroll (scroll key = K; C is the Commander key). #419
  applied in the session (unmirror), waiting for i9's eye check. #77 overlay installed, Play check at LV4 still owed.
- i5 synced to the Master disk twice (zips from i9: CD58_sync_1102 + CD58_sync2_session; backups in
  C:/UnrealProjects/CD58_backup_before_sync*_1102). Lesson: in Multi-User, saves live in the session SANDBOX, not
  Content: a disk sync must include the sandbox (i9's second zip).
- The i5 laptop (2 GB free RAM) cannot keep up with heavy live saves: it crashed 4x tonight while recompiling big BPs
  (ArmoryHUD, Muster) on map load. Rule with i9: he batches saves, posts 'saving' first, stays off hero/ZombieHUD/
  BarracksHUD/SkillTreeHUD while i5 pastes; heavy Play tests go to the Master PC. Launch now uses -LocalLogTimes.
- After a join the i5 editor shows an Untitled world; forcing load_level right after the join crashed it twice. Let it
  settle (responding for ~1 min) before opening the map.
- Next for i5: #421 Muster v2 paste (TGA), #77 LV4 Play check, BP_ArmySplit guard (4 errors/run: IsValid on
  ForEach_29's element before EqualEqual_O_31/Branch_32), then Alien's list (#64 #65 #67 need private files, #95).
