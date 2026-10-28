# Build the layered left sabaton (high or low density) and save boot_build_r<RES>.blend.
# CHEST_RES=1|3 blender -b --factory-startup -P build_boots.py
# Frame: the Codex set's world frame (metres, Z up, front = -Y). Left boot on +X, in Codex's boot envelope:
# x 0.063..0.207, toe y -0.238 .. heel y 0.093, sole on the ground (z 0), top 0.24 where the greave overlaps.
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, r'C:\Users\hossam.rabea\checkking-work\gauntlets')
import numpy as np
import bpy
from gauntletlib import *

OUT = os.path.dirname(__file__)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

def mat(name, col, metal, rough):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*col, 1); b.inputs['Metallic'].default_value = metal; b.inputs['Roughness'].default_value = rough
    return m
M_STEEL = mat('Steel', (0.035, 0.036, 0.042), 1.0, 0.38)
M_GOLD = mat('Gold', (0.95, 0.68, 0.32), 1.0, 0.3)
M_LEATHER = mat('Leather', (0.045, 0.022, 0.011), 0.0, 0.58)
M_BUCKLE = mat('Buckle', (0.30, 0.30, 0.31), 1.0, 0.32)
M_ETCH = mat('Etch', (0.012, 0.012, 0.014), 0.7, 0.75)

def coll(name):
    c = bpy.data.collections.new(name); sc.collection.children.link(c); return c
C_PLATES, C_TRIM, C_SHOE, C_INLAY = coll('Plates'), coll('Trim'), coll('Shoe'), coll('Inlay')
RES = int(os.environ.get('CHEST_RES', '1')); r = RES
PI = math.pi
X0 = 0.135

def steel(name, u0, u1, hb, ht, off, nu, nv, thick=0.0020):
    ob = patch(name, u0, u1, hb, ht, off, nu * r, nv * r, M_STEEL, C_PLATES, thick=thick)
    ob.vertex_groups.new(name='inner'); ob.modifiers['Solidify'].shell_vertex_group = 'inner'   # inward shell -> lower texel density later
    return ob
def leather(name, ax, u0, u1, hb, ht, nu, nv):
    use(ax); return patch(name, u0, u1, lambda u: hb, lambda u: ht, 0.0, nu * r, nv * r, M_LEATHER, C_SHOE, thick=0)
def rim(name, ax, us, hf, off, rad, seg=8):
    use(ax); us = np.asarray(us); hh = np.array([hf(u) for u in us])
    tube(name, ax.at(us, hh, off), rad, M_STEEL, C_TRIM, seg * r, up=ax.surf_n(us, hh))
def side_rim(name, ax, u, h0, h1, off, rad):
    use(ax); hh = np.linspace(h0, h1, 24); uu = np.full_like(hh, u)
    tube(name, ax.at(uu, hh, off), rad, M_STEEL, C_TRIM, 6 * r, up=ax.surf_n(uu, hh))
def inlay(name, ax, us, hs, off, w=0.0013, m=None):
    us = np.asarray(us); hs = np.asarray(hs)
    ribbon(name, ax.at(us, hs, off + 0.00012), ax.surf_n(us, hs), w, m or M_GOLD, C_INLAY, thick=0.0001 if m else 0.0004)
def lozenge(name, ax, h, off, half_w, half_h, w=0.0013):
    q = np.linspace(0, 2 * PI, 60 * r); RC = float(ax.r(h) * ax.k(h))
    inlay(name, ax, (half_w * np.sign(np.sin(q)) * np.abs(np.sin(q)) ** 1.6) / RC, h + half_h * np.cos(q), off, w)
