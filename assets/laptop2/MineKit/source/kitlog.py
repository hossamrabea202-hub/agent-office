# Log, rope and lashing builders extracted from the siege kit's build_kit.py (laptop2 2026-10-29), as a module.
import os, math
import bpy, numpy as np
D = os.path.dirname(os.path.abspath(__file__))
RES = os.environ.get('RES', 'low'); HIGH = RES == 'high'
PI = math.pi
MATS = {}
def mat(name):
    if name not in MATS:
        m = bpy.data.materials.get(name) or bpy.data.materials.new(name); MATS[name] = m
    return MATS[name]

def _hash(ix, iy, s):
    h = (ix * 374761393 + iy * 668265263 + s * 982451653) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0
def vnoise(u, v, s=0, pu=None):
    """2D value noise; pu = period along u (for seamless wrap around a log)."""
    iu, iv = np.floor(u).astype(np.int64), np.floor(v).astype(np.int64)
    fu, fv = u - iu, v - iv
    fu, fv = fu * fu * (3 - 2 * fu), fv * fv * (3 - 2 * fv)
    w = (lambda k: k % pu) if pu else (lambda k: k)
    a, b = _hash(w(iu), iv, s), _hash(w(iu + 1), iv, s)
    c, d = _hash(w(iu), iv + 1, s), _hash(w(iu + 1), iv + 1, s)
    return a + (b - a) * fu + (c - a) * fv + (a - b - c + d) * fu * fv
def fbm(u, v, s, oct=5, pu=None):
    t, amp, f, tot = 0, 1.0, 1.0, 0
    for o in range(oct):
        t = t + amp * vnoise(u * f, v * f, s + o * 17, pu * int(f) if pu else None); tot += amp; amp *= 0.5; f *= 2
    return t / tot
def mesh_obj(name, V, F, mats, fmat=None, uv=None):
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(p) for p in V], [], [tuple(f) for f in F]); me.update()
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    for m in mats: me.materials.append(mat(m))
    if fmat is not None: me.polygons.foreach_set('material_index', np.asarray(fmat, np.int32))
    if uv is not None:
        lay = me.uv_layers.new(name='UV')
        idx = np.empty(sum(len(f) for f in F), np.int64); k = 0
        for f in F:
            idx[k:k + len(f)] = f; k += len(f)
        lay.data.foreach_set('uv', np.asarray(uv, np.float32)[idx].ravel())
    me.polygons.foreach_set('use_smooth', np.ones(len(me.polygons), bool))
    return ob
def frame(p0, p1, roll=0.0):
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    z = p1 - p0; L = np.linalg.norm(z); z = z / L
    up = np.array([0, 0, 1.0]) if abs(z[2]) < 0.9 else np.array([1.0, 0, 0])
    x = np.cross(up, z); x /= np.linalg.norm(x); y = np.cross(z, x)
    c, s = math.cos(roll), math.sin(roll)
    return p0, L, x * c + y * s, -x * s + y * c, z
