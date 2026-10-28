# Build the layered left gauntlet (high or low density) and save gauntlet_build_r<RES>.blend.
# CHEST_RES=1|3 blender -b --factory-startup -P build_gauntlets.py
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
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
C_PLATES, C_TRIM, C_GLOVE, C_INLAY = coll('Plates'), coll('Trim'), coll('Glove'), coll('Inlay')
RES = int(os.environ.get('CHEST_RES', '1')); r = RES
PI = math.pi

def steel(name, u0, u1, hb, ht, off, nu, nv, thick=0.0018):
    ob = patch(name, u0, u1, hb, ht, off, nu * r, nv * r, M_STEEL, C_PLATES, thick=thick)
    vg = ob.vertex_groups.new(name='inner'); ob.modifiers['Solidify'].shell_vertex_group = 'inner'   # inward shell -> lower texel density later
    return ob
def leather(name, ax, hb, ht, nu, nv):
    use(ax); return patch(name, -PI, PI, lambda u: hb, lambda u: ht, 0.0, nu * r, nv * r, M_LEATHER, C_GLOVE, thick=0)
def rim(name, ax, us, hf, off, rad, seg=8):
    use(ax); us = np.asarray(us); hh = np.array([hf(u) for u in us])
    tube(name, ax.at(us, hh, off), rad, M_STEEL, C_TRIM, seg * r, up=ax.surf_n(us, hh))
def inlay(name, ax, us, hs, off, w=0.0012, m=None):
    us = np.asarray(us); hs = np.asarray(hs)
    ribbon(name, ax.at(us, hs, off + 0.00012), ax.surf_n(us, hs), w, m or M_GOLD, C_INLAY, thick=0.0001 if m else 0.0004)

# ---------------- hand body (leather glove under the plates) ----------------
W = np.array([0.351, 0.0, 0.800])                      # wrist centre
H_HS = [0.030, 0.000, -0.025, -0.050, -0.075, -0.095, -0.106]
H_DEP = [0.0205, 0.0200, 0.0192, 0.0190, 0.0182, 0.0158, 0.0115]
H_WID = [0.0310, 0.0300, 0.0400, 0.0465, 0.0495, 0.0495, 0.0470]
HAND = Axial(W, (0, 0, -1), (0, -1, 0), H_HS[::-1], H_DEP[::-1], [w / d for w, d in zip(H_WID, H_DEP)][::-1])   # tables must ascend in h
leather('Glove_Hand', HAND, -0.104, 0.028, 40, 26)

# ---------------- plates on the back of the hand (upper plates outside the lower ones) ----------------
use(HAND)
UB = 1.32
def band(h0, h1, U=UB, dip=0.004):   # outline: edges curve slightly toward the wrist at the sides
    return (lambda u: h0 + dip * (u / U) ** 2), (lambda u: h1 + dip * (u / U) ** 2)
PLATES = [  # name, bottom, top, offset, rim radius
    ('Lame_Wrist1', -0.020, 0.003, 0.0092, 0.0015),
    ('Lame_Wrist2', -0.035, -0.014, 0.0078, 0.0015),
    ('Plate_Metacarpal', -0.083, -0.029, 0.0062, 0.0019),
    ('Plate_Knuckle', -0.101, -0.077, 0.0040, 0.0017),
]
for name, h0, h1, off, rr in PLATES:
    hb, ht = band(h0, h1)
    steel(name, -UB, UB, hb, ht, off, 34, 10 if 'Lame' in name else 20)
    rim('Rim_' + name, HAND, np.linspace(-UB, UB, 50), hb, off + 0.0012, rr)
hb, ht = band(-0.083, -0.029)
for s in (-1, 1):
    hh = np.linspace(hb(UB), ht(UB), 20)
    use(HAND); tube(f'Rim_MetaSide{s}', HAND.at(np.full_like(hh, s * UB), hh, 0.0062 + 0.0010), 0.0013, M_STEEL, C_TRIM, 6 * r, up=HAND.surf_n(np.full_like(hh, s * UB), hh))

# knuckle bosses (domed, one per finger) and plate rivets
FX = [0.313, 0.339, 0.365, 0.391]                      # finger centre lines (Codex layout), index .. little
HK = -0.0895
for i, x in enumerate(FX):
    u = HAND.u_for_x(HK, x - W[0])
    rivet(f'Boss{i}', HAND.at(u, HK, 0.0040 + 0.0012), HAND.surf_n(u, HK), 0.0056, M_STEEL, C_TRIM, seg=20)
riv = [(s * (UB - 0.12), (h0 + h1) / 2 + 0.004 * ((UB - 0.12) / UB) ** 2, off) for (_, h0, h1, off, _) in PLATES[:2] for s in (-1, 1)]
riv += [(s * (UB - 0.14), hm, 0.0062) for s in (-1, 1) for hm in (-0.036, -0.074)]
for i, (u, h, off) in enumerate(riv):
    rivet(f'Rivet{i}', HAND.at(u, h, off), HAND.surf_n(u, h), 0.0024, M_STEEL, C_TRIM)

