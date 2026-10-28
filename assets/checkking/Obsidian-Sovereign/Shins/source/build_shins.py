# Build the layered left greave (high or low density) and save shin_build_r<RES>.blend.
# CHEST_RES=1|3 blender -b --factory-startup -P build_shins.py
# Frame: the Codex set's world frame (metres, Z up, front = -Y). Left leg on +X. The greave's bottom flares over the
# top band of the checkking boot (same leg axis x 0.135), its top sits just under the knee (Codex thighs start at 0.541).
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
C_PLATES, C_TRIM, C_STRAPS, C_INLAY = coll('Plates'), coll('Trim'), coll('Straps'), coll('Inlay')
RES = int(os.environ.get('CHEST_RES', '1')); r = RES
PI = math.pi

def steel(name, u0, u1, hb, ht, off, nu, nv, thick=0.0022):
    ob = patch(name, u0, u1, hb, ht, off, nu * r, nv * r, M_STEEL, C_PLATES, thick=thick)
    ob.vertex_groups.new(name='inner'); ob.modifiers['Solidify'].shell_vertex_group = 'inner'
    return ob
def rim(name, us, hf, off, rad, seg=8, m=None):
    us = np.asarray(us); hh = np.array([hf(u) for u in us])
    tube(name, LEG.at(us, hh, off), rad, m or M_STEEL, C_TRIM, seg * r, up=LEG.surf_n(us, hh))
def side_rim(name, u, h0, h1, off, rad):
    hh = np.linspace(h0, h1, 40); uu = np.full_like(hh, u)
    tube(name, LEG.at(uu, hh, off), rad, M_STEEL, C_TRIM, 6 * r, up=LEG.surf_n(uu, hh))
def inlay(name, us, hs, off, w=0.0013, m=None):
    us = np.asarray(us); hs = np.asarray(hs)
    ribbon(name, LEG.at(us, hs, off + 0.00012), LEG.surf_n(us, hs), w, m or M_GOLD, C_INLAY, thick=0.0001 if m else 0.0004)
def lozenge(name, h, off, half_w, half_h, w=0.0013):
    q = np.linspace(0, 2 * PI, 60 * r); RC = float(LEG.r(h) * LEG.k(h))
    inlay(name, (half_w * np.sign(np.sin(q)) * np.abs(np.sin(q)) ** 1.6) / RC, h + half_h * np.cos(q), off, w)
def laurel(tag, hc, off, length=0.024):
    RC = float(LEG.r(hc) * LEG.k(hc))
    for side in (-1, 1):
        t = np.linspace(0, 1, 50 * r)
        sx, sh = side * (0.008 + length * t), hc - 0.026 * t ** 1.3
        inlay(f'Laurel_Stem_{tag}{side}', sx / RC, sh, off, 0.0011)
        for k, tk in enumerate((0.3, 0.55, 0.8)):
            a = np.linspace(0, 2 * PI, 24 * r); cx, ch = side * (0.008 + length * tk), hc - 0.026 * tk ** 1.3
            L, Wd = 0.0085, 0.0032; ang = -0.9 if k % 2 else 0.4
            lx = cx + side * (L / 2) * (1 - np.cos(a)) * math.cos(ang) - (Wd / 2) * np.sin(a) * math.sin(ang)
            lh = ch + (L / 2) * (1 - np.cos(a)) * math.sin(ang) + (Wd / 2) * np.sin(a) * math.cos(ang)
            inlay(f'Laurel_Leaf_{tag}{side}_{k}', lx / RC, lh, off, 0.0009)
