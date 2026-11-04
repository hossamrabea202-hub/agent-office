# #488 carved merlon kit (i5, 2026-11-04). Every stone is real geometry; one mesh per module; one joint-free patch of the
# real scan (T_vdbhdju_2K) per stone face on UV0; vertex colour R = stone tone, G = damp, B = cavity (the contract of
# M_CastleAshlarWeathered2). courses / joints / sides_of / seg_dist / vnoise / carve come from TGA_PC's walls_aaa_v2
# generator, adapted to the module frame. The carved mesh IS the game mesh (Nanite), nothing is baked.
#   blender -b --factory-startup -P build_merlon_kit.py -- build  [out_dir] [--only Name,Name]
#   blender -b --factory-startup -P build_merlon_kit.py -- verify [out_dir]              re-imports the FBX, checks them
#   blender -b --factory-startup -P build_merlon_kit.py -- patchsheet <scan_dir> <png>   draws the clean patches on the scan
#   blender -b --factory-startup -P build_merlon_kit.py -- render <scan_dir> [out_dir] [--shots a,b]
# scan_dir holds scan_B/N/ORM.png: write them with export_scan_488_ue.py (read-only). The build needs no image.
# Frame, cm: u = along the wall, d = from the DROP-side face (0) to the walk side (+T), v = up from the base (0 = pivot).
# Blender metres: X = u, Y = -d, Z = v. UE after the FBX import: x = u, y = d, z = v, pivot at (0, 0, 0).
import bpy, bmesh, json, math, os, random, sys, zlib
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

# ---------- sizes (measured on the map, confirmed by i9; change them here and re-run) ----------
CFG = dict(PITCH=240.0,      # centre to centre along the wall: merlon 140 + crenel 100 (measured)
           MERLON_W=140.0,   # body width (measured)
           T=50.0,           # thickness (measured: merlon body 50, parapet below it 46)
           H=190.0,          # top of the coping ridge above the walk deck (z 6.80 -> 8.70, i9)
           SILL_H=75.0,      # walk-side edge of the crenel sill above the deck (z 7.55, i9)
           SILL_OUT=6.0,     # the sill top falls this much to the outer side (sheds rain)
           SILL_DRIP=3.0,    # sill stone overhang past the outer face
           Z1=34.0,          # top of the base course
           SEAT=60.0,        # top of the second course: the sill stone and the free-standing body start here
           TOOTH1=15.0,      # base course runs this far past the body...
           TOOTH2=-8.0,      # ...second course stops this far short of it: no straight joint at merlon / sill
           COPE=22.0,        # coping height, soffit to ridge
           COPE_OVER=5.0,    # coping overhang all round (drip)
           CORNER_ARM=125.0, # corner merlon: outer corner to the end of each arm
           INNER_L=240.0,    # plain inner parapet: length of one module (same grid as the merlons)
           INNER_H=105.0,    # plain inner parapet: ridge above the deck (i9 asked for 100-110)
           INNER_T=40.0,     # plain inner parapet: thickness
           INNER_COPE=17.0,  # plain inner parapet: coping height
           INNER_STAGGER=14.0, # courses alternate this far past the module ends, so two neighbours interlock
           JOINT=2.0,        # joint width
           MORTAR_IN=4.0,    # lime mortar face this deep behind the stone face
           VOXEL=0.75,       # stone surface sampling, cm (fine enough for a sharp arris)
           DECIMATE=0.115,    # share of the triangles kept on each stone
           PX_CM=5.0,        # scan pixels per cm where the patch allows it (the walls' tile 320 is 6.4)
           PX_MIN=3.4)       # long stones may drop to this density, never lower unless nothing else fits
MODULES = {'SM_Merlon488_A': ('merlon', 1), 'SM_Merlon488_B': ('merlon', 2), 'SM_Merlon488_C': ('merlon', 3),
           'SM_Merlon488_D': ('merlon', 4), 'SM_CrenelSill488_A': ('sill', 1), 'SM_CrenelSill488_B': ('sill', 2),
           'SM_MerlonCorner488': ('corner', 1), 'SM_InnerParapet488_A': ('inner', 1), 'SM_InnerParapet488_B': ('inner', 2)}
STONE_SLOT, MORTAR_SLOT = 'MI_CastleMerlon488', 'M_CastleLimeMortar'
# Joint-free rectangles of T_vdbhdju_2K, read off the scan by eye: x0, y0, x1, y1 in px of a 1932 px view (x 1.06 = 2048).
# The cracked vine, the weeds and the rust-lichen stone are left out. `patchsheet` draws them on the scan.
PATCHES_1932 = [(130, 30, 380, 335), (395, 30, 605, 335), (620, 30, 905, 335), (920, 30, 1150, 335), (1170, 30, 1365, 335),
                (1385, 30, 1730, 340), (1750, 30, 1925, 340),
                (5, 358, 260, 665), (355, 358, 645, 660), (660, 358, 930, 660), (945, 358, 1222, 660), (1250, 358, 1535, 660), (1555, 358, 1880, 660),
                (90, 680, 435, 985), (450, 680, 800, 985), (815, 680, 1100, 985), (1115, 680, 1345, 985), (1360, 680, 1685, 985),
                (140, 1005, 530, 1285), (1140, 1110, 1410, 1290), (1430, 1010, 1745, 1290),
                (5, 1305, 220, 1610), (235, 1305, 695, 1610), (710, 1305, 975, 1610), (990, 1305, 1225, 1610), (1255, 1305, 1540, 1610), (1560, 1305, 1810, 1610),
                (300, 1635, 485, 1932), (500, 1635, 795, 1932), (810, 1635, 1040, 1890), (1070, 1635, 1315, 1932), (1335, 1635, 1590, 1932)]
INSET_PX, TEX = 12, 2048
PATCHES = [(x0 * 1.06 + INSET_PX, y0 * 1.06 + INSET_PX, x1 * 1.06 - INSET_PX, y1 * 1.06 - INSET_PX) for x0, y0, x1, y1 in PATCHES_1932]

argv = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.abspath(__file__))
STAGE = argv[0]
ONLY = argv[argv.index('--only') + 1].split(',') if '--only' in argv else None
SHOTS = argv[argv.index('--shots') + 1].split(',') if '--shots' in argv else None
POS = [a for i, a in enumerate(argv) if i and not a.startswith('--') and argv[i - 1] not in ('--only', '--shots')]
CM, G = 0.01, CFG['JOINT'] / 2
H = lambda *key: zlib.crc32(repr(key).encode())
sm = lambda t: np.clip(t, 0, 1) ** 2 * (3 - 2 * np.clip(t, 0, 1))


def prism(bm, poly, d0, d1, axis):
    """axis 'd': poly is (u, v), extruded along d. axis 'u': poly is (d, v), extruded along u."""
    to = (lambda p, s: (p[0] * CM, -s * CM, p[1] * CM)) if axis == 'd' else (lambda p, s: (s * CM, -p[0] * CM, p[1] * CM))
    a = [bm.verts.new(to(p, d0)) for p in poly]; b = [bm.verts.new(to(p, d1)) for p in poly]
    bm.faces.new(a); bm.faces.new(list(reversed(b)))
    for i in range(len(poly)):
        j = (i + 1) % len(poly); bm.faces.new((a[i], a[j], b[j], b[i]))


def obj_from(name, fill):
    bm = bmesh.new(); fill(bm); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    return ob


def activate(ob):
    bpy.context.view_layer.update()
    for o in bpy.context.scene.objects: o.select_set(False)
    ob.select_set(True); bpy.context.view_layer.objects.active = ob


def vnoise(P, seed):
    I = np.floor(P).astype(np.int64); F = P - I; F = F * F * (3 - 2 * F); acc = np.zeros(len(P))
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                n = ((I[:, 0] + dx) * 73856093) ^ ((I[:, 1] + dy) * 19349663) ^ ((I[:, 2] + dz) * 83492791) ^ (seed * 2654435761)
                n &= 0xffffffff; n = ((n ^ (n >> 13)) * 1274126177) & 0xffffffff
                w = (F[:, 0] if dx else 1 - F[:, 0]) * (F[:, 1] if dy else 1 - F[:, 1]) * (F[:, 2] if dz else 1 - F[:, 2])
                acc += w * (n / 0xffffffff * 2 - 1)
    return acc


