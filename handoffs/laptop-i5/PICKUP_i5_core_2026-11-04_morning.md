# i5 core pick-up (2026-11-04 ~10:55). Replaces PICKUP_i5_core_2026-11-03_late.md (still there for history)

Seat `adjustedfilm (Claude)`, chat name **i5**. Fast chat: `http://100.87.149.123:8765` (`/read?after=N`, POST `/say` with "From: i5: ", `/upload?name=`). Last line read: 1569.
Other i5 session: "i5 #472: zombie crowd + battle logic" (local_d16f7c8b-52b1-4f62-8841-ec8128c725a8): holds the desk seat and owns BP_Zombie, BP_ZombieWaveManager, BP_SoldierSword, BP_FleshBrute, ABP_Zombie. Don't tick while it runs. It may restart the i5 editor; coordinate.
i9 = Master PC, works offline, applies + saves. Nothing is in the game until i9 says so.

## Owner's orders in force (Alien)
- "work nonestop until our game quality becomes AAA (dont add new features rather enhance existing ones)" (card 482). Parked as new features: player key rebinding, #453 Gothic set.
- "SAT IDLE? THAT IS NEVER ALLOWED": when blocked, take the next thing, including other agents' silent items. A watcher must also wake on silence.
- "i want the most realistic castle ever, the game is about the castle" + "i want a perfect castle, cooperate with i9". Real carved stone stays; never bake it back for fps. He likes "small stones together in 1 mesh".
- "go through codes and game system, find out how to optimize to reach AAA ms levels" (card 487). Project is set to 33.3 ms (30 fps); target 30 first on a strong PC, then 60.
- He stopped the grass speed work ("no"): do not restart without his word. handoffs/grass-speed-487/grass_probe_ue.py is read-only, unpushed.

## Waiting on i9 (asked in chat; i9 said NOT started at 10:04, "castle first")
| What | File | Note |
|---|---|---|
| 7 badge off the health bar (owner asked) | `obsidian-skill/ember_pos_ue.py` | 10 s. Spot is a guess: right of the bar, fallback `--y 0.8` |
| F1 weapon list over Vesna | `faults-1205/f1_fix_ue.py` | Compiled on a copy |
| F9 INFECTED grey card | `infection-card-f9/fix_card_ue.py` | iMakeMID1 Parent empty on i5. Doesn't fix health bars drawn over it |
| Speed test: step 1 of the plan | `aaa-472/profile/wave_sweep_ue.py` + `stat unit` with and without a wave | Decides everything in `vram-482/OPTIMIZE_PLAN.md` |
| Fresh castle scan + health + close-ups, realism dump | `castle-harmony-461/castle_scan_ue.py`, `aftersave_health_ue.py`, `realism_ab_ue.py --dump` | My scan is older than the rebuild |
| Helm, `--start-owned` | `obsidian-sovereign/helmet/README.md` | Never in UE. Sets EmberMinTier to 4 |
| Video memory | `vram-482/textures482_ue.py` | Numbers from i5's copy |
| Road + meadow brightness | `grass-440/ground2_ue.py` | Leaves i9's wagon ruts alone; check it still fits his realism work |
| Shop keys Flares, Medics, Cavalry, Upgrades never fire | `vram-482/shop_keys_fix_ue.py` | Compiled on copies; balance risk |
| Commander world search per frame | `vram-482/commander_scan_fix_ue.py` | Compiled on a copy |
| Grime strips hidden | `vram-482/bands482_ue.py` | Don't run on the rebuild before a close-up; read i9's sync58/bands_hidden_1104.json first |

## In the game (i9 saved)
#470 cracks, #461 harmony + keep trim, #469 stairs, #455 fire pit, F11, #472 A-F, tentacles 8/8, invisible walls (70 off, 51 kept), #440 ground tints + meadow edge (2,047 tufts; weak result), wagon ruts, #477 Obsidian skill + 3/4 fix (owner saw the badge; key 7 firing NOT confirmed). i9's own: real-stone curtains (Castle/CurtainMasonry), towers etc. (Castle/BlockoutMasonry), arcade, lime mortar, texture pass.

## My work in progress
- **#488 merlon kit, `handoffs/battlements-488/`: pushed as WORK IN PROGRESS, NOT ready, don't send to i9.** Open review items: (1) texture stretch on coping tops + parapet coping and smeared sides: measure max stretch per module; (2) stones too pillow-like: vary corners, chips; (3) report n-gons, overlaps, degenerate faces per module (owner found these on i9's stair curtain, told i9). The generator was mid-edit when stopped at 10:55: `build_merlon_kit.py` may be half changed, and renders/FBX are older than it. Check it runs, regenerate, review, then tell i9 to place. i9's numbers: curtain 2.45 m (front + bailey east 1.95), deck top z 6.80, sill 7.55, merlon top 8.70; plain inner parapet 1.0-1.1 m; pitch 240, merlon 140, crenel 100. Owner may want wider merlons (real 150-200): flagged, no answer.
- **Next on speed:** audit row E2 (ZombieHUD H2128, Minimap CX_116, HitFeel, ZombieVariety, JellyShieldAll scans): I claimed these with the crowd session. ZombieReg is on the host manager (GetActorOfClass(WM).ZombieReg, as fix D), and it misses brutes. i5's copies have no fix A, so test accordingly.
- **Then, free:** keep door, timber drawbridge, courtyard floor slab, Tower9 gate steps as real stone/timber (check i9 hasn't done them); reference study of real castles. Tower9 shapes 20 % wide: TGA_PC silent, source in /files/124821_tower9_aaa_1103.zip. Checklist for all of it: `castle-harmony-461/PERFECT_CASTLE.md`.

## Facts learned
- i9's CPU reaches 97 C (10:03): throttling may be in every fps number. Told i9; owner told.
- Battle 250-330 ms vs 64 ms without a reported wave: a wave may add about 200 ms, cause unknown; fixes A-D and LODs gave nothing. "GPU-bound" is i9's reading, not measured.
- Scan triangle counts are Nanite fallbacks, so stone is undercounted: my "grass = 71 %" isn't reliable.
- Multi-User: MI edits on i5 autosave and pump Slate, which re-entered my tick and froze the editor. Guard re-entry; no MI edits on i5.
- Deleting a BP copy then calling ListAvailableNodes in the same editor session crashes (fatal, 22:45). New folder per test, delete only right after a restart. Stuck editor: `Saved/Autosaves/PackageRestoreData.json` renamed, inbox cleared, relaunch via `Start-Process cmd /c JOIN_LIVE.bat`.
- Temp copies on i5 to delete right after the next restart: /Game/_i5tmpC1, /Game/_i5tmpK1, /Game/_i5tmpF1, /Game/_i5tmpE2 (empty), and the crowd's /Game/_i5tmp472.
- `BlueprintGraphEditor` Python edits live graphs: `obsidian-skill/ember_ops_ue.py`, `aaa-472/ops/graph_ops_ue.py`. Whole-BP exports (11-03, older than fixes): crowd session's scratchpad `.../5b12bc64-7857-4c7a-a269-88e791cdc331/scratchpad/all/*.T3D`.
- Read the chat right before any hand-off. Run `node --check data.js` after editing data.js; no apostrophes in captions.
- Don't offer to delete hidden pieces: the "188" list holds gameplay pieces; withdrawn.

## Cards
482 polish, 485 helm, 486 realism (i9 leads), 487 speed, 488 battlements, 469 stone sizes + Tower9, 477 skill (open until key 7 is seen), 461 harmony, 440 ground.
