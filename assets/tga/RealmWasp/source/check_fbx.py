# Re-import the exported FBX into an empty scene and list what UE will get: meshes, bones, materials, takes.
import bpy, sys, os
fbx = sys.argv[sys.argv.index('--') + 1]
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
for a in list(bpy.data.actions): bpy.data.actions.remove(a)
bpy.ops.import_scene.fbx(filepath=fbx)
for o in bpy.data.objects:
    extra = ''
    if o.type == 'MESH': extra = 'tris %d mats %s dims %s' % (sum(len(p.vertices) - 2 for p in o.data.polygons), [m.name for m in o.data.materials], tuple(round(d, 2) for d in o.dimensions))
    if o.type == 'ARMATURE': extra = 'bones %d' % len(o.data.bones)
    print('FBXOBJ', o.name, o.type, extra)
for a in bpy.data.actions: print('FBXTAKE', a.name, tuple(int(x) for x in a.frame_range))
