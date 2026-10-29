# "Emberoath", legendary short sword (laptop2, 2026-10-29): pattern-welded blade with an ember-glowing rune fuller,
# gilded guard set with amber, gold-wire leather grip, wheel pommel bearing the castle-tower crest of the heater shield.
#   blender -b --factory-startup -P build_sword.py      (env RES = low | high)
# low  = game mesh (~4k tris)                       -> Sword_low.blend
# high = bake source (blade 0.15 mm, runes engraved) -> Sword_high.blend + masks_sword/runes.png
# Units: metres. The blade points +Z, the edges lie along X, the flat faces look toward -Y/+Y. The pivot is the
# centre of the grip (z = -0.0475), where the hand socket goes; sword_meta.json has it.
import os, sys, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np
bpy.ops.wm.read_factory_settings(use_empty=True)
from shieldkit import fbm, sstep, mesh, grid_quads, orient, unit, sweep, rrect, circ, add, emit, dome, superellipsoid, HIGH, PI
D = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(D, 'masks_sword'), exist_ok=True)

# ---------------- blade ----------------
Z0, Z1 = 0.020, 0.525                      # blade from the guard to the point
RIC = 0.050                                 # ricasso (flat, unsharpened) up to here
def hw(z):                                  # half width: 29 mm at the base, a slight leaf swell, then the point
    t = np.clip((z - Z0) / (Z1 - Z0), 0, 1)
    w = 0.0335 - 0.0075 * t + 0.0050 * np.sin(np.clip(t / 0.75, 0, 1) * PI) * (t < 0.75)
    tip = np.clip((t - 0.78) / 0.22, 0, 1)
    return np.maximum(w * np.sqrt(np.clip(1 - tip ** 1.6, 0, 1)), 0.0)
def th(z):                                  # thickness: 6.5 mm at the base, 2.5 mm near the point (distal taper)
    t = np.clip((z - Z0) / (Z1 - Z0), 0, 1); return 0.0065 - 0.0040 * t
FZ0, FZ1, FW = 0.058, 0.395, 0.0085         # fuller: from/to, half width
def fuller_w(z): return FW * sstep(FZ0, FZ0 + 0.02, z) * sstep(FZ1, FZ1 - 0.04, z)
def blade_y(u, z, fuller_depth=0.0016):
    """half thickness profile across the blade. u in [-1, 1] (edge to edge)."""
    a = np.abs(u)
    plateau = np.where(a < 0.42, 1.0, 1.0 - (a - 0.42) / 0.58 * 0.93)                 # flat, then the edge bevel
    plateau = plateau - 0.05 * sstep(0.88, 1.0, a) * (z > RIC)                          # a secondary (sharpening) bevel
    plateau = np.where(z < RIC, np.maximum(plateau, 0.55), plateau)                     # ricasso: blunt square edges
    y = th(z) / 2 * plateau
    x = u * hw(z)
    fw = fuller_w(z)
    fg = np.where(fw > 1e-5, np.clip(1 - (x / np.maximum(fw, 1e-5)) ** 2, 0, 1) ** 0.6, 0.0)
    return y - fuller_depth * fg * sstep(0.0, 0.002, fw)

