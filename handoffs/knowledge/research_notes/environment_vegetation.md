# Photoreal Environments, Ground and Vegetation (UE 5.3, Blueprint-only, small team)

Scope note: about 16 searches and fetches. Primary sources reached: Guerrilla's talk page, GDC Vault session pages, Epic UE docs (RVT, Electric Dreams, Grass Variety API), and 80.lv's Naughty Dog interview. Several key primary decks could not be read: the Guerrilla PDF was over 10 MB, and the GDC videos are paywalled or video-only. Some details therefore come from secondary write-ups, and those are flagged.

## How did Sucker Punch, Guerrilla, Rockstar, Naughty Dog and Epic/Quixel build vegetation and ground?

### Takeaway
None of these studios hand-places grass. Each drives placement from painted or generated maps (tile textures, density maps, PCG graphs). They save hand-authoring for hero flora (pampas, spider lilies), story spaces and overgrowth. In UE 5.3 terms, the lesson for a small team is: Landscape Grass Types or PCG driven by landscape layers, plus hand-placed hero clusters.

### Cited Findings
- **Sucker Punch, grass talk.** "Procedural Grass in 'Ghost of Tsushima'" (GDC 2021 Advanced Graphics Summit, Eric Wohllaib). The art goal was large wind-swept fields. Blades are generated individually on the GPU, so each blade gets its own procedural look and animation. The talk covers keeping "acres" of grass inside memory and performance budgets. The session page gives no blade counts. — [GDC Vault](https://gdcvault.com/play/1027214/Advanced-Graphics-Summit-Procedural-Grass)
- **Ghost of Tsushima grass details** (secondary: Stylized Station thread summarising the talk):
  - Grass cards were tried first and dropped because of overdraw at the required density.
  - The world is split into tiles. Each tile has textures for terrain height, terrain material and grass type.
  - Each blade is a bezier curve built from per-grass-type parameters (height, width, tilt, colour), placed by a compute shader with random offsets.
  - LODs: 15 vertices high, 7 vertices low. Vertices morph toward the low LOD near the switch distance to hide popping.
  - Short blades are folded in the middle into two blades, which doubles apparent density at no extra cost.
  - At far distance, all foliage is replaced by an artist-authored texture.
  - Spider lilies and pampas are artist-modelled meshes, distributed by the same tile parameters. — [Threadreader/Stylized Station](https://threadreaderapp.com/thread/1688939411575119872)
- **Sucker Punch, wind talk.** A separate talk: "Blowing from the West: Simulating Wind in Ghost of Tsushima" (Bill Rockenbeck, GDC 2021). The wind is applied to particles, foliage, grass and cloth, and drives the Guiding Wind mechanic. — [GDC Vault](https://gdcvault.com/play/1027124/Blowing-from-the-West-Simulating). GDC's news page says it involves "hundreds of thousands of particles" — [GDC news](https://gdconf.com/news/see-how-ghost-tsushima’s-guiding-wind-came-life-gdc-2021)
- **Guerrilla, procedural placement** (Horizon Zero Dawn, GDC 2017, Jaap van Muijden). Artists author placement rules in a graph editor. GPU algorithms create a dense world around the player on the fly, including sounds, effects, wildlife and gameplay elements, not just rocks and trees. The talk demos painting a tree line, redirecting roads, and converting a desert into a tropical swamp. — [Guerrilla Games](https://www.guerrilla-games.com/read/gpu-based-procedural-placement-in-horizon-zero-dawn)
- **Guerrilla figures** (from a search summary of the slide deck; the PDF itself was too large to fetch, so verify before quoting):
  - 2D density maps are discretised into points by dithering.
  - 500+ asset types and 100,000+ objects in scene.
  - About 250 µs average GPU busy load.
  - World data about 32 bits per square metre. — [Guerrilla deck PDF](https://www.guerrilla-games.com/media/News/Files/GDC2017_VanMuijden_GPUBasedProceduralPlacementInHorizonZeroDawn.pdf); [80.lv summary](https://80.lv/articles/the-procedural-nature-of-the-horizon-zero-dawn)
- **Rockstar, RDR2 mud** (secondary graphics study from frame captures, not Rockstar). Human and horse footprints and wagon-wheel trails are rendered into an accumulated 2048x2048 R16_UNORM displacement map. That map drives parallax occlusion mapping on the terrain. Terrain polygon count stays very high. — [imgeself RDR2 graphics study](https://imgeself.github.io/posts/2020-06-19-graphics-study-rdr2)
- **Naughty Dog, TLOU2 overgrowth as story.** Anthony Vaccaro has artists justify placement with questions like "Is there enough sunlight here to promote vegetation growth?" and "How did this happen?" before adding damage or plants. Reuben Shah says foliage represents "growth and an undying world" and supports colour theming. Grass cover density was iterated "dozens of times" against performance and the stealth visibility volumes. — [80.lv, Naughty Dog interview](https://80.lv/articles/how-naughty-dog-created-the-immersive-world-of-the-last-of-us-part-ii)
- **Naughty Dog shaders.** Steven Tang's custom shaders add dynamic wetness and mud, and "each effect has its own grunge mask". A material mod system writes wet beach surfaces to a buffer. — [80.lv](https://80.lv/articles/how-naughty-dog-created-the-immersive-world-of-the-last-of-us-part-ii)
- **Naughty Dog vehicles.** TLOU2 vehicles have a moss-overgrowth look for heavy-foliage areas, and the library holds about 500 vehicles (artist ArtStation). — [Trevelyan ArtStation](https://trevelyan.artstation.com/projects/XngOra)
- **Epic, Electric Dreams.** The environment mixes hand-crafted and procedural areas, both built with PCG:
  - "Assemblies" (pre-built prop and rock groups) form the large cliff.
  - A ditch-embankment rule runs along an open spline.
  - A parametrised PCG forest, a procedural riverbed and creek, and a spline path that places assemblies.
  - Levels are 4 km x 4 km World Partition.
  - Minimum spec runs at 50% screen percentage at 1080p. — [Epic docs: Electric Dreams](https://dev.epicgames.com/documentation/en-us/unreal-engine/electric-dreams-environment-in-unreal-engine)
- **Epic, Valley of the Ancient.** A Nanite and Lumen sample in which Megascans make up about 90% of the environment assets (per Epic's localised doc page, via search summary). — [Epic docs: Valley of the Ancient](https://dev.epicgames.com/documentation/unreal-engine/valley-of-the-ancient-sample-game-for-unreal-engine)
- **Megascans on custom ground.** A Japanese tutorial notes that Megascans material colours often clash with the ground by default, so parameters must be tuned to blend them. — [CGWorld](https://cgworld.jp/regular/202206-pt-044.html)
- **Quixel foliage and Nanite.** A 2025 Unreal Fest session says the Quixel foliage library was updated to make foliage more viable with Nanite. — [Unreal forums, talk listing](https://forums.unrealengine.com/t/talks-and-demos-megascans-vegetation-what-s-new-and-what-s-coming-soon/2705282)

### Inferences
- In UE 5.3 Blueprint-only, the closest equivalents need no C++:
  - **GoT tile maps:** Landscape paint layers driving a Landscape Grass Type (LandscapeLayerSample into the Grass Output node).
  - **Guerrilla density maps and rule graphs:** a PCG graph sampling landscape layers, using Density Filter and Self Pruning nodes.
  - **Electric Dreams assemblies:** Level Instances or Packed Level Actors used as "assemblies".
- GPU-generated grass blades like GoT's need custom compute work, which is out of reach for Blueprint-only. Use cards or Megascans grass meshes and fake the GoT tricks instead:
  - noise-driven clumping of colour and height (sample a large world-space noise in the material);
  - far-distance replacement by a terrain colour texture (tint the landscape base colour to the grass colour at distance, so grass culling is invisible).
- RDR2-style accumulated mud is a render-target trick. A Blueprint version is possible: draw footprints into a render target with Draw Material to Render Target, then sample it in the landscape material. This is an inference, not a documented recipe.

### Gaps
- No GoT blade counts, tile size, density or memory numbers were found in primary sources. The talk video holds them.
- Guerrilla's 250 µs / 32 bits per m² / 500+ assets figures come from a search summary of the PDF and need checking in the deck.
- No official Rockstar talk on RDR2 vegetation or terrain was found. The blog points to a SIGGRAPH talk by Fabian Bauer, which was not opened.
- No primary TLOU2 vegetation tech talk was found. Cook and Becker's interview with art director John Sweeney exists but was not read: [link](https://www.cookandbecker.com/en/article/250/art-directing-the-last-of-us-part-ii.html)

## Vegetation realism: density, clumping, species mix, colour variation, translucency, wind layers, LODs/imposters, budgets

### Takeaway
Realism comes from structured non-randomness: clumps that share height, colour and direction, layered wind (global gust noise plus per-blade bob), LOD morphing, and a distance hand-off to a ground colour that matches the grass. UE's Landscape Grass density is defined per 10 m², with start and end cull distances per variety.

### Cited Findings
- **GoT clumping.** Procedural noise groups blades into clumps that vary height, colour and direction, modelled on soil nutrients. Pure random heights were rejected: "Real grass isn't simply random heights though." — [Stylized Station thread](https://threadreaderapp.com/thread/1688939411575119872)
- **Voronoi clumps.** Community re-implementations use Voronoi or cellular-noise clumps that share parameters and rotational offsets. — [Unity-Grass](https://cainrademan.github.io/Unity-Grass/); [GodotGrass](https://github.com/2Retr0/GodotGrass)
- **GoT wind layers.** A scrolling 2D Perlin noise texture sets wind strength per point (the gust field). It is blended with a sine-wave "bobbing", plus per-blade procedural variation so neighbouring blades never move in sync. — [Stylized Station thread](https://threadreaderapp.com/thread/1688939411575119872)
- **GoT shading tricks.**
  - Curved normals make flat blades look rounded.
  - Blades nearly edge-on to the camera are rotated toward it so they don't look paper-thin.
  - Folded short blades double apparent density. — [Stylized Station thread](https://threadreaderapp.com/thread/1688939411575119872)
- **GoT LOD and far field.** 15-vertex and 7-vertex LODs with vertex morphing at the transition. Far foliage is replaced by an artist-authored texture. — [Stylized Station thread](https://threadreaderapp.com/thread/1688939411575119872)
- **UE Grass Variety settings.**
  - Density is "instances per 10 square meters".
  - Start Cull Distance is where fading begins; End Cull Distance is where instances are fully faded and the cluster is culled. Fading requires the PerInstanceFadeAmount material node.
  - A value of 0 disables the cull. — [UE 5.1 Python API: GrassVariety](https://docs.unrealengine.com/5.1/en-US/PythonAPI/class/GrassVariety.html)
- **Cull settings location.** They live in the Landscape Grass Type asset under Grass Varieties. — [Epic: Open World Tools tips](https://dev.epicgames.com/documentation/unreal-engine/open-world-tools-tips-in-unreal-engine?lang=en-US)
- **Density by distance (community).** Start/end cull do not create a density falloff band. The workaround is several copies of the same grass at different densities, each with its own cull range (dense near, sparse far). — [Unreal forums](https://forums.unrealengine.com/t/reduce-grass-density-by-distance/50086)
- **Density cap (old).** A per-variety density cap of 1000 was reported in 4.22. It may be outdated. — [Unreal forums](https://forums.unrealengine.com/t/landscape-grass-type-max-density-limit/126532)
- **Gameplay as a budget driver.** TLOU2 tuned grass density against performance and stealth visibility. — [80.lv](https://80.lv/articles/how-naughty-dog-created-the-immersive-world-of-the-last-of-us-part-ii)

### Inferences
- A practical UE 5.3 grass recipe, inferred from the sources above:
  - Use 2–3 grass varieties per layer: dense near, with a cull around 30–60 m; sparser mid, with a cull around 80–150 m.
  - Fade with PerInstanceFadeAmount.
  - Tint the landscape under the grass to the grass's average colour, so the cull boundary disappears (the GoT far-field trick).
  - These distances are a starting point, not sourced figures. Profile with `stat foliage` and GPU Visualizer.
- **Colour variation:** in the foliage material, lerp between 2–3 tints using a large world-space noise (clump scale, 3–10 m) plus a small per-instance random value (PerInstanceRandom). Matching the GoT approach, noise-driven clumps should also scale instance height. In Landscape Grass Types this is limited to Scale X/Y/Z ranges, so the material has to do the clumping.
- **Species mix:** follow the real-plant logic TLOU2 uses ("enough sunlight here?"). Put dense grass in open light, ferns and moss in shade or under trees, and flowers in sparse clusters. Never spread flowers evenly.
- **Translucency:** use the Two Sided Foliage shading model with subsurface colour. This is standard UE practice and was not sourced in this pass.
- **Nanite foliage in 5.3:** Nanite supports WPO wind, but it was not sourced here. See the gaps.

### Gaps
- No sourced shipped-game triangle or instance budgets per m² were found (GoT, HZD or TLOU2).
- Not verified from a primary doc this pass: Nanite foliage and WPO behaviour in 5.3, Two Sided Foliage and subsurface setup, imposter (Impostor Baker) workflows, and UE's Pivot Painter wind. Another researcher or the Epic docs should confirm them.
- The full method of GoT's wind talk (how the gust field reaches trees) was not reachable.

## Ground: layered terrain materials, height blending, macro variation, puddles/wetness, decals, ground clutter

### Takeaway
Shipped games layer runtime masks over a base terrain blend: RDR2's accumulated mud displacement and TLOU2's per-effect grunge-masked wetness and mud. In UE the tools are height-blended landscape layers, macro variation via large-scale noise, RVT to cache an expensive landscape material, and decal-like meshes (roads, paths) rendered into the RVT.

### Cited Findings
- **RDR2 mud.** Footprints accumulate into a 2048x2048 R16 displacement map, which drives POM on the terrain. — [imgeself](https://imgeself.github.io/posts/2020-06-19-graphics-study-rdr2)
- **TLOU2 wet/mud.** Wetness and mud shaders each carry "its own grunge mask". Wet beaches use a buffer written by a material mod system. Blood pools react to surface height maps and to melting-snow deformation. — [80.lv](https://80.lv/articles/how-naughty-dog-created-the-immersive-world-of-the-last-of-us-part-ii)
- **RVT as a shading cache.** RVT caches shading over large areas. It suits landscape shading that uses decal-like materials and splines that conform to terrain, such as a Landscape spline writing its road material onto the Landscape. Writers should be Static mobility. — [Epic docs: RVT](https://dev.epicgames.com/documentation/en-us/unreal-engine/runtime-virtual-texturing-in-unreal-engine)
- **RVT "Draw in Main Pass = Never".** The component renders only into the RVT, which makes it ideal for decal-style meshes (paths, mud patches, stains). — [Epic docs: RVT](https://dev.epicgames.com/documentation/en-us/unreal-engine/runtime-virtual-texturing-in-unreal-engine)
- **RVT performance controls.**
  - Landscape Virtual Texture Num LODs = 0 renders each component as a single quad, which is optimal.
  - Virtual Texture Min Coverage = 3 culls primitives smaller than about 8 px.
  - YCoCg base colour costs about 25% more memory but reduces banding.
  - Streaming Virtual Textures can bake the low mips.
  - `r.VT.MaxUploadsPerFrame` is 8 in game.
  - Debug with `stat virtualtexturing`. — [Epic docs: RVT](https://dev.epicgames.com/documentation/en-us/unreal-engine/runtime-virtual-texturing-in-unreal-engine)
- **RVT translucent layers.** RVT has no Z-buffer, so stacked decal layers use Translucency Sort Priority (higher draws on top). — [Epic docs: RVT](https://dev.epicgames.com/documentation/en-us/unreal-engine/runtime-virtual-texturing-in-unreal-engine)
- **RVT limitations.** RVT does not support instance culling or LOD selection for Instanced Static Meshes. Virtual textures can't be sampled inside materials that write RVT pages. — [Epic docs: RVT](https://dev.epicgames.com/documentation/en-us/unreal-engine/runtime-virtual-texturing-in-unreal-engine)
- **Triplanar with RVT.** A UE4-era thread reports that triplanar mapping did not work through virtual textures. — [Unreal forums](https://forums.unrealengine.com/t/runtime-virtual-texture-with-landscape/139073)

### Inferences
- **UE 5.3 landscape material** (inferred best practice):
  - 4–6 painted layers (e.g. grass-soil, dirt, mud, rock, forest-litter, corruption), blended with height-lerp (Height Blend layer type).
  - Apply two world-space macro noises (around 20–50 m and around 200 m) to albedo brightness and saturation, which kills tiling.
  - Use distance-based texture scaling to hide repetition.
  - Output into an RVT so the cost is paid once.
  - These are not sourced numbers.
- **Puddles and wetness:** drive them by a painted "wet" layer combined with a height mask (low cavities fill first). Darken albedo, drop roughness toward about 0.05–0.1, and flatten the normal in the puddle centre. This is standard PBR wetness logic, not sourced from the studios here.
- **Ground clutter** (twigs, pebbles, leaves): add it as extra Landscape Grass Type varieties on the forest-litter and dirt layers, with short cull distances (about 15–30 m). For paths and mud patches, use Draw-in-Main-Pass = Never decal meshes in the RVT.

### Gaps
- No primary-source numbers were found for layer counts or texture sizes in shipped terrain materials.
- No official UE puddle or wetness doc was retrieved this pass.

## Blending props into terrain: RVT, pixel depth offset, dithered blends, debris skirts, moss/dirt at contact, grounding shadows/AO

### Takeaway
UE's documented, Blueprint-friendly path is RVT: the prop material samples the landscape RVT and blends toward it near the ground. Add dithered Pixel Depth Offset for soft intersections (needs TAA or TSR), world-aligned top-down moss, and physical debris skirts.

### Cited Findings
- **RVT blend setup:**
  1. Create an RVT asset.
  2. Place an RVT Volume, using Set Bounds to fit the landscape.
  3. The landscape material writes with Runtime Virtual Texture Output.
  4. Other materials read it with Runtime Virtual Texture Sample.
  5. Add the asset to each component's Render to Virtual Textures array.
  - Store normals in world space for better blending across primitives. — [Epic docs: RVT](https://dev.epicgames.com/documentation/en-us/unreal-engine/runtime-virtual-texturing-in-unreal-engine)
- **RVT blend material.** The prop material uses Blend Material Attributes between the landscape-from-RVT attributes and the asset's own material, with an alpha (typically a height gradient above the RVT World Height) controlling the mix. — [Andrew Dowell guide](https://andrewdowell.blogspot.com/2025/02/how-to-blend-assets-with-your-landscape.html); [Unreal forum guide](https://forums.unrealengine.com/t/terrain-mesh-normal-blending-with-virtual-textures-guide/135471). A related video's comments report it working in UE 5.3 — [video](https://www.espinoinsurance.com/video/zqk6PQFCetG/How-To-Blend-Objects-with-a-Landscape-Material-UE5-Runtime-Virtual-Texture-Material-Blending-RVT.html) (low-quality host, treat as weak).
- **PDO dithering.** Pixel Depth Offset dithering gives soft edges where cliffs dither into slope-based terrain. It "only works correctly with TAA enabled". Without TAA you keep the layer blend but lose the soft edge. That article's approach uses Distance Fields for the blend mask. — [Elliot Gray, UE4 terrain blending](https://elliot-gray-m2f9.squarespace.com/blog/ue4-terrain-blending)
- **Distance-field cost.** Mesh Distance Field blending is "super expensive" per a Polycount commenter, who argues the needed data already exists at runtime. — [Polycount](https://polycount.com/discussion/comment/2711697)
- **PDO between props.** PDO blending between two meshes sharing the same temporal dither can cancel out, because both get the same offset on the same pixels. — [Unreal forums](https://forums.unrealengine.com/t/is-there-a-way-to-have-pixel-depth-offset-blend-multiple-non-landscape-meshes-together-using-the-same-material/468004)
- **World-aligned moss on rocks.**
  - Blend moss and rock using world orientation (up vector) as the mask, refined with a mask texture and vertex colour. — [Hauke Thiessen ArtStation](https://haukethiessen.artstation.com/projects/Z2wV8)
  - Use world-aligned textures in both landscape and rock so the projections match at the seam. — [Polycount](https://polycount.com/discussion/comment/2415205)
  - Godfall's environment shaders combine PDO, distance fields and POM to auto-mask where geometry intersects. — [Virtual Vagabond ArtStation](https://virtualvagabond.artstation.com/projects/rAvdZe)
- **Moss shader reference.** The Zero Leagues moss is built on Naughty Dog's Uncharted 4 moss-shader breakdown. — [80.lv Zero Leagues](https://80.lv/articles/breakdown-zero-leagues-in-ue4-sd)
- **No-C++ alternative (untested).** A Blueprint construction script that line-traces from mesh vertices to the terrain to sample height and material. The author presents it as untested. — [Elliot Gray](https://elliot-gray-m2f9.squarespace.com/blog/ue4-terrain-blending)

### Inferences
- **Recommended 5.3 stack, cheapest first:**
  1. Bury props 10–30% into the ground and rotate them to the slope. This is free, and is the core lesson of rock placement.
  2. Add a debris skirt: a ring of Landscape-grass-type pebbles or gravel or a few small rock meshes, plus a grass clump hiding the seam.
  3. Use RVT blend in the prop material, lerping to the landscape over the bottom 20–50 cm.
  4. Add world-aligned top moss, dirt and dust.
  5. Add dithered PDO (UE5 TSR counts as a temporal AA, which is an inference).
  6. For grounding, rely on Lumen or DFAO plus a dark contact decal or RVT "Never" mesh under props for contact darkening.
- Distance fields are needed for Lumen anyway in UE5, so the DistanceToNearestSurface node may be affordable. Measure it. This is an inference, not sourced.

### Gaps
- No primary Epic doc on Pixel Depth Offset blending best practice was retrieved.
- No shipped-game numbers for blend-height distances were found.

## Set dressing and composition: storytelling, clustering, scale variation, avoiding uniform scatter

### Takeaway
Each top studio replaces uniform scatter with rule-driven clusters. Guerrilla uses rule graphs, Epic uses PCG "assemblies", and Naughty Dog justifies every piece by story or ecology ("how did this happen?", "enough sunlight?").

### Cited Findings
- **TLOU2 justification.**
  - Overgrowth is treated as a reclamation process: ask "How did this happen?" before adding plants or damage.
  - Ask whether there is enough sunlight for growth, and whether water could weaken a structure.
  - Every decorative piece in story spaces needs a reason tied to characters. — [80.lv](https://80.lv/articles/how-naughty-dog-created-the-immersive-world-of-the-last-of-us-part-ii)
- **TLOU2 asset tagging.** Library assets were tagged with keywords and previewed before placing. Once Seattle's look-dev was locked, most props and foliage were reused across the landscape. — [80.lv](https://80.lv/articles/how-naughty-dog-created-the-immersive-world-of-the-last-of-us-part-ii)
- **Electric Dreams assemblies.** Pre-composed assemblies are placed by PCG along splines. Cliffs are built from assemblies, and ditch-embankment rules run along splines. — [Epic docs: Electric Dreams](https://dev.epicgames.com/documentation/en-us/unreal-engine/electric-dreams-environment-in-unreal-engine)
- **Guerrilla rule graphs.** Artists author placement rules, not individual placements, so a painted tree line or a moved road re-flows all the dressing. — [Guerrilla Games](https://www.guerrilla-games.com/read/gpu-based-procedural-placement-in-horizon-zero-dawn)
- **GoT clumps.** Noise-driven clumps that share parameters are explicitly used instead of randomness. — [Stylized Station thread](https://threadreaderapp.com/thread/1688939411575119872)

### Inferences
- **Practical rules for a small team** (craft wisdom, unsourced here):
  - Compose in hero, secondary and tertiary scale tiers: one big rock, two medium, several small.
  - Cluster in odd numbers and overlap the pieces.
  - Vary scale with a skewed distribution (many small, few large).
  - Leave negative space and paths.
  - Use 3–5 pre-built Packed Level Actor "assemblies" per biome, rotated and scaled, instead of scattering single props.
  - PCG in 5.3 is usable without C++. A Surface Sampler plus Density Noise plus Self Pruning gives clustering with no overlaps.

### Gaps
- No primary-source composition talk (e.g. a GDC level-art talk) was read this pass.

## Alien and corrupted biomes: how shipped games keep them believable

### Takeaway
Source material here is thin. The one strong principle found is Naughty Dog's: corruption and overgrowth must follow a believable cause and a growth logic (light, water, structure). Horizon's red corruption and Returnal's flora are documented only at a high level, mainly in art books.

### Cited Findings
- **TLOU2 logic for invasive growth.** Nature is in "a war for survival". Overgrowth is reclamation with a cause, and placement is justified by sunlight and water. — [80.lv](https://80.lv/articles/how-naughty-dog-created-the-immersive-world-of-the-last-of-us-part-ii)
- **TLOU2 moss on vehicles.** Overgrowth is applied as a material state on reused vehicles. — [Trevelyan ArtStation](https://trevelyan.artstation.com/projects/XngOra)
- **Horizon Forbidden West.** The story features a spreading red blight that kills wildlife. No art-direction detail on its flora was found. *The Art of Horizon Forbidden West* (Dark Horse) contains environment concept art with commentary. — [Dark Horse](https://www.darkhorse.com/newsfeed/return-horizon-art-horizon-forbidden-west-dark-hor)
- **Returnal.** Atropos has deserts, frozen wastes and caves with new flora and fauna species. A review notes the alien flora reacts to the player and follows her movements. The look draws on classic sci-fi films such as *Alien*. The style only came together after art director Ilmari Kumpunen joined (GDC 2022 talk summary). — [PlayStation](https://www.playstation.com/es-es/editorial/everything-you-need-to-know-about-returnal/); [GIGA](https://www.giga.de/test/returnal-im-test-und-taeglich-gruesst-das-alien/); [Game Developer](https://www.gamedeveloper.com/marketing/a-third-person-action-roguelike-bullet-hell-arcade-thriller-the-making-of-returnal)

### Inferences
These are craft inferences that apply the sourced principles above. They are not studio-sourced.
- **Spread corruption like a real organism or infection.** Use a gradient from an epicentre (nest or tentacle core) outward, not a hard border. Drive it with one painted "corruption" landscape layer that does four things:
  - blends the ground material;
  - swaps the Landscape Grass Type to alien flora;
  - desaturates or kills normal grass at the fringe;
  - feeds a material parameter on props (RVT-sampled corruption mask, so props near corruption get veins or creep).
- **Keep real-world rules.** Corrupted flora still obeys gravity, light and clumping. Use the same GoT-style clump noise and wind layers, but change the wind's frequency or phase (slow pulsing instead of gusts) so it reads "alive and wrong".
- **Keep one grounding anchor.** Keep realistic base materials (soil, rock, Megascans) and change only hue, emissive accents and silhouette. Photoreal PBR values keep the stylised flora believable.
- **Use story logic like TLOU2.** Tentacles grow from cracks, water and dark spaces. Dead normal vegetation sits at the infection front. Remains of what it consumed (props half-swallowed via RVT blend plus PDO) show the cause.

### Gaps
- No primary sources were found on art direction for:
  - Horizon's corruption flora;
  - TLOU cordyceps environment growth (the show's VFX vendor DNEG has a write-up, not read: [DNEG](https://www.dneg.com/news/welcome-to-seattle-explore-our-emmy-nominated-work-on-the-last-of-us-season));
  - Prey's Typhon coral;
  - Annihilation-style shimmer.
- Next steps for these: the art books (*Art of Returnal*, *Art of Horizon Forbidden West*), and GDC talks by Roland Ijzermans (Horizon environments) and Housemarque (GDC 2022).
