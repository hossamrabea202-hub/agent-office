# #410 Rain makes the world wet: research (UE 5.8)

Scope: stone castle walls, stone flag walkways, cobble/dirt ground and wood get wet in rain, with puddles and mud.
Driver: `MPC_Weather.Wet` 0 (dry) to 1 (soaked). Written 2026-11-01 by a research sub-agent; nothing tested yet.

## Already decided in the knowledge base (apply, don't re-decide)
- Wetness is the **last wear layer before the shared dirt pass** (README rule 3). Lagarde wood darkening ~0.82/0.58/0.38
  per channel, gloss gain x0.5, metals don't darken.
- Colour = `lerp(base, base^2, porosity x wet)` (Naughty Dog, INDUSTRY_SECRETS 1.3.2). Above 98 % water, normal = straight up.
- **Drying: the shine goes before the darkening** (fxguide / Lagarde).
- Measured: soil 0.15 dry, 0.08 wet; sand 0.40 dry, 0.23 wet (INDUSTRY_SECRETS 1.1 table).
- Puddles: lerp the normal toward flat by water height, so low areas fill first (4.2). Rain indoors: top-down depth capture.
- Cave #296: flat glossy puddles in low spots at roughness 0.06; flatten normal 0.95 for water; mud in cracks via inverted AO.
- Stables #400: muck = `lerp(base, lerp(base^2, muck, 0.5))`, roughness 0.35; up-facing floors wet only in patches.
- Owner rule 2026-10-30: never change decal materials or DBuffer settings without the owner's OK; new MIs, not live edits.

## Sources
1. Lagarde, Water drop 1, Observe rainy world: https://seblagarde.wordpress.com/2012/12/10/observe-rainy-world/
2. Lagarde, Water drop 2b, Dynamic rain and its effects (Remember Me): https://seblagarde.wordpress.com/2013/01/03/water-drop-2b-dynamic-rain-and-its-effects/
3. Lagarde, Water drop 3a, Physically based wet surfaces: https://seblagarde.wordpress.com/2013/03/19/water-drop-3a-physically-based-wet-surfaces/
4. Lagarde, Water drop 3b, Physically based wet surfaces (game formulas): https://seblagarde.wordpress.com/2013/04/14/water-drop-3b-physically-based-wet-surfaces/
5. DONTNOD PBR chart for UE4: https://seblagarde.wordpress.com/2014/04/14/dontnod-physically-based-rendering-chart-for-unreal-engine-4/
6. Naughty Dog tech art (Uncharted 4), SIGGRAPH 2016: https://advances.realtimerendering.com/other/2016/naughty_dog/NaughtyDog_TechArt_Final.pdf
7. fxguide on Lagarde / wet drying order: https://www.fxguide.com/?p=43362
8. Tatarchuk (ATI), Artist-directable real-time rain in city environments, SIGGRAPH 2006: https://advances.realtimerendering.com/s2006/Chapter3-Artist-Directable_Real-Time_Rain_Rendering_in_City_Environments.pdf
9. Cloward, Shading the World of Anthem, GDC 2019 (wetness + height puddles): https://www.gdcvault.com/play/1026274/Shading-the-World-of-Anthem
10. Unity Production Ready Weather sample (Wet, Puddles, RainRipples, Rain_Drips structure): https://docs.unity3d.com/Packages/com.unity.shadergraph@17.0/manual/Shader-Graph-Sample-Production-Ready-Weather.html
11. Public wet-surface shader after Lagarde (porosity from smoothness): https://gist.github.com/eviltak/e04b83ffdb91aa3d477bbfe0ca370da7
12. 80.lv, Nanite displacement puddles in UE 5.5: https://80.lv/articles/master-nanite-displacement-for-dynamic-water-puddles-in-unreal-engine-5-5/
13. Epic, Lumen performance guide (Max Roughness To Trace): https://dev.epicgames.com/documentation/unreal-engine/lumen-performance-guide-for-unreal-engine
14. `r.Lumen.Reflections.MaxRoughnessToTrace` cvar note: https://indxzero.github.io/ue544cvarwiki/articles/r.lumen.reflections.maxroughnesstotrace
Not found: no public Rockstar (RDR2), Guerrilla or Ubisoft (AC) talk on rain wetness. Their look is consistent with 1-6.

