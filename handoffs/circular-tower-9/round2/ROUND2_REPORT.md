# Tower #9 round 2 (checkking (Claude), 2026-10-28)

Owner reassigned the polish to checkking today. Live castle map NOT changed (review actors placed unsaved, removed; map not dirty). Round-1 release untouched (worked on a copy).

## 1. Export axis: fixed at source
- UE's FBX import mirrors Blender Y. Round 1 needed yaw 90 in UE. Since mirrorY ∘ Rz(-90) = Rz(90) ∘ mirrorY, the source is **rotated -90° about Z** in Blender (no mirroring, so the design's handedness is kept). Export settings unchanged (apply_unit_scale, forward -Y, up Z).
- **Asymmetric marker fixture** `SM_Tower09_AxisMarkers` exported the same way. Imported bounds min (-10,-10,0) max (505,600,880) cm are exactly as predicted: Blender +X bar lands on UE +Y, and the portal markers sit at (140,490) / (490,140), z 680–880.
- Result: **placement = (50,50,0), yaw 0**. Both portals open on the wall walks (centre x=190 / y=190), as in the round-1 fit.
- Triangle question: source 84,246; UE 84,244 = 2 degenerate drum triangles dropped on import (Drum 59,124 → 59,122).

## 2. Modular split (6 meshes, shared base-centre origin)
| Part | Objects | Tris | Material |
|---|---|---|---|
| Drum (ashlar shell, backing, footing, plinth, strings, crowns) | 8 | 59,122 | MI_Castle_StoneWall_World + MI_Castle_Trim_World (bands) |
| Floors (wall-walk floor 680, mid landing, roof landing, roof deck 1070) | 4 | 1,254 | MI_Castle_StoneWall_World |
| Stairs (2×13 treads) | 26 | 2,808 | MI_Castle_StoneWall_World |
| Iron (rails, posts, guards, stringers) | 41 | 4,428 | MI_AshenGate_Iron |
| Parapet (breastwork, merlons, caps) | 41 | 11,232 | StoneWall_World + Trim_World (caps) |
| Portals (jambs, voussoirs) | 50 | 5,400 | MI_Castle_Trim_World |

Assets: `/Game/Review/Tower9_R2/SM_Tower09_*`. The castle materials are world-aligned, so no UV work was needed.

Fixes found on the way:
- (a) Smooth ring bands had riser normals averaged with their top faces, so the triplanar stone picked the top projection and showed vertical streaks. Fixed by marking sharp edges above 30° before export (smooth-by-angle, `mesh_smooth_type='OFF'`) and importing normals as authored.
- (b) `MI_Castle_Paving_POM` (UV-based) streaked on the roof-deck rim, so the floors use the wall stone, like the castle's own wall-walk slabs.

## 3. Collision + PIE walk test
- All 6 parts use complex-as-simple collision (hollow interior, stairs and portals stay open; no convex hull around the drum). Perf item: the drum has 59k collision tris. A low-poly collision ring is planned for the LOD/perf pass.
- PIE test, with the old corner tower and both roof-stair groups (89 actors) deleted **in the PIE world only**:
  - Wall walk → +X portal → across the floor: OK (x 1100 → -315, steady at floor 680).
  - Flight A to the mid landing: OK (feet ~874).
  - Flight B: **blocked by Cannon_old_field_cannon3** (roof cannon at (95,-60,1075); its mesh overhangs the hatch at y -91 and the hero's head hits the base). Moved in PIE to (95,190,1075): the hero reaches the roof (feet 1070), and the "[E] Mount Cannon" prompt works there.
- **Integration needs:** move that cannon to (95,190,1075) or similar, plus remove the old roof stairs/corner tower (inventory as listed by the PIE clear; to be done in the isolated review level first).

## Open (next sessions)
1. Isolated review level (dependencies isolated); old stairs/tower removed there; nav rebuild; soldier two-way traffic + cannon crew test.
2. The interior is pitch dark: add torches/brackets on the drum interior. Then grime/moss cards, arrow slits, banner.
3. Perf: merge Drum's 9 slots to 2, a low-poly collision ring, Nanite/LOD check, draw-call comparison against the old tower.
4. Owner review, then integration.

Shots: r2_court_lit.jpg (lit, courtyard), r2_roof_pie.jpg (PIE, hero on the roof with the cannon prompt).
