# Geometry and Baking for Photoreal Game Props

Research note. The Polycount wiki (Texture_Baking, TexelDensity) refused connections during this session (ECONNREFUSED), and the Adobe Substance bake docs returned 403/404. The Frostbite/EA photogrammetry article also returned 404. Primary sources reached: Marmoset Toolbag baking docs, Epic Nanite docs (current page is the UE 5.8 version), Beyond Extent (Playground Games artist), Maxon texel density docs, 80.lv articles, Naughty Dog artist ArtStation/80.lv. Many studio-specific numbers asked for could not be found and are listed under Gaps.

## Shape language, silhouette, bevels, edge highlights and imperfection

### Takeaway
No source found gave studio-specific bevel widths or a primary/secondary/tertiary recipe from Naughty Dog, Rockstar, Guerrilla, Sucker Punch or id. The reliable, sourced rules are: real edges are rounded, so every visible edge needs a bevel (modeled, baked or shader-faked). Bevels must be large enough to cover more than one texel at the target density, and checked at gameplay camera distance. Naughty Dog has moved small props toward baked-bevel trims on hard 90-degree geometry to save texture memory and polygons.

### Cited Findings
- Normal maps record direction, not depth. Parallel faces record nothing, so add slopes or bevels. Details smaller than one pixel are lost, so keep bevels at a consistent minimum size. — [Marmoset Toolbag baking docs](https://marmoset.co/posts/toolbag-baking-tutorial/)
- Give curved surfaces enough sides. This fixes silhouette waviness more reliably than bevels alone. — [Marmoset](https://marmoset.co/posts/toolbag-baking-tutorial/)
- Bevel shading works because "the edges of real-world objects tend to be chamfered or rounded over." — [80.lv, Marmoset Toolbag 5 bevel shader](https://80.lv/articles/learn-how-marmoset-toolbag-5-s-bevel-shader-can-boost-your-workflow)
- Very tight bevels look clean up close but break realism at normal in-game camera distance. The artist zooms out to check edges at gameplay scale. — [80.lv prop breakdowns, via search summary](https://80.lv/articles/props) (individual article not pinned; treat as practitioner opinion)
- A radio prop breakdown set bevel width per material, so bevels were not one global value. — [80.lv radio receiver](https://80.lv/articles/prop-art-tips-creating-a-realistic-radio-receiver-in-blender-marmoset-toolbag)
- Edge wear technique: a brighter, rougher edge layer, plus dirt-map grunge with cloudy breakup so the surface does not look flat. — [80.lv aiming laser breakdown](https://80.lv/articles/breakdown-modeling-texturing-realistic-aiming-laser-with-substance-3d)
- Naughty Dog (Matthew Trevelyan Johns, TLOU Part I/II): small unique props were using up texture memory. He proposed baked-bevel trims to replace one-off baked assets. Models need hard edges and 90-degree angles for the trims to work, so artists model fewer bevels and save polygons. — [Trevelyan ArtStation](https://trevelyan.artstation.com/projects/qQGK6y); [80.lv summary](https://80.lv/articles/the-last-of-us-remake-s-trim-pipeline-in-substance-3d-explained)
- In a Naughty Dog interview, an artist said weapon wear, chips and dents are sculpted in ZBrush where real wear would occur. Texturing is done in Substance Painter, and each artist has their own approach. — [80.lv, Naughty Dog TLOU2 world](https://80.lv/articles/how-naughty-dog-created-the-immersive-world-of-the-last-of-us-part-ii/)
- An AAA outsourcer (Kevuru Games) blocks the silhouette first, uses SubD for organic hard surfaces (car body) and CAD-style tools (Fusion) for mechanical parts, and works from "hundreds of references." Vehicles and weapons aim for "100% similarity" to the real object. — [80.lv Kevuru](https://80.lv/articles/mastering-realism-how-to-create-props-environments-for-aaa-games)

### Inferences
- For numpy-generated meshes, compute bevel radius from texel density, not as a fixed mm value. At 1024 px/m one texel is about 1 mm, so a bevel needs at least about 2–3 mm (2–3 texels) to bake and survive mips. At 512 px/m it needs at least about 4–6 mm. This follows from Marmoset's "sub-pixel detail is lost" rule.
- Imperfection (warp, sag, asymmetry) is not covered by any primary source found. Common practice is to apply low-frequency displacement to vertices before baking, so silhouettes are not perfectly straight. Then add mid-frequency dents along edges and high-frequency wear only in the textures. This is common practice, not a sourced figure.
- With Nanite, a modeled bevel costs triangles but no texture memory. Without Nanite, the Naughty Dog trim approach (hard 90-degree low poly plus baked-bevel trim) is the memory-cheap choice.

### Gaps
- No public bevel widths (mm), and no primary/secondary/tertiary form guidelines, from Naughty Dog, Rockstar, Guerrilla, Sucker Punch or id were found. Polycount wiki was unreachable.
- No primary source found on deliberate asymmetry, sag or warp in AAA props.

## Texel density standards, hero vs background, mips/streaming

### Takeaway
Commonly cited references are 10.24 px/cm (1024 px/m) for first person, 5.12 px/cm (512 px/m) for third person and 2.56 px/cm (256 px/m) for top-down. These are tool-vendor and forum examples, not published studio standards. Hero or inspectable items (first-person weapons, cinematics, menu objects) deliberately go above the baseline.

### Cited Findings
- Maxon (Cinema 4D docs) gives example values: first person e.g. 10.24 px/cm, third person e.g. 5.12, top-down e.g. 2.56 or less. The closer the camera, the higher the density. — [Maxon C4D Texel Density](https://help.maxon.net/c4d/en-us/Content/html/Texel_Density.html)
- A Polycount commenter says most modern games target 10.24–20.48 px/cm (about 1024–2048 px/m). Forum opinion only. — [Polycount discussion](https://polycount.com/discussion/237560/textel-density-problem-please-help-me-solving-and-understanding-this-problem)
- A practitioner blog says AAA first-person hero weapons can be 20+ px/cm while background architecture sits at about 5. Third-person props are about 4.5–6.0 px/cm. — [Stefan Groenewoud blog](https://stefangroenewoud.artstation.com/blog?page=2) (secondary, via search summary)
- Beyond Extent (Playground Games artist): first person has the highest density, third person slightly lower with more budget moved to asset density, top-down lowest. Exceptions are first-person weapons, cinematic assets, inspectable or menu objects, and navigation landmarks. The definition example is 2.56 px/cm = 256 px/m. About 20.48 px/cm is "more than enough" for portfolio work. Trim UV islands are usually scaled no more than about ±25%, to keep density consistent. — [Beyond Extent texel density deep dive](https://www.beyondextent.com/deep-dives/deepdive-texeldensity)
- Beyond Extent does not discuss streaming. Mips are mentioned only as an automatic engine optimization. — [Beyond Extent](https://www.beyondextent.com/deep-dives/deepdive-texeldensity)
- Marmoset: hard edges at UV seams hold up better at lower resolutions, mip levels and LODs. — [Marmoset](https://marmoset.co/posts/toolbag-baking-tutorial/)

### Inferences
- Suggested targets: 1024 px/m for props seen close in first person, 2048 px/m for hand-held or hero items, and 512 px/m for third-person or background. Set one density per project and derive texture size from it (asset surface area × density², rounded to a power of two), not the other way round.
- Padding must grow with mip count. A 4K map viewed at mip 3 has islands 8× smaller, so islands need wider margins (see the baking section).

### Gaps
- No published px/m standard from a named AAA studio was found.
- No primary source found on UE5 texture streaming pool or mip bias guidance for props.

## Baking best practice: cage, skew, normals, tangent space, AO, padding, UVs, artifacts

### Takeaway
Use a triangulated low poly, split UVs at every hard edge, and use a smoothed (averaged) cage just large enough to enclose the high poly. Bake in MikkTSpace and import normals (not recompute) into UE. Use DirectX green (Y−) for Unreal. Bake 16-bit, then convert or dither to 8-bit. Use AO at 256+ rays (512+ final). Generous padding.

### Cited Findings
- Cage: keep it just large enough to reach the high poly's highest points. Oversized cages cause errors on overlapping or tight-cornered meshes. Use Estimate Offset as a starting point. Set Min/Max offset so the high poly sits inside the range; the offset map starts at 50% gray. — [Marmoset](https://marmoset.co/posts/toolbag-baking-tutorial/)
- Smoothed (averaged) cages are recommended for most work because they avoid gaps at hard edges. Unsmoothed cages can reduce skew but cause seams at hard edges. — [Marmoset](https://marmoset.co/posts/toolbag-baking-tutorial/)
- Skew painting: black applies full skew correction, white none. It fixes off-axis projection errors. Offset and skew maps are fixed 512×512. Cage and skew settings are per bake group. — [Marmoset](https://marmoset.co/posts/toolbag-baking-tutorial/)
- Split UVs along every hard edge, or faces bake onto the edge and create seam artifacts. Keep the low poly close in size to the high poly. Cap holes in the high poly, or model them into the low poly. — [Marmoset](https://marmoset.co/posts/toolbag-baking-tutorial/)
- Triangulate before export. Quads and n-gons triangulate differently between apps and cause X-shaped smoothing errors. Lock normals before triangulating (Maya). — [Marmoset](https://marmoset.co/posts/toolbag-baking-tutorial/)
- Tangent space: bake with the renderer's tangent space. Mikk/xNormal is the usual choice for Unity and Unreal. Y+ (OpenGL) vs Y− (DirectX) mismatch is a common error; use Flip Y if needed. — [Marmoset](https://marmoset.co/posts/toolbag-baking-tutorial/)
- UE side: the MikkTSpace workflow expects mesh normals imported from the file, with tangents computed by MikkTSpace. Set the Normal Import Method to Import Normals, because the default is Compute Normals. Degenerate-tangent warnings usually come from UVs badly laid out for MikkTSpace. Mostly UE4-era forum sources; verify labels in 5.3. — [Polycount comment](https://polycount.com/discussion/comment/2419487); [Polycount comment](https://polycount.com/discussion/comment/2201682); [UE AnswerHub](https://answers.unrealengine.com/questions/391330/view.html)
- Bit depth: 8-bit normals band. Dithering (on by default) removes banding at the cost of slight noise. 16-bit normals bake smoother; convert at the final stage if the renderer needs 8-bit. Maximum output is 8192×8192. — [Marmoset](https://marmoset.co/posts/toolbag-baking-tutorial/)
- AO: 256 rays is medium (default), 512+ is high, under 256 is for tests. Two-sided AO helps intersections but can shadow floaters; bake both and composite. Ignore Groups grounds parts; Floor Occlusion adds directional AO for static objects. — [Marmoset](https://marmoset.co/posts/toolbag-baking-tutorial/)
- Padding: Marmoset presets have no pixel value. "Moderate" suits most uses; "extreme" fills most empty UV space. — [Marmoset](https://marmoset.co/posts/toolbag-baking-tutorial/)
- Naming: `_high`/`_low` suffixes group meshes (e.g. `Myobject1_high_bolt` joins group `Myobject1`). Exploding by groups prevents parts baking onto each other. Floaters distort height and position outputs. — [Marmoset](https://marmoset.co/posts/toolbag-baking-tutorial/)

### Inferences
- For a Blender pipeline: Blender's own normal bake uses MikkTSpace tangents, so it matches UE when the FBX exports normals (and optionally tangents) from the same triangulated mesh and UE imports normals rather than recomputing them. The bake must use the exact mesh that ships: triangulate before baking.
- Blender exports OpenGL (Y+) normal maps. UE expects DirectX (Y−), so flip green on export, or tick "Flip Green Channel" on the UE texture asset.
- Widely used padding numbers (not sourced here): 8–16 px at 2K and 16–32 px at 4K, with island spacing of about twice the padding. Blender's bake "Margin" (Extend) should be set to match.
- Cheap automatic artifact checks for a procedural pipeline: (1) the ray-miss mask (Blender bakes misses as the background colour; count those pixels), (2) a normal-map deviation check (pixels far from (0.5, 0.5, 1) on flat areas indicate cage or skew error), (3) a seam check (render the asset in UE under a grazing directional light and look for lines on UV seams), (4) a mip test (view at mip 2–3 to find islands bleeding into each other).
- Mirrored or overlapping UVs: move overlapping copies out of 0–1 by a whole UV unit during the bake, so only one copy receives rays. MikkTSpace handles mirrored tangents correctly when the same mesh is used everywhere. Not confirmed by a source this session.

### Gaps
- No source found giving a numeric cage distance as a % of object size (e.g. Substance "Max frontal distance" defaults). Adobe docs returned 403/404.
- No source this session on mirroring/overlap rules or a numeric padding standard.
- Current UE 5.3 Static Mesh build setting names ("Use MikkTSpace Tangent Space", "Recompute Tangents") were not verified from Epic docs.

## Nanite / high poly counts: does the advice change?

### Takeaway
Epic's docs recommend modeling detail as geometry instead of baking it into normal maps when using Nanite. Nanite draws the source triangles up close, and its data is highly compressed and streamed. Caveats: Nanite has no per-vertex tangents (derived per pixel, so possible edge discontinuities), supports only opaque/masked materials, and has a fallback mesh for ray tracing.

### Cited Findings
- "Use high-poly detailing rather than baking detail into normal map textures" is listed as a Nanite benefit. — [Epic Nanite docs](https://dev.epicgames.com/documentation/en-us/unreal-engine/nanite-virtualized-geometry-in-unreal-engine)
- Up close, Nanite draws the original source triangles. Good candidates are meshes with many triangles, triangles that are tiny on screen, or many instances. The scene limit is 16 million instances. Triangles per mesh and performance "should be carefully measured." — [Epic Nanite docs](https://dev.epicgames.com/documentation/en-us/unreal-engine/nanite-virtualized-geometry-in-unreal-engine)
- Nanite stores no per-vertex tangents. Tangent space is derived in the pixel shader, which "could cause discontinuities at edges"; Epic says this has not been significant so far. — [Epic Nanite docs](https://dev.epicgames.com/documentation/en-us/unreal-engine/nanite-virtualized-geometry-in-unreal-engine)
- Only Opaque and Masked blend modes are supported; translucent mesh decals are not. Nanite data is "highly compressed and supports fine-grained streaming." Disable Generate Lightmap UVs on dense meshes without baked lighting, because it adds a large UV channel. Nanite build time rises a lot for dense meshes. — [Epic Nanite docs](https://dev.epicgames.com/documentation/en-us/unreal-engine/nanite-virtualized-geometry-in-unreal-engine)
- The fallback mesh is used for ray tracing by default. Lower Fallback Relative Error to use more source triangles. — [Epic Nanite docs](https://dev.epicgames.com/documentation/en-us/unreal-engine/nanite-virtualized-geometry-in-unreal-engine)
- Note: the fetched docs page is for UE 5.8 and has no 5.3-specific notes.

### Inferences
- For a procedural team on UE 5.3: with Nanite, generate primary and secondary forms (and bevels of about 2 mm or more) as real geometry. Keep normal maps for tertiary, sub-millimetre detail (scratches, grain, pores), using tileable or detail normals rather than a full high-to-low bake. This removes most cage, skew and seam issues.
- Still bake AO and curvature, from the dense mesh to its own UVs, to drive procedural wear masks. Nanite does not remove the need for those masks.
- Keep a non-Nanite low poly plus baked normal path for anything translucent, skinned (Nanite skeletal support did not exist in 5.3) or needing mobile/VR.

### Gaps
- Epic's docs page fetched no longer shows the disk-size comparison (Nanite mesh vs low poly + normal map). No figure was verified.
- No source on recommended triangle densities for Nanite props.

## Scan vs procedural, and how procedural-only teams approach scan realism

### Takeaway
DICE (Star Wars Battlefront, GDC 2016) treated photogrammetry as one tool serving an art direction, not a magic bullet. A summary of that talk reports about 50% faster asset creation at first, with about 70% expected later. Scan processing means delighting and making textures tileable. No primary source was found on studios mixing Megascans with procedural work, or on procedural-only techniques.

### Cited Findings
- DICE's Kenneth Brown and Andrew Hamilton presented "Photogrammetry and Star Wars Battlefront" at GDC 2016, framed as practical. They called photogrammetry a tool, not a magic bullet. — [Game Developer GDC coverage](https://www.gamedeveloper.com/art/gdc-see-how-dice-used-photogrammetry-to-bring-i-star-wars-battlefront-i-to-life); [GDC Vault session](https://www.gdcvault.com/play/1022981/contactUs)
- A summary of the talk reports about 50% faster asset creation in the first generation, with about 70% expected after refinement. Secondary source; the primary Frostbite article now 404s. — [Medium summary](https://medium.com/@homicidalnacho/a-look-into-photogrammetry-and-video-games-71d602f51c31)
- A practitioner write-up on scan-to-game textures covers delighting and making scanned textures tileable. — [Game Developer photogrammetry workflows](https://gamedeveloper.com/art/the-workflows-of-creating-game-ready-textures-and-assets-using-photogrammetry)
- NVIDIA GDC 2017 photogrammetry pipeline deck exists (not read). — [NVIDIA GDC17 PDF](https://developer.download.nvidia.com/assets/gameworks/downloads/regular/GDC17/gdc-photogrammetry-pipelines-2017-03-01.pdf)

### Inferences
- For a procedural-only team, these practices are standard but were not sourced this session:
  - Calibrate albedo to measured ranges (e.g. no non-metal albedo below about 30–50 sRGB or above about 240).
  - Drive wear, dirt and colour shifts from baked curvature, AO and world-space position, so noise follows the form.
  - Layer noise at 3+ frequencies with scale tied to real-world size.
  - Compare against reference photos under the same light. Use Megascans surfaces as calibration references even if not shipping them.

### Gaps
- No primary source found on Naughty Dog, Rockstar, Guerrilla or Sucker Punch scan-plus-procedural pipelines.
- No primary measured-albedo source was retrieved in this session.

## Trim sheets, tileables plus unique bakes: when each is used

### Takeaway
Unique 1:1 bakes cost the most texture memory and are kept for hero items. Naughty Dog moved many small props to a shared baked-bevel trim layout to free texture memory. Trims require hard-edged, 90-degree geometry, and UV islands should only be scaled about ±25% to keep density.

### Cited Findings
- Naughty Dog's baked-bevel trims freed texture memory and reduced the number of uniquely baked props, as well as older trims that did not follow a shared layout. Goals: one shared trim layout for the whole team, a replacement for many unique 1:1 baked assets, and documented Substance Designer templates and examples. The method "has since evolved." — [80.lv TLOU trim pipeline](https://80.lv/articles/the-last-of-us-remake-s-trim-pipeline-in-substance-3d-explained); [Trevelyan ArtStation](https://trevelyan.artstation.com/projects/qQGK6y)
- Trim geometry needs hard edges and 90-degree angles so the baked-bevel trims work, which means fewer modeled bevels and fewer polygons. — [Trevelyan via search summary](https://trevelyan.artstation.com/projects/qQGK6y)
- Trim UV island scaling is usually limited to about ±25%. — [Beyond Extent](https://www.beyondextent.com/deep-dives/deepdive-texeldensity)
- Kevuru (AAA outsourcer) used Substance Painter unique textures for small parts and interiors, and an in-engine custom UE5 shader for the large car body. Environment work lists "Trim/Atlas Materials" as a separate task. — [80.lv Kevuru](https://80.lv/articles/mastering-realism-how-to-create-props-environments-for-aaa-games)

### Inferences
- Rule of thumb for a small team:
  - Unique bake for hero or inspectable props and anything with unique silhouette detail.
  - Trims for architecture and modular or repeated props.
  - Large surfaces: tileables plus a low-resolution unique mask (AO, curvature, dirt) blended in a UE master material (vertex colour or a second UV).
- A procedural mesh generator can emit trim-aligned UVs automatically, because it knows which edges are bevels.

### Gaps
- Trim sheet dimensions, strip heights, bevel widths in trims and density figures from Naughty Dog were not in the accessible text. They may be in images on the ArtStation page.