## Rules with numbers
**Physics (Lagarde 1, 3a):** wet porous surfaces get diffusely darker and specularly brighter. Water F0 = 0.02 (IOR 1.33).
Non-porous (metal, glazed, plastic) do not darken; they only carry a film. Water pools first in holes, cracks and curvature
lows; ripples only where water has accumulated. Walls parallel to the rain stay almost dry; complex shapes wet one-sided.
Small cracks dry before puddles, and a puddle can outlive dry ground around it.

**Albedo.** Lagarde 3b: `factor = lerp(1, 0.2, porosity)`, `Diffuse *= lerp(1, factor, Wet)` (worn asphalt 0.12 -> 0.08).
Lagarde 2b (simple): x0.3 at full wet. We use the KB's ND form `lerp(base, base^2, p x Wet)`; base^2 also raises
saturation. With **p = 0.55 on soil it reproduces the measured 0.15 -> 0.08**. Clamp the result to >= 30 sRGB (0.012 linear).

| Surface | porosity mask p | dry R (typ.) | wet R (no water) | in puddle / film |
|---|---|---|---|---|
| Limestone / whitewashed ashlar wall (open porosity 30-45 %) | 0.45-0.6 | 0.75-0.9 | 0.35-0.45 | n/a (vertical) |
| Worn stone flags (polished by feet) | 0.3-0.4 | 0.55-0.7 | 0.3-0.35 | 0.03-0.06 |
| Granite cobbles | 0.15-0.25 | 0.6-0.75 | 0.3-0.4 | 0.03-0.06 |
| Dirt / soil (clay 40-50 %) | 0.55-0.7 | 0.85-0.95 | 0.45-0.5 | mud band 0.2-0.4, water 0.04 |
| Weathered wood (planks, beams) | 0.5-0.7 | 0.65-0.8 | 0.33-0.4 | 0.1-0.15 |
| Iron, glass, glazed | 0 | as is | as is | film only, 0.1-0.15 |

**Roughness.** Lagarde 3b gloss rule = roughness x `lerp(1, factor, 0.5 Wet)` = x0.6 at p = 1. Lagarde 2b: gloss x2.5.
We use roughness x `lerp(1, 0.5, Wet)` for every porous surface, then lerp to 0.04 by accumulated water (table above).
**Specular:** keep UE 0.5 (F0 0.04); in standing water lerp to **0.25 (F0 0.02)**. Lagarde: barely visible, optional.

**Puddles (Lagarde 2b).** Water amount = `min(FloodLevel, 1 - Height)`; vertex-paint edge margin 0.4. Water uses F0 0.02 and
gloss 1. Normal: thin film keeps the surface normal, drenched = slightly smoothed, puddle = flat (vertex normal).
Our numbers: flatten 25 % for a film, 100 % where water > 0.98 (ND). Up-mask only from the **vertex** world normal.

**Ripples (Lagarde 2b).** 4 layers of a tiling ripple texture (R = ring distance, GB = direction, A = random time).
`Times = frac((Time x (1, 0.85, 0.93, 1.13) + (0, 0.2, 0.45, 0.7)) x 1.6)`; layer UV offsets (0.25,0) (-0.55,0.3)
(0.6,0.85) (0.5,-0.75); layer k on when `saturate((RainIntensity - k x 0.25) x 4)`; perturbation x0.35. Mips kill ripples:
fade them out by distance. Cost on PS3: 0.14 ms for a 256 px ripple texture.

**Streaks on walls.** Lagarde: running streams on walls are "the exception, not the standard". Keep them subtle: drip
lines under sills, merlons and string courses only. Smooth surfaces drip fast, porous ones slow (Unity sample).

**Mud on dirt:** base^2 darkening at p 0.6-0.7 (about x0.5 and more saturated), roughness 0.2-0.4 in the band around
puddles and in ruts, normal flattened 30-50 % (mud fills the fine grain), puddle water on top at 0.04.

**Timing (Lagarde 2b table, units per second as in the demo [UNVERIFIED]):** wet-level rise 0.6 / 0.75 / 1.0 for light /
moderate / heavy, fall 0.2; puddle flood rise 0.1 / 0.3 / 0.7, fall 0.05. So **drying is ~5x slower than wetting and
puddles ~4x slower than surfaces**. Lagarde 3b: a ~1 minute lerp is enough in a game. Ours: wet-up 30-60 s
(heavy), dry-down 3-5 min, puddles 10-15 min. Light rain caps Wet at 0.6 (no puddles).

