# adjustedfilm (Claude): every open card, one list (updated 2026-10-31 late night)

The owner, 2026-10-31: *"i feel you are just opening new mini quests and not finish earlier ones"*. This list holds every
card on this desk, oldest first. A card closes only when it is **in the game and checked**. Keep it updated at every
session start and end.

## FOCUS 2026-11-01: #390 WinterKeep (owner: "everything on the map is your job now")

Polish v2 done 2026-11-01 (committed, posted on #390): real Blender assets (spruce A/B, birch, 2 boulders, icicles,
frozen falls, 46 m arch bridge, half-buried farmstead), FBX + pbr-checked textures in `winter-map/assets/out`; UE
`--step meshes` + `--step props`; dress uses our meshes; terrain gorge fix (the old gorge was a road fill); lookdev uses
the real meshes, snow glints, rock texture, blizzard multiple scattering, 3 prop shots.
Session 3 (2026-11-01): snow trails handed off (#394: MPC_WK_Snow, RT_WK_TrailA/B, own POM branch in M_WK_Landscape,
BPC_SnowTrails 121-node graph on the level actor BP_WK_Snow, `--step trails`); snow VFX handed off (#395, vfx/README.md:
scripted 3D snowfall shells riding the camera, landscape snow snakes, Niagara spindrift clicks + `--step drift` on 24 ridge
spots); blizzard = extinction 0.026/m (Blender) / UE fog at castle height, falloff 0.03, white albedo.
Next, in order: (1) fix whatever the Master logs in `ue/wk390_log.txt` / on #390 #393 #394 (nothing yet; all UE steps are
untested); (2) re-render + post the 4 presets if not posted (`lookdev/render_winterkeep.py`, make_sheet.py); (3) spruce snow
cushions: DONE (flat pads). DONE 2026-11-01 morning: falls (no square back plate, wide lip + flared apron, milky ice
with blue flow lanes, 6 m tile) and the bridge-end wall (spill-through embankment cone, gen_terrain.py; heightmap + scatter
regenerated, deck z unchanged 5247.3).

## Closed today (in the game, checked by the Master)

#277 flares, #283 cannon map, #313 / #314 toasts, #315 shop swipe, #316 breach, #322 Flesh Brute (waves + animations),
plus #296 cave rock (closed by me after the owner's OK).

## New since the evening list

| Card | State |
|---|---|
| #364 Lord of the Keep (MAIN gameplay) | design done; step 1 = Day Ledger on top of #369 (next session, needs BP_DayNight from the batch export) |
| #369 quests + daily rewards | v1 handed off (handoffs/quests-369), first on the paste list |
| #355 torch-bearer + #290 v2 | handed off (#357) |
| #362 cape slot | inside TGA's #361 redesign |
| #351 meadow | in the game (Master, radius 15000); polish open |
| #341 / #349 mine dungeon + miners | placed; the miners are next on the Master's list |

## Midnight status (see the README pick-up section for details)

- In the game: #381 realm vision v2 (owner Play test + jelly swap OK pending), #188 recruit queue (play test pending).
- Handed off, not pasted: #294 cannonball bounce.
- Next for me: Day Ledger on #364 (close the duplicate #385).

## Fixed tonight (late night session), waiting for the Master

| Card | Hand-off | State |
|---|---|---|
| #269 reveal (OWNER PRIORITY) | #374, `handoffs/reveal-aaa-268/FIX269.md` | setup `--fix269` + v3 graph (516 nodes); item kept by depth, Movable stage, holds to 3.2 s. If still empty: diag `--replay` then `--probe` |
| #351 meadow roads | handoffs/meadow-351 (README bottom) | road mask: road decals, *Road*/*Path* actors, hand-cleared band, `--band` |
| #366 tentacle skin stretch | handoffs/tentacle-skin-366 | `--info` first; material copy `*_UV366`; swap only on the owner's OK |
| #350 / #349 / #341 fixes | #371 / #372 / #373 | no Master result yet |

## 1. My work (nothing blocks it): do these first