def laurel(tag, ax, hc, off, length=0.022, sign_h=1.0):
    """two sprigs either side of the centre line, growing along h (sign_h picks the direction)."""
    RC = float(ax.r(hc) * ax.k(hc))
    for side in (-1, 1):
        t = np.linspace(0, 1, 50 * r)
        sx, sh = side * (0.007 + length * t), hc + sign_h * 0.020 * t ** 1.3
        inlay(f'Laurel_Stem_{tag}{side}', ax, sx / RC, sh, off, 0.0011)
        for k, tk in enumerate((0.3, 0.55, 0.8)):
            a = np.linspace(0, 2 * PI, 24 * r); cx, ch = side * (0.007 + length * tk), hc + sign_h * 0.020 * tk ** 1.3
            L, Wd = 0.0080, 0.0030; ang = (0.9 if k % 2 else -0.4) * sign_h
            lx = cx + side * (L / 2) * (1 - np.cos(a)) * math.cos(ang) - (Wd / 2) * np.sin(a) * math.sin(ang)
            lh = ch + (L / 2) * (1 - np.cos(a)) * math.sin(ang) + (Wd / 2) * np.sin(a) * math.cos(ang)
            inlay(f'Laurel_Leaf_{tag}{side}_{k}', ax, lx / RC, lh, off, 0.0009)

# ---------------- foot: horizontal surface of revolution, axis at sole-top height, toe toward -Y ----------------
# h = y (O at y 0); r = height of the upper above the axis, k = half width / r. u = 0 is the top, +pi/2 the outer side (+X).
ZA = 0.024
F_H = [-0.270, -0.258, -0.235, -0.200, -0.160, -0.115, -0.070, -0.030, 0.010, 0.050]
F_R = [0.004, 0.020, 0.033, 0.042, 0.050, 0.060, 0.071, 0.079, 0.083, 0.080]
F_W = [0.006, 0.026, 0.041, 0.050, 0.055, 0.055, 0.052, 0.048, 0.046, 0.044]
FOOT = Axial((X0, 0.0, ZA), (0, -1, 0), (0, 0, 1), F_H, F_R, [w / rr for w, rr in zip(F_W, F_R)])
leather('Upper_Foot', FOOT, -PI / 2, PI / 2, -0.266, 0.045, 36, 30)

# ---------------- ankle: vertical surface of revolution, u = 0 toward the toe, +pi/2 outer (+X) ----------------
YA = 0.038; ZT = 0.245
A_H = [-0.222, -0.190, -0.150, -0.110, -0.070, -0.030, 0.000]           # h = z - ZT
A_R = [0.058, 0.056, 0.050, 0.047, 0.047, 0.049, 0.052]                  # front/back half depth
A_W = [0.048, 0.047, 0.042, 0.039, 0.040, 0.043, 0.046]                  # half width
ANK = Axial((X0, YA, ZT), (0, 0, -1), (0, -1, 0), A_H, A_R, [w / rr for w, rr in zip(A_W, A_R)])
leather('Upper_Ankle', ANK, -PI, PI, -0.218, -0.004, 48, 22)

# ---------------- plates over the foot: toe cap, 5 lames, instep plate (each one over the one toward the toe) ----------------
use(FOOT)
UB = 1.45
def band(h0, h1, dip=-0.005):   # edges sweep slightly toward the toe at the sides
    return (lambda u: h0 + dip * (u / UB) ** 2), (lambda u: h1 + dip * (u / UB) ** 2)
steel('ToeCap', -UB, UB, lambda u: -0.2685, lambda u: -0.196 - 0.005 * (u / UB) ** 2, 0.0035, 30, 20)
side_rim('Rim_ToeSideL', FOOT, -UB, -0.262, -0.198, 0.0035 + 0.0009, 0.0013)
side_rim('Rim_ToeSideR', FOOT, UB, -0.262, -0.198, 0.0035 + 0.0009, 0.0013)
LAMES = [('Lame1', -0.205, -0.178, 0.0047), ('Lame2', -0.186, -0.159, 0.0059), ('Lame3', -0.167, -0.140, 0.0071),
         ('Lame4', -0.148, -0.121, 0.0083), ('Lame5', -0.129, -0.102, 0.0095)]
for name, h0, h1, off in LAMES:
    hb, ht = band(h0, h1)
    steel(name, -UB, UB, hb, ht, off, 34, 8)
    rim('Rim_' + name, FOOT, np.linspace(-UB, UB, 50), hb, off + 0.0011, 0.0014)
