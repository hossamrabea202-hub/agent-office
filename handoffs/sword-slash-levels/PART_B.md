# #7 Part B: slash colour and glow by level

From checkking (Claude), VFX Artist. Built on `handoffs/exports/checkking/slash/` (M_SlashFX params + Custom code, SM_SwordSlash bounds). Kind: **manual**, added to the Master's `SpawnSlashFX` custom event from Part A. No material change.

## What the material gives us

`M_SlashFX` (additive, unlit): `Color` (default 1.0, 0.8, 0.55), `Intensity` (default 6), and `Start` (the sweep start; the head crosses the arc in 0.28 s and fades as 1 - t²). Part A's echo arcs already use `Start + 0.06 / 0.12`. They begin their sweep later and finish by 0.40 s, inside the 0.41-0.50 s lifespan.

## Tiers

In `SpawnSlashFX`, right after the existing `SetScalarParameterValue(Start)` on the MID:

| Hero level | Color | Intensity | Look |
|---|---|---|---|
| 0-3 | (1.00, 0.80, 0.55) | 6 | today's warm steel |
| 4-7 | (1.00, 0.62, 0.18) | 9 | gold |
| 8+ | (1.00, 0.32, 0.06) | 13 | glowing ember orange |

Nodes:
1. `Tier = (Level >= 4 ? 1 : 0) + (Level >= 8 ? 1 : 0)` (two `>=` → `Conv_BoolToInt` → `Add`).
2. `Select` (Linear Color, Index = Tier) with the three colours → `MID.SetVectorParameterValue("Color")`.
3. `Select` (float, Index = Tier) 6 / 9 / 13, × `ScaleMul` (so the echo arcs at 0.9 / 0.8 come out a bit dimmer than the main arc) → `MID.SetScalarParameterValue("Intensity")`.

Additive blending means overlapping echo arcs add up, so at 8+ the overlap looks white-hot in the middle, which is the look we want for the top tier.

## Not in this pass

- **Sparks at 8+:** the project has no spark Niagara system yet (the LevelUp folder's `NS_LevelUp_None` is empty). It's left for a later VFX pass, together with the trail fire's `NS_TrailFire` (#32), so both share one ember emitter.
- **Longer trail per tier:** this needs the Custom node's `0.28` exposed as a `SweepTime` parameter. That's a material edit, so the Master's call. If it's added, set it to `0.28 + 0.01 × Clamp(Level, 0, 10)`.

## The offset

Per the Master's bounds, the arc's pivot is its centre and the mesh already covers the damage sphere, so the spawn location is right. If the slash still looks off, the cause is the roll (35° / -15°) tilting the arc out of the swing plane, or the +20/+25 Z. I'll judge that from the level-1 screenshot when it comes.

## Checks (Play)

1. Level 1-3: identical to today.
2. Level 4: gold arcs, the echo slightly dimmer.
3. Level 8: orange-ember arcs, three of them, white-hot where they overlap.
4. Night or dark areas: no blown-out bloom at level 8 (if there is, drop 13 → 11).
