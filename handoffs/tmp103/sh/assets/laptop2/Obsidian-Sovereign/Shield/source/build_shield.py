# Build the Obsidian Sovereign hand shield (#96, item 30, not part of the armour set) at low or high density and
# save shield_build_r<RES>.blend.   CHEST_RES=1|3 blender -b --factory-startup -P build_shield.py
# Frame: metres, Z up, the face looks toward -Y (same as the set). Heater shield, 0.78 m tall, 0.60 m wide, point at
# z 0, top edge at z 0.78, centred on x 0. Shared helpers (mesh_obj, tube, ribbon, rivet) come from the chest's chestlib.
import sys, os, math
D = os.environ.get('WORK') or os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import numpy as np
import bpy
from chestlib import mesh_obj, grid_faces, tube, ribbon, rivet

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
C_PLATES, C_TRIM, C_BACK, C_INLAY = coll('Plates'), coll('Trim'), coll('Back'), coll('Inlay')
RES = int(os.environ.get('CHEST_RES', '1')); r = RES
PI = math.pi

# ---------------- shape ----------------
H, W = 0.78, 0.30          # height, half width
Z1 = 0.44 * H              # where the straight sides start curving to the point
ZC = 0.58 * H              # boss centre
FACE_T = 0.0045            # steel face thickness (solidified backward, +Y)

def halfw(z):
    t = np.clip(np.asarray(z, float) / Z1, 0, 1)
    return W * (1 - (1 - t) ** 2) ** 0.62

def surf(x, z):
    """Front face: convex toward -Y, a little more curved across than along."""
    x = np.asarray(x, float); z = np.asarray(z, float)
    y = -(0.055 - x * x / (2 * 0.46) - (z - ZC) ** 2 / (2 * 1.9))
    return np.stack([x, y, z * np.ones_like(x)], -1)

def surf_n(x, z, d=1e-4):
    dx = surf(np.asarray(x) + d, z) - surf(np.asarray(x) - d, z)
    dz = surf(x, np.asarray(z) + d) - surf(x, np.asarray(z) - d)
    n = np.cross(dz, dx)               # points toward -Y (the face's outside)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return np.where(n[..., 1:2] > 0, -n, n)

def at(x, z, off):
    return surf(x, z) + surf_n(x, z) * np.asarray(off, float)[..., None] if np.ndim(off) else surf(x, z) + surf_n(x, z) * off

# outline (x, z), counter-clockwise seen from the front: point -> right side -> top -> left side
def outline(n_side, n_top, inset=0.0):
    zs = np.linspace(0.0, H, n_side)
    right = np.stack([halfw(zs), zs], 1)
    top = np.stack([np.linspace(W, -W, n_top)[1:-1], np.full(n_top - 2, H)], 1)
    left = right[::-1] * np.array([-1, 1])
    P = np.vstack([right, top, left[:-1]])
    if inset:
        # offset inward along the 2D normal (the outline is CCW, so the inward normal is the left-hand normal)
        T = np.roll(P, -1, 0) - np.roll(P, 1, 0); T /= np.linalg.norm(T, axis=1, keepdims=True) + 1e-12
        N = np.stack([-T[:, 1], T[:, 0]], 1)
        P = P + N * inset
        P[:, 1] = np.clip(P[:, 1], inset * 1.6, H - inset)          # keep the point and top inside
        P[:, 0] = np.clip(P[:, 0], -(W - inset), W - inset)
    return P

# ---------------- face plate (grid over s = x / halfw, t = z / H) ----------------
def face(name, off, nu, nv, m, c, thick, t0=0.022):
    S = np.linspace(-1, 1, nu * r); T = np.linspace(t0, 1, nv * r) ** 1.0
    Z = T * H
    X = S[:, None] * halfw(Z)[None, :]
    ZZ = np.broadcast_to(Z[None, :], X.shape)
    V = at(X, ZZ, off)
    uv = np.stack([X, ZZ], -1).reshape(-1, 2)    # planar: the face curves gently, so this stays near true length
    ob = mesh_obj(name, V.reshape(-1, 3), grid_faces(len(S), len(T)), m, c, uv)
    if thick:
        md = ob.modifiers.new('Solidify', 'SOLIDIFY'); md.thickness = thick; md.offset = -1; md.use_even_offset = True; md.use_rim = True
        ob.vertex_groups.new(name='inner'); md.shell_vertex_group = 'inner'
    return ob
face('Face', 0.0, 44, 60, M_STEEL, C_PLATES, FACE_T)      # solidify goes backward (+Y): normals point to -Y, so offset -1

# back covering: leather glued over the wooden core, just behind the steel
back = face('BackCover', -(FACE_T + 0.010), 30, 40, M_LEATHER, C_BACK, 0.0)
for p in back.data.polygons: p.flip()
back.data.update()

