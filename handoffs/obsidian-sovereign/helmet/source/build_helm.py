# Obsidian Sovereign helm (#485): an armet with pointed visor, brow band, medial comb, cheek plates, neck lames, rondel.
#   CHEST_RES=1|3 blender -b --factory-startup -P build_helm.py   -> $WORK/helm_build_r<RES>.blend
# Frame: metres, Z up, the face looks toward -Y, KNIGHT SPACE (same as every other piece: pivot = knight origin at the
# feet, the mesh sits where the knight's head is). All dimensions come from probes/fit_envelope.json: see ../README.md.
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
D = os.environ.get('WORK') or HERE
import numpy as np
import bpy
from chestlib import mesh_obj, grid_faces, tube, ribbon, rivet, catmull, smoothstep

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
RES = int(os.environ.get('CHEST_RES', '1')); r = RES
HIGH = RES > 1
PI = math.pi; DEG = PI / 180

def mat(name, col, metal, rough):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*col, 1); b.inputs['Metallic'].default_value = metal; b.inputs['Roughness'].default_value = rough
    return m
M_STEEL = mat('Steel', (0.035, 0.036, 0.042), 1.0, 0.38)
M_RIM = mat('Rim', (0.05, 0.05, 0.056), 1.0, 0.3)   # rolled edges: the most handled steel on a helm, so the most worn and bright
M_GOLD = mat('Gold', (0.95, 0.68, 0.32), 1.0, 0.3)
M_LEATHER = mat('Leather', (0.045, 0.022, 0.011), 0.0, 0.58)
M_BUCKLE = mat('Buckle', (0.30, 0.30, 0.31), 1.0, 0.32)
M_ETCH = mat('Etch', (0.012, 0.012, 0.014), 1.0, 0.75)
M_LINER = mat('Liner', (0.018, 0.016, 0.014), 0.0, 0.9)
def coll(name):
    c = bpy.data.collections.new(name); sc.collection.children.link(c); return c
C_PLATES, C_TRIM, C_INLAY = coll('Plates'), coll('Trim'), coll('Inlay')

# ---------------- the shell: measured envelope + clearance (cm) ----------------
YC = 3.6                           # centre of the section, Blender y (= -UE y)
ZTOP, ZD = 182.3, 170.0            # apex, start of the dome
Z_T = [146.0, 149.0, 152.0, 156.0, 160.0, 164.0, 167.0, 170.0]
A_T = [10.45, 10.40, 10.35, 10.25, 10.40, 10.95, 11.40, 11.65]     # half width
F_T = [12.45, 12.35, 12.15, 11.95, 12.10, 12.70, 13.25, 13.65]     # front depth from YC
B_T = [11.30, 11.20, 11.15, 11.20, 11.60, 12.60, 13.40, 13.80]     # back depth from YC
NSE = 2.2; EX = 2.0 / NSE; P_DOME = 2.1

def _prof(tab, z):
    z = np.asarray(z, float); low = catmull(Z_T, tab, np.minimum(z, ZD))
    u = np.clip((z - ZD) / (ZTOP - ZD), 0, 1)
    return low * np.power(np.maximum(1 - u ** P_DOME, 0.0), 1 / P_DOME)

def surf(phi, z):
    """phi 0 = front (-Y), +90 deg = +X (the knight's left), 180 = back. z in cm. Returns metres."""
    phi = np.asarray(phi, float); z = np.asarray(z, float) * np.ones_like(phi)
    a, f, b = _prof(A_T, z), _prof(F_T, z), _prof(B_T, z)
    c, s = np.cos(phi), np.sin(phi)
    d = b + (f - b) * smoothstep(-0.25, 0.25, c)
    x = a * np.sign(s) * np.abs(s) ** EX
    y = YC - d * np.sign(c) * np.abs(c) ** EX
    return np.stack([x, y, z], -1) * 0.01

def surf_n(phi, z, dp=2e-3, dz=0.02):
    phi = np.asarray(phi, float); z = np.minimum(np.asarray(z, float) * np.ones_like(phi), ZTOP - 0.12)
    tp = surf(phi + dp, z) - surf(phi - dp, z)
    tz = surf(phi, z + dz) - surf(phi, z - dz)
    n = np.cross(tp, tz)
    n /= np.linalg.norm(n, axis=-1, keepdims=True) + 1e-15
    p = surf(phi, z); c = np.array([0, YC * 0.01, 1.65]); out = p - c
    return n * np.where(np.sum(n * out, -1, keepdims=True) < 0, -1.0, 1.0)

def lay(phi, z, off, ex=None):
    """A point on a layer: the shell + a constant offset (m) + a shape function ex(phi, z, base) in metres."""
    phi = np.asarray(phi, float); z = np.asarray(z, float) * np.ones_like(phi)
    b = surf(phi, z); n = surf_n(phi, z)
    d = np.asarray(off, float) * np.ones_like(phi)
    if ex is not None: d = d + ex(phi, z, b)
    return b + n * d[..., None]

# ---- medial comb (keel), same idea as the chest's medial keel: follows x, so it runs over the apex without a singularity
def keel(phi, z, b):
    x = b[..., 0]
    front = smoothstep(177.6, 178.8, z); back = smoothstep(160.5, 165.0, z)
    g = np.where(np.cos(phi) > 0, front, back)
    return 0.0032 * np.exp(-(x / 0.0120) ** 2) * g
