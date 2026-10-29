# Calibrate first, then let physics place the dirt

Top studios mostly don't get photorealism from clever shaders. They get it from discipline. **Every value is calibrated against measured ranges** (dielectric albedo about 30–240 sRGB, F0 fixed at 4%, metallic strictly 0 or 1). **Every layer of wear, dirt, water and growth is placed by a physical cause** (curvature, cavity, gravity, world-up, sunlight, porosity). **Placement follows rules rather than uniform scatter.** And **every asset is judged in one fixed, neutral, exposure-locked lookdev scene** before it reaches a level. For a small team that generates meshes with numpy in Blender, bakes procedural shaders to BaseColor/ORM/Normal, and ships a Blueprint-only UE 5.3 game with Lumen, five things matter most, roughly in this order. First, automated PBR range gates in the bake script. Second, a locked-exposure lookdev map. Third, form-driven layering with a "transition" layer at every blend seam, as Naughty Dog does. Fourth, bevels sized from texel density. Fifth, grounding every prop into the terrain. Lumen adds hard construction rules that a castle can break: walls at least 10 cm thick, closed meshes, real lights behind small emissives. Night scenes need exposure clamped, or auto-exposure will turn them into grey dusk. The evidence is uneven. Epic, Adobe, Marmoset and Sébastien Lagarde give hard numbers. Naughty Dog, Sucker Punch, Guerrilla and Blur give methods without numbers. **Rockstar's RDR2 material and vegetation pipeline, and the internal lookdev rigs at Weta, ILM, Unit Image and Digic, have no openable primary sources**, so anything said about them below is either a third-party frame analysis or an inference. In this report "sourced" means a claim is cited inline. Anything labelled *inference* is synthesis or common craft practice, not a published studio figure.

## Studios share methods, not numbers

What can be documented about each studio is a set of techniques. Almost none of them publish thresholds.

