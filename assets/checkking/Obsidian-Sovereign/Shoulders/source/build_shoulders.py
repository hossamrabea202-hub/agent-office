# Build the layered left pauldron (high or low density) and save shoulder_build_r<RES>.blend.
# CHEST_RES=1|3 blender -b --factory-startup -P build_shoulders.py
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import bpy
from shoulderlib import *

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
C_PLATES, C_TRIM, C_STRAPS, C_INLAY = coll('Plates'), coll('Trim'), coll('Straps'), coll('Inlay')
TWO = 2 * math.pi
RES = int(os.environ.get('CHEST_RES', '1'))
r = RES

# ---------------- plate outlines (h as a function of u) ----------------
UC = 2.15                                         # cap reaches round to here (front/back); the armpit side stays open
def ht_cap(u): return 0.112 - 0.022 * (abs(u) / UC) ** 2
def hb_cap(u): return CAP_LO - 0.014 * (abs(u) / UC) ** 2
OFF_CAP = 0.0095
# lames: (top, bottom, offset, half-range); each tucks under the plate above (smaller offset = further in)
LAMES = [(-0.028, -0.068, 0.0068, 2.05), (-0.058, -0.098, 0.0044, 1.98), (-0.088, -0.128, 0.0022, 1.91), (-0.118, -0.160, 0.0, 1.84)]
DIP = 0.014
def lame_edge(h0, U): return lambda u, h0=h0, U=U: h0 - DIP * (abs(u) / U) ** 2

patch('Cap', -UC, UC, hb_cap, ht_cap, OFF_CAP, 84 * r, 44 * r, M_STEEL, C_PLATES, thick=0.0024)
for k, (h1, h0, off, U) in enumerate(LAMES):
    patch(f'Lame{k+1}', -U, U, lame_edge(h0, U), lame_edge(h1, U), off, 72 * r, 10 * r, M_STEEL, C_PLATES)

# ---------------- rolled rims + stop rib ----------------
def edge_pts(us, hf, off):
    us = np.asarray(us); hh = np.array([hf(u) for u in us])
    return place(us, hh, off)
def edge_tube(name, us, hf, off, rad, mat=M_STEEL):
    us = np.asarray(us); hh = np.array([hf(u) for u in us])
    tube(name, place(us, hh, off), rad, mat, C_TRIM, 8 * r, up=surf_n(us, hh))

edge_tube('Rim_CapTop', np.linspace(-UC, UC, 120 * r), ht_cap, OFF_CAP + 0.0028, 0.0044)
edge_tube('Rim_CapBottom', np.linspace(-UC, UC, 120 * r), hb_cap, OFF_CAP + 0.0018, 0.0030)
for s in (-1, 1):
    hh = np.linspace(hb_cap(UC), ht_cap(UC), 50 * r)
    tube(f'Rim_CapSide{s}', place(np.full_like(hh, s * UC), hh, OFF_CAP + 0.0012), 0.0022, M_STEEL, C_TRIM, 10 * r, up=surf_n(np.full_like(hh, s * UC), hh))
for k, (h1, h0, off, U) in enumerate(LAMES):
    edge_tube(f'Rim_Lame{k+1}', np.linspace(-U, U, 100 * r), lame_edge(h0, U), off + 0.0014, 0.0022)
# turned stop rib across the top of the cap (deflects a blow sliding toward the neck)
us = np.linspace(-1.35, 1.35, 90 * r)
edge_tube('StopRib', us, lambda u: 0.080 + 0.006 * math.cos(u / 1.35 * math.pi / 2), OFF_CAP + 0.0026, 0.0033)

# ---------------- rivets (lame articulation + cap) ----------------
riv = []
for (h1, h0, off, U) in LAMES:
    hm = (h0 + h1) / 2 - 0.003
    riv += [(U - 0.09, hm - DIP * ((U - 0.09) / U) ** 2, off, 0.0034), (-(U - 0.09), hm - DIP * ((U - 0.09) / U) ** 2, off, 0.0034), (0.0, hm, off, 0.0030)]
for s in (-1, 1):
    riv += [(s * (UC - 0.10), hb_cap(UC - 0.10) + 0.012, OFF_CAP, 0.0038), (s * (UC - 0.10), 0.040, OFF_CAP, 0.0034)]
for i, (u, h, off, rr) in enumerate(riv):
    rivet(f'Rivet{i}', place(u, h, off), surf_n(u, h), rr, M_STEEL, C_TRIM)

# ---------------- leather: arming strap round the arm + hanger ----------------
HS_STRAP, RS_STRAP = -0.176, 0.076
q = np.linspace(0, TWO, 90 * r)
loop = O - D * HS_STRAP + RS_STRAP * (np.cos(q)[:, None] * E1 + KY * np.sin(q)[:, None] * EY)
loop[-1] = loop[0]
ribbon('ArmStrap', loop, axis_out(loop), 0.022, M_LEATHER, C_STRAPS, thick=0.003)
# hanger: leather tab from under the last lame down to the arm strap
hh = np.linspace(-0.150, HS_STRAP + 0.006, 24 * r)
R_TOP = float(catmull(HS, RS, -0.150)) - 0.004     # just inside the last lame
pts = np.array([O - D * h + np.interp(h, [HS_STRAP, -0.150], [RS_STRAP + 0.003, R_TOP]) * E1 for h in hh])
ribbon('Hanger', pts, axis_out(pts), 0.026, M_LEATHER, C_STRAPS, thick=0.003)
rivet('HangerRivet', O - D * (HS_STRAP + 0.014) + (np.interp(HS_STRAP + 0.014, [HS_STRAP, -0.150], [RS_STRAP + 0.003, R_TOP]) + 0.0032) * E1, E1, 0.0028, M_BUCKLE, C_STRAPS)

