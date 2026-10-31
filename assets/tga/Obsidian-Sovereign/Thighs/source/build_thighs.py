# Build the layered left cuisse (thigh defence) + poleyn (knee cop) and save thigh_build_r<RES>.blend. TGA (Claude), 2026-10-31.
# CHEST_RES=1|3 blender -b --factory-startup -P build_thighs.py
# checkking's Obsidian Sovereign vocabulary: a domed knee cop with a fan wing on the outer side, two articulation lames, the
# main cuisse plate over the front and sides (raised keel, rolled rims, gold inlay + etch borders, lozenge and laurel over
# the knee), open at the back and held by two leather straps with buckles; leather lining at the top edge.
# Frame: the Codex set's world frame (metres, Z up, front = -Y). Left leg on +X. The knee sits on top of checkking's greave
# (top z ~0.545, greave axis x 0.135 y 0.030); the cuisse top stops under the Codex fauld / tassets (z ~0.88).
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
def lozenge(ax, name, h, off, half_w, half_h, w=0.0013):
    q = np.linspace(0, 2 * PI, 60 * r); RC = float(ax.r(h) * ax.k(h))
    inlay(ax, name, (half_w * np.sign(np.sin(q)) * np.abs(np.sin(q)) ** 1.6) / RC, h + half_h * np.cos(q), off, w)
def laurel(ax, tag, hc, off, length=0.026, up=1.0):
    RC = float(ax.r(hc) * ax.k(hc))
    for side in (-1, 1):
        t = np.linspace(0, 1, 50 * r)
        sx, sh = side * (0.009 + length * t), hc + up * 0.028 * t ** 1.3
        inlay(ax, f'Laurel_Stem_{tag}{side}', sx / RC, sh, off, 0.0011)
        for k, tk in enumerate((0.3, 0.55, 0.8)):
            a = np.linspace(0, 2 * PI, 24 * r); cx, ch = side * (0.009 + length * tk), hc + up * 0.028 * tk ** 1.3
            L, Wd = 0.0090, 0.0034; ang = 0.9 if k % 2 else -0.4
            lx = cx + side * (L / 2) * (1 - np.cos(a)) * math.cos(ang) - (Wd / 2) * np.sin(a) * math.sin(ang)
            lh = ch + (L / 2) * (1 - np.cos(a)) * math.sin(ang) + (Wd / 2) * np.sin(a) * math.cos(ang)
            inlay(ax, f'Laurel_Leaf_{tag}{side}_{k}', lx / RC, lh, off, 0.0009)
def buckle(ax, tag, u, h, off):
    c = ax.at(u, h, off); n = ax.surf_n(u, h)
    t = -ax.D.copy(); t -= (t @ n) * n; t /= np.linalg.norm(t); b = np.cross(n, t)
    rect = [c + t * 0.0110 + b * 0.0080, c + t * 0.0110 - b * 0.0080, c - t * 0.0110 - b * 0.0080, c - t * 0.0110 + b * 0.0080]
    pts = np.vstack([np.linspace(rect[i], rect[(i + 1) % 4], 8, endpoint=False) for i in range(4)])
    tube(f'Buckle_{tag}', pts, 0.0016, M_BUCKLE, C_TRIM, 8 * r, closed=True, up=np.tile(n, (len(pts), 1)))
    tube(f'Buckle_{tag}_Tongue', np.linspace(c - b * 0.0080, c + b * 0.0060 + n * 0.0012, 10), 0.0011, M_BUCKLE, C_TRIM, 6 * r, up=np.tile(t, (10, 1)))

# ---------------- thigh surface: knee K -> hip H axis, u = 0 front (-Y), +pi/2 outer (+X)
K = np.array([0.135, 0.022, 0.548]); H = np.array([0.116, 0.000, 0.905])
T_H = [0.000, 0.060, 0.130, 0.200, 0.270, 0.330, 0.370]
T_D = [0.0560, 0.0620, 0.0690, 0.0750, 0.0800, 0.0830, 0.0845]    # half depth (front-back)
T_W = [0.0560, 0.0610, 0.0680, 0.0750, 0.0810, 0.0850, 0.0870]    # half width
THIGH = Axial(K, K - H, (0, -1, 0), T_H, T_D, [w / d for w, d in zip(T_W, T_D)])

