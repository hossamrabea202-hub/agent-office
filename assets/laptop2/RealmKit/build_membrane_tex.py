# The realm membrane's vein / cell texture (#169, per the owner's concept): a glassy dome skin with a fine network of
# cell walls (Voronoi edges, two scales) and brighter veins that branch; seamless across u (the dome's UV wraps 4x around)
# and fading toward v = 1 (the pole). 2K, numpy only.  blender -b --factory-startup -P build_membrane_tex.py
#   T_RealmMembrane_Veins.png: R = cell walls (fine), G = veins (coarse, bright), B = cell interior shading, A = 1
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np
D = os.path.dirname(os.path.abspath(__file__)); TEX = os.path.join(D, 'tex')
N = 2048
i = np.arange(N); U, V = np.meshgrid((i + 0.5) / N, (i + 0.5) / N, indexing='xy')

def _hash(ix, iy, s):
    h = (ix * 374761393 + iy * 668265263 + s * 982451653) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0
def cells(u, v, nu, nv, s, jit=0.9):
    """periodic-in-u jittered Voronoi: returns distance-to-edge (d2 - d1) and the cell id."""
    cu, cv = np.floor(u * nu).astype(np.int64), np.floor(v * nv).astype(np.int64)
    d1 = np.full(u.shape, 9.0); d2 = np.full(u.shape, 9.0); cid = np.zeros(u.shape)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            cx, cy = cu + dx, cv + dy
            jx, jy = _hash(cx % nu, cy, s), _hash(cx % nu, cy, s + 1)
            px, py = (cx + 0.5 + (jx - 0.5) * jit) / nu, (cy + 0.5 + (jy - 0.5) * jit) / nv
            dd = np.hypot((u - px) * (nu / nv), v - py)       # aspect-corrected so cells are round-ish
            closer = dd < d1
            d2 = np.where(closer, d1, np.minimum(d2, dd)); cid = np.where(closer, _hash(cx % nu, cy, s + 2), cid); d1 = np.where(closer, dd, d1)
    return d2 - d1, d1, cid
def sstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)
def pnoise(u, v, s, p):
    iu, iv = np.floor(u).astype(np.int64), np.floor(v).astype(np.int64); fu, fv = u - iu, v - iv
    fu, fv = fu * fu * (3 - 2 * fu), fv * fv * (3 - 2 * fv)
    a, b, c, d = _hash(iu % p, iv, s), _hash((iu + 1) % p, iv, s), _hash(iu % p, iv + 1, s), _hash((iu + 1) % p, iv + 1, s)
    return a + (b - a) * fu + (c - a) * fv + (a - b - c + d) * fu * fv
def pfbm(u, v, s, p, oct=4):
    t, amp, f, tot = 0, 1.0, 1, 0
    for o in range(oct):
        t = t + amp * pnoise(u * f, v * f, s + o * 17, p * f); tot += amp; amp *= 0.5; f *= 2
    return t / tot

# warp the lookup a little so the cells are not perfectly tidy
wu = U + 0.02 * (pfbm(U * 6, V * 6, 5, 6) - 0.5); wv = V + 0.02 * (pfbm(U * 6 + 3, V * 6, 6, 6) - 0.5)
# fine cells (~90 around, tapering with v), coarse cells (~22 around)
e1, r1, id1 = cells(wu, wv, 96, 48, 11)
e2, r2, id2 = cells(wu, wv, 22, 11, 21)
walls = sstep(0.004, 0.0, e1) * 0.7 + sstep(0.002, 0.0, e1) * 0.3
veins = sstep(0.012, 0.0, e2); veins = np.clip(veins * (0.6 + 0.8 * pfbm(U * 20, V * 20, 31, 20, 3)), 0, 1)   # bright, uneven
# a few long branching vein strands across the dome (the concept's big red filaments)
strand = np.zeros_like(U)
for k in range(9):
    ph = _hash(k, 0, 41) * 2 * math.pi; amp = 0.05 + 0.08 * _hash(k, 1, 41); v0 = 0.05 + 0.75 * _hash(k, 2, 41)
    y = v0 + amp * np.sin(U * 2 * math.pi * (1 + k % 3) + ph) + 0.03 * (pfbm(U * 8, np.full_like(U, k), 51 + k, 8, 3) - 0.5)
    w = 0.004 + 0.004 * pfbm(U * 12, np.full_like(U, k), 61 + k, 12, 2)
    strand = np.maximum(strand, sstep(w, 0.0, np.abs(V - y)) * (0.7 + 0.3 * pfbm(U * 30, np.full_like(U, k), 71 + k, 30, 2)))
veins = np.clip(veins + strand * 1.2, 0, 1)
interior = sstep(0.0, 0.04, e1) * (0.35 + 0.65 * id1)                      # per-cell shading (soap-film thickness)
fade = sstep(1.0, 0.85, V)                                                   # the pole has no cells
arr = np.stack([walls * fade, veins * fade, interior, np.ones_like(U)], -1)[::-1]
im = bpy.data.images.new('veins', N, N, alpha=True); im.colorspace_settings.name = 'Non-Color'
im.pixels.foreach_set(arr.astype(np.float32).ravel()); im.filepath_raw = os.path.join(TEX, 'T_RealmMembrane_Veins.png'); im.file_format = 'PNG'; im.save()
print('VEINS OK')
