# Medic gear for #185 (#202 item 8, TGA). blender -b --factory-startup -P build_medic.py   -> medic.blend
# SM_MedicSatchel (leather bag with a linen patch embroidered with a green herb sprig - deliberately NOT a red cross,
# which is a protected emblem), SM_MedicArmband (white linen band for the upper arm, knotted), SM_BandageRoll (pickup /
# hand prop with a loose tail). Pivots: satchel = strap top, armband = arm axis centre, roll = centre.
# One shared 2K atlas; per-piece material in the 'mat' attribute (leather / iron / cloth / patch) for bake_medic.py.
import bpy, bmesh, numpy as np, math, os
from mathutils import Vector, Matrix
D = os.path.dirname(os.path.abspath(__file__)); rng = np.random.default_rng(208)
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
pieces = []
SEG = [0]
KIND = {'wood': 0.0, 'iron': 1.0, 'leather': 2.0, 'wax': 3.0, 'flame': 4.0, 'cloth': 5.0, 'patch': 6.0}
def tag(me, kind, grain=(0.0, 0.0, 1.0)):
    n = len(me.vertices)
    me.attributes.new('grain', 'FLOAT_VECTOR', 'POINT').data.foreach_set('vector', np.tile(np.abs(np.array(grain, float)), n))
    me.attributes.new('pid', 'FLOAT', 'POINT').data.foreach_set('value', np.full(n, rng.random()))
    me.attributes.new('iron', 'FLOAT', 'POINT').data.foreach_set('value', np.full(n, 1.0 if kind == 'iron' else 0.0))
    me.attributes.new('mat', 'FLOAT', 'POINT').data.foreach_set('value', np.full(n, KIND[kind] / 8.0))
    me.attributes.new('seg', 'INT', 'POINT').data.foreach_set('value', np.full(n, SEG[0], np.int32))
def add_mesh(bm, kind, grain=(0.0, 0.0, 1.0)):
    me = bpy.data.meshes.new('m'); bm.to_mesh(me); bm.free(); tag(me, kind, grain)
    o = bpy.data.objects.new('m', me); bpy.context.scene.collection.objects.link(o); pieces.append(o); return o
def timber(a, b, w, h, sag=0.0, tilt=0.0, kind='wood', taper=1.0):
    """box from point a to b, cross-section w x h, bevelled; long axis = grain."""
    a, b = Vector(a), Vector(b); L = (b - a).length; ax = (b - a).normalized()
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co = Vector((v.co.x * L, v.co.y * w, v.co.z * h))
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=min(w, h) * 0.12, segments=1, affect='EDGES')
    bmesh.ops.subdivide_edges(bm, edges=[e for e in bm.edges if abs((e.verts[0].co - e.verts[1].co).normalized().x) > 0.9], cuts=3)
    for v in bm.verts:                                                     # sag in the middle, tiny twist
        t = v.co.x / L; v.co.z -= sag * (1 - (2 * t) ** 2); v.co.y += tilt * t * v.co.z
        k_ = 1.0 + (taper - 1.0) * (t + 0.5); v.co.y *= k_; v.co.z *= k_                # taper towards b
    up = Vector((0, 0, 1)) if abs(ax.z) < 0.9 else Vector((1, 0, 0)); yb = up.cross(ax).normalized(); zb = ax.cross(yb)
    M = Matrix((ax, yb, zb)).transposed().to_4x4(); M.translation = (a + b) / 2; bmesh.ops.transform(bm, matrix=M, verts=bm.verts)
    me = bpy.data.meshes.new('t'); bm.to_mesh(me); bm.free()
    tag(me, kind, tuple(ax))
    o = bpy.data.objects.new('t', me); bpy.context.scene.collection.objects.link(o); pieces.append(o); return o

j = lambda s=0.01: rng.normal(0, s)


