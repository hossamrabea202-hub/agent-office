# Round wooden shield (laptop2, 2026-10-29): seven bare linden planks, tapered board, iron boss, laced rawhide rim.
#   blender -b --factory-startup -P build_round.py      (env RES = low | high)
# low  = game mesh (~6k tris, real-world-scale UVs)                          -> Round_low.blend
# high = bake source (1 mm grids, gashes, scorch, nicks, lacing, hammered boss) -> Round_high.blend + masks_round/*.png
# Units: metres, Z up, the front looks toward -Y, the shield centre at (0, 0, 0.40) so the bottom edge sits at z 0.
# The pivot (hand grip centre) goes to round_meta.json and is applied when the FBX is exported.
import os, sys, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np
bpy.ops.wm.read_factory_settings(use_empty=True)
import shieldkit as K
from shieldkit import fbm, sstep, mesh, grid_quads, orient, unit, sweep, rrect, circ, add, emit, dome, sqrove, _hash, HIGH, PI
D = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(D, 'masks_round'), exist_ok=True)

R, RH, ZC = 0.40, 0.064, 0.40           # radius, hand hole radius, centre height
def thick(r): return 0.0105 - 0.0045 * sstep(0.12, 0.40, r)          # thick in the middle, 6 mm at the rim (period practice)
def yfr(r): return -thick(r) / 2
def ybr(r): return thick(r) / 2
# seven planks of slightly different widths, butt-joined, grain vertical
W_ = np.array([0.105, 0.120, 0.110, 0.125, 0.115, 0.108, 0.117]); W_ = W_ / W_.sum() * 0.82
EDGES = -0.41 + np.r_[0, np.cumsum(W_)]
SEAMS = EDGES[1:-1]
def plank_id(x): return np.clip(np.searchsorted(EDGES, x) - 1, 0, 6)
# battle damage: gashes (x0,z0,x1,z1 relative to the centre, depth, width), dents (x,z,r,depth), rim nicks (angle deg, depth, half width)
GASH = [(-0.26, 0.16, -0.08, 0.05, 0.0035, 0.0055), (0.08, 0.27, 0.25, 0.13, 0.0030, 0.0050), (0.12, -0.10, 0.30, -0.19, 0.0040, 0.0060),
        (-0.30, -0.06, -0.17, -0.23, 0.0025, 0.0040), (-0.05, -0.17, 0.07, -0.30, 0.0022, 0.0040), (-0.20, 0.27, -0.07, 0.33, 0.0020, 0.0035)]
DENT = [(0.20, 0.06, 0.035, 0.0018), (-0.14, -0.12, 0.030, 0.0015), (0.03, 0.22, 0.028, 0.0014), (-0.24, 0.10, 0.026, 0.0012)]
HOLE = (0.17, -0.25)                     # an arrow went through here (no arrow left in it)
SCORCH = (-0.18, -0.26, 0.11)            # torch / burning-oil scorch near the lower left rim
NICK = [(20, 0.009, 0.012), (75, 0.006, 0.009), (140, 0.011, 0.014), (200, 0.007, 0.010), (255, 0.010, 0.013), (320, 0.006, 0.008)]
def nick_depth(ang):
    d = np.zeros_like(ang)
    for a0, dep, hw in NICK:
        da = np.abs(((ang - math.radians(a0)) + PI) % (2 * PI) - PI) * R
        d = np.maximum(d, dep * np.clip(1 - da / hw, 0, 1) ** 0.8)
    return d

