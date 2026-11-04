# #482 Blueprint frame-cost audit (read-only, 2026-11-04)

Source: 193 T3D exports from 11-03, which predate fixes A-F. Graph walks followed local functions and custom events. Nothing was timed: ranks are reasoned from cost per call x calls per frame x instances. Every claim is **F** (FOUND in a graph, node names given) or **G** (GUESS: inference or engine knowledge).

**Read this first.** On the tested machine (editor, T1000, 3-4 fps) fixes A-D removed errors but gave no fps gain (PICKUP_472), so the frame looks GPU-limited there, though #472 says that is unmeasured. Expect no visible change from anything below on that machine. These fixes matter on a strong PC at 60 fps, where the game thread must fit 16.7 ms. Check with `stat game` / Insights there before and after; only that can confirm this order.

**Corrections to earlier notes.** (F)
- TICK_SCAN's 106 "every frame" events overcount: its filter also matches timer events such as WxTick (0.1 s) and WaveTick (0.3 s). My walk finds about 85 live per-frame roots.
- 6 BP_ZombieWaveManager are placed, not 5.
- The game HUD is one object: an 11-level inheritance chain. BP_NoticeHUD (the string in BP_ThirdPersonGameMode.uasset) > Armory > Commander > Hero > Queue > Controls > Army > Barracks > SkillTree > Minimap > BP_ZombieHUD. Each level runs its DrawHUD and calls its parent.

**Instances.** (F) From `__ExternalActors__` on i5's disk, not the Master: BlobMine 22, JellyMine 19, TentacleVitals / ShockRider / ShockAudio / BPC_TentacleStrike 10 each, Cannon 8, WaveManager 6, SwayChandelier 5, SoldierSword 2 + Xbow 2 placed. castle_scan.json shows JellyMine 12, so it covers only part of the map. Zombies: 84-85 seen (PICKUP). Soldiers in battle: **G** 20-60, no cap found in the exports.