def buckle(tag, u, h, off):
    c = LEG.at(u, h, off); n = LEG.surf_n(u, h)
    t = np.array([0.0, 0.0, 1.0]); t -= (t @ n) * n; t /= np.linalg.norm(t); b = np.cross(n, t)
    rect = [c + t * 0.0105 + b * 0.0075, c + t * 0.0105 - b * 0.0075, c - t * 0.0105 - b * 0.0075, c - t * 0.0105 + b * 0.0075]
    pts = np.vstack([np.linspace(rect[i], rect[(i + 1) % 4], 8, endpoint=False) for i in range(4)])
    tube(f'Buckle_{tag}', pts, 0.0015, M_BUCKLE, C_TRIM, 8 * r, closed=True, up=np.tile(n, (len(pts), 1)))
    tube(f'Buckle_{tag}_Tongue', np.linspace(c - b * 0.0075, c + b * 0.0055 + n * 0.0011, 10), 0.0010, M_BUCKLE, C_TRIM, 6 * r, up=np.tile(t, (10, 1)))

# ---------------- leg surface: vertical surface of revolution on the boot's leg axis, u = 0 front (-Y), +pi/2 outer (+X) ----------------
X0, Y0, ZT = 0.135, 0.030, 0.545
L_Z = [0.205, 0.235, 0.270, 0.320, 0.370, 0.420, 0.470, 0.510, 0.545]
L_D = [0.068, 0.065, 0.056, 0.060, 0.067, 0.066, 0.060, 0.055, 0.058]   # half depth (front-back), calf at 0.37-0.42
L_W = [0.062, 0.059, 0.051, 0.055, 0.061, 0.060, 0.055, 0.051, 0.055]   # half width
LEG = Axial((X0, Y0, ZT), (0, 0, -1), (0, -1, 0), [z - ZT for z in L_Z], L_D, [w / d for w, d in zip(L_W, L_D)])
use(LEG)

# front shell (outside) over the back shell (calf); they overlap at both sides
UF, UBK = 1.85, 1.45
f_b = lambda u: -0.338 + 0.010 * max(math.cos(u), 0.0) ** 2               # bottom rises a little over the instep
f_t = lambda u: -0.004 + 0.012 * max(math.cos(u), 0.0) ** 4               # top peaks under the knee cop
b_b = lambda u: -0.342
b_t = lambda u: -0.024                                                     # lower at the back for the knee bend
OFF_F, OFF_B = 0.0068, 0.0046
steel('GreaveFront', -UF, UF, f_b, f_t, OFF_F, 60, 44)
steel('GreaveBack', PI - UBK, PI + UBK, b_b, b_t, OFF_B, 48, 40)
uf = np.linspace(-UF, UF, 120); ub = np.linspace(PI - UBK, PI + UBK, 100)
rim('Rim_FrontTop', uf, f_t, OFF_F + 0.0016, 0.0030)
rim('Rim_FrontBottom', uf, f_b, OFF_F + 0.0013, 0.0024)
rim('Rim_BackTop', ub, b_t, OFF_B + 0.0016, 0.0028)
rim('Rim_BackBottom', ub, b_b, OFF_B + 0.0012, 0.0022)
for s in (-1, 1):
    side_rim(f'Rim_FrontSide{s}', s * UF, f_b(UF), f_t(UF), OFF_F + 0.0010, 0.0016)
# medial ridge down the front (keel) and the leather lining roll showing at the top edge
hz = np.linspace(f_b(0) + 0.010, f_t(0) - 0.012, 80)
tube('Ridge', LEG.at(np.zeros_like(hz), hz, OFF_F + 0.0006), 0.0034, M_STEEL, C_TRIM, 10 * r, flat=0.45, up=LEG.surf_n(np.zeros_like(hz), hz))
rim('Lining_Top', np.linspace(-PI, PI, 140), lambda u: (f_t(u) if abs(u) < UF else b_t(u)) - 0.004, 0.0018, 0.0034, m=M_LEATHER)

