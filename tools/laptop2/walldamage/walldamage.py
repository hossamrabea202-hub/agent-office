# Castle wall damage generator (#193, laptop2 2026-10-30). Takes a stone wall (today: a procedural stand-in built from
# courses of blocks; later: the exported castle meshes re-blocked by their course lines) and produces damaged variants
# with REAL geometry: chipped block corners, missing blocks (the hole shows the rubble core), broken crenels, a bulged
# course, impact craters, and a rubble heap at the foot. No material or decal is touched: the output keeps material
# slot 0 and UV0 of the original and bakes the damage into a Normal/AO/Mask set on UV1 (UE: a second UV channel).
#
# Rules from the owner (2026-10-30): never edit the live material or decal settings; new mesh variants only.
# Rules from the knowledge base: no intersecting parts (bake black), bevels >= 2 texels, nothing straight, damage in
# physical order (impacts first, then weathering).
#
#   blender -b --factory-startup -P walldamage.py            env RES=low|high, VARIANT=Wall|Tower|Crenel, DAMAGE=0.0..1.0
#   -> WallDmg<Variant>_<res>.blend + walldmg<variant>_meta.json (holes, rubble footprint, crenel states)
import os, sys, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np
bpy.ops.wm.read_factory_settings(use_empty=True)
from shieldkit import fbm, sstep, mesh, grid_quads, unit, superellipsoid, orient, HIGH, PI
D = os.path.dirname(os.path.abspath(__file__))
VAR = os.environ.get('VARIANT', 'Wall'); DMG = float(os.environ.get('DAMAGE', '0.6'))
rng = np.random.default_rng({'Wall': 301, 'Tower': 302, 'Crenel': 303}[VAR] + int(DMG * 100))

# ---------------------------------------------------------------- block primitives
def rounded_box(h, spacing, bevel):
    """TGA v2 (#193): a watertight rounded box with EVEN vertex density on every face (a lattice of the box surface,
    welded by construction), then each point is pulled onto the box shrunk by `bevel` plus a sphere of radius `bevel`
    (the rounded-box SDF), so edges get a true radius bevel. The superellipsoid of v1 crowded its vertices on the edges
    and left the faces nearly empty, so fractures projected onto it crumpled. Returns metric V and quads."""
    n = [max(2, int(round(2 * hi / spacing))) for hi in h]
    idx = {}; V = []
    def vid(i, j, k):
        key = (i, j, k)
        if key not in idx: idx[key] = len(V); V.append((i / n[0] * 2 - 1, j / n[1] * 2 - 1, k / n[2] * 2 - 1))
        return idx[key]
    Q = []
    for (a, b, fixed, val, flip) in ((1, 2, 0, n[0], False), (1, 2, 0, 0, True), (2, 0, 1, n[1], False), (2, 0, 1, 0, True), (0, 1, 2, n[2], False), (0, 1, 2, 0, True)):
        for u in range(n[a]):
            for v in range(n[b]):
                c = []
                for (du, dv) in ((0, 0), (1, 0), (1, 1), (0, 1)):
                    p = [0, 0, 0]; p[fixed] = val; p[a] = u + du; p[b] = v + dv; c.append(vid(*p))
                Q.append(c[::-1] if flip else c)
    V = np.array(V) * h
    inner = h - bevel; q = np.clip(V, -inner, inner); d = V - q; L = np.linalg.norm(d, axis=1, keepdims=True)
    N = d / np.maximum(L, 1e-9)
    return q + N * bevel, np.array(Q, np.int64), N

