# #402 Destrier tack + barding on the destrier skeleton. checkking (Claude), 2026-11-01. Original, procedural.
#   blender -b <work>/destrier_rig.blend -P build_tack.py -- <work>     -> destrier_tack.blend (rig + body + hair + tack)
# Research: handoffs/cavalry-400/RESEARCH.md §3. Pieces (one mesh SK_Destrier_Tack, one material, part id in vertex colour R
# for the bake: 0.1 caparison wool, 0.2 neck cover wool, 0.3 strap leather, 0.4 saddle seat leather, 0.5 steel, 0.6 saddle
# bows (leather over wood, brass edge)):
#   - caparison: a superellipse "tent" shrink-wrapped over the body, then hung straight down from its widest line to a
#     hem at 0.62 m (cloth hangs, it doesn't hug the belly), with a small flare
#   - neck cover: cloth tube over the neck from the withers to behind the ears
#   - war saddle on top: pad, seat, HIGH pommel and HIGH cantle (the knight isn't pushed off when the lance hits),
#     flaps, girth, breast strap, crupper, stirrup leathers + irons
#   - bridle: crownpiece, browband, noseband, cheek pieces, throatlatch, bit rings, reins to the rider's hands
#   - chanfron: steel face plate, ears to nostrils, eye openings
# Weights: copied from the body (nearest face), then smoothed so the cloth doesn't tear.
import bpy, bmesh, numpy as np, math, os, sys
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
D = argv[0] if argv else os.path.dirname(os.path.abspath(bpy.data.filepath))
sc = bpy.context.scene
body = bpy.data.objects['SK_Destrier']; arm = bpy.data.objects['SK_Destrier_Rig']
dg = bpy.context.evaluated_depsgraph_get()
bvh = BVHTree.FromObject(body, dg)
rng = np.random.default_rng(4021)
POLL = Vector((0, -1.13, 1.90)); MUZ = Vector((0, -1.47, 1.33)); TH = (MUZ - POLL).normalized()
NF = (Vector((0, 0, 1)) - Vector((0, 0, 1)).dot(TH) * TH).normalized()
PART = {'cap': 0.1, 'neck': 0.2, 'strap': 0.3, 'seat': 0.4, 'steel': 0.5, 'bow': 0.6}
OUTV, OUTF, OUTP = [], [], []                                   # all tack geometry, part id per vertex

def emit(V, F, part):
    off = len(OUTV); OUTV.extend([tuple(v) for v in V]); OUTP.extend([PART[part]] * len(V))
    OUTF.extend([[i + off for i in f] for f in F])
def surf(p, off):
    loc, nrm, _, _ = bvh.find_nearest(Vector(p))
    return (loc + nrm * off, nrm) if loc is not None else (Vector(p), Vector((0, 0, 1)))

def ribbon(pts, width, thick, part, off=0.012, project=True, n=None):
    """strap: path points (projected onto the body surface + off), flat section width x thick."""
    P = [Vector(p) for p in pts]
    if n:                                                       # resample the polyline evenly
        L = [0.0]
        for a, b in zip(P, P[1:]): L.append(L[-1] + (b - a).length)
        out = []
        for k in range(n):
            s = L[-1] * k / (n - 1); i = max(0, min(len(P) - 2, next((j for j in range(len(L) - 1) if L[j + 1] >= s), len(P) - 2)))
            t = (s - L[i]) / max(L[i + 1] - L[i], 1e-9); out.append(P[i].lerp(P[i + 1], t))
        P = out
    Q, N = [], []
    for p in P:
        if project: q, nn = surf(p, off)
        else: q, nn = p, Vector((0, 0, 1))
        Q.append(q); N.append(nn)
    V, F = [], []
    for i, q in enumerate(Q):
        T = (Q[min(i + 1, len(Q) - 1)] - Q[max(i - 1, 0)]).normalized()
        nn = N[i] - N[i].dot(T) * T
        if nn.length < 1e-6: nn = Vector((0, 0, 1))
        nn.normalize(); sd = nn.cross(T).normalized()
        for a, b in ((-1, 0), (1, 0), (1, 1), (-1, 1)):
            V.append(q + sd * a * width / 2 + nn * b * thick)
    for i in range(len(Q) - 1):
        for k in range(4):
            a0, a1 = 4 * i + k, 4 * i + (k + 1) % 4; F.append([a0, a1, a1 + 4, a0 + 4])
    F.append([3, 2, 1, 0]); m = 4 * (len(Q) - 1); F.append([m, m + 1, m + 2, m + 3])
    emit(V, F, part)

