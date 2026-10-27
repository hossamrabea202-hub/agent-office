# Obsidian Sovereign — Helmet (Codex)

**WIP / unskinned / not AAA-approved / not imported into Unreal.**

Folder: **3D Assets → Codex → Obsidian Sovereign → Helmet**

This is the first part of the planned modular armour set. It is an actual hollow, connected helmet mesh with an inner lining and eye apertures, not an approved character-fitted production asset.

## Download and open

- [Complete editable package](https://github.com/hossamrabea202-hub/agent-office/releases/download/helmet-wip-2026-10-27/Obsidian_Sovereign_Helmet_WIP_2026-10-27.zip): native Blender project, high-poly OBJ, FBX, full-resolution GLB, all 4K game textures, source atlas, renders, validation reports, design reference, and authoring scripts.
- [Release and checksums](https://github.com/hossamrabea202-hub/agent-office/releases/tag/helmet-wip-2026-10-27).
- `SM_ObsidianSovereign_Helmet.fbx`: uploaded game geometry; static and unskinned.
- `Obsidian_Sovereign_Helmet_preview_2K.glb`: self-contained lightweight preview with reduced 2K textures. Use the full package for the 4K master.
- `icon.png` and `preview.png`: renders of this actual mesh.
- `asset.json`: machine-readable handoff metadata.

Extract the complete package and open `Obsidian_Sovereign_Helmet.blend` with its adjacent `textures` directory intact. Collections separate the low-poly, high-poly, approximate fit proxy, and studio. The native project is the authoritative editable asset; scripts are an archive of incremental authoring and repair work, not an independently verified one-command rebuild.

## Measured status

- Low-poly: 18,720 triangles, 9,358 vertices; one connected component.
- Zero non-manifold and boundary edges; zero n-gons and degenerate geometric triangles.
- Zero nonadjacent BVH overlap candidates on the low-poly mesh.
- Sampled UV audit at 1024 × 1024: zero overlapping pixels, zero degenerate UV triangles. Subpixel overlaps are not ruled out by a raster audit.
- 4K high-to-low Base Color, Roughness, Material ID, and tangent Normal bakes; separately baked AO; uniform metallic. Both OpenGL and DirectX normal maps are supplied; ORM is R=AO, G=roughness, B=metallic.
- Blender FBX round-trip and static GLB policy checks passed. No Unreal runtime/animation approval.

## Next agent: continue here

1. Read `AUTHORING_NOTES.md`, `reports/validation.json`, the supplied design sheet in `reference`, and the [reference-export request](https://github.com/hossamrabea202-hub/agent-office/issues/1).
2. The source game project is on another PC. Obtain the full `/Game/ShadowKight/Mesh/ShadowknightUE_SK` FBX with the actual skeleton, reference pose, original material sections and weights, plus gorget and preferably Greystone `HeroHead`. Transfer that licensed source reference privately, not in this public repository.
3. Improve silhouette and ornamental fidelity to the supplied design sheet. The current mesh is a procedural interpretation and still falls short of the requested AAA art target. Brow and eye-rim surface finishing need review. Fine high-poly relief includes shader bump, not exclusively sculpted geometry.
4. Fit to the actual armour and gorget; preserve the one-connected, closed-manifold shell requirement. Skin primarily to `head`, with the rim's `neck_01` transition derived from the real source. Do not invent bind transforms from approximate bone positions.
5. Preserve material slots `arms`, `chest`, `cloth`, `helmet` (index 3), `pants`, and `HelmW` helmet visibility. The old `M_KnightHelmet_NoHorns` UV mask is specific to the old UVs and must not be applied blindly.
6. Test head/neck animation, gorget clearance, helmet on/off, and UE 5.3 import. Re-bake and re-validate after changes. Do not mark complete solely because the numeric topology checks pass.

The original Fab armour, skeleton, gorget and head are not included. Only newly authored geometry/textures and the user-supplied design reference are packaged. No external stock mesh or paid generation service was used for this WIP.