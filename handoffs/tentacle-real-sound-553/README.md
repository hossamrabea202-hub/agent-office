# Owner's last 4 jobs (adjustedfilm, 2026-11-06)

**Not tested in Play. Nobody has listened to the sounds in game.** Run with the editor idle.

## 1. Real recorded tentacle sounds
```
py handoffs/tentacle-real-sound-553/real_sounds_ue.py --dry-run     then --apply
```
Replaces the 6 synthesised waves in place, so nothing else changes. Mixed on your PC from packs already in the project; no pack audio is in the repo. Lab: apply, revert, apply pass. `--revert` restores the old ones.

Check in Play: roar, groan, rumble, burst, spit and splat sound like real creatures and wet impacts, at a sensible volume.

## 2. First-eruption camera, for your BP_TentacleEruption
Numbers: `handoffs/tentacle-eruption-cinematic/camera_path.py`, the KEYS table and the rules above it. Breach at 2.2 s. Layout check on stand-in shapes: `preview/camera_sheet.png`.

## 3. Chained zombie sparks and smoke
`P_Sparks` and `P_Smoke` are in `/Game/CastleDefender/AssetPacks/StarterContent/Particles/`. The script now points there. Either set those two on the BP's emitter nodes, or re-run `chained_zombie_ue.py`. Re-running was not tested on your applied copy.

## 4. #483, the 2 stopped ops
Export these two fresh: **BP_BarracksHUD** (needs `rqFindNPC_Barrac39`) and **BP_SoldierSword** (needs `CX_499`, `CX_518`). Put them in `handoffs/exports/master/2026-11-06c`. i5 rebuilds the ops when they land. The card was closed on the owner's order; reopen it.

Also for the owner: `GateCannons` default still needs a decision.