| Card | What is left |
|---|---|
| #351 meadow (grass + flowers + bushes), **owner complaint** | script handed in, waits on the Master's run + before/after; re-run when TGA's flora kit #352 lands |
| #339 multiplayer | plan + audit posted; slice 2 starts as soon as the owner says "split-screen first" (or online) |

## 2. Built and handed off: waiting for the Master to paste and test

| Card | Hand-off | Note |
|---|---|---|
| #3 tentacle hits a cannon (10-27) | v2 bone curl, README_CURL.md | asked the Master on the card: in the game or not? |
| #24 death text by cause (10-27) | handoffs/death-text-24 | **built today** (it had been forgotten since 10-27) |
| #11 survivors | #272 | |
| #44 zombie towers | #325 | |
| #157 realm distortion | #286 | |
| #185 medics | #289 | pasted; the HUD line waits on #285 |
| #224 castle upgrades | #282 | pasted (Master 10-31); needs a play test, then close |
| #226 weather | #275 + #290 | |
| #228 wall-walk tops | fix line on #306 | |
| #266 antidote (PRIORITY) | #307 | |
| #268 pickup reveal | #269 + #374 | fix handed off (#374) |
| #277 flares | #278 | waits on the compile-warning text |
| #283 cannon map | #285 | the Master's next item (10-31) |
| #292 mud prints | #298 | |
| #295 notice scroll | #303 | |
| #297 cave dungeon | #310, place_mine297, mine_workers297 | parts 1, 3 and 4 handed off |
| #313 / #314 toasts | #318 | |
| #315 shop swipe | #319 | |
| #316 breach | #328 | part B waits on `breach_dump.json` (#326) |
| #322 brute | #324 + #340 | #340 keeps the Master's bite-15 edit |
| #334 risen soldier, part A (neck) | handoffs/risen-334 | |
| #337 blood + severing | Blood337 assets + handoffs/gore-337 | the BP_BloodBurst rebuild waits on its export |

## 3. Waiting on data from the editor (requests filed)

| Card | Waiting for |
|---|---|
| #183 skill-gain pop-up | #291: screenshot + the name of the BP that draws it |
| #293 blobs, part 3 | the HLSL of M_JellyBlob's Custom node (the Master copies it next time in the editor) |
| #333 tentacle scorpion strike | #336: fresh BPC_TentacleStrike export (design is on the card) |
| #334 part B (corpses fade) | #335: BP_ZombieRisen + BP_SoldierSword export |
| #337 blood burst | BP_BloodBurst export |

## 4. Waiting on the owner

| Card | Question |
|---|---|
| #293 parts 1 and 2 | OK to swap the realm bubble and the blob-mine flesh look (lookdev copies are in the game)? |
| #302 multi-user | run `check_pc.ps1` on each PC |
| #339 | split-screen first, or online straight away? |

## Not mine any more

- #1 ShadowknightUE_SK export: editor-only, moved to the Master's queue (checkking re-filed it).
- #201 mine + carts: built by laptop2.

## 2026-11-01 14:58 pick-up (adjustedfilm (Claude), laptop-i5)
- DONE: 5.8 paste fixes (874d888): 5 graphs PureState=Pure, DoesSaveGameExist on exec chain, fix_impure skips PureState=Pure casts, 9 setup scripts 5.8-safe. Not touched: tools/master/h113/bp_create.py.
- DONE: project copied to `C:\UnrealProjects\Castle Defender 5.8` (low settings in Saved/Config/WindowsEditor, MultiUserClient in .uproject, DefaultGame.ini bAddPacks=False). Editor start ~12-17 min.
- DONE: i5 joined Multi-User session CastleDefender over Tailscale (#408). Launch args: -CONCERTAUTOCONNECT -CONCERTSERVER=CastleDefenderServer -CONCERTSESSION=CastleDefender -CONCERTDISPLAYNAME=Laptop-i5 -UDPMESSAGING_TRANSPORT_UNICAST=100.80.81.18:0 -UDPMESSAGING_TRANSPORT_STATIC=100.87.149.123:9030
- NEXT: #408 live test (move one actor, Master confirms), then job 2 = #390 rime/SSS/glint lookdev (Blender, render_winterkeep.py), job 3 = WK_Test --step meshes command list in second-editor/README.md.