def sides_of(poly):
    n = len(poly); corner = []
    for i in range(n):
        p0, p1, p2 = poly[i - 1], poly[i], poly[(i + 1) % n]
        a = math.atan2(p1[1] - p0[1], p1[0] - p0[0]); b = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
        corner.append(abs((b - a + math.pi) % (2 * math.pi) - math.pi) > math.radians(30))
    start = corner.index(True) if any(corner) else 0
    sides, cur = [], [poly[start]]
    for k in range(1, n + 1):
        i = (start + k) % n; cur.append(poly[i])
        if corner[i] or k == n: sides.append(np.array(cur)); cur = [poly[i]]
    return sides


def seg_dist(Q, S):
    A, B = S[:-1], S[1:]; AB = B - A; L2 = np.maximum((AB ** 2).sum(1), 1e-9)
    t = np.clip(((Q[:, None, :] - A[None]) * AB[None]).sum(2) / L2[None], 0, 1)
    D = Q[:, None, :] - (A[None] + t[..., None] * AB[None])
    return np.sqrt((D ** 2).sum(2)).min(1)


# ---------- stone layout ----------
def blocks(lo, hi, a, b, r, avoid=(), end_min=24.0):
    """cut [lo, hi] into blocks of a..b cm, no joint within 11 cm of a joint of the course below (real bond)."""
    span = hi - lo
    for _ in range(300):
        cuts, x = [], lo + r.uniform(a, b)
        while x < hi - end_min:
            cuts.append(x); x += r.uniform(a, b)
        if (hi - cuts[-1] if cuts else span) > b * 1.25: continue
        if all(abs(c - w) >= 11 for c in cuts for w in avoid): return [lo] + cuts + [hi]
    return [lo, 0.5 * (lo + hi), hi] if span > b else [lo, hi]


class Layout:
    def __init__(self):
        self.stones, self.core, self.cull, self.plugs, self.zones = [], [], [], [], []

    def box(self, key, u0, u1, d0, d1, v0, v1, base=False):
        """rect stone. Joints are taken off here. The bottom of the module keeps its bed."""
        low = v0 + (0 if base else G)
        self.stones.append(dict(key=key, poly=[(u0 + G, low), (u1 - G, low), (u1 - G, v1 - G), (u0 + G, v1 - G)], d0=d0, d1=d1, axis='d', rock=1.0))

    def section(self, key, poly, s0, s1, axis, rock=0.75):
        self.stones.append(dict(key=key, poly=poly, d0=s0, d1=s1, axis=axis, rock=rock))

    def corebox(self, u0, u1, d0, d1, v0, v1):
        self.core.append((u0, u1, d0, d1, v0, v1)); self.cull.append((u0, u1, d0, d1, v0 - 12, v1))


def coping_section(a, b, top, cope, over):
    """(s, v) across the wall, faces at s = a and s = b: bevelled soffit, eave, saddleback ridge (sheds rain both ways)."""
    v0 = top - cope; eave = v0 + cope * 0.43; mid = 0.5 * (a + b)
    return [(a - 1, v0 + G), (b + 1, v0 + G), (b + over, v0 + cope * 0.2), (b + over, eave), (mid, top), (a - over, eave), (a - over, v0 + cope * 0.2)]


def scaled_courses(lo, hi, want):
    k = (hi - lo) / sum(want); zs = [lo]
    for b in want: zs.append(zs[-1] + b * k)
    return zs


def merlon(seed):
    C, L, r = CFG, Layout(), random.Random(H('merlon', seed))
    T, HW, IN = C['T'], C['MERLON_W'] / 2, C['MORTAR_IN']
    top = C['H'] - C['COPE']
    body = [[31, 26, 23, 20], [37, 33, 30], [29, 27, 24, 20], [34, 28, 21, 17]][(seed - 1) % 4]
    zs = scaled_courses(C['SEAT'], top, body)
    rows = [(0.0, C['Z1'], HW + C['TOOTH1'], 52, 95), (C['Z1'], C['SEAT'], HW + C['TOOTH2'], 46, 80)]
    for i in range(len(body)):
        f = i / max(1, len(body) - 1)                                        # smaller up
        rows.append((zs[i], zs[i + 1], HW, 48 - 14 * f, 80 - 24 * f))
    under = {'o': [], 'i': []}; flip = seed % 2
    for c, (v0, v1, hw, a, b) in enumerate(rows):
        base = c == 0
        if (c + flip) % 2 == 0:                                              # through course: bond stones, seen on both faces
            js = blocks(-hw, hw, a, b, r, under['o'] + under['i'])
            for j in range(len(js) - 1): L.box(('t', c, j), js[j], js[j + 1], 0, T, v0, v1, base)
            under['o'] = under['i'] = js[1:-1]
        else:                                                                # two skins, own joints on each face
            dm = T / 2 + r.uniform(-4, 4)
            for f, (d0, d1) in (('o', (0, dm - G)), ('i', (dm + G, T))):
                js = blocks(-hw, hw, a, b, r, under[f])
                for j in range(len(js) - 1): L.box((f, c, j), js[j], js[j + 1], d0, d1, v0, v1, base)
                under[f] = js[1:-1]
    o = C['COPE_OVER']; cuts = [-HW - o, HW + o]
    cuts.insert(1, r.uniform(-34, 34))                                       # two coping stones
    sec = coping_section(0, T, C['H'], C['COPE'], o)
    for j in range(len(cuts) - 1):
        L.section(('cope', j), sec, cuts[j] + (G if j else 0), cuts[j + 1] - (G if j < len(cuts) - 2 else 0), 'u')
    L.corebox(-HW - C['TOOTH1'], HW + C['TOOTH1'], IN, T - IN, 0, C['Z1'])
    L.corebox(-HW - C['TOOTH2'], HW + C['TOOTH2'], IN, T - IN, C['Z1'], C['SEAT'])
    L.corebox(-HW, HW, IN, T - IN, C['SEAT'], C['SILL_H'] - C['SILL_OUT'])    # closes the joint against the sill stone
    L.corebox(-HW + IN, HW - IN, IN, T - IN, C['SEAT'], top + 2)
    for sg in (-1, 1):                                                       # the neighbouring sill
        for hw, v0, v1 in ((HW + C['TOOTH1'], 0, C['Z1']), (HW + C['TOOTH2'], C['Z1'], C['SEAT']), (HW, C['SEAT'], C['SILL_H'])):
            L.zones.append((min(sg * hw, sg * (hw + 70)), max(sg * hw, sg * (hw + 70)), 0, T, v0, v1))
    return L


def sill(seed):
    C, L, r = CFG, Layout(), random.Random(H('sill', seed))
    T, IN, half = C['T'], C['MORTAR_IN'], C['PITCH'] / 2
    hws = half - C['MERLON_W'] / 2                                           # 50: the opening
    h1 = half - (C['MERLON_W'] / 2 + C['TOOTH1']); h2 = half - (C['MERLON_W'] / 2 + C['TOOTH2'])
    L.box(('a', 0), -h1, h1, 0, T, 0, C['Z1'], True)
    js = [-h2, r.uniform(-20, 20) if seed % 2 else r.uniform(-34, -14), h2]
    for j in range(2): L.box(('b', j), js[j], js[j + 1], 0, T, C['Z1'], C['SEAT'])
    # sill stone: full thickness, falls to the outer side, drip over the outer face, ends tight against the jambs
    D, top, out = C['SILL_DRIP'], C['SILL_H'], C['SILL_H'] - C['SILL_OUT']
    sec = [(-D + 1, C['SEAT'] + G), (T, C['SEAT'] + G), (T, top), (-D, out), (-D, out - 5)]
    edges = [-hws, hws] if seed % 2 else [-hws, r.uniform(-16, 16), hws]        # a real joint against each jamb
    for j in range(len(edges) - 1):
        L.section(('sill', j), sec, edges[j] + G, edges[j + 1] - G, 'u', 0.6)
    # mortar under the stone and in its end joints, following the slope, so a crenel joint can't be seen through
    L.plugs.append(([(IN, C['SEAT']), (T - IN, C['SEAT']), (T - IN, top - 2), (IN, out + (top - out) * (IN + D) / (T + D) - 2)], -hws - 0.8, hws + 0.8))
    L.corebox(-h1, h1, IN, T - IN, 0, C['Z1']); L.corebox(-h2, h2, IN, T - IN, C['Z1'], C['SEAT'])
    L.corebox(-hws, hws, IN, T - IN, C['SEAT'], out)
    for sg in (-1, 1):                                                       # the neighbouring merlon
        for hw, v0, v1 in ((h1, 0, C['Z1']), (h2, C['Z1'], C['SEAT']), (hws, C['SEAT'], C['SILL_H'] + 30)):
            L.zones.append((min(sg * hw, sg * (hw + 70)), max(sg * hw, sg * (hw + 70)), 0, T, v0, v1))
    return L


