# Siege debris set for #162 battle memory (#202 item 9, TGA). blender -b --factory-startup -P build_debris.py
# SM_Debris_BrokenCart (supply cart on its side: one wheel off and lying flat, snapped axle, sprung bed planks),
# SM_Debris_Beams (pile of three splintered beams with jagged ends), SM_Debris_Palisade (five sharpened logs of a
# torn-down palisade, fallen across each other, a scrap of binding rope). Pivots on the ground at the pile centre.
# One shared 2K atlas (shed wood baker + char: bake_debris.py). Metres, Z up.
import bpy, bmesh, numpy as np, math, os
from mathutils import Vector, Matrix
D = os.path.dirname(os.path.abspath(__file__)); rng = np.random.default_rng(209)
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


def log(a, b, r, tip=0.0, kind='wood'):
    """round log a -> b (radius r), optional sharpened tip of length tip at b; grain along the axis."""
    a, b = Vector(a), Vector(b); ax = (b - a).normalized(); L = (b - a).length
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=r, radius2=r, depth=L - tip)
    for v in bm.verts: v.co.z += (L - tip) / 2; v.co.x += 0.06 * r * math.sin(v.co.z * 7); v.co.y += 0.06 * r * math.cos(v.co.z * 5)
    if tip > 0:
        top = [v for v in bm.verts if v.co.z > L - tip - 1e-4]; c = bm.verts.new(Vector((0, 0, L)))
        ring = sorted(top, key=lambda v: math.atan2(v.co.y, v.co.x))
        for k in range(len(ring)): bm.faces.new((ring[k], ring[(k + 1) % len(ring)], c))
        for f in [f for f in bm.faces if len(f.verts) == len(ring) and all(v in ring for v in f.verts)]: bm.faces.remove(f)
    M = ax.to_track_quat('Z', 'Y').to_matrix().to_4x4(); M.translation = a; bmesh.ops.transform(bm, matrix=M, verts=bm.verts)
    return add_mesh(bm, kind, tuple(ax))
def splinters(p, d, n=6, L=0.18):
    p, d = Vector(p), Vector(d).normalized()
    for k in range(n):
        q = d + Vector((j(0.25), j(0.25), j(0.25))); q.normalize()
        timber(p + Vector((j(0.02), j(0.02), j(0.02))), p + q * (L * (0.4 + rng.random())), 0.012 + abs(j(0.006)), 0.008, taper=0.2)
NAMES = ['SM_Debris_BrokenCart', 'SM_Debris_Beams', 'SM_Debris_Palisade']; OFF = [0.0, 4.0, 8.0]
# ---- broken cart on its side ---------------------------------------------------------------------------------------
SEG[0] = 0
for k in range(5):                                                     # bed planks: the cart lies on its side, so the bed is a wall
    z = 0.2 + 0.205 * k
    timber((-0.9, -0.12 + j(0.008), z + j(0.006)), (0.9 + j(0.05), -0.12 + j(0.008), z + j(0.01)), 0.04, 0.21, sag=0.006, tilt=0.02)
for sx in (-0.6, 0.6):                                                 # cross-bearers behind the bed
    timber((sx, -0.04, 0.12), (sx + j(0.02), -0.04, 1.12), 0.08, 0.08)
timber((-1.0, -0.2, 0.08), (1.0, -0.2, 0.08), 0.1, 0.08)               # side rail on the ground
timber((0.9, 0.2, 0.62), (1.6, 0.25, 0.25), 0.07, 0.07)                 # shaft, snapped
splinters((1.6, 0.25, 0.25), (1, 0.1, -0.4))
def wheel(c, normal_axis, r=0.42):
    c = Vector(c)
    u, v = (Vector((1, 0, 0)), Vector((0, 1, 0))) if normal_axis == 'Z' else (Vector((1, 0, 0)), Vector((0, 0, 1)))
    for k in range(12):                                                # felloe segments
        a0, a1 = 2 * math.pi * k / 12, 2 * math.pi * (k + 1) / 12
        timber(c + r * (math.cos(a0) * u + math.sin(a0) * v), c + r * (math.cos(a1) * u + math.sin(a1) * v), 0.06, 0.07, kind='wood')
    for k in range(8):                                                 # spokes (one broken)
        a = 2 * math.pi * k / 8 + 0.2
        timber(c, c + (r * (0.55 if k == 3 else 0.95)) * (math.cos(a) * u + math.sin(a) * v), 0.035, 0.035)
    for k in range(12):                                                # iron tyre
        a0, a1 = 2 * math.pi * k / 12, 2 * math.pi * (k + 1) / 12
        timber(c + (r + 0.035) * (math.cos(a0) * u + math.sin(a0) * v), c + (r + 0.035) * (math.cos(a1) * u + math.sin(a1) * v), 0.065, 0.012, kind='iron')
    log(c - 0.08 * (u.cross(v)), c + 0.08 * (u.cross(v)), 0.07)        # hub
wheel((-0.5, -0.35, 0.47), 'Y')                                        # still on the axle, standing
wheel((0.6, -1.0, 0.04), 'Z')                                          # torn off, lying flat
log((-0.5, -0.45, 0.47), (-0.5, 0.15, 0.47), 0.04)                     # axle stub
splinters((-0.5, 0.15, 0.47), (0, 1, 0))
# ---- splintered beams ----------------------------------------------------------------------------------------------
SEG[0] = 1; bx = OFF[1]
for k, (a, b) in enumerate((((-1.2, -0.3, 0.1), (1.1, 0.4, 0.12)), ((-0.8, 0.6, 0.3), (0.9, -0.5, 0.06)), ((-0.2, -0.9, 0.08), (0.3, 0.9, 0.42)))):
    a = Vector(a) + Vector((bx, 0, 0)); b = Vector(b) + Vector((bx, 0, 0))
    timber(a, b, 0.2, 0.2, sag=0.0, tilt=0.02)
    splinters(b, b - a, 8, 0.25); splinters(a, a - b, 5, 0.18)
# ---- fallen palisade -----------------------------------------------------------------------------------------------
SEG[0] = 2; px = OFF[2]
for k in range(5):
    a = Vector((px - 1.0 + 0.45 * k + j(0.05), -0.6 + j(0.1), 0.1 + 0.05 * (k % 2)))
    d = Vector((0.25 * j(1), 1.0, 0.08 * (k % 3))); d.normalize()
    log(a, a + d * (2.4 + j(0.2)), 0.1 + abs(j(0.01)), tip=0.3)
for k in range(10):                                                    # binding rope scrap across the logs
    p0 = Vector((px - 1.0 + 0.2 * k, 0.1, 0.22 + 0.02 * math.sin(k))); p1 = Vector((px - 0.8 + 0.2 * k, 0.12, 0.22 + 0.02 * math.sin(k + 1)))
    timber(p0, p1, 0.025, 0.025, kind='leather')
bpy.ops.object.select_all(action='DESELECT')
for o in pieces: o.select_set(True)
bpy.context.view_layer.objects.active = pieces[0]; bpy.ops.object.join()
ob = bpy.context.active_object; ob.name = 'SM_DebrisAtlas'
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
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'debris.blend'))

