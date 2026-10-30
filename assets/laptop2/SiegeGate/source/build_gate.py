# Siege kit gate (laptop2, 2026-10-29): a medieval wooden double gate worn down by water, with a drop-bar and a lever.
# Sits in the owner's #29 border gap on the east side and leads out to the tentacle realm. Fits the siege barricade kit:
# bark log posts and lintel with hemp lashings, plank leaves with ledges and a Z-brace, rusted iron strap hinges.
#   blender -b --factory-startup -P build_gate.py      (env RES = low | high)
# Pieces (vertex groups, exported as separate meshes so the leaves can swing):
#   Frame (posts, lintel, lashings, pintles, bar brackets)   LeafL / LeafR (pivot = hinge)   Bar   Lever (pivot = arm pin)
# Units: metres, Z up. The OUTSIDE face (toward the realm) looks toward -Y. The opening is centred on x 0.
import os, sys, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np
bpy.ops.wm.read_factory_settings(use_empty=True)
import kitlog
from kitlog import log, lash, rope
from shieldkit import fbm, sstep, mesh, grid_quads, unit, sweep, rrect, circ, superellipsoid, dome, HIGH, PI
D = os.path.dirname(os.path.abspath(__file__))
rng0 = np.random.default_rng(29)

GW = 5.8                 # opening between the posts
LW = GW / 2 - 0.02       # each leaf
LH = 3.25                # leaf height
Z0 = 0.06                # leaves clear the ground (the bottoms have rotted unevenly)
PR = 0.23                # post radius
PX = GW / 2 + PR         # post centres
PH = 4.75                # posts top

def group(ob, name):
    vg = ob.vertex_groups.new(name=name); vg.add(list(range(len(ob.data.vertices))), 1.0, 'REPLACE'); return ob

# ---------------- planks: a rounded-rectangle tube with grain, splits and water rot ----------------
def board_prof(w, t, hi):
    """flat board section: a rectangle with small chamfered corners; dense across the faces on the high poly."""
    c = min(0.006, t * 0.2); nf = 40 if hi else 1; ns = 6 if hi else 1
    hw, ht = w / 2, t / 2
    pts = []
    for x in np.linspace(hw - c, -hw + c, nf + 1): pts.append((x, ht))            # top face (right to left)
    pts.append((-hw, ht - c))
    for y in np.linspace(ht - c, -ht + c, ns + 1)[1:-1]: pts.append((-hw, y))
    pts.append((-hw, -ht + c))
    for x in np.linspace(-hw + c, hw - c, nf + 1): pts.append((x, -ht))           # bottom face
    pts.append((hw, -ht + c))
    for y in np.linspace(-ht + c, ht - c, ns + 1)[1:-1]: pts.append((hw, y))
    pts.append((hw, ht - c))
    return np.array(pts)