# ---- poleyn: a dome on an axis pointing forward out of the knee (u = 0 up the leg, +pi/2 outer side)
KNEE = Axial(K + np.array([0.0, -0.044, 0.004]), (0, 1, 0), (0, 0, 1), [0.000, 0.012, 0.024, 0.034, 0.041, 0.045],
             [0.0560, 0.0535, 0.0465, 0.0360, 0.0220, 0.0012], [1.05, 1.05, 1.04, 1.03, 1.02, 1.0])
use(KNEE)
steel('Poleyn', -PI, PI, lambda u: 0.0, lambda u: 0.0445, 0.0, 64, 22)
rim(KNEE, 'Rim_Poleyn', np.linspace(-PI, PI, 120), lambda u: 0.002, 0.0016, 0.0030)
for i, hr in enumerate((0.016, 0.028)):                                    # two raised rings on the dome
    rim(KNEE, f'Rim_PoleynRing{i}', np.linspace(-PI, PI, 120), lambda u, a=hr: a, 0.0012, 0.0012)
q = np.linspace(-PI, PI, 120); inlay(KNEE, 'Inlay_PoleynRing', q, np.full_like(q, 0.022), 0.0006, 0.0012)
rivet('Rivet_PoleynTop', KNEE.at(0.0, 0.006, 0.0018), KNEE.surf_n(0.0, 0.006), 0.0026, M_STEEL, C_TRIM)
rivet('Boss_Poleyn', KNEE.at(0.0, 0.0445, 0.0), np.array([0.0, -1.0, 0.0]), 0.0060, M_STEEL, C_TRIM)                  # boss closing the dome's tip
# fan wing on the outer side (+X) and the lames above the cop, on the thigh axis
use(THIGH)
fan_b = lambda u: -0.034 + 0.034 * ((u - 1.50) / 0.50) ** 2; fan_t = lambda u: 0.046 - 0.010 * ((u - 1.50) / 0.50) ** 2
steel('Wing', 1.00, 2.00, fan_b, fan_t, 0.0105, 22, 16, thick=0.0018)
rim(THIGH, 'Rim_Wing', np.linspace(1.00, 2.00, 40), fan_b, 0.0118, 0.0018)
for k in range(5): inlay(THIGH, f'Inlay_WingRib{k}', np.full(20, 1.10 + 0.20 * k), np.linspace(fan_b(1.10 + 0.20 * k) + 0.006, 0.036, 20), 0.0105, 0.0010)
for i, (h0, h1, off) in enumerate(((0.040, 0.066, 0.0074), (0.060, 0.088, 0.0086))):
    steel(f'Lame{i}', -1.75, 1.75, lambda u, a=h0: a, lambda u, a=h1: a, off, 48, 8, thick=0.0018)
    rim(THIGH, f'Rim_Lame{i}', np.linspace(-1.75, 1.75, 80), lambda u, a=h1: a, off + 0.0010, 0.0018)
    for s in (-1, 1): rivet(f'Rivet_Lame{i}{s}', THIGH.at(s * 1.6, 0.5 * (h0 + h1), off + 0.0018), THIGH.surf_n(s * 1.6, 0.5 * (h0 + h1)), 0.0022, M_STEEL, C_TRIM)
