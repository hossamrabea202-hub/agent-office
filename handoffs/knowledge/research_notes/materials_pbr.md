# Photoreal Materials: PBR Calibration, Layered Wear, Macro/Meso/Micro Detail (for Blender bakes to UE 5.3)

Scope note: about 20 tool calls. The calibration numbers (Epic, Adobe Substance, Lagarde) come from strong primary sources. Studio-specific methods for Rockstar, Sucker Punch and Guerrilla are mostly behind GDC Vault paywalls or in slide decks I could not open. Those gaps are flagged explicitly below.

## 1. How the named studios author and calibrate materials

### Takeaway
Primary sources give the *topics* AAA studios cover: uber shaders, painted shader blending, trim sheets, procedural texturing, wetness. They rarely give numbers. The most usable studio detail is Naughty Dog's. One "uber shader" covers almost every surface, artists vertex-paint between two or more shaders on one mesh with a transition blend layer, and shared trim sheets with baked bevels replace unique bakes.

### Cited Findings
- Naughty Dog's TLOU2 "Uber Shader" affects almost every surface in the game. Custom features included surface wetness, deformable snow and heightmaps that add depth to things like rock piles — [Kotaku summary of SIGGRAPH 2020 ND tech-art talk](https://kotaku.com/so-much-work-went-into-the-last-of-us-part-iis-eyes-1845162613)
- Primary source: "The Technical Art of The Last of Us Part II" (Waylon Brinck, Steven Tang), SIGGRAPH 2020. It covers rendering for mostly ambient-lit scenes, glass, rain and varied environments. Slides are public at https://s3.amazonaws.com/nd.images/research/2020_siggraph/NaughtyDog_TechArt_TLOU2-final.pptx (152.5 MB; I did not open it) — [Naughty Dog blog](https://www.naughtydog.com/blog/naughty_dog_at_siggraph_2020)
- TLOU2 shader painting: a single mesh is painted with two shaders. The visible seam between them is covered by a third "transition blend" (for example cement), and then extra details are added — [80.lv, Matthew Trevelyan Johns breakdown](https://80.lv/articles/breakdown-shader-painting-in-the-last-of-us-2/)
- TLOU Part I remake trim pipeline: baked-bevel trims freed texture memory. The goal was to "reduce the amount of uniquely baked props as well as other existing trims that didn't follow a shared layout", built with Substance Designer templates — [80.lv](https://80.lv/articles/the-last-of-us-remake-s-trim-pipeline-in-substance-3d-explained)
- Guerrilla (Horizon Forbidden West): the machines were textured with a procedural workflow that extended the Horizon Zero Dawn look and "saved months of production time" (Tom Delboo, GDC 2023). The abstract gives no technical numbers — [GDC Vault](https://gdcvault.com/play/1029327/Taking-a-Procedural-Approach-to)
- Sucker Punch (Ghost of Tsushima): the public material is about shading and lighting research (Jasmin Patry, SIGGRAPH 2020 PBS course, and Advances 2021 on lighting, atmosphere and tonemapping) plus world-scale instancing (GDC 2021 "Samurai Landscapes"). I found no published texel-density or material-authoring numbers — [Patry 2020 slides](https://blog.selfshadow.com/publications/s2020-shading-course/patry/s2020_pbs_patry_slides.pdf), [Advances 2021](https://www.advances.realtimerendering.com/s2021/jpatry_advances2021.pdf), [GDC Vault Samurai Landscapes](https://gdcvault.com/play/1027352/Samurai-Landscapes-Building-and-Rendering)
- Megascans scanning practice, from practitioners rather than official Quixel docs: cross-polarized capture removes specular from albedo, and specular is extracted by subtracting the cross-polarized shot from a parallel-polarized shot in *linear* space. Cross-polarization can shift luminance even after color-checker calibration. Albedo is a poor source for roughness — [Polycount threads (search results)](https://polycount.com/discussion/comment/2141652)
- DONTNOD (Remember Me, UE4) weathering system: wetness, dust, snow and ice are driven by 3 extra effect weights in an extra GBuffer target (6 RTs vs UE4's 5). Porosity is stored in GBuffer alpha. Authoring paths are object shader, then effect lights, then post-process, then screen-space decals (decals last so they can *remove* effects, e.g. dry areas). Artists also vertex-painted dry zones — [Lagarde, Weathering and aging effects](https://seblagarde.wordpress.com/2014/05/03/weathering-and-aging-effects/)

### Inferences
- For a small team, the most transferable studio pattern is ND's: a few tileable "base" materials, a vertex-color- or mask-driven blend between them, and a third *transition* material at the seam (grime, cement, rust) rather than a bare lerp. In a Blender bake this is a mix shader driven by a mask with a third layer on a thin band around the mask edge, e.g. `abs(mask-0.5)` remapped.
- Trim sheets with baked bevels are how AAA teams get edge highlights on cheap geometry. Baking the bevel into the normal map in Blender (Bevel shader node) matches that practice.

### Gaps
- Rockstar RDR2: I found no primary GDC, SIGGRAPH or artist interview on material authoring or weathering. Only fan-made RDR2-style scenes and unverified secondhand photogrammetry claims came up. Treat any "RDR2 does X" claim as unsourced.
- ND, Guerrilla and Sucker Punch internal numbers (texel density, layer counts, mask strengths) are not in any source I could open. The ND tech-art .pptx (above) is the best next read.
- No official Quixel document on Megascans albedo calibration was found.

## 2. PBR calibration: albedo, F0/specular, metalness, roughness

### Takeaway
Keep dielectric albedo between about 30-50 and 240 sRGB. Leave dielectric F0 at 4% (UE Specular 0.5). Metals are binary: metallic 1 with base color 180-255 sRGB (70-100% reflectance). Use metallic 0 for anything dirty, rusty or painted. Roughness has no "correct" value table in the primary sources; it is an artistic, per-surface decision that should be driven by the material's real wear state.

### Cited Findings
**Unreal Engine (official, applies directly to UE 5.3 Substrate-off default lit):**
- Nonmetal base color intensities (polarized measurement): charcoal 0.02, fresh asphalt 0.02, worn asphalt 0.08, bare soil 0.13, green grass 0.21, desert sand 0.36, fresh concrete 0.51, ocean ice 0.56, fresh snow 0.81 — [Epic, Physically Based Materials](https://dev.epicgames.com/documentation/en-us/unreal-engine/physically-based-materials-in-unreal-engine)
- Metal base color (linear RGB): iron 0.560/0.570/0.580, silver 0.972/0.960/0.915, aluminum 0.913/0.921/0.925, gold 1.000/0.766/0.336, copper 0.955/0.637/0.538, chromium 0.550/0.556/0.554, nickel 0.660/0.609/0.526, titanium 0.542/0.497/0.449, cobalt 0.662/0.655/0.634, platinum 0.672/0.637/0.585 — [Epic](https://dev.epicgames.com/documentation/en-us/unreal-engine/physically-based-materials-in-unreal-engine)
- Metallic: 0 for nonmetals and 1 for metals. Pure surfaces should be exactly 0 or 1, and intermediate values are only for hybrids like corroded or rusty metal. Metal-vs-paint masks should be strictly black and white — [Epic](https://dev.epicgames.com/documentation/en-us/unreal-engine/physically-based-materials-in-unreal-engine)
- Specular default 0.5 = about 4% reflectance. Measured values: glass 0.5, plastic 0.5, quartz 0.570, ice 0.224, water 0.255, milk 0.277, skin 0.35 — [Epic](https://dev.epicgames.com/documentation/en-us/unreal-engine/physically-based-materials-in-unreal-engine)
- Cavity maps: multiply Base Color by cavity, and use cavity × 0.5 for Specular (kills specular in crevices) — [Epic](https://dev.epicgames.com/documentation/en-us/unreal-engine/physically-based-materials-in-unreal-engine)

**Adobe Substance PBR Guide Part 2 (official):**
- Dielectric albedo should be no darker than 30 sRGB (tolerant) or 50 sRGB (strict), and no brighter than 240 sRGB — [Adobe PBR Guide pt 2](https://www.adobe.com/learn/substance-3d-designer/web/the-pbr-guide-part-2)
- Raw metal reflectance is 70-100%, which maps to 180-255 sRGB in base color. Raw-metal metallic is authored at 235-255 sRGB. If metallic goes below 235, lower the base color reflectance too — [Adobe](https://www.adobe.com/learn/substance-3d-designer/web/the-pbr-guide-part-2)
- Dielectric F0 in metal/rough is fixed at 0.04 linear. specularLevel 0-1 maps to F0 0.0-0.08, so 0.5 = 4%. Common dielectrics are 0.02-0.05 linear (sRGB 40-75), gemstones 0.05-0.17, liquids 0.02-0.04. Use 0.04 when the IOR is unknown — [Adobe](https://www.adobe.com/learn/substance-3d-designer/web/the-pbr-guide-part-2)
- Texel density should match document resolution. Low density makes metal/dielectric edge fringes visible (white fringes in metal/rough) — [Adobe](https://www.adobe.com/learn/substance-3d-designer/web/the-pbr-guide-part-2)
- sRGB to linear reference: 30 sRGB ≈ 0.009, 50 ≈ 0.028, 240 ≈ 0.875 linear — [Polycount thread (community calc)](https://polycount.com/discussion/comment/2636450)

**Lagarde (DONTNOD/Unity, primary author of the PBR charts):**
- The darkest natural material is about 0.04 (charcoal) and the brightest about 0.9 (snow). Pure water albedo is about 0.02 — [Lagarde, Water drop 3b](https://seblagarde.wordpress.com/2013/04/14/water-drop-3b-physically-based-wet-surfaces/). Note the conflict: Epic's table lists charcoal 0.02 and fresh snow 0.81. The differences come from measurement sources, so use either range as a sanity band.

### Inferences
- Practical gates for a procedural Blender bake pipeline. Clamp dielectric BaseColor luminance to linear 0.012-0.87 (sRGB about 30-240), or to linear 0.03 for the strict 50 sRGB floor. Assert metallic ∈ {0,1} except at rust or dirt transitions. Assert metal BaseColor ≥ about 0.45 linear (sRGB 180).
- Rust, dirt, paint and oxide on metal are dielectrics. Set metallic to 0 where the rust mask is set, rather than tinting the metal base color orange.
- With UE's default Specular 0.5 you rarely need a specular map. Only export one (or pack cavity) for water, skin or ice, or for cavity-occluded crevices.
- Blender's Principled BSDF "Specular IOR Level" 0.5 corresponds to UE Specular 0.5 (4%). Keep it at 0.5 in bakes so there is no mismatch. (This is my inference from Blender 4.x conventions and is not in the sources above.)

### Gaps
- I found no primary-source albedo table for wood, leather, cloth, wax, vegetation, rust or paint specifically. The DONTNOD PBR chart (Lagarde) contains such values, but the image URL I tried returned 404. Values like "rust albedo" or "leather albedo" circulating online are from community charts I could not verify.
- I found no primary-source roughness ranges per material. Adobe explicitly says roughness is artistic and gives no numeric targets.

## 3. Layering wear so it reads as physical (edges, cavity, gravity, wetness, moss)

### Takeaway
The best-sourced numbers are for wetness (Lagarde). Darken diffuse by up to `lerp(1, 0.2, porosity)`, raise smoothness with a 0.5-damped weight, and leave metals undarkened. Use world-up normals for dust and snow, and use decals or vertex paint to subtract effects (dry zones). Edge-wear and cavity-dirt conventions are standard practice but have little primary numeric sourcing.

### Cited Findings
- Wet diffuse: `factor = lerp(1, 0.2, Porosity)`, then `Diffuse *= lerp(1, factor, WetLevel)`. Literature range is 0.1-0.3 (Nakamae). Example: worn asphalt at 0.12 albedo becomes about 0.08 wet (sRGB 97 → 81) — [Lagarde, Water drop 3b](https://seblagarde.wordpress.com/2013/04/14/water-drop-3b-physically-based-wet-surfaces/)
- Measured darkening varies per RGB channel. For example, "Wood Drying 29" has factors of about (0.82, 0.58, 0.38): wet wood gets darker *and* more saturated/red — [Lagarde](https://seblagarde.wordpress.com/2013/04/14/water-drop-3b-physically-based-wet-surfaces/)
- Wet gloss: `Gloss = lerp(1, Gloss, lerp(1, factor, 0.5*WetLevel))`. Water gloss is 1.0, and the 0.5 is an empirical damping of the specular boost. Metals use `factor = lerp(1, 0.2, (1-Metalness)*Porosity)`, which means metals don't darken. Water F0 is 0.02 vs 0.04, a difference too small to bother modelling — [Lagarde](https://seblagarde.wordpress.com/2013/04/14/water-drop-3b-physically-based-wet-surfaces/)
- If there is no porosity map, derive porosity from gloss: `saturate(((1-Gloss)-0.5)/0.4)`. Rough surfaces are treated as porous — [Lagarde](https://seblagarde.wordpress.com/2013/04/14/water-drop-3b-physically-based-wet-surfaces/)
- Puddles and thin water are made by blending the normal map toward the vertex normal (flat water surface). Drying follows a sigmoid; in games a lerp over about 1 minute is suggested — [Lagarde](https://seblagarde.wordpress.com/2013/04/14/water-drop-3b-physically-based-wet-surfaces/)
- Dust (Killzone Shadow Fall approach) is applied where world normals point up. Rain/wet masks should be shadowed only by static geometry. World-space UVs from world position are needed for world effects and are tricky on vertical faces — [Lagarde, Weathering and aging](https://seblagarde.wordpress.com/2014/05/03/weathering-and-aging-effects/)
- Order in DONTNOD's system: object shader, then effect lights, then post-process, then decals. Decals come last so they can neutralize effects. Snow and dirt are mixed in the same graph for better blending — [Lagarde](https://seblagarde.wordpress.com/2014/05/03/weathering-and-aging-effects/)
- ND TLOU2 had custom surface-wetness and rain features in the uber shader (details are in the slides) — [Kotaku](https://kotaku.com/so-much-work-went-into-the-last-of-us-part-iis-eyes-1845162613)
- Dirt, rust and oxidation lower effective metal reflectance, so they must be authored as dielectric (metallic 0) with their own albedo — [Adobe PBR Guide pt 2](https://www.adobe.com/learn/substance-3d-designer/web/the-pbr-guide-part-2)

### Inferences (recommended bake order for Blender, layered from the sources plus standard practice)
1. Base material: calibrated albedo, F0 0.04, and roughness with its own low-frequency variation.
2. Edge wear from curvature (Blender: Geometry > Pointiness, or a Bevel-node vs true-normal difference, broken up by noise). It exposes the substrate: bare metal (metallic 1, lower roughness) under paint, or lighter and smoother polished wood.
3. Cavity/AO dirt: multiply a darker, rougher dielectric into crevices. Per Epic, also scale specular by cavity.
4. Gravity masks: world-Z gradient for ground splash, plus streaks (noise stretched along −Z, spawned beneath edges/cavities) for rain runs and rust runs. Rust runs set metallic to 0.
5. World-up dust/moss/snow: a `dot(N, +Z)` threshold multiplied by noise and AO. Moss should favor cavities and up-facing surfaces.
6. Wetness last, as a modifier on everything below: Lagarde's porosity darkening and gloss boost, with metals exempt.
- Keep each layer subtle. The wetness math caps darkening at ×0.2 even for fully porous, fully wet surfaces, and gives only a 0.5-damped gloss shift, which is a useful "how strong" anchor for other layers too.

### Gaps
- I found no primary source giving numeric strengths or coverage percentages for edge wear, cavity dirt or rain streaks at the named studios.
- Moss and rust-run techniques from ND, Rockstar or Guerrilla are not documented in sources I could open.

## 4. Macro/meso/micro detail and tiling breakup

### Takeaway
The sourced techniques are consistent. Use a large-scale macro variation mask that modulates the base texture, distance-dependent blending between tile scales or to an average color, height-lerp blends between layers, vertex-painted shader blends (ND) and shared trim sheets (ND). Detail normals add micro detail at close range.

### Cited Findings
- Epic's landscape layer system supports transitioning from detail textures to larger macro textures based on view distance — [Epic UDN, Landscape Materials](https://udn.epicgames.com/Three/LandscapeMaterials.html)
- Kite-demo materials blend whole layers with MatLayerBlend functions driven by a HeightLerp alpha (the heightmap is fed into the height input). The grass uses a distance texture far away to reduce tiling — [UE forum, Kite demo material question](https://forums.unrealengine.com/t/landscape-kitedemo-material-question/36944)
- Four combined anti-tiling methods taken from Epic's starter content: multi-scale texture blending, a high-contrast macro-variation mask, distance fade to average color, and more. Macro variation can shift hue (for example making grass darker green) if it isn't tuned — [UE forum](https://forums.unrealengine.com/t/how-i-made-a-landscape-material/43518) (community source); [Versluis tutorial](https://versluis.com/2023/05/how-to-use-macro-variations-for-unreal-engine-landscape-materials)
- ND: per-mesh vertex-painted blends between two shaders plus a transition blend, then added details — [80.lv](https://80.lv/articles/breakdown-shader-painting-in-the-last-of-us-2/). ND trims: baked-bevel shared trim layouts replace unique bakes — [80.lv](https://80.lv/articles/the-last-of-us-remake-s-trim-pipeline-in-substance-3d-explained)
- Deferred decals add local detail (e.g. wet footprints) and can remove effects — [Lagarde](https://seblagarde.wordpress.com/2014/05/03/weathering-and-aging-effects/)

### Inferences
- For baked, unique-UV props (the user's pipeline), tiling matters less than *frequency separation*. Bake macro (roughly 1-5 m: broad tone and roughness drift, sun or gravity fade), meso (roughly 1-20 cm: planks, chips, dents, mostly in the normal map) and micro (sub-cm: grain and pores). Then add a tiling detail normal in UE for the micro band, because the baked texel density cannot hold it.
- In UE, blend the detail normal with BlendAngleCorrectedNormals and fade it by distance. Drive macro variation from world position so repeated props don't look identical.
- Use vertex color (R/G/B) for per-instance wetness, moss and dirt overrides in UE instead of rebaking.

### Gaps
- I found no primary-source texel densities (e.g. px/m) for the named studios.
- I found no official Epic number for detail-normal tiling or distance-fade ranges.

## 5. Common mistakes that make materials look fake

### Takeaway
The primary sources name concrete failures: albedo outside 30-240 sRGB, lighting or AO baked into albedo, rust or dirt left metallic, grey-ish "half-metal" values, metal reflectance below 180 sRGB, and bright diffuse paired with bright specular. Uniform roughness and noise that ignores form are widely cited by practitioners, but I found no primary numeric sourcing for them.

### Cited Findings
- Lighting or AO baked into base color is wrong; only micro-occlusion is allowed. AO belongs in its own channel — [Adobe PBR Guide pt 2](https://www.adobe.com/learn/substance-3d-designer/web/the-pbr-guide-part-2)
- Dirt or rust left as raw metal, metal reflectance below 70% (180 sRGB), and a paint layer not marked dielectric are all named errors. So is bright diffuse with bright specular, which breaks energy conservation — [Adobe](https://www.adobe.com/learn/substance-3d-designer/web/the-pbr-guide-part-2)
- Intermediate metallic values on pure surfaces are an error; only corrosion-type hybrids get greys — [Epic](https://dev.epicgames.com/documentation/en-us/unreal-engine/physically-based-materials-in-unreal-engine)
- Too-dark albedo: no natural dielectric is darker than about 0.02-0.04 linear (charcoal) — [Epic](https://dev.epicgames.com/documentation/en-us/unreal-engine/physically-based-materials-in-unreal-engine), [Lagarde](https://seblagarde.wordpress.com/2013/04/14/water-drop-3b-physically-based-wet-surfaces/)
- Macro-variation color tinting can shift hue undesirably — [UE forum](https://forums.unrealengine.com/t/how-i-made-a-landscape-material/43518)

### Inferences
- Add automated checks to the bake script. Fail on BaseColor luminance outside linear 0.012-0.87 for dielectrics, on metallic values not in {0,1} beyond about 5% of texels, on metal BaseColor below 0.45 linear, and on a roughness map whose standard deviation is near 0 (uniform roughness).
- Oversaturation: the measured natural albedos above (soil 0.13, grass 0.21, sand 0.36) are dull. Keep procedural color saturation low and drive variation through value and roughness more than hue.
- Grunge should be masked by geometry (curvature, AO, world-up, gravity) rather than applied as a global noise overlay. This follows from every layering source above being form-driven.

### Gaps
- I found no primary source with numeric thresholds for "too much grunge" or for saturation limits.
- Studio-specific "lessons learned" lists (ND, Rockstar, Guerrilla, Sucker Punch) were not found in openable sources.
