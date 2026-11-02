# #447: copy of a merged castle-stone mesh without the faces inside a UE world box (the stepped side stones that the new
# stair replaces). The original asset is not touched; the copy is imported next to the stairs and swapped on the actor.
#   blender -b --factory-startup -P strip_merged.py -- <name> offX offY offZ  loX loY loZ  hiX hiY hiZ  <outdir>
import bpy, bmesh, os, sys
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
name = a[0]; off = Vector([float(x) for x in a[1:4]]); lo = Vector([float(x) for x in a[4:7]]); hi = Vector([float(x) for x in a[7:10]]); out = a[10]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath='C:/Users/hossam.rabea/ckw/stairs/refs/%s.fbx' % name)
ob = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]
mw = ob.matrix_world
bm = bmesh.new(); bm.from_mesh(ob.data)
def w(co):
    v = mw @ co
    return Vector((v.x * 100 + off.x, -v.y * 100 + off.y, v.z * 100 + off.z))
kill = [f for f in bm.faces if all(lo[k] <= w(v.co)[k] <= hi[k] for v in f.verts for k in range(3))]
bmesh.ops.delete(bm, geom=kill, context='FACES')
bm.to_mesh(ob.data); bm.free()
newname = name + '_s447'
ob.name = ob.data.name = newname
for o in bpy.context.scene.objects: o.select_set(o == ob)
bpy.ops.export_scene.fbx(filepath=os.path.join(out, newname + '.fbx'), use_selection=True, object_types={'MESH'},
                         mesh_smooth_type='FACE', add_leaf_bones=False)
print('STRIPPED', name, 'removed', len(kill), 'faces ->', newname)