def plank(name, p0, p1, w, t, seed, up, mname='Plank', rot=0.0, gname=None):
    """board from p0 to p1 (the grain runs along it), w wide, t thick, 'up' = its face normal.
    rot: how rotten its lower end is (0..1): eroded edges, a ragged, splintered bottom."""
    rng = np.random.default_rng(seed)
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float); L = np.linalg.norm(p1 - p0)
    nl = max(int(L / (0.006 if HIGH else 0.5)), 2) + 1
    path = p0[None] + np.linspace(0, 1, nl)[:, None] * (p1 - p0)[None]
    prof = board_prof(w, t, HIGH)
    V, Q, Tr, uv = sweep(path, np.tile(np.asarray(up, float), (nl, 1)), prof)
    M1 = len(prof) + 1
    G = V[:nl * M1].reshape(nl, M1, 3); ctr = path[:, None, :]
    pe = np.vstack([prof, prof[:1]])
    s = np.linspace(0, 1, nl)[:, None] * L                                              # along the board
    cu = pe[None, :, 0] / (w / 2)                                                       # across (-1..1)
    face = np.abs(pe[None, :, 1]) > t * 0.35                                            # on the broad faces
    zw = path[:, None, 2]                                                               # world height (water level)
    wet = sstep(0.9, 0.05, zw)
    if HIGH:
        # grain ridges the mesh can resolve (40 segments across): broad undulation + ~14 annual-ring ridges; finer grain is the material's
        grain = 0.0004 * (fbm(cu * 5 + seed, s * 0.7, seed, 3) - 0.5) * 2 + 0.0002 * (fbm(cu * 14, s * 2.5, seed + 1, 3) - 0.5)
        # splits along the grain: a few long cracks per board, wider near the ends
        cr = np.zeros_like(cu)
        for _ in range(rng.integers(2, 6)):
            c0 = rng.uniform(-0.7, 0.7); a, b = sorted(rng.uniform(0, L, 2))
            on = sstep(a - 0.05, a + 0.05, s) * sstep(b + 0.05, b - 0.05, s)
            cr = np.maximum(cr, np.exp(-((cu - c0 - 0.03 * np.sin(s * 3 + seed)) / 0.018) ** 2) * on)
        erode = (0.002 + 0.007 * rot * wet) * sstep(0.55, 1.0, np.abs(cu))             # rounded, eaten edges low down
        erode += 0.0035 * rot * wet * fbm(cu * 12, s * 6, seed + 2, 4)                  # soft rot pockets
        disp = grain * face - 0.0035 * cr * face - erode * (1 + face)
        G = ctr + (G - ctr) * (1 + 0 * disp[..., None]) + unit(G - ctr) * disp[..., None]
        # the rotten lower end: a ragged line, splinters
        if rot > 0 and p0[2] < p1[2]:
            jag = 0.01 + (0.04 + 0.12 * rot) * fbm(cu * 2.5 + seed, np.zeros_like(cu), seed + 3, 3)       # soft, uneven rot line
            for _ in range(rng.integers(2, 5)):                                                             # a few fibrous splinters
                c0, hw_, hh = rng.uniform(-0.85, 0.85), rng.uniform(0.04, 0.12), rng.uniform(0.02, 0.08) * rot
                jag = jag + hh * np.exp(-((cu - c0) / hw_) ** 2)
            G[..., 2] = np.maximum(G[..., 2], p0[2] + jag * np.clip(1 - s / 0.25, 0, 1) + 0 * G[..., 2]) if False else G[..., 2]
            lift = np.clip(jag - s, 0, None)
            G = G + (p1 - p0) / L * lift[..., None]
    V[:nl * M1] = G.reshape(-1, 3)
    K = M1 - 1; V[nl * M1:nl * M1 + K] = G[0, :K]; V[nl * M1 + K:nl * M1 + 2 * K] = G[-1, :K]
    ob = mesh(name, V, [Q, Tr], mname, uv=uv)
    if gname: group(ob, gname)
    return ob