# ---- the visor's pointed ridge: the sparrow-beak silhouette, strongest in the lower half, gone at the brow
Z_R = [156.0, 158.0, 161.0, 164.5, 168.0, 171.0, 174.0]
H_R = [0.00, 0.45, 1.70, 2.45, 1.70, 0.50, 0.00]
def ridge(phi, z, b):
    x = np.abs(b[..., 0]); rr = np.sqrt(x * x + 0.0012 ** 2)
    h = catmull(Z_R, H_R, np.clip(z, 156, 174)) * 0.01
    front = np.cos(phi) > 0
    return np.where(front, h * np.clip(1 - rr / 0.072, 0, 1) ** 1.55, 0.0)

OFF_BOWL, OFF_CHEEK, OFF_VISOR, OFF_BROW = 0.0, 0.0014, 0.0028, 0.0046
def L_bowl(phi, z, off=0.0): return lay(phi, z, OFF_BOWL + off, keel)
def L_cheek(phi, z, off=0.0): return lay(phi, z, OFF_CHEEK + off)
def L_visor(phi, z, off=0.0): return lay(phi, z, OFF_VISOR + off, ridge)
def L_brow(phi, z, off=0.0): return lay(phi, z, OFF_BROW + off)
def N_of(layer, phi, z, off=0.0):
    """Numerical normal of any layer (includes the comb / ridge shape)."""
    phi = np.asarray(phi, float); z = np.asarray(z, float) * np.ones_like(phi)
    dp, dz = 3e-3, 0.03; z2 = np.minimum(z, ZTOP - 0.12)
    tp = layer(phi + dp, z2, off) - layer(phi - dp, z2, off); tz = layer(phi, z2 + dz, off) - layer(phi, z2 - dz, off)
    n = np.cross(tp, tz); n /= np.linalg.norm(n, axis=-1, keepdims=True) + 1e-15
    return n * np.where(np.sum(n * surf_n(phi, z2), -1, keepdims=True) < 0, -1.0, 1.0)

# ---------------- outlines (cm, phi in rad) ----------------
def rim(phi): return 149.6 + 1.6 * (1 - np.cos(phi)) / 2                      # lowest edge of the helm
def plates_low(phi): return rim(phi) + 3.7                                    # lower edge of cheeks + nape
def _adeg(phi): return np.abs(np.angle(np.exp(1j * np.asarray(phi, float)))) / DEG
def brow_b(phi):                                                              # brow band: V over the visor, falls to the back
    a = _adeg(phi)
    return 172.6 + 1.5 * np.minimum(a / 34.0, 1) ** 0.75 - 2.7 * smoothstep(100.0, 175.0, a)
def brow_t(phi):
    a = _adeg(phi)
    return brow_b(phi) + 2.45 + 0.35 * np.minimum(a / 34.0, 1)
V_PHI = 101.0; PV_PHI, PV_Z = 90.0, 171.1                                    # visor end, pivot position
def _visor_round(a, z):
    """Round the visor's arm into the pivot: both edges close on the pivot height past 76 deg."""
    t = np.clip((a - 76.0) / (V_PHI - 76.0), 0, 1); f = np.sqrt(np.maximum(1 - t ** 2, 0))
    return PV_Z + (z - PV_Z) * f
def vis_b(phi):
    a = np.abs(np.asarray(phi, float)) / DEG
    return _visor_round(a, 158.1 + 9.4 * np.minimum(a / 92.0, 1) ** 1.3)
def vis_t(phi):
    a = np.abs(np.asarray(phi, float)) / DEG
    return _visor_round(a, 173.7 + 0.3 * np.minimum(a / 92.0, 1))
S0, S1 = 6.5, 53.0                                                            # slit from / to (deg)
def slit_c(phi):
    a = np.abs(np.asarray(phi, float)) / DEG
    return 168.7 + 1.9 * np.clip((a - S0) / (S1 - S0), 0, 1) ** 1.45
def slit_h(phi):
    a = np.abs(np.asarray(phi, float)) / DEG
    t = np.clip((a - S0) / (S1 - S0), 0, 1)
    return 0.01 + 0.74 * np.sin(PI * t ** 0.62) ** 0.55 * ((a > S0) & (a < S1))
CHEEK_END = 104.0
def cheek_t(phi):
    a = np.abs(np.asarray(phi, float)) / DEG
    z = 165.0 + 3.6 * np.minimum(a / 86.0, 1) ** 0.8
    t = np.clip((a - 92.0) / (CHEEK_END - 92.0), 0, 1); f = np.sqrt(np.maximum(1 - t ** 2.2, 0))
    lo = plates_low(np.asarray(phi, float))
    return lo + (z - lo) * f
def cheek_b(phi): return plates_low(phi)
def bowl_b(phi):
    a = _adeg(phi)
    upper = 170.0 - 5.2 * smoothstep(66.0, 88.0, a)
    return upper + (plates_low(np.asarray(phi, float)) - upper) * smoothstep(88.0, 100.0, a)

# ---------------- plate builder ----------------
def weld(ob):
    import bmesh
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    for e in bm.edges:                                       # UV seam at the back, medial line
        v0, v1 = e.verts[0].co, e.verts[1].co
        e.seam = abs(v0.x) < 1e-5 and abs(v1.x) < 1e-5 and v0.y > YC * 0.01 and v1.y > YC * 0.01
    bm.to_mesh(ob.data); bm.free(); ob.data.update()