## A. Per-frame ranking, top 25 (all rows F except the G notes)
| # | Blueprint, root | Inst. | What runs every frame | Fix | Owner |
|---|---|---|---|---|---|
| 1 | BP_SoldierSword CX_135 Tick, FocusCheck @0.15 s | G 20-60 | 162 exec nodes, 681 pure. Scans CX_904, CX_637, CX_707, S118_GA (gated, not per-frame always); `LineTraceSingle` CX_246. FocusCheck: CX_499 GetAll soldiers + **CX_518 GetAllActorsWithTag(SallyPort)**. Fix D moved CX_144 / CX_453 to the registry and throttled far, unseen soldiers | Soldier registry, cache SallyPort, stagger FocusCheck. Fix D applied, rest open | crowd |
| 2 | HUD chain + component draws | 1 | See HUD table: at least about 330 exec + 1780 pure nodes with all menus closed, in the BP VM | Early-out per closed panel; cache refs | free* |
| 3 | BP_HalfHorseZombie HHZ_N55, BP_RealmWasp WSP_N33 | per wave | `ThinkAcc >= 0.0` (HHZ_N62, literal 0), so the 4 Hz-style Think runs **every frame**. HHZ_N73 **SimpleMoveToActor** per frame. Wasp adds K2_SetActorLocation, FindLookAt | See B1: needs the intended numbers | free, after asking |
| 4 | BP_CommanderHUD K2Node_CallFunction_7 | 1 | **GetAllActorsWithTag(Commander)** every frame (else path merges at K2Node_VariableSet_2). G: walks every actor in the world, thousands here | CommanderRef exists: set it on spawn | free* |
| 5 | BP_ZombieHUD K2Node_CallFunction_H2128 + MacroInstance_H2129 | 1 x 84 | GetAll<BP_Zombie> and a loop to find the latest kill; also GetActorOfClass H21, H22, IW2161; nested ForLoop IW1130 / IW1201 up to 8 x 7 | Set a "last kill" on hit, read it here; cache refs | free* |
| 6 | BP_MinimapHUD CX_116 / CX_117 (when Reveal > 0) | 1 x 84 | Per zombie: distance, DrawTexture CX_166 or **Conv_StringToName(Concat_StrStr)** + MPC Get CX_183 + Set CX_198 | Prebuilt name array; registry | free* |
| 7 | BP_HitFeel CX_2 Tick | 1 x 84 | GetAll<BP_Zombie> with Cast, MPC read per zombie, to detect a hit | Event on hit; no scan | free, hook crowd |
| 8 | BP_ZombieVariety CX_2 | 1 x 84 | GetAll<BP_Zombie> forever; only acts on zombies under 1 s old (CX_6) | Run once on spawn | free, hook crowd |
| 9 | BP_JellyShieldAll CX_2 | 1 x 84 | GetAll<BP_Zombie> with Cast and overlay check, for a one-time shield | Run once on spawn | free, hook crowd |
| 10 | BP_SFXWatch CX_2 | 1 x N soldiers | GetAll soldiers; repeated GetComponentByClass per soldier; plus GetActorOfClass CX_40 | Registry + cached audio comp; soldier fires sound | free |
| 11 | BP_SoldierLevelWatch CX_2 | 1 x N soldiers | GetAll soldiers to compare Rank component positions | Event on rank change or 2 Hz timer | free |
| 12 | BP_ArmyHUD CX_8 / CX_9 | 1 x N soldiers | GetAll soldiers to tally, then 11+ draws, always on | Registry or counters on recruit / death | free* |
| 13 | BP_JellyMine CX_1001 > BP_JellyBlob CX_11 | 19 + spawned | CX_12 CreateDynamicMaterialInstance call and param read each frame; CX_83 **GetActorOfClass** + CX_89 IsBurningAt (4 loops) while armed; scale writes | Cache MID and manager; idle check at 5 Hz; wobble only if rendered | free |
| 14 | BP_TentacleVitals CX_49 | 10 | **LineTraceSingle CX_88** from the camera, each of 10, every frame; widget + SetText CX_120 string when shown | One shared trace; or 10 Hz | free |
| 15 | BP_ShockRider CX_1, BP_ShockAudio CX_1 | 10 + 10 | Repeated pure GetAttachParentActor + GetComponentByClass + GetMaterial, Cast, param reads; Band transform writes CX_81-87 every frame | Cache at BeginPlay; tick on only during a shock | free |
| 16 | BP_ZombieWaveManager GT0 Tick | 6 | 11-03: GetAll zombies x 6. **Fix A applied (registry); mark fixed.** Check all 6 no longer scan | Keep one, see D | crowd |
| 17 | BP_Crossbow K2Node_Event_1 | 1 | **GetAllWidgetsOfClass** K2Node_CallFunction_114, 2 HasMappingContext, 11 visibility sets, SetText string K2Node_CallFunction_166 | Cache widget; update on change | free |
| 18 | BP_HeroAuras CX_6 | 1 | **GetAllWidgetsOfClass CX_8** always; CX_434 GetAll at 2 Hz (BurnNext); CX_385 GetAll soldiers while an aura is on | Check St > 0.5 before the widget scan | free |
| 19 | BP_SwayChandelier CX_1 | 5 | **GetActorOfClass CX_2**, MPC Get CX_4 + Set CX_12 or CX_14, each of 5 | Cache; one writer; off when unseen | free |
| 20 | BP_ZombieJellyShield CX_1 | per shielded zombie | Attach parent casts, 6 MID param reads, one param write | Tick only during the 2.6 s growth; damage event after | free |
| 21 | BP_BlobMine BLM_N1 | 22 | Accumulator tick; 5 Hz distance check (BLM_N16) | SetActorTickInterval 0.2 | free |
| 22 | BP_RealmVision TK + RvTick @0.05 s | 1 | 5 param writes + BlendWeight per frame; RvTick does 23+ K2_LineTraceComponent when near (rwIfNear37) | Skip writes when unchanged | free |
| 23 | BP_CastleGateControl PromptTick, BP_GateBreachLeaf CX_1 | 1 + 1 | GetActorOfClass x 3, SetScalarParameterValueOnMaterials W_Set, CX_18; K2_SetText each frame | Cache; write on GateDamage change | free |
| 24 | BP_SkillUnlockFX CX_8, BP_MusicDirector, BP_PostFXDirector, BP_ScreenFeel, BP_WornPlate CX_7, BP_StairPace CX_6 | 1 each | Singletons polling state: 12+ MPC reads; 2 + 1 GetActorOfClass; **K2_AttachToComponent every frame**; LineTraceSingle per frame | Attach once; events; 4-10 Hz polls | free |
| 25 | BP_Zombie CX_524, BP_FleshBrute CX_524; BP_TowerBallista Think @0.05 s | 84; ?; G 0-2 | Zombie Tick: 13 exec, 46 pure, no scan after JTZ_15. Think fixes A-E (E: confirm it ran). Ballista: tbAllZombie44 at 20 Hz while reloaded | Check ZType first (JTZ_11); registry | crowd; ballista free |

