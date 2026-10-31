# Build the fauld (hoop lames round the hips) + two tassets and save waist_build_r<RES>.blend. TGA (Claude), 2026-10-31.
# CHEST_RES=1|3 blender -b --factory-startup -P build_waist.py
# checkking's Obsidian Sovereign vocabulary: four steel lames lapping downward from under the cuirass's bottom edge, each
# with a rolled lower edge and a gold line, sliding rivets at the sides, hinges on the left side and strap + buckle closure on
# the right, a leather lining roll under the cuirass; two tassets (three lames each, cusped lower edges, gold lozenge on the
# top lame) hang on leather straps over the front of each thigh. One centred piece (not L / R).
# Frame: the Codex set's world frame (metres, Z up, front = -Y). The cuirass (checkking chest) ends at z 0.964 with its flare
# at x +-0.18; the TGA cuisses' tops sit at z ~0.88, under the tassets.
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
def rim(name, us, hf, off, rad, seg=8, m=None):
    us = np.asarray(us); hh = np.array([hf(u) for u in us])
    tube(name, HIP.at(us, hh, off), rad, m or M_STEEL, C_TRIM, seg * r, up=HIP.surf_n(us, hh))
def inlay(name, us, hs, off, w=0.0013, m=None):
    us = np.asarray(us); hs = np.asarray(hs)
    ribbon(name, HIP.at(us, hs, off + 0.00012), HIP.surf_n(us, hs), w, m or M_GOLD, C_INLAY, thick=0.0001 if m else 0.0004)
def lozenge(name, u, h, off, half_w, half_h, w=0.0013):
    q = np.linspace(0, 2 * PI, 60 * r); RC = float(HIP.r(h) * HIP.k(h))
    inlay(name, u + (half_w * np.sign(np.sin(q)) * np.abs(np.sin(q)) ** 1.6) / RC, h + half_h * np.cos(q), off, w)
def laurel(tag, uc, hc, off, length=0.030):
    RC = float(HIP.r(hc) * HIP.k(hc))
    for side in (-1, 1):
        t = np.linspace(0, 1, 50 * r)
        sx, sh = side * (0.010 + length * t), hc - 0.010 * t ** 1.3
        inlay(f'Laurel_Stem_{tag}{side}', uc + sx / RC, sh, off, 0.0011)
        for k, tk in enumerate((0.3, 0.55, 0.8)):
            a = np.linspace(0, 2 * PI, 24 * r); cx, ch = side * (0.010 + length * tk), hc - 0.010 * tk ** 1.3
            L, Wd = 0.0090, 0.0034; ang = -0.5 if k % 2 else 0.5
            lx = cx + side * (L / 2) * (1 - np.cos(a)) * math.cos(ang) - (Wd / 2) * np.sin(a) * math.sin(ang)
            lh = ch + (L / 2) * (1 - np.cos(a)) * math.sin(ang) + (Wd / 2) * np.sin(a) * math.cos(ang)
            inlay(f'Laurel_Leaf_{tag}{side}_{k}', uc + lx / RC, lh, off, 0.0009)
def buckle(tag, u, h, off, vertical=False):
    c = HIP.at(u, h, off); n = HIP.surf_n(u, h)
    t = np.array([0.0, 0.0, 1.0]); t -= (t @ n) * n; t /= np.linalg.norm(t); b = np.cross(n, t)
    if vertical: t, b = b, t
    rect = [c + t * 0.0110 + b * 0.0080, c + t * 0.0110 - b * 0.0080, c - t * 0.0110 - b * 0.0080, c - t * 0.0110 + b * 0.0080]
    pts = np.vstack([np.linspace(rect[i], rect[(i + 1) % 4], 8, endpoint=False) for i in range(4)])
    tube(f'Buckle_{tag}', pts, 0.0016, M_BUCKLE, C_TRIM, 8 * r, closed=True, up=np.tile(n, (len(pts), 1)))
    tube(f'Buckle_{tag}_Tongue', np.linspace(c - b * 0.0080, c + b * 0.0060 + n * 0.0012, 10), 0.0011, M_BUCKLE, C_TRIM, 6 * r, up=np.tile(t, (10, 1)))

# ---------------- hip surface: vertical axis through the body; h up from z 0.62; u = 0 front (-Y), +pi/2 the body's left (+X)
H_H = [0.000, 0.060, 0.120, 0.180, 0.230, 0.280, 0.330, 0.380]
H_W = [0.210, 0.205, 0.198, 0.190, 0.181, 0.172, 0.164, 0.158]      # half width (flaring out toward the bottom)
H_D = [0.148, 0.145, 0.140, 0.134, 0.128, 0.122, 0.117, 0.113]      # half depth
HIP = Axial((0.0, -0.008, 0.620), (0, 0, -1), (0, -1, 0), H_H, H_D, [w / d for w, d in zip(H_W, H_D)])
use(HIP)

