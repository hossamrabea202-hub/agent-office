# Potions (laptop2, 2026-10-29): Health Potion (round flask, red) and Antidote (tall hexagonal bottle, green).
#   blender -b --factory-startup -P build_potion.py      (env RES = low | high, VARIANT = Health | Antidote)
# Glass and liquid are separate objects ('Glass', 'Liquid') that keep their own translucent UE materials and are not
# baked; cork, dripping wax seal, twine and the paper tag are baked (2K) from the high poly.
# Units: metres, Z up, the bottle stands on z 0, the tag faces -Y. Pivot = base centre (potion_<variant>_meta.json).
import os, sys, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np
bpy.ops.wm.read_factory_settings(use_empty=True)
from shieldkit import fbm, sstep, mesh, grid_quads, unit, sweep, rrect, circ, add, emit, superellipsoid, HIGH, PI
D = os.path.dirname(os.path.abspath(__file__))
VAR = os.environ.get('VARIANT', 'Health')
os.makedirs(os.path.join(D, 'masks_potion'), exist_ok=True)

# ---------------- bottle profile (rho, z) of the OUTER glass ----------------
if VAR == 'Health':     # round-bottomed alchemist's flask on a flat foot ring
    def outer(n):
        pts = [(0.0, 0.0015), (0.022, 0.0012), (0.026, 0.0030)]
        for q in np.linspace(-1.05, 1.05, n): pts.append((0.042 * math.cos(q), 0.043 + 0.042 * math.sin(q)))
        pts += [(0.0118, 0.087), (0.0112, 0.104), (0.0122, 0.1075), (0.0138, 0.1095), (0.0140, 0.1125), (0.0125, 0.1150), (0.0108, 0.1150)]
        return np.array(pts)
    NECK_Z, TOP_Z, FILL = 0.104, 0.115, 0.064
    def hexf(a, z): return np.ones_like(a)
