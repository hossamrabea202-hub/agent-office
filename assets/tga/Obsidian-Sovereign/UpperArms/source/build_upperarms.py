# Build the left rerebrace (upper-arm defence) + couter (elbow cop) and save upperarm_build_r<RES>.blend. TGA (Claude), 2026-10-31.
# CHEST_RES=1|3 blender -b --factory-startup -P build_upperarms.py
# checkking's Obsidian Sovereign vocabulary: a domed couter at the point of the elbow with a fan wing on the outer side, two
# articulation lames above it, two hinged shells round the upper arm (outer over inner) with rolled rims, gold borders + etch,
# lozenge and laurel on the outer shell, hinges at the back overlap and strap + buckle at the front; leather lining at the top.
# Frame: the Codex set's world frame (metres, Z up, front = -Y). Left arm on +X, hanging. The elbow E is where the TGA
# vambrace ends; the shoulder S is under checkking's pauldron, which overlaps the rerebrace top on the outer side (z ~1.2).
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy
from gauntletlib import *

OUT = os.path.dirname(os.path.abspath(__file__))
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
RES = int(os.environ.get('CHEST_RES', '1')); r = RES
PI = math.pi

def steel(name, u0, u1, hb, ht, off, nu, nv, thick=0.0022):
    ob = patch(name, u0, u1, hb, ht, off, nu * r, nv * r, M_STEEL, C_PLATES, thick=thick)
    ob.vertex_groups.new(name='inner'); ob.modifiers['Solidify'].shell_vertex_group = 'inner'
    return ob
def rim(ax, name, us, hf, off, rad, seg=8, m=None):
    us = np.asarray(us); hh = np.array([hf(u) for u in us])
    tube(name, ax.at(us, hh, off), rad, m or M_STEEL, C_TRIM, seg * r, up=ax.surf_n(us, hh))
def side_rim(ax, name, u, h0, h1, off, rad):
    hh = np.linspace(h0, h1, 40); uu = np.full_like(hh, u)
    tube(name, ax.at(uu, hh, off), rad, M_STEEL, C_TRIM, 6 * r, up=ax.surf_n(uu, hh))
def inlay(ax, name, us, hs, off, w=0.0013, m=None):
    us = np.asarray(us); hs = np.asarray(hs)
    ribbon(name, ax.at(us, hs, off + 0.00012), ax.surf_n(us, hs), w, m or M_GOLD, C_INLAY, thick=0.0001 if m else 0.0004)
def lozenge(ax, name, u, h, off, half_w, half_h, w=0.0013):
    q = np.linspace(0, 2 * PI, 60 * r); RC = float(ax.r(h) * ax.k(h))
    inlay(ax, name, u + (half_w * np.sign(np.sin(q)) * np.abs(np.sin(q)) ** 1.6) / RC, h + half_h * np.cos(q), off, w)
def laurel(ax, tag, uc, hc, off, length=0.018):
    RC = float(ax.r(hc) * ax.k(hc))
    for side in (-1, 1):
        t = np.linspace(0, 1, 50 * r)
        sx, sh = side * (0.007 + length * t), hc - 0.020 * t ** 1.3
        inlay(ax, f'Laurel_Stem_{tag}{side}', uc + sx / RC, sh, off, 0.0011)
        for k, tk in enumerate((0.3, 0.55, 0.8)):
            a = np.linspace(0, 2 * PI, 24 * r); cx, ch = side * (0.007 + length * tk), hc - 0.020 * tk ** 1.3
            L, Wd = 0.0072, 0.0027; ang = -0.9 if k % 2 else 0.4
            lx = cx + side * (L / 2) * (1 - np.cos(a)) * math.cos(ang) - (Wd / 2) * np.sin(a) * math.sin(ang)
            lh = ch + (L / 2) * (1 - np.cos(a)) * math.sin(ang) + (Wd / 2) * np.sin(a) * math.cos(ang)
            inlay(ax, f'Laurel_Leaf_{tag}{side}_{k}', uc + lx / RC, lh, off, 0.0009)
