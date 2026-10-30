# Miner NPC gear (#202 item 7, TGA). blender -b --factory-startup -P build_miner.py   -> miner.blend
# Attachables for the #201 mine workers: SM_MinerPick (0.86 m pick; pivot = grip, haft along +Z), SM_MinerHelmet
# (leather cap with iron bands, a brim and a candle in an iron cup at the front; pivot = head centre at the cap rim),
# SM_MinerSatchel (leather ore satchel with flap, shoulder strap and iron buckle; pivot = top of the strap).
# One shared 2K atlas; material per piece in the 'mat' attribute (wood / iron / leather / wax / flame) for bake_miner.py.
import bpy, bmesh, numpy as np, math, os
from mathutils import Vector, Matrix
D = os.path.dirname(os.path.abspath(__file__)); rng = np.random.default_rng(207)
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
pieces = []
SEG = [0]
KIND = {'wood': 0.0, 'iron': 1.0, 'leather': 2.0, 'wax': 3.0, 'flame': 4.0}
def tag(me, kind, grain=(0.0, 0.0, 1.0)):
    n = len(me.vertices)
    me.attributes.new('grain', 'FLOAT_VECTOR', 'POINT').data.foreach_set('vector', np.tile(np.abs(np.array(grain, float)), n))
    me.attributes.new('pid', 'FLOAT', 'POINT').data.foreach_set('value', np.full(n, rng.random()))
    me.attributes.new('iron', 'FLOAT', 'POINT').data.foreach_set('value', np.full(n, 1.0 if kind == 'iron' else 0.0))
    me.attributes.new('mat', 'FLOAT', 'POINT').data.foreach_set('value', np.full(n, KIND[kind] / 4.0))
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


NAMES = ['SM_MinerPick', 'SM_MinerHelmet', 'SM_MinerSatchel']; OFF = [0.0, 1.0, 2.0]
# ---- pick ----------------------------------------------------------------------------------------------------------
SEG[0] = 0
timber((0, 0, -0.12), (0, 0, 0.74), 0.034, 0.03, taper=1.25)                       # haft, thicker at the head end
timber((0, 0, 0.66), (0, 0, 0.78), 0.06, 0.05, kind='iron')                         # eye / collar
for sx in (-1, 1):                                                                  # two tapered, slightly drooping prongs
    timber((0, 0, 0.72), (sx * 0.16, 0, 0.71), 0.045, 0.04, kind='iron', taper=0.75)
    timber((sx * 0.16, 0, 0.71), (sx * 0.30, 0, 0.66), 0.034, 0.03, kind='iron', taper=0.25)
# ---- helmet --------------------------------------------------------------------------------------------------------
SEG[0] = 1; hx = OFF[1]
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=0.118)
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.002], context='VERTS')
for v in bm.verts: v.co.z *= 0.9; v.co.y *= 1.08
bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.006); bmesh.ops.translate(bm, vec=Vector((hx, 0, 0)), verts=bm.verts)
add_mesh(bm, 'leather')
bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=32, radius1=0.15, radius2=0.13, depth=0.012)
for v in bm.verts: v.co.y *= 1.08
bmesh.ops.translate(bm, vec=Vector((hx, 0, 0.004)), verts=bm.verts); add_mesh(bm, 'leather')                   # brim
for rot in (0, 1):                                                                   # crossing iron bands over the crown
    for k in range(10):
        a0, a1 = math.pi * k / 10, math.pi * (k + 1) / 10
        def pt(a): r = 0.125; return (hx + (r * math.cos(a) if rot == 0 else 0), (r * 1.08 * math.cos(a) if rot == 1 else 0), r * 0.9 * math.sin(a) + 0.002)
        timber(pt(a0), pt(a1), 0.022, 0.004, kind='iron')
bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=0.016, radius2=0.024, depth=0.03)
bmesh.ops.translate(bm, vec=Vector((hx, -0.128, 0.075)), verts=bm.verts); add_mesh(bm, 'iron')                    # candle cup
timber((hx, -0.108, 0.07), (hx, -0.128, 0.075), 0.02, 0.006, kind='iron')            # cup bracket
bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=0.011, radius2=0.010, depth=0.05)
bmesh.ops.translate(bm, vec=Vector((hx, -0.128, 0.11)), verts=bm.verts); add_mesh(bm, 'wax')                      # candle stub
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=8, radius=0.009)
for v in bm.verts: v.co.z = v.co.z * 2.2 if v.co.z > 0 else v.co.z
bmesh.ops.translate(bm, vec=Vector((hx, -0.128, 0.146)), verts=bm.verts); add_mesh(bm, 'flame')                   # flame
# ---- satchel -------------------------------------------------------------------------------------------------------
SEG[0] = 2; sx_ = OFF[2]
bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
for v in bm.verts: v.co = Vector((v.co.x * 0.27, v.co.y * 0.09, v.co.z * 0.21))
bmesh.ops.bevel(bm, geom=list(bm.edges), offset=0.03, segments=3, affect='EDGES')
for v in bm.verts: v.co.y *= 1.0 + 0.25 * (0.5 - abs(v.co.z) / 0.21) * (abs(v.co.x) < 0.1)      # bulging with ore
bmesh.ops.translate(bm, vec=Vector((sx_, 0, -0.55)), verts=bm.verts); add_mesh(bm, 'leather', (1, 0, 0))
timber((sx_ - 0.13, -0.058, -0.505), (sx_ + 0.13, -0.058, -0.505), 0.006, 0.12, kind='leather')             # flap
timber((sx_, -0.064, -0.575), (sx_, -0.064, -0.555), 0.03, 0.006, kind='iron')                                  # buckle
for k in range(14):                                                                  # strap: an arc up to the shoulder
    a0, a1 = math.pi * k / 14, math.pi * (k + 1) / 14
    p = lambda a: (sx_ + 0.14 * math.cos(a), 0.0, -0.46 + 0.42 * math.sin(a))
    timber(p(a0), p(a1), 0.04, 0.006, kind='leather')
bpy.ops.object.select_all(action='DESELECT')
for o in pieces: o.select_set(True)
bpy.context.view_layer.objects.active = pieces[0]; bpy.ops.object.join()
ob = bpy.context.active_object; ob.name = 'SM_MinerAtlas'
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
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'miner.blend'))
