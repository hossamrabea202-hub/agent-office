# Yellow Eagle Knight set (#367, TGA): articulated plate gauntlets after Codex sheet 08 (c. 1300-1340 transitional).
#   blender -b --factory-startup -P build_gauntlets.py      (env WORK) -> WORK/gauntlets.blend
# Built in cm in a canonical LEFT-hand frame (wrist joint at the origin, fingers toward -Z, back of the hand toward -Y,
# palm toward +Y, thumb toward +X), then scaled to metres. fit_knightset.py later moves it onto hand_l / hand_r from the
# knight ref pose (#367 export). Sheet numbers: 28 cm cuff-to-fingertip, cuff 9.5 cm tall / 14 cm max / 11.5 cm opening,
# hand 10.5 x 4.5 cm, 3 lames per finger, 2 on the thumb, plates 1.0-1.5 mm, domed brass rivets 3-4 mm, leather glove,
# strap + buckle. Parts: Steel (cuff with rolled edges, 2 wrist lames, 2 metacarpal lames, knuckle lame with 4 bosses,
# 12 finger lames + tip domes, 2 thumb lames), Brass (rivets, buckle), Leather (glove, strap).
import bpy, numpy as np, math, os
D = os.environ.get('WORK') or r'T:\knight'
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
V3 = lambda *a: np.array(a, float)
def nz(v): n = np.linalg.norm(v); return v / n if n > 1e-9 else v
def rot(v, axis, ang):
    axis = nz(axis); return v * math.cos(ang) + np.cross(axis, v) * math.sin(ang) + axis * np.dot(axis, v) * (1 - math.cos(ang))
class Mesh:
    def __init__(s): s.v, s.f = [], []
    def add(s, verts, faces):
        b = len(s.v); s.v += [tuple(p) for p in verts]; s.f += [[b + i for i in f] for f in faces]
def grid(nr, nc, wrap=False):
    f = []
    for i in range(nr - 1):
        for j in range(nc - (0 if wrap else 1)):
            j1 = (j + 1) % nc; f.append([i * nc + j, i * nc + j1, (i + 1) * nc + j1, (i + 1) * nc + j])
    return f
def frame(d, ref):
    d = nz(d); u = nz(ref - d * np.dot(ref, d)); return d, u, np.cross(d, u)
def tube(m, pts, radii, sides, cap0=False, cap1=True, ref=V3(0, -1, 0)):
    """closed tube along pts (parallel transport), rounded end cap"""
    pts = [np.asarray(p, float) for p in pts]; n = len(pts); rings = []
    _, u, _ = frame(pts[1] - pts[0], ref)
    for i in range(n):
        d = nz(pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]); u = nz(u - d * np.dot(u, d)); w = np.cross(d, u)
        rings.append([pts[i] + (u * math.cos(2 * math.pi * k / sides) + w * math.sin(2 * math.pi * k / sides)) * radii[i] for k in range(sides)])
    verts = [p for r in rings for p in r]; faces = grid(n, sides, wrap=True)
    if cap1:                                                                    # hemispherical tip
        d = nz(pts[-1] - pts[-2]); base = len(verts); r0 = radii[-1]
        for k in (1, 2):
            a = k / 3 * math.pi / 2
            verts += [pts[-1] + (p - pts[-1]) * math.cos(a) + d * r0 * math.sin(a) for p in rings[-1]]
        verts.append(pts[-1] + d * r0)
        b0 = base - sides
        for k in range(2):
            o0, o1 = b0 + k * sides if k else b0, base + k * sides
            faces += [[o0 + j, o0 + (j + 1) % sides, o1 + (j + 1) % sides, o1 + j] for j in range(sides)]
        tip = len(verts) - 1; o = base + sides
        faces += [[o + j, o + (j + 1) % sides, tip] for j in range(sides)]
    m.add(verts, faces)
def shell(m, p0, p1, dor, r0, r1, half, na=12, nl=3, flare=0.0, ell=1.0):
    """open partial tube (a lame) from p0 to p1, arc of +-half rad centred on the dorsal direction, radius r0 -> r1;
       flare bulges the lower edge out (shingle overlap), ell squashes the side extent (elliptical lames)"""
    d, u, w = frame(np.asarray(p1, float) - np.asarray(p0, float), np.asarray(dor, float))
    verts = []
    for i in range(nl):
        t = i / (nl - 1); c = np.asarray(p0) + (np.asarray(p1) - np.asarray(p0)) * t; r = r0 + (r1 - r0) * t + flare * t * t
        for j in range(na):
            a = -half + 2 * half * j / (na - 1); verts.append(c + u * math.cos(a) * r + w * math.sin(a) * r * ell)
    m.add(verts, grid(nl, na))
