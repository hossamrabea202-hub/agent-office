# Obsidian Sovereign — Thigh Guards (L/R)

**Author: Codex. WIP, unskinned, not fitted to the actual game character or approved as AAA art.**

Folder: 3D Assets → Codex → Obsidian Sovereign → Thigh Guards (L/R).

## Files

- [Complete editable master](https://github.com/hossamrabea202-hub/agent-office/releases/download/obsidian-sovereign-set-wip-2026-10-27/Obsidian_Sovereign_Thighs_WIP_2026-10-27.zip) — native Blender project, high-poly OBJ master(s), game FBX, 4K maps, review renders, validation and authoring scripts. The duplicate 4K GLB and Blender backups are omitted to keep the master download smaller.
- `SM_ObsidianSovereign_Thighs_preview_2K.glb` — self-contained review GLB with 2K maps.
- FBX geometry: `SM_ObsidianSovereign_Thighs_L.fbx`, `SM_ObsidianSovereign_Thighs_R.fbx`.
- `icon.png`, `preview.png` — renders of the actual meshes.
- `validation.json`, `overlap-check.json` — measured evidence and limitations.

Open `Obsidian_Sovereign_Thighs.blend` from the extracted package with its adjacent textures directory. High-poly and low-poly collections are separated. The Blender master is authoritative; run the included rebuild scripts only in a fresh copy. Geometry and maps are new work, not exported Fab armour.

## Measured status

- 7,168 triangles and 3,584 vertices per authored low-poly piece; mirrored pairs remain separate objects and intentionally reuse one UV atlas.
- One connected material shell per piece, closed and manifold. The body openings are rimmed hollow passages, not boundary-edge holes in the material surface.
- No duplicate geometric faces or overlapping faces detected in the detailed check. See tolerances and scope in overlap-check.json.
- Zero overlapping pixels and zero degenerate UV triangles in the 1024-square sampled atlas check. Subpixel overlaps are not formally ruled out.
- Actual 4K high-to-low Base Color, Roughness, Normal and ID bakes; AO and metallic supplied; ORM is R=AO, G=roughness, B=metallic. Cloth uses a non-metal base with metallic embroidered accents. Both OpenGL and DirectX normals are included.

## Integration and next work

Coordinates are a provisional authoring pose: meters, Z up, facing -Y. Keep the separate equipment objects. No bones, bind transforms or skin weights have been invented. Pair names are authoring labels until matched to the actual skeleton.

Obtain the actual `/Game/ShadowKight/Mesh/ShadowknightUE_SK` reference, skeleton and gorget from the project PC through [issue #1](https://github.com/hossamrabea202-hub/agent-office/issues/1). Preserve its material-slot contract and visibility behavior when integrating. The Fab reference is not included and should be transferred privately.

Further work includes closer reference fidelity, final character fit, articulation/cloth behavior, collision, LODs and Unreal Engine 5.3 validation. Fine ornamental relief includes high-source shader bump. Passing numeric geometry checks is not artistic or gameplay approval.

Release: https://github.com/hossamrabea202-hub/agent-office/releases/tag/obsidian-sovereign-set-wip-2026-10-27.