def masks(xs, zs):
    """xs, zs relative to the shield centre. Front damage masks + displacement."""
    X, Z = np.meshgrid(xs, zs); r = np.hypot(X, Z); ang = np.arctan2(Z, X)
    out = {}
    pid = plank_id(X)
    disp = (np.array([_hash(k, 1, 91) for k in range(7)])[pid] - 0.5) * 0.0007          # planks never sit perfectly flush
    disp += 0.00022 * (fbm(X * 420, Z * 11, 92, 4) - 0.5) * 2                              # grain, raised by weathering
    disp += 0.00018 * np.sin(2 * PI * (Z / 0.05 + np.array([_hash(k, 2, 93) for k in range(7)])[pid]) + 3 * fbm(X * 15, Z * 5, 94, 3))   # draw-knife marks
    ds = np.min([np.abs(X - s) for s in SEAMS], axis=0)
    gap = sstep(0.38, 0.55, fbm(Z * 25, X * 3, 95, 3))
    disp += 0.0007 * np.exp(-(ds / 0.0008) ** 2) * (0.5 + 0.5 * gap)
    crack = np.clip(1 - ds / 0.0005, 0, 1) * gap
    gm = np.zeros_like(X)
    for x0, z0, x1, z1, dep, wd in GASH:
        vx, vz = x1 - x0, z1 - z0; L2 = vx * vx + vz * vz
        s = ((X - x0) * vx + (Z - z0) * vz) / L2
        px, pz = x0 + np.clip(s, 0, 1) * vx, z0 + np.clip(s, 0, 1) * vz
        dist = np.hypot(X - px, Z - pz) * (1 + 0.4 * (fbm(X * 260, Z * 260, 96, 3) - 0.5))
        tap = np.sin(PI * np.clip(s, 0, 1)) ** 0.5
        g = np.clip(1 - dist / (wd / 2), 0, 1) * tap
        # the wood splits along the grain at the cut: short splinter lifts beside it
        spl = np.exp(-((dist - wd * 0.7) / (wd * 0.35)) ** 2) * tap * sstep(0.55, 0.75, fbm(X * 40, Z * 400, 97, 3))
        disp += dep * g - dep * 0.25 * spl
        gm = np.maximum(gm, sstep(0.05, 0.25, g))
    for cx, cz, rr, dep in DENT:
        q = ((X - cx) ** 2 + (Z - cz) ** 2) / (rr * rr); disp += dep * np.exp(-2 * q)
    rh = np.hypot(X - HOLE[0], Z - HOLE[1]); ah = np.arctan2(Z - HOLE[1], X - HOLE[0])
    sp = (0.5 + 0.5 * np.sin(ah * 7 + 2 * fbm(np.cos(ah) * 3, np.sin(ah) * 3, 98, 3))) ** 1.5
    disp += 0.006 * np.exp(-(rh / 0.006) ** 2) + 0.0015 * np.exp(-(rh / (0.012 + 0.01 * sp)) ** 2)
    gm = np.maximum(gm, sstep(0.011, 0.006, rh))
    # flames lick upward: the scorch is taller than wide, with ragged tongues
    rs = np.hypot((X - SCORCH[0]) * 1.25, (Z - SCORCH[1]) * 0.7 - 0.02 * np.sin(X * 60)) / SCORCH[2]
    char = sstep(1.0, 0.5, rs + 0.55 * (fbm(X * 22, Z * 9, 99, 5) - 0.5) + 0.2 * (fbm(X * 70, Z * 70, 102, 3) - 0.5))
    disp += char * 0.0003 * (fbm(X * 300, Z * 300, 100, 3) - 0.5)
    # fine scratches: short straight scores in every direction
    scr = np.zeros_like(X); rng = np.random.default_rng(41)
    for _ in range(260):
        cx, cz = rng.uniform(-0.38, 0.38, 2)
        if math.hypot(cx, cz) > 0.39: continue
        a = rng.uniform(0, PI); L = rng.uniform(0.015, 0.07); vx, vz = math.cos(a) * L, math.sin(a) * L
        if xs[-1] < cx - L or xs[0] > cx + L or zs[-1] < cz - L or zs[0] > cz + L: continue
        s = np.clip(((X - cx) * vx + (Z - cz) * vz) / (L * L), -0.5, 0.5)
        dd = np.hypot(X - cx - s * vx, Z - cz - s * vz)
        scr = np.maximum(scr, np.clip(1 - dd / 0.00035, 0, 1) * rng.uniform(0.4, 1.0))
    disp += 0.0002 * scr
    out['disp'] = disp
    out['gash'], out['char'] = gm, char
    out['grime'] = np.clip((0.7 * sstep(0.30, 0.395, r) + 0.35 * sstep(0.0, -0.35, Z) + 0.4 * sstep(0.12, 0.08, r)) * (0.4 + 0.8 * fbm(X * 10, Z * 10, 101, 4)), 0, 1)
    out['plank'] = (pid + 0.5) / 7.0; out['crack'] = crack; out['scratch'] = scr
    out['r'], out['ang'] = r, ang
    return out

