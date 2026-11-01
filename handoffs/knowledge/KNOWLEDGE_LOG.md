# Knowledge log: realism findings from every agent

Add new entries at the top. Format: **date · seat · topic**, then the finding, the source, and whether it was tested in our pipeline.

---

**2026-10-30 · Codex · wheel motion and continuous formation (offline verified; engine look unverified)**
The #50 draft added total accumulated wheel distance as a rotation every frame, which over-counts turns. The new controller instead accumulates signed incremental distance / measured radius independently for each wheel; stationary, reverse, turning and long-trip tests pass using laptop2's 55.4 cm radius. Crew needs one cart route with contact-following rather than two competing movement authorities. For #164, Blob/Puddle/neutral-zombie weights sum to one on corresponding topology, with a partial zombie basis present from the first instant and melt/rise overlapping. Geometry continuity and endpoint tests pass; this does not validate sculpted targets, material, skeleton, deformation normals or visual quality. Source and limits: `handoffs/castle-aftermath-gameplay-v1/README.md` and `INTEGRATION.md`. Rules applied: causal wear (3), motion/contact (8), coherence (10). No live decals/materials/settings changed; locked-grey-ball and one-piece decal tests remain required in engine.

**2026-10-30 · hossam gmail cloud (Claude) · round 2: industry secrets (researched, not yet tested)**
I ran about an hour of research in four tracks: materials, lighting and camera, characters and motion, and VFX and
environment. Everything is in [INDUSTRY_SECRETS.md](INDUSTRY_SECRETS.md), with sources. The owner made it an office rule.
Proposed gate changes for `pbr_check`:
- Warn when natural materials (wood, stone, soil) sit below 50–60 sRGB. Dyed blacks measure down to 35, so 30 stays the
  hard floor.
- Warn when mean HSV saturation is above about 60 %. Measured natural materials sit at 30–55 %; rust is about 70 %.

Highest-value items to try first:
- whitewash and false ashlar on the castle
- Composite Texture (normal → roughness) on every ORM
- torches at 1700–1900 K with a drift plus 8–10 Hz flicker and a Source Radius
- zombie play-rate and start-position variation
- sphere-mask wounds

**2026-10-29 · TGA (Claude) · passing pbr_check is not enough: judge under a locked grey ball (tested)**
The v2 siege kit passed `pbr_check` (bark median ~60 sRGB, above the 30 floor). Under a calibrated lookdev, with the
exposure locked so the 0.18 grey ball reads 118 sRGB, the bark rendered darker than the ball and looked like stained
timber. The flat grey-sky renders had hidden it. The fix: scale BaseColor ×2.1 in linear light with a soft shoulder,
giving a median ~89 sRGB, which is in the weathered-wood band. This is exact for albedo, needs no rebake, and leaves
the normal and ORM alone. Script: `assets/laptop2/SiegeBarricadeKit/source/albedo_lift.py`.
- Meter in the **Standard** view transform, which is linear, then render with AgX at that exposure. Metering through
  AgX converges very slowly because of its highlight shoulder.
- Calibrated lookdev mode: `LOOKDEV=1` in `preview135.py` (Nishita sky, sun 35°, grey and chrome balls, auto-meter).
- Still open: the bark plates repeat a regular leaf-shaped pattern, which shows in calibrated light. The fix needs
  more irregular plate cells in `build_kit.py`, not texture work.

**2026-10-29 · TGA (Claude) · the validator averages sRGB channels: deep reds need a neutral lift (tested)**
`pbr_check` measures the mean of the sRGB channels, not luminance. A deep red such as old blood (R high, G and B near 0)
fails even when its luminance is fine, and scaling it up keeps G and B at 0. What passed was a soft toe in sRGB on the
channel mean: an even add of up to ~36, applied only to tones below ~70. It keeps the hue and removes the impossible
near-zero G and B, which real dried blood and skin don't have. Used on the Flesh Brute skins (all 10 maps pass).

**2026-10-29 · hossam gmail laptop2 (Claude) · metal albedo (tested)**
Our shield iron was baked at about 71 sRGB with metallic 1, which renders as black plastic in UE. Bare iron is about 0.56 linear (Epic), so
180–200 sRGB. Old dark iron = bright metal under a dark oxide or mill-scale layer whose metallic drops. Fixed in
`shieldmat.iron`; the validator caught it. Source: Epic material docs, Adobe Substance PBR guide.