def ring_profile(m, prof, nseg, ell=0.82, yoff=0.0):
    """closed lathe with elliptical section: prof = [(z, half-width)]"""
    verts = [V3(a * math.cos(2 * math.pi * k / nseg), yoff + a * ell * math.sin(2 * math.pi * k / nseg), z) for z, a in prof for k in range(nseg)]
    m.add(verts, grid(len(prof), nseg, wrap=True))
def ring_bead(m, z, a, ell, rr, nseg, sides=6):
    pts = [V3(a * math.cos(2 * math.pi * k / nseg), a * ell * math.sin(2 * math.pi * k / nseg), z) for k in range(nseg)]
    verts = []
    for k in range(nseg):
        p = pts[k]; d = nz(pts[(k + 1) % nseg] - pts[k - 1]); outn = nz(V3(p[0], p[1] / ell ** 2, 0)); b = np.cross(d, outn)
        verts += [p + (outn * math.cos(2 * math.pi * s / sides) + b * math.sin(2 * math.pi * s / sides)) * rr for s in range(sides)]
    m.add(verts, grid(nseg + 1, sides, wrap=True)[:0] + [[k * sides + s, k * sides + (s + 1) % sides, ((k + 1) % nseg) * sides + (s + 1) % sides, ((k + 1) % nseg) * sides + s] for k in range(nseg) for s in range(sides)])
def rivet(m, p, n, r=0.18, sides=8):
    n = nz(n); _, u, w = frame(n, perp(n)); verts = [p - n * 0.03]
    for k, (h, rr) in enumerate(((0.0, r), (0.45 * r, 0.85 * r), (0.75 * r, 0.5 * r))):
        verts += [p + n * h + (u * math.cos(2 * math.pi * s / sides) + w * math.sin(2 * math.pi * s / sides)) * rr for s in range(sides)]
    verts.append(p + n * 0.85 * r); f = []
    for k in range(2): f += [[1 + k * sides + s, 1 + k * sides + (s + 1) % sides, 1 + (k + 1) * sides + (s + 1) % sides, 1 + (k + 1) * sides + s] for s in range(sides)]
    top = len(verts) - 1; f += [[1 + 2 * sides + s, 1 + 2 * sides + (s + 1) % sides, top] for s in range(sides)]
    m.add(verts, f)
def perp(d): a = V3(0, 0, 1) if abs(d[2]) < 0.9 else V3(1, 0, 0); return nz(np.cross(d, a))
steel, brass, leather = Mesh(), Mesh(), Mesh()
# ---------------- leather glove ----------------
def palm_hw(z): t = (1.5 - z) / 10.5; return 3.9 + 1.25 * min(1, t * 1.3), 2.15 - 0.35 * t      # half width / half thickness, z 1.5 .. -9
prof = []; nseg = 20
for i in range(12):
    z = 1.5 - 10.4 * i / 11; hw, ht = palm_hw(z)
    prof.append([V3(np.sign(math.cos(a)) * abs(math.cos(a)) ** 0.85 * hw, np.sign(math.sin(a)) * abs(math.sin(a)) ** 0.85 * ht, z) for a in [2 * math.pi * k / nseg for k in range(nseg)]])
z = -9.4; hw, ht = palm_hw(-9.0)                                                 # closed knuckle end
prof.append([V3(np.sign(math.cos(a)) * abs(math.cos(a)) ** 0.85 * hw * 0.85, np.sign(math.sin(a)) * abs(math.sin(a)) ** 0.85 * ht * 0.7, z) for a in [2 * math.pi * k / nseg for k in range(nseg)]])
verts = [p for r in prof for p in r]; faces = grid(len(prof), nseg, wrap=True); c = len(verts); verts.append(V3(0, 0, -9.7))
faces += [[(len(prof) - 1) * nseg + k, (len(prof) - 1) * nseg + (k + 1) % nseg, c] for k in range(nseg)]
leather.add(verts, faces)
FING = {'index': (3.45, -8.9, (4.2, 2.6, 2.0), 0.95, 4), 'middle': (1.15, -9.2, (4.6, 2.9, 2.1), 1.0, 0), 'ring': (-1.15, -9.0, (4.3, 2.7, 2.0), 0.92, -3),
        'little': (-3.35, -8.4, (3.4, 2.1, 1.8), 0.82, -7)}
CURL = (math.radians(14), math.radians(22), math.radians(16))
fingers = {}
for name, (x, zb, segs, r, spread) in FING.items():
    d = rot(V3(0, 0, -1), V3(0, 1, 0), math.radians(-spread)); p = V3(x, 0.15, zb + 0.6); joints = [p]; dirs = []
    for k, L in enumerate(segs):
        d = rot(d, V3(1, 0, 0), CURL[k]); dirs.append(d); joints.append(joints[-1] + d * L)   # curl toward the palm (+Y)
    pts = []; rad = []
    for k in range(3):
        for t in (0.0, 0.5):
            pts.append(joints[k] + (joints[k + 1] - joints[k]) * t); rad.append(r * (1 - 0.08 * (k + t)))
    pts.append(joints[3]); rad.append(r * 0.76)
    tube(leather, pts, rad, 10)
    fingers[name] = (joints, dirs, r)