def back_disp(X, Z):
    pid = plank_id(X)
    d = (np.array([_hash(k, 1, 91) for k in range(7)])[pid] - 0.5) * 0.0007
    d += 0.0003 * (fbm(X * 380, Z * 9, 111, 4) - 0.5) * 2
    d += 0.00025 * np.sin(2 * PI * (Z / 0.045 + np.array([_hash(k, 3, 112) for k in range(7)])[pid]) + 3 * fbm(X * 18, Z * 6, 113, 3))
    ds = np.min([np.abs(X - s) for s in SEAMS], axis=0)
    d -= 0.0009 * np.exp(-(ds / 0.0009) ** 2)
    rh = np.hypot(X - HOLE[0], Z - HOLE[1]); ah = np.arctan2(Z - HOLE[1], X - HOLE[0])
    sp = (0.5 + 0.5 * np.sin(ah * 6 + 2 * fbm(np.cos(ah) * 2, np.sin(ah) * 2, 114, 3))) ** 2
    d += 0.004 * np.exp(-(rh / (0.009 + 0.012 * sp)) ** 2) * sp                            # exit splinters
    return d, pid

def orient_radial(V, Q, outward):
    """flip Q so a sample face's normal points away from (outward) or toward the shield axis."""
    f = Q[len(Q) // 3]; c = V[f].mean(0); n = np.cross(V[f[1]] - V[f[0]], V[f[2]] - V[f[0]])
    rad = np.array([c[0], 0.0, c[2] - ZC])
    return Q if (np.dot(n, rad) > 0) == outward else Q[:, ::-1]
def revolve(prof, nseg, x0=0.0, z0=ZC, jitter=None):
    """profile (rho, y) revolved around the shield axis; seam column duplicated so the UV island has a real seam."""
    a = np.linspace(0, 2 * PI, nseg + 1)
    rho, y = prof[:, 0][None, :], prof[:, 1][None, :]
    if jitter is not None: rho, y = jitter(a[:, None], rho, y)
    V = np.stack(np.broadcast_arrays(x0 + rho * np.cos(a)[:, None], y, z0 + rho * np.sin(a)[:, None]), -1).reshape(-1, 3)
    Q = grid_quads(nseg + 1, len(prof), False)
    pl = np.r_[0, np.cumsum(np.hypot(np.diff(prof[:, 0]), np.diff(prof[:, 1])))]
    uv = np.stack(np.broadcast_arrays(pl[None, :], a[:, None] * max(prof[:, 0].max(), 0.01)), -1).reshape(-1, 2)
    return V, Q, uv

# =====================================================================================================
# 1. board
T0 = thick(0.0)
if HIGH:
    STEP = 0.001
    xs = np.arange(-0.405, 0.4051, STEP); zs = np.arange(-0.405, 0.4051, STEP)
    nx, nz = len(xs), len(zs)
    dl = [masks(xs, zs[c:c + 128]) for c in range(0, nz, 128)]
    disp = np.vstack([m['disp'] for m in dl]); rr = np.vstack([m['r'] for m in dl]); aa = np.vstack([m['ang'] for m in dl])
    X, Z = np.meshgrid(xs, zs)
    keep = (rr < R + 0.0015 - nick_depth(aa) * 0.6) & (rr > RH - 0.0015)
    Q = grid_quads(nz, nx); Q = Q[keep.ravel()[Q].all(1)]
    Vf = np.stack([X, yfr(rr) + disp, ZC + Z], -1).reshape(-1, 3)
    mesh('FaceFront', Vf, [orient(Vf, Q, np.array([0, -1.0, 0]))], 'WoodFront')
    bd, pid = back_disp(X, Z)
    Vb = np.stack([X, ybr(rr) + bd, ZC + Z], -1).reshape(-1, 3)
    mesh('FaceBack', Vb, [orient(Vb, Q, np.array([0, 1.0, 0]))], 'Wood', attrs={'plank': (pid.ravel() + 0.5) / 7.0})
    MX0, MX1, MNX = -0.41, 0.41, 2048
    mxs = np.linspace(MX0, MX1, MNX)
    IM = {k: np.zeros((MNX, MNX), np.float32) for k in ('gash', 'char', 'grime', 'plank', 'crack', 'scratch')}
    for c in range(0, MNX, 96):
        mm = masks(mxs, mxs[c:c + 96])
        for k in IM: IM[k][c:c + 96] = mm[k]
    for name, ch in (('damage', ('gash', 'char', 'grime')), ('wood', ('plank', 'crack', 'scratch'))):
        im = bpy.data.images.new('MR_' + name, MNX, MNX, alpha=False)
        im.pixels.foreach_set(np.stack([IM[ch[0]], IM[ch[1]], IM[ch[2]], np.ones_like(IM[ch[0]])], -1).ravel())
        im.filepath_raw = os.path.join(D, 'masks_round', name + '.png'); im.file_format = 'PNG'; im.save()
    json.dump({'x0': MX0, 'x1': MX1, 'z0': ZC + MX0, 'z1': ZC + MX1}, open(os.path.join(D, 'masks_round', 'masks.json'), 'w'))
else:
    rings = np.array([RH, 0.09, 0.14, 0.20, 0.26, 0.32, 0.37, R])
    a = np.linspace(0, 2 * PI, 72, endpoint=False)
    P = np.stack([rings[:, None] * np.cos(a)[None], rings[:, None] * np.sin(a)[None]], -1).reshape(-1, 2)
    rr = np.hypot(P[:, 0], P[:, 1])
    Q = grid_quads(len(rings), len(a), True)
    for nm, fn, want, mn in (('FaceFront', yfr, -1.0, 'WoodFront'), ('FaceBack', ybr, 1.0, 'Wood')):
        V = np.stack([P[:, 0], fn(rr), ZC + P[:, 1]], -1)
        mesh(nm, V, [orient(V, Q, np.array([0, want, 0]))], mn, uv=np.stack([P[:, 0] * (1 if want < 0 else -1), P[:, 1]], -1))
# the wall of the hand hole (seen from the back, inside the boss)
V, Q, uv = revolve(np.array([[RH, yfr(RH)], [RH, ybr(RH)]]), 160 if HIGH else 24)
mesh('HoleWall', V, [orient_radial(V, Q, False)], 'Wood', uv=uv)

# 2. rawhide rim, laced over the edge, 4 UV islands
def rim_prof(hi):
    t = thick(R); Ro = t / 2 + 0.0018
    k = 20 if hi else 4
    arc = [(-0.0004 + Ro * math.sin(q), -Ro * math.cos(q)) for q in np.linspace(0, PI, k + 1)]
    ff = [(x, -t / 2 - 0.0018) for x in np.linspace(-0.0125, -0.0008, 8 if hi else 1, endpoint=False)]
    fb = [(x, t / 2 + 0.0018) for x in np.linspace(-0.0008, -0.0125, 8 if hi else 2)[1:]]
    return np.array([(-0.0135, -t / 2 + 0.0002), (-0.0132, -t / 2 - 0.0012)] + ff + arc + fb + [(-0.0132, t / 2 + 0.0012), (-0.0135, t / 2 - 0.0002)])
NR = 3200 if HIGH else 96
ang = np.linspace(0, 2 * PI, NR, endpoint=False)
prof = rim_prof(HIGH); M_ = len(prof); side = np.where(prof[:, 1] < 0, 1.0, -1.0)
parts = []
for q in range(4):
    ii = np.arange(q * NR // 4, (q + 1) * NR // 4 + 1)
    aq = ii * 2 * PI / NR
    a2 = np.tile(prof[None, :, 0], (len(ii), 1)); b2 = np.tile(prof[None, :, 1], (len(ii), 1))
    if HIGH:
        nd = nick_depth(aq)[:, None]
        a2 = np.minimum(a2, 0.0055 - nd * 1.2)
        s = aq * R
        lace = np.abs(((s + 0.014) % 0.028) - 0.014)                        # laced every 28 mm
        hole = (np.abs(a2 + 0.0085) < 0.0012) & (lace[:, None] < 0.0012)
        thread = (lace[:, None] < 0.0007) & (a2 > -0.0092)
        b2 = b2 + side[None, :] * (-0.0004 * hole + 0.0007 * thread)
        a2 = a2 + 0.0006 * thread * (a2 > -0.001)
        b2 = b2 + side[None, :] * 0.00025 * (fbm(s[:, None] * 120, a2 * 600, 121, 3) - 0.5) * 2   # the hide shrank unevenly
    rad = R + a2
    V = np.stack([rad * np.cos(aq)[:, None], b2, ZC + rad * np.sin(aq)[:, None]], -1).reshape(-1, 3)
    Qr = grid_quads(len(ii), M_, False)
    pl = np.r_[0, np.cumsum(np.linalg.norm(np.diff(prof, axis=0), axis=1))]
    uv = np.stack(np.broadcast_arrays(pl[None, :], (aq - aq[0])[:, None] * R), -1).reshape(-1, 2)
    mid = len(ii) // 2; f = Qr[mid * (M_ - 1) + M_ // 2]
    if np.dot(np.cross(V[f[1]] - V[f[0]], V[f[2]] - V[f[0]]), [math.cos(aq[mid]), 0, math.sin(aq[mid])]) < 0: Qr = Qr[:, ::-1]
    add(parts, V, Qr, np.zeros((0, 3), int), uv)
emit('Rim', parts, 'Leather')

# 3. iron boss: flange, neck, dome; with its inside (seen through the hand hole)
yb0 = yfr(RH)
def boss_prof(hi):
    n = 28 if hi else 6
    out = [(0.090, yb0 + 0.0004), (0.089, yb0 - 0.0016), (0.086, yb0 - 0.0022), (0.072, yb0 - 0.0030), (0.068, yb0 - 0.0060)]
    out += [(0.066 - 0.002 * t, yb0 - 0.006 - 0.024 * t) for t in np.linspace(0.1, 1, 3 if hi else 1)]
    out += [(0.066 * math.cos(q), yb0 - 0.030 - 0.038 * math.sin(q)) for q in np.linspace(0, PI / 2, n + 1)[1:]]
    inner = [(p[0] * (1 - 0.03) - 0.0, p[1] + 0.0022) for p in out[4:][::-1]]
    return np.array(out + inner[1:] + [(0.064, yb0 + 0.0002)])
def boss_jit(a, rho, y):
    if not HIGH: return rho, y
    h = 0.00035 * (fbm(np.cos(a) * 30 + rho * 400, np.sin(a) * 30 + y * 400, 131, 4) - 0.5) * 2   # hammer facets
    dent = 0.0025 * np.exp(-(((a - 2.2 + PI) % (2 * PI) - PI) / 0.25) ** 2) * sstep(-0.03, -0.06, y - yb0)  # one big blow on the dome
    return rho + h - dent * 0.6, y + dent
V, Q, uv = revolve(boss_prof(HIGH), 256 if HIGH else 32, jitter=boss_jit)
# orient on the outer flange/neck faces (the first third of the profile is the outside)
f = Q[3]; n_ = np.cross(V[f[1]] - V[f[0]], V[f[2]] - V[f[0]]); c_ = V[f].mean(0)
if np.dot(n_, [c_[0], -0.3 * 0, c_[2] - ZC]) + np.dot(n_, [0, -1.0, 0]) * 0.0 < 0: Q = Q[:, ::-1]
mesh('Boss', V, [Q], 'Iron', uv=uv)

# 4. back: wooden grip bar across the hole, leather-wrapped in the middle; iron nails; guige strap
nx_ = 220 if HIGH else 12
xx = np.linspace(-0.235, 0.235, nx_)
lift = lambda x: ybr(np.abs(x)) + 0.0002
path = np.stack([xx, np.zeros_like(xx), np.full_like(xx, ZC)], -1)
nseg = 36 if HIGH else 10
V, Qg, Tg, uvg = sweep(path, np.tile([0, 1.0, 0], (nx_, 1)), circ(1.0, nseg))
w_ = np.interp(np.abs(xx), [0, 0.07, 0.11, 0.235], [0.017, 0.016, 0.014, 0.010])      # half-width (z)
h_ = np.interp(np.abs(xx), [0, 0.07, 0.11, 0.235], [0.013, 0.012, 0.009, 0.005])      # half-height (y)
wrap = np.abs(xx) < 0.062
G = V[:nx_ * (nseg + 1)].reshape(nx_, nseg + 1, 3); off = G - path[:, None, :]
side_ = off[..., 2]; upc = off[..., 1]
ang_ = np.linspace(0, 2 * PI, nseg + 1)
extra = np.zeros((nx_, nseg + 1))
if HIGH:
    ph = np.mod(xx[:, None] / 0.012 + ang_[None, :] / (2 * PI), 1.0)
    extra = wrap[:, None] * (0.0008 * np.abs(np.sin(PI * ph)) ** 0.4 - 0.0005 * (ph < 0.06))
ww = (w_ + 0.0012 * wrap)[:, None] + extra; hh = (h_ + 0.0012 * wrap)[:, None] + extra
cy = lift(xx) + h_                                                                       # sits on the back face
G2 = np.stack([path[:, None, 0] + 0 * side_, cy[:, None] + upc * hh, ZC + side_ * ww], -1)
V[:nx_ * (nseg + 1)] = G2.reshape(-1, 3)
V[nx_ * (nseg + 1):nx_ * (nseg + 1) + 2 * nseg] = np.vstack([G2[0, :nseg], G2[-1, :nseg]])
V[-2:] = [[xx[0], cy[0], ZC], [xx[-1], cy[-1], ZC]]
uvg[:nx_ * (nseg + 1), 0] *= 0.013; uvg[nx_ * (nseg + 1):] *= 0.013
if HIGH:
    fq = np.repeat(wrap[:-1] & wrap[1:], nseg)
    emit('GripWrap', [(V, Qg[fq], np.zeros((0, 3), int), uvg)], 'Leather')
    emit('GripWood', [(V, Qg[~fq], Tg, uvg)], 'Wood')
else:
    emit('GripWood', [(V, Qg, Tg, uvg)], 'Wood')
GRIP = np.array([0.0, float(lift(np.array(0.0)) + h_[nx_ // 2]), ZC])
NAILS = [-0.19, -0.10, 0.10, 0.19]
parts = []
# guige strap across the upper back, riveted at both ends with roves
nxs = int(0.48 / (0.0012 if HIGH else 0.02)) + 1; xs_ = np.linspace(-0.24, 0.24, nxs)
zs_ = ZC + 0.17 - 0.03 * np.sin(PI * (xs_ + 0.24) / 0.48)
rr_ = np.hypot(xs_, zs_ - ZC)
sp_ = np.stack([xs_, ybr(rr_) + 0.0022, zs_], -1)
Vs, Qs, Ts, uvs = sweep(sp_, np.tile([0, 1.0, 0], (nxs, 1)), rrect(0.03, 0.0036, 40 if HIGH else 8, 8.0))
if HIGH:
    pe = np.vstack([rrect(0.03, 0.0036, 40, 8.0)] * 1); pe = np.vstack([pe, pe[:1]]); M1 = len(pe)
    sl = uvs[:nxs * M1, 1].reshape(nxs, M1); line = np.abs(np.abs(pe[None, :, 0]) - 0.011)
    on = (line < 0.0007) & (np.mod(sl, 0.0045) < 0.0028)
    Vs[:nxs * M1, 1] += (-(0.00045 * on + 0.00015 * (line < 0.0011)) * np.sign(pe[None, :, 1])).ravel()
add(parts, Vs, Qs, Ts, uvs)
emit('Strap', parts, 'Leather')
parts = []
for ex in (-0.232, 0.232):
    for dz in (-0.008, 0.008):
        z = ZC + 0.17 + dz; r_ = math.hypot(ex, z - ZC)
        add(parts, *sqrove(np.array([ex, float(ybr(np.array(r_))) + 0.0036 + 0.0016, z]), np.array([0, 1.0, 0]), 0.010, 0.0016))
if HIGH:
    # boss rivets on the flange, nail heads on the front over the grip, clenched nail tips on the grip
    for k in range(5):
        q = 2 * PI * k / 5 + 0.3; px, pz = 0.081 * math.cos(q), ZC + 0.081 * math.sin(q)
        add(parts, *dome(np.array([px, yb0 - 0.0022, pz]), np.array([0, -1.0, 0]), 0.0050, 0.0022))
    for nx0 in NAILS:
        r_ = abs(nx0); add(parts, *dome(np.array([nx0, float(yfr(np.array(r_))) - 0.0001, ZC]), np.array([0, -1.0, 0]), 0.0042, 0.0018))
        i = int(np.argmin(np.abs(xx - nx0))); top = cy[i] + h_[i]
        arc = np.array([[nx0, top + 0.0012, ZC - 0.004 + 0.008 * t] for t in np.linspace(0, 1, 12)])
        arc[:, 1] += 0.0012 * np.sin(np.linspace(0, PI, 12))
        add(parts, *sweep(arc, np.tile([0, 1.0, 0], (12, 1)), circ(0.0011, 8)))
emit('Iron', parts, 'Iron')

if not HIGH:
    import shieldkit; shieldkit.smart_uv(('Iron',))
json.dump({'grip': GRIP.tolist(), 'grip_axis': [1, 0, 0], 'radius': R}, open(os.path.join(D, 'round_meta.json'), 'w'))
tris = sum(len(p.vertices) - 2 for o in bpy.data.objects if o.type == 'MESH' for p in o.data.polygons)
print('TRIS', tris, 'VERTS', sum(len(o.data.vertices) for o in bpy.data.objects if o.type == 'MESH'))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'Round_%s.blend' % ('high' if HIGH else 'low')))
print('BUILD OK')