def buckle(ax, tag, u, h, off):
    c = ax.at(u, h, off); n = ax.surf_n(u, h)
    t = -ax.D.copy(); t -= (t @ n) * n; t /= np.linalg.norm(t); b = np.cross(n, t)
    rect = [c + t * 0.0090 + b * 0.0065, c + t * 0.0090 - b * 0.0065, c - t * 0.0090 - b * 0.0065, c - t * 0.0090 + b * 0.0065]
    pts = np.vstack([np.linspace(rect[i], rect[(i + 1) % 4], 8, endpoint=False) for i in range(4)])
    tube(f'Buckle_{tag}', pts, 0.0013, M_BUCKLE, C_TRIM, 8 * r, closed=True, up=np.tile(n, (len(pts), 1)))
    tube(f'Buckle_{tag}_Tongue', np.linspace(c - b * 0.0065, c + b * 0.0048 + n * 0.0010, 10), 0.0009, M_BUCKLE, C_TRIM, 6 * r, up=np.tile(t, (10, 1)))

# ---------------- upper-arm surface: elbow E -> shoulder S; u = 0 front (-Y), +pi/2 outer (+X), pi back (elbow point)
E = np.array([0.298, 0.0, 1.105]); S = np.array([0.268, 0.0, 1.360])
U_H = [0.000, 0.040, 0.090, 0.140, 0.190, 0.240]
U_D = [0.0420, 0.0430, 0.0440, 0.0455, 0.0475, 0.0500]
U_W = [0.0440, 0.0460, 0.0480, 0.0500, 0.0530, 0.0560]
UP = Axial(E, E - S, (0, -1, 0), U_H, U_D, [w / d for w, d in zip(U_W, U_D)])

# ---- couter: dome on an axis pointing back out of the elbow; fan wing on the outer side
CO = Axial(E + np.array([0.0, 0.036, 0.004]), (0, -1, 0), (0, 0, 1), [0.000, 0.011, 0.022, 0.031, 0.038, 0.041],
           [0.0470, 0.0450, 0.0390, 0.0300, 0.0180, 0.0012], [1.05, 1.05, 1.04, 1.03, 1.02, 1.0])
use(CO)
steel('Couter', -PI, PI, lambda u: 0.0, lambda u: 0.0405, 0.0, 60, 20)
rim(CO, 'Rim_Couter', np.linspace(-PI, PI, 110), lambda u: 0.002, 0.0016, 0.0028)
for i, hr in enumerate((0.014, 0.025)): rim(CO, f'Rim_CouterRing{i}', np.linspace(-PI, PI, 110), lambda u, a=hr: a, 0.0011, 0.0011)
q = np.linspace(-PI, PI, 110); inlay(CO, 'Inlay_CouterRing', q, np.full_like(q, 0.020), 0.0005, 0.0012)
rivet('Boss_Couter', CO.at(0.0, 0.0405, 0.0), np.array([0.0, 1.0, 0.0]), 0.0055, M_STEEL, C_TRIM)
use(UP)
fan_b = lambda u: -0.032 + 0.030 * ((u - 2.10) / 0.55) ** 2; fan_t = lambda u: 0.044 - 0.010 * ((u - 2.10) / 0.55) ** 2
steel('Wing', 1.55, 2.65, fan_b, fan_t, 0.0098, 22, 16, thick=0.0018)
rim(UP, 'Rim_Wing', np.linspace(1.55, 2.65, 40), fan_b, 0.0110, 0.0017)
for k in range(5): inlay(UP, f'Inlay_WingRib{k}', np.full(20, 1.65 + 0.225 * k), np.linspace(fan_b(1.65 + 0.225 * k) + 0.006, 0.034, 20), 0.0098, 0.0010)
# ---- lames above the couter (round the back and outer side)
for i, (h0, h1, off) in enumerate(((0.040, 0.064, 0.0072), (0.058, 0.084, 0.0084))):
    steel(f'Lame{i}', PI - 2.1, PI + 2.1, lambda u, a=h0: a, lambda u, a=h1: a, off, 48, 8, thick=0.0018)
    rim(UP, f'Rim_Lame{i}', np.linspace(PI - 2.1, PI + 2.1, 80), lambda u, a=h1: a, off + 0.0010, 0.0017)
    for s in (-1, 1): rivet(f'Rivet_Lame{i}{s}', UP.at(PI + s * 1.95, 0.5 * (h0 + h1), off + 0.0018), UP.surf_n(PI + s * 1.95, 0.5 * (h0 + h1)), 0.0020, M_STEEL, C_TRIM)