def corner(seed):
    """L plan. Pivot at the bottom of the OUTER CORNER. Arms run along +u and +d. Long and short quoins: each course one
    arm runs through the corner and the other butts against it."""
    C, L, r = CFG, Layout(), random.Random(H('corner', seed))
    T, A, IN, top = C['T'], C['CORNER_ARM'], C['MORTAR_IN'], C['H'] - C['COPE']
    body = [34, 30, 25, 21]; zs = scaled_courses(C['SEAT'], top, body)
    rows = [(0.0, C['Z1'], A + C['TOOTH1'], 55, 90), (C['Z1'], C['SEAT'], A + C['TOOTH2'], 46, 80)]
    rows += [(zs[i], zs[i + 1], A, 46 - 4 * i, 74 - 7 * i) for i in range(len(body))]
    ux, uy = [], []
    for c, (v0, v1, reach, a, b) in enumerate(rows):
        base = c == 0; x_first = c % 2 == 0
        jx = blocks(0.0 if x_first else T, reach, a, b, r, ux, 26); ux = jx[1:-1]
        jy = blocks(T if x_first else 0.0, reach, a, b, r, uy, 26); uy = jy[1:-1]
        jx[0] = -G if x_first else T + G                                     # flush outer corner, a real joint at the butting arm
        for j in range(len(jx) - 1): L.box(('x', c, j), jx[j], jx[j + 1], 0, T, v0, v1, base)
        for j in range(len(jy) - 1):
            lo = 0.0 if j == 0 and not x_first else (T + 2 * G if j == 0 else jy[j] + G)
            L.box(('y', c, j), -G, T + G, lo, jy[j + 1] - G, v0, v1, base)
    o = C['COPE_OVER']; sec = coping_section(0, T, C['H'], C['COPE'], o)
    cx = r.uniform(58, 80)
    L.section(('cx', 0), sec, -o, cx - G, 'u'); L.section(('cx', 1), sec, cx + G, A + o, 'u')
    cy = r.uniform(84, 100)                                                  # the walk arm's coping butts against the other one's eave
    L.section(('cy', 0), sec, T + o + 2 * G, cy - G, 'd'); L.section(('cy', 1), sec, cy + G, A + o, 'd')
    for reach, v0, v1 in ((A + C['TOOTH1'], 0, C['Z1']), (A + C['TOOTH2'], C['Z1'], C['SEAT'])):
        L.corebox(IN, reach, IN, T - IN, v0, v1); L.corebox(IN, T - IN, IN, reach, v0, v1)
    L.corebox(IN, A, IN, T - IN, C['SEAT'], C['SILL_H'] - C['SILL_OUT']); L.corebox(IN, T - IN, IN, A, C['SEAT'], C['SILL_H'] - C['SILL_OUT'])
    L.corebox(IN, A - IN, IN, T - IN, C['SEAT'], top + 2); L.corebox(IN, T - IN, IN, A - IN, C['SEAT'], top + 2)
    for hw, v0, v1 in ((A + C['TOOTH1'], 0, C['Z1']), (A + C['TOOTH2'], C['Z1'], C['SEAT']), (A, C['SEAT'], C['SILL_H'])):
        L.zones.append((hw, hw + 70, 0, T, v0, v1)); L.zones.append((0, T, hw, hw + 70, v0, v1))
    return L


def inner(seed):
    """plain low parapet, no crenels. Courses alternate past the module ends, so a row has no straight joint."""
    C, L, r = CFG, Layout(), random.Random(H('inner', seed))
    T, HL, S, IN = C['INNER_T'], C['INNER_L'] / 2, C['INNER_STAGGER'], C['MORTAR_IN']
    top = C['INNER_H'] - C['INNER_COPE']
    zs = scaled_courses(0.0, top, [34, 28, 23])                               # the same in every variant: neighbours interlock course by course
    under = []
    for c in range(len(zs) - 1):
        s = S if (c % 2 == 0) else -S
        js = blocks(-HL + s, HL + s, 46 - 6 * c, 88 - 12 * c, r, under, 26); under = js[1:-1]
        for j in range(len(js) - 1): L.box(('p', c, j), js[j], js[j + 1], 0, T, zs[c], zs[c + 1], c == 0)
        L.corebox(-HL + s, HL + s, IN, T - IN, zs[c], zs[c + 1] + (2 if c == len(zs) - 2 else 0))
        L.zones.append((HL + s, HL + s + 70, 0, T, zs[c], zs[c + 1])); L.zones.append((-HL + s - 70, -HL + s, 0, T, zs[c], zs[c + 1]))
    sec = coping_section(0, T, C['INNER_H'], C['INNER_COPE'], 4.0)
    cuts = blocks(-HL, HL, 64, 110, r, (), 40)
    for j in range(len(cuts) - 1):
        L.section(('cope', j), sec, cuts[j] + G, cuts[j + 1] - G, 'u')
    L.zones.append((HL, HL + 70, -5, T + 5, top, C['INNER_H'])); L.zones.append((-HL - 70, -HL, -5, T + 5, top, C['INNER_H']))
    return L


# ---------- carving ----------
def to_cm(co):
    p = co / CM
    return p[:, 0], -p[:, 1], p[:, 2]        # u, d, v


def box_depth(u, d, v, boxes):
    """how deep each point sits inside the union of the boxes (cm, <= 0 is outside)."""
    best = np.full(len(u), -1e9)
    for u0, u1, d0, d1, v0, v1 in boxes:
        best = np.maximum(best, np.minimum.reduce([u - u0, u1 - u, d - d0, d1 - d, v - v0, v1 - v]))
    return best


def edge_dist(u, d, v, st):
    Q, s = (np.stack([u, v], 1), d) if st['axis'] == 'd' else (np.stack([d, v], 1), u)
    return np.stack([seg_dist(Q, x) for x in sides_of(st['poly'])] + [np.abs(s - st['d0']), np.abs(s - st['d1'])], 1)


def stone_style(name, key):
    """how worn this one stone is: 0.3 = freshly dressed, sharp arris; 1.7 = old, rounded. Not the same on any two."""
    r = random.Random(H('style', name, key)); x = r.random()
    return r.uniform(0.25, 0.5) if x < 0.45 else r.uniform(0.6, 1.0) if x < 0.85 else r.uniform(1.1, 1.7)


def side_normals(st):
    """outward normal of every side edge_dist() reports, in (u, d, v)."""
    cen = np.array(st['poly']).mean(0); out = []
    for s in sides_of(st['poly']):
        t = s[-1] - s[0]; n2 = np.array([t[1], -t[0]]); n2 /= max(1e-9, np.linalg.norm(n2))
        if (s.mean(0) - cen) @ n2 < 0: n2 = -n2
        out.append((n2[0], 0, n2[1]) if st['axis'] == 'd' else (0, n2[0], n2[1]))
    sdir = (0, -1, 0) if st['axis'] == 'd' else (-1, 0, 0)
    return np.array(out + [sdir, tuple(-x for x in sdir)], float)


def aabb(st):
    a = np.array(st['poly'])
    if st['axis'] == 'd': return (a[:, 0].min(), a[:, 0].max(), st['d0'], st['d1'], a[:, 1].min(), a[:, 1].max())
    return (st['d0'], st['d1'], a[:, 0].min(), a[:, 0].max(), a[:, 1].min(), a[:, 1].max())


def clearance(q, boxes):
    """distance from each point to the nearest of the boxes (0 = inside)."""
    best = np.full(len(q), 1e9)
    for u0, u1, d0, d1, v0, v1 in boxes:
        lo, hi = np.array([u0, d0, v0]), np.array([u1, d1, v1])
        best = np.minimum(best, np.linalg.norm(np.maximum(np.maximum(lo - q, q - hi), 0), axis=1))
    return best