**2026-10-29 · hossam gmail laptop2 (Claude) · lookdev exposure (tested)**
A physical sky at the default exposure rendered the 0.18 grey ball far too bright, and every asset looked washed out. Always set
exposure so the grey ball reads mid-grey (about 118 sRGB) before judging. Source: Cave Academy grey-ball method, Epic EV100 docs.

**2026-10-29 · hossam gmail laptop2 (Claude) · baking bugs to check for (tested)**
Three silent bake killers we hit:
1. End caps sharing the side strip's UV island paint across it.
2. Superellipsoid or planar UVs whose front and back overlap (the back gem showed on the front).
3. Tube sweeps with inward-facing normals, which render black through the normal map.

Check the BaseColor sheet itself, not just renders.

**2026-10-30 · hossam gmail laptop2 (Claude) · geometry detail must stay under the mesh's Nyquist limit (tested)**
The siege gate planks baked with a regular grid / screen-door pattern across every board. Cause: the high-poly grain
displacement used noise at 70 cycles across a board that had only 40 segments across, so the mesh sampled the noise
below its Nyquist rate and turned it into a moiré grid, which the normal bake then recorded faithfully. Rule: any
displacement frequency on a procedural high poly must be under half the segment count in that direction (we now use
5 + 14 cycles across 40 segments); finer grain belongs in the material's bump, not the geometry. Same for rot edges:
a square-wave "jag" (`mod(round(x*9),2)`) reads as a sawtooth; use low-frequency fbm plus a few random Gaussian
splinters. Fixed in `build_gate.py` / `propkit.py`; gate v2 re-bake queued. Check close-up renders, not only wide ones.

**2026-10-30 · hossam gmail laptop2 (Claude) · bake hygiene: delete raw EXRs or the disk fills (tested)**
A 4K staged bake writes 24 quarter EXRs of 50 MB each (1.2 GB) plus a 300 MB bake blend and a 300 MB high blend
per asset. Three assets filled the laptop's last 6 GB overnight and the next bake failed silently. The bake runner
now deletes `*_raw_*.exr`, the OpenGL normal and the bake/high blends after `finish`. Keep ≥ 5 GB free and
check `df` in every queue script.

**2026-10-30 · hossam gmail laptop2 (Claude) · low and high must place parts by the same rule, not by index (tested)**
All seven flora bakes came out with black leaves, bells, spore sacs and fern pinnae while stems and petals were fine.
Cause: the parts were attached to the stem path by integer index (`path[int(t * (len(path) - 1))]`), and the high
poly path has 60 points where the low has 8, so the same leaf sat 4 cm higher on the high mesh and the bake rays from
the low (cage 4 mm) found nothing: black albedo, low roughness, garbage normals. Rule: anything derived from a
resolution-dependent array (path points, ring counts, segment counts) must be computed by parameter `t` with
interpolation, identically on both meshes. Check it by printing the bounding box of the same named part in the low and
the high blend before baking. Also: give stems/trunks 0.3–0.5× texel density, they are most of the surface and need
the least detail.

**2026-10-30 · hossam gmail laptop2 (Claude) · the Nyquist rule applies to procedural texture noise too (tested, 3 bakes)**
The siege gate planks kept a fine grid / screen-door pattern through three re-bakes (geometry grain halved, edge-wear
threshold raised: no change). The cause was the material: the fibre noise ran at ~3600 cycles/m along the board while
a 4K sheet over a 6 m gate has ~800 texels/m, so the bake sampled it below Nyquist and the beat became a grid. The same
material looked fine on a 0.7 m crate (2900 texels/m). Rule: every procedural frequency must stay under half the
texel density of the *largest* object that uses the material; when one material serves props and buildings, scale its
fine detail by the object's texel density, or keep micro detail (< 2 texels) out of the bake and let UE's detail
normal supply it. Check close-up renders of the biggest asset.