def log(name, p0, p1, r, seed, tip1=0.0, tip0=0.0, bend=0.02, char=0.0, split=False, brk=0.0):
    """tip1 / tip0: length of the sharpened point at p1 / p0 (0 = axe-cut flat end). split = half log (flat back).
    brk: the p1 end is snapped off instead: a jagged, splintered break up to brk metres deep, bare fibre showing."""
    rng = np.random.default_rng(seed)
    o, L, X, Y, Z = frame(p0, p1, rng.uniform(0, 2 * PI))
    HS = float(os.environ.get('HIGH_SCALE', '1'))     # >1 = coarser high mesh (big assets seen from afar; keeps the bake in memory)
    na = int(160 / HS) if HIGH else 14
    dl = 0.006 * HS if HIGH else 0.14
    nl = max(int(L / dl), 6)
    t = np.linspace(0, 1, nl + 1)
    # extra rings near pointed ends so the facets resolve on the low mesh
    if not HIGH:
        extra = []
        for tl, at1 in ((tip1, True), (tip0, False)):
            if tl > 0:
                f = tl / L; e = np.linspace(0, f, 7)
                extra += list(1 - e if at1 else e)
        if brk > 0: extra += list(1 - np.linspace(0, min(brk * 1.2 / L, 0.5), 9))
        t = np.unique(np.clip(np.concatenate([t, extra]), 0, 1))
    a = np.linspace(0, 2 * PI, na + 1)[:-1]
    A, T = np.meshgrid(a, t)                 # [ring, around]
    zl = T * L
    # radius: taper toward p1, irregular swelling, knots
    rr = r * (1 - 0.10 * T) * (1 + 0.05 * (fbm(A / (2 * PI) * 3, zl * 1.2, seed, 3, 3) - 0.5))
    rr0 = rr.copy()
    phi = rng.uniform(0, 2 * PI, 7)
    if tip1 > 0 or tip0 > 0:
        nf = int(rng.integers(5, 8))
        for zt, tl, sgn in ((L, tip1, 1), (0.0, tip0, -1)):
            if tl <= 0: continue
            fa = rng.uniform(0, 2 * PI) + np.arange(nf) * 2 * PI / nf + rng.uniform(-0.25, 0.25, nf)
            ax = (rng.uniform(-0.25, 0.25), rng.uniform(-0.25, 0.25))    # the apex is a little off-centre
            dist = np.where(sgn > 0, zt - zl, zl - zt) * (r / tl) * (1 + rng.uniform(-0.15, 0.15, nf)[:, None, None])
            # facet k: plane at angle fa[k]; radius limited to d / cos(a - fa)
            cosd = np.cos(A[None] - fa[:, None, None])
            lim = np.where(cosd > 0.05, dist / np.maximum(cosd, 0.05), 9.0)
            lim = lim.min(0) + r * 0.02
            rr = np.minimum(rr, lim)
    # where the axe cut through the bark: a smooth 0..1 weight over ~6 mm of radius, so the bark edge is a clean curve
    # on the bake instead of following the mesh faces
    cutw = np.clip((rr0 * 0.975 - rr) / (r * 0.04), 0, 1)
    cutw = cutw * cutw * (3 - 2 * cutw)
    if brk > 0:
        # snapped end: per-angle break height (a few long splinters, most of the rim torn lower), the last stretch of
        # the log squeezed onto it so the mesh stays clean; fresh fibre shows for 3 cm below the break
        ua = A / (2 * PI)
        n1 = fbm(ua * 5, np.full_like(ua, seed * 0.37), seed + 51, 3, 5)
        n2 = fbm(ua * 17, np.full_like(ua, seed * 0.71), seed + 53, 2, 17)
        jag = brk * (0.1 + 0.9 * np.clip(n1 * 1.4 - 0.2, 0, 1) ** 2.2 + 0.25 * n2)
        z0 = max(L - brk * 1.2, L * 0.5)
        zcut = np.maximum(L - jag.max() + jag, z0 + 0.03)   # the highest splinter reaches L
        zl = np.where(zl > z0, z0 + (zl - z0) * (zcut - z0) / (L - z0), zl)
        near = np.clip(1 - (zcut - zl) / 0.03, 0, 1)
        rr = rr * (1 - 0.35 * near * (0.5 + 0.5 * n2))   # splinters thin out toward their points
        cutw = np.maximum(cutw, near)
    disp = np.zeros_like(rr)
    if HIGH:
        u = A / (2 * PI)
        # pine bark: irregular plates (Voronoi cells ~4.5 cm across x 11 cm along, warped) split by deep fissures,
        # each plate at its own height, flaky fine detail on top
        def cells(cw_m, ch_m, sd, jit=0.9):
            """Voronoi over the log surface: cell width cw_m around (wraps seamlessly), ch_m along. -> edge distance, cell id"""
            nu = max(int(round(2 * PI * r / cw_m)), 5)
            warp = fbm(u * 4, zl * 1.2, sd, 3, 4) - 0.5
            s, t2 = u * nu + warp * 1.1, zl / ch_m + warp * 1.6
            si, ti = np.floor(s).astype(np.int64), np.floor(t2).astype(np.int64)
            F1 = np.full(s.shape, 9.0); F2 = np.full(s.shape, 9.0); cid = np.zeros(s.shape, np.int64)
            for di in (-1, 0, 1):
                for dj in (-1, 0, 1):
                    ci, cj = si + di, ti + dj; cw = ci % nu
                    px = ci + 0.5 + jit * (_hash(cw, cj, sd + 1) - 0.5); py = cj + 0.5 + jit * (_hash(cw, cj, sd + 2) - 0.5)
                    dd = np.sqrt((s - px) ** 2 + (t2 - py) ** 2)
                    closer = dd < F1
                    F2 = np.where(closer, F1, np.minimum(F2, dd)); cid = np.where(closer, cw * 7919 + cj, cid); F1 = np.minimum(F1, dd)
            return F2 - F1, cid
        # pine bark: big uneven vertical plates (6-9 cm x 14-20 cm) split by deep fissures, each plate cracked again by
        # shallow minor cracks, plate tops at their own heights and laminated in thin horizontal flakes
        e1, c1 = cells(rng.uniform(0.06, 0.085), rng.uniform(0.20, 0.28), seed + 21)
        e2, _ = cells(0.035, 0.09, seed + 41, 1.0)
        valley = 1 - np.clip(e1 / 0.32, 0, 1) ** 0.75               # wide V-shaped fissure between plates
        minor = 1 - np.clip(e2 / 0.06, 0, 1)                         # narrow shallow cracks across a plate
        ph = _hash(c1, c1 // 13, seed + 23)
        rough = fbm(u * 45, zl * 22, seed + 5, 4, 45)                # coarse, uneven plate tops
        lam = fbm(u * 60, zl * 150, seed + 6, 3, 60)                 # thin horizontal flake layers
        top = 0.004 * ph + 0.0035 * rough + 0.0012 * lam
        plates = top * (1 - valley) - 0.011 * valley ** 1.3 - 0.0016 * minor * (1 - valley)
        disp = plates * (1 - cutw)
        # axe facets: shallow scallops and stringy fibres along the grain
        sc = fbm(u * 14, zl * 9, seed + 9, 2, 14)
        fib = fbm(u * 160, zl * 4, seed + 11, 2, 160)
        disp = disp + cutw * (-0.002 * sc + 0.0006 * fib)
        # end checks (cracks) near cut ends, a few knots
        for k in range(3):
            kz, ka = rng.uniform(0.15, 0.8) * L, rng.uniform(0, 2 * PI)
            dd = np.sqrt(((np.angle(np.exp(1j * (A - ka)))) * r) ** 2 + (zl - kz) ** 2)
            disp = disp + 0.012 * np.exp(-(dd / 0.028) ** 2) * (1 - cutw) - 0.006 * np.exp(-(dd / 0.012) ** 2) * (1 - cutw)
    rad = rr + disp
    bendv = bend * np.sin(T * PI)
    V = (o + zl[..., None] * Z + (rad * np.cos(A))[..., None] * X + (rad * np.sin(A) + bendv)[..., None] * Y)
    if split:   # flat sawn back (rails): clamp the +Y side
        yy = np.einsum('ijk,k->ij', V - o, Y)
        V = V - (np.maximum(yy - r * 0.15, 0))[..., None] * Y
    nr, nA = V.shape[:2]
    Vf = V.reshape(-1, 3)
    F = []
    for i in range(nr - 1):
        for j in range(nA):
            j2 = (j + 1) % nA
            F.append((i * nA + j, i * nA + j2, (i + 1) * nA + j2, (i + 1) * nA + j))
    # end caps (sawn/axed ends; pointed ends close to a point already)
    caps = []
    for ring, rev in ((0, True), (nr - 1, False)):
        c = Vf[ring * nA:(ring + 1) * nA].mean(0); ci = len(Vf) + len(caps); caps.append(c)
        for j in range(nA):
            j2 = (j + 1) % nA
            F.append((ring * nA + j2, ring * nA + j, ci) if rev else (ring * nA + j, ring * nA + j2, ci))
    Vall = np.vstack([Vf, np.array(caps)])
    # UVs: real-world scale (1 UV = 1 m) along the log and around it; caps planar
    uvs = np.zeros((len(Vall), 2))
    circ = 2 * PI * r
    uvs[:len(Vf), 0] = (A / (2 * PI) * circ).ravel(); uvs[:len(Vf), 1] = zl.ravel()
    uvs[len(Vf):] = [[0, -0.5], [0, -0.5]]
    # faces of the seam: the last column wraps; give it its own u so it doesn't stretch
    fm = np.zeros(len(F), np.int32)
    fm[(nr - 1) * nA:] = 1                    # cut ends show bare wood
    ob = mesh_obj(name, Vall, F, ['Bark', 'WoodCut'], fm, None)
    # UV via a seam-aware unwrap: let Blender split the wrap seam (cylinder project per log is good enough)
    lay = ob.data.uv_layers.new(name='UV')
    loops = np.empty(len(ob.data.loops), np.int64); ob.data.loops.foreach_get('vertex_index', loops)
    uv = uvs[loops].copy()
    # fix the seam: for each quad that wraps (j2 == 0), push its u = 0 corners to u = circ
    lp = 0
    for k, f in enumerate(F):
        n = len(f)
        if k < (nr - 1) * nA and (k % nA) == nA - 1:
            for q in range(n):
                if uv[lp + q, 0] < 1e-6: uv[lp + q, 0] = circ
        if k >= (nr - 1) * nA:   # cap: planar projection
            for q in range(n):
                vi = f[q]; p = Vall[vi] - o
                uv[lp + q] = [np.dot(p, X) + 0.5, np.dot(p, Y) - 0.5 - (0.5 if k >= (nr - 1) * nA + nA else 0)]
        lp += n
    lay.data.foreach_set('uv', uv.astype(np.float32).ravel())
    # 'tip' = fire-hardening char: 1 at a pointed end, fading out over 0.9 m (x char strength); read by the bark/cut shaders
    tipd = np.full(zl.shape, 9.0)
    if tip1 > 0: tipd = np.minimum(tipd, L - zl)
    if tip0 > 0: tipd = np.minimum(tipd, zl)
    tv = np.clip(1 - tipd / 0.9, 0, 1) ** 1.4 * char
    tv = np.concatenate([tv.ravel(), [0.0 if tip0 <= 0 else char, 0.0 if tip1 <= 0 else char]])
    at = ob.data.attributes.new('tip', 'FLOAT', 'POINT'); at.data.foreach_set('value', tv.astype(np.float32))
    cv = np.concatenate([cutw.ravel(), [1.0, 1.0]])
    at = ob.data.attributes.new('cut', 'FLOAT', 'POINT'); at.data.foreach_set('value', cv.astype(np.float32))
    return ob
def rope(name, pts, r, seed, closed=False):
    """lashing rope: a tube along pts; the high version has 3 twisted strands."""
    pts = np.asarray(pts, float)
    if closed: pts = np.vstack([pts, pts[:1]])
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1); s = np.concatenate([[0], np.cumsum(seg)])
    ns = int(s[-1] / (0.003 if HIGH else 0.03)) + 2
    ss = np.linspace(0, s[-1], ns)
    P = np.stack([np.interp(ss, s, pts[:, k]) for k in range(3)], 1)
    T = np.gradient(P, axis=0); T /= np.linalg.norm(T, axis=1, keepdims=True) + 1e-9
    N = np.cross(T, np.array([0, 0, 1.0])); bad = np.linalg.norm(N, axis=1) < 1e-3
    N[bad] = np.cross(T[bad], np.array([1.0, 0, 0])); N /= np.linalg.norm(N, axis=1, keepdims=True)
    B = np.cross(T, N)
    na = 24 if HIGH else 6
    a = np.linspace(0, 2 * PI, na + 1)[:-1]
    rr = np.full((ns, na), r)
    if HIGH:   # three strands twisted at 3 turns per 2 cm (lay angle)
        tw = ss[:, None] / 0.02 * 2 * PI
        rr = r * (0.82 + 0.18 * np.abs(np.cos(1.5 * (a[None] - tw))))
        rr = rr * (1 + 0.04 * (fbm(a[None] / (2 * PI) * 30 + 0 * ss[:, None], ss[:, None] * 300, seed, 2, 30) - 0.5))
    V = P[:, None] + rr[..., None] * (np.cos(a)[None, :, None] * N[:, None] + np.sin(a)[None, :, None] * B[:, None])
    Vf = V.reshape(-1, 3); F = []
    for i in range(ns - 1):
        for j in range(na):
            j2 = (j + 1) % na; F.append((i * na + j, i * na + j2, (i + 1) * na + j2, (i + 1) * na + j))
    uv = np.zeros((len(Vf), 2)); uv[:, 0] = np.tile(a / (2 * PI) * 2 * PI * r, ns); uv[:, 1] = np.repeat(ss, na)
    return mesh_obj(name, Vf, F, ['Rope'], None, uv)
