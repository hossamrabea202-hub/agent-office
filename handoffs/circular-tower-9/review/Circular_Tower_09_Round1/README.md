# Circular Tower 09 — first geometry review

This is an independently authored review model, not an approved AAA/game-ready asset. No existing Unreal asset or castle actor was edited. Integration requires the owner's review and approval.

## Files
- `Circular_Tower_09_Round1.blend`: editable model, procedural preview materials, studio scene, and reference-only walkway/character envelopes.
- `.glb` and `.fbx`: tower geometry only. Reference guides, lights and cameras are excluded. GLB materials are flat PBR colors; the Blender procedural surface detail is not baked into these exports.
- `01_exterior.png`: actual model render.
- `02_circulation_cutaway.png`: actual model with selected exterior/roof parts hidden to expose circulation.
- Geometry and circulation JSON reports: bounded checks, not engine acceptance.

## Measurements and design
Meters in Blender; base-centered origin, Z up. Body diameter = 4 × 4.3 / sqrt(pi), approximately 9.704 m. Projecting cornices extend the total width to about 10.104 m.

Wall-walk floor top 6.80 m; roof deck top 10.70 m, matching the exported existing corner-platform elevation. The new parapet reaches 12.07 m: this added height is a design proposal, not an existing castle measurement.

Two portal axes are +X and +Y, each offset 1.40 m toward the interior, derived from the corner at world (50,50) cm and neighboring walkway slab centers. Openings are 2.40 m wide; jamb height 2.10 m and shallow arch crown 2.70 m above floor. Other corner placements require a reviewed rotation/mirror and interface check. No final replacement actor list has been selected.

26 stair rises at 15 cm, nominal going 27 cm, flight width 1.15 m. The switchback occupies the opposite side from the wall-to-wall passage. Roof arrival landing connects across the stairwell opening. Stair rails reduce effective clear width; crowd access to the roof remains untested.

Blue slabs and orange 1.76 m envelopes are illustrative connection/scale guides, not the actual castle or soldier meshes. Reference slab width 2 m is provisional: exported slab bounds can include overlap and do not establish the true parapet-to-parapet clear width.

## Outstanding production work
- Castle screenshots/material references are absent; limestone appearance is provisional.
- Cannon mesh bounds are absent from the inspector JSON despite the Master's note. It includes mesh paths and transforms only. No cannon is embedded; actual gun, crew, recoil and firing-line clearances still need measurement.
- Final structural detailing, stair support/landing review, weathering, texture bakes, UV/lightmap optimization, LOD/material/draw-call budgets and purpose-built collision are pending.
- Do not use a single convex collision hull: it would obstruct the interior. Actual capsule sweeps, navigation-agent settings, bidirectional soldiers, roof access and cannon behavior require Unreal tests in an isolated review level.
- Separate building elements intentionally intersect at architectural joints. Zero self-intersection or overlap is not claimed.

## Provenance
Original procedural mesh authoring by Codex using Blender 4.5. No Fab mesh bytes or third-party textures are included. Measurements: Master read-only export dated 2026-10-27, `handoffs/exports/codex/tower-9/reference_manifest_20261027T181306_901046Z.json` in Agent Office. Reproducible build script accompanies the review.

Architectural research (design principles, no copied geometry):
- Historic England, Deal artillery castle: circular gun platforms, masonry and interconnected rooms. https://historicengland.org.uk/listing/the-list/list-entry/1013380
- English Heritage, History of Deal Castle: artillery function and later parapet changes. https://www.english-heritage.org.uk/visit/places/deal-castle/history-stories/history/
- Cadw, Harlech: tower stairs connect to wall walks; historical narrow/one-way routes are not adopted as the game's required two-way passage. https://cadw.gov.wales/visit/places-to-visit/castell-harlech?lang=en

This combines historical vocabulary with the project's gameplay clearances; it is not a reconstruction of one historical tower.