# ---------------- rolled rim + edge band ----------------
O = outline(70 * r, 24 * r)
OR = np.vstack([O, O[:1]])
rim_pts = at(O[:, 0], O[:, 1], -FACE_T * 0.5)
tube('Rim', rim_pts, 0.0115, M_STEEL, C_TRIM, 12 * r, closed=True, up=surf_n(O[:, 0], O[:, 1]))
# a raised flat band just inside the rim (an applied edge strip)
OB = outline(70 * r, 24 * r, inset=0.026)
OO = outline(70 * r, 24 * r, inset=0.004)
Pi = at(OB[:, 0], OB[:, 1], 0.0018); Po = at(OO[:, 0], OO[:, 1], 0.0018)
NB = len(O)
Vb = np.vstack([Po, Pi]); Fb = [(k, (k + 1) % NB, NB + (k + 1) % NB, NB + k) for k in range(NB)]
Lb = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(np.vstack([Po, Po[:1]]), axis=0), axis=1))])[:-1]
uvb = np.vstack([np.stack([Lb, np.zeros(NB)], 1), np.stack([Lb, np.full(NB, 0.024)], 1)])
eb = mesh_obj('EdgeBand', Vb, Fb, M_STEEL, C_PLATES, uvb)
md = eb.modifiers.new('Solidify', 'SOLIDIFY'); md.thickness = 0.0016; md.offset = -1; md.use_rim = True
tube('Rim_BandInner', at(OB[:, 0], OB[:, 1], 0.0032), 0.0016, M_STEEL, C_TRIM, 8 * r, closed=True, up=surf_n(OB[:, 0], OB[:, 1]))

# rivets on the edge band, evenly spaced along it
OBm = outline(70 * r, 24 * r, inset=0.013)
Lm = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(OBm, axis=0), axis=1))])
for k, s in enumerate(np.arange(0.03, Lm[-1] - 0.02, 0.058)):
    i = int(np.searchsorted(Lm, s)); x, z = OBm[min(i, len(OBm) - 1)]
    rivet(f'Rivet_Band{k}', at(x, z, 0.0035), surf_n(x, z), 0.0065, M_STEEL, C_TRIM)

# ---------------- boss: domed centre with a flat flange ----------------
RB, HB, FL = 0.074, 0.034, 0.016
na, nr = 48 * r, 16 * r
A = np.linspace(0, 2 * PI, na, endpoint=False)
R = np.linspace(0, RB + FL, nr)
Hh = np.where(R <= RB, HB * np.clip(1 - (R / RB) ** 2, 0, 1) ** 0.75, 0.0) + 0.0025
X = 0.0 + R[None, :] * np.cos(A)[:, None]; Z = ZC + R[None, :] * np.sin(A)[:, None]
V = surf(X, Z) + surf_n(X, Z) * Hh[None, :, None]
Fbs = []
for i in range(na):
    i2 = (i + 1) % na
    for j in range(nr - 1):
        Fbs.append((i * nr + j, i * nr + j + 1, i2 * nr + j + 1, i2 * nr + j))
uvs = np.stack([X - 0.0, Z - ZC], -1).reshape(-1, 2) * 1.25     # a little more texel density on the boss
boss = mesh_obj('Boss', V.reshape(-1, 3), Fbs, M_STEEL, C_PLATES, uvs)
bm_md = boss.modifiers.new('Weld', 'WELD'); bm_md.merge_threshold = 1e-6
md = boss.modifiers.new('Solidify', 'SOLIDIFY'); md.thickness = 0.0025; md.offset = -1; md.use_rim = True
boss.vertex_groups.new(name='inner'); md.shell_vertex_group = 'inner'
q = np.linspace(0, 2 * PI, 72 * r)
tube('Rim_Boss', at(RB * np.cos(q), ZC + RB * np.sin(q), 0.0040), 0.0032, M_GOLD, C_TRIM, 8 * r, closed=True,
     up=surf_n(RB * np.cos(q), ZC + RB * np.sin(q)))
for k in range(8):
    a = 2 * PI * k / 8 + PI / 8; x, z = (RB + FL * 0.55) * math.cos(a), ZC + (RB + FL * 0.55) * math.sin(a)
    rivet(f'Rivet_Boss{k}', at(x, z, 0.0030), surf_n(x, z), 0.0055, M_STEEL, C_TRIM)

# ---------------- gold inlay + etch on the face ----------------
def inlay(name, xs, zs, off, w=0.0016, m=None):
    xs = np.asarray(xs, float); zs = np.asarray(zs, float)
    ribbon(name, at(xs, zs, off + 0.00012), surf_n(xs, zs), w, m or M_GOLD, C_INLAY, thick=0.0001 if m else 0.0004)

def loop_inlay(name, P, off, w=0.0016, m=None):
    P = np.vstack([P, P[:1]]); inlay(name, P[:, 0], P[:, 1], off, w, m)

loop_inlay('Inlay_Border', outline(70 * r, 24 * r, inset=0.040), 0.0, 0.0055)
loop_inlay('Inlay_Border2', outline(70 * r, 24 * r, inset=0.060), 0.0, 0.0030)
loop_inlay('Etch_Border', outline(70 * r, 24 * r, inset=0.050), 0.0, 0.0140, M_ETCH)

