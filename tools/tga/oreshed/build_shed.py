# Ore stockpile shed (#202 item 2, TGA). blender -b --factory-startup -P build_shed.py   -> shed.blend
# Castle-yard lean-to that receives the #201 ore carts: 5 open bays (iron / copper / silver / gold ore / starmetal)
# under a plank roof, back + side plank walls, low front boards to hold the heaps, a hanging tally board per bay.
# Built from individual timbers (bevelled boxes, slight random sag/tilt) so the silhouette reads hand-made. Every
# piece carries two attributes for the baker: 'grain' (the timber's long axis) and 'pid' (random id per timber).
# Units metres, Z up, front faces -Y, origin at the floor centre. Size 6.0 x 2.6 m, 2.9 m high at the front.
import bpy, bmesh, numpy as np, math, os
from mathutils import Vector, Matrix
D = os.path.dirname(os.path.abspath(__file__)); rng = np.random.default_rng(202)
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
W, DP, HF, HB = 6.0, 2.6, 2.9, 2.2                 # width, depth, front / back eave heights
pieces = []
def timber(a, b, w, h, sag=0.0, tilt=0.0, kind='wood'):
    """box from point a to b, cross-section w x h, bevelled; long axis = grain."""
    a, b = Vector(a), Vector(b); L = (b - a).length; ax = (b - a).normalized()
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co = Vector((v.co.x * L, v.co.y * w, v.co.z * h))
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=min(w, h) * 0.12, segments=1, affect='EDGES')
    bmesh.ops.subdivide_edges(bm, edges=[e for e in bm.edges if abs((e.verts[0].co - e.verts[1].co).normalized().x) > 0.9], cuts=3)
    for v in bm.verts:                                                     # sag in the middle, tiny twist
        t = v.co.x / L; v.co.z -= sag * (1 - (2 * t) ** 2); v.co.y += tilt * t * v.co.z
    up = Vector((0, 0, 1)) if abs(ax.z) < 0.9 else Vector((1, 0, 0)); yb = up.cross(ax).normalized(); zb = ax.cross(yb)
    M = Matrix((ax, yb, zb)).transposed().to_4x4(); M.translation = (a + b) / 2; bmesh.ops.transform(bm, matrix=M, verts=bm.verts)
    me = bpy.data.meshes.new('t'); bm.to_mesh(me); bm.free()
    g = me.attributes.new('grain', 'FLOAT_VECTOR', 'POINT'); g.data.foreach_set('vector', np.tile(np.abs(np.array(ax)), len(me.vertices)))
    p = me.attributes.new('pid', 'FLOAT', 'POINT'); p.data.foreach_set('value', np.full(len(me.vertices), rng.random()))
    k = me.attributes.new('iron', 'FLOAT', 'POINT'); k.data.foreach_set('value', np.full(len(me.vertices), 1.0 if kind == 'iron' else 0.0))
    o = bpy.data.objects.new('t', me); bpy.context.scene.collection.objects.link(o); pieces.append(o); return o
j = lambda s=0.01: rng.normal(0, s)
xs = np.linspace(-W / 2 + 0.1, W / 2 - 0.1, 6)                             # 6 post lines -> 5 bays
def zroof(y): return HB + (HF - HB) * (DP / 2 - y) / DP                     # roof slopes down to the back
for x in xs:
    for y in (-DP / 2 + 0.1, DP / 2 - 0.1):
        timber((x + j(), y + j(), 0), (x + j(0.02), y + j(0.02), zroof(y) - 0.08), 0.16, 0.16)        # posts
    timber((x, -DP / 2 + 0.1, zroof(-DP / 2 + 0.1) - 0.02), (x, DP / 2 - 0.1, zroof(DP / 2 - 0.1) - 0.02), 0.10, 0.16, sag=0.02)   # rafters
    timber((x, -DP / 2 + 0.1, 0.9), (x, -DP / 2 + 0.6, zroof(-DP / 2 + 0.6) - 0.1), 0.08, 0.08)       # knee brace
