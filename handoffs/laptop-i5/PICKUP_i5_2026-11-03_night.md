# i5 core pick-up note (2026-11-03 ~21:45)

Seat `adjustedfilm (Claude)`, chat name **i5**. Fast chat: `http://100.87.149.123:8765` (`/read?after=N`, POST `/say`, uploads
`/upload?name=`). i9 works OFFLINE on the Master: nothing i5 does live reaches him; hand him scripts / zips, he applies + saves.
**Lesson (memory i5-live-edits-lost-on-rejoin):** i5 live map edits vanish on a Multi-User rejoin; saved assets survive.

## Standing role (Alien, 21:35): #472 AAA technical artist: battle, crowd, crisp image, logic
- Roadmap + audit: `handoffs/aaa-472/ROADMAP.md`; scanner `bp_smells.js` (whole-BP T3D -> per-event cost).
- Sent to i9 (chat 1270), waiting:
  - Fix 1: one pin, BP_Zombie timer `K2Node_CallFunction_ZB6` (Think) InitialStartDelayVariance 0 -> 0.25;
  - a profiled wave (request: stat unit / game / anim / ai + zombie count, into `handoffs/aaa-472/profile/`).
- NEXT (in order):
  1. Zombie registry in BP_ZombieWaveManager (array on spawn / death). It replaces the per-frame GetAllActorsOfClass on Tick and the scans in Think; cache gate / castle at BeginPlay.
  2. Significance (Think rate by distance, tick off when not rendered).
  3. Zombie AnimBP (blend space + additive directional hit reacts + death to ragdoll) instead of 40 x PlayAnimation (also kills the 678 "AnimBP mode" warnings).
  4. Crisp image after the CPU headroom: TSR 75-100 %, sharpen around 0.5.
- Fresh exports: `handoffs/exports/adjustedfilm/faults-1205/` (BP_Zombie, BP_ZombieWaveManager, BP_BattleDirector, ...).
- Tools: `handoffs/faults-1205/t3d_*.js`:
  - `t3d_arrays.js`: array reads;
  - `t3d_consumer.js`: the first exec consumer;
  - `t3d_node.js`: node pins;
  - `t3d_to_graph.js`: whole-BP T3D -> EventGraph copy for `applyall merge`.

  Generate pastes with `tools/laptop2/bpgen/bpkit.py`. Run Python with Blender's (`C:/Program Files/Blender Foundation/Blender 4.5/4.5/python/bin/python.exe`).
  **Check every generated getter against the live VariableReference (MemberParent!) before hand-off** (F11 Muster v1 failed on that).

## Handed to i9, not yet confirmed applied
| Card | What | Where |
|---|---|---|
| #470 | REMOVE fake crack overlay from 6 stone base materials (code lines, params, texture), backup _bak470 | `handoffs/castle-harmony-461/remove470_ue.py` (chat 1259); supersedes crack470_ue.py |
| #469 | 9 stairs re-baked at true size, scale 1, W2 look | zip `/files/205147_i5_469_stairs.zip`, `stairs-447/work/stair469_ue.py` (1250); supersedes the #301 W2 override fix |
| #455 | fire pit logs without overlaps | `handoffs/firepit-455/README.md` |
| F11 Muster v2 | RQ comes from BP_BarracksHUD via the live getter vGetRQ136 | `handoffs/faults-1205/f11/muster_merged.txt` (1240, re-pinged 1261) |

## Waiting on others
- **#469 stone sizes:** owners asked for course height / block length (chat 1247). Tower9 is placed at 1.2 x 1.2 x 1.0 = stones 20 % stretched: asked i9 / TGA_PC (1246).
- **#450 tentacle hit reaction:** clip `AS_Tentacle_HitReact450` imported; wiring needs a BPC_TentacleSpit + BP_TentacleVitals export (request filed). Alien undecided; decision: wire it in as is.
- **#457 tentacle idle polish:** 3 clips imported; swap all 8 after Alien's OK (`tentacle_anim_ue.py swap --apply`).
- **#458 HUD polish:** needs a fresh BP_ZombieHUD export + 4 screenshots (request filed). Found: ORE / FOOD text collides with the troop icons.
- **#453 Gothic set:** the BPC_ObsidianSet v4 graph is ready (`gothic-set-453/wiring`). It waits for TGA1's 11 meshes + a fresh Vesna export after TGA1's #446.
- **#440 grass:** phase A applied by i9. Phase B open: the ground colour is driven by the parent Landscape (proxies ignore a Python set; GrassTint did NOT change the meadow ground, so read the M_MountainBackdrop graph first), plus feathering the meadow edge.
- **#461 harmony report:** `castle-harmony-461/HARMONY_master.md` (4 stone looks, 387 Tower9 grime cards, old-kit split TGA_PC / i5).
- **New from Alien via i9 (1256):** the Obsidian complete-set effect as an activatable skill (skill bar icon, cooldown, key). i5 said yes; it is not started.
- Released to others (1268): F1 -> TGA1, F9 -> TGA.

## Done today (all pushed)
- #301 stairs saved;
- #440 grass phase A;
- #453 v4 graph;
- #457 idle clips;
- #461 scan + report;
- F3 / F12 (applied by i9);
- F11 shield (applied);
- #455, #469, #470 scripts.