def buckle(name, uc, hc, rad):
    """Rounded-rectangle frame on the arm strap at azimuth uc, plus tongue."""
    w, hgt = 0.020, 0.030
    ctr = O - D * hc
    loop = []
    for t in np.linspace(0, 1, 48 * r, endpoint=False):
        a = TWO * t
        cx = np.sign(math.cos(a)) * abs(math.cos(a)) ** 0.3; cz = np.sign(math.sin(a)) * abs(math.sin(a)) ** 0.3
        uu = uc + cx * (w / 2) / rad
        loop.append(ctr - D * (cz * hgt / 2) + rad * (math.cos(uu) * E1 + KY * math.sin(uu) * EY))
    tube(name, np.array(loop), 0.0021, M_BUCKLE, C_STRAPS, 8 * r, closed=True)
    uu = np.linspace(uc - (w / 2) / rad, uc + 0.15 * (w / 2) / rad, 12)
    tp = np.array([ctr + (rad + 0.0012) * (math.cos(v) * E1 + KY * math.sin(v) * EY) for v in uu])
    tube(name + '_Tongue', tp, 0.0013, M_BUCKLE, C_STRAPS, 6 * r)
buckle('ArmBuckle', -1.75, HS_STRAP, RS_STRAP + 0.0045)

# ---------------- gold inlay + etched bands (same vocabulary as the chest) ----------------
def inlay(name, us, hs, off, w=0.0016):
    us = np.asarray(us); hs = np.asarray(hs)
    ribbon(name, place(us, hs, off + 0.00015), surf_n(us, hs), w, M_GOLD, C_INLAY)
def etch(name, us, hs, off, w):
    us = np.asarray(us); hs = np.asarray(hs)
    ribbon(name, place(us, hs, off + 0.00008), surf_n(us, hs), w, M_ETCH, C_INLAY, thick=0.0001)

us = np.linspace(-(UC - 0.09), UC - 0.09, 200 * r)
inlay('Inlay_CapTop', us, [ht_cap(u) - 0.016 for u in us], OFF_CAP)
inlay('Inlay_CapTop2', us, [ht_cap(u) - 0.0205 for u in us], OFF_CAP, 0.0011)
etch('Etch_CapTop', us, [ht_cap(u) - 0.01825 for u in us], OFF_CAP, 0.0034)
inlay('Inlay_CapBottom', us, [hb_cap(u) + 0.0125 for u in us], OFF_CAP)
inlay('Inlay_CapBottom2', us, [hb_cap(u) + 0.0170 for u in us], OFF_CAP, 0.0011)
etch('Etch_CapBottom', us, [hb_cap(u) + 0.01475 for u in us], OFF_CAP, 0.0034)
for k, (h1, h0, off, U) in enumerate(LAMES):
    ul = np.linspace(-(U - 0.16), U - 0.16, 160 * r)
    inlay(f'Inlay_Lame{k+1}', ul, [lame_edge(h0, U)(u) + 0.0085 for u in ul], off, 0.0013)

# laurel sprays either side of the keel (designed unwrapped: s = u * RC, h)
RC = 0.12
def bez(p0, p1, p2, t):
    t = np.asarray(t)[:, None]
    return (1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t * t * p2
for side in (-1, 1):
    P0, P1, P2 = np.array([0.014, -0.016]), np.array([0.070, -0.004]), np.array([0.118, 0.046])
    st = bez(P0, P1, P2, np.linspace(0, 1, 120 * r))
    inlay(f'Laurel_Stem_{side}', side * st[:, 0] / RC, st[:, 1], OFF_CAP, 0.0018)
    for k, tk in enumerate(np.linspace(0.12, 0.92, 8)):
        c = bez(P0, P1, P2, [tk])[0]; d = bez(P0, P1, P2, [min(tk + 0.01, 1)])[0] - c; d /= np.linalg.norm(d)
        n2 = np.array([-d[1], d[0]]) * (1 if k % 2 else -1)
        ax = d * math.cos(0.6) + n2 * math.sin(0.6); ay = np.array([-ax[1], ax[0]])
        L, W = 0.018 - 0.006 * tk, 0.0056
        qq = np.linspace(0, TWO, 40 * r)
        pts = np.array([c + ax * (L / 2) * (1 - math.cos(a)) + ay * (W / 2) * math.sin(a) * abs(math.sin(a / 2)) ** 0.2 for a in qq])
        inlay(f'Laurel_Leaf_{side}_{k}', side * pts[:, 0] / RC, pts[:, 1], OFF_CAP, 0.0013)

# lozenge on the keel, echoing the breastplate
qq = np.linspace(0, TWO, 80 * r)
dh = 0.018 * np.cos(qq); ds = 0.009 * np.sign(np.sin(qq)) * np.abs(np.sin(qq)) ** 1.6 * (1 - np.abs(np.cos(qq)) * 0.2)
inlay('Inlay_Lozenge', ds / RC, 0.030 + dh, OFF_CAP + 0.0004, 0.0015)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, f'shoulder_build_r{RES}.blend'))
print('BUILD OK', len(bpy.data.objects), 'objects', sum(len(o.data.polygons) for o in bpy.data.objects if o.type == 'MESH'), 'faces (pre-mod)')