**Naughty Dog** has the most transferable material detail. In The Last of Us Part II, an "Uber Shader" covered almost every surface and included custom wetness, deformable snow and heightmaps ([Kotaku on SIGGRAPH 2020](https://kotaku.com/so-much-work-went-into-the-last-of-us-part-iis-eyes-1845162613)). Artists vertex-paint two shaders onto one mesh and hide the seam with **a third "transition blend" material** such as cement, then add details on top ([80.lv](https://80.lv/articles/breakdown-shader-painting-in-the-last-of-us-2/)). For the Part I remake, Matthew Trevelyan Johns built a shared baked-bevel trim layout to free texture memory and cut down on uniquely baked props. It relies on hard 90-degree geometry with fewer modeled bevels ([80.lv](https://80.lv/articles/the-last-of-us-remake-s-trim-pipeline-in-substance-3d-explained); [ArtStation](https://trevelyan.artstation.com/projects/qQGK6y)). Weapon chips and dents are sculpted "where real wear would occur" ([80.lv](https://80.lv/articles/how-naughty-dog-created-the-immersive-world-of-the-last-of-us-part-ii/)). Environment artists must justify overgrowth by asking "Is there enough sunlight here?" and "How did this happen?". Grass density was iterated "dozens of times" against performance and stealth visibility ([80.lv](https://80.lv/articles/how-naughty-dog-created-the-immersive-world-of-the-last-of-us-part-ii)). The full tech-art deck is public but was not opened. It is a 152 MB .pptx ([Naughty Dog](https://www.naughtydog.com/blog/naughty_dog_at_siggraph_2020)).

**Sucker Punch's** public material on Ghost of Tsushima is about shading, atmosphere and tonemapping research ([Patry 2020](https://blog.selfshadow.com/publications/s2020-shading-course/patry/s2020_pbs_patry_slides.pdf); [Advances 2021](https://www.advances.realtimerendering.com/s2021/jpatry_advances2021.pdf)), plus procedural grass and wind. A secondary summary of the GDC 2021 grass talk reports several details. Cards were dropped because of overdraw. Each world tile carries height, material and grass-type textures. Blades are bezier curves with 15-vertex and 7-vertex LODs that morph to hide popping. Short blades are folded to double apparent density. **Far foliage is replaced by an artist-authored ground texture** ([GDC Vault](https://gdcvault.com/play/1027214/Advanced-Graphics-Summit-Procedural-Grass); [Stylized Station thread](https://threadreaderapp.com/thread/1688939411575119872)).

**Guerrilla** textured Horizon Forbidden West's machines with a procedural workflow that "saved months of production time" ([GDC Vault](https://gdcvault.com/play/1029327/Taking-a-Procedural-Approach-to)). In Zero Dawn, artists authored placement *rules* in a graph editor rather than placing individual objects, and the GPU used those rules to build a dense world around the player ([Guerrilla](https://www.guerrilla-games.com/read/gpu-based-procedural-placement-in-horizon-zero-dawn)).

**Rockstar** has no primary talk on RDR2 materials or vegetation that could be found. The one technical detail comes from an outside frame-capture study. It describes footprints and wheel ruts accumulating into a **2048×2048 R16 displacement map** that drives parallax occlusion mapping on the terrain ([imgeself](https://imgeself.github.io/posts/2020-06-19-graphics-study-rdr2)). Treat any other "RDR2 does X" claim as unsourced.

**Epic/Quixel** shows the scan-heavy end of the range. Valley of the Ancient is reportedly about 90% Megascans ([Epic](https://dev.epicgames.com/documentation/unreal-engine/valley-of-the-ancient-sample-game-for-unreal-engine)). Electric Dreams builds cliffs from pre-composed "assemblies" placed by PCG along splines, across 4×4 km World Partition levels ([Epic](https://dev.epicgames.com/documentation/en-us/unreal-engine/electric-dreams-environment-in-unreal-engine)). Practitioners describe how scans are captured. Cross-polarised photos strip specular from albedo, and specular is recovered by subtracting the cross-polarised shot from a parallel-polarised one in linear space ([Polycount](https://polycount.com/discussion/comment/2141652)). No official Quixel calibration document was found.

**Film houses** add a lookdev discipline more than any single technique. For *Shape-Shifters* in Love, Death + Robots, Blur pushed detail "across the whole frame". The Military Bunker scene used **over 150 V-Ray proxies** for fences, trees and pebbles. Atmosphere came from volume grids "with accurate shadowing, lighting and camera blur". The look was locked on one or two shots and then reused ([Chaos](https://blog.chaos.com/the-render-tricks-behind-netflixs-nsfw-love-death-robots)). On *Bad Travelling*, Blur began lookdev with lighting, before building assets ([AWN](https://www.awn.com/print/news/how-blur-used-light-create-darkness-david-finchers-bad-travelling)). *The Secret War* was made by Digic, with Platige credited only for concept design ([Behance](https://www.behance.net/gallery/115769975/Love-Death-Robots-The-secret-war); [VG+](https://virtualgorillaplus.com/anime/love-death-and-robots-inside-the-animation/)). Tim Miller said stories like *Aquila Rift* "had to be photoreal to be successful and horrifying" ([Art of VFX](https://www.artofvfx.com/?p=25209)). The Unit Image credit for *Aquila Rift*, and any Weta or ILM lookdev specifics, could not be confirmed from primary sources. The general film method is documented by trainers rather than by the studios. A colour chart sets white balance and an 18% grey ball sets exposure, which gets you "about 90%" of the way. The remainder comes from how real lenses form an image ([Cave Academy](https://caveacademy.com/wiki/post-production-assets/surfacing/surfacing-training/creating-a-neutral-look-development-environment/)).

*Inference:* the common thread is not scanning. It is that every studio removes arbitrary choices. Values come from measurement, placement comes from rules or cause, and judgement happens in one calibrated scene. A procedural pipeline can copy all three without ever touching a scan.

## PBR gates and physics-ordered layers do most of the realism work

### Calibration numbers to hard-code

The best-sourced numbers in this whole field are PBR ranges, and they map directly onto UE 5.3's default lit model.

**Dielectric albedo.** Adobe sets the floor at **30 sRGB (tolerant) or 50 sRGB (strict)** and the ceiling at **240 sRGB** ([Adobe PBR Guide pt 2](https://www.adobe.com/learn/substance-3d-designer/web/the-pbr-guide-part-2)). That is roughly 0.012–0.875 linear ([Polycount calc](https://polycount.com/discussion/comment/2636450)). Epic's measured intensities show how dull real materials are: charcoal 0.02, worn asphalt 0.08, bare soil 0.13, green grass 0.21, desert sand 0.36, fresh concrete 0.51, fresh snow 0.81 ([Epic](https://dev.epicgames.com/documentation/en-us/unreal-engine/physically-based-materials-in-unreal-engine)). Lagarde gives a slightly different band, charcoal at about 0.04 and snow at about 0.9 ([Lagarde](https://seblagarde.wordpress.com/2013/04/14/water-drop-3b-physically-based-wet-surfaces/)). Use either band as a sanity range, not as an exact target.

**Specular.** UE Specular **0.5 equals 4% reflectance**, and that is the right value for nearly every dielectric. Exceptions are water (0.255), ice (0.224) and skin (0.35).

**Metallic.** Metallic is **strictly 0 or 1**. Grey values are allowed only for corroded hybrids, and metal/paint masks must be pure black and white ([Epic](https://dev.epicgames.com/documentation/en-us/unreal-engine/physically-based-materials-in-unreal-engine)). Raw metal base colour sits at **180–255 sRGB** (70–100% reflectance). Rust, dirt and paint on metal are dielectrics ([Adobe](https://www.adobe.com/learn/substance-3d-designer/web/the-pbr-guide-part-2)). Epic lists iron at linear 0.56/0.57/0.58 and copper at 0.955/0.637/0.538.

**Cavity.** Multiply cavity into Base Color, and use **cavity × 0.5 as Specular** to kill reflections in crevices ([Epic](https://dev.epicgames.com/documentation/en-us/unreal-engine/physically-based-materials-in-unreal-engine)).

**AO and lighting.** Neither belongs in albedo. Only micro-occlusion is allowed there ([Adobe](https://www.adobe.com/learn/substance-3d-designer/web/the-pbr-guide-part-2)).

**Roughness** has no sourced value table. Adobe explicitly treats it as an artistic choice, and no primary per-material albedo values were found for wood, leather, cloth, rust or paint.

*Inference for the Blender pipeline:*

- Keep Principled BSDF "Specular IOR Level" at 0.5 so it matches UE's 0.5.
- Fail a bake if more than about 2% of dielectric texels fall outside linear 0.012–0.87.
- Fail it if metallic has non-binary values on more than about 5% of texels, or if any metal BaseColor falls below 0.45 linear.
- Fail it if the roughness map's standard deviation is near zero. Uniform roughness is the single most common "plastic" tell.

### Wetness is the one layer with published maths

Lagarde's wet-surface model is the strongest numeric anchor for any weathering layer.

**Darkening:** `Diffuse *= lerp(1, lerp(1, 0.2, Porosity), WetLevel)`. Literature puts the darkening range at 0.1–0.3. Wet worn asphalt drops from 0.12 to about 0.08. Wet wood also shifts per channel, with measured factors of about (0.82, 0.58, 0.38), so it gets **darker and redder, not just darker**.

**Gloss boost:** `Gloss = lerp(1, Gloss, lerp(1, factor, 0.5*WetLevel))`.

**Metals and porosity:** metals are exempt from darkening. If no porosity map exists, derive porosity from gloss with `saturate(((1-Gloss)-0.5)/0.4)`.

**Puddles:** flatten the normal map toward the vertex normal ([Lagarde](https://seblagarde.wordpress.com/2013/04/14/water-drop-3b-physically-based-wet-surfaces/)).

**Layer order:** DONTNOD's weathering system applied dust where world normals face up, and shadowed rain masks only by static geometry. It ordered effects as object shader, then effect lights, then post-process, then decals. **Decals come last so they can remove effects**, for example dry patches under eaves ([Lagarde](https://seblagarde.wordpress.com/2014/05/03/weathering-and-aging-effects/)). Naughty Dog gave each wet and mud effect "its own grunge mask" ([80.lv](https://80.lv/articles/how-naughty-dog-created-the-immersive-world-of-the-last-of-us-part-ii)).

*Inference, recommended bake order:* each step below has a physical cause.

| Order | Layer | Driven by | Key rule |
|---|---|---|---|
| 1 | Base material | Calibrated albedo, F0 0.04 | Roughness gets its own low-frequency drift |
| 2 | Edge wear | Curvature/pointiness, broken up by noise | Exposes the substrate: bare metal (metallic 1, smoother) under paint, polished wood |
| 3 | Cavity dirt | Baked AO/cavity | Darker, rougher dielectric; specular × cavity |
| 4 | Gravity streaks | World −Z, seeded under edges and cavities | Rust runs set metallic to 0 |
| 5 | Dust/moss/snow | `dot(N,+Z)` × noise × AO | Moss favours cavities and up-facing surfaces |
| 6 | Wetness | Lagarde porosity model | Applied last, over everything; metals exempt |
| 7 | Transition band | `abs(mask−0.5)` remapped around any blend | Grime/cement/rust at seams, the Naughty Dog pattern |

Two caveats. The layer strengths are not sourced; no studio published coverage percentages for edge wear or grime. But Lagarde's ×0.2 darkening ceiling and 0.5-damped gloss shift are a useful sense of scale: real weathering is **subtle**.

### Macro, meso and micro: separate the frequencies, then break the repetition

Epic's landscape tools blend from detail textures to macro textures by view distance. The Kite demo blends layers with HeightLerp alphas and uses a distance texture to reduce grass tiling ([Epic UDN](https://udn.epicgames.com/Three/LandscapeMaterials.html); [UE forum](https://forums.unrealengine.com/t/landscape-kitedemo-material-question/36944)). Community breakdowns add high-contrast macro-variation masks and a distance fade to average colour. They also warn that macro tinting can shift hue, for example pushing grass toward a darker green ([UE forum](https://forums.unrealengine.com/t/how-i-made-a-landscape-material/43518)).

*Inference:* for unique-UV baked props, separating detail frequencies matters more than hiding tiles. Bake three bands:

- **Macro** (about 1–5 m): tonal drift, sun fade, gravity fade.
- **Meso** (about 1–20 cm): planks, chips and dents, mostly in the normal map.
- **Micro** (under 1 cm): grain and pores. Baked texel density can't hold this band, so add it in UE as a tiling detail normal blended with BlendAngleCorrectedNormals and faded by distance.

On top of that, drive a world-position macro variation so repeated props differ, and use vertex colour R/G/B for per-instance wetness, moss and dirt instead of rebaking. Keep procedural saturation low and vary value and roughness more than hue, because the measured natural albedos are muted.

### Scan versus procedural

DICE called photogrammetry "a tool, not a magic bullet" serving the art direction ([Game Developer](https://www.gamedeveloper.com/art/gdc-see-how-dice-used-photogrammetry-to-bring-i-star-wars-battlefront-i-to-life)). A secondary summary reports about **50% faster asset creation at first, with about 70% expected later** ([Medium](https://medium.com/@homicidalnacho/a-look-into-photogrammetry-and-video-games-71d602f51c31)). Scan processing means delighting and making textures tileable ([Game Developer](https://gamedeveloper.com/art/the-workflows-of-creating-game-ready-textures-and-assets-using-photogrammetry)). Guerrilla shows the procedural route can reach AAA quality.

*Inference:* a procedural team gets most of a scan's credibility from three things scans have by default. **Measured albedo ranges**, **form-correlated variation** (wear that follows geometry), and **3+ noise octaves tied to real-world scale**. Use Megascans surfaces as calibration references beside your own assets in the lookdev map, even if you never ship them. Note that Megascans colours often clash with custom ground until they are tuned ([CGWorld](https://cgworld.jp/regular/202206-pt-044.html)).

## Geometry, bevels and bakes fail at the texel, not the polygon

Marmoset's baking documentation states the core constraint. Normal maps record direction, not depth. **Anything smaller than a pixel is lost**, and parallel faces record nothing, so edges need bevels or slopes of consistent minimum size. Curved surfaces need enough sides to fix silhouette waviness ([Marmoset](https://marmoset.co/posts/toolbag-baking-tutorial/)). Real edges are "chamfered or rounded over" ([80.lv](https://80.lv/articles/learn-how-marmoset-toolbag-5-s-bevel-shader-can-boost-your-workflow)). Practitioners set bevel width per material ([80.lv](https://80.lv/articles/prop-art-tips-creating-a-realistic-radio-receiver-in-blender-marmoset-toolbag)) and check edges at gameplay distance, because very tight bevels vanish there.

**Texel density** has no published AAA studio standard. The common reference values are vendor and practitioner examples: **10.24 px/cm (1024 px/m) for first person, 5.12 px/cm for third person, 2.56 px/cm for top-down** ([Maxon](https://help.maxon.net/c4d/en-us/Content/html/Texel_Density.html)). A Playground Games artist notes that first-person weapons, cinematic, inspectable and landmark assets go above baseline, and that trim UV islands are usually scaled no more than **about ±25%** ([Beyond Extent](https://www.beyondextent.com/deep-dives/deepdive-texeldensity)). Low density also causes visible white fringes at metal/dielectric borders ([Adobe](https://www.adobe.com/learn/substance-3d-designer/web/the-pbr-guide-part-2)).

*Inference:* compute bevel radius from density. At 1024 px/m, one texel is about 1 mm, so bevels need **at least 2–3 mm**. At 512 px/m they need **at least 4–6 mm**. Derive texture size from surface area × density², rounded to a power of two, not the other way round.

**Bake rules from Marmoset:**

- Triangulate before export, or quads and n-gons cause X-shaped smoothing errors.
- Split UVs at every hard edge.
- Use a smoothed (averaged) cage just large enough to enclose the high poly.
- Bake in the renderer's tangent space (MikkTSpace for Unreal).
- Bake 16-bit, then dither down to 8-bit to avoid banding.
- AO: 256 rays is medium, **512+ is final quality**.
- Separate parts with `_high`/`_low` groups so they don't bake onto each other ([Marmoset](https://marmoset.co/posts/toolbag-baking-tutorial/)).

On the UE side, set the import to **Import Normals rather than Compute Normals** so MikkTSpace tangents match the bake. That advice comes from UE4-era forums; check the label names in 5.3 ([Polycount](https://polycount.com/discussion/comment/2419487)). *Inference:* Blender outputs OpenGL Y+ normal maps, so flip green for UE's DirectX Y− convention. Common padding is about 8–16 px at 2K and 16–32 px at 4K (not sourced).

**Nanite changes the trade-off.** Epic lists "use high-poly detailing rather than baking detail into normal map textures" as a benefit. Up close, Nanite draws the source triangles. It has no per-vertex tangents, supports only opaque and masked materials, and uses a fallback mesh for ray tracing. You should also disable Generate Lightmap UVs on dense meshes ([Epic Nanite](https://dev.epicgames.com/documentation/en-us/unreal-engine/nanite-virtualized-geometry-in-unreal-engine)). Note that the fetched page is the current docs version, not 5.3-specific.

*Inference:* with numpy-generated meshes, generate primary and secondary forms and 2 mm+ bevels as real geometry under Nanite. Keep normal maps for sub-millimetre detail. Still bake AO and curvature, because they drive the wear masks. Add low-frequency vertex displacement (sag, warp, asymmetry) before baking so no silhouette is ruler-straight; no primary source covers this, but it is standard practice. Keep a non-Nanite low-poly plus baked-normal path for anything translucent or skinned. For repeated castle architecture, Naughty Dog's hard-edged geometry with baked-bevel trims is the memory-cheap option. A mesh generator can emit trim-aligned UVs automatically because it knows where its bevels are.

## Ground, vegetation and corruption need rules and contact, not scatter

**No studio here hand-places grass.** Ghost of Tsushima uses per-tile maps. Guerrilla dithers 2D density maps into points. Electric Dreams uses PCG graphs and assemblies. Hand-authoring is saved for hero flora (GoT's spider lilies and pampas are modeled meshes) and story spaces ([Guerrilla](https://www.guerrilla-games.com/read/gpu-based-procedural-placement-in-horizon-zero-dawn); [Stylized Station](https://threadreaderapp.com/thread/1688939411575119872); [Epic](https://dev.epicgames.com/documentation/en-us/unreal-engine/electric-dreams-environment-in-unreal-engine)).

**Realism comes from structured non-randomness.** Sucker Punch rejected random heights because "real grass isn't simply random heights". Noise groups blades into **clumps that share height, colour and direction**. Wind combines a scrolling Perlin gust field with sine bobbing and per-blade offsets so neighbouring blades never move in sync ([Stylized Station](https://threadreaderapp.com/thread/1688939411575119872)).

**UE's Landscape Grass Type controls.** Density is measured in **instances per 10 m²**. Start and End Cull distances fade instances out, and the fade requires the PerInstanceFadeAmount node ([UE API](https://docs.unrealengine.com/5.1/en-US/PythonAPI/class/GrassVariety.html)). Cull distances do not thin density gradually, so the workaround is several copies of the same variety at different densities, each with its own cull range ([UE forum](https://forums.unrealengine.com/t/reduce-grass-density-by-distance/50086)).

*Inference for Blueprint-only UE 5.3:*

- Use landscape paint layers feeding Landscape Grass Types, or a PCG graph with Density Filter and Self Pruning.
- Run 2–3 varieties per layer: dense near (cull about 30–60 m), sparser mid (cull about 80–150 m).
- Tint the landscape under the grass to the grass's average colour so the cull line disappears. This is GoT's far-field trick.
- Do clumping in the foliage material: lerp 2–3 tints with world-space noise at 3–10 m scale plus PerInstanceRandom.
- Place flowers in sparse clusters where light allows, never evenly.

**Terrain and blending props into it.** Runtime Virtual Texturing (RVT) is the documented route. RVT caches landscape shading. Meshes set to **Draw in Main Pass = Never** render only into the RVT, which makes them ideal for paths, mud and stains. Normals should be stored in world space. **Virtual Texture Min Coverage 3** culls primitives under about 8 px. RVT does not support LOD or culling for instanced static meshes ([Epic RVT](https://dev.epicgames.com/documentation/en-us/unreal-engine/runtime-virtual-texturing-in-unreal-engine)). Prop materials sample the RVT and blend toward the landscape with a height gradient above the RVT's world height ([Dowell](https://andrewdowell.blogspot.com/2025/02/how-to-blend-assets-with-your-landscape.html)). Dithered Pixel Depth Offset softens intersections but "only works correctly with TAA" ([Elliot Gray](https://elliot-gray-m2f9.squarespace.com/blog/ue4-terrain-blending)). It can cancel out between two meshes that share the same dither ([UE forum](https://forums.unrealengine.com/t/is-there-a-way-to-have-pixel-depth-offset-blend-multiple-non-landscape-meshes-together-using-the-same-material/468004)). World-aligned moss masked by the up vector, using the same projection in rock and landscape materials, hides the seam ([Thiessen](https://haukethiessen.artstation.com/projects/Z2wV8); [Polycount](https://polycount.com/discussion/comment/2415205)).

*Inference, cheapest grounding first:*

1. Sink props 10–30% into the ground and align them to the slope.
2. Add a debris skirt of pebbles, a few small rocks and a grass clump.
3. Blend to the RVT over the bottom 20–50 cm.
4. Add world-aligned top moss and dust.
5. Add dithered PDO (TSR presumably qualifies as temporal AA).
6. Add a dark contact decal.

For the landscape material: 4–6 height-blended layers, two world-space macro noises (about 20–50 m and about 200 m) on brightness and saturation, distance-based rescaling, and output into an RVT. For puddles, fill low cavities first, push roughness toward about 0.05–0.1, and flatten the normal. Set dressing should use 3–5 Packed Level Actor "assemblies" per biome, odd-numbered clusters, a skewed scale distribution (many small pieces, few large) and deliberate negative space.

**The tentacle realm** has almost no primary source support. Horizon's red blight and Returnal's reactive alien flora are documented only at a high level ([Dark Horse](https://www.darkhorse.com/newsfeed/return-horizon-art-horizon-forbidden-west-dark-hor); [GIGA](https://www.giga.de/test/returnal-im-test-und-taeglich-gruesst-das-alien/)). The transferable sourced principle is Naughty Dog's: invasive growth needs a cause and a growth logic ([80.lv](https://80.lv/articles/how-naughty-dog-created-the-immersive-world-of-the-last-of-us-part-ii)).

*Inference:* paint **one corruption landscape layer that drives four outputs**:

- the ground material blend;
- a swap of the grass type to alien flora;
- dead or desaturated normal grass at the infection front;
- an RVT-sampled mask that grows veins on nearby props.

Grade corruption outward from an epicentre rather than drawing a hard border. Keep realistic PBR base values and change only hue, emissive accents and silhouette. Give alien flora the same clumping logic, but with slow pulsing wind instead of gusts so it reads "alive and wrong". Show half-swallowed props as evidence of the cause.

## Lighting, not assets, decides whether the frame reads real

### Lookdev discipline

The film method is calibrate, then judge. Each reference object has one job: the grey ball reads intensity and shadow, the chrome ball reads HDRI orientation, and the colour chart reads tone and saturation ([blenderartists](https://blenderartists.org/t/color-chart-question/1375162)). Chrome-ball light probes trace back to Debevec's image-based lighting ([befores & afters](https://beforesandafters.com/2021/04/27/vfx-firsts-what-was-the-first-film-to-use-a-hdri-chrome-ball/)). Cave Academy's order is to build the stage, build the light rig, calibrate it, and only then do lookdev. ACES puts middle grey at **0.18 scene-linear** ([ACES Central](https://community.acescentral.com/t/middle-gray-confusion/808)). UE's Filmic tonemapper matches ACES, with defaults Slope 0.88, Toe 0.55, Shoulder 0.26, Black Clip 0 and White Clip 0.04. Epic says to set these once per project, grade with Global colour correction in scene-linear space, use Exposure Bias rather than Gain, and prefer grading controls over LUTs ([Epic](https://dev.epicgames.com/documentation/en-us/unreal-engine/color-grading-and-the-filmic-tonemapper-in-unreal-engine)).

### Exposure and physical units in UE

UE uses physical units: Directional Light in **lux**, Sky Light and emissive in **cd/m²**. Exposure follows EV100 = log2(Aperture²/Shutter × 100/ISO). **Setting Min EV100 equal to Max EV100 disables auto-exposure.** The recommended histogram bounds are Low 70–80 and High 80–95. "Extend default luminance range" is needed for real lux values, but switching it on breaks existing exposure setups ([Epic Auto Exposure](https://dev.epicgames.com/documentation/en-us/unreal-engine/auto-exposure-in-unreal-engine); [Epic Physical Units](https://dev.epicgames.com/documentation/en-us/unreal-engine/using-physical-lighting-units-in-unreal-engine)). Forum and secondary sources put the sun at about **100–120k lux** and moonlight at about **0.1–1 lux** ([UE forum](https://forums.unrealengine.com/t/lighting-ratio-using-physically-based-light-with-skyatmosphere/2651660); [UE forum](https://forums.unrealengine.com/t/ffabien-kit-lighting-one-click-physically-based-lighting/2842730)).

### Lumen's hard rules for a castle

- **Walls at least 10 cm thick**, closed meshes, and separate wall, floor and ceiling pieces rather than one room mesh.
- Meshes get 12 Lumen cards by default. Pink in the Surface Cache view means that area gets no bounce and appears black in reflections.
- The software Lumen Scene covers about 200 m, extendable to 800 m.
- **Small emissive meshes are culled, so torches need real lights.**
- Foliage needs "Affect Distance Field Lighting", and software RT ignores World Position Offset.

All from [Epic Lumen](https://dev.epicgames.com/documentation/en-us/unreal-engine/lumen-technical-details-in-unreal-engine).

### Fog

**Exponential Height Fog:** a far Start Distance can cut fog cost by 50% or more.

**Volumetric fog:**

- Scattering distribution runs from 0 (even) to about 0.9 (strong forward shafts toward the light).
- Fog albedo is near 1.
- Shadow-casting point and spot lights cost about 3× more in volumetric fog.
- **Flickering lights leave temporal trails, so set their scattering to 0.**
- Translucent materials such as moat water need "Compute Fog Per-Pixel".

From [Epic Height Fog](https://dev.epicgames.com/documentation/en-us/unreal-engine/exponential-height-fog-in-unreal-engine) and [Epic Volumetric Fog](https://dev.epicgames.com/documentation/en-us/unreal-engine/volumetric-fog-in-unreal-engine).

*Inference, castle setup:*

- **Night:** a cool moon directional light at about 0.1–0.5 lux. Warm candela point-light torches paired with emissive flames. Exposure locked or held in a narrow band per zone. Ground mist from the second fog layer or a Local Fog Volume.
- **Day:** about 100k lux sun with Sky Atmosphere and a real-time-captured Sky Light. Exposure should land near EV100 14–15; that is the photographic "sunny 16" rule, not an Epic figure.
- **Darkness helps.** Blur's low-key, motivated lighting hides CG weaknesses. That is an observation from viewing the episodes, not a sourced claim.

### The common CG tells

Practitioners consistently cite these sourced tells:

- razor-sharp edges;
- "too perfect" surfaces;
- lifeless materials;
- light direction and colour temperature that don't match the scene;
- ungraded CG;
- overused flares and glows ([ProEdu](https://proedu.com/blogs/news/how-to-make-3d-renders-look-real); [Plemya](https://rossplemya.kit.com/posts/your-render-looks-fake-because-of-this); [Archviz Insider](https://archvisinsider.substack.com/p/avoid-these-5-cgi-mistakes-and-improve)).

The PBR sources add more:

- albedo outside 30–240 sRGB;
- baked AO or lighting in albedo;
- metallic rust or dirt;
- half-metal greys;
- bright diffuse paired with bright specular.

UE-specific tells inferred from the Lumen docs:

- light leaks through thin walls;
- black reflections on objects missing from the surface cache;
- flat ambient light where small emissives were culled;
- night auto-brightening into dusk.

These are practitioner consensus without a primary citation: uniform roughness, over-sharp shadows (missing Source Angle or Source Radius), floating objects without contact shadow, visible tiling, oversaturation, missing atmospheric perspective, and no wear where hands touch.

## Ranked playbook, most impact first

The ranking is an inference. It weighs how often each failure appears in the sources against how cheaply a small procedural team can fix it.

| Rank | Practice | Why it ranks here | Basis |
|---|---|---|---|
| 1 | Automated PBR gates in the bake script (albedo, metallic, metal floor, roughness variance) | Catches the most-cited errors at zero artist cost on every asset | Sourced ranges (Epic, Adobe); gates are inference |
| 2 | Neutral lookdev map with locked exposure; judge nothing in the castle level | Without it, every other decision is made under uncalibrated light | Sourced method (Cave Academy, Epic EV100) |
| 3 | Form-driven layer stack (edge, cavity, gravity, up-facing, wetness) plus a transition band at blends | Turns noise into evidence of physical history | Sourced: Lagarde maths, ND transition blend |
| 4 | Bevels sized from texel density (≥2–3 texels), 16-bit bakes, MikkTSpace, Nanite geometry for forms | Edges catching light is the top cited geometry tell | Sourced: Marmoset, Epic; thresholds inferred |
| 5 | Ground every prop: sink, debris skirt, RVT blend, world-aligned moss, contact darkening | Floating props break whole frames, not just one asset | Sourced: Epic RVT, PDO notes; stack inferred |
| 6 | Lumen-safe construction: ≥10 cm walls, modular closed meshes, real lights behind emissives | Castle architecture and torches are exactly what Lumen mishandles | Sourced: Epic Lumen |
| 7 | Rule-driven vegetation: clump noise, layered wind, multi-density culls, ground tint at the cull line | Uniform scatter reads as CG immediately | Sourced: GoT, Guerrilla, UE grass API |
| 8 | Macro/meso/micro separation: world-space macro variation plus distance-faded detail normal | Kills tiling and "clone" repetition | Sourced: Epic landscape; bands inferred |
| 9 | Night and fog lookdev: moon 0.1–0.5 lux, clamped exposure, zero volumetric scattering on flicker | Night is the castle's dominant mood and the easiest look to ruin | Sourced: Epic fog; values partly forum |
| 10 | Frame-filling detail and hero-shot propagation (Blur): lock one shot's look, reuse it | Empty surfaces and per-area tweaking erode consistency | Sourced: Chaos/Blur |
| 11 | Corruption as one physical system: a painted layer driving ground, flora, props and an epicentre gradient | Keeps the alien biome believable through real-world rules | Principle sourced (ND); application inferred |

## Pre-hand-off checklist with numeric thresholds

Thresholds marked † are inferences or common practice. Unmarked thresholds are sourced in the sections above.

| Area | Check | Pass threshold |
|---|---|---|
| Albedo | Dielectric BaseColor luminance | 30 (tolerant) / 50 (strict) to 240 sRGB; at most 2% of texels outside† |
| Albedo | No baked lighting or AO in BaseColor | Visual check in Buffer Visualization > Base Color; only micro-occlusion allowed |
| Metal | Metallic values | Exactly 0 or 1; non-binary on at most 5% of texels, only at rust/dirt transitions† |
| Metal | Metal BaseColor | ≥180 sRGB (≈0.45 linear); rust, dirt and paint have metallic 0 |
| Specular | UE Specular / Blender Specular IOR Level | 0.5 default; water 0.255, ice 0.224; cavity × 0.5 where cavity is used |
| Roughness | Variation | Standard deviation across the map well above 0†; extra polish on hand-contact areas† |
| Wetness | Darkening and gloss | Wet diffuse ≥ ×0.2 of dry; gloss boost damped by 0.5; metals not darkened |
| Layers | Grime masks | Every grunge layer masked by curvature, AO, world-up or gravity; no global overlay† |
| Geometry | Bevel width | ≥2–3 texels at target density (≥2–3 mm at 1024 px/m, ≥4–6 mm at 512 px/m)† |
| Geometry | Silhouette | Curves have enough sides that no faceting is visible at gameplay distance; low-frequency sag/warp applied† |
| Texel density | Project baseline | 1024 px/m close props, 2048 px/m hero, 512 px/m background†; trim islands within ±25% |
| Bake | Normal map | 16-bit bake, dithered to 8-bit; MikkTSpace; triangulated before bake; green flipped for UE (DirectX Y−) |
| Bake | AO | ≥512 rays for final (256 = medium) |
| Bake | Padding / misses | 8–16 px at 2K, 16–32 px at 4K†; 0 ray-miss pixels; no island bleed at mip 2–3† |
| Import | UE static mesh | Import Normals (not Compute); no degenerate-tangent warnings; Generate Lightmap UVs off for Nanite meshes |
| Lumen | Construction | Walls ≥10 cm; closed meshes; no pink in Surface Cache view; Max Lumen Mesh Cards raised if needed (default 12) |
| Lumen | Emissives | Every small emissive paired with a real light |
| Lookdev | Neutral scene | Grey ball albedo 0.18, chrome ball, colour chart, fixed HDRI, Min EV100 = Max EV100, Filmic defaults, no grade |
| Lookdev | Turntable | 360° under neutral HDRI, castle day (~100k lux sun†) and castle night (moon 0.1–0.5 lux† plus a torch) |
| Scale | Reference | Read correctly beside a 1.8 m mannequin† |
| Grounding | Contact | No visible gap; sunk 10–30%†; RVT blend over the bottom 20–50 cm†; contact darkening visible |
| Repetition | Tiling | Not visible at 5, 20 and 50 m† |
| Vegetation | Culling | PerInstanceFadeAmount in the material; dense variety culled ~30–60 m, mid ~80–150 m†; ground tinted to the grass colour at the cull line |
| Fog | Readability | Asset reads in height and volumetric fog at night; translucent materials use Compute Fog Per-Pixel; flicker lights have volumetric scattering 0 |

## Conclusion

Most of what makes CG look fake can be checked automatically. Albedo bounds, binary metallic, roughness variance, bevel-to-texel ratio, ray misses and wall thickness are all things a numpy and Blender pipeline can measure and reject before a human ever looks. That is a real advantage over hand-authored workflows. The judgement that can't be automated, whether wear and growth have a believable cause, is exactly what Naughty Dog and Blur put first. They light before they build and ask "how did this happen?" before they add anything. The team's competitive edge is therefore to put the numbers in the pipeline and spend artist time only on cause, composition and light.

The biggest open gaps are worth closing before locking the standard. First, Naughty Dog's public 2020 tech-art deck, likely the richest source of real layer and wetness parameters. Second, Epic's sample projects, whose actual light and post-process values can be read directly. Third, the Horizon and Returnal art books for corrupted-biome direction. Fourth, primary per-material roughness and albedo charts for wood, leather, rust and paint. No sourced numbers exist yet for edge-wear coverage, grass budgets per m², UE 5.3-specific Nanite foliage behaviour, or any Rockstar, Weta, ILM or Unit Image internal practice. Every threshold marked † above should be treated as a starting point to tune in the lookdev map, not a studio standard.