def tube(pts, r, part, seg=8):
    P = [Vector(p) for p in pts]; V, F = [], []
    for i, p in enumerate(P):
        T = (P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]).normalized()
        a = Vector((0, 0, 1)) if abs(T.z) < 0.9 else Vector((1, 0, 0)); u = T.cross(a).normalized(); w = T.cross(u)
        for k in range(seg):
            ang = 2 * math.pi * k / seg; V.append(p + (u * math.cos(ang) + w * math.sin(ang)) * r)
    for i in range(len(P) - 1):
        for k in range(seg):
            a0, a1 = seg * i + k, seg * i + (k + 1) % seg; F.append([a0, a1, a1 + seg, a0 + seg])
    emit(V, F, part)
def ringv(c, normal, R, r, part, seg=14):
    c = Vector(c); n = Vector(normal).normalized(); a = Vector((0, 0, 1)) if abs(n.z) < 0.9 else Vector((1, 0, 0))
    u = n.cross(a).normalized(); w = n.cross(u)
    pts = [c + (u * math.cos(2 * math.pi * k / seg) + w * math.sin(2 * math.pi * k / seg)) * R for k in range(seg + 1)]
    tube(pts, r, part, 6)

def shell(pred, off, thick, part, smooth_iter=2):
    """copy body faces where pred(center, normal) is true, push out along the normal, give it thickness."""
    me = body.data; bm = bmesh.new(); bm.from_mesh(me)
    keep = [f for f in bm.faces if pred(f.calc_center_median(), f.normal)]
    dele = [f for f in bm.faces if f not in set(keep)]
    bmesh.ops.delete(bm, geom=dele, context='FACES')
    loose = [v for v in bm.verts if not v.link_faces]; bmesh.ops.delete(bm, geom=loose, context='VERTS')
    for _ in range(smooth_iter): bmesh.ops.smooth_vert(bm, verts=bm.verts, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
    bm.normal_update()
    for v in bm.verts: v.co = v.co + v.normal * off
    ret = bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=thick)
    V = [v.co.copy() for v in bm.verts]; idx = {v: i for i, v in enumerate(bm.verts)}
    F = [[idx[v] for v in f.verts] for f in bm.faces]; bm.free(); emit(V, F, part)

# ================================================================ caparison (shrink-wrapped tent, then hung)
NPHI, NWALL, NCAP = 120, 30, 9
CY = 0.04; AX, AY, PW = 0.52, 1.28, 3.0
ZH, ZT, ZC = 0.62, 1.38, 1.70
def sup(phi, s=1.0):
    c, sn = math.cos(phi), math.sin(phi)
    return Vector((s * AX * math.copysign(abs(c) ** (2 / PW), c), CY + s * AY * math.copysign(abs(sn) ** (2 / PW), sn), 0))
bm = bmesh.new(); grid = []
for i in range(NWALL):                                          # wall rows, hem (i=0) up to the rim
    z = ZH + (ZT - ZH) * i / (NWALL - 1); grid.append([bm.verts.new(sup(2 * math.pi * j / NPHI) + Vector((0, 0, z))) for j in range(NPHI)])
for k in range(1, NCAP):                                        # cap rings inward and up
    s = 1 - k / NCAP; z = ZT + (ZC - ZT) * math.sin(0.5 * math.pi * k / NCAP)
    grid.append([bm.verts.new(sup(2 * math.pi * j / NPHI, s) + Vector((0, 0, z))) for j in range(NPHI)])
for i in range(len(grid) - 1):
    for j in range(NPHI): bm.faces.new([grid[i][j], grid[i][(j + 1) % NPHI], grid[i + 1][(j + 1) % NPHI], grid[i + 1][j]])
