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