# hinges on the outer side (+X) across the front/back overlap, strap + buckle on the inner side (-X)
UH = 0.5 * (UF + (PI - UBK))
for k, hm in enumerate((-0.250, -0.110)):
    hz = np.linspace(hm - 0.020, hm + 0.020, 12)
    tube(f'Hinge{k}', LEG.at(np.full_like(hz, UH), hz, OFF_F + 0.0036), 0.0034, M_STEEL, C_TRIM, 12 * r, up=LEG.surf_n(np.full_like(hz, UH), hz))
    for s in (-1, 1):
        uu = UH + s * 0.11
        steel(f'HingeLeaf{k}{s}', min(UH, uu), max(UH, uu), lambda u, a=hm: a - 0.016, lambda u, a=hm: a + 0.016, OFF_F + 0.0016 if s < 0 else OFF_B + 0.0024, 6, 6, thick=0.0012)
        rivet(f'Rivet_Hinge{k}{s}', LEG.at(UH + s * 0.08, hm, OFF_F + 0.0030 if s < 0 else OFF_B + 0.0038), LEG.surf_n(UH + s * 0.08, hm), 0.0022, M_STEEL, C_TRIM)
    # inner strap: riveted to the back shell, crosses the seam, buckles on the front shell
    us_s = np.linspace(-UH - 0.32, -UH + 0.22, 30 * r)
    offs = np.where(us_s > -UF, OFF_F + 0.0026, OFF_B + 0.0026)
    P = LEG.surf(us_s, np.full_like(us_s, hm)) + LEG.surf_n(us_s, np.full_like(us_s, hm)) * offs[:, None]
    ribbon(f'Strap{k}', P, LEG.surf_n(us_s, np.full_like(us_s, hm)), 0.015, M_LEATHER, C_STRAPS, thick=0.0022)
    buckle(f'S{k}', -UH + 0.27, hm, OFF_F + 0.0052)
    rivet(f'Rivet_Strap{k}', LEG.at(-UH - 0.28, hm, OFF_B + 0.0050), LEG.surf_n(-UH - 0.28, hm), 0.0024, M_STEEL, C_TRIM)

# gold + etch (set vocabulary): borders under the top and above the bottom, lozenge + laurel under the knee, ridge line
us = np.linspace(-(UF - 0.10), UF - 0.10, 160 * r)
inlay('Inlay_FrontTop', us, [f_t(u) - 0.0120 for u in us], OFF_F)
inlay('Inlay_FrontTop2', us, [f_t(u) - 0.0160 for u in us], OFF_F, 0.0009)
inlay('Etch_FrontTop', us, [f_t(u) - 0.0140 for u in us], OFF_F, 0.0026, M_ETCH)
inlay('Inlay_FrontBottom', us, [f_b(u) + 0.0110 for u in us], OFF_F)
inlay('Inlay_FrontBottom2', us, [f_b(u) + 0.0150 for u in us], OFF_F, 0.0009)
inlay('Etch_FrontBottom', us, [f_b(u) + 0.0130 for u in us], OFF_F, 0.0026, M_ETCH)
ubk = np.linspace(PI - UBK + 0.10, PI + UBK - 0.10, 120 * r)
inlay('Inlay_BackTop', ubk, [b_t(u) - 0.0110 for u in ubk], OFF_B)
inlay('Inlay_BackBottom', ubk, [b_b(u) + 0.0100 for u in ubk], OFF_B)
lozenge('Inlay_KneeLozenge', -0.058, OFF_F + 0.0034, 0.0085, 0.0150)
laurel('Knee', -0.078, OFF_F + 0.0002)
for s in (-1, 1):   # fine gold lines either side of the ridge
    hz = np.linspace(f_b(0) + 0.024, -0.095, 120 * r)
    RC = float(LEG.r(-0.2) * LEG.k(-0.2))
    inlay(f'Inlay_Ridge{s}', np.full_like(hz, s * 0.0085 / RC), hz, OFF_F, 0.0009)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, f'shin_build_r{RES}.blend'))
print('BUILD OK', len(bpy.data.objects), 'objects', sum(len(o.data.polygons) for o in bpy.data.objects if o.type == 'MESH'), 'faces (pre-mod)')
