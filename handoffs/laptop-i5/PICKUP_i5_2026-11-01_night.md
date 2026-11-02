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

## Update 2026-11-02 08:15 (context ~89 %): i5 editor cannot open the map in the session
- The i5 editor crashed at 06:18 (compiling BP_ZombieHUD) and nobody noticed until 08:00: my watch only covered the chat.
  The Monitor now also prints "I5 EDITOR DOWN" when UnrealEditor.exe disappears: always run it that way.
- Synced again with i9's sync3 zip (163 files, backup C:/UnrealProjects/CD58_backup_before_sync3_1102). The editor
  joins CastleDefender6 fine and stays responsive with an Untitled world, but **loading ThirdPersonMap crashes it ~3 s
  after MAP CHECKDEP** (05:10, 05:18, 08:13; access violation, no callstack; last compiles before it were BP_ArmoryHUD /
  BPC_Muster / BP_ZombieWallBreaker). Not yet diagnosed. Ideas for the next i5 session: try opening the map WITHOUT
  Multi-User (plain editor, no -CONCERTAUTOCONNECT) to see if the map itself or the session replay crashes; check
  Saved/Crashes/<latest>/ for a minidump callstack; try -nullrhi or lower texture pool (GPU memory warnings all night).
- Open: Alien's green soot card on the north wall above the torch next to Vesna (TorchSoot_28, Plane at 700,3309,473,
  shows pale green = broken/missing material). Handed to i9 (chat 396).
- i5 next: #421 Muster v2 paste (needs a working map-free BP editor: the paste itself doesn't need the map), #77 LV4 check.

## Update 2026-11-02 09:35: map-load crash FIXED, #421 setup done, #77 checked
- **Crash cause:** JOIN started the editor ON ThirdPersonMap (EditorStartupMap) from disk, which loaded ~110 BPs; the
  Multi-User join then hot-reloaded 107 of them in ONE engine frame (`Reloading 107 Package(s)`, `*_DEADPACKAGE` classes,
  UberGraphFunctionKey ensures). The inbox watcher ran `_loadmap.py` from a Slate tick nested inside that loop (frame
  counter stuck), and the laptop sat at the commit limit (28/29 GB; ~20 idle Claude processes hold 5.7 GB). Result:
  access violations at map load (05:10, 05:18, 08:13) or during the reload itself (08:38).
- **Fix:** JOIN_LIVE.bat now starts on `/Engine/Maps/Entry` (+ `r.Streaming.PoolSize 400` + the watcher). Join = 0
  reloads, 0 compiles; then `_loadmap.py` (GC + load_level) opens the map from the session: OK at 08:50, stable since.
  The watcher only runs scripts from real engine frames (>= 3 frames / 10 s). If it seems idle, focus the editor
  (`ue_windows.ps1`): an unfocused editor runs at ~3 fps. To stop a stuck PIE: PostMessage Esc to the main window works.
- i5 keeps its Lumen SurfaceCache atlas at 2048 (i9 moved the Master to 4096; 2 GB GPU here).
- **#421:** setup steps 1-2 done in the session (backup, T_MU2 textures, vars). Busts: 5.8 refuses
  `show_only_actors` as a property (wrapper `muster421_setup_ue.py` uses `show_only_actor_components`), but the
  captures come out blown out/white, so BustTex is cleared (medallions) until TGA tunes it. i9 pasted the graph at 09:08
  (compiles clean, 0 Muster errors in Play). Owed: the click checklist in Play (needs GUI / someone at a PC).
- **#77:** arcs work at LV4 (`fresh77_lv4.png`, `xbow77_fresh_ue.py`). The TradeShowcase placed in the map has no
  overlay on ItemXbow/ItemSov (stale instance): asked i9 to reset it on the Master.
- **PIE on i5 is not usable right now** (hero doesn't spawn behind the start menu, 1.6 fps, 27k runtime errors/9 min,
  commit at the limit). Play checks go to the Master.
- BP_ArmySplit IsValid guard: still open (needs an export + GUI paste; no screen access on i5 this morning).

## Update 2026-11-02 10:00: #425 (owner order: AAA realism pass)
- Step 1 contact stains: built + previewed, NOT placed (owner OK asked, desk bell). Everything in handoffs/contact-decals-425 (README).
- Half the castle walls have Receives Decals OFF: stain cards (unlit Modulate) instead of decals.
- Next: steps 2 (wood/stone/grass) and 3 (re-bake fake props) on card #425.
