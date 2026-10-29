# Industry secrets: realism research round 2 (2026-10-30)

Written by `hossam gmail (Claude)` (cloud session) for the owner. It covers about an hour of research in four parallel
tracks:

- materials
- lighting and camera
- characters and motion
- VFX, environment and medieval authenticity

It fills the gaps the first round listed in `research_notes/*` → "Gaps". It does not repeat the playbook.

**Owner's rule, 2026-10-30:** this file is part of the realism knowledge base. Every agent reads it together with the
[playbook](Photoreal%20game%20asset%20playbook.md) and the [STANDARD](../laptop2-realism/STANDARD.md) before visual work,
and applies the rules that fit the card. Items marked **[UNVERIFIED]** are single-source claims or inferences. Test them
in lookdev before you trust them, then log the result in `KNOWLEDGE_LOG.md`.

---

## 0. The 10 rules (TLDR, apply on every visual card)

1. **Calibrate, then judge only under the locked grey ball.** Correct values matter more than detail.
2. **Roughness carries the realism.** It is never flat. Use Composite Texture (§1.3) to stop distant sparkle.
3. **Every dirt layer has a physical cause** (edge, cavity, gravity, sun, water). There is no global grunge.
4. **Castles were whitewashed.** Use limewash outside and false-ashlar red lines inside (§4.5). Bare grey stone is the
   exception, not the rule.
5. **Light like Naughty Dog.** Use one key light first, rim-light the enemies, and light the path (§2.5).
6. **Torches are 1700–1900 K.** Flicker is a slow drift plus an 8–10 Hz component. There is a real light behind every
   flame.
7. **A perfect camera reads as CG.** Add subtle motion blur, local exposure, light lens artefacts, and `r.Tonemapper.Sharpen
   0.5`.
8. **Motion is the biggest tell.** That means:
   - root motion
   - the ±15–20 % play-rate rule
   - orientation and stride warping
   - physics-blended hit reactions
   - variation for every zombie
9. **Do gore without C++.** Use sphere-mask wounds on Pre-Skinned Local Position, plus cap-mesh dismemberment.
10. **Coherence:** one wind field, one shared dirt pass and one exposure per zone. Real means everything agrees with
    everything else.

---

## 1. Materials

### 1.1 Measured values (linear 0–1 unless marked sRGB; R = UE roughness)

