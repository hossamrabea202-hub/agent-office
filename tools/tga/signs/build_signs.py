# Hanging shop signs (#202 item 6, TGA). blender -b --factory-startup -P build_signs.py   -> signs.blend
# Three wall signs for the castle town: SM_Sign_Smith (iron anvil + hammer), SM_Sign_Tavern (carved tankard),
# SM_Sign_Shop (gilded coin stack). Each: iron wall bracket with a curled brace, two short chains, a 0.7 x 0.45 m
# weathered board, the emblem as a raised silhouette on both faces. One shared 2K atlas (shed wood baker + gilt).
# Pivot = the bracket's wall plate (mount flush on a wall, the sign hangs along +X), metres, Z up.
import bpy, bmesh, numpy as np, math, os
from mathutils import Vector, Matrix
D = os.path.dirname(os.path.abspath(__file__)); rng = np.random.default_rng(206)
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
    gd = me.attributes.new('gild', 'FLOAT', 'POINT'); gd.data.foreach_set('value', np.full(len(me.vertices), 1.0 if kind == 'gild' else 0.0))
    s_ = me.attributes.new('seg', 'INT', 'POINT'); s_.data.foreach_set('value', np.full(len(me.vertices), SEG[0], np.int32))
    o = bpy.data.objects.new('t', me); bpy.context.scene.collection.objects.link(o); pieces.append(o); return o

j = lambda s=0.01: rng.normal(0, s)

j = lambda s=0.01: rng.normal(0, s)
def plate(pts, x0, z0, s, thick, kind):
    """extruded 2D silhouette (pts in a unit box, x right / z up) on the board's two faces, centred at (x0, z0)."""
    for side in (-1, 1):
        bm = bmesh.new(); vs = [bm.verts.new(Vector((x0 + px * s, side * 0.026, z0 + pz * s))) for px, pz in pts]
        f = bm.faces.new(vs); r = bmesh.ops.extrude_face_region(bm, geom=[f])
        bmesh.ops.translate(bm, vec=Vector((0, side * thick, 0)), verts=[v for v in r['geom'] if isinstance(v, bmesh.types.BMVert)])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        me = bpy.data.meshes.new('p'); bm.to_mesh(me); bm.free(); n = len(me.vertices)
        me.attributes.new('grain', 'FLOAT_VECTOR', 'POINT').data.foreach_set('vector', np.tile([1.0, 0.0, 0.0], n))
        me.attributes.new('pid', 'FLOAT', 'POINT').data.foreach_set('value', np.full(n, rng.random()))
        me.attributes.new('iron', 'FLOAT', 'POINT').data.foreach_set('value', np.full(n, 1.0 if kind == 'iron' else 0.0))
        me.attributes.new('gild', 'FLOAT', 'POINT').data.foreach_set('value', np.full(n, 1.0 if kind == 'gild' else 0.0))
        me.attributes.new('seg', 'INT', 'POINT').data.foreach_set('value', np.full(n, SEG[0], np.int32))
        o = bpy.data.objects.new('p', me); bpy.context.scene.collection.objects.link(o); pieces.append(o)
def circle(cx, cz, r, n=20): return [(cx + r * math.cos(2 * math.pi * k / n), cz + r * math.sin(2 * math.pi * k / n)) for k in range(n)]
ANVIL = [(-0.5, 0.25), (0.35, 0.25), (0.5, 0.18), (0.25, 0.1), (0.12, 0.0), (0.12, -0.15), (0.3, -0.3), (-0.3, -0.3), (-0.12, -0.15),
         (-0.12, 0.0), (-0.3, 0.12), (-0.5, 0.15)]