def strap(name, p0, p1, w, t, gname, tip=True):
    """flat iron strap along the face (a hinge leaf), with a rounded spear end."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float); L = np.linalg.norm(p1 - p0)
    n = max(int(L / (0.004 if HIGH else 0.25)), 2) + 1
    path = p0[None] + np.linspace(0, 1, n)[:, None] * (p1 - p0)[None]
    prof = rrect(w, t, 32 if HIGH else 6, 6.0)
    V, Q, Tr, uv = sweep(path, np.tile([0, -1.0, 0], (n, 1)), prof)
    M1 = len(prof) + 1; G = V[:n * M1].reshape(n, M1, 3); ctr = path[:, None, :]
    ss = np.linspace(0, 1, n)
    wid = np.where(ss > 0.86, 0.35 + 0.65 * np.sqrt(np.clip((1 - ss) / 0.14, 0, 1)), 1.0) if tip else np.ones(n)
    wid = wid + 0.25 * np.exp(-((ss - 0.93) / 0.03) ** 2) * tip                        # a small bulb before the point
    tang = unit(p1 - p0); off = G - ctr; along = (off * tang).sum(-1, keepdims=True) * tang
    side = off - along; up = np.array([0, -1.0, 0]); vert = (side * up).sum(-1, keepdims=True) * up; lat = side - vert
    G = ctr + lat * wid[:, None, None] + vert
    if HIGH: G = G + up * (0.0004 * (fbm(G[..., 0] * 90, G[..., 2] * 90, 41, 3) - 0.5))[..., None]   # forge hammering
    V[:n * M1] = G.reshape(-1, 3); K = M1 - 1; V[n * M1:n * M1 + K] = G[0, :K]; V[n * M1 + K:n * M1 + 2 * K] = G[-1, :K]
    return group(mesh(name, V, [Q, Tr], 'Iron', uv=uv), gname)

def nails(name, pts, normal, gname, r=0.011):
    if not HIGH: return None
    Vs, Qs, Ts, us, off = [], [], [], [], 0
    for p in pts:
        V, Q, Tr, uv = dome(np.asarray(p, float), np.asarray(normal, float), r, r * 0.55, 14, 5)
        Vs.append(V); Qs.append(Q + off); Ts.append(Tr + off); us.append(uv); off += len(V)
    return group(mesh(name, np.vstack(Vs), [np.vstack(Qs), np.vstack(Ts)], 'Iron', uv=np.vstack(us)), gname)

# ---------------- frame ----------------
frame = []
for k, sx in enumerate((-1, 1)):
    o = log('Post_%d' % k, (sx * PX, 0.0, -0.40), (sx * PX + sx * 0.03, 0.02, PH), PR, 700 + k, bend=0.015)
    frame.append(group(o, 'Frame'))
o = log('Lintel', (-PX - 0.45, 0.05, PH - 0.38), (PX + 0.45, 0.03, PH - 0.42), 0.19, 710, bend=0.02); frame.append(group(o, 'Frame'))
for k, sx in enumerate((-1, 1)):
    o = lash('Lash_%d' % k, (sx * PX, 0.0, PH - 0.40), PR, (sx * PX, 0.05 + PR + 0.19 - 0.02, PH - 0.40), 0.19, (0, 0, 1), (1, 0, 0), 720 + k)
    frame.append(group(o, 'Frame'))
# pintles (hinge pins) on the posts and the bar brackets (inside, +Y)
HZ = (Z0 + 0.45, Z0 + LH - 0.45)
for sx in (-1, 1):
    for hz in HZ:
        n = 24 if HIGH else 6
        V, Q, Tr, uv = sweep(np.array([[sx * (PX - PR * 0.6), -0.02, hz - 0.09], [sx * (PX - PR * 0.6), -0.02, hz + 0.09]]), np.tile([0, -1.0, 0], (2, 1)), circ(0.022, n))
        frame.append(group(mesh('Pintle', V, [Q, Tr], 'Iron', uv=uv), 'Frame'))
    zb = Z0 + LH * 0.52
    pts = np.array([[sx * (PX - PR * 0.4), 0.12, zb - 0.09], [sx * (PX - PR * 0.55), 0.30, zb - 0.09], [sx * (PX - PR * 0.55), 0.30, zb + 0.11],
                    [sx * (PX - PR * 0.4), 0.12, zb + 0.11]])
    V, Q, Tr, uv = sweep(pts, np.tile([1.0, 0, 0], (4, 1)), rrect(0.07, 0.014, 16 if HIGH else 5, 5.0))
    frame.append(group(mesh('Bracket', V, [Q, Tr], 'Iron', uv=uv), 'Frame'))

# ---------------- the two leaves ----------------
def leaf(side):
    g = 'LeafL' if side < 0 else 'LeafR'
    x_h = side * (GW / 2 - 0.02)                      # hinge edge
    x_m = side * 0.01                                 # meeting edge
    nb = 6; bw = LW / nb
    rng = np.random.default_rng(800 + (side > 0))
    objs = []
    for k in range(nb):
        xc = x_h - side * (bw * (k + 0.5))
        top = Z0 + LH + rng.uniform(-0.05, 0.05) - (0.10 if k == nb - 1 else 0)
        rot = rng.uniform(0.5, 1.0)
        objs.append(plank('Board', (xc, -0.035, Z0 + rng.uniform(0, 0.04)), (xc + rng.uniform(-0.006, 0.006), -0.035, top),
                          bw - 0.006, 0.055, 810 + k + (100 if side > 0 else 0), (0, -1.0, 0), rot=rot, gname=g))
    # ledges (inside) and the Z-brace
    for k, zl in enumerate((Z0 + 0.42, Z0 + LH * 0.52, Z0 + LH - 0.38)):
        objs.append(plank('Ledge', (x_h - side * 0.06, 0.035, zl), (x_m + side * 0.06, 0.035, zl), 0.20, 0.05, 840 + k + (100 if side > 0 else 0),
                          (0, 1.0, 0), rot=0.6 if k == 0 else 0.15, gname=g))
    objs.append(plank('Brace', (x_m + side * 0.12, 0.034, Z0 + 0.55), (x_h - side * 0.18, 0.034, Z0 + LH * 0.52 - 0.12), 0.17, 0.045,
                      850 + (100 if side > 0 else 0), (0, 1.0, 0), rot=0.4, gname=g))
    objs.append(plank('Brace', (x_m + side * 0.12, 0.034, Z0 + LH * 0.52 + 0.12), (x_h - side * 0.18, 0.034, Z0 + LH - 0.5), 0.17, 0.045,
                      851 + (100 if side > 0 else 0), (0, 1.0, 0), rot=0.1, gname=g))
    # strap hinges on the outside, running from the pintle across most of the leaf; nails along them
    nl = []
    for hz in HZ:
        objs.append(strap('Strap', (side * (GW / 2 + 0.06), -0.068, hz), (x_m + side * 0.35, -0.068, hz + 0.01), 0.075, 0.009, g))
        for xx in np.linspace(side * (GW / 2 - 0.12), x_m + side * 0.5, 7): nl.append((xx, -0.073, hz))
    # clench nails through the ledges (outside heads)
    for zl in (Z0 + 0.42, Z0 + LH * 0.52, Z0 + LH - 0.38):
        for k in range(nb): nl.append((x_h - side * (bw * (k + 0.5)) + 0.03, -0.064, zl + 0.04)); nl.append((x_h - side * (bw * (k + 0.5)) - 0.03, -0.064, zl - 0.04))
    nails('Nails', nl, (0, -1.0, 0), g)
    return objs
leaf(-1); leaf(1)

# ---------------- drop bar (inside, resting in the brackets) ----------------
zb = Z0 + LH * 0.52
plank('Bar', (-PX + PR * 0.3, 0.21, zb), (PX - PR * 0.3, 0.21, zb + 0.01), 0.18, 0.13, 870, (0, 1.0, 0), rot=0.0, gname='Bar')

# ---------------- lever: a post beside the gate (inside), an arm on an iron pin, a rope up to the lintel pulley ----------------
LX = -(PX + 0.9)
o = log('LeverPost', (LX, 0.55, -0.35), (LX + 0.02, 0.56, 1.55), 0.13, 880, bend=0.01); group(o, 'Lever')
plank('LeverArm', (LX, 0.40, 1.15), (LX + 0.25, 0.40, 2.25), 0.10, 0.08, 881, (0, -1.0, 0), rot=0.0, gname='Lever')
n = 16 if HIGH else 5
V, Q, Tr, uv = sweep(np.array([[LX, 0.30, 1.18], [LX, 0.68, 1.18]]), np.tile([0, 0, 1.0], (2, 1)), circ(0.025, n))
group(mesh('LeverPin', V, [Q, Tr], 'Iron', uv=uv), 'Lever')
rp = np.array([[LX + 0.25, 0.40, 2.22], [LX + 0.55, 0.32, 3.0], [-PX + 0.1, 0.24, PH - 0.62]])
rp = np.vstack([rp[0] + (rp[1] - rp[0]) * t for t in np.linspace(0, 1, 12)] + [rp[1] + (rp[2] - rp[1]) * t for t in np.linspace(0, 1, 24)[1:]])
group(rope('LeverRope', rp, 0.012, 882), 'Lever')

meta = {'grip': [0, 0, 0], 'pieces': {'Frame': [0, 0, 0], 'LeafL': [-(GW / 2 - 0.02), -0.035, 0], 'LeafR': [GW / 2 - 0.02, -0.035, 0],
        'Bar': [0, 0.21, zb], 'Lever': [LX, 0.40, 1.18]}, 'opening': GW, 'leaf_height': LH, 'outside': '-Y'}
json.dump(meta, open(os.path.join(D, 'gate_meta.json'), 'w'), indent=1)
tris = sum(len(p.vertices) - 2 for o in bpy.data.objects if o.type == 'MESH' for p in o.data.polygons)
print('TRIS', tris, 'VERTS', sum(len(o.data.vertices) for o in bpy.data.objects if o.type == 'MESH'))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'Gate_%s.blend' % ('high' if HIGH else 'low')))
print('BUILD OK')