# sovereign lozenge around the boss
qq = np.linspace(0, 2 * PI, 160 * r)
def lozenge(name, a, b, p, w):
    c, s = np.cos(qq), np.sin(qq)
    x = a * np.sign(c) * np.abs(c) ** (2 / p); z = ZC + b * np.sign(s) * np.abs(s) ** (2 / p)
    inlay(name, x, z, 0.0, w)
lozenge('Inlay_Lozenge', 0.150, 0.215, 1.25, 0.0060)
lozenge('Inlay_Lozenge2', 0.168, 0.240, 1.25, 0.0030)
# pale: a vertical line from the lozenge down to the point, and up to the top border
zl = np.linspace(0.075, ZC - 0.235, 60 * r); inlay('Inlay_PaleLow', np.zeros_like(zl), zl, 0.0, 0.0050)
zu = np.linspace(ZC + 0.236, H - 0.058, 30 * r); inlay('Inlay_PaleHigh', np.zeros_like(zu), zu, 0.0, 0.0050)
inlay('Etch_PaleLow', np.zeros_like(zl), zl, 0.0, 0.0160, M_ETCH)

def laurel(tag, cx, cz, length=0.095, rise=-0.060):
    """two sprigs leaving the pale, curving outward and down (rise < 0)."""
    for side in (-1, 1):
        t = np.linspace(0, 1, 60 * r)
        sx, sz = cx + side * (0.010 + length * t), cz + rise * t ** 1.4
        inlay(f'Laurel_Stem_{tag}{side}', sx, sz, 0.0, 0.0036)
        for k, tk in enumerate((0.22, 0.42, 0.62, 0.82)):
            a = np.linspace(0, 2 * PI, 28 * r)
            ox, oz = cx + side * (0.010 + length * tk), cz + rise * tk ** 1.4
            L, Wd = 0.038, 0.014; ang = (0.85 if k % 2 else -0.35)
            lx = ox + side * ((L / 2) * (1 - np.cos(a)) * math.cos(ang) - (Wd / 2) * np.sin(a) * math.sin(ang))
            lz = oz + (L / 2) * (1 - np.cos(a)) * math.sin(ang) + (Wd / 2) * np.sin(a) * math.cos(ang)
            inlay(f'Laurel_Leaf_{tag}{side}_{k}', lx, lz, 0.0, 0.0028)
laurel('Low', 0.0, ZC - 0.255)
laurel('High', 0.0, ZC + 0.250, 0.075, 0.012)

# ---------------- back: arm strap (enarme) and hand grip ----------------
def back_strap(name, z, half, bow, wdt, m):
    xs = np.linspace(-half, half, 40 * r)
    base = at(xs, np.full_like(xs, z), -(FACE_T + 0.0105))
    bowv = np.array([0, 1.0, 0])[None, :] * (bow * (1 - (xs / half) ** 2) ** 1.2)[:, None]
    nrm = -surf_n(xs, np.full_like(xs, z))
    return ribbon(name, base + bowv, nrm, wdt, m, C_BACK, thick=0.0035), xs, base
_, xs_a, base_a = back_strap('Strap_Arm', ZC + 0.07, 0.15, 0.028, 0.040, M_LEATHER)
zg = ZC - 0.13
xg = np.linspace(-0.065, 0.065, 30 * r)
pg = at(xg, np.full_like(xg, zg), -(FACE_T + 0.0105)) + np.array([0, 1.0, 0])[None, :] * (0.040 * (1 - (xg / 0.065) ** 2) ** 0.8 + 0.006)[:, None]
tube('Grip', pg, 0.0125, M_LEATHER, C_BACK, 12 * r, up=np.tile([0, 0, 1.0], (len(pg), 1)))
for s in (-1, 1):
    for z, x in ((ZC + 0.07, 0.15), (zg, 0.068)):
        rivet(f'Rivet_BackStrap{s}_{z:.3f}', at(s * x, z, -(FACE_T + 0.0105)) + np.array([0, 0.004, 0]),
              -surf_n(s * x, z), 0.0050, M_BUCKLE, C_BACK)
        # the strap rivets go through the shield: their heads show on the face too
        rivet(f'Rivet_Front{s}_{z:.3f}', at(s * x, z, 0.0004), surf_n(s * x, z), 0.0048, M_STEEL, C_TRIM)
# a leather pad under the forearm
pad_x = np.linspace(-0.11, 0.11, 24 * r)
pad_pts = at(pad_x, np.full_like(pad_x, ZC - 0.03), -(FACE_T + 0.0115))
ribbon('Pad_Arm', pad_pts, -surf_n(pad_x, np.full_like(pad_x, ZC - 0.03)), 0.085, M_LEATHER, C_BACK, thick=0.010)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, f'shield_build_r{RES}.blend'))
print('BUILD OK', len(bpy.data.objects), 'objects', sum(len(o.data.polygons) for o in bpy.data.objects if o.type == 'MESH'), 'faces (pre-mod)')