HAMMER = [(-0.05, 0.25), (0.05, 0.25), (0.05, 0.48), (0.2, 0.48), (0.2, 0.62), (-0.2, 0.62), (-0.2, 0.48), (-0.05, 0.48)]
TANKARD = [(-0.28, -0.4), (0.22, -0.4), (0.22, -0.3), (0.22, 0.32), (0.27, 0.4), (-0.33, 0.4), (-0.28, 0.32)]
HANDLE = [(0.22, 0.22), (0.42, 0.22), (0.46, 0.15), (0.46, -0.1), (0.42, -0.18), (0.22, -0.18), (0.22, -0.08), (0.35, -0.08), (0.35, 0.12), (0.22, 0.12)]
NAMES = ['SM_Sign_Smith', 'SM_Sign_Tavern', 'SM_Sign_Shop']; OFF = [0.0, 1.5, 3.0]
for k, name in enumerate(NAMES):
    SEG[0] = k; x0 = OFF[k]
    timber((x0, 0, 2.55), (x0, 0, 2.95), 0.06, 0.012, kind='iron')                      # wall plate
    timber((x0, 0, 2.9), (x0 + 0.95, 0, 2.9), 0.03, 0.03, kind='iron')                   # bracket arm
    for t in range(8):                                                                   # curled brace under the arm
        a0, a1 = math.pi * t / 8, math.pi * (t + 1) / 8
        timber((x0 + 0.3 - 0.28 * math.cos(a0), 0, 2.62 + 0.28 * math.sin(a0) * 0.9 - 0.0), (x0 + 0.3 - 0.28 * math.cos(a1), 0, 2.62 + 0.28 * math.sin(a1) * 0.9), 0.02, 0.012, kind='iron')
    for cx in (x0 + 0.27, x0 + 0.83):                                                    # chains: 4 links each
        for l in range(4):
            z = 2.88 - 0.05 * l; timber((cx, 0, z), (cx, 0, z - 0.045), 0.012 if l % 2 else 0.004, 0.004 if l % 2 else 0.012, kind='iron')
    bz = 2.43; timber((x0 + 0.2, 0, bz), (x0 + 0.9, 0, bz + j(0.005)), 0.05, 0.45, sag=0.003, tilt=0.01)        # the board (grain across)
    timber((x0 + 0.18, 0, bz + 0.235), (x0 + 0.92, 0, bz + 0.235), 0.06, 0.03)                                  # top batten
    ex, ez, s = x0 + 0.55, bz, 0.34
    if k == 0: plate(ANVIL, ex, ez - 0.03, s, 0.012, 'iron'); plate(HAMMER, ex + 0.04, ez - 0.03 + 0.004, s, 0.012, 'iron')   # hammer stands on the anvil face
    if k == 1: plate(TANKARD, ex - 0.03, ez, s, 0.014, 'wood'); plate(HANDLE, ex - 0.03, ez, s, 0.014, 'wood')
    if k == 2:
        for c, (cx, cz) in enumerate(((-0.18, -0.22), (0.0, -0.22), (0.18, -0.22), (-0.09, 0.0), (0.09, 0.0), (0.0, 0.22))):
            plate(circle(cx, cz, 0.1), ex, ez, s, 0.01 + 0.004 * (c % 2), 'gild')
bpy.ops.object.select_all(action='DESELECT')
for o in pieces: o.select_set(True)
bpy.context.view_layer.objects.active = pieces[0]; bpy.ops.object.join()
ob = bpy.context.active_object; ob.name = 'SM_SignAtlas'
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.003, area_weight=0.0, scale_to_bounds=False)
bpy.ops.uv.select_all(action='SELECT'); bpy.ops.uv.average_islands_scale(); bpy.ops.uv.pack_islands(rotate=True, margin=0.003)
bpy.ops.object.mode_set(mode='OBJECT'); bpy.ops.object.shade_auto_smooth(angle=math.radians(35))
seg = np.empty(len(ob.data.vertices), np.int32); ob.data.attributes['seg'].data.foreach_get('value', seg)
for k, name in enumerate(NAMES):
    c = ob.copy(); c.data = ob.data.copy(); c.name = name; c.data.name = name; bpy.context.scene.collection.objects.link(c)
    bm = bmesh.new(); bm.from_mesh(c.data); bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if seg[v.index] != k], context='VERTS')
    bmesh.ops.translate(bm, vec=Vector((-OFF[k], 0, -2.55)), verts=bm.verts); bm.to_mesh(c.data); bm.free()
    print('SEG', name, len(c.data.polygons), flush=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'signs.blend'))
