# Realm dream look: how to get the owner's target in UE 5.3

Owner, 2026-10-31 23:51: *"this is exactly how i want to see the world when i am inside the bubble"*.
Target image: `owner_target.png`.

## What is in the picture (layer by layer)

| # | Layer | What you see |
|---|---|---|
| 1 | **Grade** | The whole frame is magenta/pink, the highlights are hot orange-gold, and the light cores are near white. The shadows are deep maroon, never black. |
| 2 | **Fog** | Thick pink volumetric fog that eats the distance; the mountains fade to pink silhouettes. |
| 3 | **Sky** | A swirling vortex with a glowing core and liquid, marbled flow lines. It reads as the inside of the bubble. |
| 4 | **Caustics** | A net of orange light lines moving on the tentacle and the rocks, as if under water. |
| 5 | **Lens** | Liquid warping and strong RGB fringing at the screen edges, a centre that stays clear, and blurred translucent jelly shapes in the near foreground. |
| 6 | **Bloom** | A big soft glow around every bright thing, plus bokeh on small lights. |
| 7 | **DOF** | The foreground is blurred, the mid-ground is sharp, and the distance dissolves into fog. |
| 8 | **Life** | Glowing bulb flora on the ground, glowing egg sacs with veins, jellyfish creatures in the air, drifting motes. |
| 9 | **Ground** | A wet, shiny path reflecting the glow. |

## How UE 5.3 does each one (cheapest first)

1. **Grade (post-process settings, already on `Realm_Vision`).**
   - Split tone: Shadows Gain/Tint toward maroon-magenta, Highlights Gain toward orange.
   - Global Saturation about 1.3, with a pink-orange Scene Color Tint.
   - Raise Auto Exposure Bias (the old values were too dark).
   - Dial in the Film toe/shoulder so the shadows stay maroon.
   - Driven by `W`, so it fades in with the crossing.
2. **Pink fog: Local Fog Volume (new in 5.3)** + volumetric fog on the existing Exponential Height Fog.
   - Each volume has its own **Fog Albedo** (pink) and **Fog Emissive** (warm), so it glows even in shadow.
   - Place 3-6 sphere volumes inside the bubble only; it is spherical with uniform scale.
   - Translucency needs the project setting *Local Fog Volume Apply on Translucent*.
   - Cost grows with overlaps, so keep them few and large.
   - Docs: Local Fog Volumes, Exponential Height Fog (links below).
3. **Vortex sky = the INSIDE face of the bubble.**
   - The bubble is two-sided. In the bubble material, `TwoSidedSign` < 0 (seen from inside) switches to an emissive **vortex**:
     - polar UV around a point high in the bubble;
     - the angle twisted by `1/(r+k)` and time;
     - flow noise for the marbling;
     - a hot core.
   - From outside nothing changes.
   - It is a material-only change on a copy of `M_RealmBubble3_Rim2S`. It also fixes "the bubble disappears when you are inside".
4. **Caustics: a light function.**
   - One big point or spot light inside the bubble, warm orange, with a **Light Function material**: two panning Voronoi/caustic layers, `min()` of them, then a power.
   - Movable light, attenuation radius set to the bubble.
   - The caustics land on the tentacle and the rocks without touching their materials.
   - Alternative: a world-aligned caustic term in a Deferred Decal box (additive emissive), so no light cost.
5. **Lens: post-process material (`M_RealmDream`, Before Tonemapping for HDR, plus an After Tonemapping pass for the fringe).**
   - `SceneTexture:PostProcessInput0` sampled at a UV offset by curl/flow noise × an edge mask (`smoothstep` on the distance from the centre), so the centre stays clean.
   - Per-channel UV scale gives RGB split at the edges (fringe 3-6 at full, scaled by `W`).
   - Barrel warp, 0.03-0.06.
   - A few large soft **foreground jelly overlays**: screen-space blobs with refraction, slow drift, iridescent rim.
   - Ready-made references: the "Imperfecter" post-process toolkit and Elias Wick's camera effects (Fab/Gumroad).
6. **Bloom.**
   - Bloom Intensity 2-4.
   - Large Bloom Size scale (or Convolution bloom with a soft star kernel).
   - Lens flares on, at a pink tint.
   - The emissive things must be truly HDR, roughly 5-50 nits, so bloom has something to grab.
7. **DOF: Cinematic DOF in the same post-process.**
   - Focal distance follows the hero (the camera-to-pawn distance, updated in BP_RealmVision).
   - Low f-stop for a shallow foreground blur.
8. **Life.**
   - Glowing bulbs: an emissive mesh + a tiny unshadowed point light on every 4th-5th one, for Lumen.
   - Egg sacs: Subsurface or two-sided foliage, veins in emissive.
   - Motes and spores: one Niagara GPU system in a box the size of the bubble, ~2000 sprites, soft, additive, pink/gold, slow curl noise.
   - Jellyfish: the existing wasps re-skinned later.
9. **Wet ground.**
   - New wet decals (dark, roughness 0.05, slight normal ripple) on the realm path. They are new decals only: the owner's decals stay untouched.
   - With Lumen reflections the glow reflects.

## Build order (fastest visible win first)

| Step | Who | Time | Result |
|---|---|---|---|
| A | Master | 10 min | Grade + bloom + DOF values on `Realm_Vision` (pink/orange, brighter) |
| B | Master | 15 min | 4 Local Fog Volumes inside the bubble, pink albedo + warm emissive; volumetric fog on |
| C | adjustedfilm | 40 min | `M_RealmDream` v3: edge liquid warp, RGB split, foreground jelly overlays (all scaled by MPC `Amount`) |
| D | adjustedfilm | 30 min | Bubble inside-face vortex sky (`TwoSidedSign` branch in a Rim2S copy) |
| E | Master | 15 min | Caustic light-function light inside the bubble |
| F | TGA | 60 min | Glow bulbs, egg sacs, Niagara motes, wet path decals |

## Sources
- Local Fog Volumes (Epic docs): https://dev.epicgames.com/documentation/unreal-engine/local-fog-volumes-in-unreal-engine
- Local Height Fog, introduced in 5.3 (community tutorial): https://forums.unrealengine.com/t/community-tutorial-local-height-fog-in-unreal-5/1260813
- Exponential Height Fog (Epic docs): https://dev.epicgames.com/documentation/unreal-engine/exponential-height-fog-in-unreal-engine
- Four levels of fog (Magnopus): https://www.magnopus.com/blog/mastering-fog-four-levels-of-fog-in-unreal-engine
- Light functions (Epic docs): https://dev.epicgames.com/documentation/unreal-engine/using-light-functions-in-unreal-engine
- Faking caustics with a light function (UE5 Shaders and Effects Cookbook): https://packtpub.com/en-es/product/unreal-engine-5-shaders-and-effects-cookbook-9781837633081/chapter/chapter-3-making-translucent-objects-3/section/faking-caustics-with-a-light-function-ch03lvl1sec24
- Post-process toolkit reference (Imperfecter): https://80.lv/articles/imperfecter-ue5-s-post-process-toolkit-is-out-now
- Camera distortion reference (Elias Wick): https://eliaswick.gumroad.com/l/EliasWickDistortion
- Open-world atmosphere breakdown (The Rookies): https://www.therookies.co/blog/breakdowns/creating-open-world-environments-in-unreal-engine-5-part-3