# gold + etch on the metacarpal plate and lames (chest vocabulary)
us = np.linspace(-(UB - 0.10), UB - 0.10, 90 * r)
ht_m = lambda u: -0.029 + 0.004 * (u / UB) ** 2
inlay('Inlay_MetaTop', HAND, us, [ht_m(u) - 0.0065 for u in us], 0.0062)
inlay('Inlay_MetaTop2', HAND, us, [ht_m(u) - 0.0095 for u in us], 0.0062, 0.0009)
inlay('Etch_MetaTop', HAND, us, [ht_m(u) - 0.0080 for u in us], 0.0062, 0.0022, M_ETCH)
for name, h0, h1, off, _ in PLATES[:2]:
    inlay('Inlay_' + name, HAND, us, [h0 + 0.004 * (u / UB) ** 2 + 0.0055 for u in us], off, 0.0010)
q = np.linspace(0, 2 * PI, 60 * r)
RC = float(HAND.r(-0.056) * HAND.k(-0.056))
inlay('Inlay_Lozenge', HAND, (0.0075 * np.sign(np.sin(q)) * np.abs(np.sin(q)) ** 1.6) / RC, -0.056 + 0.0135 * np.cos(q), 0.0064, 0.0012)
for side in (-1, 1):   # small laurel sprigs either side of the lozenge
    t = np.linspace(0, 1, 50 * r)
    sx, sh = side * (0.006 + 0.020 * t), -0.064 + 0.020 * t ** 1.3
    inlay(f'Laurel_Stem_{side}', HAND, sx / RC, sh, 0.0062, 0.0011)
    for k, tk in enumerate((0.3, 0.55, 0.8)):
        a = np.linspace(0, 2 * PI, 24 * r); cx, ch = side * (0.006 + 0.020 * tk), -0.064 + 0.020 * tk ** 1.3
        L, Wd = 0.0075, 0.0028; ang = 0.9 if k % 2 else -0.4
        lx = cx + side * (L / 2) * (1 - np.cos(a)) * math.cos(ang) - (Wd / 2) * np.sin(a) * math.sin(ang)
        lh = ch + (L / 2) * (1 - np.cos(a)) * math.sin(ang) + (Wd / 2) * np.sin(a) * math.cos(ang)
        inlay(f'Laurel_Leaf_{side}_{k}', HAND, lx / RC, lh, 0.0062, 0.0009)

# ---------------- cuff (flared, over the wrist lames) ----------------
CUFF = Axial(W, (0, 0, -1), (0, -1, 0), [-0.006, 0.020, 0.045, 0.078], [0.0305, 0.0320, 0.0360, 0.0420], [1.40, 1.38, 1.34, 1.30])
use(CUFF)
cb = lambda u: -0.006 + 0.004 * math.cos(u) ** 2      # dips a little over the back of the hand
ct = lambda u: 0.076 + 0.003 * math.cos(u)
ob = patch('Cuff', -PI, PI, cb, ct, 0.0, 64 * r, 22 * r, M_STEEL, C_PLATES, thick=0.0022)
ob.vertex_groups.new(name='inner'); ob.modifiers['Solidify'].shell_vertex_group = 'inner'
rim('Rim_CuffTop', CUFF, np.linspace(-PI, PI, 80), ct, 0.0016, 0.0030)
rim('Rim_CuffBottom', CUFF, np.linspace(-PI, PI, 80), cb, 0.0012, 0.0020)
us = np.linspace(-PI, PI, 160 * r)
inlay('Inlay_CuffTop', CUFF, us, [ct(u) - 0.0110 for u in us], 0.0)
inlay('Inlay_CuffTop2', CUFF, us, [ct(u) - 0.0150 for u in us], 0.0, 0.0009)
inlay('Etch_CuffTop', CUFF, us, [ct(u) - 0.0130 for u in us], 0.0, 0.0028, M_ETCH)
inlay('Inlay_CuffBottom', CUFF, us, [cb(u) + 0.0075 for u in us], 0.0)
q = np.linspace(0, 2 * PI, 60 * r); RCc = float(CUFF.r(0.035) * CUFF.k(0.035))
inlay('Inlay_CuffLozenge', CUFF, (0.0080 * np.sign(np.sin(q)) * np.abs(np.sin(q)) ** 1.6) / RCc, 0.034 + 0.0125 * np.cos(q), 0.0002, 0.0012)
for s in (-1, 1):
    rivet(f'CuffRivet{s}', CUFF.at(s * 1.7, 0.010, 0.0), CUFF.surf_n(s * 1.7, 0.010), 0.0026, M_STEEL, C_TRIM)

# ---------------- fingers: leather tubes with three overlapping steel scales each ----------------
LEN = [0.082, 0.093, 0.087, 0.068]
RAD = [0.0094, 0.0098, 0.0094, 0.0084]
SPLAY = [-0.05, -0.012, 0.02, 0.07]                  # radians in X
CURL = [0.10, 0.30, 0.52]                             # cumulative bend toward the palm (+Y) per joint
SPLIT = [0.45, 0.30, 0.25]