for y in (-DP / 2 + 0.1, DP / 2 - 0.1):                                     # eave beams
    timber((-W / 2, y, zroof(y) - 0.08), (W / 2, y, zroof(y) - 0.08), 0.18, 0.20, sag=0.035)
n = 15                                                                      # roof planks across the rafters, slightly overlapping
for k in range(n):
    y = -DP / 2 - 0.15 + (DP + 0.3) * (k + 0.5) / n
    timber((-W / 2 - 0.15, y, zroof(y) + 0.1), (W / 2 + 0.15, y + j(0.01), zroof(y) + 0.1 + j(0.008)), 0.205, 0.035, sag=0.03, tilt=0.02)
for z in np.arange(0.12, HB - 0.1, 0.22):                                   # back wall planks (horizontal)
    timber((-W / 2 + 0.05, DP / 2 - 0.02 + 0.012 * (int(z / 0.22) % 2), z), (W / 2 - 0.05, DP / 2 - 0.02 + 0.012 * (int(z / 0.22) % 2), z + j(0.006)), 0.03, 0.235, sag=0.01)   # overlapping, no light gaps
for sx in (-1, 1):                                                          # side walls (vertical boards)
    for y in np.arange(-DP / 2 + 0.25, DP / 2 - 0.05, 0.22):
        timber((sx * (W / 2 - 0.02 + 0.01 * (round(y / 0.22) % 2)), y, 0.02), (sx * (W / 2 - 0.02 + 0.01 * (round(y / 0.22) % 2)), y, zroof(y) - 0.12 + j(0.02)), 0.235, 0.03)
for i in range(5):                                                          # bay dividers + front boards
    x0, x1 = xs[i] + 0.09, xs[i + 1] - 0.09
    for z in (0.12, 0.34):
        timber((x0, -DP / 2 + 0.05, z), (x1, -DP / 2 + 0.05, z + j(0.01)), 0.03, 0.21, sag=0.008)
    if i > 0:
        for z in (0.12, 0.34, 0.56):
            timber((xs[i], -DP / 2 + 0.15, z), (xs[i], DP / 2 - 0.15, z), 0.03, 0.21)
    xc = (x0 + x1) / 2                                                      # tally board hung from the eave on two chains
    timber((xc - 0.25, -DP / 2 + 0.02, zroof(-DP / 2) - 0.55), (xc + 0.25, -DP / 2 + 0.02, zroof(-DP / 2) - 0.55), 0.025, 0.24)
    for sx in (-1, 1): timber((xc + sx * 0.2, -DP / 2 + 0.02, zroof(-DP / 2) - 0.42), (xc + sx * 0.2, -DP / 2 + 0.02, zroof(-DP / 2) - 0.18), 0.012, 0.012, kind='iron')
for k in range(12):                                                         # floor planks
    y = -DP / 2 + DP * (k + 0.5) / 12
    timber((-W / 2 + 0.05, y, 0.015), (W / 2 - 0.05, y, 0.015 + j(0.004)), 0.21, 0.03)
for o in pieces: o.select_set(True)
bpy.context.view_layer.objects.active = pieces[0]; bpy.ops.object.join()
ob = bpy.context.active_object; ob.name = 'SM_OreShed'; ob.data.name = 'SM_OreShed'
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.003, area_weight=0.0, scale_to_bounds=False)
bpy.ops.uv.select_all(action='SELECT'); bpy.ops.uv.average_islands_scale(); bpy.ops.uv.pack_islands(rotate=True, margin=0.003)
bpy.ops.object.mode_set(mode='OBJECT'); bpy.ops.object.shade_auto_smooth(angle=math.radians(35))
print('SHED tris', sum(len(p.vertices) - 2 for p in ob.data.polygons), 'pieces', len(pieces), flush=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'shed.blend'))