def conchoidal(V, h, ci, depth, seed):
    """TGA v2 (#193): a conchoidal fracture off one corner of a block (metric space, half-size h). Stone breaks in shells:
    the vertices inside a large fracture sphere set just outside the corner are projected onto it (a shallow concave
    scoop with a sharp rim where the sphere leaves the block), a second smaller nested shell scoops deeper near the
    corner, the rim is ragged (fbm on the sphere radius), and fine ripple rings run round the impact point."""
    sgn = np.array([(ci & 1) * 2 - 1, ((ci >> 1) & 1) * 2 - 1, ((ci >> 2) & 1) * 2 - 1], float)
    corner = sgn * h; axis = sgn / np.linalg.norm(sgn)
    s = (0.05 + 0.15 * depth) * min(1.0, h.min() / 0.21)          # chip size (m): about 5-20 cm on a 42 cm course
    a_ = np.cross(axis, [0, 0, 1.0] if abs(axis[2]) < 0.9 else [1.0, 0, 0]); a_ /= np.linalg.norm(a_); b_ = np.cross(axis, a_)
    for k, (reach, flat) in enumerate(((1.0, 2.2), (0.55, 1.4))):  # outer shell, then the nested inner shell
        F = corner + axis * s * flat                                 # sphere centre outside the corner
        Rs = s * flat + s * reach                                   # reaches s*reach inside along the diagonal
        D = V - F; L = np.linalg.norm(D, axis=1); U = D / L[:, None]
        rim = 1 + 0.07 * (fbm(U @ a_ * 1.8 + seed, U @ b_ * 1.8 + k * 7, seed + k, 2) - 0.5) * 2       # ragged outline (coarse: stone, not wax)
        R = Rs * rim
        inside = L < R
        if not inside.any(): continue
        ang = np.arccos(np.clip(U @ (-axis), -1, 1))                 # angle from the impact axis
        ph = ang * (30 + 8 * k) + 2.5 * fbm(U @ a_ * 2.5, U @ b_ * 2.5, seed + 9 + k, 2)
        saw = (ph / (2 * np.pi)) % 1.0; saw = sstep(0.0, 0.85, saw) - sstep(0.85, 1.0, saw)            # stepped shell ridges
        ripple = 0.025 * s * (saw - 0.5) * sstep(0.0, 0.25, ang)
        Vn = F + U * (R + ripple)[:, None]
        V = np.where(inside[:, None], Vn, V)
    return V

def block(name, c, sz, seed, chips=(), crater=None, mname='Stone', group=None):
    """one ashlar block: a rounded box (superellipsoid e=0.1) with per-vertex tool marks on the high; chips = list of
    (corner_index 0..7, depth 0..1) that cut a rough wedge off that corner; crater = (local xyz on the face, radius,
    depth). All deformation is vertex displacement of a closed surface, so the block stays watertight."""
    r = np.random.default_rng(seed)
    h = np.asarray(sz, float) / 2
    # TGA v2: even-density rounded box (1.5 cm high / 9 cm low), bevel 1.2-2.4 cm (>= 2 texels at the bake density)
    V, Qs, Nrm = rounded_box(h, 0.015 if HIGH else 0.09, r.uniform(0.012, 0.024))
    Ts = np.zeros((0, 3), np.int64)
    if HIGH:
        # point-chisel tool marks and a soft lump, along the surface normal, in metres
        V = V + Nrm * (0.0035 * (fbm(V[:, 0] * 9 + seed, V[:, 1] * 9 + V[:, 2] * 7, seed, 3) - 0.5) * 2
                       + 0.0012 * (fbm(V[:, 0] * 40, V[:, 2] * 40 + V[:, 1] * 30, seed + 1, 2) - 0.5) * 2)[:, None]
    for ci, depth in chips:
        V = conchoidal(V, h, ci, depth, seed * 13 + ci)
    if crater is not None:
        p, rad, depth = crater; p = np.asarray(p, float) * h; n = p / max(np.linalg.norm(p), 1e-6)
        d = np.linalg.norm(V - p, axis=1); w = sstep(rad * h.min() * 2, 0.0, d) ** 0.7
        rough = 1 + 0.3 * (fbm(V[:, 0] * 30, V[:, 2] * 30, seed + 9, 3) - 0.5) * 2 if HIGH else 1.0
        V = V - n[None] * (w * depth * h.min() * 2 * rough)[:, None]
    P = V + np.asarray(c)
    uv = np.stack([P[:, 0] + P[:, 1], P[:, 2]], -1)
    return mesh(name, P, [Qs, Ts], mname, uv=uv, group=group), P