else:                   # tall hexagonal apothecary bottle with rounded edges and shoulders
    def outer(n):
        pts = [(0.0, 0.0015), (0.024, 0.0012), (0.0285, 0.004), (0.0300, 0.012)]
        pts += [(0.0300, z) for z in np.linspace(0.02, 0.088, max(n // 3, 3))]
        for q in np.linspace(0, PI / 2, n // 2)[1:]: pts.append((0.0105 + 0.0195 * math.cos(q), 0.088 + 0.014 * math.sin(q)))
        pts += [(0.0102, 0.112), (0.0098, 0.124), (0.0110, 0.1275), (0.0124, 0.1295), (0.0126, 0.1325), (0.0112, 0.1345), (0.0095, 0.1345)]
        return np.array(pts)
    NECK_Z, TOP_Z, FILL = 0.124, 0.1345, 0.074
    def hexf(a, z):   # hexagonal cross-section on the body, fading to round at the shoulder
        k = np.cos(PI / 6) / np.cos((a % (PI / 3)) - PI / 6)          # a flat face looks toward -Y
        k = 1 + (k - 1) * 0.92                                                 # soften the edges a little
        return 1 + (k - 1) * sstep(0.096, 0.088, z) * sstep(0.004, 0.012, z)

def revolve(prof, nseg, rfac=None, jit=None):
    a = np.linspace(0, 2 * PI, nseg + 1)
    rho, z = prof[:, 0][None, :], prof[:, 1][None, :]
    A = a[:, None] + 0 * rho
    f = hexf(A, z + 0 * A) if rfac is None else rfac
    R = rho * f
    if jit is not None: R = R + jit(A, z + 0 * A)
    V = np.stack([R * np.cos(A), R * np.sin(A), z + 0 * A], -1).reshape(-1, 3)
    Q = grid_quads(nseg + 1, len(prof), False)
    pl = np.r_[0, np.cumsum(np.hypot(np.diff(prof[:, 0]), np.diff(prof[:, 1])))]
    uv = np.stack(np.broadcast_arrays(pl[None, :], a[:, None] * 0.03), -1).reshape(-1, 2)
    return V, Q, uv
def outward(V, Q):
    f = Q[len(Q) // 2]; c = V[f].mean(0); n = np.cross(V[f[1]] - V[f[0]], V[f[2]] - V[f[0]])
    return Q if np.dot(n, [c[0], c[1], 0]) > 0 else Q[:, ::-1]

NS = 96 if HIGH else 24
po = outer(24 if HIGH else 10)
Vg, Qg, uvg = revolve(po, NS)
mesh('Glass', Vg, [outward(Vg, Qg)], 'Glass', uv=uvg)
# liquid: the inside of the glass (2 mm in), filled to FILL, with a flat surface and a slight meniscus
inner = np.array([(max(r - 0.002, 0.0), z + (0.002 if i < 2 else 0)) for i, (r, z) in enumerate(po)])
inner = inner[inner[:, 1] <= FILL]
r_at = math.sqrt(0.042 ** 2 - (FILL - 0.043) ** 2) - 0.002 if VAR == 'Health' else 0.0245
inner = np.vstack([inner, [(r_at, FILL)], [(r_at * 0.6, FILL - 0.0006)], [(0.0, FILL - 0.0008)]])
Vl, Ql, uvl = revolve(inner, NS)
mesh('Liquid', Vl, [outward(Vl, Ql)], 'Liquid', uv=uvl)

# ---------------- cork ----------------
CR = (0.0098 if VAR == 'Health' else 0.0086)
cz0, cz1 = NECK_Z - 0.010, TOP_Z + 0.006
nz = 60 if HIGH else 6
zz = np.linspace(cz0, cz1, nz)
def cork_r(z):
    t = (z - cz0) / (cz1 - cz0)
    return CR * (0.95 + 0.08 * t) * np.where(t > 0.9, 1 - 0.6 * ((t - 0.9) / 0.1) ** 2, 1.0)     # a plain tapered plug, eased top edge
prof = np.stack([cork_r(zz), zz], -1)
prof = np.vstack([prof, [(0.0, cz1 + 0.0004)]])
jit = (lambda A, Z: 0.00025 * (fbm(np.cos(A) * 30 + Z * 300, np.sin(A) * 30, 161, 3) - 0.5) * 2) if HIGH else None
Vc, Qc, uvc = revolve(prof, 48 if HIGH else 10, rfac=np.ones((1, 1)), jit=jit)
parts_cork = [(Vc, outward(Vc, Qc), np.zeros((0, 3), int), uvc)]

# ---------------- wax seal: a cap over the cork and lip, with drips down the neck ----------------
WCOL = {'Health': 'WaxRed', 'Antidote': 'WaxGreen'}[VAR]
rng = np.random.default_rng(7 if VAR == 'Health' else 11)
drips = [(rng.uniform(0, 2 * PI), rng.uniform(0.005, 0.014), rng.uniform(0.0014, 0.0026)) for _ in range(7)]
wz0 = TOP_Z - 0.0025
nzw = 140 if HIGH else 10; naw = 160 if HIGH else 24
zw = np.linspace(wz0 - 0.012, cz1 + 0.0025, nzw)
aw = np.linspace(0, 2 * PI, naw + 1)
Aw, Zw = np.meshgrid(aw, zw, indexing='ij')
lip_r = po[-3, 0] + 0.0014
def base_r(z):
    r = np.where(z < TOP_Z, np.interp(z, po[:, 1][-8:], po[:, 0][-8:]) + 0.0011, lip_r)
    over = np.clip((z - cz1 + 0.003) / 0.0058, 0, 1)                                       # rounds over the cork top
    return r * np.sqrt(np.clip(1 - over ** 2, 0, 1)) + 0.0
edge = np.full_like(Aw, wz0)                                                                # the lower edge of the wax
for a0, L, w in drips:
    da = np.abs(((Aw - a0) + PI) % (2 * PI) - PI) * lip_r
    edge = np.minimum(edge, wz0 - L * np.clip(1 - (da / w) ** 2, 0, 1) ** 0.5)
edge = edge - 0.0008 * fbm(np.cos(Aw) * 8, np.sin(Aw) * 8, 171, 3)
Rw = base_r(Zw)
thick = 0.0012 * sstep(edge - 0.0002, edge + 0.0025, Zw)                                     # thins to nothing at the edge
for a0, L, w in drips:    # drip beads: thicker blobs at their tips
    da = np.abs(((Aw - a0) + PI) % (2 * PI) - PI) * lip_r
    thick = thick + 0.0011 * np.exp(-(da / (w * 0.8)) ** 2) * np.exp(-((Zw - (wz0 - L + 0.0012)) / 0.0016) ** 2)
if HIGH: thick = thick + 0.0004 * (fbm(np.cos(Aw) * 6 + Zw * 90, np.sin(Aw) * 6, 172, 4) - 0.5) + 0.00012 * (fbm(np.cos(Aw) * 40 + Zw * 300, np.sin(Aw) * 40, 173, 3) - 0.5)
vis = Zw >= edge - 0.0003
Rw2 = np.where(vis, Rw + thick, Rw - 0.0004)
# seal disc pressed into the top: a raised ring and the stamp
Vw = np.stack([Rw2 * np.cos(Aw), Rw2 * np.sin(Aw), Zw], -1)
topz = cz1 + 0.0025
Vw[..., 2] = np.where(Zw > cz1 - 0.001, np.minimum(Zw, topz), Zw)
Vw = Vw.reshape(-1, 3)
Qw = grid_quads(naw + 1, nzw, False)
f = Qw[len(Qw) // 2]; cfa = Vw[f].mean(0)
if np.dot(np.cross(Vw[f[1]] - Vw[f[0]], Vw[f[2]] - Vw[f[0]]), [cfa[0], cfa[1], 0]) < 0: Qw = Qw[:, ::-1]
uvw = np.stack([Aw * lip_r, Zw], -1).reshape(-1, 2)
# a flat wax disc on top (the stamped seal)
nr = 40 if HIGH else 4
rr_ = np.linspace(0, 1, nr)
Ad, Rd = np.meshgrid(aw, rr_, indexing='ij')
Rtop = base_r(np.array(topz - 0.0004)) + 0.0006
stamp = np.zeros_like(Rd)
if HIGH:
    xx, yy = Rd * np.cos(Ad), Rd * np.sin(Ad)
    ring = np.exp(-((Rd - 0.78) / 0.05) ** 2)
    if VAR == 'Health':   # a cross
        glyph = ((np.abs(xx) < 0.14) & (np.abs(yy) < 0.5)) | ((np.abs(yy) < 0.14) & (np.abs(xx) < 0.5))
    else:                 # a leaf: an almond with a midrib
        glyph = ((xx / 0.32) ** 2 + (yy / 0.58) ** 2 < 1) & ~((np.abs(xx) < 0.04) & (np.abs(yy) < 0.5))
    stamp = 0.0005 * ring - 0.00045 * glyph
Vd = np.stack([Rd * Rtop * np.cos(Ad), Rd * Rtop * np.sin(Ad), topz + stamp - 0.0003 * Rd ** 4], -1).reshape(-1, 3)
Qd = grid_quads(naw + 1, nr, False)
if np.cross(Vd[Qd[5][1]] - Vd[Qd[5][0]], Vd[Qd[5][2]] - Vd[Qd[5][0]])[2] < 0: Qd = Qd[:, ::-1]
parts_wax = [(Vw, Qw, np.zeros((0, 3), int), uvw), (Vd, Qd, np.zeros((0, 3), int), np.stack([Rd * np.cos(Ad), Rd * np.sin(Ad)], -1).reshape(-1, 2) * 0.012)]

# ---------------- twine around the neck, a knot, and a paper tag on a loop ----------------
TZ = NECK_Z - 0.010 if VAR == 'Health' else NECK_Z - 0.006
rn = np.interp(TZ, po[:, 1][-8:], po[:, 0][-8:]) + 0.0009
parts_tw = []
turns = 3
nt = 900 if HIGH else 40
t = np.linspace(0, turns, nt)
helix = np.stack([rn * np.cos(2 * PI * t - PI / 2), rn * np.sin(2 * PI * t - PI / 2), TZ + 0.0019 * (t - turns / 2)], -1)
prof = circ(0.0009, 10 if HIGH else 5)
Vt, Qt, Tt, uvt = sweep(helix, np.tile([0, 0, 1.0], (nt, 1)), prof)
if HIGH:   # two-ply twist
    M1 = len(prof) + 1; G = Vt[:nt * M1].reshape(nt, M1, 3); ctr = helix[:, None, :]
    ang = np.linspace(0, 2 * PI, M1)[None, :]; tw = np.cos(2 * (ang - t[:, None] * 2 * PI * 9))
    G = ctr + (G - ctr) * (1 + 0.18 * tw[..., None]); Vt[:nt * M1] = G.reshape(-1, 3)
add(parts_tw, Vt, Qt, Tt, uvt)
# knot at the front
kc = np.array([0, -rn - 0.0012, TZ])
Vs, Qs, Ts = superellipsoid(20 if HIGH else 6, 10 if HIGH else 3, 0.8)
add(parts_tw, kc + Vs * np.array([0.0026, 0.0018, 0.0022]), Qs, Ts, np.stack([Vs[:, 0], Vs[:, 2]], -1) * 0.003)
# the paper tag rests against the outside of the glass: on the flask's shoulder, or flat on the hex bottle's front face
TAGW, TAGH = 0.022, 0.030
if VAR == 'Health':
    e = math.radians(48); RS = 0.042 + 0.0009
    hole = np.array([0.003, -RS * math.cos(e), 0.043 + RS * math.sin(e)])
    Nt = np.array([0, -math.cos(e), math.sin(e)]); Dt = np.array([0, -math.sin(e), -math.cos(e)])
else:
    hole = np.array([0.002, -0.0272, 0.086]); Nt = np.array([0, -1.0, 0]); Dt = np.array([0, 0, -1.0])
Rt = np.cross(Nt, Dt)
for side in (-1, 1):   # two strands from the knot down to the tag hole, bowing outward over the glass
    n = 60 if HIGH else 6; s = np.linspace(0, 1, n)
    p = kc[None, :] * (1 - s[:, None]) + hole[None, :] * s[:, None]
    p[:, 0] += side * 0.0012 * np.sin(PI * s); p[:, 1] -= 0.0045 * np.sin(PI * s)
    V_, Q_, T_, u_ = sweep(p, np.tile([0, -1.0, 0], (n, 1)), circ(0.0006, 8 if HIGH else 4))
    add(parts_tw, V_, Q_, T_, u_)
nu, nv = (120, 160) if HIGH else (4, 5)
U, Vv = np.meshgrid(np.linspace(-1, 1, nu), np.linspace(0, 1, nv))
tilt = math.radians(-7)
pu, pv = U * TAGW / 2, Vv * TAGH - 0.003
pu2, pv2 = pu * math.cos(tilt) - pv * math.sin(tilt), pu * math.sin(tilt) + pv * math.cos(tilt)
curl = 0.0010 * U ** 2 + 0.0006 * Vv ** 2 + 0.0004
Vf = (hole + pu2[..., None] * Rt + pv2[..., None] * Dt + curl[..., None] * Nt).reshape(-1, 3)
th = 0.00035
Vb = Vf - Nt * th
Qf = grid_quads(nv, nu, False)
if np.dot(np.cross(Vf[Qf[3][1]] - Vf[Qf[3][0]], Vf[Qf[3][2]] - Vf[Qf[3][0]]), Nt) < 0: Qf = Qf[:, ::-1]
uvf = np.stack([U * TAGW / 2, -Vv * TAGH], -1).reshape(-1, 2)
TAG = (np.vstack([Vf, Vb]), np.vstack([Qf, Qf[:, ::-1] + len(Vf)]), np.vstack([uvf, uvf * np.array([-1, 1])]),
       np.r_[np.ones(len(Vf)), np.zeros(len(Vb))])
if HIGH:   # tag ink mask (front): a hand-inked symbol and a line of script
    N = 512
    xs = np.linspace(-1, 1, N); ys = np.linspace(0, 1, int(N * TAGH / TAGW))
    X, Y = np.meshgrid(xs, ys)
    xm, ym = X * TAGW / 2, (Y - 0.45) * TAGH
    wob = 0.0003 * (fbm(X * 9, Y * 9, 181, 3) - 0.5)
    if VAR == 'Health':   # a heart
        hx, hy = xm / 0.0072, -ym / 0.0072
        heart = (hx ** 2 + (hy - 0.55 * np.sqrt(np.abs(hx))) ** 2) < 1.0 + wob * 300
        ink = heart.astype(float)
    else:                 # a three-leaf sprig
        ink = np.zeros_like(X)
        for cx_, cy_, a_ in ((0, -0.004, 0), (-0.0042, 0.0005, 0.7), (0.0042, 0.0005, -0.7)):
            ca, sa = math.cos(a_), math.sin(a_)
            lx, ly = (xm - cx_) * ca - (ym - cy_) * sa, (xm - cx_) * sa + (ym - cy_) * ca
            ink = np.maximum(ink, ((lx / 0.0022) ** 2 + (ly / 0.0042) ** 2 < 1 + wob * 300).astype(float))
        ink = np.maximum(ink, ((np.abs(xm) < 0.00035) & (ym > 0.0) & (ym < 0.009)).astype(float))
    # a line of "script" under the symbol: little strokes
    lines = np.zeros_like(X)
    for row in (0.80, 0.88):
        yy = np.abs(Y - row) < 0.012
        st = np.sin(X * 90 + 3 * fbm(X * 6, Y * 6 + row, 182, 2)) > 0.2
        lines = np.maximum(lines, (yy & st & (np.abs(X) < 0.72 - (row - 0.8) * 3)).astype(float))
    ink = np.clip(ink + lines, 0, 1)
    im = bpy.data.images.new('M_tag', N, len(ys), alpha=False)
    im.pixels.foreach_set(np.stack([ink, ink, ink, np.ones_like(ink)], -1).astype(np.float32).ravel())
    im.filepath_raw = os.path.join(D, 'masks_potion', 'tag_%s.png' % VAR); im.file_format = 'PNG'; im.save()
    json.dump({'w': TAGW, 'h': TAGH}, open(os.path.join(D, 'masks_potion', 'tag_%s.json' % VAR), 'w'))

emit('Cork', parts_cork, 'Cork')
emit('Wax', parts_wax, WCOL)
emit('Twine', parts_tw, 'Twine')
mesh('Tag', TAG[0], [TAG[1]], 'Tag', uv=TAG[2], attrs={'front': TAG[3]})
json.dump({'grip': [0.0, 0.0, 0.0], 'variant': VAR, 'height': TOP_Z}, open(os.path.join(D, 'potion%s_meta.json' % VAR.lower()), 'w'))
tris = sum(len(p.vertices) - 2 for o in bpy.data.objects if o.type == 'MESH' for p in o.data.polygons)
print('TRIS', tris, 'VERTS', sum(len(o.data.vertices) for o in bpy.data.objects if o.type == 'MESH'))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'Potion%s_%s.blend' % (VAR, 'high' if HIGH else 'low')))
print('BUILD OK')
