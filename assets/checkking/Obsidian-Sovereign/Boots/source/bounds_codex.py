# Bounds of Codex's boots/shins FBX in the set frame: blender -b --factory-startup -P bounds_codex.py -- <fbx>...
import sys, bpy
from mathutils import Vector
for f in sys.argv[sys.argv.index('--') + 1:]:
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.fbx(filepath=f)
    for o in bpy.data.objects:
        if o.type != 'MESH': continue
        bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
        mn = Vector((min(v.x for v in bb), min(v.y for v in bb), min(v.z for v in bb))); mx = Vector((max(v.x for v in bb), max(v.y for v in bb), max(v.z for v in bb)))
        print('BB', f.split('/')[-1], o.name, 'min', tuple(round(x, 3) for x in mn), 'max', tuple(round(x, 3) for x in mx), 'tris', sum(len(p.vertices) - 2 for p in o.data.polygons))
