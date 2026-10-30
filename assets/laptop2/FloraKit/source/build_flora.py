# Flora kit (laptop2, 2026-10-30): meadow flowers for the castle fields and alien flora + corrupted ground for the
# tentacle realm. One parametric plant generator: a bezier stem, leaves and petals as parametric surfaces (real
# geometry, two-sided; no alpha cards), a centre. High poly adds veins, ruffled edges, serrations, pollen bumps.
#   blender -b --factory-startup -P build_flora.py      (env RES = low | high, VARIANT = <species>)
# Species: Daisy, Poppy, Foxglove (meadow), Bloodcap, SporeStalk, TentacleFern (realm), CorruptPatch (ground, 2 m)
# Units: metres, Z up, the plant base at the origin. 'glow' point attribute = emissive mask for the realm species.
import os, sys, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np
bpy.ops.wm.read_factory_settings(use_empty=True)
from shieldkit import fbm, sstep, mesh, grid_quads, unit, sweep, circ, superellipsoid, HIGH, PI
D = os.path.dirname(os.path.abspath(__file__))
VAR = os.environ.get('VARIANT', 'Daisy')
rng = np.random.default_rng({'Daisy': 1, 'Poppy': 2, 'Foxglove': 3, 'Bloodcap': 11, 'SporeStalk': 12, 'TentacleFern': 13, 'CorruptPatch': 21, 'BlobMine': 31, 'EggCluster': 32}[VAR])
PARTS = []     # (name, V, faces, material, uv, attrs)
def part(name, V, Q, mname, uv, glow=None):
    PARTS.append((name, V, Q, mname, uv, glow))

