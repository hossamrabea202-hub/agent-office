# AAA stair kit (#279, TGA). blender -b --factory-startup -P build_stairs.py   -> stairs.blend (env WORK = output folder)
# Industry trick (trim-module bake): 4 sculpted high-poly step modules (2 m wide, rise 18 cm, going 30 cm; rounded edges,
# chipped noses, dished worn treads, a mortar joint, a crack) are baked ONCE to a 2K strip atlas (bake_stairs.py). Every
# flight is then ONE watertight low-poly mesh whose riser/nose/tread strips point at those baked strips (variant per
# step, the most worn at the bottom), so all flights share one texture set and one MI. Sides, soffit and back use
# material slot 1 = the castle wall stone (MI_Castle_StoneWall_World), metre-planar UVs, so the flight sits in the wall.
# Kit: SM_Stair_W{120,200,300,400}_{Solid,Soffit}_N{02..16}, Z up, metres, pivot at the bottom front left corner of
# the first riser, climbing +Y, width +X. UV0 = textures, UV1 = lightmap. UCX_ convex wedge each (walkable ramp).
import bpy, bmesh, numpy as np, math, os
from mathutils import Vector
D = os.environ.get('WORK') or os.path.dirname(os.path.abspath(__file__))
R, G, B = 0.18, 0.30, 0.02                     # rise, going, nose chamfer
WM = 2.0                                       # module (baked strip) width
def vn(p, f, seed=0):
    q = p * f; i = np.floor(q).astype(np.int64); t = q - i; t = t * t * (3 - 2 * t)
    def h(dx, dy, dz):
        n = ((i[:, 0] + dx) * 73856093) ^ ((i[:, 1] + dy) * 19349663) ^ ((i[:, 2] + dz) * 83492791) ^ (seed * 2654435761)
        n = (n ^ (n >> 13)) * 1274126177; n = n ^ (n >> 16); return (n & 0xFFFF).astype(np.float64) / 65535.0
    x0 = h(0, 0, 0) + (h(1, 0, 0) - h(0, 0, 0)) * t[:, 0]; x1 = h(0, 1, 0) + (h(1, 1, 0) - h(0, 1, 0)) * t[:, 0]
    x2 = h(0, 0, 1) + (h(1, 0, 1) - h(0, 0, 1)) * t[:, 0]; x3 = h(0, 1, 1) + (h(1, 1, 1) - h(0, 1, 1)) * t[:, 0]
    y0 = x0 + (x1 - x0) * t[:, 1]; y1 = x2 + (x3 - x2) * t[:, 1]; return y0 + (y1 - y0) * t[:, 2]
def fbm(p, f, oct=4, seed=0):
    s, a, tot = 0.0, 1.0, 0.0
    for k in range(oct): s = s + a * vn(p, f * 2 ** k, seed + k); tot += a; a *= 0.5
    return s / tot
def ss(e0, e1, x): t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)
def link(name, me):
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); return o

# ---------------- strip atlas layout (shared by the bake module and every flight) ----------------
L1, L2, L3 = R - B, B * math.sqrt(2), G - B    # riser, nose chamfer, tread lengths along the profile
LP = L1 + L2 + L3
SU = 0.98 / WM                                 # atlas units per metre (same in v: square texels)
def slot_uv(k, lx, s):                         # variant k, x inside the module (0..WM), profile arc length s
    return (0.01 + SU * lx, 0.015 + k * 0.246 + SU * s)
PROF = [(0.0, 0.0, 0.0), (0.0, L1, L1), (B, R, L1 + L2), (G, R, LP)]   # (y, z, s) of one step, from riser foot

# ---------------- high-poly modules ----------------
VARS = [dict(wear=0.35, joint=False, crack=False, seed=11),     # light
        dict(wear=0.6, joint=True, crack=False, seed=23),       # two blocks, medium
        dict(wear=1.0, joint=False, crack=False, seed=37),      # heavy, bottom steps
        dict(wear=0.75, joint=True, crack=True, seed=51)]       # cracked