# ---- cuisse: front + sides, open at the back
UC = 2.05
c_b = lambda u: 0.082
c_t = lambda u: 0.335 - 0.022 * (1 - math.cos(u)) / 2 + 0.010 * max(math.sin(u), 0.0)   # a little higher on the outer hip
OFF_C = 0.0098
steel('Cuisse', -UC, UC, c_b, c_t, OFF_C, 60, 52)
uc = np.linspace(-UC, UC, 120)
rim(THIGH, 'Rim_CuisseTop', uc, c_t, OFF_C + 0.0016, 0.0032)
rim(THIGH, 'Rim_CuisseBottom', uc, c_b, OFF_C + 0.0013, 0.0024)
for s in (-1, 1): side_rim(THIGH, f'Rim_CuisseSide{s}', s * UC, c_b(UC), c_t(s * UC), OFF_C + 0.0010, 0.0017)
hz = np.linspace(c_b(0) + 0.012, c_t(0) - 0.014, 90)
tube('Ridge', THIGH.at(np.zeros_like(hz), hz, OFF_C + 0.0006), 0.0036, M_STEEL, C_TRIM, 10 * r, flat=0.45, up=THIGH.surf_n(np.zeros_like(hz), hz))
rim(THIGH, 'Lining_Top', np.linspace(-UC, UC, 120), lambda u: c_t(u) - 0.004, OFF_C - 0.0030, 0.0034, m=M_LEATHER)
# straps round the open back, buckled on the back-outer side
for k, hm in enumerate((0.165, 0.270)):
    us_s = np.linspace(-UC + 0.12, UC + 0.55, 46 * r)                        # from the inner edge round the back to the outer side
    us_w = np.where(us_s > PI, us_s - 2 * PI, us_s)
    hh = np.full_like(us_s, hm)
    on_plate = np.abs(us_w) < UC
    offs = np.where(on_plate, OFF_C + 0.0026, 0.0028)
    P = THIGH.surf(us_s, hh) + THIGH.surf_n(us_s, hh) * offs[:, None]
    ribbon(f'Strap{k}', P, THIGH.surf_n(us_s, hh), 0.017, M_LEATHER, C_STRAPS, thick=0.0024)
    buckle(THIGH, f'S{k}', UC - 0.18, hm, OFF_C + 0.0052)
    rivet(f'Rivet_Strap{k}', THIGH.at(-UC + 0.18, hm, OFF_C + 0.0052), THIGH.surf_n(-UC + 0.18, hm), 0.0026, M_STEEL, C_TRIM)
# gold + etch: borders, lozenge + laurel over the knee, ridge lines
us = np.linspace(-(UC - 0.12), UC - 0.12, 170 * r)
inlay(THIGH, 'Inlay_CuisseTop', us, [c_t(u) - 0.0130 for u in us], OFF_C)
inlay(THIGH, 'Inlay_CuisseTop2', us, [c_t(u) - 0.0175 for u in us], OFF_C, 0.0009)
inlay(THIGH, 'Etch_CuisseTop', us, [c_t(u) - 0.0152 for u in us], OFF_C, 0.0028, M_ETCH)
inlay(THIGH, 'Inlay_CuisseBottom', us, [c_b(u) + 0.0110 for u in us], OFF_C)
inlay(THIGH, 'Inlay_CuisseBottom2', us, [c_b(u) + 0.0150 for u in us], OFF_C, 0.0009)
inlay(THIGH, 'Etch_CuisseBottom', us, [c_b(u) + 0.0130 for u in us], OFF_C, 0.0028, M_ETCH)
lozenge(THIGH, 'Inlay_KneeLozenge', 0.128, OFF_C + 0.0036, 0.0095, 0.0170)
laurel(THIGH, 'Knee', 0.112, OFF_C + 0.0002)
for s in (-1, 1):
    hz = np.linspace(0.165, c_t(0) - 0.026, 120 * r)
    RC = float(THIGH.r(0.25) * THIGH.k(0.25))
    inlay(THIGH, f'Inlay_Ridge{s}', np.full_like(hz, s * 0.0095 / RC), hz, OFF_C, 0.0009)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, f'thigh_build_r{RES}.blend'))
print('BUILD OK', len(bpy.data.objects), 'objects', sum(len(o.data.polygons) for o in bpy.data.objects if o.type == 'MESH'), 'faces (pre-mod)')
