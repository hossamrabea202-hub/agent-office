# Tower #9 round 1: fit test in the castle (2026-10-28)

Run by hossam gmail (Claude), Master, on the owner's request. The live castle map was **not** changed: the review copy was placed unsaved, screenshotted and removed. The old tower was only hidden in the editor view (temporary flag).

## Setup
- Release zip `Circular_Tower_09_Round1_REVIEW.zip` downloaded, SHA256 matches (f7f4ac65...b054).
- FBX imported as one combined mesh: `/Game/Review/Tower9_R1/SM_CircularTower09_R1` (+10 preview materials). 84,244 tris, bounds ±505 cm, height 1207 cm, scale correct. No collision generated. Saved (new folder only).
- Placed at the front corner tower centre (50, 50, 0). Viewport was Unlit in these shots.

## Result: fits, with a 90° turn
- **The FBX imports mirrored on Y** (Blender right-handed to UE). At yaw 0 one doorway faces outside the castle and the other sits 2.8 m off the wall-walk (`fit_walkX_yaw0_mirrored.jpg`). **Yaw 90** puts both doorways on the wall-walks (centred y=190 / x=190). No mesh change needed, but the export axis should be fixed at source.
- Doorway floor 680 cm = wall-walk slab top 680 cm. Roof deck 1070 cm = old tower roof 1070 cm.

## Conflicts (for integration, NOT done)
1. Old roof stairs on both walls (StairRamp_07, SM_StairTread_44-50, Cube_124-130, SM_StoneModule_43-49; StairRamp_10, SM_StairTread_142/143, SM_StoneModule_140/141, Cube_222/223) **half-block both doorways**. New tower has internal stairs, so these go.
2. Swallowed by the drum: Castle_CornerTower + 4 cornices, roof slab SM_WalkSlab_43/Cube_125, old roof parapet ParapetStone_1306-1412, wall parapet ends ParapetStone_0000-0008/0072-0077/0552-0560/0579-0584, Castle_SouthCurtain_Buttress, 8 SM_Cube_Nanite slit blocks.
3. Drum bulges ~4.8 m into the courtyard corner; NPC_BarracksWarden (700,380) stands ~2.4 m from it.
4. After yaw 90 the roof stairwell is on the outer -Y side (x -180..280, y -294..-30). Cannon_old_field_cannon3 at (181,37) sits just beside it, so check for overhang.
5. Look: flat cream preview stone vs the castle's brown rubble; no collision, LODs or castle materials.

## Shots
fit_outside, fit_court, fit_walkX, fit_roof, fit_inside (yaw 90).
