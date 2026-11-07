# The Abyssal Devourer: brief for TGA

**Owner's order (Alien, 2026-11-07):** "Tell him to modify and create this for our game. Based on the references, and pick what he needs from ChatGPT advice below."

The owner's words rule. The rest of this file is ChatGPT's advice: take what you need, change what does not fit our game.

## Owner's changes
- **Size:** spread and height are "relative to our current tanticles". Ignore 300 m, 120 m and the 30 m mouth in the sheets and the script, unless the owner says otherwise. Need the size of our tentacles? Ask Master for a dump.
- **Stage gates:** blockout, sculpt, retopology, materials, rig, animation, Unreal. No next stage without approval.

## Careful (notes from i9, not the owner)
- `ref/3.webp` is a planning picture, not real work. Its tri counts, VRAM and FPS were never measured. Do not use them as targets.
- `abyssal_stage_a.py` was not run by anyone here.
- The office rules still apply: realism knowledge base, `INDUSTRY_SECRETS.md`, only Master imports, FBX scale stated in the README.
- See what exists first: `handoffs/tentacle-eruption-cinematic`, `tentacle-rise-541`, `tentacle-anim-457`, `tentacle-spore-base-539`.

## References
`ref/1.webp` concept sheet, `ref/2.webp` model sheet (ChatGPT calls these two the design authority), `ref/3.webp` planning board.

---

# ChatGPT's advice, as passed on by the owner

**Goal:** Build a photorealistic, fully rigged, animated boss monster for CastleDefender in Unreal Engine 5.8. Use the supplied concept sheet as the visual reference. Maintain the same creature identity across every model and animation.

## 1. Creature proportions

| Part | Design target |
|---|---|
| Overall tentacle spread | relative to our current tentacles |
| Maximum visible height | relative to our current tentacles |
| Tentacles | Exactly 12 |
| Main mouth | Approximately 25% of central body height |
| Eyes | None |
| Nose | None |
| Color | Obsidian black, dark red flesh |
| Surface | Organic, armored, wet and damaged |

These dimensions are initial art targets, not verified engineering measurements.

## 2. Modeling

**Stage A, blockout**
- Central body as a huge, asymmetrical organic mass, partly buried.
- A circular, cavernous mouth facing forward.
- 12 enormous tentacles around the central body, individually identifiable.
- Tentacle roots thick and muscular, tapering into sharp, curved ends.
- A readable silhouette from front, side, back and top.
- Present the blockout for approval before detailed sculpting. Only proportions, body mass, tentacle arrangement and mouth placement are approved at this stage.

**Stage B, high-poly sculpt**
- Overlapping black chitin plates.
- Stretched skin, wrinkles, scars and damaged organic tissue.
- Sharp protective spikes along the tentacles.
- Multiple concentric layers of irregular teeth in the mouth.
- The throat as a deep fleshy tunnel.
- Cracks and glowing red veins beneath the armor.
- No recognizable human facial anatomy: no nose, forehead or eyes.

**Stage C, materials**
- Black organic armor with varied roughness.
- Dark red exposed muscle and flesh.
- Subtle wet reflections, especially inside the mouth.
- Bone-colored teeth and spikes.
- Red emissive fissures with adjustable intensity.
- Normal, roughness, base color and mask textures.
- Avoid plastic-looking skin, excessive emissive brightness and repetitive texture patterns.

## 3. Rigging
- One central root and a deformable central body.
- 12 independently controlled tentacles, about 8-16 deformation bones each, subject to testing.
- Mouth open and close controls. Throat contraction and expansion. Secondary tissue movement.
- FK/IK or spline-based tentacle controls. An Unreal Control Rig where appropriate.
- Keep geometry, material slots, bone names and controls organized for export.

## 4. Animations

| Animation | Description |
|---|---|
| Idle | Slow breathing, subtle pulsing, independent tentacle movement |
| Tentacle Retract | Tentacles withdraw toward the buried central body |
| Emergence | Bursts violently through the mountain terrain |
| Roar | Mouth opens wide, throat expands, body contracts |
| Tentacle Slam | One tentacle rises and strikes the ground |
| Sweep Attack | Tentacle sweeps sideways across a large area |
| Grab Attack | Tentacle reaches forward and curls around a target |
| Stagger | Body recoils, tentacles lose coordination |
| Death | Tentacles collapse, body sinks, emissive veins fade |

**Emergence sequence**
1. Tentacles begin retracting underground.
2. The mountain shakes, fractures and releases dust.
3. The central mass pushes upward.
4. Twelve tentacles spread outward.
5. The mouth opens.
6. The creature roars while debris and fog spread.
7. Smooth transition into gameplay idle.

Terrain destruction, debris and fog are separate Unreal VFX systems synced to the animation.

## 5. Unreal integration
- Skeletal meshes and animations through a verified FBX pipeline.
- Individually reusable clips.
- Collision for the central body and attacking tentacles.
- Animation-driven hit detection, not every visible movement as damage.
- Close, medium and distant detail strategies.
- Test material, silhouette, deformation and performance at gameplay camera distances.
- Cheaper distant animation where quality allows.

## 6. Deliverables
1. Editable source scene with organized meshes and rig.
2. High-resolution sculpt and optimized game mesh.
3. UVs, baked detail maps and PBR textures.
4. Rigged skeletal mesh with all 12 tentacles.
5. Individual animation clips.
6. Unreal-ready assets and integration docs.
7. Front, side, back and top orthographic renders.
8. Screenshots and performance measurements from Unreal.

## 7. Quality control
Not finished until:
- The silhouette matches the approved reference.
- Exactly 12 tentacles.
- No nose or visible eye anatomy.
- The giant mouth stays the main focal feature.
- Tentacles deform without visible tearing.
- Animation transitions work.
- Collision and attack timing tested in Unreal.
- Real gameplay captures show the intended scale.

Preserve existing project assets and make backups before changes.

## Blockout script
`abyssal_stage_a.py` makes the central mass, a recessed mouth, placeholder teeth, 12 tapered tentacles and 5 review cameras, in a separate Blender scene:

    blender -b --factory-startup -P abyssal_stage_a.py -- ./Abyssal_Stage_A
