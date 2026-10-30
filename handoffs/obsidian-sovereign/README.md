# Obsidian Sovereign helmet handoff

Shared task: https://github.com/hossamrabea202-hub/agent-office/issues/1

## Request for the agent on the Unreal project PC

Export the existing hero armour reference so the modelling PC can fit and skin the Obsidian Sovereign replacement helmet.

### Required reference
- Asset: `/Game/ShadowKight/Mesh/ShadowknightUE_SK` (keep the pack's spelling).
- Export the full skeletal mesh as FBX, with the actual skeleton hierarchy, bind/reference pose, original skin weights, and all material sections. LOD0 is sufficient.
- Include the fitted steel gorget in the reference. It may already be part of the armour export; verify this.
- Export the Greystone `HeroHead` separately if available.
- Measure helmet section 3 alone: bounds, triangle count, material mapping, and existing head/neck_01 weights.
- Return the FBX through a private file transfer or private project storage. Keep the public Agent Studio issue limited to status, measurements, and non-sensitive handoff notes; do not publish the Fab source asset here.
- Preserve the source project assets. No reimport, material replacement, or Blueprint changes are required for this reference-export task.

### Integration target supplied by the owner
- Hero component: `KnightMesh`, scale 1.0.
- Skeleton family: UE4 Mannequin, retargeted from the hidden Quinn mesh. Use the asset's actual Skeleton and bind transforms.
- Slots in order: `arms`, `chest`, `cloth`, `helmet` (index 3), `pants`.
- Current helmet material: `M_KnightHelmet_NoHorns`; textures `T_Hero_helmet_*`.
- Skin influences: `head` and `neck_01` at the rim.
- Approximate component-space bone positions (cm, Z up): head (-1.9, -0.8, 153.7); neck_01 (-1.0, -2.6, 146.0). These are context, not substitutes for bind transforms.
- No head under the worn armour helmet; `HeroHead` appears when helmet is off.
- Visibility: `HelmW = 0` hides helmet.
- Inventory: `HelmLoc = 0` means worn; 10–29 means in pack.
- The replacement must preserve visibility behavior. The old horn-hiding UV mask cannot be assumed valid on new UVs.

### Current modelling-PC work
A static, unskinned WIP has been created: 18,720 triangles, one connected watertight component, zero non-manifold edges, and 4K high-to-low baked maps. The final sampled UV audit found zero overlaps and zero degenerate UV triangles. Blender FBX round-trip and GLB policy checks passed.

**This is not an AAA-approved or character-fitted asset.** Artistic fidelity, final fit, skinning, Unreal import, section replacement, animation/gorget clearance, and HelmW behavior remain unverified. The native Blender file and textures are still on the modelling PC; this request does not claim those binaries were uploaded.

### Coordination
The Agent Studio page is a browser-local prototype, not a connected agent executor. This GitHub issue is the shared handoff. The project-PC agent should explicitly acknowledge it and report the export result here when the owner directs it to read this task.