# ---- rerebrace: outer shell (centred on the outside) over the inner shell
UO, UI = 1.90, 1.40; CO_, CI_ = PI / 2, -PI / 2
o_b = lambda u: 0.078; o_t = lambda u: 0.215 - 0.035 * ((u - CO_) / UO) ** 2         # highest under the pauldron (outer side)
i_b = lambda u: 0.082; i_t = lambda u: 0.165
OFF_O, OFF_I = 0.0090, 0.0068
steel('RereOuter', CO_ - UO, CO_ + UO, o_b, o_t, OFF_O, 56, 40)
steel('RereInner', CI_ - UI, CI_ + UI, i_b, i_t, OFF_I, 44, 30)
uo = np.linspace(CO_ - UO, CO_ + UO, 110); ui = np.linspace(CI_ - UI, CI_ + UI, 90)
rim(UP, 'Rim_OuterTop', uo, o_t, OFF_O + 0.0016, 0.0027); rim(UP, 'Rim_OuterBottom', uo, o_b, OFF_O + 0.0013, 0.0021)
rim(UP, 'Rim_InnerTop', ui, i_t, OFF_I + 0.0016, 0.0025); rim(UP, 'Rim_InnerBottom', ui, i_b, OFF_I + 0.0012, 0.0019)
for s in (-1, 1): side_rim(UP, f'Rim_OuterSide{s}', CO_ + s * UO, o_b(0), o_t(CO_ + s * UO), OFF_O + 0.0010, 0.0015)
hz = np.linspace(o_b(CO_) + 0.010, o_t(CO_) - 0.012, 70)
tube('Ridge', UP.at(np.full_like(hz, CO_), hz, OFF_O + 0.0006), 0.0029, M_STEEL, C_TRIM, 10 * r, flat=0.45, up=UP.surf_n(np.full_like(hz, CO_), hz))
rim(UP, 'Lining_Top', uo, lambda u: o_t(u) - 0.0035, OFF_O - 0.0028, 0.0030, m=M_LEATHER)
# hinges at the back overlap, strap + buckle at the front overlap
UHB, UHF = 0.5 * ((CO_ + UO) + (CI_ - UI + 2 * PI)), 0.5 * ((CO_ - UO) + (CI_ + UI))
for k, hm in enumerate((0.110, 0.150)):
    hz = np.linspace(hm - 0.013, hm + 0.013, 10)
    tube(f'Hinge{k}', UP.at(np.full_like(hz, UHB), hz, OFF_O + 0.0030), 0.0028, M_STEEL, C_TRIM, 12 * r, up=UP.surf_n(np.full_like(hz, UHB), hz))
    us_s = np.linspace(UHF - 0.32, UHF + 0.24, 26 * r)
    P = UP.surf(us_s, np.full_like(us_s, hm)) + UP.surf_n(us_s, np.full_like(us_s, hm)) * (OFF_O + 0.0024)
    ribbon(f'Strap{k}', P, UP.surf_n(us_s, np.full_like(us_s, hm)), 0.012, M_LEATHER, C_STRAPS, thick=0.0020)
    buckle(UP, f'S{k}', UHF + 0.18, hm, OFF_O + 0.0046)
    rivet(f'Rivet_Strap{k}', UP.at(UHF - 0.28, hm, OFF_I + 0.0044), UP.surf_n(UHF - 0.28, hm), 0.0021, M_STEEL, C_TRIM)
# gold + etch
us = np.linspace(CO_ - UO + 0.10, CO_ + UO - 0.10, 150 * r)
inlay(UP, 'Inlay_OuterTop', us, [o_t(u) - 0.0105 for u in us], OFF_O)
inlay(UP, 'Etch_OuterTop', us, [o_t(u) - 0.0125 for u in us], OFF_O, 0.0024, M_ETCH)
inlay(UP, 'Inlay_OuterTop2', us, [o_t(u) - 0.0145 for u in us], OFF_O, 0.0009)
inlay(UP, 'Inlay_OuterBottom', us, [o_b(u) + 0.0095 for u in us], OFF_O)
inlay(UP, 'Inlay_OuterBottom2', us, [o_b(u) + 0.0135 for u in us], OFF_O, 0.0009)
lozenge(UP, 'Inlay_ArmLozenge', CO_, 0.150, OFF_O + 0.0030, 0.0070, 0.0120)
laurel(UP, 'Arm', CO_, 0.133, OFF_O + 0.0002)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, f'upperarm_build_r{RES}.blend'))
print('BUILD OK', len(bpy.data.objects), 'objects', sum(len(o.data.polygons) for o in bpy.data.objects if o.type == 'MESH'), 'faces (pre-mod)')