tb = V3(4.0, 0.9, -2.4); td = nz(V3(0.25, 0.55, -0.8)); tj = [tb, tb + td * 4.0]; tdirs = [td]
td2 = rot(td, V3(0, 1, 0), math.radians(-35)); td2 = rot(td2, nz(np.cross(td2, V3(0, 1, 0))), math.radians(10)); tj.append(tj[-1] + td2 * 3.3); tdirs.append(td2)
tube(leather, [tj[0], tj[0] + (tj[1] - tj[0]) * 0.5, tj[1], tj[1] + (tj[2] - tj[1]) * 0.5, tj[2]], [1.35, 1.2, 1.12, 1.05, 0.92], 10)
# strap round the wrist on the palm side (cuff lining strap) + buckle
shell(leather, V3(0, 0, -0.35), V3(0, 0, -2.05), V3(0, 1, 0), 2.85, 2.85, math.radians(80), na=14, nl=2, ell=1.75)
bk = V3(0, 2.62, -1.2)
for (a0, a1) in (((-0.9, -0.95), (0.9, -0.95)), ((0.9, -0.95), (0.9, 0.95)), ((0.9, 0.95), (-0.9, 0.95)), ((-0.9, 0.95), (-0.9, -0.95))):
    tube(brass, [bk + V3(a0[0], 0.12, a0[1]), bk + V3(a1[0], 0.12, a1[1])], [0.11, 0.11], 6, cap1=False, ref=V3(0, 1, 0))
tube(brass, [bk + V3(0, 0.15, -0.95), bk + V3(0, 0.3, 0.6)], [0.07, 0.07], 6, cap1=False, ref=V3(0, 1, 0))     # tongue
# ---------------- steel ----------------
CUFF = [(9.2, 6.6), (8.0, 6.05), (6.5, 5.45), (5.0, 4.98), (3.5, 4.62), (2.2, 4.42), (1.0, 4.36), (0.2, 4.45), (-0.25, 4.6)]   # bell flare, sheet 08
ring_profile(steel, CUFF, 40)
ring_bead(brass, 9.2, 6.6, 0.82, 0.26, 40); ring_bead(brass, -0.25, 4.6, 0.82, 0.2, 40)       # rolled edges, brass-bound as on the sheet
for k in range(12):                                                               # rivets round the upper band
    a = 2 * math.pi * (k + 0.5) / 12; p = V3(6.2 * math.cos(a), 6.2 * 0.82 * math.sin(a), 8.25); rivet(brass, p + nz(V3(math.cos(a), math.sin(a), 0)) * 0.12, V3(math.cos(a), math.sin(a) / 0.82, 0.25))
for k in range(4):                                                                # and a few on the waist of the cuff (lining rivets)
    a = math.radians(-90 + (k - 1.5) * 40); p = V3(4.38 * math.cos(a), 4.38 * 0.82 * math.sin(a), 2.4); rivet(brass, p + V3(math.cos(a), math.sin(a), 0) * 0.1, V3(math.cos(a), math.sin(a) / 0.82, 0))
# wrist lames + metacarpal lames + knuckle lame: elliptical arcs over the back (-Y)
LAMES = [(-0.45, -1.95, 5.0, 2.5, 115), (-1.45, -3.05, 5.05, 2.4, 110), (-2.5, -5.15, 5.15, 2.25, 80), (-4.55, -7.15, 5.25, 2.15, 80)]
for z0, z1, a, b, hd in LAMES:
    shell(steel, V3(0, 0, z0), V3(0, 0, z1), V3(0, -1, 0), 1.0, 1.0, math.radians(hd), na=22, nl=4, flare=0.06, ell=1.0)
    # scale the unit arc to the ellipse a x b: last added verts
    n0 = len(steel.v) - 22 * 4
    for i in range(n0, len(steel.v)):
        x, y, z = steel.v[i]; t = (z0 - z) / (z0 - z1); s = 1 + 0.05 * t * t
        steel.v[i] = (x * a * s, y * b * s, z)
    for sgn in (-1, 1):
        ang = math.radians(hd - 8) * sgn; p = V3(a * math.sin(ang) * 1.02, -b * math.cos(ang) * 1.02, (z0 + z1) / 2)
        rivet(brass, p, V3(math.sin(ang) / a, -math.cos(ang) / b, 0))
