# i5 core pick-up note (2026-11-03 ~08:00, context 88 %, weekly plan 85 %)

Seat `adjustedfilm (Claude)`, chat name **i5**. The owner (Alien) talks to i5 in the app; i9 drives the Master and saves.
Fast chat: `http://100.87.149.123:8765/read?after=N`, post with POST `/say` (plain text body, "From: i5: ...").

## State right now
- i5 editor restarting after applying i9's zips **1103_k..n** (backups `C:/UnrealProjects/CD58_backup_before_sync9_1103`;
  earlier syncs: sync7 = 1102_i..1103_b, sync8 = 1103_c..i). Restore list set aside as `PackageRestoreData.skipped_1103_0800.json`.
  JOIN_LIVE.bat starts on the Entry map; `a1_loadmap.py` in the inbox opens ThirdPersonMap after the join.
- "Server CastleDefenderServer lost" right after a join is a ~75 s discovery blip, not a disconnect (check
  `MultiUserClientStatics.get_multi_user_connection_status_detail()`).
- i9 rule (chat 906): **no editor scripts while Alien is in Play** (crash).

## Done this morning (all pushed)
- **#451 castle polish batches 1-6** (i9 re-ran + saved on the Master at 02:34): duplicates hidden, 36 original blocks
  restored, courtyard paving plates hidden, forge hearth stone (per-instance), 3 white cubes hidden, fire-pit log teepee
  (`SM_FirePitLogs451`). README: `handoffs/gpt-review-polish/README.md`.
- **#301 AAA stairs**: all 9 kit flights `Stair279_01..09` use `SM_StairBaked451_N13/N20/N31`
  (`/Game/CastleDefender/Environment/Castle/StairsBaked451`), built on the #447 pipeline (`handoffs/stairs-447/work/
  build_stair.py` + `spec_kit_N*.json`, `solid` option; `stair_baked451_ue.py assets|swap|check`). Collision trace OK
  on all 9. 91 old stair grime cards deleted (`remove_old_stairs451_ue.py`, record + `--restore`). **Not saved: i9 must
  save + Play-walk + show Alien (chat 923).** Open question to i9 (chat 928): point the stair MIs at his new
  `M_CastleAshlarWeathered2` look so stairs match the keep + walls.
- **#453 Landshut Gothic set**: research + 11-piece spec + sizes (`handoffs/gothic-set-453/RESEARCH.md`). TGA1 models.
  i5 does the shop/bundle/tier wiring once i9 sends fresh exports of BPC_ObsidianSet + BPC_VesnaTrade.
- **#440 mountain grass**: research + 7-step plan (`handoffs/grass-mountain-research/RESEARCH.md`), step 1 inventory
  done (`grass_inventory.txt`). Steps 2-7 wait for Alien's OK.
- **#452** card for TGA: forge re-UV, mine rock, gate leaves to the arch, arrow loops, keep stair slabs.

## Next for i5 (in order)
1. LESSON: unsaved session changes are LOST when i5 restarts (08:00 the 9 stair swaps reverted to the kit). Re-applied at 08:05 (check OK). Never restart i5 before i9 has saved i5's live changes.
2. Read i9's answer (chat 928) and re-point `MI_StairBaked451_N*` to the keep's new weathered look if he says so.
3. #453 wiring when the exports land. 4. Grass steps 2-7 after Alien's OK. 5. #452 items not taken by TGA.
Rules learned: lookdev captures below the clouds, small, 1-3 per script (2 GB GPU); A/B with `lit_ab_ue.py`
(temp light 20-60 cd); wait for streaming before judging; never bake on the GPU while rendering lookdev.