def rubble(name, c, extent, n, seed, mname='Stone'):
    """heap of broken blocks and chips at the foot: n lumps, bigger ones at the bottom, none intersecting (placed on a
    jittered grid with sizes under the spacing)."""
    r = np.random.default_rng(seed); k = 0
    cols = max(int(extent[0] / 0.22), 1); rows = max(int(extent[1] / 0.22), 1)
    for i in range(cols):
        for jj in range(rows):
            if k >= n: break
            x = c[0] - extent[0] / 2 + (i + 0.5) * extent[0] / cols + r.uniform(-0.03, 0.03)
            y = c[1] - extent[1] / 2 + (jj + 0.5) * extent[1] / rows + r.uniform(-0.03, 0.03)
            s = r.uniform(0.08, 0.17) * (1 - 0.5 * (jj / rows))
            sz = (s * r.uniform(0.9, 1.3), s * r.uniform(0.8, 1.1), s * r.uniform(0.5, 0.8))
            Vs, Qs, Ts = superellipsoid(20 if HIGH else 8, 10 if HIGH else 4, r.uniform(0.15, 0.4))
            yaw, pitch = r.uniform(0, 2 * PI), r.uniform(-0.4, 0.4); cy, sy, cp, sp = math.cos(yaw), math.sin(yaw), math.cos(pitch), math.sin(pitch)
            R = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1.0]]) @ np.array([[1.0, 0, 0], [0, cp, -sp], [0, sp, cp]])
            P = (Vs * np.asarray(sz)) @ R.T + [x, y, c[2] + sz[2] * 0.8]
            mesh('%s_%02d' % (name, k), P, [Qs, Ts], mname, uv=np.stack([P[:, 0] + P[:, 1], P[:, 2]], -1)); k += 1

# ---------------------------------------------------------------- the wall (stand-in: 6 m x 1.2 m x 4 m, 9 courses, crenels)
WL, WT, WH = 6.0, 1.2, 4.0
CH = 0.42; ncourse = int(WH / CH)
blocks = []      # (course, index, centre, size)
for c in range(ncourse):
    z = (c + 0.5) * CH; off = 0.5 * (c % 2); nb = int(WL / 0.7) + 1
    for i in range(nb):
        x = -WL / 2 + (i + off) * 0.7 + 0.35
        if x - 0.35 > WL / 2 + 0.05 or x + 0.35 < -WL / 2 - 0.05: continue
        w = min(0.7, WL / 2 - x + 0.35, x + WL / 2 + 0.35) - 0.008
        if w < 0.2: continue
        blocks.append((c, i, np.array([min(max(x, -WL / 2 + w / 2), WL / 2 - w / 2), rng.uniform(-0.012, 0.012), z + rng.uniform(-0.006, 0.006)]), np.array([w, WT * rng.uniform(0.97, 1.0), CH - 0.008])))
# damage plan (physical order): 1 impact craters -> 2 missing blocks around them -> 3 chipped corners everywhere, more near
# the top and the impacts -> 4 broken crenels -> 5 a bulge where blocks are missing below -> 6 rubble under the holes
impacts = [(rng.uniform(-WL / 2 + 1, WL / 2 - 1), rng.uniform(0.8, WH - 0.6), rng.uniform(0.45, 0.8)) for _ in range(int(1 + 3 * DMG))]
missing = set()
for (ix, iz, ir) in impacts:
    for (c, i, ctr, sz) in blocks:
        d = math.hypot(ctr[0] - ix, ctr[2] - iz)
        if d < ir * 0.9 * DMG + 0.12 and rng.random() < 0.7: missing.add((c, i))     # TGA v2: v1's radius rarely caught a block
