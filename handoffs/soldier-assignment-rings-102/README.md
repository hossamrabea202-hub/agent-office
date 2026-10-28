# Soldier assignment rings — office #102

Prepared for the authorized Master/editor agent. Target: Unreal Engine 5.3, Blueprint project. No C++ build or Niagara system is required.

This package contains the original mesh, two analytic shaders, a new-asset editor builder and a clipboard graph for a **new** marker Actor. It has passed offline mesh/package/graph checks. Unreal import, shader compilation, Blueprint reconstruction and PIE have **not** been run here. Keep #102 open until the editor acceptance checks pass.

## Obtain the complete package from an office checkout

Run `./UNPACK.ps1 -Destination D:/work/assignment-rings-102` in this handoff directory (choose an existing parent and a new destination). It decodes `package.zip.b64`, checks the archive SHA256, extracts FBX/GLB and all sources, and verifies every manifest file. It does not touch Unreal. The ZIP also contains the canonical mesh package and rebuild tools. Read the extracted setup before importing.

## Install order

1. Read `BLUEPRINT_SETUP.md`. Outside PIE, run `build_assets_ue.py` in the authorized editor. It creates `/Game/Codex/AssignmentMarkers102_v1` and refuses to overwrite an existing folder.
2. Create `BP_AssignmentMarker102` and its components/variables exactly as specified. Paste `blueprints/BP_AssignmentMarker102_EventGraph.t3d` into its empty EventGraph; reconstruct nodes, compile and save.
3. Resolve the fresh order/death/Settings exports requested in [office #110](https://github.com/hossamrabea202-hub/agent-office/issues/110), then follow `GAME_INTEGRATION.md`. Semantic style IDs in this package are **not** verified game order numbers.
4. Complete `EDITOR_ACCEPTANCE.md`, post the resulting graphs/screenshots and measured performance on #102, and answer the handoff request with pass/fail.

## Appearance and method

The ground decal carries the readable order pattern and emblem and projects onto uneven receivers. A two-sided 256-triangle ribbon supplies the faint visible glow above the ground. Its vertical band is 8–24 cm above the traced tangent plane after the component offset. A narrow horizontal lip keeps it visible from a high gameplay camera. Depth Fade softens intersections and the ordinary depth test occludes it behind geometry.

The actor follows owner translation through attachment; the root uses absolute world rotation and scale. A static-world center trace refreshes height and slope every 0.2 seconds. The air rim follows this local plane; it does **not** deform separately around every stone. Sharp ledges and very rough ground need visual review. This supplies emissive geometry in the air, not a volumetric fog simulation or a light source.

Eight semantic styles: Idle, Follow, Guard, Hold, Patrol, Man cannon, Strike team, Guard team. Color, pattern and emblem provide redundant identification. The palette is provisional until matched to the current order wheel. `orders.json` is the integration contract.

## Contents

| File | Purpose |
| --- | --- |
| `build_assets_ue.py` | Creates MPC, shared decal/surface materials, preview instances and imports the mesh |
| `shaders/*.hlsl` | Original analytic masks and palettes; no bitmap texture dependencies |
| `meshes/*.fbx` | Unreal import source, 135 × 135 × 16 cm expected bounds |
| `meshes/*.obj` | Text geometry source, centimeters and Z up |
| `meshes/*.glb` | Portable geometry with a simple preview material; not the UE runtime shader |
| `blueprints/*EventGraph.t3d` | Clipboard nodes for the new marker Actor only |
| `tools/*.py` | Rebuild sources, Blender export and offline validation |
| `reports/` | Actual offline evidence; absent engine checks are explicitly marked |
| `canonical/` | Verified reusable GLB package with provenance, validation and file hashes |

At 120 visible markers the air geometry totals 30,720 triangles. There are two shared master shaders and two runtime material instances per soldier, allocated once. Worst-case terrain queries are 600 per second at the default 5 Hz, gated by life, Settings and 60 m range. These are design counts, not a frame-time benchmark. Measure decal/translucency cost in the actual renderer.

No HP-to-LP texture bake is needed for this flat unlit VFX ribbon: the detail is shader coverage. The soldier/tower mesh production pipeline is separate.

## Export basis and boundaries

The new actor clipboard serialization was checked against the office's UE 5.3 `handoffs/exports/checkking/levelup/BP_SoldierLevelUpFX.t3d` and custom-event format in `handoffs/commander-kit/paste_commander_orders.t3d`. These establish serialization format only. This package contains **no replacement paste for an existing soldier graph**. Current raw order values, parent/child inheritance and death/Settings entry points remain subject to the fresh export request #110.

Original authored geometry and shader source for the owner's project; no third-party model, paid generation or downloaded textures. Internal project use: `LicenseRef-Owner-Internal`. See `asset-spec.json` and `PROVENANCE.md`.
