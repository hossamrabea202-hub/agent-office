# #539/#540 spore base: owner revision request (2026-11-06, in-game, Lit viewport)

Owner: "spore bases needs revision". Screenshot: review/owner_ingame_1106.webp (Master seat, Lit, one base at a tentacle foot).

## What the shot shows (audit session, read-only)
1. **Slabs are flat, untextured grey boxes.** No vertex-colour albedo, no roughness variation, no rock detail except a
   few white "slate" patches sitting on single faces like stickers. The 880k-quad Nanite claim is not visible: every
   slab is a sharp 6-face box with no chips, bevels or fracture faces.
2. **The crust reads as a black jagged 2D silhouette.** Flat black, no lighting response, spiky outline, no cracks or
   heave visible. Looks like unlit back-faces or a black vertex colour, not rock.
3. **Spore sacs are the only part that reads** (purple-brown clusters), but they float on top of the slabs instead of
   growing out of gaps and cracks.
4. **Scale and grounding:** slabs are hero-sized cubes piled on the crust with no dirt skirt, no rubble transition,
   no contact darkening; the base sits on the tentacle like a collar, not a rupture out of the ground.
5. Lookdev previews (Blender Cycles) showed none of this: the vertex-colour pipeline is not reaching UE's material.

## Likely causes to check first (i5)
- Vertex colours not imported or not read: check the FBX import option (Vertex Color Import = Replace), that the colour
  attribute is the FIRST colour layer in the FBX, and that M_TentacleSporeBase samples VertexColor (RGB albedo, A
  roughness) and not a constant. Black crust = colour layer missing (0,0,0) or a second layer.
- Nanite + vertex colour: fine in 5.8, but a Nanite fallback/proxy with stripped attributes will show grey.
- Starter Content slate detail: it tiles in world space only on faces whose UV/triplanar input is wired; the stickers
  say it is UV0 on a mesh with no clean UVs. Use world-aligned triplanar.
- Slabs: the generator emits axis-aligned boxes; needs fracture faces (Voronoi cut), bevel/chamfer, and 2 to 3 slab
  sizes, with dust/rubble fill between them.
- Grounding: a dirt skirt + rubble gradient at the mesh edge, contact grime where slabs meet crust, sacs clustered in
  cracks and under slab lips, not on top faces.

## Owner's visual bar
This is in the same shot as the vein-lit tentacle, which reads well. The base must reach that level: real rock with
albedo/roughness, lit crust with visible heave cracks, slabs that look thrown, and a ground transition. Until then the
Master keeps bases unsaved or reverted (`sporebase_ue.py --revert`).