\* README_F says HUD work belongs to #458: check before editing. AnimBPs are low: ABP_Zombie, ABP_KnightFollow, ABP_RisenKnight, ABP_Quinn_PostProcess, ABP_TentacleStrikePP event graphs are empty. ABP_FleshBrute fbUpdate 8 exec / 60 pure, Greystone 12 / 23, ABP_Manny 10 / 11, all using DeltaSeconds or no time. Anim graphs themselves were not audited.

### HUD DrawHUD weight (F)
"Always" = runs on every path, with paused and key-press branches treated as false. "All" = everything reachable, including open menus.
| Level | All: exec / draws / GetTextSize | Always: exec / pure / draws | Always-run scans |
|---|---|---|---|
| BP_NoticeHUD | 120 / 35 / 10 | 35 / 83 / 0 | - |
| BP_ArmoryHUD | 186 / 69 / 9 | 11 / 18 / 0 | calls the 5 Draw hooks below |
| BP_CommanderHUD | 123 / 23 / 0 | 15 / 22 / 0 | K2Node_CallFunction_7 (tag) |
| BP_HeroHUD | 50 / 24 / 9 | 8 / 30 / 0 | CX_5, CX_241 |
| BP_QueueHUD | 99 / 13 / 3 | 25 / 86 / 0 | CX_226, CX_60, CX_61 |
| BP_ControlsHUD | 33 / 2 / 0 | 9 / 13 / 0 | - |
| BP_ArmyHUD | 31 / 15 / 0 | 22 / 122 / 11 | CX_8 + loop |
| BP_BarracksHUD | 650 / 267 / 81 | 6 / 9 / 0 | - (scans behind gates) |
| BP_SkillTreeHUD | 517 / 318 / 29 | 63 / 369 / 0 | - |
| BP_MinimapHUD | 45 / 10 / 1 | 4 / 11 / 0 | CX_116 when Reveal > 0 |
| BP_ZombieHUD | 839 / 232 / 68 | 70 / 480 / 18 | H21, H22, H2128 + loop, IW2161 |
| Hooks: Muster / MotionFX / Potion / Scroll / Obsidian / WeaponKit / Toast | 640 / 146 | 61 / 534 / 11 | - |
Totals: all about 3300 exec and 1150 draw nodes; always about 330 exec, 1780 pure, 40 draws. G: a battle frame is above "always", since most gates test live state; I would guess about 100-150 draws. Pure nodes re-run for each consumer, so 1780 understates VM work (G). BPC_PotionBelt alone is 405 pure for 10 draws.

## B. Frame-rate bugs
1. **F: BP_HalfHorseZombie HHZ_S64 and BP_RealmWasp WSP_S56:** `StateTime = StateTime + 1.0` once per frame, behind `ThinkAcc >= 0.0` (HHZ_N62, WSP_N52). Any StateTime threshold counts frames, so state phases run twice as fast at 60 fps as at 30. Worse, ranges and speeds read 0.0 as well (HHZ_N78, HHZ_N98, WSP_N95, WSP_N119, WSP_N145, launch velocity). HHZ_N59 keeps a 35.0 on a linked pin, which is ignored. **G:** the generator lost or misplaced its numbers. Half-horse never ran before fix F, so this is new behaviour: states flip at once and attack range is 0. Wasp may have the same problem, unverified in Play.
2. **F: BPC_PotionBelt ppSetHealLeft72 / ppSetDamageTaken69:** dt = `FClamp(GetTimeSeconds - LastT, 0, 0.1)`. Fine at 30 and 60 fps. Under 10 fps healing falls behind (at 3-4 fps roughly a third of the rate, by the formula), and it stops if the HUD stops drawing, since it runs in DrawHUD. Remove the clamp: FMin(HealLeft) already limits it.
3. **F: BP_HitFeel CX_42 / CX_43:** hit-stop is dilation 0.08 + `Delay 0.005`, so it ends only on a tick. Near 66 ms at 30 and 60 fps, one whole frame (over 250 ms) at 3-4 fps. Low.
4. **F: BP_HeroLevelUpWatcher CX_14** uses a 0.3 s window on poll; below about 3 fps it can miss a level-up. Low. BP_ShockAudio CX_10 is safe, it scales by dt.
5. **F: DrawHUD holds game logic and input** (WasInputKeyJustPressed in Commander, Army, Barracks, SkillTree, PotionBelt; gold spending; the RQ queue at QTickIn). It works per frame, but it stops whenever the HUD is hidden. No fixed per-frame step found; self-adds in HUD are input-gated.
6. **Checked, no bug (F):**
   - No literal-alpha Lerp or literal-dt InterpTo on any Tick or in the HUD chain (no InterpTo in HUD at all). No GetFrameCount. No Timelines.
   - Per-frame random: ArmySplit runs at 0.5 s, ZombieCharge at 0.5 s.
   - Berserk CX_37, Infection iSetDamageTaken143, HeroAuras CX_454 are one-shot or time-gated.
   - Timers under 0.05 s (Cannonball Grow 0.02, ZombieRisen RiseStep 0.03): RiseStep uses time. Grow adds 0.65 per fire, and G: UE catches up looping timers, so it stays correct but chunky at low fps.
   - BP_SoldierSword CX_178, CX_571, CX_592 are one-shot on events, by context. Not all paths were read: crowd should recheck.

