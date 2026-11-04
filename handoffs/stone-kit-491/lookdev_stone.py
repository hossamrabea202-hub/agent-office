# Lookdev for the masonry builder (i9 11-04): one 3 x 0.6 x 2 m sample wall from gen_boxmason.masonry(), an automatic
# fold check per stone (every face normal must point away from its stone's centre; zero-area faces counted too), and
# Cycles close-ups under neutral raking light. Run: blender -b -P lookdev_stone.py   -> lookdev/*.png + fold report.
import sys, os, math, random
sys.path.insert(0, 'C:/Users/hossa/sync58/tunnel')
import bpy, bmesh, numpy as np
from mathutils import Vector
import gen_boxmason as GB
OUT = 'C:/Users/hossa/sync58/tunnel/lookdev'; os.makedirs(OUT, exist_ok=True)
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
B = GB.masonry(dict(name='LD', size=[300, 60, 200], depth=0.38, len=[0.45, 0.95], course=[0.42, 0.56], damp=0.3, seed=7))
me = bpy.data.meshes.new('LD'); me.from_pydata([tuple(p) for p in B.v], [], B.f)
bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
# fold check per loose part
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
parts = []; seen = set()
for f in bm.faces:
    if f.index in seen: continue
    stack, comp = [f], []
    while stack:
        g = stack.pop()
        if g.index in seen: continue
        seen.add(g.index); comp.append(g)
        for e in g.edges:
            for h in e.link_faces:
                if h.index not in seen: stack.append(h)
    parts.append(comp)
bad = zero = total = 0
for comp in parts:
    vs = {v for f in comp for v in f.verts}; c = sum((v.co for v in vs), Vector()) / len(vs)
    for f in comp:
        total += 1
        if f.calc_area() < 1e-9: zero += 1; continue
        if f.normal.dot(f.calc_center_median() - c) < 0: bad += 1
print('FOLDCHECK parts %d faces %d inverted %d (%.3f%%) zero-area %d' % (len(parts), total, bad, 100.0 * bad / max(total, 1), zero))
bm.to_mesh(me); bm.free(); me.shade_smooth()
try: me.set_sharp_from_angle(angle=math.radians(40))
except Exception: pass
ob = bpy.data.objects.new('LD', me); bpy.context.scene.collection.objects.link(ob)
mat = bpy.data.materials.new('clay'); mat.use_nodes = True
bs = mat.node_tree.nodes['Principled BSDF']; bs.inputs['Base Color'].default_value = (0.55, 0.52, 0.47, 1); bs.inputs['Roughness'].default_value = 0.85
me.materials.append(mat)
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = 48; sc.render.resolution_x, sc.render.resolution_y = 960, 640
sc.world = bpy.data.worlds.new('w'); sc.world.use_nodes = True; sc.world.node_tree.nodes['Background'].inputs[1].default_value = 0.35
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sun.data.energy = 3.5; sun.data.angle = math.radians(1.5)
sun.rotation_euler = (math.radians(70), 0, math.radians(25)); sc.collection.objects.link(sun)     # raking light across the face
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
tgt = bpy.data.objects.new('tgt', None); sc.collection.objects.link(tgt)
tc = cam.constraints.new('TRACK_TO'); tc.target = tgt; tc.track_axis = 'TRACK_NEGATIVE_Z'; tc.up_axis = 'UP_Y'
for n, loc, aim, lens in (('ld_face', (0.0, -2.4, 0.0), (0.0, 0.0, 0.0), 35), ('ld_edge', (1.95, -0.9, 0.25), (1.45, -0.28, 0.0), 45),
                          ('ld_macro', (0.35, -0.75, 0.15), (0.2, -0.3, 0.05), 60), ('ld_graze', (-1.2, -0.45, 0.3), (0.6, -0.3, 0.1), 40)):
    cam.location = loc; tgt.location = aim; cam.data.lens = lens
    sc.render.filepath = '%s/%s.png' % (OUT, n); bpy.ops.render.render(write_still=True)
print('LOOKDEV done')