def bezier(p0, p1, p2, p3, n):
    t = np.linspace(0, 1, n)[:, None]
    return (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3

def stem(name, path, r0, r1, mname='Stem', nseg=None, glow=None, bumpy=0.0):
    n = len(path); nseg = nseg or (24 if HIGH else 6)
    V, Q, Tr, uv = sweep(path, np.tile([0, 1.0, 0], (n, 1)), circ(1.0, nseg), caps=False)
    M1 = nseg + 1; G = V[:n * M1].reshape(n, M1, 3); ctr = path[:, None, :]
    t = np.linspace(0, 1, n)[:, None, None]
    rad = r0 + (r1 - r0) * t
    if HIGH:
        a = np.linspace(0, 2 * PI, M1)[None, :, None]
        rad = rad * (1 + 0.08 * (fbm(np.cos(a[..., 0]) * 3 + t[..., 0] * 40, np.sin(a[..., 0]) * 3, 7, 3) - 0.5)[..., None])
        if bumpy: rad = rad * (1 + bumpy * np.abs(np.sin(t * 60 + a * 0)) ** 6)       # nodes along the stalk
    G = ctr + (G - ctr) * rad
    V[:n * M1] = G.reshape(-1, 3); uv[:n * M1, 0] *= float(r0) * 2; uv[:n * M1] *= 0.4   # stems need little detail: 0.4x texel density, the leaves and petals get the rest
    part(name, V, Q, mname, uv, None if glow is None else np.full(len(V), glow))

def blade(name, origin, d, up, L, W, shape, mname, nu=None, nv=None, curl=0.0, cup=0.0, twist=0.0, ruffle=0.0, serr=0.0, vein=0.0, glow=None, taper_t=0.0):
    """parametric petal / leaf: u along (0..1), v across (-1..1). shape(u) = half width 0..1. Two-sided geometry (one
    surface; the material is two-sided). d = direction, up = the blade's normal at the base."""
    # the low must follow the high's curl and cup within the bake cage (4 mm): big cupped petals get more segments
    nu = nu or (48 if HIGH else (8 if L > 0.07 else 6)); nv = nv or (24 if HIGH else (6 if cup * W > 0.02 else 4))
    u = np.linspace(0, 1, nu); v = np.linspace(-1, 1, nv); U, Vv = np.meshgrid(u, v, indexing='ij')
    d = unit(np.asarray(d, float)); up = unit(np.asarray(up, float) - np.dot(up, d) * d); side = np.cross(d, up)
    w = shape(U) * W
    if serr and HIGH: w = w * (1 - serr * np.abs(np.sin(U * 42 * PI)) ** 8)
    if ruffle and HIGH: w = w * (1 + ruffle * (fbm(U * 6, Vv * 3 + 9, 31, 3) - 0.5))
    x = Vv * w
    # curl: the tip bends toward -up (petal) or +up; cup: the sides rise
    z = -curl * U ** 2 * L + cup * (Vv ** 2) * w * 0.9 + taper_t * 0
    tw = twist * U
    X = x * np.cos(tw) - z * np.sin(tw); Z = x * np.sin(tw) + z * np.cos(tw)
    if HIGH:
        Z = Z + vein * 0.5 * np.exp(-(Vv / 0.08) ** 2) * sstep(0.02, 0.2, U) * sstep(1.0, 0.85, U)          # midrib
        if vein: Z = Z + vein * 0.25 * np.abs(np.sin((Vv * 0.5 + U * 0.3) * 18 * PI)) ** 3 * (np.abs(Vv) > 0.1) * np.exp(-((np.abs(Vv) - 0.1) / 0.6) ** 2) * 0.6
        Z = Z + vein * 0.08 * (fbm(U * 30, Vv * 30, 33, 3) - 0.5)
    P = origin + U[..., None] * L * d + X[..., None] * side + Z[..., None] * up
    V = P.reshape(-1, 3); Q = grid_quads(nu, nv, False)
    uv = np.stack([Vv * W * 0.5 + 0.0, U * L], -1).reshape(-1, 2)
    part(name, V, Q, mname, uv, None if glow is None else np.full(len(V), glow))

def disc(name, c, n, r, h, mname, nu=None, nv=None, bump=0.0, glow=None):
    nu = nu or (64 if HIGH else 10); nv = nv or (16 if HIGH else 3)
    n = unit(np.asarray(n, float)); a = unit(np.cross(n, [0, 0, 1.0] if abs(n[2]) < 0.9 else [1.0, 0, 0])); b = np.cross(n, a)
    th = np.linspace(0, 2 * PI, nu + 1); rr = np.linspace(0, 1, nv + 1)[1:]
    T, R = np.meshgrid(th, rr, indexing='ij')
    hh = h * np.sqrt(np.clip(1 - R ** 2, 0, 1))
    if HIGH and bump:
        hh = hh + bump * (0.5 + 0.5 * np.sin(T * 40 + R * 90)) * np.abs(np.sin(R * 30 * PI)) * 0.6
    P = c + (R * r * np.cos(T))[..., None] * a + (R * r * np.sin(T))[..., None] * b + hh[..., None] * n
    V = np.vstack([P.reshape(-1, 3), c + n * h]); Q = grid_quads(nu + 1, nv, False)
    j = np.arange(nu); Tr = np.stack([np.full(nu, len(V) - 1), (j + 1) * nv, j * nv], -1)
    uv = np.vstack([np.stack([R * r * np.cos(T), R * r * np.sin(T)], -1).reshape(-1, 2), [[0, 0]]])
    PARTS.append((name, V, [Q, Tr], mname, uv, None if glow is None else np.full(len(V), glow)))

def flower_head(c, axis, n_pet, L, W, shape, mname, curl, cup, tilt, whorls=1, spread=0.0, ruffle=0.3, vein=0.004, glow=None, twist=0.0):
    axis = unit(np.asarray(axis, float))
    for wh in range(whorls):
        for k in range(n_pet):
            a = 2 * PI * (k + 0.5 * wh) / n_pet + rng.uniform(-0.08, 0.08)
            a0 = unit(np.cross(axis, [0, 0, 1.0] if abs(axis[2]) < 0.9 else [1.0, 0, 0])); b0 = np.cross(axis, a0)
            radial = np.cos(a) * a0 + np.sin(a) * b0
            tl = tilt + wh * 0.25 + rng.uniform(-0.1, 0.1)
            d = unit(radial * np.cos(tl) + axis * np.sin(tl))
            up = unit(axis - np.dot(axis, d) * d)
            o = c + radial * spread * (1 + 0.3 * wh) + axis * (-0.006 * wh)
            blade('Petal_%d_%d' % (wh, k), o, d, up, L * rng.uniform(0.92, 1.08), W * rng.uniform(0.9, 1.1), shape, mname,
                  curl=curl * rng.uniform(0.8, 1.2), cup=cup, ruffle=ruffle, vein=vein, glow=glow, twist=twist * rng.uniform(-1, 1))

def at(path, t):
    """point and tangent at fraction t of the path, interpolated (the high and low paths have different point counts,
    so integer indexing put leaves at different heights on the two meshes and the bake rays found nothing)."""
    path = np.asarray(path, float); s = np.linspace(0, 1, len(path)); t = float(np.clip(t, 0, 1))
    p = np.array([np.interp(t, s, path[:, k]) for k in range(3)])
    e = 0.5 / (len(path) - 1); p1 = np.array([np.interp(min(t + e, 1), s, path[:, k]) for k in range(3)]); p0 = np.array([np.interp(max(t - e, 0), s, path[:, k]) for k in range(3)])
    return p, unit(p1 - p0)

def leaves(path, n, L, W, shape, mname, z0=0.1, z1=0.8, serr=0.0, vein=0.004, droop=0.5, glow=None):
    for k in range(n):
        t = z0 + (z1 - z0) * (k + rng.uniform(0.2, 0.8)) / n
        p, tang = at(path, t)
        a = rng.uniform(0, 2 * PI) + k * 2.4
        radial = unit(np.cross(tang, [math.cos(a), math.sin(a), 0.0]))
        d = unit(radial * math.cos(droop) + tang * math.sin(droop))
        blade('Leaf_%d' % k, p, d, unit(np.cross(d, np.cross(radial, d))) * -1 if False else unit(tang - np.dot(tang, d) * d), L * rng.uniform(0.8, 1.1), W, shape, mname,
              curl=0.35, cup=0.25, ruffle=0.15, serr=serr, vein=vein, glow=glow)

ell = lambda p: (lambda u: np.sin(np.clip(u, 0, 1) * PI) ** p)
lanceolate = lambda u: np.sin(np.clip(u, 0, 1) ** 0.8 * PI) ** 0.9
spoon = lambda u: np.clip(np.sin(np.clip(u, 0, 1) * PI) ** 0.6 * (0.4 + 0.6 * u), 0, 1)

if VAR == 'Daisy':       # oxeye daisy, 45 cm, 3 heads
    for h in range(3):
        base = np.array([rng.uniform(-0.03, 0.03), rng.uniform(-0.03, 0.03), 0]); H = rng.uniform(0.35, 0.5)
        lean = rng.uniform(0, 2 * PI); lv = np.array([math.cos(lean), math.sin(lean), 0]) * rng.uniform(0.03, 0.09)
        path = bezier(base, base + [0, 0, H * 0.4], base + lv * 0.6 + [0, 0, H * 0.8], base + lv + [0, 0, H], 60 if HIGH else 8)
        stem('Stem_%d' % h, path, 0.0022, 0.0016)
        leaves(path, 3, 0.05, 0.016, lanceolate, 'Leaf', 0.05, 0.5, serr=0.5)
        top = path[-1]; axis = unit(path[-1] - path[-3]); axis = unit(axis + [0, 0, 0.6])
        flower_head(top, axis, 22, 0.021, 0.0045, ell(0.7), 'PetalWhite', curl=0.25, cup=0.12, tilt=0.12, whorls=2, spread=0.006)
        disc('Center_%d' % h, top + axis * 0.004, axis, 0.0075, 0.004, 'Pollen', bump=0.0012)
elif VAR == 'Poppy':     # red poppy, 55 cm, 2 heads + a bud
    for h in range(3):
        base = np.array([rng.uniform(-0.04, 0.04), rng.uniform(-0.04, 0.04), 0]); H = rng.uniform(0.4, 0.58)
        lean = rng.uniform(0, 2 * PI); lv = np.array([math.cos(lean), math.sin(lean), 0]) * rng.uniform(0.04, 0.12)
        path = bezier(base, base + [0, 0, H * 0.5], base + lv * 0.7 + [0, 0, H * 0.9], base + lv + [0, 0, H], 60 if HIGH else 8)
        stem('Stem_%d' % h, path, 0.0025, 0.0018)
        leaves(path, 3, 0.08, 0.025, ell(0.6), 'Leaf', 0.05, 0.4, serr=0.9, droop=0.4)
        top = path[-1]; axis = unit(unit(path[-1] - path[-3]) + [0, 0, 0.3])
        if h < 2:
            flower_head(top, axis, 4, 0.038, 0.035, spoon, 'PetalRed', curl=-0.15, cup=0.55, tilt=0.55, whorls=2, spread=0.004, ruffle=0.5, vein=0.003)
            disc('Center_%d' % h, top + axis * 0.004, axis, 0.0065, 0.006, 'PollenDark', bump=0.001)
        else:
            Vs, Qs, Ts = superellipsoid(24 if HIGH else 8, 12 if HIGH else 4, 1.0)
            PARTS.append(('Bud', top + axis * 0.012 + Vs * np.array([0.008, 0.008, 0.013]), [Qs, Ts], 'Leaf', np.stack([Vs[:, 0], Vs[:, 2]], -1) * 0.01, None))
elif VAR == 'Foxglove':  # 1.1 m spire of bells
    H = 1.1; lean = rng.uniform(0, 2 * PI); lv = np.array([math.cos(lean), math.sin(lean), 0]) * 0.08
    path = bezier(np.zeros(3), [0, 0, H * 0.45], lv * 0.5 + [0, 0, H * 0.85], lv + [0, 0, H], 120 if HIGH else 14)
    stem('Stem', path, 0.006, 0.0025)
    leaves(path, 5, 0.16, 0.05, ell(0.7), 'Leaf', 0.02, 0.35, serr=0.4, droop=0.35)
    for k in range(24):
        t = 0.42 + 0.56 * k / 24; p, _ = at(path, t)
        a = k * 2.399 + rng.uniform(-0.2, 0.2); radial = np.array([math.cos(a), math.sin(a), 0]); d = unit(radial + [0, 0, -0.55 + 0.3 * (k / 24)])
        n = 10 if HIGH else 4; bl = 0.045 * (1 - 0.5 * (k / 24) ** 2)
        bp = np.array([p + d * bl * s + [0, 0, -0.004 * s] for s in np.linspace(0, 1, n)])
        Vb, Qb, Tb, uvb = sweep(bp, np.tile([0, 0, 1.0], (n, 1)), circ(1.0, 20 if HIGH else 7), caps=False)
        M1 = (20 if HIGH else 7) + 1; G = Vb[:n * M1].reshape(n, M1, 3); ctr = bp[:, None, :]
        s_ = np.linspace(0, 1, n)[:, None, None]; rad = 0.004 + 0.011 * np.sin(np.clip(s_ * 1.15, 0, 1) * PI / 2) ** 0.8 * (1 + 0.15 * np.sin(np.linspace(0, 2 * PI, M1)[None, :, None] * 5) * sstep(0.7, 1.0, s_))
        Vb[:n * M1] = (ctr + (G - ctr) * rad).reshape(-1, 3)
        part('Bell_%d' % k, Vb, Qb, 'PetalPink', uvb * 0.02)
elif VAR == 'Bloodcap':  # realm: fleshy cup flower, 60 cm, veined dark petals around a glowing core
    for h in range(2):
        base = np.array([rng.uniform(-0.05, 0.05), rng.uniform(-0.05, 0.05), 0]); H = rng.uniform(0.45, 0.62)
        lean = rng.uniform(0, 2 * PI); lv = np.array([math.cos(lean), math.sin(lean), 0]) * 0.12
        path = bezier(base, base + [0, 0, H * 0.5], base + lv * 0.4 + [0, 0, H * 0.95], base + lv + [0, 0, H], 70 if HIGH else 9)
        stem('Stem_%d' % h, path, 0.009, 0.005, 'Flesh', bumpy=0.3, glow=0.0)
        top = path[-1]; axis = unit(unit(path[-1] - path[-3]) + [0, 0, 0.5])
        flower_head(top, axis, 6, 0.09, 0.05, ell(0.8), 'FleshPetal', curl=-0.2, cup=0.7, tilt=0.75, whorls=2, spread=0.01, ruffle=0.4, vein=0.008, glow=0.15, twist=0.3)
        disc('Core_%d' % h, top + axis * 0.012, axis, 0.028, 0.024, 'Core', bump=0.004, glow=1.0)
        leaves(path, 3, 0.16, 0.04, lanceolate, 'FleshLeaf', 0.05, 0.5, vein=0.006, glow=0.05)
elif VAR == 'SporeStalk':   # realm: 1.4 m stalk, spore sacs hanging on thin stems, glowing
    H = 1.4; lean = rng.uniform(0, 2 * PI); lv = np.array([math.cos(lean), math.sin(lean), 0]) * 0.2
    path = bezier(np.zeros(3), [0, 0, H * 0.4], lv * 0.3 + [0, 0, H * 0.8], lv + [0, 0, H], 120 if HIGH else 14)
    stem('Stem', path, 0.014, 0.004, 'Flesh', bumpy=0.4, glow=0.0)
    for k in range(9):
        t = 0.35 + 0.6 * k / 9; p, _ = at(path, t)
        a = k * 2.399; radial = np.array([math.cos(a), math.sin(a), 0]); L = 0.09 + 0.05 * rng.random()
        sp = bezier(p, p + radial * L * 0.5 + [0, 0, 0.03], p + radial * L + [0, 0, 0.0], p + radial * L * 1.05 + [0, 0, -L * 0.5], 20 if HIGH else 5)
        stem('Pedicel_%d' % k, sp, 0.0025, 0.0018, 'Flesh', glow=0.0)
        Vs, Qs, Ts = superellipsoid(32 if HIGH else 10, 16 if HIGH else 5, 1.0)
        r_ = 0.022 + 0.01 * rng.random()
        if HIGH: Vs = Vs * (1 + 0.06 * (fbm(Vs[:, 0] * 9, Vs[:, 1] * 9 + k, 41, 3) - 0.5))[:, None]
        PARTS.append(('Sac_%d' % k, sp[-1] + [0, 0, -r_ * 0.9] + Vs * np.array([r_, r_, r_ * 1.35]), [Qs, Ts], 'Sac', np.stack([Vs[:, 0], Vs[:, 2]], -1) * r_, np.full(len(Vs), 0.8)))
    leaves(path, 4, 0.22, 0.03, lanceolate, 'FleshLeaf', 0.03, 0.3, vein=0.006, droop=0.25, glow=0.05)
elif VAR == 'TentacleFern':  # realm: 7 curling fronds with glowing tips, 70 cm
    for k in range(7):
        a = k * 2 * PI / 7 + rng.uniform(-0.2, 0.2); radial = np.array([math.cos(a), math.sin(a), 0]); L = rng.uniform(0.5, 0.75)
        p0 = radial * 0.02; path = bezier(p0, p0 + [0, 0, L * 0.5], p0 + radial * L * 0.5 + [0, 0, L * 0.9], p0 + radial * L * 0.75 + [0, 0, L * 0.55], 90 if HIGH else 12)
        # curl the tip over itself
        tip = path[-1]; tang = unit(path[-1] - path[-2]); curl = np.array([tip + (np.cos(th) * tang - np.sin(th) * np.array([0, 0, 1.0])) * 0.03 * (th / PI) + tang * 0.0 for th in np.linspace(0.3, 2.6, 25 if HIGH else 5)])
        path = np.vstack([path, curl])
        n = len(path); g = np.clip((np.arange(n) - n * 0.55) / (n * 0.45), 0, 1) ** 2
        stem('Frond_%d' % k, path, 0.011, 0.002, 'Flesh', glow=None, bumpy=0.2)
        PARTS[-1] = PARTS[-1][:5] + (np.repeat(g, (24 if HIGH else 6) + 1),)
        for j in range(14 if HIGH else 8):
            t = 0.12 + 0.7 * j / 14; p, tg = at(path, t)
            for s_ in (-1, 1):
                d = unit(np.cross(tg, [0, 0, 1.0]) * s_ * 0.8 + tg * 0.35 + [0, 0, 0.1])
                blade('Pinna_%d_%d_%d' % (k, j, s_ > 0), p, d, unit(np.cross(d, np.cross(tg, d))), 0.07 * (1 - 0.6 * t) + 0.02, 0.012, ell(0.8), 'FleshLeaf', curl=0.4, cup=0.2, ruffle=0.2, vein=0.004, glow=0.15 * t)
elif VAR == 'CorruptPatch':  # 2 m irregular patch of corrupted ground: cracked, veined flesh-earth with glowing fissures
    n_a, n_r = (256, 48) if HIGH else (48, 8)
    th = np.linspace(0, 2 * PI, n_a + 1); rr = np.linspace(0, 1, n_r + 1)
    T, R = np.meshgrid(th, rr, indexing='ij')
    edge_r = 1.0 * (1 + 0.18 * (fbm(np.cos(T) * 2 + 5, np.sin(T) * 2, 51, 4) - 0.5) * 2)
    X, Y = R * edge_r * np.cos(T), R * edge_r * np.sin(T)
    Z = np.zeros_like(X)
    if HIGH:
        Z = 0.012 * (fbm(X * 3, Y * 3, 52, 4) - 0.5) + 0.004 * (fbm(X * 12, Y * 12, 53, 4) - 0.5)
        # veins: ridges that wander outward from the centre
        ang = np.arctan2(Y, X); vr = np.sin(ang * 7 + 4 * fbm(X * 1.5, Y * 1.5, 54, 3)) ** 2
        Z = Z + 0.008 * np.exp(-((vr - 1) / 0.08) ** 2) * sstep(0.95, 0.4, R)
        # bubbles
        bub = fbm(X * 6 + 3, Y * 6, 55, 2); Z = Z + 0.014 * np.clip((bub - 0.62) / 0.1, 0, 1) ** 0.5
    Z = Z * sstep(1.0, 0.75, R)                                      # flat at the rim so it blends into the ground
    V = np.stack([X, Y, Z], -1).reshape(-1, 3); Q = grid_quads(n_a + 1, n_r + 1, False)
    glow = np.zeros(len(V))
    PARTS.append(('Patch', V, Q, 'Corrupt', np.stack([X, Y], -1).reshape(-1, 2), glow))
    # a few flesh bulbs breaking the surface
    for k in range(5 if HIGH else 5):
        a = rng.uniform(0, 2 * PI); r_ = rng.uniform(0.15, 0.7); c = np.array([r_ * math.cos(a), r_ * math.sin(a), -0.01])
        Vs, Qs, Ts = superellipsoid(32 if HIGH else 10, 16 if HIGH else 5, 1.0); sz = rng.uniform(0.05, 0.11)
        if HIGH: Vs = Vs * (1 + 0.05 * (fbm(Vs[:, 0] * 7 + k, Vs[:, 1] * 7, 56, 3) - 0.5))[:, None]
        PARTS.append(('Bulb_%d' % k, c + Vs * np.array([sz, sz * 0.8, sz * 0.5]), [Qs, Ts], 'Sac', np.stack([Vs[:, 0], Vs[:, 2]], -1) * sz, np.full(len(Vs), 0.6)))

elif VAR == 'BlobMine':  # realm: 0.5 m bio land mine: a quivering membrane sac on a flesh skirt, pustules on top, tendrils rooting it
    Vs, Qs, Ts = superellipsoid(64 if HIGH else 20, 32 if HIGH else 10, 1.0)
    bump = 0.08 * (fbm(Vs[:, 0] * 2.5 + 1, Vs[:, 1] * 2.5 + Vs[:, 2], 61, 3) - 0.5) * 2
    if HIGH: bump = bump + 0.015 * (fbm(Vs[:, 0] * 12, Vs[:, 1] * 12 + Vs[:, 2] * 6, 62, 4) - 0.5) * 2
    V = Vs * (1 + bump)[:, None] * np.array([0.25, 0.23, 0.20]); V[:, 2] = np.maximum(V[:, 2], -0.15) + 0.16
    V[:, 2] = V[:, 2] - 0.03 * np.clip(V[:, 2] / 0.36, 0, 1) ** 3 * (np.linalg.norm(V[:, :2], axis=1) / 0.25)      # sags over the skirt
    PARTS.append(('Sac', V, [Qs, Ts], 'Sac', np.stack([np.arctan2(Vs[:, 1], Vs[:, 0]) * 0.25, Vs[:, 2] * 0.2], -1), 0.55 + 0.4 * np.clip(Vs[:, 2], 0, 1)))
    for k in range(4):   # pustules: the trigger spots
        a = k * 1.9 + 0.4; r_ = 0.09 + 0.05 * (k % 2); c = np.array([r_ * math.cos(a), r_ * math.sin(a), 0.16 + 0.19 * math.sqrt(max(1 - (r_ / 0.25) ** 2, 0)) - 0.012])
        Vp, Qp, Tp = superellipsoid(24 if HIGH else 8, 12 if HIGH else 4, 1.0); sz = 0.028 + 0.012 * (k == 0)
        PARTS.append(('Pustule_%d' % k, c + Vp * np.array([sz, sz, sz * 0.8]), [Qp, Tp], 'Core', np.stack([Vp[:, 0], Vp[:, 2]], -1) * sz, np.full(len(Vp), 1.0)))
    Vk, Qk, Tk = superellipsoid(64 if HIGH else 20, 12 if HIGH else 5, 0.8)
    skirt = Vk * (1 + 0.12 * (fbm(Vk[:, 0] * 3, Vk[:, 1] * 3, 63, 3) - 0.5) * 2)[:, None] * np.array([0.34, 0.31, 0.045]); skirt[:, 2] += 0.03
    PARTS.append(('Skirt', skirt, [Qk, Tk], 'Flesh', np.stack([Vk[:, 0], Vk[:, 1]], -1) * 0.3, np.full(len(Vk), 0.1)))
    for k in range(6):   # tendrils rooting it into the ground
        a = k * 2 * PI / 6 + rng.uniform(-0.3, 0.3); radial = np.array([math.cos(a), math.sin(a), 0]); L = rng.uniform(0.25, 0.42)
        path = bezier(radial * 0.2 + [0, 0, 0.06], radial * (0.2 + L * 0.4) + [0, 0, 0.05], radial * (0.2 + L * 0.8) + [0, 0, 0.0], radial * (0.2 + L) + [0, 0, -0.03], 40 if HIGH else 7)
        stem('Tendril_%d' % k, path, 0.016, 0.004, 'Flesh', bumpy=0.3, glow=0.15)
elif VAR == 'EggCluster':   # realm: 0.7 m clutch of translucent eggs half sunk in a flesh mound, two hatched
    Vk, Qk, Tk = superellipsoid(64 if HIGH else 20, 14 if HIGH else 5, 0.9)
    mound = Vk * (1 + 0.14 * (fbm(Vk[:, 0] * 2.5, Vk[:, 1] * 2.5 + 2, 64, 3) - 0.5) * 2)[:, None] * np.array([0.36, 0.31, 0.085]); mound[:, 2] += 0.045
    if HIGH: mound = mound * (1 + 0.02 * (fbm(Vk[:, 0] * 10, Vk[:, 1] * 10, 65, 4) - 0.5) * 2)[:, None]
    PARTS.append(('Mound', mound, [Qk, Tk], 'Flesh', np.stack([Vk[:, 0], Vk[:, 1]], -1) * 0.33, np.full(len(Vk), 0.08)))
    for k in range(9):
        a = k * 2.399; r_ = 0.03 + 0.24 * math.sqrt(k / 9); c = np.array([r_ * math.cos(a), r_ * math.sin(a), 0.135 - 0.04 * (r_ / 0.27)])
        Ve, Qe, Te = superellipsoid(32 if HIGH else 10, 16 if HIGH else 5, 1.0); sz = rng.uniform(0.055, 0.075)
        if HIGH: Ve = Ve * (1 + 0.03 * (fbm(Ve[:, 0] * 8 + k, Ve[:, 1] * 8, 66, 3) - 0.5))[:, None]
        tilt = rng.uniform(0, 0.35); ca, sa = math.cos(tilt), math.sin(tilt)
        E = Ve * np.array([sz, sz * 0.95, sz * 1.4]); E = E @ np.array([[1, 0, 0], [0, ca, -sa], [0, sa, ca]]).T
        if k < 2:   # hatched: the top torn open (cut the upper third off, the rim ragged)
            keep = E[:, 2] < sz * 0.55; E[:, 2] = np.minimum(E[:, 2], sz * (0.5 + 0.1 * (fbm(Ve[:, 0] * 6, Ve[:, 1] * 6, 67, 3) - 0.5) * 2))
        PARTS.append(('Egg_%d' % k, c + E, [Qe, Te], 'Sac', np.stack([np.arctan2(Ve[:, 1], Ve[:, 0]) * sz, Ve[:, 2] * sz], -1), np.full(len(Ve), 0.25 if k < 2 else 0.45 + 0.3 * rng.random())))
for name, V, Q, mname, uv, glow in PARTS:
    blocks = Q if isinstance(Q, list) else [Q]
    mesh(name, V, blocks, mname, uv=uv, attrs={'glow': glow} if glow is not None else None)
tris = sum(len(p.vertices) - 2 for o in bpy.data.objects if o.type == 'MESH' for p in o.data.polygons)
print('TRIS', tris, 'VERTS', sum(len(o.data.vertices) for o in bpy.data.objects if o.type == 'MESH'))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'Flora%s_%s.blend' % (VAR, 'high' if HIGH else 'low')))
print('BUILD OK')
