# #390 WinterKeep: snow VFX (falling snow, ground drift, ridge spindrift)

By `adjustedfilm (Claude)`, 2026-11-01. Everything follows **one wind**: from 315° (NW), set in `MPC_WK_Snow`
(`WindYaw`, `WindSpeed`) with the weather amount in `SnowFall` (INDUSTRY_SECRETS rule 10). `--step light --preset ...`
sets them:

| Preset | SnowFall | WindSpeed |
|---|---|---|
| overcast | 0.3 | 3 m/s |
| lowsun | 0 | 2 m/s |
| blizzard | 1.0 | 14 m/s |
| night | 0.15 | 2 m/s |

**Decision:** the #226 rain is not a Niagara system. It is a material curtain on camera cylinders (`M_Rain` on
`BP_RainCurtain`). So falling snow copies that method, which is fully scripted with no clicks, but it uses real 3D
flakes. Niagara is used only for the spindrift plumes on ridges, because that needs real particles.

## 1. Falling snow (scripted, no clicks)

`py S --step assets` builds `M_WK_Snowfall` plus `MI_WK_Snowfall_200/400/800`. `py S --step trails` adds 4 shells to
`BP_WK_Snow`, and `BPC_SnowTrails` attaches `WK_Snow` to the camera every second.

- Each shell shows the flakes inside one slab: 1–2, 2–4, 4–8 and 8–16 m. The flakes are world-space points, so they
  don't swim when the camera turns.
- The flakes fall at 1.1 m/s, are carried by the wind and flutter ±4 cm. Each streaks over a 1/60 s shutter, with its
  energy kept.
- Density = `SnowFall`. Flakes are lit translucent with albedo 0.82–0.86: grey against an overcast sky, white against
  dark trees, dim at night.
- Offline check (numpy port of the shader): `trails/preview_snowfall.py`, output in `trails/snowfall_*.png`. Coverage is
  1.2 % in overcast and 3.4 % in a blizzard. Past 16 m the height fog carries the white-out.

## 2. Ground drift (scripted, in M_WK_Landscape)

"Snow snakes" are wisps of loose snow (albedo 0.86, roughness 0.8) that stream over the snow layers along the wind at
0.6 × the wind speed. They start at 5 m/s, the snow-transport threshold, and are fully on at 11 m/s, so you see them in
the blizzard. They also soften track and ripple normals, which is how trails get buried.

## 3. Ridge spindrift: NS_WK_Spindrift (Niagara, about 25 clicks, once)

`py S --step assets` has already made the sprite material `Materials/M_WK_SnowPuff` (soft grainy puff, lit, uses
Particle Color).

1. **Content Browser:** open `/Game/CastleDefender/WinterKeep`, make a folder `VFX`, open it. Then right-click,
   **Niagara System**, **New system from selected emitter(s)**, **Next**. Pick the template emitter
   **Fountain**, click **+**, then **Finish**. Name it **NS_WK_Spindrift** and open it.
2. **Emitter Properties** (click the emitter name):
   - Sim Target **GPUCompute Sim**
   - Local Space **on**
   - Calculate Bounds Mode **Fixed**: Fixed Bounds Min `(-600, -1000, -300)`, Max `(3200, 1000, 1200)`
3. **Emitter Update > Spawn Rate:** SpawnRate **250**. (The weather gate is in step 8.)
4. **Particle Spawn:**
   - **Initialize Particle:**
     - Lifetime Mode **Random**, 2.5 to 4.5
     - Color `(0.84, 0.86, 0.88, 0.35)`
     - Sprite Size Mode **Random Uniform**, 6 to 18
     - Mass 1
   - Delete **Add Velocity** (the fountain cone). Add **Add Velocity**, Velocity Mode **Linear**, then from the dropdown
     **Random Range Vector**: Minimum `(700, -150, 50)`, Maximum `(1300, 150, 300)`. Local X is downwind; the actors
     are placed at yaw 45 = toward the SE.
   - Add **Shape Location**: Shape **Box**, Box Size `(300, 1400, 40)`. This is the crest line, across the wind.
5. **Particle Update:**
   - Delete the fountain's **Gravity Force**. Add **Gravity Force** with Gravity `(0, 0, -250)`: grains settle slowly.
   - Add **Drag**, Drag 0.8.
   - Add **Curl Noise Force**: Noise Strength 450, Noise Frequency 0.003.
   - **Scale Color**: Scale Mode **RGBA Linear Color Curve**. Alpha curve: 0 at 0, 1 at 0.15, 0.6 at 0.7, 0 at 1.
   - Add **Scale Sprite Size**: uniform curve 1 at 0, 4 at 1. The plume spreads.
6. **Render > Sprite Renderer:**
   - Material **M_WK_SnowPuff**
   - Alignment **Unaligned**, Facing Mode **Face Camera Position**
   - Sort Mode **View Depth**
7. **Emitter Properties > Scalability:** Cull by distance on, Max Distance 70000 (700 m).
8. **Weather gate:**
   - Content Browser, right-click, **Niagara > Niagara Parameter Collection**. Name it **NPC_WK_Snow** and set Source
     Material Collection = **MPC_WK_Snow**. Save.
   - In NS_WK_Spindrift, **Spawn Rate** dropdown, **Dynamic Inputs > Multiply Float**:
     - A = 250
     - B = dropdown **Link Inputs > Parameter Collections > NPC_WK_Snow.SnowFall**
   - Repeat on B with another **Multiply Float**: B.A = SnowFall, B.B = **NPC_WK_Snow.WindSpeed** × (1/14 = 0.0714)
     via a third Multiply Float.
   - Result: full plumes in the blizzard, none at 2 m/s.
9. Compile, then **Save**. In WinterKeep run `py S --step drift --dry-run`, then `py S --step drift`. This places 24
   `WK_Spindrift_NN` on the ridge crests from `terrain/out/drift.json` (heights 173–377 m, ≥150 m apart, none over the
   castle).

## Tests

1. **Overcast** (`--step light --preset overcast`, Play): slow flakes, some grey against the sky, white against the
   forest. They don't move when you turn the camera. A light 3 m/s drift from the NW.
2. **Blizzard:** dense streaks rushing SE. Looking downwind they stream away from the view centre. Snow snakes run over
   the fields, tracks fill in about 45 s, white plumes come off the ridges, and sight lines are about 80–150 m.
3. **Night:** flakes dim with the scene. There's no glow.
4. **`stat unit`:** snowfall shells about 0.3 ms GPU at 1080p, spindrift about 0.2 ms (GPU sprites, culled at 700 m).