**Not frame rate, but found (F, by graph, not seen in Play):** BPC_Flares fxSetFWas32 > fxIfBuy33, BPC_Medics mdSetMWas40 > mdIfM41, BPC_Cavalry ccSetLWas49 > ccIfL50, BPC_CastleUpgrades cuSetJWas62 > cuIfJ63 set `KeyWas` **before** testing `Down AND NOT KeyWas`, so these shop keys can never fire. BP_CaveDoor and BP_TreasureChest use the right order. Fixing this changes behaviour: owner's call.

## C. Spawn and allocation churn in battle (F unless marked)
- **FX pooling:** all 49 SpawnSystem / SpawnEmitter nodes in the top 50 spawners use PoolingMethod None or unset. Per hit or shot: BP_Zombie 3, BP_FleshBrute 4, BP_CrossbowBolt 2, BP_Cannonball 7, BP_SoldierSword 1, abilities Whirlwind 6, Fissure 5, QuakeSlam 4. All are auto-destroy, so no leak; G: the cost is allocation spikes.
- **Actor per hit or shot:**
  - BP_BloodBurst from Zombie, Brute, Bolt x 2, Cannonball, Gore (SetLifeSpan present).
  - BP_CrossbowBolt and BP_SoldierBolt per shot (SoldierSword, ArmySplit). BP_SoldierBolt has no SetLifeSpan or DestroyActor of its own; G: its spawners set it (BP_ArmySplit SetLifeSpan_258, BP_SoldierSword CX_284 / CX_452), so probably no leak; check they target the bolt.
  - BPC_Gore337 per cut: limb + wound cap + burst + decal + MID (limb has SetLifeSpan; cap checks its parent at 1 Hz).
  - Fix: pool bolts and bursts.
- **Dynamic materials:**
  - Per instance: BP_JellyShieldAll CX_19 per shielded zombie, BP_JellyBlob CX_47 per hatch, BP_ZombieRisen, BP_SoldierSword x 3.
  - BP_JellyBlob CX_12 and BP_TentacleVitals CX_258 call Create every frame. G: UE returns the existing MID once made, so wasted calls, not a leak. Cache anyway.
  - BPC_MudPrints mpPrintMID64: one MID + one decal per muddy step; SetFadeOut is correct, bounded by Prints.
- **Timers and Delays:** looping timers die with their owner, so none leak (G: engine). Fix A-E targets Delay on corpses: BP_Zombie 11, BP_FleshBrute 11. PICKUP lists E as not yet run: confirm. Still open: BP_HalfHorseZombie HHZ_N102, BP_RealmWasp WSP_N146, BP_GateBreachLeaf x 5, all Delay on a Tick path; a second Tick cannot restart them, so they are harmless except after death.
- **Sound:** most PlaySoundAtLocation pass ConcurrencySettings None (e.g. BP_SoldierSword CX_179, BP_BlobMine BLM_N22). G: voice spikes in big fights; set a concurrency class.

