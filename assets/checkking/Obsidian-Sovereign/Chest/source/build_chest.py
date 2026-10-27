# Build the layered chest (high-detail scene) and save chest_build.blend.
# blender -b --factory-startup -P build_chest.py
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import bpy
from chestlib import *

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

def coll(name):
    c = bpy.data.collections.new(name); sc.collection.children.link(c); return c
C_PLATES, C_TRIM, C_STRAPS, C_INLAY = coll('Plates'), coll('Trim'), coll('Straps'), coll('Inlay')

TWO = 2 * math.pi
RES = int(os.environ.get('CHEST_RES', '1'))  # 1 = low poly, 3 = high poly density

# ---------------- plate outlines ----------------
def zt_breast(p):
    u = abs(p)
    if u < 0.62: return 0.430 + 0.046 * (u / 0.62) ** 1.6
    if u < 0.95: return 0.476 - 0.004 * math.sin(math.pi * (u - 0.62) / 0.33)
    w = (u - 0.95) / (1.78 - 0.95)
    return 0.476 - 0.14 * math.sin(w * math.pi * 0.62)
def zb_breast(p): return 0.112 + 0.02 * (abs(p) / 1.78) ** 2

def zt_back(p):
    u = abs(p - math.pi)
    if u < 0.55: return 0.452 + 0.024 * (u / 0.55) ** 1.6
    if u < 0.85: return 0.476
    w = (u - 0.85) / (1.59 - 0.85)
    return 0.476 - 0.14 * math.sin(w * math.pi * 0.62)
def zb_back(p): return 0.052 + 0.012 * (abs(p - math.pi) / 1.59) ** 2

def zt_plack(p): return 0.272 - 0.135 * (abs(p) / 1.45) ** 1.15
def zb_plack(p): return 0.072 + 0.006 * (abs(p) / 1.45) ** 2

OFF_BACK, OFF_BREAST, OFF_PLACK = 0.0, 0.003, 0.0062
FAULDS = [(0.046, 0.082, 0.0040), (0.022, 0.056, 0.0065), (-0.004, 0.031, 0.0090)]
CULET = [(0.024, 0.062, -0.0032), (-0.004, 0.034, -0.0004)]
FPH = 1.84

r = RES
patch('Backplate', 1.55, TWO - 1.55, zb_back, zt_back, OFF_BACK, 70 * r, 56 * r, M_STEEL, C_PLATES)
patch('Breastplate', -1.78, 1.78, zb_breast, zt_breast, OFF_BREAST, 96 * r, 56 * r, M_STEEL, C_PLATES)
patch('Plackart', -1.45, 1.45, zb_plack, zt_plack, OFF_PLACK, 72 * r, 26 * r, M_STEEL, C_PLATES)
for k, (z0, z1, off) in enumerate(FAULDS):
    patch(f'Fauld{k+1}', -FPH, FPH, lambda p, z0=z0: z0 + 0.004 * (abs(p) / FPH) ** 2, lambda p, z1=z1: z1 + 0.004 * (abs(p) / FPH) ** 2, off, 80 * r, 8 * r, M_STEEL, C_PLATES)
for k, (z0, z1, off) in enumerate(CULET):
    patch(f'Culet{k+1}', 1.66, TWO - 1.66, lambda p, z0=z0: z0, lambda p, z1=z1: z1, off, 70 * r, 8 * r, M_STEEL, C_PLATES)

# ---------------- rolled rims ----------------
def edge_pts(phis, zf, off):
    phis = np.asarray(phis); zz = np.array([zf(p) for p in phis])
    return place(phis, zz, off)

seg = 10 * r
ph = np.linspace(-1.78, 1.78, 160 * r)
tube('Rim_Breast', edge_pts(ph, zt_breast, OFF_BREAST + 0.0026), 0.0042, M_STEEL, C_TRIM, seg)
ph = np.linspace(1.55, TWO - 1.55, 140 * r)
tube('Rim_Back', edge_pts(ph, zt_back, OFF_BACK + 0.0026), 0.0042, M_STEEL, C_TRIM, seg)
ph = np.linspace(-1.45, 1.45, 120 * r)
tube('Rim_Plackart', edge_pts(ph, zt_plack, OFF_PLACK + 0.0016), 0.0026, M_STEEL, C_TRIM, seg)
tube('Rim_BackBottom', edge_pts(np.linspace(1.55, TWO - 1.55, 120 * r), zb_back, OFF_BACK + 0.0014), 0.0024, M_STEEL, C_TRIM, seg)
for k, (z0, z1, off) in enumerate(FAULDS):
    tube(f'Rim_Fauld{k+1}', edge_pts(np.linspace(-FPH, FPH, 130 * r), lambda p, z0=z0: z0 + 0.004 * (abs(p) / FPH) ** 2, off + 0.0012), 0.0019, M_STEEL, C_TRIM, seg)
