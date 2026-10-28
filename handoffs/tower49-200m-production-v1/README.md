# Medieval spiral tower #49 - 200 m production candidate

Owner-approved realistic medieval design. Ground datum is Z=0; roof deck is at
198 m and battlements end at 200 m. The original whiteboard 250 m was superseded
by the owner. First stair consoles extend below grade as foundations.

Static environment asset; not yet imported or Play-tested in Unreal. Gameplay,
wind/E-to-grab, fog, enemies, checkpoints and summit rewards are not implemented.

## Architecture

Main drum radius 10.5 m, base radius 13 m tapering over 11 m. Exterior stairs are
3 m wide: 9 turns, 1,296 risers at 15.278 cm. A 45-degree stair section rises
2.75 m with 18 real treads. Drum bands are 5.5 m high. Arrow slits and the arched
entrance have actual openings. Crown includes corbels, deck, parapet and merlons.
This is monumental game architecture, not a structural engineering claim.

## Production contents

Editable master Blender source separates the assembly, modular kit, high-poly
bake source, collision and LODs. The high-poly masonry tile contains beveled,
tessellated, displaced stone geometry and recessed mortar; selected-to-active
bakes produce 4096-square BaseColor, tangent normal, AO and roughness maps.
Authored mineral/mottling detail is layered onto the raw albedo bake, retained
separately. Wood/iron fittings use original authored 2048-square PBR maps. They
are procedural maps, not sculpt bakes. No paid/stock/third-party assets used.

UV0 repeats the 2 m stone tile; UV1 is separately packed per module for lightmaps.
The stone bake is a reusable tile, not a unique texture for an entire 200 m tower.
Complete FBX/GLB exports are review assemblies; prefer modular FBXs under
meshes/kit with assembly.json for scene construction. Verify axes in Unreal.

BaseColor is sRGB. NormalGL is linear +Y for Blender/glTF; NormalDX is -Y for
Unreal (do not flip green twice). ORM is linear R=AO, G=roughness, B=metallic.
Source is meters/Z up. FBX uses unit-scale export and -Y forward/Z up. Check
actual import scale and orientation in a new review folder before integration.

## Collision, LOD and acceptance

Supported kit modules include matching UCX convex wall/ramp segments. Do not use
a single convex hull around this hollow tower. Validate imported hulls, doorway
and slit collision, roof access and the real hero capsule in an isolated review
scene. Decorative handholds do not implement a grab action. Decimated LOD1/2 are
candidates requiring silhouette and screen-size review, not measured performance
improvements. Choose streaming/Nanite/LOD settings from engine measurements.

Only the authorized operator touches Unreal. Preserve existing castle assets and
maps. Owner reviews the isolated result before integration. Do not close #49
before engine import, movement, collision, lighting and performance acceptance.

reports contains actual geometry, route-probe, reimport and CLI checks. A sampled
floor pass is not a capsule sweep, AI navigation test or full intersection audit.
Intentional architectural joints overlap. Check report errors before calling any
stage passed. Renders are actual authored mesh views, separate from concept art.

Original authored content for the owner. Keep provenance and hashes on handoff.