NAMES = ['SM_MedicSatchel', 'SM_MedicArmband', 'SM_BandageRoll']; OFF = [0.0, 1.0, 2.0]
# ---- satchel (as the miner's, slimmer, with a front patch) ---------------------------------------------------------
SEG[0] = 0; sx_ = 0.0
bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
for v in bm.verts: v.co = Vector((v.co.x * 0.25, v.co.y * 0.08, v.co.z * 0.19))
bmesh.ops.bevel(bm, geom=list(bm.edges), offset=0.03, segments=3, affect='EDGES')
bmesh.ops.translate(bm, vec=Vector((sx_, 0, -0.55)), verts=bm.verts); add_mesh(bm, 'leather', (1, 0, 0))
timber((sx_ - 0.12, -0.054, -0.5), (sx_ + 0.12, -0.054, -0.5), 0.006, 0.11, kind='leather')               # flap
timber((sx_ - 0.055, -0.059, -0.5), (sx_ + 0.055, -0.059, -0.5), 0.004, 0.08, kind='patch')                # linen patch on the flap
timber((sx_, -0.062, -0.565), (sx_, -0.062, -0.545), 0.03, 0.006, kind='iron')                             # buckle
for k in range(14):
    a0, a1 = math.pi * k / 14, math.pi * (k + 1) / 14
    p = lambda a: (sx_ + 0.13 * math.cos(a), 0.0, -0.47 + 0.42 * math.sin(a))
    timber(p(a0), p(a1), 0.04, 0.006, kind='leather')
# ---- armband -------------------------------------------------------------------------------------------------------
SEG[0] = 1; ax_ = OFF[1]
bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=False, segments=24, radius1=0.058, radius2=0.056, depth=0.07)
for v in bm.verts: v.co.x *= 1.0 + 0.04 * math.sin(math.atan2(v.co.y, v.co.x) * 3)                         # soft, uneven cloth
bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.004); bmesh.ops.translate(bm, vec=Vector((ax_, 0, 0)), verts=bm.verts)
add_mesh(bm, 'cloth', (1, 0, 0))
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=8, radius=0.014)                    # knot
bmesh.ops.translate(bm, vec=Vector((ax_ + 0.062, 0, 0)), verts=bm.verts); add_mesh(bm, 'cloth', (0, 0, 1))
for sgn in (-1, 1):                                                                                            # two short tails
    timber((ax_ + 0.066, 0, 0.004 * sgn), (ax_ + 0.09, sgn * 0.012, -0.045), 0.022, 0.003, kind='cloth')
# ---- bandage roll --------------------------------------------------------------------------------------------------
SEG[0] = 2; bx = OFF[2]
bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=0.032, radius2=0.032, depth=0.075)
bmesh.ops.rotate(bm, verts=bm.verts, cent=Vector((0, 0, 0)), matrix=Matrix.Rotation(math.pi / 2, 3, 'Y'))
bmesh.ops.translate(bm, vec=Vector((bx, 0, 0.032)), verts=bm.verts); add_mesh(bm, 'cloth', (0, 1, 0))
pts = [(bx + 0.0, -0.03, 0.01 + 0.0), (bx, -0.07, 0.004), (bx + 0.01, -0.12, 0.002), (bx - 0.005, -0.16, 0.002)]
for p0, p1 in zip(pts, pts[1:]): timber(p0, p1, 0.07, 0.002, kind='cloth')                                     # loose tailbpy.ops.object.select_all(action='DESELECT')
for o in pieces: o.select_set(True)
bpy.context.view_layer.objects.active = pieces[0]; bpy.ops.object.join()
ob = bpy.context.active_object; ob.name = 'SM_MedicAtlas'
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.003, area_weight=0.0, scale_to_bounds=False)
bpy.ops.uv.select_all(action='SELECT'); bpy.ops.uv.average_islands_scale(); bpy.ops.uv.pack_islands(rotate=True, margin=0.003)
bpy.ops.object.mode_set(mode='OBJECT'); bpy.ops.object.shade_auto_smooth(angle=math.radians(40))
seg = np.empty(len(ob.data.vertices), np.int32); ob.data.attributes['seg'].data.foreach_get('value', seg)
for k, name in enumerate(NAMES):
    c = ob.copy(); c.data = ob.data.copy(); c.name = name; c.data.name = name; bpy.context.scene.collection.objects.link(c)
    bm = bmesh.new(); bm.from_mesh(c.data); bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if seg[v.index] != k], context='VERTS')
    bmesh.ops.translate(bm, vec=Vector((-OFF[k], 0, 0)), verts=bm.verts); bm.to_mesh(c.data); bm.free()
    print('SEG', name, len(c.data.polygons), flush=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'medic.blend'))