for k, (z0, z1, off) in enumerate(CULET):
    tube(f'Rim_Culet{k+1}', edge_pts(np.linspace(1.66, TWO - 1.66, 110 * r), lambda p, z0=z0: z0, off + 0.0012), 0.0019, M_STEEL, C_TRIM, seg)
for s in (-1, 1):
    zz = np.linspace(zb_breast(1.78), zt_breast(1.78), 40 * r)
    tube(f'Rim_BreastSide{s}', place(np.full_like(zz, s * 1.78), zz, OFF_BREAST + 0.0012), 0.0018, M_STEEL, C_TRIM, seg)

# ---------------- straps + buckles ----------------
def buckle(name, phc, zc, off, s):
    w, h = 0.020, 0.032
    R = float(np.linalg.norm(surf(phc, zc)[:2]))
    dph = w / 2 / R
    loop = []
    for t in np.linspace(0, 1, 48 * r, endpoint=False):
        a = TWO * t
        # rounded rectangle via superellipse
        cx, cz = np.sign(math.cos(a)) * abs(math.cos(a)) ** 0.3, np.sign(math.sin(a)) * abs(math.sin(a)) ** 0.3
        loop.append(place(phc + cx * dph, zc + cz * h / 2, off))
    tube(name, np.array(loop), 0.0021, M_BUCKLE, C_STRAPS, 8 * r, closed=True)
    zz = np.full(12, zc); pp = np.linspace(phc + s * dph, phc - s * dph * 0.15, 12)
    tube(name + '_Tongue', place(pp, zz, off + 0.0012), 0.0013, M_BUCKLE, C_STRAPS, 6 * r)

for s in (-1, 1):
    for zc in (0.165, 0.288):
        a, b = s * 1.98, s * 1.43
        p0, p1 = min(a, b), max(a, b)
        patch(f'Strap_{s}_{zc}', p0, p1, lambda p, zc=zc: zc - 0.0115, lambda p, zc=zc: zc + 0.0115, 0.0078, 24 * r, 4 * r, M_LEATHER, C_STRAPS, thick=0.003)
        buckle(f'Buckle_{s}_{zc}', s * 1.575, zc, 0.0112, s)
        for dz in (-0.0055, 0.0055):
            p = place(s * 1.93, zc + dz, 0.0108); n = surf_n(s * 1.93, zc + dz)
            rivet(f'StrapRivet_{s}_{zc}_{dz}', p, n, 0.0026, M_BUCKLE, C_STRAPS)

# shoulder straps (over the shoulder, back plate to breast plate)
for s in (-1, 1):
    pf, pb = s * 0.80, math.pi - s * 0.70
    B0, B1 = place(pb, 0.425, 0.0078), place(pb, 0.472, 0.0078)
    F1, F0 = place(pf, 0.472, 0.0078), place(pf, 0.418, 0.0078)
    up = np.array([s * 0.35, 0.0, 0.94]); up /= np.linalg.norm(up)
    arc = [B1 + (F1 - B1) * t + up * 0.013 * math.sin(math.pi * t) for t in np.linspace(0, 1, 40 * r)]
    path = np.concatenate([np.linspace(B0, B1, 10 * r, endpoint=False), np.array(arc), np.linspace(F1, F0, 12 * r)[1:]])
    ctr = np.array([s * 0.085, 0.0, 0.40])
    nrm = path - ctr; nrm /= np.linalg.norm(nrm, axis=1, keepdims=True)
    ribbon(f'ShoulderStrap_{s}', path, nrm, 0.024, M_LEATHER, C_STRAPS, thick=0.003)
    buckle(f'ShoulderBuckle_{s}', pf, 0.438, 0.0112, 1)
    for dz in (-0.006, 0.006):
        rivet(f'ShoulderRivet_{s}_{dz}', place(pb + s * 0.0, 0.432 + dz, 0.0108), surf_n(pb, 0.432 + dz), 0.0026, M_BUCKLE, C_STRAPS)

# ---------------- rivets on plates ----------------
riv = [(0, 0.250, OFF_PLACK, 0.0045)]
for s in (-1, 1):
    riv += [(s * 1.30, 0.108, OFF_PLACK, 0.0038), (s * 0.75, 0.130, OFF_PLACK, 0.0034)]
    for (z0, z1, off) in FAULDS:
        riv.append((s * 1.74, (z0 + z1) / 2 + 0.003, off, 0.0033))
    riv += [(s * 1.68, 0.40, OFF_BREAST, 0.003), (s * 1.70, 0.24, OFF_BREAST, 0.003)]
