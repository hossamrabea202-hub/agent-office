# Paste order for the Master: adjustedfilm's hand-offs (2026-10-31 evening)

Go top to bottom. Each line is one sitting. The order puts owner priorities first and keeps changes to the same
Blueprint together, so one export serves several merges. **Skip a line if its "needs" line is not in yet.**

## A. Owner priority and quick wins (about 30 min)

| # | Hand-off | Blueprint(s) | Needs |
|---|---|---|---|
| 1 | **#307 Antidote (PRIORITY, the infection cure)** | BP_NoticeHUD (merge) + icon import | — |
| 2 | **#318** tiny toasts, press-T reminder, "all cannons mounted" | BP_NoticeHUD (merge on the same fresh export after #307) + BP_BarracksHUD | #307 |
| 3 | **#354** death screen says what killed you | BP_ThirdPersonCharacter (1 BPVar + merge) + BP_ZombieHUD (merge) | — |
| 4 | #319 Vesna A/D swipe | BP_SkillTreeHUD | (you were on it) |

## B. The HUD chain in BPC_MotionFX (in this order)

| # | Hand-off | Needs |
|---|---|---|
| 5 | **#285** cannon scroll map | #239 (done) |
| 6 | #289 step 5: the medics HUD line | #285 |

#269 (the reveal) is in; it waits on the PIE diagnostic `diag_reveal268.txt`.

## C. The fight feels better (waves, enemies)

| # | Hand-off | Blueprint(s) | Needs |
|---|---|---|---|
| 7 | #324 brutes join the waves | BP_BruteDirector (new) | — |
| 8 | **#340** brute animation polish (whole-graph replace, keeps your bite-15 edit) | ABP_FleshBrute (new) + BP_FleshBrute | #324 |
| 9 | #325 zombie towers | 2 new BPs | — |
| 10 | **#350** blood splats + limb severing | 3 new BPs + BP_Zombie merge (after the Blood337 import script) | — |
| 11 | #344 risen soldier neck | retarget + ABP, BP_ZombieRisen defaults | — |
| 12 | #328 breach crash, dust, shake | BP_BreachFX (new) | — |

## D. The world

| # | Hand-off | Needs |
|---|---|---|
| 13 | **#356 TGA flora import**, then **#351 meadow script** (owner complaint) | — |
| 14 | #310 cave door → #341 mine dungeon → #349 miners | in that order |
| 15 | #275 weather → **#357 torches v2 + torch-bearer** (it replaces #290: **don't paste #290**) | #275 |
| 16 | #272 survivors, #321 treasure chest, #298 mud prints, #286 realm distortion | — |

## E. Looks (owner OK needed first)

- #303 notice scroll: rebuilt in place, with a backup.
- #306 wall-top tiling fix: dry-run first, reversible.
- #305 realm bubble and #329 blob-mine flesh: these swap only after the owner's OK on the lookdev copies.

## Already pasted: needs a play test, then close

- #282 castle upgrades: pasted 10-31.
- #289 medics: pasted, except step 5.
- #278 flares: has a compile warning; please paste the warning text on #278.