def high_module(k, v):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for vt in bm.verts: vt.co = Vector(((vt.co.x + 0.5) * WM, (vt.co.y + 0.5) * (G + 0.04), -0.06 + (vt.co.z + 0.5) * (R + 0.06)))
    me = bpy.data.meshes.new('HM%d' % k); bm.to_mesh(me); bm.free(); o = link('High_%d' % k, me)
    bpy.context.view_layer.objects.active = o
    m = o.modifiers.new('bev', 'BEVEL'); m.width = 0.014; m.segments = 4; bpy.ops.object.modifier_apply(modifier='bev')
    m = o.modifiers.new('rm', 'REMESH'); m.mode = 'VOXEL'; m.voxel_size = 0.0075; bpy.ops.object.modifier_apply(modifier='rm')
    me = o.data; n = len(me.vertices)
    P = np.empty(n * 3); me.vertices.foreach_get('co', P); P = P.reshape(-1, 3)
    Nv = np.array([vv.vector for vv in me.vertex_normals]); x, y, z = P[:, 0], P[:, 1], P[:, 2]
    w, sd = v['wear'], v['seed']; inward = np.zeros(n)
    mid = np.exp(-((x - WM / 2) / (0.42 * WM)) ** 2)                     # foot traffic: centre of the tread
    top = ss(R - 0.02, R - 0.004, z)
    dish = w * 0.013 * mid * ss(-0.02, 0.06, y) * ss(G + 0.02, 0.12, y) * (0.85 + 0.3 * fbm(P, 3, 2, sd))
    inward += dish * top
    dn = np.hypot(np.maximum(y, 0), np.maximum(R - z, 0))               # distance to the nose edge (y=0, z=R)
    inward += w * 0.016 * mid * (1 - ss(0.0, 0.05, dn))                  # nose rounded off where people step
    de = np.minimum.reduce([dn, np.hypot(np.minimum(x, WM - x), np.maximum(R - z, 0)), np.hypot(np.minimum(x, WM - x), np.maximum(y, 0))])
    Pw = P + 0.05 * np.stack([fbm(P, 6, 2, sd + 8), fbm(P, 6, 2, sd + 9), fbm(P, 6, 2, sd + 10)], -1)   # warp: round chips, not blocks
    chip = ss(0.56, 0.63, fbm(Pw, 14, 3, sd + 1)) * (1 - ss(0.012, 0.04, de))
    inward += chip * 0.02 * (0.5 + fbm(P, 45, 2, sd + 2))               # broken corners / chipped noses
    if v['joint']:
        jx = WM * 0.47 + 0.03 * (fbm(P * [0, 1, 1], 4, 2, sd + 3) - 0.5)
        dj = np.abs(x - jx); inward += 0.007 * (1 - ss(0.002, 0.007, dj))
        inward += 0.012 * ss(0.5, 0.62, fbm(P, 22, 2, sd + 4)) * (1 - ss(0.006, 0.02, dj))   # chipped joint rims
    if v['crack']:
        cx = WM * 0.72 + 0.06 * np.sin(y * 21 + z * 9) + 0.04 * (fbm(P, 7, 3, sd + 5) - 0.5)
        inward += 0.005 * (1 - ss(0.0015, 0.005, np.abs(x - cx))) * ss(R * 0.3, R * 0.6, z + y)
    inward += 0.0025 * (fbm(P, 9, 3, sd + 6) - 0.5) + 0.0008 * (fbm(P, 70, 2, sd + 7) - 0.5)   # tooled stone surface
    P -= Nv * inward[:, None]; me.vertices.foreach_set('co', P.ravel()); me.update()
    m = o.modifiers.new('dec', 'DECIMATE'); m.ratio = min(1.0, 50000 / len(me.polygons)); bpy.ops.object.modifier_apply(modifier='dec')
    bpy.ops.object.shade_smooth(); print('HIGH', k, len(o.data.polygons), flush=True); return o

# ---------------- low-poly bake module (one step per variant, UVs in its strip slot) ----------------
def low_module(k):
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UV0'); xs = [0.0, 0.5, 1.0, 1.5, 2.0]
    grid = [[bm.verts.new((x, py, pz)) for (py, pz, s) in PROF] for x in xs]
    for a in range(len(xs) - 1):
        for p in range(len(PROF) - 1):
            f = bm.faces.new((grid[a][p], grid[a + 1][p], grid[a + 1][p + 1], grid[a][p + 1]))
            for lp, (xx, pi) in zip(f.loops, ((xs[a], p), (xs[a + 1], p), (xs[a + 1], p + 1), (xs[a], p + 1))):
                lp[uvl].uv = slot_uv(k, xx, PROF[pi][2])
    me = bpy.data.meshes.new('LM%d' % k); bm.to_mesh(me); bm.free(); return link('BakeLow_%d' % k, me)

# ---------------- flights ----------------
def variant_for(i, n):
    if i == 0: return 2                                                  # bottom step: the most worn
    if i == n - 1: return 1 if n % 2 else 0
    return (3, 0, 1, 2, 0, 1)[(i * 7 + n) % 6]