for i, (p, z, off, rr) in enumerate(riv):
    rivet(f'Rivet{i}', place(p, z, off), surf_n(p, z), rr, M_STEEL, C_TRIM)

# ---------------- gold inlay ----------------
R0 = 0.17
def inlay(name, phis, zs, off, w=0.0016):
    phis = np.asarray(phis); zs = np.asarray(zs)
    ribbon(name, place(phis, zs, off + 0.00015), surf_n(phis, zs), w, M_GOLD, C_INLAY)

ph = np.linspace(-1.62, 1.62, 200 * r)
inlay('Inlay_BreastBorder', ph, [zt_breast(p) - 0.016 for p in ph], OFF_BREAST)
inlay('Inlay_BreastBorder2', ph, [zt_breast(p) - 0.0205 for p in ph], OFF_BREAST, 0.0011)
phb = np.linspace(1.70, TWO - 1.70, 180 * r)
inlay('Inlay_BackBorder', phb, [zt_back(p) - 0.016 for p in phb], OFF_BACK)
inlay('Inlay_BackBorder2', phb, [zt_back(p) - 0.0205 for p in phb], OFF_BACK, 0.0011)
ph = np.linspace(-1.32, 1.32, 160 * r)
inlay('Inlay_PlackBorder', ph, [zt_plack(p) - 0.011 for p in ph], OFF_PLACK)
inlay('Inlay_PlackBorder2', ph, [zt_plack(p) - 0.0145 for p in ph], OFF_PLACK, 0.0011)
ph = np.linspace(-1.32, 1.32, 160 * r)
inlay('Inlay_PlackBottom', ph, [zb_plack(p) + 0.011 for p in ph], OFF_PLACK)

def bez(p0, p1, p2, t):
    t = np.asarray(t)[:, None]
    return (1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t * t * p2

# laurel branches (designed in unwrapped metres: s = phi * R0, z)
for side in (-1, 1):
    P0, P1, P2 = np.array([0.035, 0.300]), np.array([0.085, 0.395]), np.array([0.165, 0.405])
    t = np.linspace(0, 1, 120 * r)
    st = bez(P0, P1, P2, t)
    inlay(f'Laurel_Stem_{side}', side * st[:, 0] / R0, st[:, 1], OFF_BREAST, 0.0019)
    for k, tk in enumerate(np.linspace(0.12, 0.92, 8)):
        c = bez(P0, P1, P2, [tk])[0]; d = bez(P0, P1, P2, [min(tk + 0.01, 1)])[0] - c; d /= np.linalg.norm(d)
        nrm2 = np.array([-d[1], d[0]]) * (1 if k % 2 else -1)
        ang = 0.6
        ax = d * math.cos(ang) + nrm2 * math.sin(ang); ay = np.array([-ax[1], ax[0]])
        L, W = 0.020 - 0.006 * tk, 0.0062
        q = np.linspace(0, TWO, 40 * r)
        # leaf outline: pointed ellipse from the stem outward
        pts = np.array([c + ax * (L / 2) * (1 - math.cos(a)) + ay * (W / 2) * math.sin(a) * abs(math.sin(a / 2)) ** 0.2 for a in q])
        inlay(f'Laurel_Leaf_{side}_{k}', side * pts[:, 0] / R0, pts[:, 1], OFF_BREAST, 0.0014)

# etched bands between the double gold borders (dark matte stipple, classic etched-and-gilt border)
M_ETCH = mat('Etch', (0.012, 0.012, 0.014), 0.7, 0.75)
def etch(name, phis, zs, off, w):
    phis = np.asarray(phis); zs = np.asarray(zs)
    ribbon(name, place(phis, zs, off + 0.00008), surf_n(phis, zs), w, M_ETCH, C_INLAY, thick=0.0001)
ph = np.linspace(-1.62, 1.62, 200 * r)
etch('Etch_Breast', ph, [zt_breast(p) - 0.01825 for p in ph], OFF_BREAST, 0.0034)
etch('Etch_Back', phb, [zt_back(p) - 0.01825 for p in phb], OFF_BACK, 0.0034)
ph = np.linspace(-1.32, 1.32, 160 * r)
etch('Etch_Plack', ph, [zt_plack(p) - 0.01275 for p in ph], OFF_PLACK, 0.0026)

# central lozenge on the keel
q = np.linspace(0, TWO, 80 * r)
dz = 0.022 * np.cos(q); ds = 0.011 * np.sign(np.sin(q)) * np.abs(np.sin(q)) ** 1.6 * (1 - np.abs(np.cos(q)) * 0.2)
inlay('Inlay_Lozenge', ds / R0, 0.355 + dz, OFF_BREAST + 0.0004, 0.0016)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, f'chest_build_r{RES}.blend'))
print('BUILD OK', len(bpy.data.objects), 'objects')


