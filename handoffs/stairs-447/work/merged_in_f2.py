import bpy, bmesh, sys
from mathutils import Vector
locs = {'SM_CastleStones_0_0_4': Vector((1370, 280, 590)), 'SM_CastleStones_0_0_3': Vector((1575, 445, 770))}
lo, hi = Vector((1240, 490, -5)), Vector((2345, 775, 690))
for name, off in locs.items():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath='C:/Users/hossam.rabea/ckw/stairs/refs/%s.fbx' % name)
    ob = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]
    bm = bmesh.new(); bm.from_mesh(ob.data); bm.transform(ob.matrix_world)
    islands, seen = [], set()
    for f in bm.faces:
        if f.index in seen: continue
        stack, isl = [f], []
        seen.add(f.index)
        while stack:
            g = stack.pop(); isl.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h.index not in seen: seen.add(h.index); stack.append(h)
        vs = [v.co * 100 + off for g in isl for v in g.verts]
        a = Vector([min(v[k] for v in vs) for k in range(3)]); b = Vector([max(v[k] for v in vs) for k in range(3)])
        c = (a + b) / 2
        if all(lo[k] < c[k] < hi[k] for k in range(3)): islands.append((a, b, len(isl)))
    print('%s: %d islands with centre inside F2 volume' % (name, len(islands)))
    for a, b, n in sorted(islands, key=lambda t: (t[0].x, t[0].z))[:60]:
        print('   lo=%s hi=%s faces=%d' % ([round(x) for x in a], [round(x) for x in b], n))