INSTEP = ('Instep', -0.110, 0.012, 0.0107)   # runs back under the ankle plate's front edge
hb_i, ht_i = band(INSTEP[1], INSTEP[2])
steel('Instep', -UB, UB, hb_i, ht_i, INSTEP[3], 34, 18)
rim('Rim_Instep', FOOT, np.linspace(-UB, UB, 50), hb_i, INSTEP[3] + 0.0011, 0.0016)
for s in (-1, 1):
    side_rim(f'Rim_InstepSide{s}', FOOT, s * UB, hb_i(UB), ht_i(UB), INSTEP[3] + 0.0009, 0.0013)
# sliding rivets at both ends of every lame, two on each side of the instep plate
for i, (name, h0, h1, off) in enumerate(LAMES):
    for s in (-1, 1):
        u = s * (UB - 0.13); hm = (h0 + h1) / 2 - 0.005 * ((UB - 0.13) / UB) ** 2
        rivet(f'Rivet_{name}{s}', FOOT.at(u, hm, off), FOOT.surf_n(u, hm), 0.0024, M_STEEL, C_TRIM)
for s in (-1, 1):
    for hm in (-0.095, -0.045):
        u = s * (UB - 0.15)
        rivet(f'Rivet_Instep{s}_{hm}', FOOT.at(u, hm, INSTEP[3]), FOOT.surf_n(u, hm), 0.0026, M_STEEL, C_TRIM)

# gold + etch: toe cap borders and lozenge, a line on every lame, lozenge and laurel on the instep plate
us = np.linspace(-(UB - 0.10), UB - 0.10, 90 * r)
toe_t = lambda u: -0.196 - 0.005 * (u / UB) ** 2
inlay('Inlay_ToeBack', FOOT, us, [toe_t(u) - 0.0090 for u in us], 0.0035)
inlay('Inlay_ToeBack2', FOOT, us, [toe_t(u) - 0.0125 for u in us], 0.0035, 0.0009)
inlay('Etch_ToeBack', FOOT, us, [toe_t(u) - 0.0107 for u in us], 0.0035, 0.0024, M_ETCH)
lozenge('Inlay_ToeLozenge', FOOT, -0.236, 0.0037, 0.0070, 0.0110)
for name, h0, h1, off in LAMES:
    inlay('Inlay_' + name, FOOT, us, [(h0 + h1) / 2 - 0.005 * (u / UB) ** 2 for u in us], off, 0.0011)
inlay('Inlay_InstepBottom', FOOT, us, [hb_i(u) + 0.0075 for u in us], INSTEP[3])
inlay('Inlay_InstepBottom2', FOOT, us, [hb_i(u) + 0.0105 for u in us], INSTEP[3], 0.0009)
inlay('Etch_InstepBottom', FOOT, us, [hb_i(u) + 0.0090 for u in us], INSTEP[3], 0.0024, M_ETCH)
lozenge('Inlay_InstepLozenge', FOOT, -0.062, INSTEP[3] + 0.0002, 0.0085, 0.0140)
laurel('Instep', FOOT, -0.080, INSTEP[3] + 0.0001, 0.020, 1.0)

# ---------------- ankle plate (front + sides), heel counter, top band ----------------
use(ANK)
UA = 1.95
cb = lambda u: -0.205 + 0.058 * max(math.cos(u), 0.0) ** 2   # dips down over the instep at the front, overlapping it
ct = lambda u: -0.030
steel('AnklePlate', -UA, UA, cb, ct, 0.0060, 54, 22)
rim('Rim_AnkleBottom', ANK, np.linspace(-UA, UA, 90), cb, 0.0060 + 0.0012, 0.0019)
for s in (-1, 1):
    side_rim(f'Rim_AnkleSide{s}', ANK, s * UA, cb(UA), ct(UA), 0.0060 + 0.0010, 0.0015)