def lash(name, cA, ra, cB, rb, a, b, seed):
    """diagonal (X) lashing that binds two crossing logs: log A at cA (axis a, radius ra) lies against log B at cB.
    Each loop runs around both logs on one diagonal; two loops per diagonal, then two frapping turns between them."""
    rng = np.random.default_rng(seed)
    cA, cB = np.asarray(cA, float), np.asarray(cB, float)
    a, b = np.asarray(a, float) / np.linalg.norm(a), np.asarray(b, float) / np.linalg.norm(b)
    n = cB - cA; dist = np.linalg.norm(n); n /= dist
    m = (cA + cB) / 2
    pts = []
    for loop, dg in enumerate((1, 1, -1, -1)):
        d = a + dg * b; d /= np.linalg.norm(d)
        q = np.cross(d, n); q /= np.linalg.norm(q)
        spread = (loop % 2 - 0.5) * 0.026
        c0 = m + d * spread
        for k in range(96):
            th = k / 96 * 2 * PI
            w = math.cos(th) * n + math.sin(th) * q
            # march outward from the joint until the rope sits on the surface of both logs (it wraps them tightly)
            tt = 0.0
            while tt < 0.6:
                p = c0 + w * tt
                da = np.linalg.norm((p - cA) - np.dot(p - cA, a) * a); db = np.linalg.norm((p - cB) - np.dot(p - cB, b) * b)
                if da >= ra + RR * 0.9 and db >= rb + RR * 0.9: break
                tt += 0.0015
            pts.append(p + rng.normal(0, 0.0008, 3))
    return rope(name, pts, RR, seed)
RR = 0.0115   # lashing rope radius (23 mm hemp)