def carve(ob, st, name, others, cull, core):
    """TGA_PC's rock-faced stone, with a different arris on every stone: flat dressed faces up to a crisp edge with small
    chips, or an old rounded one, and now and then a broken corner. Faces against a neighbour only ever go inward, so
    two stones can't touch. More wear higher up (more weather)."""
    me = ob.data; nv = len(me.vertices)
    co = np.zeros(nv * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    nr = np.zeros(nv * 3); me.vertex_normals.foreach_get('vector', nr); nr = nr.reshape(-1, 3)
    u, d, v = to_cm(co); p = np.stack([u, d, v], 1)
    Dist = edge_dist(u, d, v, st); e = np.sort(Dist, 1)[:, 1]
    r = random.Random(H(name, st['key'])); seed = r.randint(0, 99999); rock = st['rock']; wear = stone_style(name, st['key'])
    c = p.mean(0); tilt = np.array([r.uniform(-1, 1) for _ in range(3)]) * 0.006
    # three dressings, not one soft bulge on every stone (that read as pillows): flat-dressed with a crisp arris, a tooled
    # drafted margin round a rougher face, or old rock-faced. The flat tilt stays, so a face is a plane, not a cushion.
    cls = r.random()
    if cls < 0.55: amp, rel, mw, ramp = 0.22, 0.35, 0.0, 0.9 + 1.2 * wear          # dressed
    elif cls < 0.85: amp, rel, mw, ramp = 0.9, 0.75, r.uniform(2.0, 3.5), 0.8       # drafted margin
    else: amp, rel, mw, ramp = 1.0, 1.0, 0.0, 1.8 + 3.8 * wear                     # old rock face
    face = sm((e - mw) / ramp)
    high = sm(v / CFG['H'])
    relief = 0.55 * vnoise(p / 5.0, seed) + 0.32 * vnoise(p / 2.6, seed + 4) + 0.5 * vnoise(p / 12.0, seed + 1)
    dd = ((0.5 + 0.9 * r.random()) * rock * amp + r.uniform(-0.5, 0.5) * amp + relief * rock * rel) * face + (p - c) @ tilt * sm(e / 1.5)
    # the arris changes along its length too: a stretch of sharp edge, then a worn one
    along = 0.35 + 1.3 * sm(0.5 + 0.9 * vnoise(p / 16.0, seed + 5))
    width = 1.0 + 2.2 * wear
    dd -= (0.35 + 0.8 * wear) * (0.8 + 0.5 * high) * along * (1 - sm(e / width))
    near = 1 - sm(e / (2.2 + 1.6 * wear))
    dd -= np.maximum(0, vnoise(p / 3.2, seed + 2) - 0.2) * (2.6 + 1.4 * high) * near * rock * (0.6 if cls < 0.55 else 1.0)   # bigger bites
    dd -= np.maximum(0, vnoise(p / 1.25, seed + 8) - 0.28) * (1.9 - 0.5 * min(wear, 1.5)) * (1 - sm(e / 2.2))  # small crisp chips on the edge
    dd -= np.maximum(0, vnoise(p / 1.7, seed + 3) - 0.55) * (1.2 + 0.8 * high)
    for _ in range(r.choice((0, 1, 1, 2))):                                  # spalls on an arris
        i = r.randrange(nv)
        if e[i] < 3:
            rad = r.uniform(3.5, 8.0); w = 1 - np.clip(np.linalg.norm(p - p[i], axis=1) / rad, 0, 1)
            dd -= sm(w * 1.6) * r.uniform(1.2, 2.6) * (1 + 0.35 * vnoise(p / 1.5, seed + 7))
    dd = np.clip(dd, -(CFG['MORTAR_IN'] - 0.8), 2.2)                         # the surface always stays in front of the mortar
    N = side_normals(st)[Dist.argmin(1)]
    room = clearance(p + N * (CFG['JOINT'] + 0.6), others)                    # 0 = another stone is right there
    dd = np.where(dd > 0, dd * sm(room / 4.0), dd)
    out = p + nr * np.array([1, -1, 1]) * dd[:, None]                        # nr is in Blender axes, p in (u, d, v)
    # broken corners: a rough cut across an exposed corner (a plane, so the surface can't fold)
    corners = [(a, b, s_) for a, b in st['poly'] for s_ in (st['d0'], st['d1'])]
    corners = [np.array((a, s_, b) if st['axis'] == 'd' else (s_, a, b), float) for a, b, s_ in corners]
    corners = [x for x in corners if box_depth(x[:1], x[1:2], x[2:3], cull)[0] <= 0
               and clearance((x + (x - c) / np.linalg.norm(x - c) * 3)[None], others)[0] > 1.5]
    for _ in range(r.choices((0, 1, 2), (0.62, 0.3, 0.08))[0]):
        if not corners: break
        x = r.choice(corners); n = c - x; n /= np.linalg.norm(n)
        n = n + np.array([r.uniform(-0.35, 0.35) for _ in range(3)]); n /= np.linalg.norm(n)
        # how far the cut may go before it would reach the mortar: the nearest mortar box corner along the cut direction
        limit = min(sum(((b_[2 * i_] if n[i_] > 0 else b_[2 * i_ + 1]) - x[i_]) * n[i_] for i_ in range(3)) for b_ in core)
        top_ = min(r.uniform(4.5, 9.0), limit - 2.8)
        if top_ < 2.2: continue
        R_ = top_ + 1.2 * vnoise(p / 3.0, seed + 11) + 0.5 * vnoise(p / 1.2, seed + 12)
        k = (out - x) @ n
        out = out + n[None] * np.maximum(R_ - k, 0)[:, None]
    out[:, 2] = np.maximum(out[:, 2], 0.0)                                   # nothing below the pivot
    me.vertices.foreach_set('co', (np.stack([out[:, 0], -out[:, 1], out[:, 2]], 1) * CM).ravel()); me.update()


def cull_hidden(ob, boxes):
    """delete what the mortar core hides (joint faces deeper than 2 cm behind it, beds): triangles go to what is seen."""
    bm = bmesh.new(); bm.from_mesh(ob.data); bm.faces.ensure_lookup_table()
    c = np.array([f.calc_center_median() for f in bm.faces])
    u, d, v = to_cm(c); dep = box_depth(u, d, v, boxes)
    bmesh.ops.delete(bm, geom=[f for f, x in zip(bm.faces, dep) if x > 2.0], context='FACES_ONLY')
    bmesh.ops.delete(bm, geom=[e for e in bm.edges if not e.link_faces], context='EDGES')
    bmesh.ops.delete(bm, geom=[w for w in bm.verts if not w.link_faces], context='VERTS')
    bm.to_mesh(ob.data); bm.free(); ob.data.update()


def pick_patch(fw, fh, r):
    """a patch where this face fits at the target density, else one of the best fits at a lower density. fw, fh in cm.
    turn = True: the chart goes in turned 90 degrees (a tall chart in a wide patch)."""
    s = [(min(CFG['PX_CM'], (c - a) / w_, (e - b) / h_), i, t_) for i, (a, b, c, e) in enumerate(PATCHES)
         for t_, (w_, h_) in ((False, (fw, fh)), (True, (fh, fw)))]
    ok = [x for x in s if x[0] >= min(CFG['PX_MIN'], max(s)[0])]              # many candidates, so long stones don't all show the same patch
    pick = r.choice(ok)
    return pick[1], pick[0], pick[2]


def tri_min_angle(a, b, c):
    ab, ac, bc = b - a, c - a, c - b
    if min(ab.length, ac.length, bc.length) < 1e-7: return 0.0
    return min(ab.angle(ac, 0.0), (-ab).angle(bc, 0.0), (-ac).angle(-bc, 0.0))


def fix_slivers(bm, min_angle=5.0):
    """decimation leaves a few needle triangles, the only place a texture still stretches: turn the long edge of a needle
    when the surface there is nearly flat and the two new triangles are better and keep facing the same way (no folds)."""
    for _ in range(3):
        n = 0
        for f in list(bm.faces):
            if not f.is_valid or len(f.verts) != 3: continue
            if min(l.calc_angle() for l in f.loops) > math.radians(min_angle): continue
            e = max(f.edges, key=lambda x: x.calc_length())
            if len(e.link_faces) != 2: continue
            a, b = e.link_faces
            if len(a.verts) != 3 or len(b.verts) != 3 or a.normal.angle(b.normal, 0.0) > math.radians(12): continue
            p, q = e.verts[0].co, e.verts[1].co
            x = next(v for v in a.verts if v not in e.verts).co; y = next(v for v in b.verts if v not in e.verts).co
            old = min(tri_min_angle(p, q, x), tri_min_angle(p, q, y)); new = min(tri_min_angle(x, y, p), tri_min_angle(x, y, q))
            mean = (a.normal + b.normal).normalized()
            n1, n2 = (y - x).cross(p - x), (y - x).cross(q - x)
            if n1.length < 1e-12 or n2.length < 1e-12: continue
            if new <= old or n1.normalized().dot(n2.normalized()) > -0.9: continue      # p and q must sit on opposite sides of x-y
            if abs(n1.normalized().dot(mean)) < 0.9: continue
            if bmesh.utils.edge_rotate(e, True): n += 1
        bm.normal_update()
        if not n: break


def apply_uv_colour(ob, st, name, stat):
    """UV0: every face of the stone is one chart, unwrapped for minimum stretch (so slopes, bevels and chips keep the
    texture at scale), scaled to a uniform px/cm and set inside one clean patch. Col = (tone, damp, cavity)."""
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.dissolve_degenerate(bm, dist=0.001, edges=bm.edges[:])
    bmesh.ops.triangulate(bm, faces=bm.faces, quad_method='BEAUTY', ngon_method='BEAUTY')
    fix_slivers(bm)
    bm.faces.ensure_lookup_table(); bm.normal_update()
    c = np.array([f.calc_center_median() for f in bm.faces]); fn = np.array([f.normal for f in bm.faces])
    u, d, v = to_cm(c); near = edge_dist(u, d, v, st); N = side_normals(st)
    fnp = np.stack([fn[:, 0], -fn[:, 1], fn[:, 2]], 1)
    label = (fnp @ N.T - near / 3.0).argmax(1)                               # the nearest side, unless the surface really faces another
    # sides that meet at under 50 degrees (the two slopes of a coping ridge, a bevel and its face) are one chart: two planes
    # on a shallow fold flatten without stretch, while a seam on the worn ridge folded the UVs (up to 240x on a sliver)
    grp = np.arange(len(N))
    for i_ in range(len(N)):
        for j_ in range(i_):
            if N[i_] @ N[j_] > math.cos(math.radians(50)): grp[grp == grp[i_]] = grp[j_]
    label = grp[label]
    for _ in range(3):                                                       # no specks: a triangle follows its neighbours
        nxt = label.copy()
        for f in bm.faces:
            ns = [label[g.index] for e in f.edges for g in e.link_faces if g is not f]
            if ns:
                best = max(set(ns), key=ns.count)
                if ns.count(best) >= 2: nxt[f.index] = best
        label = nxt
    def islands():
        isl = np.full(len(bm.faces), -1); n = 0
        for f0 in bm.faces:
            if isl[f0.index] >= 0: continue
            isl[f0.index] = n; todo = [f0]
            while todo:
                f = todo.pop()
                for e in f.edges:
                    for g in e.link_faces:
                        if isl[g.index] < 0 and label[g.index] == label[f0.index]:
                            isl[g.index] = n; todo.append(g)
            n += 1
        return isl, n
    isl, n_isl = islands()
    # a bed or joint face whose hidden middle was culled is a thin ring around the stone: as one chart it spans the whole
    # stone and drops to ~1.5 px/cm (the smeared look). Cut such a ring into its strips, by the nearest other side.
    fa = np.array([f.calc_area() for f in bm.faces]) / CM ** 2; cc = np.stack([u, d, v], 1); split = False
    for i in range(n_isl):
        m = np.where(isl == i)[0]
        if len(m) < 12: continue
        k = label[m[0]]; n_ = N[k]; a_ = np.cross(n_, (0, 0, 1) if abs(n_[2]) < 0.9 else (1, 0, 0)); a_ /= np.linalg.norm(a_); b_ = np.cross(n_, a_)
        q = np.stack([cc[m] @ a_, cc[m] @ b_], 1); box2 = (q.max(0) - q.min(0)).prod()
        if box2 > 3.0 * fa[m].sum():
            other = near[m].copy(); other[:, grp == k] = 1e9
            label[m] = k + 16 * (1 + other.argmin(1)); split = True
    if split: isl, n_isl = islands()
    for e in bm.edges:
        e.seam = len(e.link_faces) == 2 and bool(label[e.link_faces[0].index] != label[e.link_faces[1].index])
    bm.to_mesh(ob.data); bm.free(); me = ob.data
    me.uv_layers.new(name='UVMap'); activate(ob)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.unwrap(method='MINIMUM_STRETCH', fill_holes=True, correct_aspect=False, margin=0.0, no_flip=True, iterations=12)
    bpy.ops.object.mode_set(mode='OBJECT')
    nv, nt = len(me.vertices), len(me.polygons)
    co = np.zeros(nv * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    vi = np.zeros(nt * 3, int); me.loops.foreach_get('vertex_index', vi); tri = vi.reshape(-1, 3)
    uvs = np.zeros(nt * 6); me.uv_layers[0].data.foreach_get('uv', uvs); uvs = uvs.reshape(-1, 3, 2)
    u, d, v = to_cm(co); P = np.stack([u, d, v], 1)
    A3 = 0.5 * np.linalg.norm(np.cross(P[tri[:, 1]] - P[tri[:, 0]], P[tri[:, 2]] - P[tri[:, 0]]), axis=1)
    e1, e2 = uvs[:, 1] - uvs[:, 0], uvs[:, 2] - uvs[:, 0]; Auv = 0.5 * np.abs(e1[:, 0] * e2[:, 1] - e1[:, 1] * e2[:, 0])
    r = random.Random(H('uv', name, st['key'])); out = np.zeros_like(uvs)
    for i in range(n_isl):
        m = np.where(isl == i)[0]
        k = math.sqrt(A3[m].sum() / max(Auv[m].sum(), 1e-12))                 # cm per unwrap unit: the chart at real size
        Q = uvs[m] * k; Q -= Q.reshape(-1, 2).mean(0)
        best = None
        for deg in range(0, 180, 12):
            a = math.radians(deg); Rm = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
            W = (Q.reshape(-1, 2) @ Rm.T); ext = W.max(0) - W.min(0)
            if best is None or ext.prod() < best[0]: best = (ext.prod(), W, ext)
        W, ext = best[1], best[2]; W = W - W.min(0)
        fw, fh = max(ext[0], 0.5) + 0.3, max(ext[1], 0.5) + 0.3
        pi, s_, turn = pick_patch(fw, fh, r); x0, y0, x1, y1 = PATCHES[pi]
        if turn: W = W[:, ::-1].copy(); ext = ext[::-1].copy(); fw, fh = fh, fw
        if r.random() < 0.5: W[:, 0] = ext[0] - W[:, 0]
        if r.random() < 0.5: W[:, 1] = ext[1] - W[:, 1]
        ox = x0 + r.uniform(0, max(0.0, x1 - x0 - fw * s_)); oy = y0 + r.uniform(0, max(0.0, y1 - y0 - fh * s_))
        px = (W + 0.15) * s_ + np.array([ox, oy])
        out[m, :, 0] = (px[:, 0] / TEX).reshape(-1, 3); out[m, :, 1] = (1 - px[:, 1] / TEX).reshape(-1, 3)
        if A3[m].sum() > 50: stat.append(s_)
        if os.environ.get('MERLON_DEBUG') and A3[m].sum() > 50 and s_ < CFG['PX_MIN']:
            print('  LOWPX', name, st['key'], 'side', int(np.bincount(label[m]).argmax()), 'chart cm %.0f x %.0f' % (fw, fh), 'px/cm %.2f' % s_, flush=True)
    me.uv_layers[0].data.foreach_set('uv', out.ravel())
    e = np.sort(edge_dist(u, d, v, st), 1)[:, 1]
    tone = random.Random(H('tone', name, st['key'])).uniform(0.12, 0.92)
    rs = random.Random(H('n', name, st['key'])).randint(0, 9999)
    damp = np.clip((1 - sm(v / 34.0)) * 0.55 + np.maximum(0, vnoise(P / 22.0, rs)) * 0.25, 0, 1)
    cav = np.clip((1 - sm(e / 2.6)) * 0.55 + np.maximum(0, -vnoise(P / 2.5, rs + 1)) * 0.22, 0, 1)
    col = me.color_attributes.new('Col', 'FLOAT_COLOR', 'POINT')
    col.data.foreach_set('color', np.stack([np.full(nv, tone), damp, cav, np.ones(nv)], 1).ravel())
    for p in me.polygons: p.use_smooth = True
    me.update()


def mortar(L, name):
    """closes every joint, at the bottom of each joint: the boxes and plugs as ONE closed surface, own slot (matte lime)."""
    def fill(bm):
        for u0, u1, d0, d1, v0, v1 in L.core:
            a = [bm.verts.new((u * CM, -d * CM, v * CM)) for u, d, v in
                 ((u0, d0, v0), (u1, d0, v0), (u1, d1, v0), (u0, d1, v0), (u0, d0, v1), (u1, d0, v1), (u1, d1, v1), (u0, d1, v1))]
            for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
                bm.faces.new([a[i] for i in f])
        for poly, s0, s1 in L.plugs: prism(bm, poly, s0, s1, 'u')
    ob = obj_from('mortar', fill); activate(ob)
    m = ob.modifiers.new('rm', 'REMESH'); m.mode = 'VOXEL'; m.voxel_size = 1.5 * CM; m.adaptivity = 0.0
    bpy.ops.object.modifier_apply(modifier='rm')
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(3), verts=bm.verts, edges=bm.edges)
    bmesh.ops.triangulate(bm, faces=bm.faces, quad_method='BEAUTY', ngon_method='BEAUTY')
    bmesh.ops.dissolve_degenerate(bm, dist=0.0005, edges=bm.edges[:])
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.to_mesh(ob.data); bm.free(); me = ob.data
    nv = len(me.vertices); co = np.zeros(nv * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    co[:, 2] = np.maximum(co[:, 2], 0.0); me.vertices.foreach_set('co', co.ravel())
    u, d, v = to_cm(co); P = np.stack([u, d, v], 1)
    nt = len(me.polygons); vi = np.zeros(nt * 3, int); me.loops.foreach_get('vertex_index', vi); tri = vi.reshape(-1, 3)
    n = np.abs(np.cross(P[tri[:, 1]] - P[tri[:, 0]], P[tri[:, 2]] - P[tri[:, 0]])).argmax(1)
    plane = np.array([[1, 2], [0, 2], [0, 1]])[n]
    uv = np.zeros((nt, 3, 2))
    for j in range(3):
        uv[:, j, 0] = P[tri[:, j], plane[:, 0]] / 200.0; uv[:, j, 1] = P[tri[:, j], plane[:, 1]] / 200.0   # 1 UV = 2 m, own material
    me.uv_layers.new(name='UVMap').data.foreach_set('uv', uv.ravel())
    col = me.color_attributes.new('Col', 'FLOAT_COLOR', 'POINT')
    col.data.foreach_set('color', np.tile([0.1, 0.35, 1.0, 1.0], nv))
    for p in me.polygons: p.use_smooth = False
    me.update()
    return ob, nt


def self_hits(me):
    """triangle pairs of this stone that cross each other, ignoring neighbours."""
    co = [v.co.copy() for v in me.vertices]; tri = [tuple(p.vertices) for p in me.polygons]
    t = BVHTree.FromPolygons(co, tri, all_triangles=True)
    return sum(1 for a, b in t.overlap(t) if a < b and not set(tri[a]) & set(tri[b]))


def build_module(name, kind, seed):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    L = {'merlon': merlon, 'sill': sill, 'corner': corner, 'inner': inner}[kind](seed)
    stone_m, lime_m = bpy.data.materials.new(STONE_SLOT), bpy.data.materials.new(MORTAR_SLOT)
    parts, stat = [], []
    C = CFG
    boxes_all = [aabb(x) for x in L.stones] + L.zones
    for i, st in enumerate(L.stones):
        ob = obj_from('st%03d' % i, lambda bm: prism(bm, st['poly'], st['d0'], st['d1'], st['axis']))
        activate(ob)
        b = ob.modifiers.new('bev', 'BEVEL'); b.width = (0.2 + 0.45 * stone_style(name, st['key'])) * CM; b.segments = 3; b.limit_method = 'ANGLE'; b.angle_limit = math.radians(30)
        bpy.ops.object.modifier_apply(modifier='bev')
        m = ob.modifiers.new('rm', 'REMESH'); m.mode = 'VOXEL'; m.voxel_size = C['VOXEL'] * CM; m.adaptivity = 0.0
        bpy.ops.object.modifier_apply(modifier='rm')
        carve(ob, st, name, [x for j, x in enumerate(boxes_all) if j != i], L.cull, L.core)
        activate(ob)                                                         # again after carving: a clean surface, no folds where chips cross
        m = ob.modifiers.new('rm2', 'REMESH'); m.mode = 'VOXEL'; m.voxel_size = C['VOXEL'] * CM; m.adaptivity = 0.0
        bpy.ops.object.modifier_apply(modifier='rm2')
        cull_hidden(ob, L.cull)
        if len(ob.data.polygons) == 0:
            bpy.data.objects.remove(ob); continue
        keep = ob.data.copy()
        for ratio in (1.0, 1.12, 1.25, 1.4):                                  # a fold from the reduction: reduce this stone a little less
            ob.data = keep.copy(); activate(ob)
            d = ob.modifiers.new('dec', 'DECIMATE'); d.decimate_type = 'COLLAPSE'; d.ratio = C['DECIMATE'] * ratio
            bpy.ops.object.modifier_apply(modifier='dec')
            fold_stat = []
            apply_uv_colour(ob, st, name, fold_stat)
            if self_hits(ob.data) == 0: break
        stat += fold_stat
        ob.data.materials.append(stone_m)
        parts.append(ob)
    n_st = len(parts)
    mo, mort_t = mortar(L, name)
    mo.data.materials.append(lime_m); parts.append(mo)
    activate(parts[0])
    for o in parts: o.select_set(True)
    bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active; ob.name = name; ob.data.name = name
    bm = bmesh.new(); bm.from_mesh(ob.data)                                  # anything still degenerate goes: under 0.2 mm2, nobody sees the hole
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.calc_area() < 2e-7 or min(l.calc_angle() for l in f.loops) < math.radians(0.3)], context='FACES_ONLY')
    bm.to_mesh(ob.data); bm.free()
    me = ob.data
    co = np.zeros(len(me.vertices) * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3) / CM
    rep = dict(kind=kind, stones=n_st, tris=len(me.polygons), mortar_tris=mort_t, slots=[m.name for m in me.materials],
               bbox_ue_cm=dict(x=[round(float(co[:, 0].min()), 1), round(float(co[:, 0].max()), 1)], y=[round(float(-co[:, 1].max()), 1), round(float(-co[:, 1].min()), 1)],
                               z=[round(float(co[:, 2].min()), 1), round(float(co[:, 2].max()), 1)]),
               px_per_cm_min=round(float(min(stat)), 2), px_per_cm_median=round(float(np.median(stat)), 2))
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, 'fbx', name + '.fbx'), use_selection=True, object_types={'MESH'}, mesh_smooth_type='FACE',
                             use_tspace=False, add_leaf_bones=False, bake_space_transform=False, apply_unit_scale=True, colors_type='LINEAR')
    print('MODULE', name, json.dumps(rep), flush=True)
    return rep


