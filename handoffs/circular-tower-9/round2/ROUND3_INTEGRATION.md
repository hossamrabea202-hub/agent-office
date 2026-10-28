# Tower #9 round 3: both FRONT towers replaced in the live castle (checkking (Claude), 2026-10-28)

The owner said "continue until the castle is AAA and the two front towers are replaced correctly". Done and saved in ThirdPersonMap (World Partition). Backup taken before any change: `Castle Defender/Tools/Tower9_R2/backup_map_pre_towers/` (umap, BuiltData, __ExternalActors__, __ExternalObjects__, 81 MB).

## Placement
| Tower | Corner | Yaw | Doorways onto |
|---|---|---|---|
| A | (50, 50, 0) | 0 | south wall walk (+X) and front wall walk (+Y) |
| B | (50, 3450, 0) | -90 | north wall walk (+X) and front wall walk (-Y) |
Actors: `Tower9_<A|B>_<Drum|Floors|Stairs|Iron|Parapet|Portals>` in outliner folders Castle/Tower9_A and Castle/Tower9_B.

## Removed / changed (integrate.py, dry run reviewed first)
- 467 actors deleted, per tower:
  - the old Castle_CornerTower and its 4 cornices, the roof slab and roof paving cube, and the buttress (fully inside the drum);
  - the side-wall roof stairs (y = 80 / y = 3420: treads, stone-module supports, caps, contact cards, StairRamp);
  - 8 slit blocks, plus parapet stones and contact cards lying fully inside the drum (~135 per tower);
  - only the 2 lowest steps of the front-wall gatehouse stairs (inside the drum). The rest of those stairs is kept.
- 12 wall-walk slabs and paving caps lowered 3 cm where they run under the tower floor (no z-fighting; invisible step).
- Tower B courtyard: 2 barrels (+ dust/blob cards) moved (+210, -350); SkillBookPickup moved (+150, -130) out of the drum.
- Roof cannons:
  - Cannon_old_field_cannon3 → (95, 190, 1075). Its base overhung the stair hatch.
  - Cannon_old_field_cannon4 → (200, 3450, 1075), yaw 90 (aims north).

## Added
- 4 interior wall torches (2 per tower), copied from the castle's torch set: iron torch, mount card, flame emitter, warm point light, soot card. Placed on the inner wall (r 413), one between the doorways and one on the far wall.
- 4 hidden nav/movement ramps over the stair flights (castle StairRamp convention). The tower railings are set to *not affect navigation*: the 105 cm clear flight width minus the 35 cm agent radius on each side erased the navmesh. Build Paths run and saved.
- Perf: Drum and Parapet merged to 2 sections each (wall + trim; draw calls 9 → 2 and 8 → 2).

## Verified
- Hero in PIE, both towers: wall walk → doorway → flight A → landing → flight B → roof (feet at 1070). Mount Cannon prompt on tower A's roof.
- AI navigation (find_path_to_location_synchronously): from both wall walks of each tower to its roof, all 4 paths complete (not partial).
- Lit views: front, both courtyards, interior torch light.

## Open
- The tower assets still live in /Game/Review/Tower9_R2 (they work and get packaged). Moving them to /Game/CastleDefender/Environment is a cleanup for a later pass.
- Drum collision is complex-as-simple (59k tris). Fine for one static actor; a low-poly collision ring is optional.
- Soldier cannon crews on the roof cannons have not been watched live in PIE.
