# Meadow flora kit (#352 for #351, TGA): blender -b --factory-startup -P build_flora.py   (env WORK, needs out/tex/T_MeadowFlora_* from tex_flora.py)
# Original procedural plants of a medieval European meadow. Real geometry for flowers and fern (no alpha), masked leaf-spray
# cards (baked from real leaf geometry) for the two bushes, 4 LODs each (LOD3 = crossed impostor cards baked from LOD0).
#   SM_Flower_Daisy|Poppy|Yarrow|Cornflower_A/B/C, SM_Bush_Hawthorn|Hazel_A/B, SM_Fern_Bracken_A      (pivot = base on the ground, Z up)
# Materials: M_MeadowFlora (atlas 1, opaque, two-sided foliage) and M_MeadowCards (atlas 2 T_MeadowCards_*, masked).
# Vertex colour 'Col' for wind: R = stiffness (1 rooted .. 0 free tip), G = phase (random per stem / branch), B = flutter (leaf / petal tips).
import bpy, bmesh, numpy as np, os, math, json
from mathutils import Vector, Matrix
D = os.environ.get('WORK') or os.path.dirname(os.path.abspath(__file__)); TEX = os.path.join(D, 'out', 'tex'); FBX = os.path.join(D, 'out', 'fbx')
os.makedirs(FBX, exist_ok=True)
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
sc = bpy.context.scene
# stable string hash (str hash() is salted per process)
def H(s): return sum((i + 1) * ord(c) for i, c in enumerate(s)) % 100003
def rng(*key): return np.random.default_rng([H(k) if isinstance(k, str) else int(k) for k in key])
V3 = lambda *a: np.array(a, float)
def nz(v): n = np.linalg.norm(v); return v / n if n > 1e-9 else v
def perp(d): a = V3(0, 0, 1) if abs(d[2]) < 0.9 else V3(1, 0, 0); return nz(np.cross(d, a))
def rot(v, axis, ang):                                                          # Rodrigues
    axis = nz(axis); return v * math.cos(ang) + np.cross(axis, v) * math.sin(ang) + axis * np.dot(axis, v) * (1 - math.cos(ang))
M1 = 10 / 512
def uv1(tile, s, t):                                                            # atlas 1: 4x4 tiles
    c, r = tile % 4, tile // 4; return ((c + M1 + s * (1 - 2 * M1)) / 4, (r + M1 + t * (1 - 2 * M1)) / 4)
class Mesh:
    def __init__(s): s.v, s.f, s.uv, s.col, s.mat, s.nrm = [], [], [], [], [], []
    def add(s, verts, faces, uvs, cols, mat=0, nrms=None):
        b = len(s.v); s.v += [tuple(p) for p in verts]; s.uv += uvs; s.col += cols
        s.nrm += nrms if nrms is not None else [None] * len(verts)
        for f in faces: s.f.append([b + i for i in f]); s.mat.append(mat)
    def tris(s): return sum(len(f) - 2 for f in s.f)
def grid_faces(nr, nc):                                                         # nr rows x nc cols of vertices
    return [[i * nc + j, i * nc + j + 1, (i + 1) * nc + j + 1, (i + 1) * nc + j] for i in range(nr - 1) for j in range(nc - 1)]
def tube(m, pts, radii, sides, tile, R, G, cap=False):
    pts = [np.asarray(p, float) for p in pts]; n = len(pts); L = [0.0]
    for i in range(1, n): L.append(L[-1] + np.linalg.norm(pts[i] - pts[i - 1]))
    tot = L[-1] or 1; verts, uvs, cols = [], [], []; nrm = perp(nz(pts[1] - pts[0]))
    for i in range(n):
        d = nz(pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]); nrm = nz(nrm - d * np.dot(nrm, d)); bi = np.cross(d, nrm)
        for k in range(sides + 1):
            a = 2 * math.pi * k / sides; verts.append(pts[i] + (nrm * math.cos(a) + bi * math.sin(a)) * radii[i])
            uvs.append(uv1(tile, L[i] / tot, k / sides)); cols.append((R[i], G, 0.0, 1.0))
    m.add(verts, grid_faces(n, sides + 1), uvs, cols)
    if cap:                                                                     # close the cut end (bush stems)
        b = len(m.v); m.add([pts[-1]], [], [uv1(tile, 1, 0.5)], [(R[-1], G, 0.0, 1.0)])
        base = b - (sides + 1)
        for k in range(sides): m.f.append([base + k, base + k + 1, b]); m.mat.append(0)
def blade(m, base, d, side, L, wfun, nl, cols, tile, R0, R1, G, droop=0.0, fold=0.0, twist=0.0, crumple=0.0, tips=0.0, seed=0, B0=0.0, mat=0, uvf=None):
    """leaf / petal / pinna: spine from base along d bending by droop (rad) around side; width wfun(s) (m, half-width);
       fold lifts the edges (V or cup), tips shortens alternate columns (toothed floret ends)"""
    d, side = nz(np.asarray(d, float)), nz(np.asarray(side, float)); up = np.cross(side, d); r = np.random.default_rng(seed)
    verts, uvs, colz = [], [], []; p = np.asarray(base, float).copy(); ds = L / (nl - 1); dd = d.copy(); sd = side.copy(); nn = up.copy()
    for i in range(nl):
        s = i / (nl - 1)
        if i:
            ang = droop / (nl - 1); dd = rot(dd, sd, ang); nn = rot(nn, sd, ang); tw = twist / (nl - 1); sd = rot(sd, dd, tw); nn = rot(nn, dd, tw)
            p = p + dd * ds
        for j in range(cols):
            a = -1 + 2 * j / (cols - 1); w = wfun(s); sl = 1.0
            if tips and i == nl - 1 and j % 2 == 1: sl = 1 - tips
            q = p - dd * ds * (1 - sl) * (i == nl - 1) + sd * a * w + nn * (fold * w * a * a) + nn * (crumple * w * (r.random() - 0.5) * (0 < i))
            verts.append(q); uvs.append(uvf(s, 0.5 + 0.5 * a) if uvf else uv1(tile, s, 0.5 + 0.5 * a))
            colz.append((R0 + (R1 - R0) * s, G, B0 + (1 - B0) * s, 1.0))
    m.add(verts, grid_faces(nl, cols), uvs, colz, mat)
