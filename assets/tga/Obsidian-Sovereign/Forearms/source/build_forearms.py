# Build the layered left vambrace (forearm defence) and save forearm_build_r<RES>.blend. TGA (Claude), 2026-10-31.
# CHEST_RES=1|3 blender -b --factory-startup -P build_forearms.py
# checkking's Obsidian Sovereign vocabulary (greave / gauntlet pipeline): two hinged steel shells around the forearm,
# raised keel, rolled rims, gold inlay borders + etch band, a lozenge and laurel under the elbow, hinges on the outer side,
# leather strap + buckle on the inner side, leather lining showing at the top.
# Frame: the Codex set's world frame (metres, Z up, front = -Y). Left arm on +X, hanging, back of hand toward -Y (as the
# checkking gauntlet). The arm axis runs from the gauntlet's wrist centre W up to the elbow E (Codex forearm/upper-arm
# meshes meet at z ~1.10). The vambrace's bottom tucks under the gauntlet's flared cuff (cuff top h 0.078); its top stops
# under the couter (Codex upper arms start at z 1.089): low in front (elbow crease), high at the back (point of the elbow).
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
    tube(name, ARM.at(us, hh, off), rad, m or M_STEEL, C_TRIM, seg * r, up=ARM.surf_n(us, hh))
def side_rim(name, u, h0, h1, off, rad):
    hh = np.linspace(h0, h1, 40); uu = np.full_like(hh, u)
    tube(name, ARM.at(uu, hh, off), rad, M_STEEL, C_TRIM, 6 * r, up=ARM.surf_n(uu, hh))
def inlay(name, us, hs, off, w=0.0013, m=None):
    us = np.asarray(us); hs = np.asarray(hs)
    ribbon(name, ARM.at(us, hs, off + 0.00012), ARM.surf_n(us, hs), w, m or M_GOLD, C_INLAY, thick=0.0001 if m else 0.0004)
def lozenge(name, h, off, half_w, half_h, w=0.0013):
    q = np.linspace(0, 2 * PI, 60 * r); RC = float(ARM.r(h) * ARM.k(h))
    inlay(name, (half_w * np.sign(np.sin(q)) * np.abs(np.sin(q)) ** 1.6) / RC, h + half_h * np.cos(q), off, w)
def laurel(tag, hc, off, length=0.020):
    RC = float(ARM.r(hc) * ARM.k(hc))
    for side in (-1, 1):
        t = np.linspace(0, 1, 50 * r)
        sx, sh = side * (0.007 + length * t), hc - 0.022 * t ** 1.3
        inlay(f'Laurel_Stem_{tag}{side}', sx / RC, sh, off, 0.0011)
        for k, tk in enumerate((0.3, 0.55, 0.8)):
            a = np.linspace(0, 2 * PI, 24 * r); cx, ch = side * (0.007 + length * tk), hc - 0.022 * tk ** 1.3
            L, Wd = 0.0075, 0.0028; ang = -0.9 if k % 2 else 0.4
            lx = cx + side * (L / 2) * (1 - np.cos(a)) * math.cos(ang) - (Wd / 2) * np.sin(a) * math.sin(ang)
            lh = ch + (L / 2) * (1 - np.cos(a)) * math.sin(ang) + (Wd / 2) * np.sin(a) * math.cos(ang)
            inlay(f'Laurel_Leaf_{tag}{side}_{k}', lx / RC, lh, off, 0.0009)
def buckle(tag, u, h, off):
    c = ARM.at(u, h, off); n = ARM.surf_n(u, h)
    t = -ARM.D.copy(); t -= (t @ n) * n; t /= np.linalg.norm(t); b = np.cross(n, t)
    rect = [c + t * 0.0090 + b * 0.0065, c + t * 0.0090 - b * 0.0065, c - t * 0.0090 - b * 0.0065, c - t * 0.0090 + b * 0.0065]
    pts = np.vstack([np.linspace(rect[i], rect[(i + 1) % 4], 8, endpoint=False) for i in range(4)])
    tube(f'Buckle_{tag}', pts, 0.0013, M_BUCKLE, C_TRIM, 8 * r, closed=True, up=np.tile(n, (len(pts), 1)))
    tube(f'Buckle_{tag}_Tongue', np.linspace(c - b * 0.0065, c + b * 0.0048 + n * 0.0010, 10), 0.0009, M_BUCKLE, C_TRIM, 6 * r, up=np.tile(t, (10, 1)))

# ---------------- forearm surface: surface of revolution on the wrist -> elbow axis; u = 0 back of the forearm (-Y), +pi/2 outer (+X)
W = np.array([0.351, 0.0, 0.800]); E = np.array([0.298, 0.0, 1.105])
A_H = [0.030, 0.060, 0.110, 0.160, 0.210, 0.250, 0.290]
A_D = [0.0285, 0.0300, 0.0360, 0.0410, 0.0440, 0.0450, 0.0445]     # half depth (back-front)
A_W = [0.0310, 0.0330, 0.0400, 0.0450, 0.0475, 0.0480, 0.0470]     # half width (side-side): widest at the muscle belly under the elbow
ARM = Axial(W, W - E, (0, -1, 0), A_H, A_D, [w / d for w, d in zip(A_W, A_D)])
use(ARM)