# ---- fauld: 4 hoop lames, upper over lower; the front centre of each lower edge dips a little
NL = 4
def lame_b(i): return lambda u, i=i: 0.362 - 0.036 * i - 0.048 - 0.006 * max(math.cos(u), 0.0) ** 3
def lame_t(i): return lambda u, i=i: 0.362 - 0.036 * i
for i in range(NL):
    off = 0.0118 - 0.0018 * i
    steel(f'Fauld{i}', -PI, PI, lame_b(i), lame_t(i), off, 96, 10)
    rim(f'Rim_Fauld{i}', np.linspace(-PI, PI, 200), lame_b(i), off + 0.0012, 0.0021)
    uu = np.linspace(-PI, PI, 260 * r)
    inlay(f'Inlay_Fauld{i}', uu, [lame_b(i)(u) + 0.0085 for u in uu], off)
    for k in range(10):                                                         # sliding rivets
        u = -PI + (k + 0.5) * 2 * PI / 10
        rivet(f'Rivet_Fauld{i}_{k}', HIP.at(u, lame_t(i)(u) - 0.011, off + 0.0018), HIP.surf_n(u, lame_t(i)(u) - 0.011), 0.0020, M_STEEL, C_TRIM)
inlay('Etch_Fauld0', np.linspace(-PI, PI, 260 * r), np.full(260 * r, 0.362 - 0.012), 0.0118, 0.0030, M_ETCH)
rim('Lining_Top', np.linspace(-PI, PI, 200), lambda u: 0.362 - 0.003, 0.0070, 0.0034, m=M_LEATHER)
laurel('Front', 0.0, 0.362 - 0.020, 0.0118 + 0.0002)
# closure: hinges on the left (+X), strap + buckle on the right (-X), across the four lames
for k, hm in enumerate((0.325, 0.253)):
    hz = np.linspace(hm - 0.014, hm + 0.014, 10)
    tube(f'Hinge{k}', HIP.at(np.full_like(hz, PI / 2), hz, 0.0155), 0.0030, M_STEEL, C_TRIM, 12 * r, up=HIP.surf_n(np.full_like(hz, PI / 2), hz))
    hs = np.linspace(hm + 0.030, hm - 0.030, 20 * r)
    ribbon(f'Strap_Side{k}', HIP.surf(np.full_like(hs, -PI / 2), hs) + HIP.surf_n(np.full_like(hs, -PI / 2), hs) * 0.0150, HIP.surf_n(np.full_like(hs, -PI / 2), hs), 0.016, M_LEATHER, C_STRAPS, thick=0.0022)
    buckle(f'Side{k}', -PI / 2, hm - 0.012, 0.0175)

# ---- tassets: three lames each over the front of each thigh, hung from the lowest fauld lame on two straps
TOP = 0.362 - 0.036 * (NL - 1) - 0.040
for side in (-1, 1):
    uc = side * 0.62; hw = 0.50
    for j in range(3):
        tb = TOP - 0.050 * j
        cusp = lambda u, tb=tb: tb - 0.062 - 0.012 * math.cos(min(abs(u - uc) / hw, 1.0) * PI / 2)
        off = 0.0128 - 0.0010 * j
        steel(f'Tasset{side}_{j}', uc - hw, uc + hw, cusp, lambda u, tb=tb: tb, off, 40, 10)
        rim(f'Rim_Tasset{side}_{j}', np.linspace(uc - hw, uc + hw, 80), cusp, off + 0.0012, 0.0021)
        uu = np.linspace(uc - hw + 0.04, uc + hw - 0.04, 120 * r)
        inlay(f'Inlay_Tasset{side}_{j}', uu, [cusp(u) + 0.0085 for u in uu], off)
        for s in (-1, 1):
            rivet(f'Rivet_Tasset{side}_{j}{s}', HIP.at(uc + s * (hw - 0.07), tb - 0.010, off + 0.0018), HIP.surf_n(uc + s * (hw - 0.07), tb - 0.010), 0.0020, M_STEEL, C_TRIM)
        if j == 0: lozenge(f'Inlay_TassetLozenge{side}', uc, tb - 0.036, off + 0.0010, 0.0085, 0.0150)
    for s in (-1, 1):                                                          # hanging straps + buckles
        hs = np.linspace(TOP + 0.034, TOP - 0.020, 16 * r); us_ = np.full_like(hs, uc + s * 0.24)
        ribbon(f'Strap_Tasset{side}{s}', HIP.surf(us_, hs) + HIP.surf_n(us_, hs) * 0.0150, HIP.surf_n(us_, hs), 0.015, M_LEATHER, C_STRAPS, thick=0.0022)
        buckle(f'Tasset{side}{s}', uc + s * 0.24, TOP + 0.008, 0.0175, vertical=True)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, f'waist_build_r{RES}.blend'))
print('BUILD OK', len(bpy.data.objects), 'objects', sum(len(o.data.polygons) for o in bpy.data.objects if o.type == 'MESH'), 'faces (pre-mod)')