def finger(tag, base, d0, length, rad, curl, back):
    """base: knuckle point; d0: unit direction of the first joint (toward the tip); back: dorsal direction."""
    p = np.asarray(base, float); bend_axis = unit(np.cross(d0, back))   # rotate toward the palm about this
    for j, (fr, cu) in enumerate(zip(SPLIT, curl)):
        L = length * fr
        c, s = math.cos(cu), math.sin(cu)
        d = d0 * c + np.cross(bend_axis, d0) * s + bend_axis * (bend_axis @ d0) * (1 - c)
        d = unit(d)
        e1 = back - (back @ d) * d                      # dorsal side of this joint (Axial orthogonalises it too)
        rj = rad * (1 - 0.06 * j); tip = j == len(SPLIT) - 1
        hs = [-L - (0.0 if tip else 0.003), -L + 0.004, -L * 0.5, 0.0, 0.004] if tip else [-L - 0.003, -L * 0.5, 0.0, 0.004]
        rs = [0.0030, rj * 0.80, rj, rj, rj] if tip else [rj * 0.97, rj * 0.98, rj, rj]
        ax = Axial(p, d, e1, hs, rs, [1.08] * len(hs))
        use(ax)
        patch(f'Glove_{tag}{j}', -PI, PI, (lambda u, a=hs[0] + (0.0004 if tip else 0): a), (lambda u, b=hs[-1]: b), 0.0, 22 * r, 10 * r, M_LEATHER, C_GLOVE, thick=0)
        top, bot = 0.0035, (-L + 0.0025 if not tip else -L + 0.0016)
        scl = steel(f'Scale_{tag}{j}', -1.30, 1.30, (lambda u, b=bot: b + 0.0012 * (u / 1.3) ** 2), (lambda u, t=top: t - 0.0016 * (u / 1.3) ** 2), 0.0016 + 0.0004 * (2 - j), 14, 6, thick=0.0012)
        p = p + d * L
    return p

for i in range(4):
    x = FX[i]; base = np.array([x, -0.0012, 0.705])
    d0 = unit([math.sin(SPLAY[i]), 0.0, -math.cos(SPLAY[i])])
    finger(f'F{i}', base, d0, LEN[i], RAD[i], CURL, np.array([0.0, -1.0, 0.0]))

# thumb: thenar pad from the hand edge, then two joints angled toward the body and the palm
TH0 = np.array([0.318, 0.004, 0.778]); TD = unit([-0.62, 0.22, -0.75])
th = Axial(TH0, TD, (0, -1, 0), [-0.046, -0.030, -0.010, 0.006], [0.0108, 0.0118, 0.0128, 0.0120], [1.10] * 4)
use(th); patch('Glove_Thenar', -PI, PI, lambda u: -0.046, lambda u: 0.006, 0.0, 22 * r, 12 * r, M_LEATHER, C_GLOVE, thick=0)
steel('Scale_Thenar', -1.25, 1.25, lambda u: -0.040 + 0.002 * (u / 1.25) ** 2, lambda u: -0.004, 0.0024, 16, 8, thick=0.0014)
SPLIT_T = SPLIT; SPLIT = [0.55, 0.45]
finger('T', TH0 + TD * 0.042, unit([-0.30, 0.30, -0.90]), 0.060, 0.0100, [0.0, 0.22], np.array([-0.45, -0.89, 0.0]))
SPLIT = SPLIT_T

# palm seams: raised saddle-stitch dashes in the glove leather (bake-only detail)
def stitches(name, ax, us, hs, off=0.0003, dash=0.0030, gap=0.0018, w=0.0011):
    P = ax.at(np.asarray(us), np.asarray(hs), off); N = ax.surf_n(np.asarray(us), np.asarray(hs))
    L = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
    k, s0 = 0, 0.0
    while s0 + dash < L[-1]:
        sel = (L >= s0) & (L <= s0 + dash)
        if sel.sum() >= 2: ribbon(f'Stitch_{name}_{k}', P[sel], N[sel], w, M_LEATHER, C_INLAY, thick=0.0004)
        s0 += dash + gap; k += 1
t = np.linspace(0, 1, 200 * r)
for s in (-1, 1):   # down both palm edges (the palm is centred on u = pi)
    stitches(f'PalmEdge{s}', HAND, np.full_like(t, s * (PI - 1.15)), -0.010 - 0.088 * t)
across = np.linspace(PI - 1.15, PI + 1.15, 200 * r)
stitches('PalmWrist', HAND, across, np.full_like(across, -0.010))
stitches('PalmBase', HAND, across, np.full_like(across, -0.098))

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, f'gauntlet_build_r{RES}.blend'))
print('BUILD OK', len(bpy.data.objects), 'objects', sum(len(o.data.polygons) for o in bpy.data.objects if o.type == 'MESH'), 'faces (pre-mod)')