The main source is [physicallybased.info](https://physicallybased.info), whose full JSON is on
[GitHub](https://raw.githubusercontent.com/AntonPalmqvist/physically-based-api/main/deploy/v2/materials.json).
Roughness values from [Roblox's material reference](https://create.roblox.com/docs/art/modeling/material-reference) are
marked "Roblox".

| Material | Albedo | Roughness |
|---|---|---|
| Weathered wood | 0.12–0.16 (≈100 sRGB) | 0.7–0.9 |
| Fresh wood | 0.35–0.42 | 0.2–0.3 varnished |
| Iron | 0.53–0.58 (≈195 sRGB), metallic 1 | polished 0, worn 0.2–0.4 |
| Rust | 0.18, 0.057, 0.017 (sRGB 118,68,35), **metallic 0** | **1.0** |
| Gold | 1.0, 0.77, 0.34 | 0–0.3 |
| Copper | 0.96, 0.64, 0.54 | |
| Brass (stand-in for bronze) [UNVERIFIED] | 0.91, 0.78, 0.42 | |
| Brick | 0.26, 0.10, 0.06 | 0.5–1.0 |
| Plaster or limewash | 0.40–0.45 (never 255 white) | |
| Soil, dry then wet | 0.15, then 0.08 (wet is about half) | |
| Sand, dry then wet | 0.40, then 0.23 | 1.0 |
| Grass | 0.105, 0.133, 0.041 | 0.5 |
| Bone | 0.79, 0.79, 0.66 | 0.5–0.9 |
| Fresh blood | 0.64, 0.003, 0.005 | about 0 (wet) |
| Deoxygenated blood | 0.42, 0, 0 | rougher as it dries [UNVERIFIED] |
| Charcoal | 0.02 | 1.0 |
| Wool or cotton | dark dyes 41–73 sRGB | **0.8–0.96** |
| Fur | | 0.65–0.75 (Roblox) |
| Skin, Fitzpatrick type I | 0.85, 0.64, 0.55 | 0.4–0.65 |
| Skin, Fitzpatrick type VI | 0.09, 0.05, 0.02 | 0.4–0.65 |

Specular values: **skin is 0.35, not 0.5.** Water is 0.255, ice 0.224 and quartz 0.570
([Epic](https://dev.epicgames.com/documentation/en-us/unreal-engine/physically-based-materials-in-unreal-engine)).

Bark, moss, straw, limestone, bronze, dried blood and mid-tone leather have no free measured source. The best paid source
is Grzegorz Baran's *PBR Color Reference List*: about 600 spectrometer-measured materials for about $25
([CGChannel](https://www.cgchannel.com/2026/01/this-25-pdf-lists-the-pbr-values-for-600-real-world-materials/)).

### 1.2 Corrections to our current gates

- **Dark floor.** Measured dyed or manufactured blacks go below 50 sRGB: black leather 35, dyed cotton 41–44, black
  painted wood 42 ([Unity dark dielectrics PDF](https://docs-alpha.unity3d.com/cn/2018.1/uploads/ExpertGuides/Dark_Dielectric_Materials.pdf)).
  - Keep 30 as the hard floor.
  - For **natural** materials (wood, stone, soil), warn below 50–60 sRGB. Shinsoj's chart puts non-metals at about
    60–240 ([Shinsoj](https://shinsoj.artstation.com/blog/Q9j6/pbr-color-space-conversion-and-albedo-chart)).
- **Saturation ceiling [inference from the measured table].** Natural materials sit at about **30–55 % HSV saturation**:
  grass 44 %, mud 42 %, skin 31 %, wood 56 %. Rust at about 70 % is the high outlier. **Candidate `pbr_check` gate:**
  warn above 60 % mean saturation unless the material is rust or dye.
- **Metallic in-between values** are valid only for dust or dirt over metal
  ([Unity](https://docs.unity3d.com/2018.3/Documentation/Manual/BestPracticeMakingBelievableVisuals5.html)).

### 1.3 Tricks

1. **Composite Texture, which kills specular sparkle.** It is a hidden UE texture feature
   ([UE docs](https://docs.unrealengine.com/4.26/en-US/RenderingAndGraphics/Textures/Composite)). Setup on the ORM
   texture:
   - Composite Texture = the normal map
   - Composite Texture Mode = Green (roughness)
   - Power 1
   - Both maps must share UVs.
   UE then adds the normal variance lost at each mip into roughness (the Toksvig idea). Distant surfaces stop sparkling
   and stop looking plastic.
2. **Wetness, Naughty Dog style (Uncharted 4).**
   - The colour is `lerp(base, base², porosity × wetness)`. Squaring darkens mid-tones most, which is physically right.
   - Above 98 % wet, force the normal to straight up so puddles read flat.
   - Clay is the most porous material, at about 50–70 %.
   Sources: [ND 2016 tech art](https://advances.realtimerendering.com/other/2016/naughty_dog/NaughtyDog_TechArt_Final.pdf),
   [DONTNOD chart](https://seblagarde.wordpress.com/2014/04/14/dontnod-physically-based-rendering-chart-for-unreal-engine-4/).
   - When surfaces dry, **the shine goes before the darkening** ([fxguide / Lagarde](https://www.fxguide.com/?p=43362)).
3. **Moss (Uncharted 4).** Same source as above.
   - Light wrap with a tint, plus a fuzz layer.
   - AO fades to white at grazing angles.
   - Some colour is added back where AO is very dark, so moss never goes black.
4. **Layer logic (TLOU2 vehicles).** About 8 layers per shader. Moss sits on up-facing and occluded areas with a dirt
   layer under it, and **rust is masked out where moss sits**, which also saves texture samples
   ([Trevelyan](https://trevelyan.artstation.com/projects/XngOra)).
5. **Cloth.**
   - Use the Cloth shading model with Cloth = 1 and a Fuzz Color.
   - Sheen is about the base colour's luminance for ordinary cloth. Velvet has a dark base and a bright sheen
     ([Filament](https://google.github.io/filament/main/materials.html)).
   - Wool roughness is 0.8–0.96.
   - Ghost of Tsushima fuzz: fibre albedo 5× Lambert, density 0.5, spread 0.9, wrap 0.2
     ([Patry 2020](https://blog.selfshadow.com/publications/s2020-shading-course/patry/slides/)).
6. **Mip sharpening.** Use Mip Gen **Sharpen4** on colour textures. Above 6 you get halos. **Never sharpen normal maps.**
7. **Fix values at import without a rebake.** Texture Adjustments (Brightness, Saturation, Vibrance, RGBCurve) apply at
   compression time ([UE texture properties](https://docs.unrealengine.com/4.26/RenderingAndGraphics/Textures/Properties)).
   This is the in-engine version of the ×2.1 bark lift.
8. **Compression.**
   - Normal maps: BC5.
   - ORM: "Masks (no sRGB)".
   - Single-channel maps: BC4 (Alpha).
9. **Brushed metal.** Set the project setting "Use anisotropic BRDF", which adds Anisotropy (−1..1) and Tangent inputs.
   Directional and rect lights fall back to isotropic. It may not work on Nanite (UE-203751) [UNVERIFIED].
10. **Virtual textures** cost at least 2 fetches per sample. Use them only for big textures; normal streaming is cheaper
    ([UE SVT](https://dev.epicgames.com/documentation/en-us/unreal-engine/streaming-virtual-texturing-in-unreal-engine)).
11. **Blender procedural damage starting values**
    ([StraySpark](https://www.strayspark.studio/blog/procedural-damage-game-assets-complete-workflow)):
    - pointiness above 0.5 is convex edges, below 0.5 is crevices
    - up-facing mask: Z above 0.7
    - breakup noise: scale 200, detail 6

---

## 2. Lighting and camera

### 2.1 Real numbers

- **Sun** is 120,000 lux at zenith with an angular size of 0.545°. **Moon** is **0.26 lux** with an angular size of
  0.568°. Set the moon light's Atmosphere Sun Light Index to 1
  ([Epic Sky Atmosphere](https://dev.epicgames.com/documentation/en-us/unreal-engine/sky-atmosphere-component-in-unreal-engine)).
- **Electric Dreams (Epic demo, from EXIF data).** Source: [Magnopus](https://www.magnopus.com/blog/lighting-in-unreal-with-photography-principles).
  - Sun 100k lux, scene about 9.5 EV100.
  - Grade: Film Toe 0.55 → 0.38 (lifts the shadows), contrast via Slope, saturation 1.1.
  - Local Exposure, not the shoulder, saves the highlights.
  - The Quixel demo locked EV100 at 13.
- **Key-to-shade ratios:** 4:1 by day (midday can reach 16:1), 3:1 at sunset, 2:1 overcast.
- **Kelvin** ([Wikipedia](https://en.wikipedia.org/wiki/Color_temperature)):

  | Source | Temperature |
  |---|---|
  | Match | 1700 K |
  | Candle or sunset | 1850 K |
  | Household bulb | 2400 K |
  | Tungsten | 3200 K |
  | Overcast | 6500 K |
  | Clear blue sky | 15–27k K |

  **Torch: 1700–1900 K.**
- **Moonlight is not physically blue.** A camera records it at about 4000 K. It looks blue because of the Purkinje shift
  in our night vision. Ghost of Tsushima simulated that shift
  ([Patry 2021](https://www.advances.realtimerendering.com/s2021/jpatry_advances2021/index.html)). A blue moon is a
  stylistic choice, so make it on purpose.
- **Flicker.** Measured flames flicker at about 8–12 Hz, and bigger fires flicker slower: f ≈ 1.5/√D, with D the burner
  diameter in metres ([arXiv](https://ar5iv.labs.arxiv.org/html/2207.02019)).
  - Torch [inference]: a slow random drift plus an 8–10 Hz component.
  - A single sine wave reads fake.
- **Units.** 1000 cd gives 1000 lux at 1 m, and 1 cd ≈ 12.6 lm for a point light. There is no measured candela figure
  for a wooden torch, so tune it in lookdev.

### 2.2 Soft shadows

Softness comes only from **Source Angle and Source Radius**. The default sun angle is 0.5357° and is correct.
**Source Radius 0 on point lights gives razor-sharp CG shadows**, so give torches a radius.

### 2.3 Camera realism

Why bodycam and Unrecord look real
([80.lv](https://80.lv/articles/developing-a-game-with-realistic-graphics-in-unreal-engine/),
[Creative Bloq](https://www.creativebloq.com/news/unrecord-is-an-optical-illusion)):

- slow shutter, so constant motion blur
- blown highlights
- a chest-height camera that sways separately from the arms
- fisheye distortion
- chromatic aberration, noise and compression
- A real bodycam has about 118° horizontal FOV.

**The lesson: a perfect camera is a CG tell.**

UE settings:

- **Motion blur** Amount 0.5 ≈ 180° shutter [UNVERIFIED]. Target FPS 0 ties the blur to the real frame rate.
- **Panini projection:** `r.LensDistortion.Panini.D` > 0 fixes stretched edges at wide FOV.
- **Sharpening:** TSR has no sharpening of its own. Fortnite uses `r.Tonemapper.Sharpen 0.5`
  ([Epic TSR FAQ](https://dev.epicgames.com/documentation/en-us/unreal-engine/temporal-super-resolution-frequently-asked-questions-for-unreal-engine)).
- **Has Pixel Animation:** tick it on fire and animated materials. It stops TSR ghosting.
- **Bloom:** Standard bloom for games; Convolution is for cinematics. A lens-dirt mask with chromatic aberration baked in
  looks real.

### 2.4 Hidden UE 5.3 settings

- **Local Exposure:** Highlight and Shadow Contrast Scale 0.6–1.0, Blurred Luminance Blend 0.4–0.6. The Exposure
  Compensation Curve corrects day and night automatically.
- **Sky:**
  - Mie anisotropy 0.9 gives a tighter sun halo (the default is 0.8).
  - Turn on "Support Sky Atmosphere Affecting Height Fog" with the fog's inscattering colours set to black.
  - Cloud shadows are set on the directional light.
- **Volumetric fog:**
  - Scattering Distribution about 0.9 with low density gives shafts without milk.
  - Use 4 fog layers: height fog, fog cards, local fog volumes, volumetric fog.
  - Lit fog is tinted orange and shadowed fog blue.
  - Source: [Magnopus fog](https://www.magnopus.com/blog/mastering-fog-four-levels-of-fog-in-unreal-engine).
- **VSM:** swaying WPO (banners, flags, foliage) re-renders shadows every frame. Set a **WPO Disable Distance**. Each −1 on
  `r.Shadow.Virtual.ResolutionLodBiasDirectional` doubles shadow resolution.
- **Lumen:**
  - Diffuse Color Boost stays below 2.
  - Raise Max Lumen Mesh Cards above 12 for complex castle rooms.
  - Overbright environment albedo makes characters look **oily** under Lumen.
- **Why games look "Unreal-y"** [community, UNVERIFIED]:
  - the default motion blur
  - an untouched post-process
  - Lumen shimmer
  - roughness at 0 or 1 (keep it about 0.05–0.85)
  - stock Megascans assets
- **Far Cry 3** calibrated albedo to a colour chart. Albedo that is too dark goes black in poor light, which is our bark
  lesson again ([McAuley 2012](https://blog.selfshadow.com/publications/s2012-shading-course/mcauley/s2012_pbs_farcry3_notes_v2.pdf)).

### 2.5 Lighting design

- **Naughty Dog (Gabe Betancourt):** match the reference with **one key light**, and add lights only when that is
  exhausted. If the scene is muddy, delete everything and rebuild from the key. The key is about 80 % of the work
  ([Game Developer](https://gamedeveloper.com/art/-i-last-of-us-i-lighting-artist-offers-devs-a-tip-set-the-mood-with-a-single-light)).
- **GDC "How To Light A Level"** ([slides](https://www.blog.radiator.debacle.us/2018/03/gdc-2018-how-to-light-level-slides-and.html)):
  - Light the exit and the critical path.
  - In combat spaces, put **rim and background lights behind enemies** so zombie silhouettes read.
  - Keep faint fill lights non-specular.
  - Avoid overusing blue and orange.
- **True black only in small torch-lit rooms and caves.** Elsewhere, give the feeling of darkness without crushing it.

---

## 3. Characters, creatures and motion

### 3.1 Skin and flesh

- Use the Subsurface Profile shading model with **Specular 0.35** and Roughness about 0.4
  ([Epic human skin](https://dev.epicgames.com/documentation/unreal-engine/creating-human-skin-in-unreal-engine)).
- **Cavity:** BaseColor × Cavity and Specular = Cavity × 0.35. Never set Specular to 0; raise roughness instead.
- **Epic digital humans:**
  - more specular where skin is stretched tight, less in pores
  - roughness made from the normal map
  - fresnel roughness at the edges fakes peach fuzz
- **Mean Free Path Distance is in cm.** Epic's own example broke at 50 and looked right at 5. If SSS "doesn't work" in
  5.3, check this value first.
- **Rotten flesh** [UNVERIFIED recommendation]. Make one Subsurface Profile per creature.
  - Corpse skin: MFP 0.3–0.6 cm with a grey-olive colour (about 0.5, 0.45, 0.4). There is less blood, so there is less
    red scatter.
  - Exposed muscle: red, 0.5–1 cm.
- **Wet flesh.** Clear Coat cannot be combined with SSS in 5.3. Do the wetness in roughness (0.05–0.2 with noise breakup)
  and in the normal.
- **Flesh Brute idea (Rat King, TLOU2).** Physics jiggle on the growths. Our cheap version is AnimDynamics on the growth
  bones ([GamesRadar](https://gamesradar.com/the-last-of-us-2-rat-king-making-of)).

### 3.2 Eyes, teeth, hair

- Use Epic's eye material and mesh. Sclera brightness 0.9–1.3, roughness 0–0.1. Source:
  [Photoreal Character](https://docs.unrealengine.com/4.26/en-US/Resources/Showcases/PhotorealisticCharacter).
- **The secret is three extra small meshes:** an eyelid occlusion sheet, a **wet tear-line strip** and the caruncle.
- **Zombie eyes:** a milky, low-contrast iris, but keep the wet tear line. TLOU2's infected have retro-reflective eyes.
- **Teeth:** never white. Use about 0.6–0.7 off-yellow, darker toward the back of the mouth, with low SSS.
- **Hair cards:** about 800 hand-placed cards, a random tangent per strand, and Pixel Depth Offset at the scalp line.

### 3.3 Armour and cloth on characters

- Iron is 0.56, 0.57, 0.58 linear with metallic 1. All variation lives in roughness.
- **Chainmail:** never model it ring by ring. Bake a small tile of interlocking rings to normal, opacity and AO, and tile
  it. The dark holes hide the tiling.
- **Dirt:** the bottom is darker and rougher (mud, blood splash), the top is cleaner, and grime packs around rivets.

### 3.4 Motion: the biggest tell

1. **Fix the Mixamo root first.** Use Bake to Root or a Blender root-bone fix, then root motion.
2. **±15–20 % rule:** never change play rate or stride by more than about 20 %. Change movement speed instead
   ([Epic Lyra animation blog](https://www.unrealengine.com/tech-blog/adapting-lyra-animation-to-your-ue5-game)).
3. **Animation Warping plugin**
   ([Epic pose warping](https://dev.epicgames.com/documentation/unreal-engine/pose-warping-in-unreal-engine)):
   - Orientation Warping: one forward cycle covers 180° of direction.
   - Stride Warping: clamp to about 0.8–1.2.
   - Avoid Slope Warping, which is experimental.
4. **Distance Matching:** add a Distance Curve modifier on start and stop animations.
5. **Inertialization** on every transition. The 5.3 experimental **Dead Blending** node handles very different poses
   (halflife scale 0.3) ([orange duck](https://theorangeduck.com/page/dead-blending-node-unreal-engine)).
6. **Physical hit reaction (Blueprint):**
   1. Get the hit bone.
   2. ApplyPhysicalAnimationProfileBelow.
   3. SetAllBodiesBelowSimulatePhysics.
   4. Ramp the blend weight 0 → 1 → 0 over about 0.3 s [UNVERIFIED timing].
   - Exclude the pelvis and legs.
7. **Scale check:** Dying Light 2's Biter has about 1,000 hit reactions. For a small team, about 8 directional hit
   additives plus the physics blend give most of the effect
   ([3dvf](https://3dvf.com/en/redaction/dying-light-2-stay-human-our-interview-with-techland-about-the-gut-feeling-update-focused-on-combat-animations-and-physics/)).
8. **RE2 grab trick:** they used one bite animation corrected with IK at 5 contact points instead of 135 variants, which
   cut the work to under a third ([CGWorld](https://cgworld.jp/feature/201910-re2019-02.html)). Do the same for zombie
   grabs with Two Bone IK or Control Rig.
9. **Variation for every zombie** [standard practice]:
   - play rate 0.85–1.15
   - a random start position
   - 3–5 walk cycles
   - a limp or arm-hang additive at a random alpha
   - lower physics muscle force on the head and arms
   - For hordes, the **Animation Budget Allocator** (a.Budget.BudgetMs 1.0).

### 3.5 Gore without C++

- **Wounds (Tom Looman):** move the hit point into bone space, then into reference-pose space, and pass it as a vector
  parameter to a **sphere mask on Pre-Skinned Local Position**. It never swims during animation. Use 3–5 slots and animate
  the radius ([tomlooman.com](https://tomlooman.com/unreal-engine-render-character-wounds/)). Avoid render-target wounds,
  which cost 1.6–4.5 ms spikes.
- **Dismemberment (DL2 style):**
  1. Hide the limb (HideBoneByName or a mask).
  2. Put a pre-made cap mesh on the stump.
  3. Spawn the limb as its own physics mesh plus VFX.
  - Break Constraint is exposed to Blueprint.
- **Layered flesh (Dead Space remake rule: peel before you sever).** For each body zone, a damage stage from 0 to 3 picks
  skin, then muscle shell, then bone. Only allow a cut at stage 2 or higher [design, UNVERIFIED].

---

## 4. VFX, environment, medieval authenticity

### 4.1 Fire and smoke (Niagara)

- **Motion-vector flipbooks**
  ([loronsodev](https://loronsodev.github.io/posts/explosion-fx)):
  - A 2048² sheet at 8×8 frames gives 256 px per frame.
  - With motion vectors, about 32 frames match about 120.
  - Use UE's **Flipbook Motion Vectors** function.
- **Pack 2 textures:**
  - Texture 1: R/G = motion, B = emissive, A = alpha.
  - Texture 2: lighting from Top/Left/Right/Bottom. This 4-way lighting makes smoke react to torches and the moon.
  - The 6-way version is in [Unity's blog](https://unity.com/blog/engine-platform/realistic-smoke-with-6-way-lighting-in-vfx-graph).
  - **EmberGen ≤1.0.5 swaps Top and Right**, so check the channels.
- **Why fire looks fake:**
  - a static flame, with no smoke or embers
  - no glow falloff on the ground
  - the moon as bright as the fire
  - the core not desaturated toward white
  Use a **blackbody colour ramp**.
- **Campfire structure**
  ([80.lv](https://80.lv/articles/creating-a-campfire-vfx-in-ue4)):
  - 14 emitters: 6 fire, 3 embers, 1 heat haze (refraction 1.1→1.0), 2 smoke, 2 lights.
  - Spawn particles invisible and fade them in fast.
- **Emissive:** about 10–50+ for fire. Lumen drops emissive lighting at low scalability, so **always add a real point
  light**.
- **Performance** ([unrealtechart](https://adamkomarowski.github.io/unrealtechart/book/vfx/)):
  - Smoke overdraw reaches 5–20×, so use cut-out sprite shapes.
  - Set Fixed Bounds on torches.
  - Use GPU emitters only above about 1000 particles.
- **No VDB / heterogeneous volumes in 5.3.** They are still preview quality; use flipbooks.

### 4.2 Wetness, decals, wind

- **Ghost of Tsushima:** **one global wind field** drives grass, trees, smoke, fire, cloth and ropes. Characters get mud on
  the knees, elbows and shoulders when rolling ([PlayStation Blog](https://blog.playstation.com/?p=345372)).
- **Puddles:** lerp the normal toward flat by water height, so water fills low areas first. It also breaks up tiling.
- **DBuffer decals:** overlapping decals don't blend (Sort Order picks one). Turn off Receives Decals on characters
  ([UE decals](https://dev.epicgames.com/documentation/unreal-engine/decal-materials-in-unreal-engine)).
- **Rain indoors:** a top-down depth capture to a render target masks indoor areas.

### 4.3 Environment method (Kingdom Come: Deliverance, the realistic medieval benchmark)

Sources: [80.lv](https://80.lv/articles/kingdom-come-deliverance-an-interview-with-daniel-vavra) and
[Xbox Wire](https://news.xbox.com/en-us/2025/02/04/building-an-authentic-bohemia-in-kingdom-come-deliverance-2/).

- Start from real terrain data.
- Lay out villages from old military maps.
- Shoot plants on location.
- Treat forests as human-managed, not uniform wild cover.
- Crafts cluster by street.
- Their test: miss enough small details and people "smell the inaccuracy".
- **Village tricks** ([80.lv](https://80.lv/articles/medieval-village-production-guide/)):
  - one mesh with 2–4 colour variants
  - a distant castle built from simple boxes with black window fills
  - foreground, mid and background split in PureRef

### 4.4 UE 5.3 Nanite and foliage

- **Nanite tessellation is experimental in 5.3.**
  1. Enable the Nanite Displaced Mesh plugin.
  2. In DefaultEngine.ini under `[/Script/Engine.RendererSettings]`, set `r.Nanite.AllowTessellation=1` and
     `r.Nanite.Tessellation=1`.
  3. Tick Enable Tessellation in the material.
  - Known 5.3 bug: keep the magnitude multiplier below 1.
- **Foliage FPS killer:** Pixel Depth Offset in foliage materials tanks VSM shadow depth (one report gained about 60 fps
  back). Use Shadow Cache Invalidation = Rigid on trees, and a WPO Disable Distance of about 20–50 m
  ([forum](https://forums.unrealengine.com/t/shadowdepth-tanking-fps-with-nanite-vsm-foliage-ue-5-3/2072806)).
- Masked Nanite foliage costs about 2× opaque, so prefer modelled leaves.
- Streaming pool warning: `r.Streaming.PoolSize=4000`.

### 4.5 Real medieval castles (authenticity cues)

- **Whitewashed.** In 1240 Henry III ordered the Tower of London keep "whitened inside and out", which is where the name
  White Tower comes from ([Wikipedia](https://en.wikipedia.org/wiki/White_Tower_(Tower_of_London))). Harlech was white
  too.
  - **Weathering:**
    - brown streaks below garderobe (toilet) chutes
    - render falls off projecting stones first
    - plaster drifts toward grey and brown over time
    - putlog (scaffold) holes dot the walls
    Sources: [thecollector](https://www.thecollector.com/medieval-castles-prime-appearance/),
    [Rauna](https://pils.rauna.lv/en/rauna-castle-plastering/).
- **Interiors use "false ashlar":** white limewash with thin red lines imitating stone blocks, sometimes a flower per block
  (Durham). Halls have murals and wall hangings, and royal rooms are green, red and gold. Source:
  [Goodrich](https://the-past.com/feature/worth-a-thousand-words-examining-medieval-wall-paintings-at-goodrich-castle/).
- **Great hall** ([World History](https://www.worldhistory.org/Great_Hall/)):
  - a rush floor with herbs
  - an early central hearth with a roof louvre, so smoke-blackened rafters
  - a raised dais where only the lord has a chair; everyone else sits on benches
  - a screens passage to the kitchen
  - shuttered unglazed windows before the 14th century
  - **Real size about 30×12–17 m**, up to about 18 m high.
- **Scale (Rochester keep)** ([Wikipedia](https://en.wikipedia.org/wiki/Rochester_Castle)):
  - footprint 21×21 m
  - walls **3.7 m thick at the base**, 3 m at the top
  - about 35 m tall
  - entrance on the **first floor** via an external stair and forebuilding
- **Stairs** are steep, narrow and have no handrails, and they spiral **both** ways. The clockwise-for-defenders idea is a
  myth ([source](https://talesoftimesforgotten.com/2019/12/18/no-medieval-staircases-werent-designed-to-give-right-handed-defenders-an-advantage/)).

---

## 5. Still open (next research round)

- Measured torch candela.
- Real flame luminance in nits.
- Measured medieval door, step and merlon sizes.
- The settings inside City Sample, Lyra and Valley of the Ancient. Open the projects and read the Post Process and lights.
- The Naughty Dog TLOU2 tech-art deck (a 152 MB .pptx; the download was blocked).
- Bark, moss and straw albedo (Baran's list).
- Edge-wear coverage percentages: no public source exists.
