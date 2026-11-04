# NEXT AGENT - castle stone (i9 Master, 11-04 ~12:40)
## State
- C: has ~138 GB free (Alien cleared the UE cache). Shader/Nanite cache rebuilds once, then stays.
- Sharp stone builder verified: sync58/tunnel/gen_boxmason.py (SHARP default), gate = sync58/tunnel/lookdev_stone.py fold check, must print inverted 0.
- Rebuilt + SAVED: CurtainMasonry (25), BlockoutMasonry (49), KeepMasonry (129).
- Running/last: Tools/PasteRegen_1027/sharp_rest.ps1 (gate, stair cheeks, arcade, entrance, nav, save) -> log sync58/sharp_rest.log. Check it, then close-up render (bgshot) at the stair cheek and arcade, nav must be 8/8.
## What the free disk lets us do
1. No more failed saves: Nanite builds/saves need GBs; today 190 saves failed at 0 GB.
2. #491 stone KIT (this folder): kit FBX, cache, backups during the swap fit; afterwards the castle uses LESS disk than the giant merged walls.
3. Keep the shader cache: faster editor + Play after the first rebuild.
4. Better stone texture: room for a 4K-8K ashlar scan cooked to 2K (needs Alien's download OK).
5. A Shipping build to test FPS on a strong PC + a real project backup before big changes.
## Keep it that way
- Pipelines delete their FBX right after import (sharp_all.ps1 does). Stop below 4 GB free.
- After the kit replaces the merged walls, archive/remove the old wall meshes ONLY with Alien's OK.
## Next
1. Finish/verify sharp_rest (above). 2. #491 kit: TGA_PC blocks, i5 layout JSON, i9 HISM spawner + PerInstanceRandom (README.md). 3. i5 queue: E2 (5 scripts, README_E2.md), wave_sweep_ue.py + stat unit in a wave. 4. Courtyard-side crenellations -> plain parapet (i5 merlon kit #488 waits on Alien's look OK).
