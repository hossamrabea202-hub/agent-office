# #539 Tentacle rocky spore base (adjustedfilm, 2026-11-06)

Owner: "build a spore like tanticle rocky base shows the sprouting out of ground impsact".

**What it is:** one mesh, about 190 m wide at nominal size. Crust heaved up with cracks radiating from the wound, 58 rock slabs thrown outward, rubble, roots gripping the ground, and clusters of fungal spore sacs, some burst open. Its edge dives under the terrain on an irregular line, so no circle shows.

**Decisions:**
- One mesh, turned to a different angle per tentacle. A second variant is only a seed change.
- Nanite, about 880k quads. Vertex colours hold albedo and roughness, so there are no baked textures. Starter Content rock slate adds tiling fine detail, 1 tile per 5 m at nominal size.
- New material and new actors only. No live material or decal is touched, and decals still land on it by default.

## Steps (Master, editor idle, not in Play, main level open)

1. `git pull`.
2. `py handoffs/tentacle-spore-base-539/sporebase_ue.py --dry-run`. Every tentacle should print its ground, height and width. No SKIP lines expected.
3. `py handoffs/tentacle-spore-base-539/sporebase_ue.py --only Env_CorruptedTentacle_02,Env_CorruptedTentacle_05` and look at both. Then run with no flags. Save the level.
4. Play.

Remove: `sporebase_ue.py --revert`, then save the level. Tuning in `M_TentacleSporeBase`: `DetailTile`, `DetailMean`, `DetailAmount`.

## Tests

- The throat hugs the arm with no gap, including during strikes, on normal and mirrored tentacles.
- The edge meets the terrain with no floating lip, also on slopes. It is placed level, not tilted to the slope.
- Colours sit with the terrain in the real light. If too dark or light, change `DetailMean`.
- Frame time near a base is steady.

## Tested, and not tested

Lab, headless, with a temporary level and one mirrored tentacle: dry-run, import (extent 95 m, Nanite on), material builds, 2 bases placed at the right centres and scales, re-run replaces them, revert removes them.

Albedo checks on the vertex colours: sRGB luminance p1 35, p50 78, p99 141, 0 % below 30, 0 % above 240. Roughness 0.22 to 0.99. `pbr_check.py` reads textures, so it does not apply here; the same limits are measured in `gen_sporebase.py`.

**Not tested:** it has never rendered in Unreal. The previews are Blender Cycles lookdev with locked exposure and a grey ball. Unconfirmed: its look with the final material, its fit on the real terrain, and frame time.

**Known limits:**
- **No collision:** the hero and soldiers walk through the rocks. Roots and slabs are visual only.
- **Spores are still:** nothing puffs yet. A drifting spore effect needs Niagara, which cannot be authored by script.
- **Terrain colour:** the edge has no blend with the terrain colour, only the dive under it.
- **Size:** the FBX is about 55 MB.

## Previews

`preview/SporeBase_before_far.png` and `SporeBase_after_far.png`, `SporeBase_top.png`, `SporeBase_near.png`. Generator: `gen_sporebase.py`. Lookdev: `lookdev.py`.

## Rules applied

Knowledge base 1 (calibrated values), 2 (locked exposure, grey ball), 3 (layers with a physical cause), 5 (grounded, sunk, debris skirt). INDUSTRY_SECRETS 0.3 and 0.10.