def import_fbx(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=path, colors_type='LINEAR')
    return [o for o in bpy.data.objects if o not in before][0]


OUT = None
if STAGE == 'build':
    OUT = POS[0] if POS else HERE
    os.makedirs(os.path.join(OUT, 'fbx'), exist_ok=True)
    path = os.path.join(OUT, 'kit_report.json')
    report = json.load(open(path)) if os.path.exists(path) else {}
    for name, (kind, seed) in MODULES.items():
        if ONLY and name not in ONLY: continue
        report[name] = build_module(name, kind, seed)
        json.dump(report, open(path, 'w'), indent=1)
    print('BUILD OK', len(report))

def read_mesh(path, offset=(0, 0, 0)):
    """FBX -> verts (cm, in Blender axes), triangles, slot per triangle, UVs per corner, polygon sizes."""
    ob = import_fbx(path); bpy.context.view_layer.update()
    me = ob.data; M = np.array(ob.matrix_world)
    co = np.zeros(len(me.vertices) * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    co = ((M[:3, :3] @ co.T).T + M[:3, 3]) / CM + np.array(offset)
    sizes = np.zeros(len(me.polygons), int); me.polygons.foreach_get('loop_total', sizes)
    vi = np.zeros(len(me.loops), int); me.loops.foreach_get('vertex_index', vi)
    uv = np.zeros(len(me.loops) * 2); me.uv_layers[0].data.foreach_get('uv', uv)
    slot = np.zeros(len(me.polygons), int); me.polygons.foreach_get('material_index', slot)
    return ob, co, vi, uv.reshape(-1, 2), slot, sizes


def loose_parts(nv, tri):
    """connected pieces: one per stone (plus the mortar)."""
    par = list(range(nv))
    def find(a):
        while par[a] != a:
            par[a] = par[par[a]]; a = par[a]
        return a
    for a, b, c in tri.tolist():
        ra, rb, rc = find(a), find(b), find(c); par[rb] = ra; par[rc] = ra
    return np.array([find(a) for a, b, c in tri.tolist()])


def stone_trees(co, tri, slot):
    """one BVH per connected stone piece, mortar left out."""
    lab = loose_parts(len(co), tri); out = []
    for l in np.unique(lab[slot == 0]):
        m = np.where((lab == l) & (slot == 0))[0]
        t = tri[m]; out.append((BVHTree.FromPolygons(co.tolist(), t.tolist(), all_triangles=True), t, co[np.unique(t)].min(0), co[np.unique(t)].max(0)))
    return out


def count_pairs(trees_a, trees_b=None):
    """triangle pairs of two different stones that intersect."""
    n = 0; pairs = 0
    tb = trees_b if trees_b is not None else trees_a
    for i, (ta, _, la, ha) in enumerate(trees_a):
        for j, (tc, _, lb, hb) in enumerate(tb):
            if trees_b is None and j <= i: continue
            if (la > hb).any() or (lb > ha).any(): continue
            hit = ta.overlap(tc)
            if hit:
                n += len(hit); pairs += 1
                if os.environ.get('MERLON_DEBUG'): print('  HIT', len(hit), np.round(la, 1).tolist(), np.round(ha, 1).tolist(), '|', np.round(lb, 1).tolist(), np.round(hb, 1).tolist())
    return n, pairs


if STAGE == 'verify':
    OUT = POS[0] if POS else HERE
    rep = {}
    rects = np.array(PATCHES) / TEX
    data = {}
    for name in MODULES:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        ob, co, vi, uv, slot, sizes = read_mesh(os.path.join(OUT, 'fbx', name + '.fbx'))
        me = ob.data
        ngons = int((sizes > 3).sum())
        tri = vi.reshape(-1, 3) if ngons == 0 else None
        P0, P1, P2 = co[tri[:, 0]], co[tri[:, 1]], co[tri[:, 2]]
        area = 0.5 * np.linalg.norm(np.cross(P1 - P0, P2 - P0), axis=1)
        edges_min = np.minimum.reduce([np.linalg.norm(P1 - P0, axis=1), np.linalg.norm(P2 - P1, axis=1), np.linalg.norm(P0 - P2, axis=1)])
        stone = slot == 0
        # stretch: singular values of the 3D -> texture map of each stone triangle
        U = uv.reshape(-1, 3, 2) * TEX
        e1, e2 = P1 - P0, P2 - P0; l1 = np.maximum(np.linalg.norm(e1, axis=1), 1e-9); a1 = e1 / l1[:, None]
        nrm = np.cross(e1, e2); nl = np.maximum(np.linalg.norm(nrm, axis=1), 1e-9); a2 = np.cross(nrm / nl[:, None], a1)
        A = np.zeros((len(tri), 2, 2)); A[:, 0, 0] = l1; A[:, 1, 0] = 0; A[:, 0, 1] = (e2 * a1).sum(1); A[:, 1, 1] = (e2 * a2).sum(1)
        B = np.stack([U[:, 1] - U[:, 0], U[:, 2] - U[:, 0]], 2)
        ok = stone & (area > 0.02)                                           # 2 mm2: below that no pixel of the map lands on it
        Sg = np.linalg.svd(B[ok] @ np.linalg.inv(A[ok]), compute_uv=False)
        an = Sg[:, 0] / np.maximum(Sg[:, 1], 1e-6); w = area[ok]
        if os.environ.get('MERLON_DEBUG'):
            cen = ((P0 + P1 + P2) / 3)[ok]
            for t_ in np.argsort(-(an - 1.25).clip(0) * w)[:8]:
                print('  STRETCH', name, 'x %.0f y %.0f z %.0f' % (cen[t_, 0], -cen[t_, 1], cen[t_, 2]), 'aniso %.2f area %.2f cm2' % (an[t_], w[t_]), flush=True)
        # patch test
        pu, pv = uv[:, 0], 1 - uv[:, 1]; inside = np.zeros(len(uv), bool)
        for x0, y0, x1, y1 in rects:
            inside |= (pu >= x0 - 1e-3) & (pu <= x1 + 1e-3) & (pv >= y0 - 1e-3) & (pv <= y1 + 1e-3)
        sl = np.repeat(stone, 3)
        # overlaps: self, stone against stone, duplicates
        trees = stone_trees(co, tri, slot); data[name] = (co.copy(), tri.copy(), slot.copy())
        pair_tris, pair_n = count_pairs(trees)
        selfx = 0
        for t, ft, _, _ in trees:
            for a, b in t.overlap(t):
                if a < b and not (set(ft[a].tolist()) & set(ft[b].tolist())): selfx += 1
        key = np.sort(tri, 1); dup = len(key) - len(np.unique(key, axis=0))
        ca = me.color_attributes[0]; col = np.zeros(len(ca.data) * 4); ca.data.foreach_get('color', col); col = col.reshape(-1, 4)
        lab_ = loose_parts(len(co), tri); small = np.unique(lab_, return_counts=True)[1].min()
        rep[name] = dict(smallest_piece_tris=int(small), tris=len(tri), ngons=ngons, degenerate_area_lt_0p001cm2=int((area < 0.001).sum()), degenerate_edge_lt_0p01cm=int((edges_min < 0.01).sum()),
                         duplicate_faces=int(dup), stones_found=len(trees), stone_stone_intersecting_tri_pairs=pair_tris, stone_pairs_touching=pair_n,
                         self_intersecting_tri_pairs_within_stones=selfx,
                         uv_stretch_max=round(float(an.max()), 2), uv_stretch_p999=round(float(np.percentile(an, 99.9)), 2), uv_stretch_p99=round(float(np.percentile(an, 99)), 2),
                         uv_stretch_area_mean=round(float((an * w).sum() / w.sum()), 3), area_share_stretch_over_1p25=round(float(w[an > 1.25].sum() / w.sum()), 4), area_share_stretch_over_1p5=round(float(w[an > 1.5].sum() / w.sum()), 4),
                         px_per_cm_p1=round(float(np.percentile(np.sqrt(Sg[:, 0] * Sg[:, 1]), 1)), 2), px_per_cm_median=round(float(np.median(np.sqrt(Sg[:, 0] * Sg[:, 1]))), 2), px_per_cm_p99=round(float(np.percentile(np.sqrt(Sg[:, 0] * Sg[:, 1]), 99)), 2),
                         stone_uv_in_clean_patch=round(float(inside[sl].mean()), 5), bbox_m=[np.round(co.min(0) * CM, 3).tolist(), np.round(co.max(0) * CM, 3).tolist()],
                         slots=[m.name for m in me.materials], mortar_tris=int((slot == 1).sum()), col_name=ca.name)
        print('VERIFY', name, json.dumps(rep[name]), flush=True)
    # neighbours as they will be placed (Blender axes: u = X, d = -Y)

    def at(name, off):
        c, t, sl = data[name]; return stone_trees(c + np.array(off, float), t, sl)
    P = CFG['PITCH']; A_ = CFG['CORNER_ARM'] + (P - CFG['MERLON_W']) / 2
    rows = {'merlon A | sill A | merlon B': [at('SM_Merlon488_A', (0, 0, 0)), at('SM_CrenelSill488_A', (P / 2, 0, 0)), at('SM_Merlon488_B', (P, 0, 0))],
            'merlon C | sill B | merlon D': [at('SM_Merlon488_C', (0, 0, 0)), at('SM_CrenelSill488_B', (P / 2, 0, 0)), at('SM_Merlon488_D', (P, 0, 0))],
            'inner A | inner B': [at('SM_InnerParapet488_A', (0, 0, 0)), at('SM_InnerParapet488_B', (CFG['INNER_L'], 0, 0))],
            'inner B | inner A': [at('SM_InnerParapet488_B', (0, 0, 0)), at('SM_InnerParapet488_A', (CFG['INNER_L'], 0, 0))],
            'corner | sill on the +X arm': [at('SM_MerlonCorner488', (0, 0, 0)), at('SM_CrenelSill488_A', (A_, 0, 0))]}
    rep['_neighbours'] = {}
    for label, groups in rows.items():
        n = 0
        for i in range(len(groups)):
            for j in range(i + 1, len(groups)): n += count_pairs(groups[i], groups[j])[0]
        rep['_neighbours'][label] = n; print('NEIGHBOURS', label, n, flush=True)
    json.dump(rep, open(os.path.join(OUT, 'kit_verify.json'), 'w'), indent=1)

if STAGE == 'patchsheet':
    im = bpy.data.images.load(os.path.join(POS[0], 'scan_B.png')); w, h = im.size
    a = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)
    for x0, y0, x1, y1 in PATCHES:
        x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
        for t in range(5):
            for yy in (h - 1 - y0 - t, h - 1 - y1 + t): a[yy, x0:x1, :3] = (1, 0.1, 0.1)
            for xx in (x0 + t, x1 - t): a[h - 1 - y1:h - 1 - y0, xx, :3] = (1, 0.1, 0.1)
    o = bpy.data.images.new('s', w, h, alpha=False); o.pixels[:] = a.ravel(); o.scale(1024, 1024)
    o.filepath_raw = POS[1]; o.file_format = 'PNG'; o.save(); print('SHEET', POS[1])