top = bm.verts.new(Vector((0, CY, ZC + 0.02)))
for j in range(NPHI): bm.faces.new([grid[-1][j], grid[-1][(j + 1) % NPHI], top])
cme = bpy.data.meshes.new('cap_tmp'); bm.to_mesh(cme); bm.free()
cob = bpy.data.objects.new('cap_tmp', cme); sc.collection.objects.link(cob)
sw = cob.modifiers.new('SW', 'SHRINKWRAP'); sw.target = body; sw.wrap_method = 'NEAREST_SURFACEPOINT'; sw.wrap_mode = 'OUTSIDE_SURFACE'; sw.offset = 0.035
dg = bpy.context.evaluated_depsgraph_get(); ev = cob.evaluated_get(dg); W = np.array([tuple(v.co) for v in ev.data.vertices])
G = W[:NWALL * NPHI].reshape(NWALL, NPHI, 3).copy()
DIRS, IW = [], []
for j in range(NPHI):                                           # widest line of every column (between 0.98 and 1.45 m)
    d = np.array(sup(2 * math.pi * j / NPHI))[:2] - np.array([0, CY]); d /= np.linalg.norm(d) + 1e-9
    o = (G[:, j, :2] - np.array([0, CY])) @ d
    ok = (G[:, j, 2] > 0.98) & (G[:, j, 2] < 1.45)
    DIRS.append(d); IW.append(int(np.argmax(np.where(ok, o, -9))) if ok.any() else NWALL // 2)
IW = np.array(IW, float)
for _ in range(6): IW = 0.25 * np.roll(IW, 1) + 0.5 * IW + 0.25 * np.roll(IW, -1)   # no steps in the drape line
for j in range(NPHI):                                           # hang every column straight down from its widest line
    d = DIRS[j]; iw = int(round(IW[j])); top_p = G[iw, j].copy()
    for i in range(iw):
        z = ZH + (top_p[2] - ZH) * i / max(iw, 1)
        flare = 0.10 * ((top_p[2] - z) / max(top_p[2] - ZH, 1e-3)) ** 1.5
        fold = 0.012 * math.sin(j * 2 * math.pi / 10) * ((top_p[2] - z) / max(top_p[2] - ZH, 1e-3))   # soft folds in the skirt
        G[i, j, :2] = top_p[:2] + d * (flare + fold); G[i, j, 2] = z
W[:NWALL * NPHI] = G.reshape(-1, 3)
bm = bmesh.new(); bm.from_mesh(cme)
bm.verts.ensure_lookup_table()
for v, p in zip(bm.verts, W): v.co = Vector(p)
bm.normal_update()
# no hole for the neck: the cap stays continuous and the neck cover (further out) overlaps it
for _ in range(2): bmesh.ops.smooth_vert(bm, verts=[v for v in bm.verts if v.co.z > 1.0], factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=-0.008)
V = [v.co.copy() for v in bm.verts]; idx = {v: i for i, v in enumerate(bm.verts)}; F = [[idx[v] for v in f.verts] for f in bm.faces]
bm.free(); emit(V, F, 'cap')
bpy.data.objects.remove(cob); bpy.data.meshes.remove(cme)

# ================================================================ clean projected patches (no ragged shell edges)
def patch(fn, nu, nv, off, thick, part, keep=None):
    """fn(u, v) -> (origin, direction): a ray cast onto the body; hit + normal * off. keep(u, v) trims the corners."""
    V, F, idx = [], [], {}
    for i in range(nu + 1):
        for j in range(nv + 1):
            u, v = i / nu, j / nv
            if keep and not keep(u, v): continue
            o, d = fn(u, v); o = Vector(o); d = Vector(d).normalized()
            hit, nrm, _, _ = bvh.ray_cast(o, d, 3.0)
            if hit is None: hit, nrm = surf(o + d * 0.5, 0.0)[0], Vector((0, 0, 1))
            idx[(i, j)] = len(V); V.append((hit + nrm * off, nrm))
    for i in range(nu):
        for j in range(nv):
            q = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
            if all(k in idx for k in q): F.append([idx[k] for k in q])
    n0 = len(V); P = [p for p, _ in V] + [p + nn * thick for p, nn in V]
    FF = [f[::-1] for f in F] + [[k + n0 for k in f] for f in F]
    edges = {}
    for f in F:
        for a, b in zip(f, f[1:] + f[:1]): edges[(a, b)] = edges.get((a, b), 0) + 1
    for (a, b) in edges:                                              # side walls on the open boundary
        if (b, a) not in edges: FF.append([a, b, b + n0, a + n0])
    emit(P, FF, part)
rounded = lambda r: (lambda u, v: ((abs(2 * u - 1) ** 6 + abs(2 * v - 1) ** 6) ** (1 / 6)) <= 1.0 + 1e-6 if r else True)

# ---- neck cover: a lofted cloth tube from the withers (flared over the caparison's neck hole) to behind the ears
NECKP = [Vector(p) for p in [(0, -0.50, 1.24), (0, -0.78, 1.46), (0, -0.98, 1.68), (0, -1.10, 1.84), (0, -1.15, 1.90)]]
def cr(pts, t):
    s = t * (len(pts) - 1); i = min(int(s), len(pts) - 2); f = s - i
    p0, p1, p2, p3 = pts[max(i - 1, 0)], pts[i], pts[i + 1], pts[min(i + 2, len(pts) - 1)]
    return 0.5 * ((2 * p1) + (-p0 + p2) * f + (2 * p0 - 5 * p1 + 4 * p2 - p3) * f * f + (-p0 + 3 * p1 - 3 * p2 + p3) * f ** 3)
SEGN, ROWN = 40, 30
V, F = [], []
for r in range(ROWN):
    t = 0.02 + 0.93 * r / (ROWN - 1); c = cr(NECKP, t); T = (cr(NECKP, min(t + 0.01, 1)) - cr(NECKP, max(t - 0.01, 0))).normalized()
    up = (Vector((0, 0, 1)) - Vector((0, 0, 1)).dot(T) * T).normalized(); sd = up.cross(T)
    rv = float(np.interp(t, [0, 0.25, 0.6, 0.88, 1.0], [0.34, 0.27, 0.18, 0.13, 0.115])); rl = float(np.interp(t, [0, 0.25, 0.6, 0.88, 1.0], [0.24, 0.19, 0.125, 0.095, 0.09]))
    flare = 0.07 * max(0.0, 1 - t / 0.18)
    for k in range(SEGN):
        a = 2 * math.pi * k / SEGN
        crest = 1 + 0.16 * max(math.cos(a), 0) ** 2 * math.sin(math.pi * min(1.0, t * 1.1)) - 0.06 * max(-math.cos(a), 0)
        rr_v = rv * crest + 0.045 + flare; rr_l = rl * crest + 0.040 + flare
        V.append(c + up * math.cos(a) * rr_v + sd * math.sin(a) * rr_l)
for r in range(ROWN - 1):
    for k in range(SEGN): F.append([r * SEGN + k, r * SEGN + (k + 1) % SEGN, (r + 1) * SEGN + (k + 1) % SEGN, (r + 1) * SEGN + k])
n0 = len(V); V2 = V + [V[i] + (V[i] - cr(NECKP, 0.02 + 0.93 * (i // SEGN) / (ROWN - 1))).normalized() * 0.007 for i in range(n0)]
F2 = [f[::-1] for f in F] + [[k + n0 for k in f] for f in F]
for r in (0, ROWN - 1):
    for k in range(SEGN):
        a, b = r * SEGN + k, r * SEGN + (k + 1) % SEGN; F2.append([a, b, b + n0, a + n0] if r == 0 else [b, a, a + n0, b + n0])
emit(V2, F2, 'neck')

# ================================================================ war saddle (on top of the caparison)
patch(lambda u, v: (((u - 0.5) * 0.54, -0.46 + 0.56 * v, 2.2), (0, 0, -1)), 14, 16, 0.075, 0.035, 'seat', rounded(True))    # seat
patch(lambda u, v: (((u - 0.5) * 0.64, -0.50 + 0.68 * v, 2.2), (0, 0, -1)), 14, 16, 0.058, 0.012, 'strap', rounded(True))   # pad under it
for sg in (1, -1):                                                     # saddle flaps down each side
    patch(lambda u, v, sg=sg: ((sg * 1.2, -0.44 + 0.50 * u, 1.06 + 0.38 * v), (-sg, 0, 0)), 12, 10, 0.055, 0.012, 'strap', rounded(True))
def bow(yc, height, rad, wrap, open_dir):
    """pommel / cantle: a thick U-shaped arch over the back; its sides wrap toward the rider, the middle rises."""
    V, F = [], []; K = 18
    for k in range(K + 1):
        a = math.pi * k / K; x = -rad * math.cos(a); y = yc - open_dir * wrap * (1 - math.sin(a))
        hit, nrm, _, _ = bvh.ray_cast(Vector((x, y, 2.4)), Vector((0, 0, -1)), 3.0)
        z0 = (hit.z if hit is not None else 1.45) + 0.075
        lift = height * (0.25 + 0.75 * math.sin(a) ** 1.5)
        for zz in (z0, z0 + lift):
            for dy in (0.0, 0.045):
                V.append(Vector((x * (1 + 0.08 * (zz - z0) / max(lift, 1e-3)), y + open_dir * (dy + 0.05 * (zz - z0) / 0.3), zz)))
    for k in range(K):
        b0, b1 = 4 * k, 4 * (k + 1)
        for (p, q) in ((0, 2), (2, 3), (3, 1), (1, 0)):              # inner face, top, outer face, bottom
            F.append([b0 + p, b1 + p, b1 + q, b0 + q])
    F.append([0, 2, 3, 1]); e = 4 * K; F.append([e + 1, e + 3, e + 2, e])
    emit(V, F, 'bow')
bow(-0.44, 0.17, 0.19, 0.06, -1)                                      # pommel (front), sides sweep back
bow(0.07, 0.24, 0.23, 0.14, 1)                                        # cantle: the backrest wrapping the hips
# girth, breast strap, crupper
ribbon([(x * 0.36, -0.36, 1.12 + 0.36 * math.cos(math.pi * x / 2)) for x in np.linspace(-1, 1, 3)], 0.09, 0.008, 'strap', 0.05)
ring_pts = []
for k in range(41):
    a = math.pi * 2 * k / 40; ring_pts.append((0.42 * math.sin(a), -0.36, 1.12 + 0.42 * math.cos(a)))
ribbon(ring_pts, 0.09, 0.008, 'strap', 0.048, n=60)
ribbon([(0.30, -0.42, 1.34), (0.30, -0.70, 1.22), (0.20, -0.95, 1.12), (0.0, -1.05, 1.10), (-0.20, -0.95, 1.12), (-0.30, -0.70, 1.22), (-0.30, -0.42, 1.34)], 0.06, 0.008, 'strap', 0.045, n=60)
ribbon([(0, 0.10, 1.62), (0, 0.40, 1.58), (0, 0.75, 1.52), (0, 0.95, 1.44), (0, 1.02, 1.36)], 0.05, 0.007, 'strap', 0.042, n=40)
for sg in (1, -1):                                               # hip straps of the crupper
    ribbon([(0.0, 0.62, 1.58), (0.2 * sg, 0.62, 1.48), (0.34 * sg, 0.66, 1.25), (0.32 * sg, 0.70, 1.05)], 0.04, 0.006, 'strap', 0.042, n=24)
# stirrup leathers + irons (long, straight-legged war seat)
for sg in (1, -1):
    top, _ = surf((0.32 * sg, -0.25, 1.45), 0.06)
    bot = Vector((top.x + 0.05 * sg, top.y, 0.86))
    ribbon([top, top.lerp(bot, 0.5), bot], 0.035, 0.006, 'strap', project=False, n=8)
    st = [bot + Vector((0.0, 0.07 * math.sin(a), -0.13 * (0.5 - 0.5 * math.cos(a)))) for a in np.linspace(0, 2 * math.pi, 22)]
    tube(st, 0.008, 'steel', 6)
    tube([bot + Vector((0, -0.06, -0.125)), bot + Vector((0, 0.06, -0.125))], 0.012, 'steel', 6)

# ================================================================ bridle + reins
def head_ring(t, extra=0.012, w=0.025, part='strap', squash=1.0):
    c = POLL + TH * t; X = Vector((1, 0, 0)); pts = []
    for k in range(33):
        a = 2 * math.pi * k / 32; d = (NF * math.cos(a) + X * math.sin(a) * squash).normalized()
        pts.append(c + d * 0.6)
    pts = [surf(p, extra)[0] for p in pts]
    ribbon(pts, w, 0.006, part, project=False, n=40)
def head_path(ts_off, w=0.022):
    pts = [POLL + TH * t + NF * nf + Vector((x, 0, 0)) for t, nf, x in ts_off]
    ribbon(pts, w, 0.006, 'strap', 0.012, n=20)
head_ring(0.02, 0.014)                                           # crownpiece behind the ears + throatlatch run
head_ring(0.72, 0.012, 0.03)                                     # noseband
for sg in (1, -1):
    head_path([(0.02, 0.0, 0.11 * sg), (0.25, -0.02, 0.12 * sg), (0.55, -0.05, 0.10 * sg), (0.80, -0.06, 0.085 * sg)])   # cheek pieces
    bitc, _ = surf(POLL + TH * 0.84 - NF * 0.07 + Vector((0.09 * sg, 0, 0)), 0.02)
    ringv(bitc + Vector((0.012 * sg, 0, 0)), (1, 0, 0), 0.032, 0.005, 'steel')
    # rein: bit ring -> the rider's hand above the pommel, sagging a little
    hand = Vector((0.07 * sg, -0.52, 1.80)); mid = bitc.lerp(hand, 0.5) + Vector((0, 0, -0.10))
    pts = [bitc.lerp(mid, s) if s <= 1 else mid.lerp(hand, s - 1) for s in np.linspace(0, 2, 24)]
    ribbon(pts, 0.022, 0.005, 'strap', project=False)
tube([surf(POLL + TH * 0.84 - NF * 0.07 + Vector((0.09, 0, 0)), 0.02)[0], surf(POLL + TH * 0.84 - NF * 0.07 + Vector((-0.09, 0, 0)), 0.02)[0]], 0.007, 'steel', 6)  # bit mouthpiece
head_path([(0.04, 0.10, -0.11), (0.02, 0.13, 0.0), (0.04, 0.10, 0.11)], 0.025)                  # browband

# ================================================================ chanfron (steel face plate)
def chan_ray(u, v):
    t = 0.04 + 0.52 * u; ang = math.radians(-62 + 124 * v) * (1 - 0.25 * u)      # narrower toward the nose
    d = (NF * math.cos(ang) + Vector((1, 0, 0)) * math.sin(ang)).normalized()
    return POLL + TH * t + d * 0.5, -d
patch(chan_ray, 22, 14, 0.024, 0.004, 'steel', lambda u, v: not (0.18 < u < 0.34 and (v < 0.08 or v > 0.92)))   # notches at the eyes

# ================================================================ object, UVs, weights
me = bpy.data.meshes.new('SK_Destrier_Tack'); me.from_pydata(OUTV, [], OUTF); me.update()
me.validate(clean_customdata=False)
tack = bpy.data.objects.new('SK_Destrier_Tack', me); sc.collection.objects.link(tack)
ca = me.color_attributes.new('Part', 'FLOAT_COLOR', 'POINT')
pc = np.zeros((len(me.vertices), 4), np.float32); pc[:, 0] = np.array(OUTP[:len(me.vertices)]); pc[:, 3] = 1
ca.data.foreach_set('color', pc.ravel())
for p in me.polygons: p.use_smooth = True
for o in sc.objects: o.select_set(False)
tack.select_set(True); bpy.context.view_layer.objects.active = tack
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.002, area_weight=0.0, scale_to_bounds=False)
bpy.ops.uv.select_all(action='SELECT'); bpy.ops.uv.average_islands_scale(); bpy.ops.uv.pack_islands(rotate=True, margin=0.003)
bpy.ops.object.mode_set(mode='OBJECT')
for vg in body.vertex_groups: tack.vertex_groups.new(name=vg.name)
dt = tack.modifiers.new('DT', 'DATA_TRANSFER'); dt.object = body; dt.use_vert_data = True; dt.data_types_verts = {'VGROUP_WEIGHTS'}
dt.vert_mapping = 'POLYINTERP_NEAREST'; dt.layers_vgroup_select_src = 'ALL'; dt.layers_vgroup_select_dst = 'NAME'
bpy.ops.object.modifier_apply(modifier='DT')
# reins + stirrups: by part: stirrups ride the saddle (spine_01); reins blend head -> spine_02
bpy.ops.object.mode_set(mode='WEIGHT_PAINT'); bpy.ops.object.vertex_group_smooth(group_select_mode='ALL', factor=0.5, repeat=4)
bpy.ops.object.vertex_group_normalize_all(lock_active=False); bpy.ops.object.mode_set(mode='OBJECT')
co = np.array([tuple(v.co) for v in me.vertices])
sp1 = tack.vertex_groups['spine_01']; sp2 = tack.vertex_groups['spine_02']; hd = tack.vertex_groups['head']
for i, p in enumerate(co):
    if p[2] < 0.95 and abs(p[0]) > 0.3 and -0.4 < p[1] < -0.1 and p[2] > 0.6:     # stirrup leathers + irons hang free of the legs
        for vg in tack.vertex_groups: vg.remove([i])
        sp1.add([i], 1.0, 'REPLACE')
mo = tack.modifiers.new('Armature', 'ARMATURE'); mo.object = arm; tack.parent = arm
print('TACK verts', len(me.vertices), 'tris', sum(len(p.vertices) - 2 for p in me.polygons), flush=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'destrier_tack.blend'))
print('TACK OK', flush=True)