holes = []
for (c, i, ctr, sz) in blocks:
    if (c, i) in missing:
        holes.append([float(v) for v in ctr]); continue
    near = min([math.hypot(ctr[0] - ix, ctr[2] - iz) / ir for (ix, iz, ir) in impacts] + [9.0])
    top = ctr[2] / WH
    pchip = 0.08 + 0.5 * DMG * (0.4 * top + 0.6 * max(0.0, 1 - near))
    chips = [(int(rng.integers(0, 8)), float(rng.uniform(0.2, 0.9))) for _ in range(rng.integers(0, 3)) if rng.random() < pchip]
    # the front face is -Y: only chips on front corners read (ci bit1 == 0); keep back corners too for towers seen from both sides
    crater = None
    for (ix, iz, ir) in impacts:
        if math.hypot(ctr[0] - ix, ctr[2] - iz) < ir and (c, i) not in missing and rng.random() < 0.6 * DMG:
            lx = np.clip((ix - ctr[0]) / (sz[0] / 2), -0.8, 0.8); lz = np.clip((iz - ctr[2]) / (sz[2] / 2), -0.8, 0.8)
            crater = ((lx, -1.0, lz), rng.uniform(0.5, 0.9), rng.uniform(0.12, 0.3) * DMG)
    # TGA v2: blocks beside a hole spall on the corners that face it (the impact cracked them off), front corners only
    for (mc, mi) in missing:
        if mc == c and abs(mi - i) == 1:
            side = 1 if mi > i else 0
            chips += [(side | (0 << 1) | (0 << 2), float(rng.uniform(0.6, 1.0))), (side | (0 << 1) | (1 << 2), float(rng.uniform(0.5, 0.9)))]
        elif abs(mc - c) == 1 and abs(mi - i) <= 1:
            top_ = 1 if mc > c else 0
            chips.append((int(rng.integers(0, 2)) | (0 << 1) | (top_ << 2), float(rng.uniform(0.5, 0.9))))
    # bulge: blocks above a missing one lean out a little (the wall sags into the hole)
    lean = 0.0
    for (mc, mi) in missing:
        if mc == c - 1 and abs(mi - i) <= 1: lean = max(lean, 0.03 * DMG)
    # exposed rubble-core faces where neighbours are missing: a darker 'Core' material on a thin slab behind the hole
    block('Block_%d_%02d' % (c, i), ctr + [0, -lean, 0], sz, 400 + c * 50 + i, chips=chips, crater=crater)
# rubble core slabs behind the holes (so the hole is not see-through), rough and dark
for (c, i, ctr, sz) in blocks:
    if (c, i) in missing:
        Vs, Qs, Ts = superellipsoid(24 if HIGH else 8, 12 if HIGH else 4, 0.5)
        V = Vs * (1 + 0.15 * (fbm(Vs[:, 0] * 4, Vs[:, 2] * 4 + c, 500 + i, 3) - 0.5) * 2)[:, None]
        P = V * np.array([sz[0] * 0.5, WT * 0.3, sz[2] * 0.5]) + ctr + [0, WT * 0.15, 0]
        mesh('Core_%d_%02d' % (c, i), P, [Qs, Ts], 'Core', uv=np.stack([P[:, 0], P[:, 2]], -1))
# crenels on top: 5 merlons, some broken
nm = 5; mw = WL / (2 * nm)
crenels = []
for k in range(nm):
    x = -WL / 2 + mw * (2 * k + 0.5) + mw / 2
    state = 'ok' if rng.random() > 0.35 * DMG else ('broken' if rng.random() < 0.6 else 'gone')
    crenels.append(state)
    if state == 'gone': continue
    h = 0.9 if state == 'ok' else rng.uniform(0.3, 0.55)
    for cc in range(2 if state == 'ok' else 1):
        z = WH + (cc + 0.5) * (h / (2 if state == 'ok' else 1))
        chips = [(int(rng.integers(4, 8)), float(rng.uniform(0.4, 0.9))) for _ in range(2 if state == 'broken' else rng.integers(0, 2))]
        block('Merlon_%d_%d' % (k, cc), [x, 0, z], [mw - 0.02, WT * 0.6, h / (2 if state == 'ok' else 1) - 0.01], 600 + k * 3 + cc, chips=chips)
# rubble heaps under the holes (front side)
for (hx, hy, hz) in holes:
    if hz < 1.6: rubble('Rubble_%d' % int(hx * 10 + 50), [hx, -WT / 2 - 0.35, 0.0], [0.9, 0.6], 7, 700 + int(hx * 10))
meta = {'variant': VAR, 'damage': DMG, 'size': [WL, WT, WH + 0.9], 'holes': holes, 'crenels': crenels, 'impacts': [[float(a) for a in t] for t in impacts],
        'note': 'stand-in wall; the exported castle meshes get re-blocked by their course lines with the same damage plan'}
json.dump(meta, open(os.path.join(D, 'walldmg%s_meta.json' % VAR.lower()), 'w'), indent=1)
tris = sum(len(p.vertices) - 2 for o in bpy.data.objects if o.type == 'MESH' for p in o.data.polygons)
print('TRIS', tris, 'blocks', len(blocks), 'missing', len(missing), 'crenels', crenels)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'WallDmg%s_%s.blend' % (VAR, 'high' if HIGH else 'low')))
print('BUILD OK')
