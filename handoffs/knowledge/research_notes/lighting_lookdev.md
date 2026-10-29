# Lighting, Lookdev and Final-Image Photorealism (Film VFX + UE 5.3 Lumen)

## Q1. How do film/streaming VFX houses approach lookdev (HDRI, grey/chrome balls, Macbeth, turntables, ACES, exposure, lens artefacts)?

### Takeaway
The film method is "calibrate first, then judge". A colour chart sets white balance, an 18% grey ball sets exposure, and a chrome ball sets HDRI orientation and the key light's position. Assets are then lit in one fixed, neutral environment (HDRI plus turntable, colour-managed in ACEScg / scene-linear) so every asset is judged against the same reference. I found no primary ILM or Weta documents on their internal lookdev rigs. The specifics below come from training and practitioner sources.

### Cited Findings
- Chrome balls used as HDR light probes come from Paul Debevec's image-based lighting work: an HDR panorama shot from a chrome ball can serve as the entire lighting for a CG object. — [befores & afters, VFX Firsts](https://beforesandafters.com/2021/04/27/vfx-firsts-what-was-the-first-film-to-use-a-hdri-chrome-ball/)
- Each reference object has a job. The grey ball shows light intensity and shadows, the chrome ball shows HDRI orientation, and the colour chart shows colour tone and saturation. Grey cards are typically 18% grey (about LAB L 50). — [blenderartists thread](https://blenderartists.org/t/color-chart-question/1375162)
- Calibrating the real and CG setups "using a colour chart (for white balance) and grey ball (for exposure)" gets you about 90% of the way. The rest comes from how a real camera and lens form an image differently from a renderer. (Jahirul Amin, Cave Academy) — [Cave Academy: neutral lookdev environment](https://caveacademy.com/wiki/post-production-assets/surfacing/surfacing-training/creating-a-neutral-look-development-environment/)
- The Cave Academy workflow is: build a stage, build the light rig, calibrate the rig, and only then do lookdev. Their related topics include "Setting your Mid-Grey Value" and "Processing a 360 HDRI for Lighting in ACES". — [Cave Academy](https://caveacademy.com/wiki/post-production-assets/surfacing/surfacing-training/creating-a-neutral-look-development-environment/)
- A Macbeth chart lets shots in a sequence be white-balanced and exposed consistently. Lookdev artists use it to keep their lighting environment in a colour-controlled neutral space. Lay the chart flat where the HDRI is shot. — [Cave Academy](https://caveacademy.com/?p=35653); [Cave Academy](https://caveacademy.com/?p=38061)
- Standard lookdev kits bundle a turntable, a grey ball, a chrome ball, a Macbeth chart and studio HDRIs. — [Cave Academy lookdev props](https://caveacademy.com/product/houdini-look-development-and-lighting-props/); [Carsten Baars ACEScg lookdev HDA](https://carstenbaars.gumroad.com/l/xpaio)
- ACES puts middle grey at 0.18 scene-linear. — [ACES Central: Middle Gray confusion](https://community.acescentral.com/t/middle-gray-confusion/808)
- In ACES 2.0, the displayed middle grey can shift with peak luminance, so SDR and HDR views of the same grade may differ. — [ACES Central, ACES 2.0 meeting, Mar 2025](https://community.acescentral.com/t/aces-2-0-implementation-optimization-meeting-march-5th-2025/5732)
- HDRIs should be captured and stored as 32-bit and in ACEScg where possible, with backplates for the floor. — [Pixelsham (Xuan Prada / Greg Zaal)](https://www.pixelsham.com/?p=13000)
- HDRI light data is relative to pixel brightness and must be converted to real measured units. This is a SIGGRAPH 2016 note quoted in a reader comment, so it is secondary. — [Cave Academy comments](https://caveacademy.com/wiki/post-production-assets/surfacing/surfacing-training/creating-a-neutral-look-development-environment/)
- ILM's StageCraft is an LED volume built for *The Mandalorian*. StageCraft 2.0 (season 2) added a larger volume and Helios, ILM's own real-time renderer for the stage. — [Wikipedia: StageCraft](https://en.wikipedia.org/wiki/StageCraft); [Engadget](https://www.engadget.com/the-mandalorian-season-two-stagecraft-2-0-225548912.html)

### Inferences
- Game equivalent: build a "lookdev map" in UE with a grey ball (albedo about 0.18), a chrome ball (metallic 1, roughness 0), a Macbeth chart, a fixed HDRI Sky Light, one Directional Light, and a Post Process Volume with manual exposure. Every asset is checked there before hand-off, and the castle level is never used as the judge.
- UE's Filmic tonemapper follows ACES (see Q3), so a scene-linear workflow with 0.18 middle grey carries straight over from film.

### Gaps
- I found no primary Weta FX, ILM, Unit Image or Digic documents giving their exact lookdev rig, HDRI calibration steps or lens-artefact settings. fxguide and befores & afters breakdowns did not show up in search results.
- There were no sourced numbers for real lens artefacts (grain size, CA amount, vignette falloff) as used by film houses.

## Q2. What makes the photoreal Love, Death & Robots episodes look real?

### Takeaway
The best-documented technique, from Blur's *Shape-Shifters*, is detail density across the whole frame. They used very high poly counts through proxies (fences, trees, pebbles), volumetric atmosphere with accurate shadowing and camera blur, and set the look on one or two shots before reusing it across the scene. Note the studio credits: *The Secret War* is Digic Pictures (Platige only did concept work), and *Jibaro* is a stylised Alberto Mielgo piece, not a Blur photoreal episode.

### Cited Findings
- *Shape-Shifters* (Blur): photorealism had to extend across the whole frame, so environments were built with as much detail as possible. V-Ray Proxies allowed very high poly counts, and the Military Bunker scene used over 150 proxies (fences, trees, pebbles). — [Chaos blog](https://blog.chaos.com/the-render-tricks-behind-netflixs-nsfw-love-death-robots)
- *Shape-Shifters*: V-Ray Volume Grids handled atmospherics "with accurate shadowing, lighting and camera blur". The look was set on one or two shots and reused across the scene with little per-shot tweaking. — [Chaos blog](https://blog.chaos.com/the-render-tricks-behind-netflixs-nsfw-love-death-robots)
- *Sonnie's Edge* (Blur): progressive renders early in production meant animators saw performances under the final-style lighting, and lighting problems were solved before full lighting and compositing began. — [Chaos blog](https://blog.chaos.com/the-render-tricks-behind-netflixs-nsfw-love-death-robots)
- On *Bad Travelling*, Blur's lookdev began with lighting: they refined each sequence's look before building the assets. — [AWN](https://www.awn.com/print/news/how-blur-used-light-create-darkness-david-finchers-bad-travelling)
- Tim Miller: "Some stories, like Aquila Rift, had to be photoreal to be successful and horrifying." — [Art of VFX interview](https://www.artofvfx.com/?p=25209)
- *The Secret War*: Digic Pictures made the 15-minute episode, which won an Annie Award. Digic scanned and motion-captured real horses. Platige's credit is concept design "commissioned by DIGIC Pictures". — [3DVF / Digic coverage](https://3dvf.com/actualite-25912-peter-hostyanszki-showreel-lighting-et-compositing-2019-html/); [VG+](https://virtualgorillaplus.com/anime/love-death-and-robots-inside-the-animation/); [Behance concept credit](https://www.behance.net/gallery/115769975/Love-Death-Robots-The-secret-war)
- *Jibaro* is described as boundary-pushing CG by director Alberto Mielgo, with its own Netflix behind-the-scenes video. — [befores & afters LDR tag](https://beforesandafters.com/tag/love-death-robots)

### Inferences
- Lessons a game can borrow: (1) Fill the frame with small detail (pebbles, debris, fences) so no surface reads as empty. Nanite plus PCG scatter is the game version of V-Ray proxies. (2) Put atmosphere in front of the camera with lit volumes. (3) Lock a "hero shot" look and propagate it instead of tweaking every area. (4) Light early: grey-box lighting before final assets, as Blur did.
- From viewing, though not sourced: *Beyond the Aquila Rift* and *The Secret War* rely on dim, low-key, motivated lighting. Darkness hides CG weaknesses. That is relevant to the castle's night scenes.

### Gaps
- I found no making-of for Unit Image's *Beyond the Aquila Rift*, and no Digic lighting breakdown for *The Secret War*. Their Netflix "Inside the Animation" videos were not reachable as text.
- Studio credits come from my background knowledge and need confirming: Aquila Rift = Unit Image, Jibaro = Pinkman.tv / Mielgo. Art of VFX only lists Unit among the studios.

## Q3. Game side: UE5 Lumen, physical exposure, grading, fog, sky, Kelvin, AO. What do Epic's samples use?

### Takeaway
UE5 supports real light units: sun in lux, sky and emissive in cd/m². EV100 exposure follows the camera formula, and the Filmic tonemapper is ACES-based. To use real lux values, turn on "Extend default luminance range". Lumen has hard rules about scene construction: walls at least 10 cm thick, closed meshes, modular rooms, and a roughly 200 m Lumen Scene range. A castle can easily break those rules.

### Cited Findings: Exposure
- With physical camera exposure on, EV100 = log2(Aperture² / Shutter × 100 / ISO). Manual exposure = 1 / 2^(EV100 + Exposure Compensation). Auto-exposure meters to middle grey (about 18%). — [Epic: Auto Exposure](https://dev.epicgames.com/documentation/en-us/unreal-engine/auto-exposure-in-unreal-engine)
- Exposure Compensation is a 2^x scale: +1 is twice as bright, -1 is half. The histogram method (64 bins) is the default. Setting Min EV100 equal to Max EV100 disables auto-exposure. — [Epic: Auto Exposure](https://dev.epicgames.com/documentation/en-us/unreal-engine/auto-exposure-in-unreal-engine)
- Recommended values: Low Percent 70–80, High Percent 80–95, Local Exposure Highlight/Shadow contrast 0.6–1, Blurred Luminance Blend 0.4–0.6, Detail Strength 1. The exponential transition distance defaults to 1.5 stops (`r.EyeAdaptation.ExponentialTransitionDistance`). — [Epic: Auto Exposure](https://dev.epicgames.com/documentation/en-us/unreal-engine/auto-exposure-in-unreal-engine)
- "Extend default luminance range in Auto Exposure settings" (Project Settings > Rendering) switches the min/max fields to EV100. That lets you use correct lux values without blowing out the image. Switching an existing project breaks its current exposure setups. — [Epic: Auto Exposure](https://dev.epicgames.com/documentation/en-us/unreal-engine/auto-exposure-in-unreal-engine); [Epic: Physical Lighting Units](https://dev.epicgames.com/documentation/en-us/unreal-engine/using-physical-lighting-units-in-unreal-engine)
- Use the Visualize HDR show flag to narrow the histogram min and max around the range the scene actually uses. Black patches on reflective surfaces mean you should enable "Apply Pre-Exposure before writing to the scene color" or dim the light. Always place a Post Process Volume. — [Epic: Physical Lighting Units](https://dev.epicgames.com/documentation/en-us/unreal-engine/using-physical-lighting-units-in-unreal-engine)

### Cited Findings: Light units and values
- Directional Light is set in lux. Sky Light and emissive are set in cd/m². Point, Spot and Rect lights can use candela or lumens, which need inverse-squared falloff. 1 cd = 625 unitless. A 1000 cd light gives 1000 lux at 1 m. For a point light, 1 cd ≈ 12.6 lm. A narrower spot cone in lumens lights surfaces more strongly. — [Epic: Physical Lighting Units](https://dev.epicgames.com/documentation/en-us/unreal-engine/using-physical-lighting-units-in-unreal-engine)
- Sun values: the Sky Atmosphere docs are quoted as saying a white surface under the sun at zenith receives about 150,000 lux in total, with the sky contributing about 20%. Forum users use roughly 100–120k lux for the sun, or about 111k lux sun plus 20k lux sky. These are secondary sources, and a reference table elsewhere lists direct sun at 32–100k lux. — [UE forum: lighting ratio w/ SkyAtmosphere](https://forums.unrealengine.com/t/lighting-ratio-using-physically-based-light-with-skyatmosphere/2651660); [UE forum 4.19 Physical Lights](https://forums.unrealengine.com/t/4-19-physical-lights/105121?page=8)
- Moonlight is roughly 0.1–1 lux in the real world. A UE plugin uses a bluish 0.25 lux full moon. These come from a forum and a plugin, not Epic. — [UE forum: Kit-Lighting](https://forums.unrealengine.com/t/ffabien-kit-lighting-one-click-physically-based-lighting/2842730)
- For a physically based lighting reference database for UE5, see the PBL database article on 80.lv. — [80.lv PBL database](https://80.lv/articles/get-started-with-physically-based-lighting-in-ue5-with-pbl-database)

### Cited Findings: Lumen rules
- Walls should be at least 10 cm thick to avoid light leaks. Very thin or one-sided meshes seen from behind are poorly represented, so use closed geometry. — [Epic: Lumen Technical Details](https://dev.epicgames.com/documentation/en-us/unreal-engine/lumen-technical-details-in-unreal-engine)
- Make walls, floors and ceilings separate meshes, not one room mesh with furniture. Large single meshes (a mountain, a multi-storey building) cause self-occlusion. Meshes get up to 12 cards by default; raise "Max Lumen Mesh Cards" for complex shapes. Pink in the Surface Cache view means no coverage, so that area won't bounce light and goes black in reflections. — [Epic: Lumen Technical Details](https://dev.epicgames.com/documentation/en-us/unreal-engine/lumen-technical-details-in-unreal-engine)
- The software RT Lumen Scene covers about 200 m. "Lumen Scene View Distance" extends it to 800 m, and sky occlusion fades past 200 m. Hardware RT Far Field reaches 1 km and needs `r.LumenScene.FarField=1` plus HLOD1. — [Epic: Lumen Technical Details](https://dev.epicgames.com/documentation/en-us/unreal-engine/lumen-technical-details-in-unreal-engine)
- Small emissive meshes are culled from the Lumen Scene, so lighting from them is inconsistent. Torches and candles need real lights, not emissive alone. Light leaks in cave-like areas: raise Lumen Scene Detail and Max Trace Distance. Splotchy reflections: raise Lumen Scene Quality, or use Hit Lighting for Reflections. — [Epic: Lumen Technical Details](https://dev.epicgames.com/documentation/en-us/unreal-engine/lumen-technical-details-in-unreal-engine)
- Foliage needs "Affect Distance Field Lighting". Software RT does not support World Position Offset. Large Indirect Lighting Scale values make GI view-dependent through Screen Traces. Epic scalability targets 30 fps at about 8 ms for GI plus reflections at 1080p internal resolution, and High targets 60 fps. — [Epic: Lumen Technical Details](https://dev.epicgames.com/documentation/en-us/unreal-engine/lumen-technical-details-in-unreal-engine)
- Outdoor Lumen noise can come from a very bright sun baked into the sky environment map. Advice from users: constrain exposure and add direct lighting. — [UE forum: Lumen GI and PBR values](https://forums.unrealengine.com/t/lumen-gi-and-pbr-values/2657431)

### Cited Findings: Fog
- Exponential Height Fog settings are Fog Density, Height Falloff (smaller values give a longer transition), Max Opacity, Start Distance, Cutoff Distance, and a Second Fog Data layer (density 0 disables it). A far Start Distance can cut fog cost by 50% or more. — [Epic: Exponential Height Fog](https://dev.epicgames.com/documentation/en-us/unreal-engine/exponential-height-fog-in-unreal-engine)
- Volumetric Fog Scattering Distribution runs from 0 (even in all directions) to about 0.9 (forward, giving strong shafts toward the light). For visible side-lit shafts, keep it nearer 0. Albedo for fog, cloud and mist is near 1; dust is darker. Extinction Scale above 1 means more absorption. — [Epic: Exponential Height Fog](https://dev.epicgames.com/documentation/en-us/unreal-engine/exponential-height-fog-in-unreal-engine); [Epic: Volumetric Fog](https://dev.epicgames.com/documentation/en-us/unreal-engine/volumetric-fog-in-unreal-engine)
- Per-light Volumetric Scattering Intensity defaults to 1, and 0 disables it. Shadow-casting point and spot lights in volumetric fog cost about 3× more. Fast-changing lights such as flicker leave temporal trails; set their scattering to 0. Volumetric fog costs about 1 ms on PS4 High and about 3 ms on a GTX 970 at Epic. — [Epic: Volumetric Fog](https://dev.epicgames.com/documentation/en-us/unreal-engine/volumetric-fog-in-unreal-engine)
- Volumetric fog does not support IES profiles or light functions on point and spot lights, Source Radius, or self-shadowing. Inside View Distance it replaces the height fog inscattering colour. Translucent materials such as moat water should enable "Compute Fog Per-Pixel". — [Epic: Volumetric Fog](https://dev.epicgames.com/documentation/en-us/unreal-engine/volumetric-fog-in-unreal-engine)

### Cited Findings: Grading and tonemapper
- The Filmic tonemapper matches ACES. Its defaults are Slope 0.88, Toe 0.55, Shoulder 0.26, Black Clip 0, White Clip 0.04. Emissive desaturates to white as it saturates, as on real film. — [Epic: Color Grading & Filmic Tonemapper](https://dev.epicgames.com/documentation/en-us/unreal-engine/color-grading-and-the-filmic-tonemapper-in-unreal-engine)
- Set the Film controls once for the whole project. Do the look with Global colour correction, which works in scene-linear space before tonemapping. Don't use Gain for exposure; use Exposure Bias. Prefer grading controls over LUTs, because LUTs apply after tonemapping and don't carry over to HDR. — [Epic: Color Grading & Filmic Tonemapper](https://dev.epicgames.com/documentation/en-us/unreal-engine/color-grading-and-the-filmic-tonemapper-in-unreal-engine)

### Cited Findings: Epic samples
- The Matrix Awakens city: tall buildings block the sun at street level, so most on-screen lighting is Lumen GI. With Lumen off, almost the whole screen goes black. This comes from a secondary video transcript. — [lilys.ai notes](https://lilys.ai/zh/notes/unreal-engine-5-20251111/unreal-engine-5-lumen-global-illumination); [befores & afters Matrix Awakens BTS](https://beforesandafters.com/2022/04/06/these-matrix-awakens-behind-the-scenes-videos-are-fantastic)
- Electric Dreams (UE 5.2) is a PCG showcase: a jungle built from a few Quixel assets, plus a 4×4 km fully procedural area, integrated with Lumen and Nanite. — [CG Channel](https://www.cgchannel.com/?p=148070); [ArtStation Magazine](https://magazine.artstation.com/2023/06/epic-games-unreal-engine-electric-dreams-art-blast/)

### Inferences
- Castle night setup (an inference, not a sourced recipe): turn on Extend Luminance Range. Moon Directional Light at about 0.1–0.5 lux, cool tint. Torches as real point lights with inverse-squared falloff in candela, warm tint, plus emissive meshes. Fix the exposure range (Min equals Max EV100) for each zone, or keep a narrow band, so night stays dark instead of auto-brightening to grey. Keep flickering torch Volumetric Scattering Intensity low or 0 to avoid trails. Use a Local Fog Volume or the second height fog layer for courtyard ground mist.
- Day setup: sun at about 100k lux plus Sky Atmosphere, with a Sky Light in real-time capture mode. Exposure then lands around EV100 14–15. That EV figure is the photographic "sunny 16" rule and is not from an Epic source.
- Castle walls are thick, which suits Lumen. Banners, thin roofs, ivy and one-sided wall cards will leak light and need closed geometry or a real thickness of 10 cm or more.

### Gaps
- I found no official Epic list of real-world EV100 or lux values. The Epic physical units page had no such table. Sourced Kelvin values for light colour (candle, tungsten, moonlight) were not found; common values like candle about 1900 K and tungsten about 2700–3200 K are background knowledge and need a source.
- I found no published lighting settings for Valley of the Ancient, Matrix Awakens or Electric Dreams. You would need to open the sample projects and read their Directional Light, Sky Light and Post Process Volume values directly.
- There are no sourced specifics on contact shadows, DFAO or SSAO tuning, or Epic's defaults for lens effects (grain, chromatic aberration, vignette).

## Q4. The most common "CG tells"

### Takeaway
Practitioner sources agree on these tells: razor-sharp edges, flat or uniform materials, light direction and colour that don't match the scene, missing grading, overused lens effects, and unconvincing motion. I found no authoritative VFX-supervisor source that lists the full set (light ratio, scale, floating objects, repetition). Treat those as expert consensus that still needs a citation.

### Cited Findings
- Perfect hard edges almost never exist in reality, even on the hardest surfaces, so add micro-bevels or fake them with normals so edges catch light. — [ProEdu](https://proedu.com/blogs/news/how-to-make-3d-renders-look-real); [Highend3D micro bevel](https://www.highend3d.com/tutorials/faking-micro-bevel-with-mentalray)
- "Too perfect" is a common critique even of renders with otherwise high-detail textures. — [Ross Plemya](https://rossplemya.kit.com/posts/your-render-looks-fake-because-of-this)
- Lifeless materials that don't interact with light naturally are a common pitfall. Light direction and colour temperature must match the scene. Grade CG layers to match. Motion must feel physically believable. — [DEV Community CGI checklist](https://dev.to/maverickframe/why-cgi-ads-look-fake-a-practical-quality-checklist-for-brands-3iol); [Archviz Insider](https://archvisinsider.substack.com/p/avoid-these-5-cgi-mistakes-and-improve)
- Overusing lens flares and glows is a tell: "less is more". — [Archviz Insider](https://archvisinsider.substack.com/p/avoid-these-5-cgi-mistakes-and-improve)
- The remaining part of realism comes from real camera and lens image formation, which renderers don't reproduce by default. — [Cave Academy](https://caveacademy.com/wiki/post-production-assets/surfacing/surfacing-training/creating-a-neutral-look-development-environment/)
- Shape-Shifters filled the whole frame with dense detail so nothing read as empty. — [Chaos blog](https://blog.chaos.com/the-render-tricks-behind-netflixs-nsfw-love-death-robots)

### Inferences
- Tells specific to Lumen and UE (from the Lumen docs above): light leaking through thin walls, black reflections on objects missing from the surface cache, GI popping when the camera moves fast, flat ambient where small emissives were culled, and auto-exposure brightening night to dusk.
- The rest of the requested list is not sourced here: over-sharp shadows (set Source Radius / Source Angle on lights), wrong key-to-fill ratio, too much saturation, no atmospheric perspective, uniform specular (vary roughness), no wear where hands touch, floating objects with no contact shadow or AO, visible tiling, and no scale reference. The report writer should present these as practitioner consensus.

### Gaps
- I found no SIGGRAPH or fxguide source that lists the full set of CG tells, and no source with numeric key-to-fill ratios.

## Q5. Lookdev checklist before asset hand-off

### Takeaway
Combine the film calibration steps (Q1) with UE and Lumen asset rules (Q3) into a pass/fail check run in a neutral lookdev map.

### Cited Findings (basis for checklist items)
- Calibrate first: colour chart for white balance, grey ball for exposure. — [Cave Academy](https://caveacademy.com/wiki/post-production-assets/surfacing/surfacing-training/creating-a-neutral-look-development-environment/)
- Use a neutral lookdev environment with a turntable, grey and chrome balls, a Macbeth chart and an HDRI. — [Cave Academy props](https://caveacademy.com/product/houdini-look-development-and-lighting-props/)
- Lumen checks: closed mesh, walls 10 cm or thicker, distance field resolution correct for the import scale, Surface Cache coverage (no pink), Max Lumen Mesh Cards, Nanite for high-poly and foliage, and material overrides that match the asset material (blend mode and two-sided). — [Epic: Lumen Technical Details](https://dev.epicgames.com/documentation/en-us/unreal-engine/lumen-technical-details-in-unreal-engine)
- Micro-bevels on edges. — [Highend3D](https://www.highend3d.com/tutorials/faking-micro-bevel-with-mentalray)
- Translucent materials: Compute Fog Per-Pixel. — [Epic: Volumetric Fog](https://dev.epicgames.com/documentation/en-us/unreal-engine/volumetric-fog-in-unreal-engine)

### Inferences (proposed checklist; items beyond the cited ones are expert practice)
1. Lookdev map: grey ball (albedo 0.18), chrome ball, Macbeth chart, neutral HDRI Sky Light, one sun, manual exposure (Min EV100 = Max EV100), project Filmic defaults, no grade.
2. Turntable: a 360° spin under three setups: neutral HDRI, castle day (about 100k lux sun), and castle night (moon plus a torch).
3. Albedo in a plausible range, with no pure black or white. Check with Buffer Visualization > Base Color.
4. Roughness varies: no uniform specular, and more wear and polish where hands touch (handles, rails, steps).
5. Edges: micro-bevels or edge wear, with no razor edges in silhouette.
6. Scale: the asset sits next to a 1.8 m mannequin reference.
7. Grounding: no gaps under the asset, with contact AO and shadows visible.
8. Lumen: closed mesh, 10 cm or thicker, no pink in the Surface Cache view, distance field looks right in the Mesh Distance Fields view, no leaks at night.
9. Repetition: tiling not visible at 5 m, 20 m and 50 m. Use macro variation or a vertex-paint layer.
10. Emissive: a real light is paired with any small emissive (Lumen culls small emissives).
11. Fog: check readability in volumetric fog and height fog at night, and check that translucent materials use per-pixel fog.

### Gaps
- I found no published studio-grade asset hand-off checklist from ILM, Weta or Epic. The list above is a synthesis.
- I found no sourced albedo ranges (for example sRGB 30–240 or the PBR charts). Chris Brejon's albedo article, linked from Cave Academy, is a likely primary source but I did not fetch it.