UH = 1.38
hc_t = lambda u: -0.046 - 0.014 * ((u - PI) / UH) ** 2   # up to the top band: closes the back above the strap
steel('HeelPlate', PI - UH, PI + UH, lambda u: -0.2185, hc_t, 0.0088, 40, 22)
rim('Rim_HeelTop', ANK, np.linspace(PI - UH, PI + UH, 60), hc_t, 0.0088 + 0.0012, 0.0019)
for s in (-1, 1):
    side_rim(f'Rim_HeelSide{s}', ANK, PI + s * UH, -0.214, hc_t(PI + s * UH), 0.0088 + 0.0010, 0.0015)
bt = lambda u: -0.0035
steel('TopBand', -PI, PI, lambda u: -0.042, bt, 0.0090, 72, 8)
rim('Rim_TopBand', ANK, np.linspace(-PI, PI, 120), bt, 0.0090 + 0.0016, 0.0030)
rim('Rim_TopBandBottom', ANK, np.linspace(-PI, PI, 120), lambda u: -0.042, 0.0090 + 0.0010, 0.0016)
ua = np.linspace(-PI, PI, 200 * r)
inlay('Inlay_TopBand', ANK, ua, np.full_like(ua, -0.0145), 0.0090)
inlay('Inlay_TopBand2', ANK, ua, np.full_like(ua, -0.0305), 0.0090, 0.0010)
inlay('Etch_TopBand', ANK, ua, np.full_like(ua, -0.0225), 0.0090, 0.0060, M_ETCH)
uf = np.linspace(-(UA - 0.12), UA - 0.12, 140 * r)
inlay('Inlay_AnkleBottom', ANK, uf, [cb(u) + 0.0085 for u in uf], 0.0060)
inlay('Inlay_AnkleBottom2', ANK, uf, [cb(u) + 0.0118 for u in uf], 0.0060, 0.0009)
lozenge('Inlay_AnkleLozenge', ANK, -0.098, 0.0062, 0.0080, 0.0150)
uh = np.linspace(PI - UH + 0.12, PI + UH - 0.12, 90 * r)
inlay('Inlay_HeelTop', ANK, uh, [hc_t(u) - 0.0090 for u in uh], 0.0088)
for s in (-1, 1):
    for hm in (-0.180, -0.120):
        rivet(f'Rivet_Ankle{s}_{hm}', ANK.at(s * (UA - 0.14), hm, 0.0060), ANK.surf_n(s * (UA - 0.14), hm), 0.0027, M_STEEL, C_TRIM)
    rivet(f'Rivet_Heel{s}', ANK.at(PI + s * (UH - 0.14), -0.150, 0.0088), ANK.surf_n(PI + s * (UH - 0.14), -0.150), 0.0027, M_STEEL, C_TRIM)

# ---------------- ankle strap with buckle on the outer side (+X) ----------------
HS = -0.150
us_s = np.linspace(-PI, PI, 160 * r)
offs = np.array([0.0108 if abs(((u + PI) % (2 * PI)) - PI) > PI - UH else 0.0080 for u in us_s])   # over the heel plate it rides higher
P = ANK.surf(us_s, np.full_like(us_s, HS)) + ANK.surf_n(us_s, np.full_like(us_s, HS)) * offs[:, None]
Nn = ANK.surf_n(us_s, np.full_like(us_s, HS))
gap = np.abs(us_s - PI / 2) > 0.10           # leave room for the buckle frame
P_s, N_s = P[gap], Nn[gap]
split = np.argmax(np.diff(np.where(gap)[0]) > 1) + 1
ribbon('Strap_A', P_s[:split], N_s[:split], 0.017, M_LEATHER, C_SHOE, thick=0.0025)
ribbon('Strap_B', P_s[split:], N_s[split:], 0.017, M_LEATHER, C_SHOE, thick=0.0025)
c = ANK.at(PI / 2, HS, 0.0122); n = ANK.surf_n(PI / 2, HS)
t = np.array([0.0, 0.0, 1.0]); t -= (t @ n) * n; t /= np.linalg.norm(t); b = np.cross(n, t)
rect = [c + t * 0.0125 + b * 0.0085, c + t * 0.0125 - b * 0.0085, c - t * 0.0125 - b * 0.0085, c - t * 0.0125 + b * 0.0085]
pts = np.vstack([np.linspace(rect[i], rect[(i + 1) % 4], 8, endpoint=False) for i in range(4)])
tube('Buckle_Frame', pts, 0.0016, M_BUCKLE, C_TRIM, 8 * r, closed=True, up=np.tile(n, (len(pts), 1)))
tube('Buckle_Tongue', np.linspace(c - b * 0.0085, c + b * 0.0060 + n * 0.0012, 10), 0.0011, M_BUCKLE, C_TRIM, 6 * r, up=np.tile(t, (10, 1)))
for k in range(3):   # strap holes past the buckle
    hp = ANK.at(PI / 2 + 0.24 + 0.09 * k, HS, 0.0108 + 0.0026)
    rivet(f'Rivet_StrapHole{k}', hp, ANK.surf_n(PI / 2 + 0.24 + 0.09 * k, HS), 0.0016, M_ETCH, C_INLAY, seg=10)