# knuckle lame with 4 bosses
zk0, zk1, na = -6.55, -9.05, 30; verts = []
for i in range(5):
    t = i / 4; z = zk0 + (zk1 - zk0) * t
    for j in range(na):
        a = math.radians(-82 + 164 * j / (na - 1)); x = 5.25 * math.sin(a)
        boss = sum(0.32 * math.exp(-((x - fx) / 0.75) ** 2) for fx in (3.45, 1.15, -1.15, -3.35)) * math.sin(math.pi * t) ** 0.7
        verts.append(V3(x, -(2.32 + boss) * math.cos(a) - 0.08 * t * t, z))
steel.add(verts, grid(5, na))
for fx in (4.6, -4.5):
    rivet(brass, V3(fx, -1.55, -7.9), V3(np.sign(fx) * 0.6, -1, 0))
# finger lames: 3 shells per finger following the curl, tip domes, a rivet on each side of each lame
for name, (joints, dirs, r) in fingers.items():
    for k in range(3):
        p0 = joints[k] - dirs[k] * (0.32 if k else 0.15); p1 = joints[k + 1] + dirs[k] * (0.05 if k < 2 else -0.15)
        dor = nz(V3(0, -1, 0) - dirs[k] * np.dot(V3(0, -1, 0), dirs[k]))
        rr = r * (1 - 0.08 * k) + 0.22
        shell(steel, p0, p1, dor, rr, rr * 1.03, math.radians(100), na=12, nl=3, flare=0.14)
        side = nz(np.cross(dirs[k], dor)); mid = (p0 + p1) / 2
        if k < 2:
            for sgn in (-1, 1): rivet(brass, mid + (dor * math.cos(math.radians(80)) + side * sgn * math.sin(math.radians(80))) * (rr + 0.04), dor * math.cos(math.radians(80)) + side * sgn * math.sin(math.radians(80)), r=0.12, sides=6)
    jd = joints[3]; d = dirs[2]; dor = nz(V3(0, -1, 0) - d * np.dot(V3(0, -1, 0), d)); rr = r * 0.84 + 0.22
    verts = []                                                                  # tip dome over the nail
    for i in range(4):
        a = i / 3 * math.pi / 2
        for j in range(12):
            b_ = math.radians(-100 + 200 * j / 11); side = nz(np.cross(d, dor))
            verts.append(jd - d * 0.15 + (dor * math.cos(b_) + side * math.sin(b_)) * rr * math.cos(a) + d * rr * 0.85 * math.sin(a))
    steel.add(verts, grid(4, 12))
for k in range(2):                                                                # thumb lames
    d = tdirs[k]; dor = nz(V3(0.25, -1, 0) - d * np.dot(V3(0.25, -1, 0), d)); rr = (1.3 if k == 0 else 1.1) + 0.22
    shell(steel, tj[k] - d * 0.2, tj[k + 1] + d * (0.0 if k == 0 else -0.1), dor, rr, rr * 1.02, math.radians(95), na=12, nl=3, flare=0.05)
    rivet(brass, (tj[k] + tj[k + 1]) / 2 + dor * (rr + 0.05), dor, r=0.13, sides=6)
# ---------------- objects ----------------
def make(name, m, thick, bevel):
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(np.asarray(v) * 0.01) for v in m.v], [], m.f); me.update()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    bpy.context.view_layer.objects.active = o; o.select_set(True)
    if thick:
        s = o.modifiers.new('S', 'SOLIDIFY'); s.thickness = thick; s.offset = -1; s.use_even_offset = True
        bpy.ops.object.modifier_apply(modifier='S')
    if bevel:
        b = o.modifiers.new('B', 'BEVEL'); b.width = bevel; b.segments = 1; b.limit_method = 'ANGLE'; b.angle_limit = math.radians(50)
        bpy.ops.object.modifier_apply(modifier='B')
    bpy.ops.object.shade_smooth(); o.select_set(False)
    return o
oS = make('Steel', steel, 0.0013, 0.0004); oB = make('Brass', brass, 0, 0); oL = make('Leather', leather, 0, 0)
for o, mn in ((oS, 'M_EagleSteel'), (oB, 'M_EagleBrass'), (oL, 'M_EagleLeather')):
    mt = bpy.data.materials.get(mn) or bpy.data.materials.new(mn); o.data.materials.append(mt)
for o in (oS, oB, oL): o.select_set(True)
bpy.context.view_layer.objects.active = oS; bpy.ops.object.join(); g = bpy.context.active_object; g.name = 'SM_EagleGauntlets_L'
g.data.name = 'SM_EagleGauntlets_L'
for p in g.data.polygons: p.use_smooth = True
print('TRIS', sum(len(p.vertices) - 2 for p in g.data.polygons), flush=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'gauntlets.blend')); print('GAUNTLETS OK', flush=True)