def disc(m, c, n, radius, segs, rings, tile, R, G, dome=0.0):
    n = nz(np.asarray(n, float)); u = perp(n); w = np.cross(n, u); verts, uvs, cols = [np.asarray(c, float) + n * dome * radius], [uv1(tile, 0.5, 0.5)], [(R, G, 0.0, 1.0)]
    for ri in range(1, rings + 1):
        rr = ri / rings
        for k in range(segs):
            a = 2 * math.pi * k / segs; verts.append(np.asarray(c) + (u * math.cos(a) + w * math.sin(a)) * radius * rr + n * dome * radius * (1 - rr * rr))
            uvs.append(uv1(tile, 0.5 + 0.5 * rr * math.cos(a), 0.5 + 0.5 * rr * math.sin(a))); cols.append((R, G, 0.2 * rr, 1.0))
    f = [[0, 1 + k, 1 + (k + 1) % segs] for k in range(segs)]
    for ri in range(1, rings):
        o0, o1 = 1 + (ri - 1) * segs, 1 + ri * segs
        f += [[o0 + k, o1 + k, o1 + (k + 1) % segs, o0 + (k + 1) % segs] for k in range(segs)]
    m.add(verts, f, uvs, cols)
def lathe(m, base, ax, prof, sides, tile, R, G):
    """prof = [(h, r)] in metres along ax; s = h / max h"""
    ax = nz(np.asarray(ax, float)); u = perp(ax); w = np.cross(ax, u); hm = max(h for h, _ in prof) or 1; verts, uvs, cols = [], [], []
    for h, rr in prof:
        for k in range(sides + 1):
            a = 2 * math.pi * k / sides; verts.append(np.asarray(base) + ax * h + (u * math.cos(a) + w * math.sin(a)) * rr)
            uvs.append(uv1(tile, h / hm, k / sides)); cols.append((R, G, 0.0, 1.0))
    m.add(verts, grid_faces(len(prof), sides + 1), uvs, cols)
def stem_pts(base, h, lean_dir, lean, bend, n, wob=0.0, r=None, hook=0.0):
    pts = []; ld = nz(V3(lean_dir[0], lean_dir[1], 0))
    for i in range(n):
        s = i / (n - 1); p = V3(base[0], base[1], 0) + V3(0, 0, h * s) + ld * (lean * s + bend * s * s) * h
        if r is not None and wob: p = p + V3(*(r.normal(0, wob, 2)), 0) * math.sin(math.pi * s)
        if hook and s > 0.8: k = (s - 0.8) / 0.2; p = p + ld * hook * math.sin(k * 1.4) - V3(0, 0, hook * (1 - math.cos(k * 1.6)) * 1.4)
        pts.append(p)
    return pts
LOD = {0: dict(sides=6, nl=1.0, k=1.0), 1: dict(sides=4, nl=0.7, k=0.6), 2: dict(sides=3, nl=0.5, k=0.35)}
def nlod(n, lod): return max(2, int(round(n * LOD[lod]['nl'])))
def keep(i, n, lod):                                                            # deterministic thinning: which of n elements survive a LOD
    k = LOD[lod]['k']; return (i * 0.618034) % 1.0 < k or n * k < 1.5 and i == 0
def comp(n, lod): return (1.0 / math.sqrt(max(LOD[lod]['k'], 1e-3))) if n > 2 else 1.0   # survivors grow to keep coverage
def rosette(m, r_, lod, cnt, Lr, Wr, wfun, tile, seed, stiff=1.0):
    for i in range(cnt):
        if not keep(i, cnt, lod): continue
        q = rng(seed, i); a = 2 * math.pi * i / cnt + q.normal(0, 0.25); d = V3(math.cos(a), math.sin(a), 0.5 + 0.4 * q.random())
        L = Lr * (0.7 + 0.5 * q.random()); sc_ = comp(cnt, lod)
        blade(m, V3(0, 0, 0.005) + nz(d) * 0.01, d, perp(nz(d)), L * min(sc_, 1.3), lambda s, W=Wr * sc_ ** 0.5: W * wfun(s), nlod(7, lod), 3 if lod < 2 else 2 + 1, 6,
              stiff, 0.25, q.random(), droop=1.0 + 0.5 * q.random(), fold=0.25, twist=q.normal(0, 0.3), seed=H('ro') + i)
# ------------------------------------------------------------------ species
def spoon(s): return (0.25 + 0.75 * math.sin(math.pi * min(1, s * 1.15)) ** 0.8) * (1 + 0.12 * math.sin(s * 40)) * (s < 0.995)
def lance(s): return math.sin(math.pi * s) ** 0.7 + 0.02
def lobed(s): return (0.15 + 0.85 * math.sin(math.pi * s) ** 0.6) * (0.4 + 0.6 * abs(math.sin(s * math.pi * 5.5))) + 0.02
def feather(s): return (1 - s) ** 0.4 * (0.25 + 0.75 * abs(math.sin(s * math.pi * 12)) ** 0.5) + 0.02
def head_dir(r, lean_dir):
    ld = nz(V3(lean_dir[0], lean_dir[1], 0)); return nz(V3(0, 0, 1) + ld * (0.3 + 0.5 * r.random()))
def flower_stems(m, sp, var, lod, heads, hmin, hmax, rad, spread):
    out = []
    for k in range(heads):
        q = rng(sp, var, 'stem', k); a = 2 * math.pi * q.random(); rr = spread * math.sqrt(q.random())
        base = V3(rr * math.cos(a), rr * math.sin(a), 0); ld = V3(math.cos(a + q.normal(0, 0.5)), math.sin(a + q.normal(0, 0.5)), 0)
        h = hmin + (hmax - hmin) * q.random(); n = nlod(10, lod); pts = stem_pts(base, h, ld, 0.08 + 0.15 * q.random(), 0.06 * q.normal(), n, 0.01, q)
        R = [1 - i / (n - 1) for i in range(n)]; G = q.random()
        tube(m, pts, [rad * (1 - 0.35 * i / (n - 1)) for i in range(n)], LOD[lod]['sides'], 7, R, G)
        out.append((pts, ld, G, q, h))
    return out