## D. Systems that do nothing useful (F)
- **21 empty ReceiveTick nodes** (no exec wire): BPC_CastleScroll, BPC_Quests, BP_CourtyardFountain, BP_CreditsHUD, BP_MapCapture, BP_MineWorker, BP_MudPad, BP_NPC_Barracks, BP_NPC_Elder, BP_RainCurtain, BP_RealmDirector, BP_RevealStage, BP_RisenDirector, BP_SiegeDirector, BP_SoldierBolt, BP_StoneWallFountain, BP_TowerDirector, BP_UndergroundFog, BP_WallBreachCollapse, BP_ZombieTower and the Muster backup. G: the compiler drops them, so they cost nothing; delete for clarity.
- **Stubs:** BP_RealmDirector, BP_SiegeDirector, BP_TowerDirector are 12.7 KB with no logic, and none is placed.
- **Wave managers:** 6 placed, all with Tick + WaveTick. Other Blueprints use GetActorOfClass and get whichever comes first. **Crowd should decide** which is the host before removing any: fix A's ZombieReg lives on one.
- **Duplicate polling:** 5 per-frame zombie scans remain after fix A (ZombieHUD H2128, Minimap CX_116, HitFeel, ZombieVariety, JellyShieldAll). 3 soldier scans outside the soldiers (SFXWatch, SoldierLevelWatch, ArmyHUD). GetActorOfClass<WaveManager> per frame from 6+ Blueprints (Sway x 5, CastleGateControl, GateBreachLeaf, ZombieHUD, QueueHUD, MusicDirector).
- **MPC as global state:** game state (gold-shop flags, cooldowns, St, Shop, Seen0-6) lives in a Material Parameter Collection, read and written per frame by many Blueprints. G: each call has a world and name lookup and each write dirties a render resource. Too big to change now; note it.
- **Backups in Content:** BP_FleshBrute_BAK, _BAK322, BPC_Muster_v1, BPC_ObsidianSet_v2, BPC_VesnaTrade_v1 / v2. No other export references them: exclude from cook, or delete.
- **BP_TorchBearer** Step @0.4 s has no outcome (README_F, unfinished). Not placed on disk. BP_ZombieHUD H2104 / H2105 are a cut chain: dead code, harmless.

## E. Ranked fix list (all keep behaviour unless noted; gains are relative and unmeasured)
| # | Fix | Gain, why | Risk | Owner |
|---|---|---|---|---|
| 1 | Commander tag scan > CommanderRef (A4); FocusCheck SallyPort cached (A1) | **High** per edit: tag scans walk all actors (G), one is per frame, the other per soldier at 6.7 Hz | Low | free*; crowd |
| 2 | Registry reads for the 5 zombie + 3 soldier scans; spawn or hit events for HitFeel, Variety, JellyShieldAll (A5-12) | **High**: removes about 8 x N loops in the VM each frame, and scales with crowd | Medium: needs spawn / hit hooks; ZombieReg misses brutes | free, hook crowd |
| 3 | Half-horse and wasp Think: real interval + real seconds (B1) | **High** per enemy (sync path search per frame) and a real gameplay bug | **Changes behaviour**; needs the intended numbers from the author | free, ask first |
| 4 | BP_SoldierSword remaining scans, stagger (A1) | **High** but N x M | **High** (state in component positions, per PICKUP): only with Play tests | crowd |
| 5 | Tentacles x 10: shared trace, cached comps, tick only in a shock (A14-15) | **Medium**: 10 traces + 20 ticks with repeat lookups, always on | Low | free |
| 6 | Mines x 41: tick interval, cached MID and manager, off when unseen (A13, A21) | **Medium**: many idle ticks, including 19 GetActorOfClass | Low-medium: trigger delay up to 0.2 s | free |
| 7 | HUD early-outs for closed panels, minimap name array, cached refs (A2, A6) | **Medium**: every frame, for sure | Medium: nested chain, HUD held by #458 | free* |
| 8 | Chandeliers, Crossbow and HeroAuras widget cache, WornPlate attach once (A17-19, A24) | **Medium-low**: cheap, safe, small each | Low | free |
| 9 | FX PoolingMethod AutoRelease; pool bolts and bursts (C) | **Medium** for spikes, not average frame | Low-medium: pooled FX must reset | free |
| 10 | Remove spare wave managers (D) | **Low** after fix A | Medium | crowd |
| 11 | PotionBelt clamp (B2); empties and backups (D) | **Low** for fps; B2 fixes low-fps healing | Very low | free |

**On a strong PC at 60 fps:** 1, 2, 4 and 5-7 target the game thread, and matter most at full crowd. **On the T1000:** none should move fps until the GPU frame shrinks. B1 and the shop-key bug matter on any machine.

## Could not read or verify
- BPC_VesnaTrade's export has no `DrawTrade`, though BP_ArmoryHUD calls it (nodes around line 33277), so the trade draw path is unaudited. It is gated by Covering and Shop state. BP_CorruptionBubble_Hero (9 placed) is not in the 193. Actor defaults such as bCanEverTick, tick intervals set on assets, and InitialLifeSpan are not in the T3Ds.
- Graphs are from 11-03, instance counts from i5's disk. Node names in fixed Blueprints may have changed. "Always" analysis treats unknown branches conservatively.
