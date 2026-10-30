# Zombie variations v2 (#199) — TGA work in progress

`build_zombie.py VARIANT=Base|Bloated|Burnt|Hollow|Infected|Soldier|Crawler` (Blender 5.2, `--factory-startup`):
an original procedural humanoid. Anatomy lofts are fused by a voxel remesh, smoothed, carved, decimated to about 22k
tris, smart-UV'd and auto-weighted to a UE-mannequin rig (23 bones). The variant switches are already in the build:
missing right arm (Hollow), legless stumps (Crawler), distended belly (Bloated).

## Status (2026-10-30)

| Part | State |
|---|---|
| Body | Fused, with hips and ankles connected (`wip_base_34.png`). Still reads as a mannequin. Needs a collarbone and sternum, a ribcage that shows through, knees, and more hunch for a zombie |
| Head | Not good yet (`wip_base_face.png`): the features are separate lumps. Next: build the skull from landmarks (cranium, zygomatic arch, orbits, maxilla, mandible) as one shaped loft or SDF, with the eyes sunk into it, then remesh |
| Rig | Named like the UE mannequin until the Master answers the SK_Zombie bone-list request (#200). Then rename the bones to match SK_Zombie, so the zombie anims play without a retarget |

## Then

- 6 variants with wounds as geometry plus texture (no decals)
- 3 skins each (pale / dark / realm), baked like the wasp and horse (pbr_check, calibrated lookdev)
- the crawler's crawl and death anims
- one import script, and a README with spawn weights per wave