**2026-10-30 · hossam gmail laptop2 (Claude) · parts that intersect each other bake black (tested, 3 assets)**
Campfire logs crossing each other, a sack with folds deeper than the cage, and nested petal whorls all baked black
and glossy (albedo 0, roughness 0 = missed rays). Rule for selected-to-active bakes: no part of the high poly may sit
inside another part within the ray distance, and the low must follow the high within the cage. Stack crossing logs
one diameter apart, keep whorls > ray distance apart, and give slumped cloth a low mesh dense enough to follow it.
Diagnose with a "mat" render of the high poly: if the source material looks right, the black is the bake, not the
material.

**2026-10-30 · hossam gmail laptop2 (Claude) · bake cage size is per material relief, not per asset (tested)**
Bark logs baked black twice because the cage/ray distance had been shortened to 4/8 mm to stop neighbouring parts
leaking; bark plates stand 10–20 mm proud of the low mesh, so the rays never reached them. Rule: set the cage from the
deepest relief in the asset (bark 12/30 mm, planks 6/12, petals 4/8, lumpy sacs 20/45) and fix leaks by moving parts
apart, never by shortening the rays. Keep the per-asset table in `bake_shield.py`.

## 2026-10-30 — Grindstone wheel (laptop2)
- A wheel baked with the fieldstone material looked like smooth plastic: lichen/moss/bleach rules are for rocks, not a worked tool.
  Tools need their own material: sandstone grit (Voronoi 1500), a glazed darker rim band on the running surface (radius mask),
  radial scratches on the faces (noise stretched in angle), swarf ring at the axle, wet band where it dips in the trough.
- A 0.6 m disc needs 48 segments on the low or the rim polygons show in close-ups (28 was visible).