## Recommended material-function design: `MF_RainWet` (new asset; plug into new master MIs / material layer)
Inputs: `BaseColor, Roughness, Normal(TS), Specular` (from the dry material); `Wet` (MPC_Weather.Wet); `Porosity`
(scalar per MI, or a texture channel); `Height` (heightmap 0-1, or `1 - AO`, or vertex paint); `PuddleAllowed`
(vertex paint or per-MI scalar, 0 on walls); `Shelter` (vertex paint, 1 = under a roof); optional `Puddle` (MPC_Weather.Puddle).
```
WetS    = Wet * (1 - Shelter)                                   // sheltered areas stay dry
Up      = saturate((VertexNormalWS.z - 0.8) / 0.15)              // pools only below ~37 deg slope
Side    = lerp(0.6, 1.0, saturate(VertexNormalWS.z))             // walls get 60 % wet
Dark    = sqrt(WetS * Side)                                      // darkening lingers while drying
Shine   = WetS * Side                                            // shine leaves first (rule: shine before dark)
Level   = Puddle (if set) else saturate((WetS - 0.55) / 0.45)    // no puddles below Wet 0.55
H       = Height * 0.7 + LargeWorldNoise(4-8 m) * 0.3            // breaks tiling, so puddles don't repeat per tile
Water   = Up * PuddleAllowed * saturate((Level - H) / 0.08)      // 0.08 = crisp puddle edge
Film    = Up * WetS * 0.25
Mud     = saturate(Water * 3) * (1 - Water) * MudAmount          // band around puddles (MudAmount 1 on dirt MIs)
BaseColor = max(lerp(Base, Base*Base, Porosity * Dark), 0.012)
           then lerp(.., Base*Base, Mud * 0.5)
Roughness = lerp(R * lerp(1, 0.5, Shine), 0.3, Mud) -> lerp(.., 0.04, Water)
Specular  = lerp(Spec, 0.25, Water)
Normal    = FlattenNormal(N, max(Film, Mud * 0.4, Water))         // fully flat at Water > 0.98
          + BlendAngleCorrected(ripples) * Water * RainIntensity * DistanceFade(15-20 m)
Optional: WallStreaks = world-aligned streak mask, |N.z| < 0.3, panning down 2-5 cm/s, roughness -> 0.15, only Wet > 0.3.
```
Outputs: BaseColor, Roughness, Normal, Specular (plus `Water` mask out for debug views). Metals: Porosity 0, so only the film acts.

## Pitfalls
- **Decals:** a decal that writes roughness/colour will show a dry patch on wet ground (forum report: decals don't inherit
  ground roughness). Fixing it means touching decal materials: **owner's OK first** (rule 2026-10-30).
- **Lumen reflection cut-off:** pixels above Max Roughness To Trace (PPV) use a rough fallback. Wet stone at 0.35-0.45
  sits on the usual threshold and pops. Raise it in the rain PPV (0.5-0.6) or keep wet roughness clear of it.
- **Pixel-normal up-mask** puts puddles on wall bumps and in brick cavities: use VertexNormalWS.
- **Over-darkening:** base^2 on already dark wood/soil drops below 30 sRGB; clamp. Squared form gives less per-channel
  spread than Lagarde's wood 0.82/0.58/0.38; check wood in lookdev.
- **One scalar has no hysteresis:** puddles that outlive dry ground need a second MPC value (`Puddle`), driven slower.
- **RVT / landscape:** apply wetness after the RVT sample, never bake it into the RVT (update cost, stale results).
- **Ripples:** mipmapped ripples vanish and alias; distance-fade them; no Composite Texture help on procedural normals.
- **Exposure:** an overcast rain sky shifts exposure; compare dry vs wet in lookdev at the same locked EV.
- **Indoors / under roofs:** without a Shelter mask (vertex paint or top-down depth RT) gate passages and halls get wet.

## [UNVERIFIED] (test in lookdev, then log the result)
- Porosity masks per surface in the table (derived from open-porosity % and the soil fit, not measured per asset).
- Roughness x0.5 at full wet and 0.04 for puddles on our textures; the 0.6 wall side factor; the 0.55 puddle start.
- Lagarde 2b timing table units (per second?); our 30-60 s / 3-5 min / 10-15 min timings.
- Lumen PPV Max Roughness To Trace default in 5.8 (often quoted as 0.4) and whether raising it costs too much.
- Substrate (if enabled in 5.8): same outputs should map to a Slab; a water-over-surface vertical layer may be nicer but costs more.
- Water F0 0.02 in puddles visible at all (Lagarde says barely).
- No film/streaming VFX breakdown on wet stone was found; the studio practice of "wetting down" sets before shooting is common
  knowledge, not sourced here.