# ---------------- sole: leather slab with a welt and stitches ----------------
def outline(n_side=60, n_heel=40, grow=0.004):
    hs = np.linspace(-0.2655, 0.020, n_side)
    right = [(X0 + float(FOOT.r(h) * FOOT.k(h)) + grow, h) for h in hs]
    aw = float(ANK.r(-0.222) * ANK.k(-0.222)) + grow; ad = float(ANK.r(-0.222)) + grow
    heel = [(X0 + aw * math.sin(a), YA + ad * -math.cos(a)) for a in np.linspace(PI / 2 + 0.25, 3 * PI / 2 - 0.25, n_heel)]
    left = [(2 * X0 - x, y) for x, y in right[::-1]]
    tip = [(X0, -0.2705 - grow)]
    pts = right + heel + left + tip
    return np.array(pts)   # counter-clockwise seen from above (toe -> outer side -> heel -> inner side)
O2 = outline(60 * r, 40 * r)
Z0, Z1 = 0.0, ZA
n = len(O2)
L = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(np.vstack([O2, O2[:1]]), axis=0), axis=1))])
V = [(x, y, Z0) for x, y in O2] + [(O2[0][0], O2[0][1], Z0)] + [(x, y, Z1) for x, y in O2] + [(O2[0][0], O2[0][1], Z1)]
F = [(k, k + 1, n + 1 + k + 1, n + 1 + k) for k in range(n)]
uvs = [(L[k], 0.0) for k in range(n + 1)] + [(L[k], Z1 - Z0) for k in range(n + 1)]
base = len(V)
V += [(x, y, Z0) for x, y in O2]; uvs += [(x, y) for x, y in O2]
F.append(tuple(range(base, base + n))[::-1])
mesh_obj('Sole', np.array(V), F, M_LEATHER, C_SHOE, np.array(uvs))
welt = np.array([(x, y, Z1 + 0.0004) for x, y in O2])
tube('Welt', welt, 0.0030, M_LEATHER, C_SHOE, 8 * r, closed=True, flat=0.55)
def stitches(name, P, Nrm, dash=0.0036, gap=0.0022, w=0.0012):
    Ls = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
    k, s0 = 0, 0.0
    while s0 + dash < Ls[-1]:
        sel = (Ls >= s0) & (Ls <= s0 + dash)
        if sel.sum() >= 2: ribbon(f'Stitch_{name}_{k}', P[sel], Nrm[sel], w, M_LEATHER, C_INLAY, thick=0.0004)
        s0 += dash + gap; k += 1
dense = np.vstack([np.linspace(O2[i], O2[(i + 1) % n], 6, endpoint=False) for i in range(n)])
stitches('Welt', np.column_stack([dense, np.full(len(dense), Z1 + 0.0031)]), np.tile([0, 0, 1.0], (len(dense), 1)))

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, f'boot_build_r{RES}.blend'))
print('BUILD OK', len(bpy.data.objects), 'objects', sum(len(o.data.polygons) for o in bpy.data.objects if o.type == 'MESH'), 'faces (pre-mod)')