def flight(name, W, n, soffit):
    T = 0.28                                                              # soffit depth under the nosing line
    sof = lambda y: max(0.0, y * R / G - T) if soffit else 0.0
    xs = sorted(set([round(x, 4) for x in list(np.arange(0, W + 1e-6, 1.0)) + list(np.arange(0, W + 1e-6, WM)) + [W]]))
    bm = bmesh.new(); uv0 = bm.loops.layers.uv.new('UV0'); vid = {}
    def V(x, y, z):
        key = (round(x, 5), round(y, 5), round(z, 5))
        if key not in vid: vid[key] = bm.verts.new(key)
        return vid[key]
    def face(vs, uvs, mat):
        f = bm.faces.new(vs); f.material_index = mat
        for lp, uv in zip(f.loops, uvs): lp[uv0].uv = uv
    for i in range(n):                                                    # stepped strips, material 0
        k = variant_for(i, n); pts = [(i * G + py, i * R + pz, s) for (py, pz, s) in PROF]
        for a in range(len(xs) - 1):
            x0, x1 = xs[a], xs[a + 1]; seg = math.floor(x0 / WM + 1e-6); l0, l1 = x0 - seg * WM, x1 - seg * WM
            for p in range(3):
                (ya, za, sa), (yb, zb, sb) = pts[p], pts[p + 1]
                face((V(x0, ya, za), V(x1, ya, za), V(x1, yb, zb), V(x0, yb, zb)),
                     (slot_uv(k, l0, sa), slot_uv(k, l1, sa), slot_uv(k, l1, sb), slot_uv(k, l0, sb)), 0)
    ytop = n * G; ztop = n * R
    bot = [(i * G, sof(i * G)) for i in range(n + 1)]                     # soffit samples at every step boundary
    for side, x in ((0, 0.0), (1, W)):                                    # side walls, material 1, metre-planar UV
        for i in range(n):
            ring = [(i * G, bot[i][1])] + [(i * G + py, i * R + pz) for (py, pz, s) in PROF] + [((i + 1) * G, bot[i + 1][1])]
            ring = [p for j, p in enumerate(ring) if j == 0 or abs(p[0] - ring[j - 1][0]) + abs(p[1] - ring[j - 1][1]) > 1e-6]
            if ring[0] == ring[1]: ring = ring[1:]
            vs = [V(x, py, pz) for (py, pz) in ring]; uvs = [(py, pz) for (py, pz) in ring]
            if side == 0: vs, uvs = vs[::-1], uvs[::-1]
            face(vs, uvs, 1)
    for i in range(n):                                                    # soffit / base, material 1
        (ya, za), (yb, zb) = bot[i], bot[i + 1]
        for a in range(len(xs) - 1):
            x0, x1 = xs[a], xs[a + 1]
            face((V(x0, ya, za), V(x0, yb, zb), V(x1, yb, zb), V(x1, ya, za)), ((x0, ya), (x0, yb), (x1, yb), (x1, ya)), 1)
    zb = bot[n][1]                                                        # back face
    for a in range(len(xs) - 1):
        x0, x1 = xs[a], xs[a + 1]
        face((V(x0, ytop, zb), V(x0, ytop, ztop), V(x1, ytop, ztop), V(x1, ytop, zb)), ((x0, zb), (x0, ztop), (x1, ztop), (x1, zb)), 1)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    open_e = sum(1 for e in bm.edges if not e.is_manifold)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); o = link(name, me)
    for mn in ('M_StairStrip', 'M_CastleStone'):
        o.data.materials.append(bpy.data.materials.get(mn) or bpy.data.materials.new(mn))
    lm = me.uv_layers.new(name='UV1'); me.uv_layers.active = lm
    bpy.context.view_layer.objects.active = o
    for ob in bpy.context.scene.objects: ob.select_set(ob is o)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.lightmap_pack(PREF_CONTEXT='ALL_FACES', PREF_MARGIN_DIV=0.3); bpy.ops.object.mode_set(mode='OBJECT')
    me.uv_layers.active = me.uv_layers['UV0']
    tris = sum(len(p.vertices) - 2 for p in me.polygons)
    yk = min(ytop, T * G / R) if soffit else ytop                         # where the soffit leaves the ground
    ch = [(0, 0, 0), (W, 0, 0), (0, yk, 0), (W, yk, 0), (0, ytop, ztop), (W, ytop, ztop), (0, ytop, bot[n][1]), (W, ytop, bot[n][1])]
    cb = bmesh.new(); [cb.verts.new(c) for c in ch]; bmesh.ops.convex_hull(cb, input=cb.verts)
    cm = bpy.data.meshes.new('UCX_' + name); cb.to_mesh(cm); cb.free(); c = link('UCX_' + name, cm); c.parent = o
    return o, tris, open_e

if __name__ == '__main__':
    for o in list(bpy.data.objects): bpy.data.objects.remove(o)
    for k, v in enumerate(VARS):
        h = high_module(k, v); l = low_module(k); h.location.x = l.location.x = k * 3.0
    rep = []
    for W in (1.2, 2.0, 3.0, 4.0):
        for soffit in (False, True):
            for n in range(2, 33 if W == 2.0 else 17):                         # 2 m flights up to 32 steps: no split pieces (#301)
                nm = 'SM_Stair_W%03d_%s_N%02d' % (round(W * 100), 'Soffit' if soffit else 'Solid', n)
                o, tris, open_e = flight(nm, W, n, soffit); o.location = (20 + n * 6, (W * 10) + (40 if soffit else 0), 0)
                rep.append((nm, tris, open_e))
    bad = [r for r in rep if r[2] or r[1] > 1000]
    print('FLIGHTS', len(rep), 'max tris', max(r[1] for r in rep), 'not watertight / over 1k:', bad, flush=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'stairs.blend'))