def warp_cols(phi0, phi1, n, keep=(), cluster=()):
    """Columns from phi0 to phi1 (deg), with exact breakpoints."""
    a = np.linspace(phi0, phi1, n)
    for k in keep:
        a[np.argmin(np.abs(a - k))] = k
    extra = [e for c in cluster for e in (c - 3.6, c - 1.5, c + 1.5, c + 3.6) if phi0 < e < phi1]
    if extra:
        # drop plain columns that crowd a cluster column, keep the ends and the breakpoints
        ex = np.array(extra); hard = np.array(list(keep) + [phi0, phi1])
        a = np.array([v for v in a if np.min(np.abs(hard - v)) < 1e-6 or np.min(np.abs(ex - v)) > 1.8])
        a = np.array(sorted(set(np.round(np.concatenate([a, ex]), 4))))
    return np.sort(a)

def plate(name, cols_deg, zb, zt, nv, layer, m=M_STEEL, c=C_PLATES, vp=1.0, off=0.0, seam=False):
    ph = np.asarray(cols_deg) * DEG
    W = np.linspace(0, 1, nv) ** vp
    Pts = []
    for p in ph:
        z0, z1 = float(zb(np.array(p))), float(zt(np.array(p)))
        Pts.append(layer(np.full(nv, p), z0 + (z1 - z0) * W, off))
    V = np.stack(Pts)
    U = np.concatenate([np.zeros((1, nv)), np.cumsum(np.linalg.norm(np.diff(V, axis=0), axis=-1), axis=0)], 0)
    Vv = np.concatenate([np.zeros((len(ph), 1)), np.cumsum(np.linalg.norm(np.diff(V, axis=1), axis=-1), axis=1)], 1)
    uv = np.stack([U - U[len(ph) // 2], Vv], -1).reshape(-1, 2)
    ob = mesh_obj(name, V.reshape(-1, 3), grid_faces(len(ph), nv), m, c, uv)
    ob['unwrap'] = 1; ob['seam_back'] = 1 if seam else 0
    if seam: weld(ob)
    return ob

def edge_tube(name, layer, phis_deg, zf, off, rad, seg=8, m=M_RIM, closed=False):
    ph = np.asarray(phis_deg) * DEG; z = zf(ph)
    return tube(name, layer(ph, z, off), rad, m, C_TRIM, seg, closed=closed, up=surf_n(ph, z))

# ---- bowl: everything above the brow + the nape. No plate edge is free: each has a rolled tube, and a liner closes the inside
cols = warp_cols(-180, 180, 56 * r, keep=(0.0,), cluster=(-180.0, 0.0, 180.0))
def build_bowl():
    ph = cols * DEG; nv = 20 * r
    w = 1 - (1 - np.linspace(0, 1, nv)) ** 1.55              # rows tighten toward the apex so the dome stays round
    Z = bowl_b(ph)[:, None] + (ZTOP - bowl_b(ph))[:, None] * w[None, :]
    V = L_bowl(ph[:, None] * np.ones_like(Z), Z)
    U = np.concatenate([np.zeros((1, nv)), np.cumsum(np.linalg.norm(np.diff(V, axis=0), axis=-1), axis=0)], 0)
    Vv = np.concatenate([np.zeros((len(ph), 1)), np.cumsum(np.linalg.norm(np.diff(V, axis=1), axis=-1), axis=1)], 1)
    ob = mesh_obj('Bowl', V.reshape(-1, 3), grid_faces(len(ph), nv), M_STEEL, C_PLATES, np.stack([U, Vv], -1).reshape(-1, 2))
    ob['unwrap'] = 1; ob['seam_back'] = 1
    weld(ob)
build_bowl()
# rolled lower edge of the nape, from behind one cheek round the back to the other
a = np.linspace(100, 260, 56 * r)
edge_tube('Rim_Nape', L_bowl, a, plates_low, 0.0, 0.0030)
# comb bar: forehead -> apex -> nape, a raised roped ridge as on real armets (keeps the silhouette crisp at any distance)
def medial(z0, z1, n):
    t = np.linspace(0, 1, n)
    zf = z0 + (ZTOP - z0) * np.sin(t * PI / 2); zb_ = z1 + (ZTOP - z1) * np.sin(t * PI / 2)
    return np.concatenate([np.zeros(n), np.full(n - 1, PI)]), np.concatenate([zf, zb_[::-1][1:]])
pc, zc = medial(179.2, 173.6, 26 * r)
tc = np.linspace(0, 1, len(pc)); sink = smoothstep(0.0, 0.14, tc) * smoothstep(0.0, 0.10, 1 - tc)   # both ends run down into the plate
Pc = L_bowl(pc, zc, 0.0004 * sink - 0.0060 * (1 - sink)); Nc = N_of(L_bowl, pc, zc)
Nc[len(Nc) // 2] = (0, 0, 1)
tube('Comb', Pc, 0.0046, M_RIM, C_TRIM, 8, flat=0.82, up=Nc)
# ---- cheek / bevor plate
cols = warp_cols(-CHEEK_END, CHEEK_END, 44 * r, keep=(0.0,))
plate('Cheek', cols, cheek_b, cheek_t, 11 * r, L_cheek)
a = np.linspace(-CHEEK_END, CHEEK_END, 76 * r)
edge_tube('Rim_CheekLow', L_cheek, a, cheek_b, 0.0, 0.0030)
for s in (-1, 1):
    a = np.concatenate([np.linspace(s * 88.5, s * 92, 4 * r), s * (92 + 12 * np.sin(np.linspace(0, PI / 2, 14 * r)))[1:]])
    edge_tube('Rim_CheekTop%d' % s, L_cheek, a, cheek_t, 0.0, 0.0024)
# ---- neck lames
def lame(name, lo, hi, base, flare, nv=4):
    cols = warp_cols(-180, 180, 60 * r, keep=(0.0,))
    ph = cols * DEG; pt = np.linspace(-PI, PI, 104 * r)
    def L(phi, z, off=0.0):
        t = np.clip((z - lo(phi)) / np.maximum(hi(phi) - lo(phi), 1e-3), 0, 1)
        return lay(phi, z, base + off + flare * (1 - t) ** 1.2)
    plate(name, cols, lo, hi, nv * r, L, seam=True)
    tube('Rim_' + name, L(pt[:-1], lo(pt[:-1])), 0.0030, M_RIM, C_TRIM, 8, closed=True, up=surf_n(pt[:-1], lo(pt[:-1])))
    return L
LB_lo = lambda p: rim(p); LB_hi = lambda p: rim(p) + 2.5
LA_lo = lambda p: rim(p) + 1.75; LA_hi = lambda p: rim(p) + 5.0
L_B = lame('LameB', LB_lo, LB_hi, -0.0016, 0.0060)
L_A = lame('LameA', LA_lo, LA_hi, -0.0006, 0.0042)
# ---- visor: a single grid with two holes for the sights
def build_visor():
    cols = warp_cols(-V_PHI, V_PHI, 54 * r, keep=(0.0,), cluster=(0.0,))
    for k in (-S1, -S0, S0, S1):
        i = np.argmin(np.abs(cols - k)); cols[i] = k
    cols = np.sort(cols); ph = cols * DEG; n = len(cols)
    nl, nm, nu = 12 * r, 3, 7 * r
    rows = []
    zb, zt, sc_, sh = vis_b(ph), vis_t(ph), slit_c(ph), slit_h(ph)
    lo, hi = sc_ - sh, sc_ + sh
    # the slit lines can fall outside the visor's rounded arm: keep them between its edges
    pad = (zt - zb) * 0.45; mid = (zb + zt) / 2
    lo = np.where(np.abs(cols) > S1, mid - np.minimum(pad, 0.4), lo); hi = np.where(np.abs(cols) > S1, mid + np.minimum(pad, 0.4), hi)
    for j in range(nl): rows.append(zb + (lo - zb) * j / nl)
    for j in range(nm): rows.append(lo + (hi - lo) * j / nm)
    for j in range(nu + 1): rows.append(hi + (zt - hi) * j / nu)
    Z = np.stack(rows, 1)                                     # (cols, rows)
    V = L_visor(ph[:, None] * np.ones_like(Z), Z)
    nv = Z.shape[1]
    # faces; the hole = the mid band between S0 and S1 on each side
    F = []
    mc = np.abs(cols[:-1] + cols[1:]) / 2
    inhole = (mc > S0) & (mc < S1)
    for i in range(n - 1):
        for j in range(nv - 1):
            if inhole[i] and nl <= j < nl + nm: continue
            F.append((i * nv + j, (i + 1) * nv + j, (i + 1) * nv + j + 1, i * nv + j + 1))
    U = np.concatenate([np.zeros((1, nv)), np.cumsum(np.linalg.norm(np.diff(V, axis=0), axis=-1), axis=0)], 0)
    Vv = np.concatenate([np.zeros((n, 1)), np.cumsum(np.linalg.norm(np.diff(V, axis=1), axis=-1), axis=1)], 1)
    ob = mesh_obj('Visor', V.reshape(-1, 3), F, M_STEEL, C_PLATES, np.stack([U - U[n // 2], Vv], -1).reshape(-1, 2))
    ob['unwrap'] = 1; ob['seam_back'] = 0
build_visor()
a = np.linspace(-V_PHI, V_PHI, 64 * r)
edge_tube('Rim_VisorLow', L_visor, a, vis_b, 0.0, 0.0028)
a2 = np.linspace(-V_PHI, V_PHI, 30 * r)
edge_tube('Rim_VisorTop', L_visor, a2, vis_t, 0.0, 0.0020)
# sights: a rolled lip round each hole, and a wall going back to the liner so the slit has real depth
for s in (-1, 1):
    a = np.linspace(S0, S1, 18 * r) * s
    p = a * DEG
    up, dn = slit_c(p) + slit_h(p), slit_c(p) - slit_h(p)
    Pz = np.concatenate([up, dn[::-1][1:-1]]); Pa = np.concatenate([p, p[::-1][1:-1]])
    tube('Rim_Slit%d' % s, L_visor(Pa, Pz), 0.0015, M_RIM, C_TRIM, 6, closed=True, up=surf_n(Pa, Pz))
    # flange on the upper edge: a stronger turned lip, the armet's "sight"
    tube('Rim_SightLip%d' % s, L_visor(p, up + 0.13, 0.0012), 0.0023, M_RIM, C_TRIM, 6, up=surf_n(p, up))
    n = len(Pa); Vw = np.vstack([L_visor(Pa, Pz), lay(Pa, Pz, -0.0036)])
    Fw = [(n + k, n + (k + 1) % n, (k + 1) % n, k) for k in range(n)]
    Lw = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(L_visor(Pa, Pz), axis=0), axis=1))])
    uvw = np.vstack([np.stack([Lw, np.zeros(n)], 1), np.stack([Lw, np.full(n, 0.012)], 1)])
    w = mesh_obj('SlitWall%d' % s, Vw, Fw, M_LINER, C_PLATES, uvw)
    w['slitwall'] = s
# ---- brow band: all the way round, like a circlet set into the steel
cols = warp_cols(-180, 180, 60 * r, keep=(0.0,), cluster=(0.0,))
plate('Brow', cols, brow_b, brow_t, 3 * r, L_brow, seam=True)
a = np.linspace(-180, 180, 100 * r)[:-1]
a = np.sort(np.concatenate([a, [0.0, -2.0, 2.0]]))
edge_tube('Rim_BrowLow', L_brow, a, brow_b, 0.0, 0.0020, closed=True)
edge_tube('Rim_BrowTop', L_brow, a, brow_t, 0.0, 0.0017, closed=True)
# ---- liner: closes the whole inside. Dark, so a slit or the neck opening never shows skin or sky
def build_liner():
    n = 42 * r; cols = warp_cols(-180, 180, n, keep=(0.0,)); ph = cols * DEG
    w = np.concatenate([[0.0, 0.03, 0.1], np.linspace(0.22, 1.0, 8 * r)])
    Z = rim(ph)[:, None] + (ZTOP - rim(ph))[:, None] * w[None, :] ** 0.9
    d = np.full(Z.shape, -0.0034); d[:, 0] = 0.0030; d[:, 1] = -0.0005
    V = lay(ph[:, None] * np.ones_like(Z), Z, d)
    F = [tuple(reversed(f)) for f in grid_faces(n, len(w))]
    U = np.concatenate([np.zeros((1, len(w))), np.cumsum(np.linalg.norm(np.diff(V, axis=0), axis=-1), axis=0)], 0)
    Vv = np.concatenate([np.zeros((n, 1)), np.cumsum(np.linalg.norm(np.diff(V, axis=1), axis=-1), axis=1)], 1)
    ob = mesh_obj('Liner', V.reshape(-1, 3), F, M_LINER, C_PLATES, np.stack([U, Vv], -1).reshape(-1, 2))
    ob['unwrap'] = 1; ob['seam_back'] = 1
    weld(ob)
build_liner()

# ---------------- bosses: visor pivots + rondel at the nape (the shield's boss, small) ----------------
def frame(n):
    n = n / np.linalg.norm(n); u = np.cross([0, 0, 1.0], n); u /= np.linalg.norm(u); v = np.cross(n, u); return u, v, n
def boss(name, c, nrm, R, H, fl, m=M_STEEL, seg=22, rings=6, ringm=M_GOLD):
    u, v, n = frame(np.asarray(nrm, float)); seg *= r; rings *= r
    A = np.linspace(0, 2 * PI, seg, endpoint=False); Rr = np.linspace(0, R + fl, rings)
    Hh = np.where(Rr <= R, H * np.clip(1 - (Rr / R) ** 2, 0, 1) ** 0.75, 0.0) + 0.0012
    V = (c + np.outer(np.cos(A), Rr)[..., None] * u + np.outer(np.sin(A), Rr)[..., None] * v + Hh[None, :, None] * n)
    F = []
    for i in range(seg):
        i2 = (i + 1) % seg
        for j in range(rings - 1):
            F.append((i * rings + j, i * rings + j + 1, i2 * rings + j + 1, i2 * rings + j))
    uv = np.stack([np.outer(np.cos(A), Rr), np.outer(np.sin(A), Rr)], -1).reshape(-1, 2)
    ob = mesh_obj(name, V.reshape(-1, 3), F, m, C_PLATES, uv)
    wm = ob.modifiers.new('Weld', 'WELD'); wm.merge_threshold = 1e-6
    q = np.linspace(0, 2 * PI, 40 * r)
    P = c + np.outer(np.cos(q) * R, u) + np.outer(np.sin(q) * R, v) + n * 0.0016
    tube('Rim_' + name, P, 0.0017, ringm, C_TRIM, 6, closed=True, up=np.tile(n, (len(q), 1)))
    return u, v, n
for s in (-1, 1):
    ph = np.array(s * PV_PHI * DEG); z = np.array(PV_Z)
    c = L_visor(ph, z, 0.0004); nn = N_of(L_visor, ph, z)
    u, v, n = boss('Pivot%d' % s, c, nn, 0.0145, 0.0048, 0.0045)
    rivet('Rivet_PivotStud%d' % s, c + n * 0.0052, n, 0.0042, M_GOLD, C_TRIM)
    if HIGH:
        for k in range(6):
            t = 2 * PI * k / 6 + PI / 6
            rivet('Rivet_Pivot%d_%d' % (s, k), c + 0.0165 * (math.cos(t) * u + math.sin(t) * v) + n * 0.0012, n, 0.0020, M_STEEL, C_TRIM)
# rondel: a disc on a short stem at the nape, as on 15th c. armets; it covers the end of the strap
ph = np.array(PI); z = np.array(160.6)
c0 = L_bowl(ph, z); n0 = N_of(L_bowl, ph, z)
STEM = 0.0135
q = np.linspace(0, 1, 5 * r)[:, None]
tube('Stem', c0 + n0 * (q * STEM), 0.0085, M_STEEL, C_TRIM, 10, up=np.tile([0, 0, 1.0], (len(q), 1)))
c1 = c0 + n0 * STEM
u, v, n = boss('Rondel', c1, n0, 0.0235, 0.0058, 0.0048)
q = np.linspace(0, 2 * PI, 34 * r)
Rn = 0.0235 + 0.0048
tube('Rim_RondelEdge', c1 + np.outer(np.cos(q) * Rn, u) + np.outer(np.sin(q) * Rn, v), 0.0020, M_RIM, C_TRIM, 6, closed=True, up=np.tile(n, (len(q), 1)))
# back of the disc, facing the nape
A = np.linspace(0, 2 * PI, 22 * r, endpoint=False)
Vb = np.vstack([c1 + np.outer(np.cos(A) * Rn, u) + np.outer(np.sin(A) * Rn, v), [c1 - n * 0.0005]])
Fb = [(len(A), (i + 1) % len(A), i) for i in range(len(A))]
mesh_obj('RondelBack', Vb, Fb, M_STEEL, C_PLATES, np.vstack([np.stack([np.cos(A) * Rn, np.sin(A) * Rn], 1), [[0, 0]]]))
rivet('Rivet_RondelStud', c1 + n * 0.0064, n, 0.0052, M_GOLD, C_TRIM)
if HIGH:
    for k in range(8):
        t = 2 * PI * k / 8 + PI / 8
        rivet('Rivet_Rondel%d' % k, c1 + (0.0235 + 0.0026) * (math.cos(t) * u + math.sin(t) * v) + n * 0.0016, n, 0.0017, M_STEEL, C_TRIM)
# ---------------- leather closing strap: cheek -> under the rondel, with a buckle on the knight's left ----------------
ZS_ = 158.2
for s in (-1, 1):
    a = np.linspace(CHEEK_END - 8, 172, 16 * r) * s * DEG
    zz = ZS_ + (160.3 - ZS_) * np.linspace(0, 1, len(a)) ** 2
    ribbon('Strap%d' % s, L_bowl(a, zz, 0.0034 if HIGH else 0.0052), N_of(L_bowl, a, zz), 0.0165, M_LEATHER, C_TRIM, thick=0.0018 if HIGH else 0)
    if HIGH:
        for k, aa in enumerate((s * (CHEEK_END - 4.5) * DEG, s * (CHEEK_END - 7.5) * DEG)):
            aa = np.array(aa); zr = np.array(ZS_)
            rivet('Rivet_StrapCheek%d_%d' % (s, k), L_cheek(aa, zr, 0.004), N_of(L_cheek, aa, zr), 0.0030, M_STEEL, C_TRIM)
# buckle on the left: a steel frame + tongue (geometry stays in the game mesh, it's a silhouette detail up close)
a0 = 132.0 * DEG; zz0 = ZS_ + (160.3 - ZS_) * ((132 - CHEEK_END + 8) / (172 - CHEEK_END + 8)) ** 2
cb = L_bowl(np.array(a0), np.array(zz0), 0.0058); nb = N_of(L_bowl, np.array(a0), np.array(zz0))
tg = L_bowl(np.array(a0 + 0.05), np.array(zz0), 0.0058) - cb; tg /= np.linalg.norm(tg); bt = np.cross(nb, tg); bt /= np.linalg.norm(bt)
W_, H_ = 0.0120, 0.0115
corner = np.array([(-W_, -H_), (W_, -H_), (W_, H_), (-W_, H_)])
pts = []
for i in range(4):
    p, q2 = corner[i], corner[(i + 1) % 4]
    for t_ in np.linspace(0, 1, 3 * r, endpoint=False): pts.append(p + (q2 - p) * t_)
pts = np.array(pts); P = cb + pts[:, 0:1] * tg + pts[:, 1:2] * bt
tube('Buckle', P, 0.0019, M_BUCKLE, C_TRIM, 6, closed=True, up=np.tile(nb, (len(P), 1)))
tube('BuckleTongue', cb + np.outer(np.linspace(-W_, W_ * 1.05, 4 * r), tg) + nb * 0.0007, 0.0012, M_BUCKLE, C_TRIM, 6, up=np.tile(nb, (4 * r, 1)))

# ================ gold inlay + etch: bake only ================
def inlay(name, layer, ph, z, w=0.0016, off=0.0, m=None):
    ph = np.asarray(ph, float); z = np.asarray(z, float)
    ribbon(name, layer(ph, z, off + 0.00012), N_of(layer, ph, z), w, m or M_GOLD, C_INLAY, thick=0.0001 if m else 0.0004)
def sprig(tag, layer, phi0, z0, side, length=9.0, rise=2.5, up=1, off=0.0, leaf=0.016, count=4):
    """A laurel spray in (arc cm, cm) around (phi0, z0): side = +/-1 phi direction, the set's motif on shield + pauldrons."""
    R = 12.0
    t = np.linspace(0, 1, 40 * r)
    sa = phi0 + side * (length * t) / R; sz = z0 + rise * up * t ** 1.5
    inlay('Laurel_Stem_%s' % tag, layer, sa, sz, 0.0012, off)
    for k in range(count):
        tk = 0.2 + 0.72 * k / max(count - 1, 1)
        for sgn in (1, -1):
            if k == count - 1 and sgn == -1: continue
            ang = (0.62 + 0.25 * k / count) * sgn
            aa = np.linspace(0, 2 * PI, 22 * r)
            ox, oz = (phi0 + side * (length * tk) / R), z0 + rise * up * tk ** 1.5
            L_, W2 = leaf * 100, leaf * 100 * 0.32
            dirz = math.atan2(rise * up * 1.5 * tk ** 0.5, length)
            th = dirz + ang
            lx = ((L_ / 2) * (1 - np.cos(aa)) * math.cos(th) - (W2 / 2) * np.sin(aa) * math.sin(th))
            lz = (L_ / 2) * (1 - np.cos(aa)) * math.sin(th) + (W2 / 2) * np.sin(aa) * math.cos(th)
            inlay('Laurel_Leaf_%s_%d_%d' % (tag, k, sgn), layer, ox + side * lx / R, oz + lz, 0.0011, off)
def lozenge(tag, layer, phic, zc, ax, az, w=0.0026, off=0.0, p=1.25):
    q = np.linspace(0, 2 * PI, 80 * r); c_, s_ = np.cos(q), np.sin(q)
    R = 12.0
    x = ax * np.sign(c_) * np.abs(c_) ** (2 / p); z = zc + az * np.sign(s_) * np.abs(s_) ** (2 / p)
    inlay('Inlay_Lozenge_' + tag, layer, phic + x / R, z, w, off)

if HIGH:
    # ---- bowl: lozenge on the forehead, double line along the comb, lozenge on the crown of the nape
    lozenge('Fore', L_bowl, 0.0, 177.05, 1.55, 1.85, 0.0024)
    lozenge('Fore2', L_bowl, 0.0, 177.05, 1.95, 2.3, 0.0012)
    rivet('Rivet_Fore', L_bowl(np.array(0.0), np.array(177.05), 0.0002), N_of(L_bowl, np.array(0.0), np.array(177.05)), 0.0048, M_GOLD, C_INLAY)
    lozenge('Nape', L_bowl, PI, 169.0, 1.7, 2.1, 0.0024)
    lozenge('Nape2', L_bowl, PI, 169.0, 2.1, 2.6, 0.0012)
    rivet('Rivet_Nape', L_bowl(np.array(PI), np.array(169.0), 0.0002), N_of(L_bowl, np.array(PI), np.array(169.0)), 0.0048, M_GOLD, C_INLAY)
    for s in (-1, 1):
        sprig('Nape%d' % s, L_bowl, s * (PI - 0.24), 168.0, -s, 8.0, 3.0, -1, 0.0, 0.0115, 3)
    # comb lines at x = const: solve phi from x so they run true over the apex
    def comb_line(sx, dx, z0, z1, w):
        zz = np.linspace(z0, ZTOP - 0.01, 90 * r)
        a = _prof(A_T, zz)
        ok = a > dx * 1.002
        zz = zz[ok]; a = a[ok]
        pf = np.arcsin(np.clip((dx / a) ** (1 / EX), 0, 1))
        zb2 = np.linspace(z1, ZTOP - 0.01, 90 * r); ab = _prof(A_T, zb2); okb = ab > dx * 1.002; zb2 = zb2[okb]; ab = ab[okb]
        pb = PI - np.arcsin(np.clip((dx / ab) ** (1 / EX), 0, 1))
        ph = np.concatenate([pf, pb[::-1]]) * sx; z_ = np.concatenate([zz, zb2[::-1]])
        inlay('Inlay_Comb%d_%.3f' % (sx, dx), L_bowl, ph, z_, w)
    for sx in (-1, 1):
        comb_line(sx, 0.92, 179.2, 173.9, 0.0022)
        comb_line(sx, 1.22, 179.0, 173.9, 0.0011)
    # ---- brow band: gold border lines, etched field, laurel running back from the centre, small lozenge at the V
    a = np.linspace(-PI, PI, 170 * r)
    h = brow_t(a) - brow_b(a)
    inlay('Etch_Brow', L_brow, a, brow_b(a) + h * 0.5, 0.0150, 0.0, M_ETCH)
    inlay('Inlay_BrowLow', L_brow, a, brow_b(a) + 0.34, 0.0022)
    inlay('Inlay_BrowTop', L_brow, a, brow_t(a) - 0.30, 0.0016)
    for s in (-1, 1):
        for k, a0_ in enumerate((0.14, 0.86, 1.62, 2.38)):
            ph0 = s * a0_; z_m = float(brow_b(np.array(ph0)) + 1.12)
            sprig('Brow%d_%d' % (s, k), L_brow, ph0, z_m, s, 6.4, -0.05, 1, 0.0, 0.0095, 4)
    # ---- visor: pale on the ridge, double border with etch, a gold line round each sight, laurel at the chin
    inlay('Inlay_PaleVisor', L_visor, np.zeros(40 * r), np.linspace(float(vis_b(np.array(0.0))) + 0.5, 167.9, 40 * r), 0.0034)
    inlay('Inlay_PaleBar', L_visor, np.zeros(14 * r), np.linspace(170.1, 172.5, 14 * r), 0.0030)
    a = np.linspace(-84, 84, 120 * r) * DEG
    bb = vis_b(a)
    inlay('Etch_VisorBorder', L_visor, a, bb + 0.92, 0.0105, 0.0, M_ETCH)
    inlay('Inlay_VisorBorder', L_visor, a, bb + 0.46, 0.0024)
    inlay('Inlay_VisorBorder2', L_visor, a, bb + 1.40, 0.0012)
    for s in (-1, 1):
        a = np.linspace(S0 - 1.6, S1 + 2.6, 40 * r) * s * DEG
        tt = np.clip((np.abs(a) / DEG - (S0 - 1.6)) / (S1 + 2.6 - S0 + 1.6), 0, 1)
        grow = 0.42 * np.sin(PI * tt) ** 0.5
        inlay('Inlay_SightLow%d' % s, L_visor, a, slit_c(a) - slit_h(a) - grow - 0.12, 0.0016)
        sprig('Chin%d' % s, L_visor, s * 0.05, float(vis_b(np.array(s * 0.05))) + 2.15, s, 8.0, 2.4, 1, 0.0, 0.0115, 3)
    # ---- breaths: three staggered rows on each flank, a steel funnel with a dark centre
    def breath(tag, ph_, z_):
        ph_ = np.array(ph_); z_ = np.array(z_)
        c = L_visor(ph_, z_, 0.00015); nn = N_of(L_visor, ph_, z_)
        u_, v_, n_ = frame(nn)
        na = 16; A_ = np.linspace(0, 2 * PI, na, endpoint=False)
        def ring(R_, h_): return c + np.outer(np.cos(A_) * R_, u_) + np.outer(np.sin(A_) * R_, v_) + n_ * h_
        V_ = np.vstack([ring(0.0034, 0.0), ring(0.0028, 0.0005), ring(0.0020, 0.0001)])
        F_ = []
        for j in range(2):
            for i in range(na):
                i2 = (i + 1) % na
                F_.append((j * na + i, j * na + i2, (j + 1) * na + i2, (j + 1) * na + i))
        mesh_obj('Breath_f' + tag, V_, F_, M_STEEL, C_INLAY)
        Vd = np.vstack([ring(0.0021, 0.00005), [c + n_ * 0.00005]])
        Fd = [(i, (i + 1) % na, na) for i in range(na)]
        mesh_obj('Breath_d' + tag, Vd, Fd, M_LINER, C_INLAY)
    for s in (-1, 1):
        for row, z_r in enumerate((166.1, 164.4, 162.7)):
            n_c = 6 - row
            for k in range(n_c):
                ph_d = 24.0 + k * 7.6 + (3.8 if row % 2 else 0.0)
                breath('%d_%d_%d' % (s, row, k), s * ph_d * DEG, z_r + 0.18 * k)
    # ---- cheeks: line along the lower + rear edge, laurel on the jaw
    a = np.linspace(-CHEEK_END + 5, CHEEK_END - 5, 100 * r) * DEG
    inlay('Inlay_CheekLow', L_cheek, a, cheek_b(a) + 0.62, 0.0022)
    inlay('Etch_CheekLow', L_cheek, a, cheek_b(a) + 1.2, 0.0080, 0.0, M_ETCH)
    inlay('Inlay_CheekLow2', L_cheek, a, cheek_b(a) + 1.74, 0.0012)
    for s in (-1, 1):
        zz = np.linspace(float(cheek_b(np.array(s * (CHEEK_END - 5) * DEG))) + 0.62, 165.3, 30 * r)
        inlay('Inlay_CheekRear%d' % s, L_cheek, np.full_like(zz, s * (CHEEK_END - 5) * DEG), zz, 0.0020)
        sprig('Jaw%d' % s, L_cheek, s * 66 * DEG, 159.6, s, 7.0, 3.2, 1, 0.0, 0.0115, 3)
        for k, zr in enumerate(np.linspace(158.6, 164.8, 4)):
            pa = np.array(s * (CHEEK_END - 2.1) * DEG); zz_ = np.array(zr)
            if k == 0: continue
            rivet('Rivet_CheekRear%d_%d' % (s, k), L_cheek(pa, zz_, 0.0002), N_of(L_cheek, pa, zz_), 0.0032, M_STEEL, C_TRIM)
    # ---- nape: border along the lower edge
    a = np.linspace(102, 258, 60 * r) * DEG
    inlay('Inlay_NapeLow', L_bowl, a, plates_low(a) + 0.62, 0.0022)
    inlay('Etch_NapeLow', L_bowl, a, plates_low(a) + 1.2, 0.0080, 0.0, M_ETCH)
    inlay('Inlay_NapeLow2', L_bowl, a, plates_low(a) + 1.74, 0.0012)
    # ---- lames: one gold line each + sliding rivets
    a = np.linspace(-PI, PI, 120 * r)
    inlay('Inlay_LameB', L_B, a, LB_lo(a) + 1.15, 0.0016)
    inlay('Inlay_LameA', L_A, a, LA_lo(a) + 1.0, 0.0016)
    for k in range(10):
        pa = np.array(2 * PI * k / 10 + 0.1)
        zz_ = LB_lo(pa) + 1.9; rivet('Rivet_LameB%d' % k, L_B(pa, zz_, 0.0002), surf_n(pa, zz_), 0.0029, M_STEEL, C_TRIM)
        pa2 = np.array(2 * PI * (k + 0.5) / 10 + 0.1); zz2 = LA_lo(pa2) + 1.9
        rivet('Rivet_LameA%d' % k, L_A(pa2, zz2, 0.0002), surf_n(pa2, zz2), 0.0029, M_STEEL, C_TRIM)
    # ---- brow band rivets, regularly round the head, between the gold lines
    for pa_ in (0.77, 1.50, 2.27, PI, -0.77, -1.50, -2.27):
        pa = np.array(pa_); zz_ = (brow_b(pa) + brow_t(pa)) / 2; k = int(pa_ * 100)
        rivet('Rivet_Brow%d' % k, L_brow(pa, zz_, 0.0003), surf_n(pa, zz_), 0.0034, M_GOLD, C_TRIM)
    # ---- brow V: a small lozenge stud over the visor
    pa = np.array(0.0); zz_ = brow_b(pa) + 1.22
    lozenge('Brow', L_brow, 0.0, float(zz_), 0.72, 0.90, 0.0018)
    rivet('Rivet_BrowV', L_brow(pa, zz_, 0.0003), surf_n(pa, zz_), 0.0034, M_GOLD, C_TRIM)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, f'helm_build_r{RES}.blend'))
print('BUILD OK', len(bpy.data.objects), 'objects', sum(len(o.data.polygons) for o in bpy.data.objects if o.type == 'MESH'), 'faces (pre-mod)')