def daisy(var, lod):
    m = Mesh(); heads = {'A': 3, 'B': 5, 'C': 7}[var]; rosette(m, None, lod, 9, 0.09, 0.013, spoon, 6, H('dz' + var))
    for pts, ld, G, q, h in flower_stems(m, 'daisy', var, lod, heads, 0.32, 0.6, 0.0022, 0.06):
        for j in range(3):                                                       # clasping stem leaves
            if not keep(j, 3, lod) or lod == 2: continue
            s = 0.15 + 0.2 * j; p = pts[int(s * (len(pts) - 1))]; a = q.random() * 6.28; d = nz(V3(math.cos(a), math.sin(a), 0.9))
            blade(m, p, d, perp(d), 0.045 * (1 - 0.25 * j), lambda s_: 0.006 * lance(s_) * (1 + 0.15 * math.sin(s_ * 30)), nlod(5, lod), 3, 6, 1 - s, 0.3, G, droop=0.6, fold=0.3)
        top = pts[-1]; hd = head_dir(q, ld)
        lathe(m, top - hd * 0.004, hd, [(0, 0.002), (0.004, 0.007), (0.007, 0.0085)], LOD[lod]['sides'] + 2, 15, 0.0, G)
        disc(m, top + hd * 0.007, hd, 0.009, 10 if lod < 2 else 6, 2 if lod == 0 else 1, 1, 0.0, G, dome=0.35)
        np_ = {0: 22, 1: 16, 2: 11}[lod]; u = perp(hd); w = np.cross(hd, u)
        for i in range(np_):
            a = 2 * math.pi * (i + 0.3 * q.random()) / np_; rd = u * math.cos(a) + w * math.sin(a); pb = top + hd * 0.006 + rd * 0.008
            d = nz(rd + hd * (0.15 + 0.2 * q.random())); W = 0.0022 * (22 / np_) ** 0.7
            blade(m, pb, d, np.cross(hd, rd), 0.019 * (0.9 + 0.2 * q.random()), lambda s_, W=W: W * (0.55 + 0.45 * math.sin(math.pi * min(1, s_ * 0.7 + 0.3))),
                  4 if lod < 2 else 3, 3 if lod < 2 else 2, 0, 0.0, 0.0, G, droop=0.25 + 0.35 * q.random(), fold=-0.15, tips=0.12, B0=0.5)
    return m