**2026-10-31 · adjustedfilm (Claude) · creature slime and "other realm" domes: what film studios do (#293, research)**
Stranger Things 3 (Rodeo FX) matched the Mind Flayer goop to filmed meat and slime: "a mix of wet and dry skin" for
breakup; flesh lives through subsurface, not emissive (ILM, S5). Annihilation's Shimmer (DNEG + DP Rob Hardy) is a
mostly clear "petrol slick" thin-film iridescence, colour only at grazing angles, structure from fractals. Rules for us:
dark organics 0.03-0.15 albedo, roughness patches wet 0.05-0.15 / tacky 0.35-0.5, no glow on biology, one danger cue
(a pulse), domes clear head-on with thin-film colour in the fresnel band. Details + sources: handoffs/blob-realism-293/RESEARCH.md

**2026-10-31 · adjustedfilm (Claude) · caves and medieval mines: what film, Netflix and game studios do (#296, research)**
The Descent lit its Pinewood cave sets only with what the characters carry (headlamps, flares, glow sticks), and red flares are
noisy and unsteady (ASC). Stranger Things built its Upside Down tunnels practically; VFX only extended the distance, and dust
or smoke sells the air. Indiana Jones and the Great Circle: geometry and materials rebuilt together, Slocombe-style high-contrast
candle light. Rainforest Cavern (80.lv): low-contrast base colour, wetness and rain streaks via vertex-colour lerps, mud in
cracks via inverted AO, flatten normal 0.95 for water, sharp rocks beat rounded scans. Real caves: calcite is white; yellow
or brown is impurity or organic stain; orange is iron; black is manganese, guano or soot. Medieval mines were fire-set,
which leaves rounded, smooth, spalled walls with lamp soot, not sharp pick facets. Not tested yet. Rules, spec and sources:
handoffs/cave-296-297/RESEARCH.md

**2026-10-31 · adjustedfilm (Claude) · procedural rock on flat boxes hits a ceiling (#296, tested in a Cycles OSL lookdev)**
Four iterations of a fully procedural 3D rock (fbm, ridged noise, limestone ledges, Voronoi blocks, cm grain) on box walls.
Value-noise isolines read as smooth "worm" cracks. Closed Voronoi cells read as crazy paving. Breaking the cracks with noise
helps, but the result stays stylised. What works procedurally: wetness bands, drip streaks, flat glossy puddles in low spots
(roughness 0.06), per-bed tone shifts. Rule: use scanned rock (Megascans on the Master PC, or CC0) as the base, add the
procedural wet/stain layers on top, and put real geometry near the camera. Renders: assets/adjustedfilm/CaveRock296/renders.

**2026-10-31 · adjustedfilm (Claude) · realistic blood and "not too gory" dismemberment (#337, research)**
Blood looks fake when it is bright red, unlit, uniform round blobs, too much, unblurred and dry-looking. Measured optics
(physicallybased.info): IOR 1.35 (UE Specular ~0.28, not 0.5), viscosity ~4 mPa·s, surface tension 56 mN/m; bright red
(sRGB ~210,10,16) is only the thin-film transmission colour, thick blood is dark maroon with a sharp highlight. Stains go
red to brown as haemoglobin oxidises; zombie blood (no oxygen, no pump) is darker/browner and oozes, which is both more
real and less gory. Slash spatter is 1-4 mm (forensics), render 0.25-1.2 cm. Ghost of Tsushima uses lit "deferred"
billboards + ribbons, no meshes, blood from wound and blade. Dying Light 2 severs by hiding the part with a shader, a
cap mesh, and a spawned limb mesh; it backed off excess. Not tested yet. Spec (counts, colours, chances), sources:
handoffs/gore-337/RESEARCH.md

- 2026-10-31 adjustedfilm (#366): long skinned meshes (tentacles) with stretched UVs: don't use world triplanar (it
  swims on animation). Map on **Pre-Skinned Local Position** (pass it through a Vertex Interpolator to the pixel shader),
  as a cylindrical UV: along = distance along the long axis x actor scale, around = angle x a whole number of tiles.
  Fix the atan2 mip seam by taking the smaller derivative of the two wrapped UVs (Ben Golus, 2021). Keep the samples that
  feed WPO on their old UVs (ddx is not allowed in the vertex shader). Script: handoffs/tentacle-skin-366.

**2026-11-01 · adjustedfilm (Claude) · winter: snow, drifts, ice, rime, tracks (#390, research + Blender lookdev)**
Snow albedo is ~0.80 typical, >0.90 only for fresh snow in whiteout (Journal of Glaciology), so use 0.80-0.86 fresh,
0.66-0.72 wind-packed, 0.36-0.45 trampled, never 1.0. Clear lake ice reads BLACK (you see deep water through it); only
bubbles and cracks read white. Rime grows INTO the wind (windward), drifts pile on the LEE side: pair them per object, it
is the realism tell. Place snow by the Winstral Sx shelter index (max upwind horizon angle). Tracks: TLOU2 uses parallax,
GoW Ragnarok rebuilt snow displacement for scale; our pick is a player-centred render-target mask + POM in the landscape
material (no WPO, no VHM: no collision, RVT writes lag). Tested in Blender: a world volume in Cycles blocks the infinitely
far sky and renders black; put fog in a bounded box. Notes, sources: handoffs/winter-map/RESEARCH.md

## 2026-11-01 — WinterKeep polish v2: snow-loaded trees, ice, terrain (adjustedfilm, tested in Blender lookdev)
- **Norway spruce reads real only with hanging branchlets.** Flat or V-shaped fronds alone read as stacked plates. The
  "comb" habit (narrow needle strips hanging under each branch) plus snow cushions on top of each branch (15-37 cm,
  lumpy, only on top) made it read as a snow-loaded spruce at once. Tested: lineup render `winter-map/lookdev/shots/assets_trees.png`.
- **Single-octave value noise thresholded = star shapes.** A speckle mask from 1 octave of value noise makes repeating
  X/star blobs on rock. Use 3+ octaves before thresholding. Tested.
- **Dense fog in Cycles goes dark with volume bounces 0** (the default). A white-out needs multiple scattering:
  `cycles.volume_bounces` 3-4. Snow fog is bright because light scatters many times, not because the fog is white.
- **Check a "gorge" is terrain, not a road fill.** Our gorge under the bridge was a 30 m road embankment with 1 px
  spikes. Never fill a river crossing to deck height in the heightmap; let the bridge mesh span it.
- **Real big single arches exist:** Pont du Diable at Céret (1341) spans about 45 m and stands 22 m high, so one 46 m
  segmental arch over a 30 m gorge is authentic, not fantasy. [source: Wikipedia, Pont du Diable (Céret)]
- **Frozen falls:** mostly bubbly white-blue ice (albedo ~0.5) with a few clear dark streaks; an irregular outline and a
  spray cone at the foot. A full-width square curtain reads as a slab.

### 2026-11-01 · adjustedfilm (Claude) · #390 blizzard white-out, snowfall, snow trails (tested in lookdev / numpy)
- **Blizzard fog in a path tracer: don't scatter it, fake the converged field.** A uniform scattering fog of 0.026/m over
  a 500 m deep box rendered a pure BLACK frame in Cycles (optical depth ~13 blocks the sun and sky; 4 volume bounces can't
  recover it). Classic fog model instead: absorption σ + emission σ·L_fog (= L_fog·(1−T) + L_scene·T), visible to camera
  rays only. This is what a deep albedo≈1 snow cloud converges to (uniform radiance). Result: bright white-out. Tested.
- **Sight line from extinction:** 5 % contrast distance (Koschmieder) = 3/σ. 80–150 m means σ = 0.020–0.037/m. At 0.026
  a bridge 142 m away vanished, so the lookdev uses 0.020. UE ExponentialHeightFog: density 0.22 at the fog actor's height
  is about 0.022/m, with falloff 0.03 (near-uniform) and white volumetric albedo.
- **Falling snow without Niagara:** a world-space jittered 3D flake field shown through camera-centred slabs (1–2, 2–4,
  4–8, 8–16 m). Rules:
  - cell = R/6, 6 samples per slab;
  - flake radius max(0.8 cm, R·0.0025) so every flake covers ≥1 px;
  - streak over a 1/60 s shutter, opacity scaled by 2r/(2r+streak) so energy is kept;
  - lit translucent, not emissive.
  The first try (cell R/4, radius 0.45 cm) gave 0.1–0.3 % screen coverage, which is invisible. The fix gave 1.2 %
  (overcast) and 3.4 % (blizzard). Looking downwind, the streaks fan out from the view centre, which is correct.
- **Trail render target:** snap the rolling window to whole texels (25 cm = 8 texels at 3.1 cm). The shift copy then
  stays exact, with no bilinear blur accumulating. Store HEIGHT (1 = untouched) so POM and the refill clamp work without
  inverting.

### 2026-11-01 · TGA (Claude) · #397 weapon kit AAA: forged steel, iron, ash, leather, brass (research; lookdev results follow)
- **A blade is three finishes on one steel:**
  - **satin ground flats**, with faint grind streaks *along* the blade (roughness 0.16–0.30);
  - a **brighter stoned edge bevel** (a secondary bevel about 3–4 mm wide, roughness 0.10–0.16);
  - **satin fullers** that collect grime.
  A dead mirror reads as a modern replica. Medieval finishing went from a coarse grind to fine stones, and fullers were cleaned to a satin. [sources: EXARC polishing-bench reconstruction; myArmoury maker thread]
- **Forged heads (axes, halberds, maces) keep forge scale next to a ground, polished edge:**
  - scale = dark blue-black **non-metal** oxide, about 50–62 sRGB, roughness 0.55–0.75, flaked in patches with pitting;
  - the edge strip = bright metal;
  - a wavy boundary between them.
  [makers: BeaverCraft, Hoffman Blacksmithing; Outdoors SE on forge scale]
- **Iron F0 (≈ steel) = 0.562, 0.565, 0.578 linear (198 sRGB)** is the base for ground steel; forged fittings 0.50–0.54 linear. [AMU CG course table; KB iron 0.53–0.58]
- **Polearm hafts were ash, oiled with linseed,** which darkens and yellows over time, so it is mid amber-brown (≈128, 96, 64 sRGB), not pale. Hand zones are darker and smoother, and the butt is dirtier. [myArmoury citing Waldman; Roman Army Talk; conservation list] **[inference: no measured albedo for aged oiled ash]**
- **Grip leather:** never uniform wear; keep its value clearly apart from the wood. [Polycount]
- **Not found:** no public AAA (Warhorse / KCD) weapon-texturing breakdown. Full notes: `handoffs/weapon-kit-aaa/RESEARCH.md`.
