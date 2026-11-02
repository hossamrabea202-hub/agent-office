# Stairs #447: pick-up note (i5, 2026-11-02 19:20, written before a forced Windows restart)

Owner (Alien): "each staircase must be 1 watertight asset, low poly baked out of high poly, the AAA way". The
project is being finalized, so hand over finished, game-ready results. TGA1 does the store (#446, chat line 656);
i5 does the stairs.

## State
- Study done: `STUDY.md` (19 flights, dimensions, transforms, materials, tones, bevels).
- Raw data on i5 in `C:\Users\hossam.rabea\ckw\stairs\` (also copied to `work/` here):
  - `castle_pieces.json`, `flights.json`, `refs.json`, `refs/*.fbx`
  - dump scripts `*_ue.py`
  - `flights.py` (flight finder)
- Builder: `build_stair.py` (Blender 4.5):
  - `-- build <spec> <out>`: low + high + low FBX + report
  - `-- bake <spec> <out> 4096`: N + packed masks
- Pilot spec: `spec_courtyard34.json`, for F2 and F3, one asset placed twice with no mirror:
  - F2 origin world (1250, 495, 0)
  - F3 origin world (1250, 2775, 0)
- **F3's parapet side is not checked yet.** F2's parapet is at UE local y 230–275, toward the courtyard. Check F3 with
  `around.py 1200 2700 3 2400 2775 900`. If F3's parapet is on the low-y side, place F3 with scale Y = -1 at y = 3005.
- First build run hit a typo (fixed at 19:20, not re-run yet).

## Next, in order
1. DONE 19:19: build OK, watertight, 0 non-manifold edges, 304 tris low, 1.64M tris high (out/ in ckw/stairs). Look at it before baking.
2. Close the UE editor (it holds the 2 GB GPU), then run the bake at 4096 on OptiX. Reopen the editor after.
3. UE (offline editor, i9 owns the map). Write `apply_stairs447_ue.py` with `--dry-run` / `--apply` / `--revert`:
   - Import the FBX to `/Game/CastleDefender/Environment/Castle/StairsBaked/`:
     - no Nanite
     - generate lightmap UVs
     - complex collision off; the invisible `Collision/StairRamps` stay as walk collision
   - Textures:
     - `_N` imported as normal with flip green
     - `_M` imported as linear masks
   - Material `M_Castle_StairBaked`:
     - a duplicate of `M_Castle_StoneWall_World`
     - the baked normal blended over the world normal (BlendAngleCorrectedNormals)
     - AO multiplied in
     - joint darkening, wear lowers roughness, stone tone varies the tint
   - MIs:
     - `MI_StairBaked_Tread` uses StepCap values
     - `MI_StairBaked_Body` uses StoneWall values, limewash 0.5
   - Place the asset at F2/F3. Hide the old pieces without deleting them: move them to the `Stairs_Old_447` folder.
   - Old pieces for F2: treads and caps in `flights.json` F2, Trim `SM_StoneModule_17..29` at y 499–721, and
     StoneWall `SM_StoneModule_19..27` at y 730–770. Keep paving, bench, decals and StairRamps.
4. Lookdev shots (960×540, below the clouds, cloud and fog off), then a zip for i9 plus a chat note. Roll out the other
   ~10 assets with new spec files, after Alien's OK.
