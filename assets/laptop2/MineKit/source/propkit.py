# Prop building blocks shared by the gate and the barracks props: planks with grain, splits and water rot; iron straps;
# nail heads. Extracted from build_gate.py (laptop2 2026-10-30).
import math
import bpy, numpy as np
from shieldkit import fbm, sstep, mesh, grid_quads, unit, sweep, rrect, circ, superellipsoid, dome, HIGH, PI

def group(ob, name):
    if name is None: return ob
    vg = ob.vertex_groups.new(name=name); vg.add(list(range(len(ob.data.vertices))), 1.0, 'REPLACE'); return ob
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