if STAGE == 'render':
    SCAN = POS[0]; OUT = POS[1] if len(POS) > 1 else HERE
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 64; sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 4
    sc.render.threads_mode = 'FIXED'; sc.render.threads = max(2, (os.cpu_count() or 4) - 2)
    sc.render.resolution_x, sc.render.resolution_y = 1600, 900; sc.render.image_settings.file_format = 'PNG'
    sc.view_settings.view_transform = 'AgX'; sc.view_settings.exposure = 0.3
    w = bpy.data.worlds.new('w'); sc.world = w
    if not w.node_tree: w.use_nodes = True
    sky = w.node_tree.nodes['Background']; sky.inputs[0].default_value = (0.62, 0.70, 0.85, 1); sky.inputs[1].default_value = 0.9
    sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sc.collection.objects.link(sun)
    sun.data.energy = 3.4; sun.data.angle = math.radians(1.5); sun.data.color = (1.0, 0.97, 0.92)
    sun.rotation_euler = (math.radians(55), 0, math.radians(-40))

    def tex(n, nodes, nonc):
        t = nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(os.path.join(SCAN, n))
        t.image.colorspace_settings.name = 'Non-Color' if nonc else 'sRGB'; return t

    def stone_material():
        m = bpy.data.materials.new('stone'); m.use_nodes = True; N, Lk = m.node_tree.nodes, m.node_tree.links
        bs = N['Principled BSDF']; b = tex('scan_B.png', N, False); nr = tex('scan_N.png', N, True); o = tex('scan_ORM.png', N, True)
        at = N.new('ShaderNodeAttribute'); at.attribute_name = 'Col'; sp = N.new('ShaderNodeSeparateColor'); Lk.new(at.outputs['Color'], sp.inputs[0])
        so = N.new('ShaderNodeSeparateColor'); Lk.new(o.outputs['Color'], so.inputs[0])

        def op(kind, a, c):
            n = N.new('ShaderNodeMath'); n.operation = kind
            for i, x in enumerate((a, c)):
                if isinstance(x, (int, float)): n.inputs[i].default_value = x
                else: Lk.new(x, n.inputs[i])
            return n.outputs[0]
        # same contract as M_CastleAshlarWeathered2: tone 0.80-1.10 (i9's values), cavity + damp darken, tint of MI_CastleAshlar
        tone = op('ADD', 0.80, op('MULTIPLY', sp.outputs[0], 0.30))
        cav = op('SUBTRACT', 1.0, op('MULTIPLY', sp.outputs[2], 0.72))
        damp = op('SUBTRACT', 1.0, op('MULTIPLY', sp.outputs[1], 0.25))
        k = op('MULTIPLY', op('MULTIPLY', tone, cav), damp)
        mix = N.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'; mix.inputs['Factor'].default_value = 1.0
        rgb = N.new('ShaderNodeCombineColor'); rgb.inputs[0].default_value = 1.04; rgb.inputs[1].default_value = 1.01; rgb.inputs[2].default_value = 0.94
        mix2 = N.new('ShaderNodeMix'); mix2.data_type = 'RGBA'; mix2.blend_type = 'MULTIPLY'; mix2.inputs['Factor'].default_value = 1.0
        Lk.new(b.outputs['Color'], mix.inputs[6]); Lk.new(rgb.outputs[0], mix.inputs[7]); Lk.new(mix.outputs[2], mix2.inputs[6])
        gr = N.new('ShaderNodeCombineColor')
        for i in range(3): Lk.new(k, gr.inputs[i])
        Lk.new(gr.outputs[0], mix2.inputs[7]); Lk.new(mix2.outputs[2], bs.inputs['Base Color'])
        Lk.new(so.outputs[1], bs.inputs['Roughness'])
        nm = N.new('ShaderNodeNormalMap'); Lk.new(nr.outputs['Color'], nm.inputs['Color']); Lk.new(nm.outputs[0], bs.inputs['Normal'])
        return m

    stone = stone_material()
    lime = bpy.data.materials.new('lime'); lime.use_nodes = True; bs = lime.node_tree.nodes['Principled BSDF']
    bs.inputs['Base Color'].default_value = (0.30, 0.28, 0.24, 1); bs.inputs['Roughness'].default_value = 0.95   # stand-in for M_CastleLimeMortar
    plain = bpy.data.materials.new('context'); plain.use_nodes = True; bs = plain.node_tree.nodes['Principled BSDF']
    bs.inputs['Base Color'].default_value = (0.20, 0.19, 0.175, 1); bs.inputs['Roughness'].default_value = 0.9
    scale_m = bpy.data.materials.new('scalebox'); scale_m.use_nodes = True
    scale_m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.55, 0.10, 0.06, 1)
    src = {}
    for name in MODULES:
        ob = import_fbx(os.path.join(OUT, 'fbx', name + '.fbx')); ob.hide_render = True; ob.hide_viewport = True
        ob.data.materials[0] = stone; ob.data.materials[1] = lime; src[name] = ob

    def place(name, u, d=0.0, yaw=0.0):
        o = bpy.data.objects.new(name + '_i', src[name].data); sc.collection.objects.link(o)
        o.location = (u * CM, -d * CM, 0); o.rotation_euler = (0, 0, yaw); return o

    def box(name, u0, u1, d0, d1, v0, v1, mat):
        o = obj_from(name, lambda bm: bmesh.ops.create_cube(bm, size=1.0))
        o.location = ((u0 + u1) / 2 * CM, -(d0 + d1) / 2 * CM, (v0 + v1) / 2 * CM); o.scale = ((u1 - u0) * CM, (d1 - d0) * CM, (v1 - v0) * CM)
        o.data.materials.append(mat); return o

    P = CFG['PITCH']; order = ['A', 'C', 'B', 'D', 'A', 'D', 'C', 'B']; sills = ['A', 'B', 'B', 'A', 'B', 'A', 'A']
    WALL = 245.0                                                             # i9: curtain thickness
    for i, k in enumerate(order):
        place('SM_Merlon488_' + k, i * P)
        if i < 7: place('SM_CrenelSill488_' + sills[i], (i + 0.5) * P)
        place('SM_InnerParapet488_' + ('A' if i % 3 else 'B'), i * P, WALL, math.pi)
    mid = 3.5 * P
    box('wall', -600, 8 * P + 400, 0, WALL, -680, -35, plain); box('deck', -600, 8 * P + 400, 0, WALL, -35, -0.5, plain)
    box('ground', -6000, 9000, -6000, 6000, -690, -680, plain)
    scale = box('human_180cm', mid - 150, mid - 105, 85, 115, 0, 180, scale_m)
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
    Eye = 165.0
    SH = {'close_outer': ((mid - 330, -270, 60), 35, (mid - 60, 25, 100)),
          'close_walk': ((mid + 150, 190, Eye), 30, (mid - 90, 30, 105)),
          'row_walk_eye': ((-280, 172, Eye), 40, (6 * P, 25, 95)),
          'row_ground': ((mid + 120, -2300, -515), 40, (mid, 0, -120)),
          'row_outer_34': ((mid - 1100, -800, 30), 35, (mid - 50, 20, 90)),
          'scale_human': ((mid + 170, 215, 150), 35, (mid - 130, 30, 90))}
    for shot, (pos, lens, at) in SH.items():
        if SHOTS and shot not in SHOTS: continue
        cam.location = (pos[0] * CM, -pos[1] * CM, pos[2] * CM); cam.data.lens = lens
        t = Vector((at[0] * CM, -at[1] * CM, at[2] * CM)); cam.rotation_euler = (t - Vector(cam.location)).to_track_quat('-Z', 'Y').to_euler()
        scale.hide_render = shot != 'scale_human'
        sc.render.filepath = os.path.join(OUT, 'renders', shot + '.png')
        bpy.ops.render.render(write_still=True); print('SHOT', shot, flush=True)
