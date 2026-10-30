# Water trough + bucket (#202 item 5, TGA). blender -b --factory-startup -P build_trough.py   -> trough.blend
# Plank horse/soldier trough on two trestles (2.0 x 0.6 m, rim 0.75 m), iron bands at the ends, water surface as a
# second material slot; a staved wooden bucket (0.32 m) with two iron hoops and an iron bail handle. Both share one
# 2K wood/iron atlas (the ore-shed baker). Built side by side, split back into SM_WaterTrough / SM_Bucket.
import bpy, bmesh, numpy as np, math, os
from mathutils import Vector, Matrix
D = os.path.dirname(os.path.abspath(__file__)); rng = np.random.default_rng(205)
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

j = lambda s=0.01: rng.normal(0, s)
NAMES = ['SM_WaterTrough', 'SM_Bucket']; OFF = [0.0, 2.0]
# ---- trough -------------------------------------------------------------------------------------------------------
SEG[0] = 0; L, Wd, z0, Hh = 2.0, 0.6, 0.30, 0.45                      # length, width, bottom height, box height
for k in range(3):                                                    # bottom planks
    y = -Wd / 2 + 0.03 + (Wd - 0.06) * (k + 0.5) / 3
    timber((-L / 2, y, z0), (L / 2, y + j(0.004), z0 + j(0.003)), 0.19, 0.04)
for sy in (-1, 1):
    for k in range(2):                                                # side planks, slightly splayed outwards
        z = z0 + 0.03 + 0.21 * k + 0.1
        timber((-L / 2 - 0.02, sy * (Wd / 2 + 0.02 * k), z), (L / 2 + 0.02, sy * (Wd / 2 + 0.02 * k), z + j(0.004)), 0.04, 0.22, sag=0.004)
for sx in (-1, 1):
    for k in range(3):                                                # end boards (vertical)
        y = -Wd / 2 + 0.03 + (Wd - 0.06) * (k + 0.5) / 3
        timber((sx * (L / 2 - 0.02), y, z0 - 0.02), (sx * (L / 2 - 0.02), y + j(0.004), z0 + Hh), 0.2, 0.04)
    for sy in (-1, 1):                                                # trestle legs, splayed
        timber((sx * 0.7, sy * 0.36, 0.0), (sx * 0.7, sy * 0.22, z0 - 0.01), 0.09, 0.09)
    timber((sx * 0.7, -0.4, z0 - 0.05), (sx * 0.7, 0.4, z0 - 0.05), 0.1, 0.08)        # trestle cross bar
    for zz in (z0 + 0.08, z0 + Hh - 0.08):                            # iron band round the end
        timber((sx * (L / 2 - 0.08), -Wd / 2 - 0.035, zz), (sx * (L / 2 - 0.08), Wd / 2 + 0.035, zz), 0.012, 0.035, kind='iron')
# ---- bucket -------------------------------------------------------------------------------------------------------
SEG[0] = 1; bx = OFF[1]; n = 14; rb, rt, hb = 0.13, 0.16, 0.32
bm = bmesh.new()                                                      # body: one tapered shell (staves read in the texture/normal)
bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=n * 2, radius1=rb, radius2=rt, depth=hb)
bmesh.ops.translate(bm, vec=Vector((bx, 0, hb / 2)), verts=bm.verts)
top = [f for f in bm.faces if f.normal.z > 0.9]; bmesh.ops.delete(bm, geom=top, context='FACES_ONLY')
bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=-0.018)
me = bpy.data.meshes.new('bucket'); bm.to_mesh(me); bm.free()
co = np.array([v.co for v in me.vertices]); ang = np.arctan2(co[:, 1], co[:, 0] - bx)
me.attributes.new('grain', 'FLOAT_VECTOR', 'POINT').data.foreach_set('vector', np.tile([0.0, 0.0, 1.0], len(co)))
me.attributes.new('pid', 'FLOAT', 'POINT').data.foreach_set('value', ((np.floor((ang + math.pi) / (2 * math.pi) * n) * 0.618) % 1.0))
me.attributes.new('iron', 'FLOAT', 'POINT').data.foreach_set('value', np.zeros(len(co)))
me.attributes.new('seg', 'INT', 'POINT').data.foreach_set('value', np.ones(len(co), np.int32))
o = bpy.data.objects.new('bucket', me); bpy.context.scene.collection.objects.link(o); pieces.append(o)
for zz in (0.06, hb - 0.06):
    rr = rb + (rt - rb) * zz / hb + 0.006
    for k in range(16):                                               # iron hoops as 16 short straight links
        a0, a1 = 2 * math.pi * k / 16, 2 * math.pi * (k + 1) / 16
        timber((bx + rr * math.cos(a0), rr * math.sin(a0), zz), (bx + rr * math.cos(a1), rr * math.sin(a1), zz), 0.008, 0.03, kind='iron')
for k in range(10):                                                   # bail handle arc
    a0, a1 = math.pi * k / 10, math.pi * (k + 1) / 10
    timber((bx + rt * math.cos(a0), 0, hb - 0.03 + 0.16 * math.sin(a0)), (bx + rt * math.cos(a1), 0, hb - 0.03 + 0.16 * math.sin(a1)), 0.01, 0.01, kind='iron')
bpy.ops.object.select_all(action='DESELECT')
for o in pieces: o.select_set(True)
bpy.context.view_layer.objects.active = pieces[0]; bpy.ops.object.join()
ob = bpy.context.active_object; ob.name = 'SM_TroughAtlas'
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.003, area_weight=0.0, scale_to_bounds=False)
bpy.ops.uv.select_all(action='SELECT'); bpy.ops.uv.average_islands_scale(); bpy.ops.uv.pack_islands(rotate=True, margin=0.003)
bpy.ops.object.mode_set(mode='OBJECT'); bpy.ops.object.shade_auto_smooth(angle=math.radians(35))
seg = np.empty(len(ob.data.vertices), np.int32); ob.data.attributes['seg'].data.foreach_get('value', seg)
for k, name in enumerate(NAMES):
    c = ob.copy(); c.data = ob.data.copy(); c.name = name; c.data.name = name; bpy.context.scene.collection.objects.link(c)
    bm = bmesh.new(); bm.from_mesh(c.data); bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if seg[v.index] != k], context='VERTS')
    bmesh.ops.translate(bm, vec=Vector((-OFF[k], 0, 0)), verts=bm.verts); bm.to_mesh(c.data); bm.free()
    c.data.materials.append(bpy.data.materials.new('M_Wood'))
    print('SEG', name, len(c.data.polygons), flush=True)
tr = bpy.data.objects['SM_WaterTrough']                                # water surface: slot 1, its own UV corner
bm = bmesh.new(); bm.from_mesh(tr.data); uvl = bm.loops.layers.uv.active
f = bm.faces.new([bm.verts.new(Vector((sx * (L / 2 - 0.04), sy * (Wd / 2 - 0.02), z0 + Hh - 0.08))) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
f.material_index = 1
for l, uv in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): l[uvl].uv = uv
bm.to_mesh(tr.data); bm.free(); tr.data.materials.append(bpy.data.materials.new('M_Water'))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'trough.blend'))