def poppy(var, lod):
    m = Mesh(); nf, nb = {'A': (2, 1), 'B': (3, 2), 'C': (4, 1)}[var]; rosette(m, None, lod, 7, 0.13, 0.022, lobed, 6, H('pp' + var))
    st = flower_stems(m, 'poppy', var, lod, nf + nb, 0.35, 0.65, 0.0026, 0.07)
    for k, (pts, ld, G, q, h) in enumerate(st):
        if k < 2 and lod < 2:                                                   # one stem leaf on the first stems
            p = pts[len(pts) // 3]; d = nz(V3(-ld[0], -ld[1], 0.8))
            blade(m, p, d, perp(d), 0.07, lambda s_: 0.012 * lobed(s_), nlod(6, lod), 3, 6, 0.7, 0.3, G, droop=0.7, fold=0.2)
        top = pts[-1]; hd = head_dir(q, ld)
        if k >= nf:                                                              # nodding hairy bud: re-run the stem with a hook
            hk = pts[-1] + V3(ld[0], ld[1], 0) * 0.03 - V3(0, 0, 0.035); bd = nz(V3(ld[0], ld[1], 0) * 0.3 - V3(0, 0, 1))
            tube(m, [pts[-1], pts[-1] + V3(ld[0], ld[1], 0) * 0.02 + V3(0, 0, 0.01), hk], [0.0022, 0.002, 0.0018], LOD[lod]['sides'], 7, [0.1, 0.05, 0.0], G)
            lathe(m, hk, bd, [(0, 0.003), (0.006, 0.008), (0.014, 0.0085), (0.02, 0.005), (0.023, 0.0005)], LOD[lod]['sides'] + 2, 15, 0.0, G); continue
        if var == 'C' and k == nf - 1:                                          # one ripe seed capsule
            lathe(m, top, hd, [(0, 0.002), (0.004, 0.006), (0.012, 0.0075), (0.016, 0.006), (0.017, 0.0065), (0.018, 0.001)], LOD[lod]['sides'] + 2, 3, 0.0, G); continue
        lathe(m, top, hd, [(0, 0.0025), (0.003, 0.004), (0.008, 0.0045), (0.011, 0.0038), (0.0125, 0.004), (0.013, 0.0005)], LOD[lod]['sides'] + 2, 3, 0.0, G)
        u = perp(hd); w = np.cross(hd, u); a0 = q.random() * 6.28; cup = 0.5 + 0.4 * q.random()
        for i in range(4):
            a = a0 + i * math.pi / 2 + (0.0 if i % 2 == 0 else 0.15); rd = u * math.cos(a) + w * math.sin(a); inner = i % 2
            d = nz(rd * (1 - 0.35 * inner) + hd * (0.5 + 0.3 * inner)); L = 0.034 * (0.9 if inner else 1.05)
            blade(m, top + hd * 0.002 + rd * 0.002, d, np.cross(hd, rd), L, lambda s_: 0.026 * (0.2 + 0.8 * math.sin(math.pi * min(1, s_ * 0.75 + 0.12)) ** 0.5) * (s_ < 0.999) + 0.002,
                  6 if lod == 0 else 4, 7 if lod == 0 else (5 if lod == 1 else 3), 2, 0.0, 0.0, G, droop=-cup * 0.5 + (0.7 if not inner else 0.2), fold=0.35,
                  crumple=0.25 if lod == 0 else 0.0, seed=H('pt') + k * 7 + i, B0=0.4)
    return m
def yarrow(var, lod):
    m = Mesh(); heads = {'A': 3, 'B': 4, 'C': 6}[var]; rosette(m, None, lod, 8, 0.11, 0.009, feather, 6, H('ya' + var))
    for pts, ld, G, q, h in flower_stems(m, 'yarrow', var, lod, heads, 0.3, 0.58, 0.0024, 0.05):
        for j in range(3):
            if lod == 2 or not keep(j, 3, lod): continue
            p = pts[int((0.2 + 0.2 * j) * (len(pts) - 1))]; a = q.random() * 6.28; d = nz(V3(math.cos(a), math.sin(a), 0.7))
            blade(m, p, d, perp(d), 0.06, lambda s_: 0.007 * feather(s_), nlod(9, lod), 3, 6, 0.6, 0.3, G, droop=0.5, fold=0.2)
        top = pts[-1]; R0 = 0.6 * 1.0; nray = {0: 6, 1: 4, 2: 3}[lod]; ends = []
        for i in range(nray):                                                   # corymb rays: short stalks spreading to a flat top
            a = 2 * math.pi * i / nray + q.random(); rr = 0.012 + 0.012 * q.random(); e = top + V3(math.cos(a) * rr, math.sin(a) * rr, 0.025 + 0.008 * q.random())
            tube(m, [top - V3(0, 0, 0.02), top + V3(math.cos(a) * rr * 0.3, math.sin(a) * rr * 0.3, 0.012), e], [0.0012, 0.001, 0.0008], 3, 7, [0.05, 0.02, 0.0], G)
            ends.append(e)
        nfl = {0: 46, 1: 24, 2: 12}[lod]; rad = 0.0026 * math.sqrt(46 / nfl); ctr = top + V3(0, 0, 0.032)
        for i in range(nfl):                                                    # florets on a dome, golden-angle spiral
            rr = 0.03 * math.sqrt((i + 0.5) / nfl); a = i * 2.39996; p = ctr + V3(math.cos(a) * rr, math.sin(a) * rr, -18 * rr * rr + q.normal(0, 0.0015))
            n_ = nz(V3(math.cos(a) * rr * 8, math.sin(a) * rr * 8, 1)); disc(m, p, n_, rad, 5, 1, 5, 0.0, G, dome=0.15)
    return m
def cornflower(var, lod):
    m = Mesh(); heads = {'A': 2, 'B': 3, 'C': 5}[var]; rosette(m, None, lod, 5, 0.08, 0.005, lance, 6, H('cf' + var))
    for pts, ld, G, q, h in flower_stems(m, 'cornflower', var, lod, heads, 0.4, 0.72, 0.0018, 0.05):
        for j in range(4):                                                      # narrow linear stem leaves
            if not keep(j, 4, lod): continue
            p = pts[int((0.1 + 0.18 * j) * (len(pts) - 1))]; a = q.random() * 6.28; d = nz(V3(math.cos(a), math.sin(a), 1.4))
            blade(m, p, d, perp(d), 0.07 - 0.01 * j, lambda s_: 0.0028 * lance(s_), nlod(5, lod), 3 if lod < 2 else 2, 6, 0.8 - 0.15 * j, 0.3, G, droop=0.5, fold=0.4)
        tops = [(pts[-1], ld)]
        if q.random() < 0.7:                                                    # side branch with a second (bud or flower) head
            b0 = pts[int(0.65 * (len(pts) - 1))]; bl = V3(-ld[1], ld[0], 0) * (1 if q.random() < 0.5 else -1)
            bp = stem_pts(b0, 0.14, bl, 0.35, 0.05, nlod(6, lod)); bp = [p + V3(0, 0, b0[2]) for p in bp]
            tube(m, bp, [0.0014] * len(bp), max(3, LOD[lod]['sides'] - 1), 7, [0.35 * (1 - i / (len(bp) - 1)) for i in range(len(bp))], G)
            tops.append((bp[-1], bl))
        for t_i, (top, l2) in enumerate(tops):
            hd = head_dir(q, l2); lathe(m, top, hd, [(0, 0.0015), (0.004, 0.0042), (0.010, 0.0058), (0.0135, 0.0042)], LOD[lod]['sides'] + 2, 15, 0.0, G)
            if t_i == 1 and q.random() < 0.5: continue                          # bud only
            u = perp(hd); w = np.cross(hd, u); nfl = {0: 9, 1: 7, 2: 5}[lod]; c = top + hd * 0.012
            disc(m, c, hd, 0.0045, 7, 1, 4, 0.0, G, dome=0.6)
            for i in range(nfl):
                a = 2 * math.pi * i / nfl + q.normal(0, 0.1); rd = u * math.cos(a) + w * math.sin(a); d = nz(rd + hd * (0.35 + 0.2 * q.random()))
                blade(m, c + rd * 0.003, d, np.cross(hd, rd), 0.016 * (0.9 + 0.2 * q.random()), lambda s_: 0.0012 + 0.0042 * s_ ** 1.3,
                      4 if lod < 2 else 3, 5 if lod == 0 else 3, 4, 0.0, 0.0, G, droop=0.3, fold=0.5, tips=0.25 if lod == 0 else 0.0, B0=0.5)
    return m
def bracken(var, lod):
    m = Mesh(); nfr = 6
    for k in range(nfr):
        if lod == 2 and k % 3 == 2: continue
        q = rng('bracken', var, k); a = 2 * math.pi * k / nfr + q.normal(0, 0.3); ld = V3(math.cos(a), math.sin(a), 0)
        base = ld * 0.06 * q.random(); hs = 0.35 + 0.25 * q.random(); n = nlod(8, lod)
        sp = stem_pts(base, hs, ld, 0.25, 0.2, n, 0.0); G = q.random()
        tube(m, sp, [0.0045 * (1 - 0.5 * i / (n - 1)) for i in range(n)], max(3, LOD[lod]['sides'] - 1), 14, [1 - 0.5 * i / (n - 1) for i in range(n)], G)
        # blade: rachis arching outwards, near horizontal
        L = 0.55 + 0.25 * q.random(); nr = nlod(10, lod); rp = [sp[-1]]; d = nz(ld * 0.9 + V3(0, 0, 0.5))
        for i in range(1, nr): d = rot(d, np.cross(d, V3(0, 0, 1)), -0.06); rp.append(rp[-1] + d * L / (nr - 1))
        tube(m, rp, [0.0025 * (1 - 0.7 * i / (nr - 1)) for i in range(nr)], 3, 14, [0.5 - 0.5 * i / (nr - 1) for i in range(nr)], G)
        npair = {0: 9, 1: 7, 2: 5}[lod]
        for i in range(npair):
            s = 0.08 + 0.85 * i / npair; idx = s * (nr - 1); p = rp[int(idx)] + (rp[min(int(idx) + 1, nr - 1)] - rp[int(idx)]) * (idx % 1)
            dd = nz(rp[min(int(idx) + 1, nr - 1)] - rp[int(idx)]); side = nz(np.cross(dd, V3(0, 0, 1))); Lp = L * 0.42 * (1 - s) ** 0.8 + 0.03
            for sgn in (-1, 1):
                pd = nz(side * sgn + dd * 0.55); ps = nz(np.cross(V3(0, 0, 1), pd))
                if np.dot(np.cross(pd, ps), V3(0, 0, 1)) < 0: ps = -ps
                blade(m, p, pd, ps, Lp, lambda s_, w0=0.018 * (1 - 0.5 * s): w0 * (1 - s_) ** 0.7 * (0.55 + 0.45 * abs(math.sin(s_ * math.pi * 7))) + 0.0015,
                      {0: 14, 1: 9, 2: 6}[lod], 3 if lod < 2 else 2, 10, 0.5 * (1 - s), 0.0, G, droop=0.35, fold=-0.15, twist=0.25 * sgn, B0=0.3)
    return m
# ---- bushes: branch skeleton (bark tubes) + leaf-spray cards from atlas 2 (8x8 cells of 256; sprays = 2x2 cells on rows 6-7)
def spray_uv(k, s, t): return ((2 * k + 0.02 + s * 1.96) / 8, (6 + 0.02 + t * 1.96) / 8)
def bush(sp, var, lod):
    m = Mesh(); q0 = rng(sp, var); hz = sp == 'Hazel'; Hh = (1.5 if var == 'A' else 1.9) if hz else (1.2 if var == 'A' else 1.7)
    bark = 12 if hz else 11; twigs = []
    nst = (9 if var == 'B' else 7) if hz else (2 if var == 'A' else 3)
    def branch(p, d, L, r, depth, G, key):
        q = rng(sp, var, *key); n = max(3, nlod(6 if depth < 2 else 4, lod)); pts = [p]; dd = d.copy()
        for i in range(1, n):
            dd = nz(dd + V3(*q.normal(0, 0.12, 3)) + V3(0, 0, 0.05 if hz else 0.02)); pts.append(pts[-1] + dd * L / (n - 1))
        if not (lod == 2 and depth >= 3):
            R = [max(0.0, 1 - 0.35 * depth - 0.3 * i / (n - 1)) for i in range(n)]
            tube(m, pts, [r * (1 - 0.6 * i / (n - 1)) for i in range(n)], max(3, LOD[lod]['sides'] - depth), bark, R, G, cap=depth == 0 and not hz)
        if depth >= 2: twigs.extend([(pts[i], nz(pts[i] - pts[i - 1]), depth, G) for i in range(1, n)])
        if depth >= 3: return
        nch = (3 if hz else 4) if depth < 2 else (2 if hz else 3)
        for c in range(nch):
            s = 0.3 + 0.65 * (c + q.random() * 0.5) / nch; i = min(n - 1, int(s * (n - 1)))
            cd = nz(rot(dd, perp(dd), (0.5 if hz else 0.8) + 0.3 * q.random())); cd = rot(cd, dd, q.random() * 6.28)
            branch(pts[i], nz(cd + V3(0, 0, 0.2)), L * (0.45 + 0.2 * q.random()), r * 0.55, depth + 1, q.random() if depth == 0 else G, key + (c,))
    for k in range(nst):
        q = rng(sp, var, 'st', k); a = 2 * math.pi * k / nst + q.normal(0, 0.3); spread = 0.18 if hz else 0.5
        d = nz(V3(math.cos(a) * spread, math.sin(a) * spread, 1)); base = V3(math.cos(a), math.sin(a), 0) * (0.08 if hz else 0.03) - V3(0, 0, 0.04)
        branch(base, d, Hh * (0.75 + 0.2 * q.random()) * (1.0 if hz else 0.55), (0.022 if hz else 0.035) * (0.8 + 0.3 * q.random()), 0, q.random(), ('b', k))
    # leaf-spray cards on twigs: count by LOD, survivors scaled up; bent normals toward an ellipsoid around the crown
    allpts = np.array([t[0] for t in twigs]); ctr = allpts.mean(0); ext = np.maximum(allpts.max(0) - allpts.min(0), 0.3) * 0.5
    cnt = {0: 260, 1: 165, 2: 85}; want = cnt[lod] * (1.15 if var == 'B' else 1.0); step = len(twigs) / want; scl = math.sqrt(cnt[0] / cnt[lod])
    i = 0.0; c = 0
    while int(i) < len(twigs):
        p, d, depth, G = twigs[int(i)]; q = rng(sp, var, 'card', c); c += 1; i += step
        k = (2 if hz else 0) + (1 if q.random() < (0.4 if var == 'B' else 0.2) else 0)
        # card lies on the crown surface (geometric normal ~ outward, so the bent normal and the face agree), tilted 35 % outward
        out = nz((p - ctr) / ext + V3(0, 0, 0.4)); fwd = nz(d - out * np.dot(d, out) + out * 0.35 + V3(*q.normal(0, 0.3, 3)))
        sd = nz(np.cross(out, fwd)); nn = np.cross(fwd, sd)
        W = (0.30 if hz else 0.26) * scl * (0.85 + 0.3 * q.random()); Lc = W * 1.0
        fold = 0.18 * W; verts, uvs, cols, nrms = [], [], [], []
        for a_i, a in enumerate((-1, 0, 1)):
            for b_i, b in enumerate((0, 1)):
                pt = p - fwd * 0.04 + fwd * Lc * b + sd * a * W * 0.5 + nn * fold * (1 - abs(a)) - V3(0, 0, 0.05 * b * b)
                verts.append(pt); uvs.append(spray_uv(k, b, (a + 1) / 2))
                bn = nz(0.25 * nn + 0.75 * nz((pt - ctr) / ext)); nrms.append(tuple(bn)); cols.append((0.25 * (1 - b), G, 0.4 + 0.6 * b, 1.0))
        # vertex order: a-major (3) x b (2) -> grid rows = a, cols = b
        m.add(verts, grid_faces(3, 2), uvs, cols, mat=1, nrms=nrms)
    return m
SPECIES = [('Flower_Daisy', daisy, 'ABC'), ('Flower_Poppy', poppy, 'ABC'), ('Flower_Yarrow', yarrow, 'ABC'), ('Flower_Cornflower', cornflower, 'ABC'),
           ('Bush_Hawthorn', lambda v, l: bush('Hawthorn', v, l), 'AB'), ('Bush_Hazel', lambda v, l: bush('Hazel', v, l), 'AB'), ('Fern_Bracken', bracken, 'A')]
# ------------------------------------------------------------------ materials (Cycles preview + bake passes)
def img(n, cs):
    p = os.path.join(TEX, n + '.png'); i = bpy.data.images.load(p, check_existing=True); i.colorspace_settings.name = cs; return i
def make_mat(name, prefix, masked):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    o = nt.nodes.new('ShaderNodeOutputMaterial'); bs = nt.nodes.new('ShaderNodeBsdfPrincipled')
    bc = nt.nodes.new('ShaderNodeTexImage'); bc.image = img(prefix + '_BC', 'sRGB'); bc.name = 'BC'
    orm = nt.nodes.new('ShaderNodeTexImage'); orm.image = img(prefix + '_ORM', 'Non-Color'); orm.name = 'ORM'; sp = nt.nodes.new('ShaderNodeSeparateColor')
    nm = nt.nodes.new('ShaderNodeTexImage'); nm.image = img(prefix + '_N', 'Non-Color'); nm.name = 'N'
    fl = nt.nodes.new('ShaderNodeRGBCurve'); fl.mapping.curves[1].points[0].location = (0, 1); fl.mapping.curves[1].points[1].location = (1, 0)
    nn = nt.nodes.new('ShaderNodeNormalMap'); nn.name = 'NM'
    L = nt.links.new; L(orm.outputs[0], sp.inputs[0]); L(nm.outputs[0], fl.inputs['Color']); L(fl.outputs[0], nn.inputs['Color'])
    L(bc.outputs[0], bs.inputs['Base Color']); L(sp.outputs[1], bs.inputs['Roughness']); L(nn.outputs[0], bs.inputs['Normal'])
    tr = nt.nodes.new('ShaderNodeBsdfTranslucent'); L(bc.outputs[0], tr.inputs['Color']); L(nn.outputs[0], tr.inputs['Normal'])
    mx = nt.nodes.new('ShaderNodeMixShader'); mx.inputs[0].default_value = 0.3; L(bs.outputs[0], mx.inputs[1]); L(tr.outputs[0], mx.inputs[2]); mx.name = 'LIT'
    # bake passes: emission of BC / camera-space normal (DirectX) / ORM; alpha through a transparent mix
    eb = nt.nodes.new('ShaderNodeEmission'); eb.name = 'E_BC'; L(bc.outputs[0], eb.inputs[0])
    eo = nt.nodes.new('ShaderNodeEmission'); eo.name = 'E_ORM'; L(orm.outputs[0], eo.inputs[0])
    gm = nt.nodes.new('ShaderNodeNewGeometry'); fb = nt.nodes.new('ShaderNodeMath'); fb.operation = 'MULTIPLY_ADD'; L(gm.outputs['Backfacing'], fb.inputs[0]); fb.inputs[1].default_value = -2; fb.inputs[2].default_value = 1
    vf = nt.nodes.new('ShaderNodeVectorMath'); vf.operation = 'SCALE'; L(nn.outputs[0], vf.inputs[0]); L(fb.outputs[0], vf.inputs['Scale'])
    vt = nt.nodes.new('ShaderNodeVectorTransform'); vt.vector_type = 'NORMAL'; vt.convert_from = 'WORLD'; vt.convert_to = 'CAMERA'; L(vf.outputs[0], vt.inputs[0])
    se = nt.nodes.new('ShaderNodeSeparateXYZ'); L(vt.outputs[0], se.inputs[0]); cb = nt.nodes.new('ShaderNodeCombineXYZ')
    for ax_, sgn in ((0, 0.5), (1, -0.5), (2, 0.5)):                                # DirectX: green down
        mm = nt.nodes.new('ShaderNodeMath'); mm.operation = 'MULTIPLY_ADD'; L(se.outputs[ax_], mm.inputs[0]); mm.inputs[1].default_value = sgn; mm.inputs[2].default_value = 0.5; L(mm.outputs[0], cb.inputs[ax_])
    en = nt.nodes.new('ShaderNodeEmission'); en.name = 'E_N'; L(cb.outputs[0], en.inputs[0])
    if masked:
        for nm_ in ('LIT', 'E_BC', 'E_ORM', 'E_N'):
            tp = nt.nodes.new('ShaderNodeBsdfTransparent'); mz = nt.nodes.new('ShaderNodeMixShader'); mz.name = 'A_' + nm_
            gt = nt.nodes.new('ShaderNodeMath'); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = 0.4; L(bc.outputs['Alpha'], gt.inputs[0])
            L(gt.outputs[0], mz.inputs[0]); L(tp.outputs[0], mz.inputs[1]); L(nt.nodes[nm_].outputs[0], mz.inputs[2])
    m['masked'] = masked; return m
def set_pass(p):                                                                # 'LIT' | 'E_BC' | 'E_ORM' | 'E_N'
    for m in bpy.data.materials:
        if not m.use_nodes or 'masked' not in m: continue
        nt = m.node_tree; out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'); src = nt.nodes[('A_' + p) if m['masked'] else p]
        nt.links.new(src.outputs[0], out.inputs['Surface'])
    sc.view_settings.view_transform = 'Standard' if p in ('LIT', 'E_BC') else 'Raw'
MF = make_mat('M_MeadowFlora', 'T_MeadowFlora', False)
def to_obj(m, name, mats):
    me = bpy.data.meshes.new(name); me.from_pydata(m.v, [], m.f); me.update()
    uvl = me.uv_layers.new(name='UVMap'); li = np.zeros(len(me.loops), int); me.loops.foreach_get('vertex_index', li)
    uv = np.array(m.uv, float)[li]; uvl.data.foreach_set('uv', uv.ravel())
    ca = me.color_attributes.new('Col', 'BYTE_COLOR', 'POINT'); ca.data.foreach_set('color', np.clip(np.array(m.col, float), 0, 1).ravel())
    me.polygons.foreach_set('material_index', m.mat); me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
    for mt in mats: me.materials.append(mt)
    if any(n is not None for n in m.nrm):                                       # bent normals on cards, default elsewhere
        me.update(); base = [tuple(v.normal) for v in me.vertices]
        me.normals_split_custom_set_from_vertices([m.nrm[i] if m.nrm[i] is not None else base[i] for i in range(len(me.vertices))])
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o); return o
# ------------------------------------------------------------------ render setup for card / impostor bakes
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 24; sc.render.film_transparent = True
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'; sc.view_settings.look = 'None'
sc.cycles.max_bounces = 0; sc.cycles.filter_width = 1.0
wd = bpy.data.worlds.new('Wb'); sc.world = wd
cam = bpy.data.objects.new('BakeCam', bpy.data.cameras.new('BakeCam')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.type = 'ORTHO'
def shoot(objs, res, center, size, view, path_prefix):
    """ortho render of objs: view 'top' (look -Z) or 'front' (look +Y). returns dict pass -> float RGBA array (res,res,4) bottom-up"""
    for o in sc.objects: o.hide_render = o.type == 'MESH' and o not in objs
    sc.render.resolution_x = sc.render.resolution_y = res; cam.data.ortho_scale = size
    if view == 'top': cam.location = Vector(center) + Vector((0, 0, 5)); cam.rotation_euler = (0, 0, 0)
    else: cam.location = Vector(center) + Vector((0, -5, 0)); cam.rotation_euler = (math.radians(90), 0, 0)
    cam.data.clip_end = 20; out = {}
    for p in ('E_BC', 'E_N', 'E_ORM'):
        set_pass(p); sc.render.filepath = path_prefix + p + '.png'; bpy.ops.render.render(write_still=True)
        im = bpy.data.images.load(sc.render.filepath); im.colorspace_settings.name = 'Non-Color'; a = np.empty(res * res * 4, np.float32); im.pixels.foreach_get(a)
        bpy.data.images.remove(im); out[p] = a.reshape(res, res, 4)
    return out
def dilate(rgb, alpha, it=24):
    """push colour of covered texels into the empty ones (no dark fringes in mips)"""
    c = rgb * alpha[..., None]; w = alpha.copy(); filled = alpha > 0.5
    for _ in range(it):
        cs = sum(np.roll(np.roll(c, i, 0), j, 1) for i in (-1, 0, 1) for j in (-1, 0, 1)); ws = sum(np.roll(np.roll(w, i, 0), j, 1) for i in (-1, 0, 1) for j in (-1, 0, 1))
        new = (~filled) & (ws > 1e-4); c[new] = cs[new] / ws[new, None]; w[new] = 1; filled |= new
    rgb = rgb.copy(); rgb[alpha <= 0.5] = (c / np.maximum(w, 1e-4)[..., None])[alpha <= 0.5]; return rgb
A2 = 2048; CELL = 256
ATL = {'E_BC': np.zeros((A2, A2, 4), np.float32), 'E_N': np.zeros((A2, A2, 4), np.float32), 'E_ORM': np.zeros((A2, A2, 4), np.float32)}
ATL['E_N'][..., :] = (0.5, 0.5, 1.0, 1.0); ATL['E_ORM'][..., :] = (1.0, 0.6, 0.0, 1.0)
def place(res, cx, cy, span, thicken=False):
    if thicken:                                                                 # impostors: grow alpha 1 px so 2 mm stems survive at 256 px
        al = res['E_BC'][..., 3]; res['E_BC'][..., 3] = np.maximum.reduce([np.roll(np.roll(al, i, 0), j, 1) for i in (-1, 0, 1) for j in (-1, 0, 1)])
    for p, a in res.items():
        tile = a.copy()
        if p == 'E_BC': tile[..., :3] = dilate(tile[..., :3], a[..., 3] if not thicken else al)
        else: tile[..., :3] = dilate(tile[..., :3], res['E_BC'][..., 3]); tile[..., 3] = 1
        ATL[p][cy * CELL:cy * CELL + span, cx * CELL:cx * CELL + span] = tile
TMP = os.path.join(D, 'out', 'bake'); os.makedirs(TMP, exist_ok=True)
# ---- leaf sprays (real leaf geometry -> card): k 0 hawthorn, 1 hawthorn + haws, 2 hazel, 3 hazel + nuts. card space: x along (0..1), y across (-0.5..0.5)
def hawleaf(s): return (0.2 + 0.8 * math.sin(math.pi * min(1, s * 1.05)) ** 0.7) * (0.35 + 0.65 * abs(math.cos(s * math.pi * 2.5)) ** 0.6) * (s < 0.99) + 0.01
def hazleaf(s): return (math.sin(math.pi * min(1, 0.15 + s * 0.95)) ** 0.6) * (1 + 0.06 * math.sin(s * 70)) * (s < 0.985) + 0.01
def spray(k):
    m = Mesh(); q = rng('spray', k); hz = k >= 2; tw = [V3(0, 0, 0)]
    for i in range(1, 7): tw.append(tw[-1] + nz(V3(1, q.normal(0, 0.12), 0)) * 0.09)
    tube(m, tw, [0.010 * (1 - 0.6 * i / 6) for i in range(7)], 6, 12 if hz else 11, [1] * 7, 0.0)
    shoots = [(tw[0], V3(1, 0, 0), 0.54)]                                       # main twig + 2 side shoots: the spray fills its square card
    for j, (s0, sg) in enumerate(((0.3, 1), (0.5, -1))):
        b0 = tw[int(s0 * 6)]; dd = nz(V3(math.cos(0.65 * sg), math.sin(0.65 * sg), 0)); pts = [b0]
        for i in range(4): pts.append(pts[-1] + dd * 0.07)
        tube(m, pts, [0.006 * (1 - 0.5 * i / 4) for i in range(5)], 5, 12 if hz else 11, [1] * 5, 0.0); shoots.append((b0, dd, 0.28))
    for sh, (o0, dd, Ls) in enumerate(shoots):
        nleaf = (8 if hz else 16) if sh == 0 else (4 if hz else 8); sdv = nz(np.cross(V3(0, 0, 1), dd))
        for i in range(nleaf):
            s = 0.15 + 0.85 * i / nleaf; p = o0 + dd * s * Ls; side = 1 if i % 2 else -1
            a = side * (0.6 + 0.6 * q.random()) + (0 if hz else q.normal(0, 0.3)); d = nz(dd * math.cos(a) * 0.8 + sdv * math.sin(a) + V3(0, 0, q.normal(0, 0.1)))
            L = (0.15 + 0.05 * q.random()) * (0.8 + 0.3 * s) if hz else (0.08 + 0.04 * q.random())
            blade(m, p, d, -nz(np.cross(V3(0, 0, 1), d)), L, (lambda s_, L=L: 0.38 * L * hazleaf(s_)) if hz else (lambda s_, L=L: 0.42 * L * hawleaf(s_)),
                  8, 5, 9 if hz else 8, 0, 0, 0, droop=q.normal(0, 0.15), fold=0.12, twist=q.normal(0, 0.4))
    if k == 1:                                                                  # clusters of haws
        for c in range(4):
            cp = V3(0.18 + 0.17 * c, q.normal(0, 0.1), 0.03)
            for b in range(5):
                bp = cp + V3(*q.normal(0, 0.018, 2), 0.01); tube(m, [cp - V3(0, 0, 0.01), bp], [0.0015, 0.0012], 3, 11, [0, 0], 0)
                lathe(m, bp, V3(0, 0, 1), [(0, 0.0005), (0.002, 0.0055), (0.006, 0.0065), (0.010, 0.005), (0.012, 0.002)], 8, 13, 0, 0)
    if k == 3:                                                                  # hazelnuts in their leafy husks
        for c in range(3):
            cp = V3(0.3 + 0.22 * c, q.normal(0, 0.08), 0.04)
            lathe(m, cp, V3(0, 0, 1), [(0, 0.001), (0.004, 0.008), (0.012, 0.0085), (0.018, 0.005), (0.02, 0.001)], 10, 12, 0, 0)
            for h_ in range(5):
                a = h_ * 1.256; d = nz(V3(math.cos(a), math.sin(a), 1.2))
                blade(m, cp + V3(0, 0, 0.004), d, perp(d), 0.026, lambda s_: 0.008 * math.sin(math.pi * min(1, 0.3 + s_)) + 0.002, 4, 3, 15, 0, 0, 0, droop=-0.4, fold=0.3)
    o = to_obj(m, 'Spray_%d' % k, [MF]); return o
for k in range(4):
    o = spray(k); res = shoot([o], 512, (0.4, 0, 0), 0.86, 'top', os.path.join(TMP, 'spray%d_' % k)); place(res, 2 * k, 6, 512)
    bpy.data.objects.remove(o)
print('SPRAYS OK', flush=True)
def save_atlas(name, a, alpha):
    im = bpy.data.images.new(name, A2, A2, alpha=alpha); im.colorspace_settings.name = 'Non-Color'; b = a.copy()
    if not alpha: b[..., 3] = 1
    im.pixels.foreach_set(np.clip(b, 0, 1).ravel()); im.filepath_raw = os.path.join(TEX, name + '.png'); im.file_format = 'PNG'
    if alpha: im.alpha_mode = 'STRAIGHT'
    im.save(); bpy.data.images.remove(im)
def save_all():
    save_atlas('T_MeadowCards_BC', ATL['E_BC'], True); save_atlas('T_MeadowCards_N', ATL['E_N'], False); save_atlas('T_MeadowCards_ORM', ATL['E_ORM'], False)
save_all()                                                                      # sprays only for now: bushes are rendered with them for their impostors
MC = make_mat('M_MeadowCards', 'T_MeadowCards', True)
# ------------------------------------------------------------------ build every plant, LOD0-2
stats = {}; cell = 0; objs = {}
for sp_name, fn, vars_ in SPECIES:
    for v in vars_:
        name = 'SM_%s_%s' % (sp_name, v); objs[name] = []
        for lod in range(3):
            m = fn(v, lod); o = to_obj(m, name + ('' if lod == 0 else '_LOD%d' % lod), [MF, MC] if sp_name.startswith('Bush') else [MF]); objs[name].append(o)
            stats.setdefault(name, {})['LOD%d' % lod] = m.tris()
        print('BUILT', name, stats[name], flush=True)
# ------------------------------------------------------------------ impostors (front view of LOD0) -> LOD3 crossed cards
for name, ol in objs.items():
    o = ol[0]; bb = np.array([o.matrix_world @ Vector(c) for c in o.bound_box]); lo, hi = bb.min(0), bb.max(0)
    w, h = hi[0] - lo[0], hi[2] - lo[2]; size = max(w, h) * 1.04; ctr = ((lo[0] + hi[0]) / 2, 0, (lo[2] + hi[2]) / 2)
    cx, cy = cell % 8, cell // 8; cell += 1
    res = shoot([o], CELL, ctr, size, 'front', os.path.join(TMP, name + '_')); place(res, cx, cy, CELL, thicken=True)
    m = Mesh(); q = rng(name, 'imp'); dep = max(hi[1] - lo[1], 0.05)
    u0, u1 = 0.5 - w / (2 * size), 0.5 + w / (2 * size); v0, v1 = 0.5 - h / (2 * size), 0.5 + h / (2 * size)
    def cuv(u, v_): return ((cx + 0.0 + u) / 8, (cy + v_) / 8)
    for ang, half in ((0.0, w / 2), (math.pi / 2, max(dep, w * 0.8) / 2)):     # 2 crossed cards; the side card reuses the front view
        ax_ = V3(math.cos(ang), math.sin(ang), 0); nrm_ = V3(-math.sin(ang), math.cos(ang), 0) * -1; cxw = V3(ctr[0], (lo[1] + hi[1]) / 2, 0)
        vs = [cxw - ax_ * half + V3(0, 0, lo[2]), cxw + ax_ * half + V3(0, 0, lo[2]), cxw + ax_ * half + V3(0, 0, hi[2]), cxw - ax_ * half + V3(0, 0, hi[2])]
        uvs = [cuv(u0, v0), cuv(u1, v0), cuv(u1, v1), cuv(u0, v1)]; G = q.random()
        cols = [(1, G, 0, 1), (1, G, 0, 1), (0, G, 0.3, 1), (0, G, 0.3, 1)]
        nr = [tuple(nz(nrm_ * 0.5 + V3(0, 0, 0.6) + (np.asarray(p) - cxw - V3(0, 0, (lo[2] + hi[2]) / 2)) / max(w, h))) for p in vs]
        m.add(vs, [[0, 1, 2, 3]], uvs, cols, mat=0, nrms=nr)
    lo3 = to_obj(m, name + '_LOD3', [MC]); ol.append(lo3); stats[name]['LOD3'] = 4
print('IMPOSTORS OK', cell, flush=True)
save_all()
for im in list(bpy.data.images):
    if im.name.startswith('T_MeadowCards'): im.reload()
# ------------------------------------------------------------------ export: one FBX per LOD (LOD0 = SM name), keep the scene for lookdev
set_pass('LIT'); sc.render.film_transparent = False
for name, ol in objs.items():
    for lod, o in enumerate(ol):
        bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
        fn = name + ('' if lod == 0 else '_LOD%d' % lod)
        bpy.ops.export_scene.fbx(filepath=os.path.join(FBX, fn + '.fbx'), use_selection=True, object_types={'MESH'}, mesh_smooth_type='FACE',
                                 use_tspace=True, colors_type='LINEAR', apply_scale_options='FBX_SCALE_UNITS', add_leaf_bones=False, bake_anim=False)
for o in list(sc.objects):
    if o.type == 'MESH': o.hide_render = False
json.dump(stats, open(os.path.join(D, 'out', 'flora_stats.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'flora.blend')); print('FLORA OK', len(objs), 'meshes', flush=True)
