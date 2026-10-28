# Tower #9: Codex response to adjustedfilm's fit review
Date: 2026-10-28
Status: review findings recorded; geometry/export corrections and Unreal validation remain open.

## Ownership and source
The owner asked Codex to check adjustedfilm's feedback and take action. Reviewed issue #9, cafeteria #25, and [FIT_REPORT.md](../exports/codex/tower-9/round1-fit/FIT_REPORT.md).
Adjustedfilm's latest claim on #9 says the owner assigned them production polish, starting after 2026-10-31 ~09:00 UTC (10:00 Stockholm). Preserve that assignment; this note is a continuation checklist, not a competing round-2 asset or an integration approval.

## Export orientation: required correction and acceptance test
The review FBX at yaw 0 put a doorway outside the castle. Yaw 90 aligned both portals at the tested front corner (50,50,0 cm).
Do not blindly mirror all vertices or encode the review yaw into the castle. Blender/Unreal handedness and export/import settings must be verified together.
1. Keep the round-1 source/release immutable. Work in a versioned copy.
2. Export a small asymmetric axis/portal-marker fixture with the tower; record Blender version, FBX forward/up axes, applied transforms, and Unreal import conversion options.
3. In a new review folder, compare imported marker coordinates, portal centres/normals, winding, normals and scale against the intended castle interfaces.
4. Specify the resulting asset orientation and placement yaw together. Repeat FBX reimport and actual Unreal fit checks. A 90-degree placement workaround alone is not evidence that the source issue is fixed.
5. Keep the base origin, wall-walk floor 680 cm and roof deck 1070 cm. Record both source and imported triangle counts (84,246 vs 84,244 reported) and explain any topology difference.

## Integration conflicts: isolated test level only
- Both wall roof-stair groups obstruct the portals. Review report lists StairRamp_07 / StairRamp_10 and associated tread, cube and stone-module actors. Inventory exact actor identities/dependencies before any change.
- Inventory the swallowed old tower, four cornices, roof slab, roof/wall parapet ends, buttress and eight slit blocks. Report names/ranges are candidates for review, not a deletion script.
- Preserve original actors and assets; isolate shared sublevels/external actor data before hiding or modifying anything in a test copy.
- Base extends about 4.8 m into the courtyard. Test the actual NPC_BarracksWarden interaction space and traffic; its reported ~2.4 m separation does not prove capsule clearance.
- At review yaw 90, stairwell is x=-180..280, y=-294..-30 cm; Cannon_old_field_cannon3 is at (181,37). Test actual mesh, crew, recoil, aiming and firing envelopes rather than actor bounds.

## Production and acceptance
Adjustedfilm's continuation: modular drum/floors/roof/stairs/parapet/portals; castle-matching stone, UV/lightmap work; open-interior collision with stair ramps; LOD/Nanite and draw-call/performance comparison.
Authorized editor operator must verify two-way soldier traffic, hero stairs/roof access, cannon operation, courtyard/NPC clearance and collision in PIE. Capture lit views (fit-review images were Unlit). Keep #9 open until complete and accepted. Live-castle integration still requires the owner's review of the isolated test result.

## Actions completed by Codex
Reviewed the findings and latest ownership; published this actionable checklist and acknowledged the handoff on the tower card/cafeteria. No corrected FBX, geometry change, collision, production material or in-engine pass is claimed by this response.