# outer shell (back of the forearm) over the inner shell; they overlap on both sides
UO, UI = 1.90, 1.40
o_b = lambda u: 0.062 + 0.004 * max(math.cos(u), 0.0) ** 2         # bottom: under the gauntlet cuff
o_t = lambda u: 0.236 + 0.020 * (1 - math.cos(u)) / 2               # top: low at the elbow crease, rising to the sides
i_b = lambda u: 0.066
i_t = lambda u: 0.262 - 0.012 * (1 + math.cos(u)) / 2               # highest at the point of the elbow (u = pi)
OFF_O, OFF_I = 0.0064, 0.0042
steel('VambOuter', -UO, UO, o_b, o_t, OFF_O, 56, 40)
steel('VambInner', PI - UI, PI + UI, i_b, i_t, OFF_I, 44, 38)
uo = np.linspace(-UO, UO, 110); ui = np.linspace(PI - UI, PI + UI, 90)
rim('Rim_OuterTop', uo, o_t, OFF_O + 0.0016, 0.0028)
rim('Rim_OuterBottom', uo, o_b, OFF_O + 0.0013, 0.0022)
rim('Rim_InnerTop', ui, i_t, OFF_I + 0.0016, 0.0026)
rim('Rim_InnerBottom', ui, i_b, OFF_I + 0.0012, 0.0020)
for s in (-1, 1):
    side_rim(f'Rim_OuterSide{s}', s * UO, o_b(UO), o_t(UO), OFF_O + 0.0010, 0.0015)
# keel down the back of the forearm, leather lining roll at the top edge
hz = np.linspace(o_b(0) + 0.010, o_t(0) - 0.012, 70)
tube('Ridge', ARM.at(np.zeros_like(hz), hz, OFF_O + 0.0006), 0.0030, M_STEEL, C_TRIM, 10 * r, flat=0.45, up=ARM.surf_n(np.zeros_like(hz), hz))
rim('Lining_Top', np.linspace(-PI, PI, 130), lambda u: (o_t(u) if abs(u) < UO else i_t(u)) - 0.0035, 0.0018, 0.0030, m=M_LEATHER)

# hinges on the outer side (+X) across the overlap, strap + buckle on the inner side (-X, toward the body)
UH = 0.5 * (UO + (PI - UI))
for k, hm in enumerate((0.110, 0.195)):
    hz = np.linspace(hm - 0.016, hm + 0.016, 12)
    tube(f'Hinge{k}', ARM.at(np.full_like(hz, UH), hz, OFF_O + 0.0032), 0.0030, M_STEEL, C_TRIM, 12 * r, up=ARM.surf_n(np.full_like(hz, UH), hz))
    for s in (-1, 1):
        uu = UH + s * 0.12
        steel(f'HingeLeaf{k}{s}', min(UH, uu), max(UH, uu), lambda u, a=hm: a - 0.013, lambda u, a=hm: a + 0.013, OFF_O + 0.0016 if s < 0 else OFF_I + 0.0024, 6, 6, thick=0.0012)
        rivet(f'Rivet_Hinge{k}{s}', ARM.at(UH + s * 0.09, hm, OFF_O + 0.0028 if s < 0 else OFF_I + 0.0036), ARM.surf_n(UH + s * 0.09, hm), 0.0020, M_STEEL, C_TRIM)
    us_s = np.linspace(-UH - 0.34, -UH + 0.24, 30 * r)
    offs = np.where(us_s > -UO, OFF_O + 0.0024, OFF_I + 0.0024)
    P = ARM.surf(us_s, np.full_like(us_s, hm)) + ARM.surf_n(us_s, np.full_like(us_s, hm)) * offs[:, None]
    ribbon(f'Strap{k}', P, ARM.surf_n(us_s, np.full_like(us_s, hm)), 0.013, M_LEATHER, C_STRAPS, thick=0.0020)
    buckle(f'S{k}', -UH + 0.29, hm, OFF_O + 0.0048)
    rivet(f'Rivet_Strap{k}', ARM.at(-UH - 0.30, hm, OFF_I + 0.0046), ARM.surf_n(-UH - 0.30, hm), 0.0022, M_STEEL, C_TRIM)

# gold + etch (set vocabulary): borders under the top and above the bottom, lozenge + laurel under the elbow, ridge lines
us = np.linspace(-(UO - 0.10), UO - 0.10, 150 * r)
inlay('Inlay_OuterTop', us, [o_t(u) - 0.0110 for u in us], OFF_O)
inlay('Inlay_OuterTop2', us, [o_t(u) - 0.0150 for u in us], OFF_O, 0.0009)
inlay('Etch_OuterTop', us, [o_t(u) - 0.0130 for u in us], OFF_O, 0.0024, M_ETCH)
inlay('Inlay_OuterBottom', us, [o_b(u) + 0.0100 for u in us], OFF_O)
inlay('Inlay_OuterBottom2', us, [o_b(u) + 0.0140 for u in us], OFF_O, 0.0009)
inlay('Etch_OuterBottom', us, [o_b(u) + 0.0120 for u in us], OFF_O, 0.0024, M_ETCH)
ui2 = np.linspace(PI - UI + 0.10, PI + UI - 0.10, 110 * r)
inlay('Inlay_InnerTop', ui2, [i_t(u) - 0.0100 for u in ui2], OFF_I)
inlay('Inlay_InnerBottom', ui2, [i_b(u) + 0.0090 for u in ui2], OFF_I)
lozenge('Inlay_ElbowLozenge', 0.196, OFF_O + 0.0032, 0.0075, 0.0130)
laurel('Elbow', 0.178, OFF_O + 0.0002)
for s in (-1, 1):
    hz = np.linspace(o_b(0) + 0.022, 0.160, 110 * r)
    RC = float(ARM.r(0.12) * ARM.k(0.12))
    inlay(f'Inlay_Ridge{s}', np.full_like(hz, s * 0.0075 / RC), hz, OFF_O, 0.0009)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, f'forearm_build_r{RES}.blend'))
print('BUILD OK', len(bpy.data.objects), 'objects', sum(len(o.data.polygons) for o in bpy.data.objects if o.type == 'MESH'), 'faces (pre-mod)')
