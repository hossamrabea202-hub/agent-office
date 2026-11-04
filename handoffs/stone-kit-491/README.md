# #491 Castle stone KIT (Alien 11-04: AAA modular kit, instanced, instead of giant merged walls)
Builder: gen_boxmason.py (SHARP default: 3-8 mm arrises, flat faces, worn-corner chips as local larger radius; MASON_SOFT=1 = old).
GATE: lookdev_stone.py fold check must print inverted 0 for every block before delivery (blender -b -P lookdev_stone.py).
## TGA_PC: model the kit (Blender only)
- ~32 blocks: heights 0.42/0.46/0.50/0.55 m x lengths 0.45/0.60/0.75/0.95 m x 2 variants, depth 0.38 m
- + quoin 0.38 deep both faces, coping slab, impost, springer, ONE voussoir set (arcade: 8 equal bays, r = 1.025 m, VS 0.32, see gen_arcade.py)
- use rbox() per block, pivot at block centre, units m, FBX like gen_boxmason (Y mirrored, colors LINEAR), names SM_Kit_H<cm>_L<cm>_V<n>
- deliver FBX + fold-check log + 1 lookdev sheet in this folder
## i5: layout script (offline Python)
- from the *_specs.json + gen_boxmason.masonry() logic, output per wall a JSON list: kit block name, centre (m, wall-local), yaw/flip, scale fit (<= +-8 %)
- each stone -> nearest kit size; random 180 deg flips for variety; joint 12 mm kept
## i9 (Master): Unreal side
- HISM wall spawner from the JSON, PerInstanceRandom -> stone tone/seed in M_CastleAshlarWeathered2, import, swap (old = invisible colliders), nav 8/8, VRAM/FPS A/B, save
