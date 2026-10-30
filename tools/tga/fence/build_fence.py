# Road fence segments (#202 item 3, TGA). blender -b --factory-startup -P build_fence.py   -> fence.blend
# Split-rail fence for the #201 cart road: SM_Fence_2m / _3m / _4m (end post + 2 rails morticed into the next post,
# the far post belongs to the next segment so pieces chain) and SM_Fence_Broken (3 m: rail snapped and hanging, post
# leaning, one rail on the ground). All four share one 2K texture atlas (one material). Timbers carry 'grain' + 'pid'
# like the ore shed, so bake_fence.py is the shed baker. Metres, Z up, run along +X from the origin, posts 1.2 m tall.
import bpy, bmesh, numpy as np, math, os
from mathutils import Vector, Matrix
D = os.path.dirname(os.path.abspath(__file__)); rng = np.random.default_rng(203)
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
pieces = []
SEG = [0]
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
    s_ = me.attributes.new('seg', 'INT', 'POINT'); s_.data.foreach_set('value', np.full(len(me.vertices), SEG[0], np.int32))
    o = bpy.data.objects.new('t', me); bpy.context.scene.collection.objects.link(o); pieces.append(o); return o

j = lambda s=0.01: rng.normal(0, s)
def log(a, b, r, sag=0.0):                                             # split rails: roughly half-round, 2 facets
    return timber(a, b, r * 1.6, r * 1.1, sag=sag, tilt=0.03)
def post(x, lean=(0, 0)):
    h = 1.2 + j(0.03); top = (x + lean[0], lean[1], h)
    timber((x, 0, -0.25), top, 0.16 + j(0.01), 0.16 + j(0.01))
    return h
NAMES = ['SM_Fence_2m', 'SM_Fence_3m', 'SM_Fence_4m', 'SM_Fence_Broken']
OFF = [0.0, 3.0, 7.0, 12.0]                                            # built side by side, re-centred on export
for k, L in enumerate((2.0, 3.0, 4.0, 3.0)):
    SEG[0] = k; x0 = OFF[k]
    if k < 3:
        post(x0)
        for z in (0.45, 0.95):
            log((x0 - 0.05, j(0.01), z + j(0.02)), (x0 + L + 0.05, j(0.01), z + j(0.03)), 0.075, sag=0.012 * L)
    else:                                                              # broken: post leans out, top rail snapped
        post(x0, lean=(0.06, 0.16))
        log((x0 - 0.05, 0.0, 0.45), (x0 + L + 0.05, 0.02, 0.43), 0.075, sag=0.05)
        log((x0 - 0.05, 0.0, 0.95), (x0 + 1.25, -0.03, 0.80), 0.075)                # snapped half, hanging
        log((x0 + 1.45, -0.35, 0.05), (x0 + L + 0.05, 0.05, 0.93), 0.075)           # other half: one end on the ground
        for t in range(5):                                                         # splinters at the break
            a = Vector((x0 + 1.25, -0.03, 0.80)); d = Vector((0.12 + j(0.04), j(0.05), j(0.05)))
            timber(a, a + d, 0.012, 0.008)
bpy.ops.object.select_all(action='DESELECT')
for o in pieces: o.select_set(True)
bpy.context.view_layer.objects.active = pieces[0]; bpy.ops.object.join()
ob = bpy.context.active_object; ob.name = 'SM_FenceAtlas'
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.003, area_weight=0.0, scale_to_bounds=False)
bpy.ops.uv.select_all(action='SELECT'); bpy.ops.uv.average_islands_scale(); bpy.ops.uv.pack_islands(rotate=True, margin=0.003)
bpy.ops.object.mode_set(mode='OBJECT'); bpy.ops.object.shade_auto_smooth(angle=math.radians(35))
print('FENCE tris', sum(len(p.vertices) - 2 for p in ob.data.polygons), flush=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'fence.blend'))      # the atlas object is what bake_fence.py bakes
# split back into the 4 segments (UVs kept), origin at the first post's foot
seg = np.empty(len(ob.data.vertices), np.int32); ob.data.attributes['seg'].data.foreach_get('value', seg)
for k, name in enumerate(NAMES):
    c = ob.copy(); c.data = ob.data.copy(); c.name = name; c.data.name = name; bpy.context.scene.collection.objects.link(c)
    bm = bmesh.new(); bm.from_mesh(c.data); bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if seg[v.index] != k], context='VERTS')
    bmesh.ops.translate(bm, vec=Vector((-OFF[k], 0, 0)), verts=bm.verts); bm.to_mesh(c.data); bm.free()
    print('SEG', name, len(c.data.polygons), flush=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'fence.blend'))
