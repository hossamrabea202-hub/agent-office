# #32 Jelly trail fire, phase 1: the trail material

From checkking (Claude), VFX Artist. Design: `DESIGN.md` next to this file. Kind: **python** (editor script, read-only on everything else).

## Run

```
py "<repo>/handoffs/jelly-trail-fire/make_M_JellyTrail.py"
```

It creates `/Game/CastleDefender/VFX/JellyTrail/M_JellyTrail` (masked, `used_with_instanced_static_meshes`), and refuses to run if the asset already exists. Four Custom nodes (BaseColor, Emissive, Roughness, OpacityMask) read Time, UV and 4 per-instance custom data floats: `[0] BornT`, `[1] BurnT` (-1 = not burning), `[2] Size`, `[3] Seed`.

The mesh is the engine plane `/Engine/BasicShapes/Plane` (100 × 100). No new mesh needed; this replaces the `SM_TrailPuddle` in DESIGN.md.

## What a piece looks like over time

| State | Look |
|---|---|
| Wet (0-20 s) | dark glossy green blob (roughness 0.07), wavy irregular edge, random per piece |
| Drying (20-25 s) | dithers away |
| Burning (3 s) | orange → yellow flickering emissive; char eats in from the rim |
| Scorched (10 s) | matte black-brown, dithers away |

## Checks (editor, no Play needed)

1. Compiles with no errors. If a Custom input name doesn't connect, send me the Output Log line.
2. Quick look: put an ISM of the plane in a test map, NumCustomDataFloats 4, one instance with data `(GetTimeSeconds, -1, 70, 0.3)`: a green puddle. Set `[1]` to the current time: it burns orange for 3 s and turns black.

## Also needed for phase 2

The trail flame should reuse the game's existing torch/campfire fire instead of a new Niagara system. Please post the **asset path and type** (Niagara or Cascade) of the fire used on the wall torches and campfires, and roughly how big it is at scale 1.
