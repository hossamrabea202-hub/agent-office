import bpy, bmesh, sys
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
name, off = a[0], Vector([float(x) for x in a[1:4]]); lo = Vector([float(x) for x in a[4:7]]); hi = Vector([float(x) for x in a[7:10]])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath='C:/Users/hossam.rabea/ckw/stairs/refs/%s.fbx' % name)
ob = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]
bm = bmesh.new(); bm.from_mesh(ob.data); bm.transform(ob.matrix_world)
def w(v):  # blender metres -> UE world cm (UE y = -blender y)
    return Vector((v.x * 100 + off.x, -v.y * 100 + off.y, v.z * 100 + off.z))
inside = [f for f in bm.faces if all(lo[k] <= w(v.co)[k] <= hi[k] for v in f.verts for k in range(3))]
mats = {}
for f in inside: mats[f.material_index] = mats.get(f.material_index, 0) + 1
if inside:
    vs = [w(v.co) for f in inside for v in f.verts]
    print('RESULT %s: %d of %d faces fully inside; bbox lo=%s hi=%s; slots=%s; mat names=%s' % (name, len(inside), len(bm.faces),
          [round(min(v[k] for v in vs)) for k in range(3)], [round(max(v[k] for v in vs)) for k in range(3)], mats, [m.name for m in ob.data.materials]))
else:
    print('RESULT %s: 0 faces inside' % name)
