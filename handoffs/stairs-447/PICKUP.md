# Stairs #447: pick-up note (i5, updated 2026-11-02 19:45)

PILOT DONE and handed to i9 (chat, zip /files/193403_stairs447_courtyard_v1.zip). See README.md.
- Courtyard F2+F3 = SM_Stair447_Courtyard34 (one watertight asset, 296 tris, 4K bake, M_Castle_StairBaked + 2 MIs).
- Assets are saved on i5 in Content/CastleDefender/Environment/Castle/StairsBaked. The i5 map has the trial apply
  (NOT saved). i9 applies on the Master and saves.
- Before/after shots: build/before_*.png, build/after_*.png. Lighting in the shots is a harsh temp light, because the
  editor world is at night.

## Next
1. Wait for i9's Play check on #447. Fix anything it reports.
2. Roll out the other flights with new spec files. Each needs a `STAIRS` entry in `apply_stairs447_ue.py` with `old_boxes`;
   check for merged stones with `merged_box.py`. Pairs: F0/F1, F4/F5, F14/F15; singles: F17, F18; keep dog-legs
   F9+F10+F11 and F12+F13 (these need an L-shaped profile: extend build_stair.py); keep steps F6/F7/F8, F16.
3. Pack the UVs tighter for big flights (about 40 % empty in the pilot).