# runes: a band of engraved glyphs down the fuller, built from straight strokes (staves, branches, crossbars)
RX, RZ0, RZ1, RNX, RNZ = 0.0075, 0.075, 0.385, 192, 4096
def rune_mask(xs, zs):
    X, Z = (xs, zs) if np.ndim(xs) == 2 else np.meshgrid(xs, zs)
    m = np.zeros_like(X)
    rng = np.random.default_rng(1291)
    gh, gap = 0.016, 0.006                      # glyph height, gap
    z = RZ0
    while z + gh < RZ1:
        segs = [((0, 0), (0, 1))]                # the stave
        for _ in range(rng.integers(1, 4)):
            y0 = rng.choice([0.0, 0.25, 0.5, 0.75]); s = rng.choice([-1, 1])
            kind = rng.integers(0, 3)
            if kind == 0: segs.append(((0, y0), (s * 0.55, y0 + 0.30)))         # branch up
            elif kind == 1: segs.append(((0, y0 + 0.3), (s * 0.55, y0)))       # branch down
            else: segs.append(((-0.5, y0 + 0.15), (0.5, y0 + 0.15)))          # crossbar
        for (ax, ay), (bx, by) in segs:
            p0 = np.array([ax * 0.0055, z + ay * gh]); p1 = np.array([bx * 0.0055, z + min(by, 1) * gh])
            v = p1 - p0; L2 = max(v @ v, 1e-12)
            t = np.clip(((X - p0[0]) * v[0] + (Z - p0[1]) * v[1]) / L2, 0, 1)
            d = np.hypot(X - p0[0] - t * v[0], Z - p0[1] - t * v[1])
            m = np.maximum(m, np.clip(1 - (d - 0.00055) / 0.00025, 0, 1))
        z += gh + gap
        if rng.random() < 0.25: z += gap * 1.5                                    # word breaks
    return m * (np.abs(X) < fuller_w(Z) * 0.85)

def blade(hi):
    nu = 121 if hi else 9
    nz = 3400 if hi else 26
    if hi: zz = np.linspace(Z0, Z1, nz)
    else: zz = np.r_[np.linspace(Z0, RIC, 3), np.linspace(RIC + 0.01, Z1 - 0.12, 15), Z1 - np.linspace(0.11, 0.0, 8) ** 1.0 * 1.0][:]
    zz = np.unique(np.clip(zz, Z0, Z1)); nz = len(zz)
    u = np.sin(np.linspace(-PI / 2, PI / 2, nu)) if not hi else np.linspace(-1, 1, nu)
    if not hi: u = np.array([-1, -0.88, -0.42, -0.25, 0.0, 0.25, 0.42, 0.88, 1.0])
    U, Zg = np.meshgrid(u, zz)
    X = U * hw(Zg)
    Yf = blade_y(U, Zg, 0.0016 if hi else 0.0)
    if hi:
        rm = rune_mask(np.clip(X, -RX, RX), Zg)
        Yf = Yf - 0.00028 * rm
        Yf = Yf + 0.00003 * (fbm(X * 3000, Zg * 300, 141, 3) - 0.5)            # polishing strokes
    else:
        Yf = blade_y(U, Zg, 0.0016)
    # loop: front (y<0) edge to edge, then back (y>0) edge to edge without repeating the edge vertices
    Vfront = np.stack([X, -Yf, Zg], -1)
    Vback = np.stack([X[:, ::-1], Yf[:, ::-1], Zg], -1)[:, 1:-1]
    V = np.concatenate([Vfront, Vback, Vfront[:, :1]], 1)                         # seam column repeated (UV seam)
    M = V.shape[1]
    Q = grid_quads(nz, M, False)
    per = np.r_[0, np.cumsum(np.linalg.norm(np.diff(V[nz // 3], axis=0), axis=1))]
    uv = np.stack(np.broadcast_arrays(per[None, :] * (hw(zz)[:, None] / max(hw(zz[nz // 3]), 1e-4)), zz[:, None]), -1)
    Vf = V.reshape(-1, 3); uvf = uv.reshape(-1, 2)
    Q = orient(Vf, Q[: (nz - 1) * (M - 1) // 2 * 0 + len(Q)], np.array([0, -1.0, 0])) if False else Q
    # base cap (inside the guard) as a fan
    c0 = len(Vf); Vf = np.vstack([Vf, [[0, 0, Z0]]]); uvf = np.vstack([uvf, [[0, 0]]])
    j = np.arange(M - 1); T = np.stack([np.full(M - 1, c0), j + 1, j], -1)
    return Vf, Q, T, uvf, M, nz
Vb, Qb, Tb, uvb, Mb, nzb = blade(HIGH)
# make the front face's normal point -Y
f = Qb[(nzb // 2) * (Mb - 1) + (Mb - 1) // 4]
if np.cross(Vb[f[1]] - Vb[f[0]], Vb[f[2]] - Vb[f[0]])[1] > 0: Qb = Qb[:, ::-1]; Tb = Tb[:, ::-1]
mesh('Blade', Vb, [Qb, Tb], 'Blade', uv=uvb)
if HIGH:
    xs = np.linspace(-RX, RX, RNX); zs = np.linspace(RZ0, RZ1, RNZ)
    rm = np.vstack([rune_mask(xs, zs[c:c + 256]) for c in range(0, RNZ, 256)])
    im = bpy.data.images.new('M_runes', RNX, RNZ, alpha=False)
    im.pixels.foreach_set(np.stack([rm, rm, rm, np.ones_like(rm)], -1).astype(np.float32).ravel())
    im.filepath_raw = os.path.join(D, 'masks_sword', 'runes.png'); im.file_format = 'PNG'; im.save()
    json.dump({'x0': -RX, 'x1': RX, 'z0': RZ0, 'z1': RZ1}, open(os.path.join(D, 'masks_sword', 'masks.json'), 'w'))

# ---------------- guard: gilded quillons with ball terminals, a centre block holding amber on both faces ----------------
def quillon(sgn, hi):
    n = 120 if hi else 10
    t = np.linspace(0, 1, n)
    x = sgn * (0.010 + 0.082 * t)                                                     # starts buried in the centre block
    z = 0.012 + 0.016 * t ** 2.2                                                      # sweeps gently toward the blade
    path = np.stack([x, np.zeros(n), z], -1)
    prof = rrect(1.0, 1.0, 32 if hi else 8, 3.2)
    V, Q, Tr, uv = sweep(path, np.tile([0, 1.0, 0], (n, 1)), prof)
    M1 = len(prof) + 1
    G = V[:n * M1].reshape(n, M1, 3); off = G - path[:, None, :]
    sz = np.interp(t, [0, 0.7, 1], [0.0105, 0.0080, 0.0068])     # half height (along the blade)
    sy = np.interp(t, [0, 0.7, 1], [0.0118, 0.0088, 0.0074])     # half depth
    if hi:   # a raised spine ridge along the top of each quillon
        ang = np.linspace(0, 2 * PI, M1)
        sz = sz[:, None] * (1 + 0.10 * np.exp(-((np.sin(ang) - 1) / 0.2) ** 2))[None, :]
        sy = sy[:, None] * np.ones((1, M1))
    else:
        sz, sy = sz[:, None], sy[:, None]
    tdir = unit(np.gradient(path, axis=0)); updir = np.tile([0, 1.0, 0], (n, 1)); sd = unit(np.cross(tdir, updir))
    a_side = (off * sd[:, None, :]).sum(-1); a_up = off[..., 1]
    G2 = path[:, None, :] + a_side[..., None] * sz[..., None] * sd[:, None, :] + a_up[..., None] * sy[..., None] * np.array([0, 1.0, 0])
    V[:n * M1] = G2.reshape(-1, 3)
    K = M1 - 1; V[n * M1:n * M1 + K] = G2[0, :K]; V[n * M1 + K:n * M1 + 2 * K] = G2[-1, :K]; V[-2:] = [path[0], path[-1]]
    uv[:n * M1, 0] *= 0.008; uv[n * M1:] *= 0.008
    return V, Q, Tr, uv, path[-1]
parts = []
for sgn in (-1, 1):
    V, Q, Tr, uv, tip = quillon(sgn, HIGH)
    add(parts, V, Q, Tr, uv)
    Vs, Qs, Ts = superellipsoid(32 if HIGH else 8, 16 if HIGH else 4, 1.0)
    c = tip + np.array([sgn * 0.004, 0, 0.001])
    add(parts, c + Vs * 0.0102, Qs, Ts, np.stack([Vs[:, 0], Vs[:, 2]], -1) * 0.0102)
# centre block (escutcheon) with short langets down the blade
Vs, Qs, Ts = superellipsoid(48 if HIGH else 10, 24 if HIGH else 6, 0.30)
cb = np.array([0, 0, 0.013])
add(parts, cb + Vs * np.array([0.025, 0.0130, 0.019]), Qs, Ts, np.stack([Vs[:, 0] * 0.022 + Vs[:, 1] * 0.012, Vs[:, 2] * 0.017], -1))
for sy_ in (-1, 1):   # langets: thin tongues lying on the blade faces
    Vs, Qs, Ts = superellipsoid(24 if HIGH else 6, 12 if HIGH else 3, 0.35)
    cl = np.array([0, sy_ * (th(0.035) / 2 + 0.0008), 0.040])
    add(parts, cl + Vs * np.array([0.0065, 0.0012, 0.014]), Qs, Ts, np.stack([Vs[:, 0] * 0.0065, Vs[:, 2] * 0.014], -1))
# gem bezels (gold rims around the stones): high poly only, too thin to bake onto as their own low-poly parts
for sy_ in ((-1, 1) if HIGH else ()):
    a = np.linspace(0, 2 * PI, 64 if HIGH else 10, endpoint=False)
    ring = np.stack([0.0105 * np.cos(a), np.full_like(a, sy_ * 0.0118), 0.013 + 0.0078 * np.sin(a)], -1)
    V, Q, Tr, uv = sweep(ring, np.tile([0, sy_ * 1.0, 0], (len(a), 1)), circ(0.0014, 12 if HIGH else 5), closed=True, caps=False)
    add(parts, V, Q, Tr, uv)
emit('Guard', parts, 'Gold')
# amber cabochons
parts = []
for sy_ in (-1, 1):
    Vs, Qs, Ts = superellipsoid(48 if HIGH else 10, 24 if HIGH else 5, 1.0)
    Vs[:, 1] = np.maximum(Vs[:, 1] * sy_, -0.2) * sy_                                  # a dome, flattened behind
    add(parts, np.array([0, sy_ * 0.0112, 0.013]) + Vs * np.array([0.0095, 0.0045, 0.0070]), Qs, Ts, np.stack([Vs[:, 0], Vs[:, 2]], -1) * 0.01)
emit('Gem', parts, 'Gem')

# ---------------- grip: leather over a wooden core, twisted gold wire in the grooves, gilded ferrules ----------------
GZ0, GZ1 = -0.095, 0.0
ng = 300 if HIGH else 10; nsg = 48 if HIGH else 10
zg = np.linspace(GZ0 + 0.006, GZ1 - 0.006, ng)
path = np.stack([np.zeros(ng), np.zeros(ng), zg], -1)
V, Q, Tr, uv = sweep(path, np.tile([0, 1.0, 0], (ng, 1)), circ(1.0, nsg))
M1 = nsg + 1; G = V[:ng * M1].reshape(ng, M1, 3)
tt = (zg - GZ0) / (GZ1 - GZ0)
swell = 1 + 0.10 * np.sin(np.clip(tt, 0, 1) * PI)
rx = 0.0148 * swell; ry = 0.0118 * swell
ang = np.linspace(0, 2 * PI, M1)
rr = np.ones((ng, M1))
if HIGH:
    ph = np.mod(zg[:, None] / 0.0105 + ang[None, :] / (2 * PI), 1.0)                     # leather turns
    rr = 1 + 0.035 * np.abs(np.sin(PI * ph)) ** 0.5 - 0.06 * (ph < 0.05)
G[..., 0] = rx[:, None] * np.cos(ang)[None] * rr; G[..., 1] = ry[:, None] * np.sin(ang)[None] * rr
V[:ng * M1] = G.reshape(-1, 3); K = M1 - 1
V[ng * M1:ng * M1 + K] = G[0, :K]; V[ng * M1 + K:ng * M1 + 2 * K] = G[-1, :K]
uv[:ng * M1, 0] *= 0.014; uv[ng * M1:] *= 0.014
mesh('Grip', V, [Q, Tr], 'Leather', uv=uv)
parts = []
if HIGH:   # the twisted gold wire sits in the grooves between the leather turns
    for k in range(2):
        n = 1600; t = np.linspace(0, 1, n); zw = GZ0 + 0.007 + t * (GZ1 - GZ0 - 0.014)
        tw = (zw - GZ0) / (GZ1 - GZ0); sw = 1 + 0.10 * np.sin(tw * PI)
        a = 2 * PI * ((zw / 0.0105) % 1.0) * -1 + k * 0.0 + 2 * PI * 0.05
        base = np.stack([0.0148 * sw * np.cos(a) * 1.01, 0.0118 * sw * np.sin(a) * 1.01, zw], -1)
        tw2 = 2 * PI * t * 380 + k * PI
        nrm = unit(np.stack([np.cos(a) / 0.0148, np.sin(a) / 0.0118, np.zeros(n)], -1))
        tan = unit(np.gradient(base, axis=0)); bi = np.cross(tan, nrm)
        wire = base + 0.00055 * (np.cos(tw2)[:, None] * nrm + np.sin(tw2)[:, None] * bi)
        Vw, Qw, Tw, uw = sweep(wire, nrm, circ(0.00045, 8))
        add(parts, Vw, Qw, Tw, uw)
# ferrules at both ends of the grip
for zc, s in ((GZ1 - 0.004, 1), (GZ0 + 0.004, -1)):
    n = 24 if HIGH else 3; zz = np.linspace(zc - 0.004, zc + 0.004, n)
    path = np.stack([np.zeros(n), np.zeros(n), zz], -1)
    V, Q, Tr, uv = sweep(path, np.tile([0, 1.0, 0], (n, 1)), circ(1.0, 48 if HIGH else 10))
    M1f = (48 if HIGH else 10) + 1; G = V[:n * M1f].reshape(n, M1f, 3); a = np.linspace(0, 2 * PI, M1f)
    bulge = 1.08 + 0.05 * np.sin(np.linspace(0, PI, n))
    if HIGH: bulge = bulge + 0.02 * (np.abs(np.linspace(-1, 1, n)) < 0.2)   # a fine bead in the middle
    G[..., 0] = 0.0155 * bulge[:, None] * np.cos(a)[None]; G[..., 1] = 0.0125 * bulge[:, None] * np.sin(a)[None]
    V[:n * M1f] = G.reshape(-1, 3); K = M1f - 1; V[n * M1f:n * M1f + K] = G[0, :K]; V[n * M1f + K:n * M1f + 2 * K] = G[-1, :K]
    uv[:n * M1f, 0] *= 0.015; uv[n * M1f:] *= 0.015
    add(parts, V, Q, Tr, uv)

# ---------------- pommel: a wheel with a raised castle-tower medallion on each face, and the peen block ----------------
PZ = -0.118
def box_sdf(x, z, x0, x1, z0, z1): return np.maximum(np.maximum(x0 - x, x - x1), np.maximum(z0 - z, z - z1))
def tower(x, z):   # the heater shield's tower, scaled to the medallion (unit = medallion radius)
    t = np.minimum(box_sdf(x, z, -0.42, 0.42, -0.55, 0.40), box_sdf(x, z, -0.48, 0.48, -0.62, -0.52))
    for k in range(4): x0 = -0.42 + k * 0.24; t = np.minimum(t, box_sdf(x, z, x0, x0 + 0.13, 0.40, 0.62))
    gate = np.minimum(box_sdf(x, z, -0.13, 0.13, -0.62, -0.30), np.hypot(x, z + 0.30) - 0.13)
    return np.maximum(t, -gate)
nr, na = (90, 160) if HIGH else (5, 20)
a = np.linspace(0, 2 * PI, na + 1)
rads = np.linspace(0, 1, nr)
Rp, Ap = np.meshgrid(rads, a)
px, pz = Rp * np.cos(Ap), Rp * np.sin(Ap)
PR = 0.026; PT = 0.0135                                                    # radius, half thickness
def face_y(rn, xn, zn, hi):
    y = PT * (1 - 0.35 * rn ** 2)                                           # domed faces
    y = y - 0.0018 * sstep(0.62, 0.66, rn) * sstep(0.78, 0.74, rn)          # a ring groove around the medallion
    if hi:
        tw = tower(xn / 0.6, zn / 0.6)
        y = y + 0.0007 * np.clip(0.5 - tw / 0.03, 0, 1) * (rn < 0.6)        # the raised tower
        y = y + 0.00012 * (fbm(xn * 60, zn * 60, 151, 3) - 0.5)
    return y
parts_p = []
for sgn in (-1, 1):
    yv = face_y(Rp, px, pz, HIGH) * sgn
    V = np.stack([px * PR, yv, PZ + pz * PR], -1).reshape(-1, 3)
    Q = grid_quads(na + 1, nr, False)
    Q = Q if sgn > 0 else Q[:, ::-1]
    f = Q[len(Q) // 2]
    if np.cross(V[f[1]] - V[f[0]], V[f[2]] - V[f[0]])[1] * sgn < 0: Q = Q[:, ::-1]
    add(parts_p, V, Q, np.zeros((0, 3), int), np.stack([px * PR * sgn, pz * PR], -1).reshape(-1, 2))
# the rim band of the wheel (a bevelled edge between the two faces)
nb = 24 if HIGH else 4
bprof = np.array([[PR * (1 - 0.02 * math.sin(q) ** 2 * 0), (PT * 0.65) * math.cos(q)] for q in np.linspace(0, PI, nb + 1)])
yy = PT * 0.65 * np.cos(np.linspace(0, PI, nb + 1)); rb = PR * (1 + 0.04 * np.sin(np.linspace(0, PI, nb + 1)))
A2, J = np.meshgrid(a, np.arange(nb + 1), indexing='ij')
V = np.stack([rb[J] * np.cos(A2), yy[J], PZ + rb[J] * np.sin(A2)], -1).reshape(-1, 3)
Q = grid_quads(na + 1, nb + 1, False)
f = Q[len(Q) // 3]; cfa = V[f].mean(0)
if np.dot(np.cross(V[f[1]] - V[f[0]], V[f[2]] - V[f[0]]), [cfa[0], 0, cfa[2] - PZ]) < 0: Q = Q[:, ::-1]
add(parts_p, V, Q, np.zeros((0, 3), int), np.stack([A2 * PR, yy[J]], -1).reshape(-1, 2))
# peen block on top of the pommel (the tang riveted over)
Vs, Qs, Ts = superellipsoid(24 if HIGH else 6, 12 if HIGH else 3, 0.35)
add(parts_p, np.array([0, 0, PZ - PR - 0.004]) + Vs * np.array([0.0065, 0.0055, 0.0045]), Qs, Ts, np.stack([Vs[:, 0], Vs[:, 2]], -1) * 0.006)
# neck between grip and pommel
Vs, Qs, Ts = superellipsoid(32 if HIGH else 8, 12 if HIGH else 3, 0.6)
add(parts_p, np.array([0, 0, GZ0 - 0.002]) + Vs * np.array([0.0125, 0.0105, 0.0060]), Qs, Ts, np.stack([Vs[:, 0], Vs[:, 2]], -1) * 0.012)
emit('Pommel', parts_p + parts, 'Gold')

# the superellipsoid parts got planar UVs whose front and back faces overlap (the back gem showed on the front):
# give them a real unwrap with seams on the low poly
if not HIGH:
    for nm in ('Guard', 'Pommel', 'Gem'):
        o = bpy.data.objects[nm]
        bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
        bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.004, scale_to_bounds=False)
        bpy.ops.object.mode_set(mode='OBJECT')
GRIP = [0.0, 0.0, (GZ0 + GZ1) / 2]
json.dump({'grip': GRIP, 'blade_axis': [0, 0, 1], 'length': Z1 - (PZ - PR - 0.008)}, open(os.path.join(D, 'sword_meta.json'), 'w'))
tris = sum(len(p.vertices) - 2 for o in bpy.data.objects if o.type == 'MESH' for p in o.data.polygons)
print('TRIS', tris, 'VERTS', sum(len(o.data.vertices) for o in bpy.data.objects if o.type == 'MESH'))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'Sword_%s.blend' % ('high' if HIGH else 'low')))
print('BUILD OK')
