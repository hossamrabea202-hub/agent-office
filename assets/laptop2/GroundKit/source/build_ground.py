# Tiling ground textures (laptop2 2026-10-30): Cobble, Mud, GrassDirt, Corrupt. A 2 x 2 m seamless tile: the high poly is a
# periodic displaced heightfield (every noise wraps at the tile edge, and the mesh is padded one cell past the border so the
# bake rays never fall off), the low poly is one flat quad with UV 0..1. Per-vertex attributes carry the masks the material
# needs (h = height 0..1, id = per-stone random, gap = joints, wet = puddles / ruts, veg = moss or grass, glow = realm).
#   blender -b --factory-startup -P build_ground.py      (env RES = low | high, VARIANT = Cobble | Mud | GrassDirt | Corrupt)
import os, sys, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np
bpy.ops.wm.read_factory_settings(use_empty=True)
from shieldkit import mesh, grid_quads, sstep, HIGH, PI
D = os.path.dirname(os.path.abspath(__file__))
VAR = os.environ.get('VARIANT', 'Cobble')
TILE = 2.0
rng = np.random.default_rng({'Cobble': 201, 'Mud': 202, 'GrassDirt': 203, 'Corrupt': 204, 'CobbleMud': 205}[VAR])

def _hash(ix, iy, s):
    h = (ix * 374761393 + iy * 668265263 + s * 982451653) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0
def pnoise(u, v, s, p):
    """value noise periodic in both axes with period p cells (u, v in cells)."""
    p = max(int(round(p)), 1); iu, iv = np.floor(u).astype(np.int64), np.floor(v).astype(np.int64)
    fu, fv = u - iu, v - iv; fu, fv = fu * fu * (3 - 2 * fu), fv * fv * (3 - 2 * fv)
    a, b = _hash(iu % p, iv % p, s), _hash((iu + 1) % p, iv % p, s)
    c, d = _hash(iu % p, (iv + 1) % p, s), _hash((iu + 1) % p, (iv + 1) % p, s)
    return a + (b - a) * fu + (c - a) * fv + (a - b - c + d) * fu * fv
def pfbm(u, v, s, p, oct=5, gain=0.5):
    t, amp, f, tot = 0, 1.0, 1, 0
    for o in range(oct):
        t = t + amp * pnoise(u * f, v * f, s + o * 17, p * f); tot += amp; amp *= gain; f *= 2
    return t / tot
def pcells(u, v, n, s, jit=0.4):
    """periodic jittered cell grid (n x n per tile): distance to the nearest and second centre, the cell's random id."""
    cu, cv = np.floor(u * n).astype(np.int64), np.floor(v * n).astype(np.int64)
    d1 = np.full(u.shape, 9.0); d2 = np.full(u.shape, 9.0); cid = np.zeros(u.shape)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            cx, cy = cu + dx, cv + dy
            jx, jy = _hash(cx % n, cy % n, s), _hash(cx % n, cy % n, s + 1)
            px, py = (cx + 0.5 + (jx - 0.5) * jit) / n, (cy + 0.5 + (jy - 0.5) * jit) / n
            dd = np.hypot(u - px, v - py)
            closer = dd < d1
            d2 = np.where(closer, d1, np.minimum(d2, dd)); cid = np.where(closer, _hash(cx % n, cy % n, s + 2), cid); d1 = np.where(closer, dd, d1)
    return d1, d2, cid

N = 1024 if HIGH else 1
pad = 12 if HIGH else 0
i = np.arange(-pad, N + pad + 1); U, V = np.meshgrid(i / N, i / N, indexing='ij')   # 0..1 across the tile, padded past the border
u, v = np.mod(U, 1.0), np.mod(V, 1.0)
H = np.zeros_like(U); ID = np.zeros_like(U); GAP = np.zeros_like(U); WET = np.zeros_like(U); VEG = np.zeros_like(U); GLOW = np.zeros_like(U)

if VAR == 'Cobble':   # river cobbles set in packed earth: ~8 stones per metre, rounded tops, sunken ones, dirt and moss in the joints
    d1, d2, cid = pcells(u, v, 14, 11, jit=0.8)
    edge = d2 - d1                                     # 0 at the joint, grows into the stone
    r = (0.5 / 14) * (0.85 + 0.6 * cid)                # stone radius varies per stone (packed, small joints)
    dome = np.clip(1 - (d1 / r) ** 2.2, 0, 1) ** 0.32  # flattened top, rounded shoulder
    joint = sstep(0.002, 0.011, edge)                  # 0 in the joint (narrow)
    tilt = (pnoise(u * 14 + 0.5, v * 14 + 0.5, 17, 14) - 0.5) * 0.02 * (u - np.floor(u * 14) / 14 - 0.5 / 14) * 14   # each stone leans
    hs = (dome * (0.020 + 0.016 * cid) + tilt * dome) * joint   # stone relief 2-3.6 cm above the packed earth
    hs = hs + 0.004 * (pfbm(u * 40, v * 40, 12, 40, 3) - 0.5) * joint          # stone surface roughness
    earth = 0.008 * pfbm(u * 6, v * 6, 13, 6, 4) + 0.003 * pfbm(u * 60, v * 60, 14, 60, 2)
    sunk = 0.5 + 0.5 * (pfbm(u * 2, v * 2, 15, 2, 3) - 0.5) * 2                 # some areas have settled
    H = hs * (0.75 + 0.5 * sunk) + earth
    ID = cid; GAP = 1 - joint
    VEG = np.clip((1 - joint) * (pfbm(u * 4, v * 4, 16, 4, 3) - 0.35) * 2.5, 0, 1)   # moss in the joints, in patches
    WET = sstep(0.55, 0.3, sunk) * (1 - dome * joint)                             # puddles where it settled, in the joints

elif VAR == 'Mud':   # trodden mud: soft lumps, cart ruts along v, boot prints, standing water in the low spots
    base = 0.05 * pfbm(u * 3, v * 3, 21, 3, 5, 0.55) + 0.012 * pfbm(u * 20, v * 20, 22, 20, 3)
    rut = np.exp(-((np.sin(u * 2 * PI * 1 + 0.6 * np.sin(v * 2 * PI)) - 0.0) / 0.25) ** 2) * 0.035      # one pair of ruts winding along v
    rut2 = np.exp(-((np.sin(u * 2 * PI * 1 + 0.6 * np.sin(v * 2 * PI)) - 0.55) / 0.22) ** 2) * 0.03
    H = base - rut - rut2
    pr = np.zeros_like(U)                                                         # boot prints: 14 ovals, pressed in
    for k in range(14):
        cx, cy, a = rng.uniform(0, 1), rng.uniform(0, 1), rng.uniform(0, PI)
        for ox in (-1, 0, 1):
            for oy in (-1, 0, 1):
                dx, dy = u - cx + ox, v - cy + oy
                x_, y_ = dx * math.cos(a) + dy * math.sin(a), -dx * math.sin(a) + dy * math.cos(a)
                pr = np.maximum(pr, np.clip(1 - ((x_ / 0.07) ** 2 + (y_ / 0.14) ** 2), 0, 1) ** 0.5)
    H = H - 0.012 * pr
    wet = sstep(0.0, -0.03, H - H.mean()) * (0.5 + 0.5 * pfbm(u * 5, v * 5, 23, 5, 3))
    WET = np.clip(wet * 1.4, 0, 1); GAP = pr
    VEG = np.clip((pfbm(u * 3, v * 3, 24, 3, 3) - 0.6) * 3, 0, 1) * (1 - WET)     # a little grass on the high dry spots

elif VAR == 'GrassDirt':   # worn meadow: grass tufts (short, they are geometry in the game), bare earth paths, pebbles, roots
    gmask = sstep(0.42, 0.6, pfbm(u * 2.5, v * 2.5, 31, 2.5, 4))                  # grass patches vs dirt
    tuft = pfbm(u * 90, v * 90, 32, 90, 2); tuft = np.clip((tuft - 0.5) * 4, 0, 1) * gmask
    earth = 0.02 * pfbm(u * 4, v * 4, 33, 4, 5) + 0.004 * pfbm(u * 50, v * 50, 34, 50, 2)
    d1, d2, cid = pcells(u, v, 40, 35, jit=0.95); peb = np.clip(1 - (d1 / (0.003 + 0.009 * cid)) ** 2, 0, 1) ** 0.6 * (cid > 0.8) * (1 - gmask)
    H = earth + 0.012 * tuft + 0.009 * peb + 0.006 * gmask * pfbm(u * 12, v * 12, 36, 12, 3)
    VEG = gmask * (0.6 + 0.4 * tuft); ID = cid * (peb > 0.2); GAP = peb
    WET = sstep(0.5, 0.35, pfbm(u * 3, v * 3, 37, 3, 3)) * (1 - gmask) * 0.6

elif VAR == 'Corrupt':   # realm ground: flesh-earth, cracked crust, pulsing veins, blister bulbs, glowing fissures
    crust = pfbm(u * 5, v * 5, 41, 5, 5, 0.6)
    d1, d2, cid = pcells(u, v, 9, 42, jit=0.7); crack = sstep(0.02, 0.0, d2 - d1)                 # crack network between crust plates
    vein = np.sin(u * 2 * PI * 3 + 4 * pfbm(u * 2, v * 2, 43, 2, 3)) * np.sin(v * 2 * PI * 2 + 4 * pfbm(u * 2, v * 2, 44, 2, 3))
    vein = np.exp(-((vein - 0.0) / 0.12) ** 2)                                                      # raised vein ridges
    d1b, d2b, cidb = pcells(u, v, 6, 45, jit=0.9); bulb = np.clip(1 - (d1b / (0.03 + 0.04 * cidb)) ** 2, 0, 1) ** 0.5 * (cidb > 0.55)
    H = 0.03 * crust - 0.025 * crack + 0.012 * vein + 0.045 * bulb + 0.003 * pfbm(u * 40, v * 40, 46, 40, 2)
    GAP = crack; GLOW = np.clip(crack * 1.2 + vein * 0.5 + bulb * 0.8, 0, 1); ID = cidb * (bulb > 0.1)
    WET = np.clip(bulb * 1.5 + vein, 0, 1); VEG = 0 * U

elif VAR == 'CobbleMud':   # transition strip: cobbles on the left third sinking into mud on the right (seamless in v only; u 0 = cobble side, u 1 = mud side)
    d1, d2, cid = pcells(u, v, 14, 11, jit=0.8)
    edge = d2 - d1; r = (0.5 / 14) * (0.85 + 0.6 * cid)
    dome = np.clip(1 - (d1 / r) ** 2.2, 0, 1) ** 0.32; joint = sstep(0.002, 0.011, edge)
    tilt = (pnoise(u * 14 + 0.5, v * 14 + 0.5, 17, 14) - 0.5) * 0.02 * (u - np.floor(u * 14) / 14 - 0.5 / 14) * 14
    hs = (dome * (0.020 + 0.016 * cid) + tilt * dome) * joint
    blend = sstep(0.3, 0.75, u + 0.12 * (pfbm(u * 4, v * 4, 18, 4, 3) - 0.5) * 2)           # 0 cobbles .. 1 mud, a ragged edge
    mudh = 0.05 * pfbm(u * 3, v * 3, 21, 3, 5, 0.55) + 0.012 * pfbm(u * 20, v * 20, 22, 20, 3)
    sink = 0.03 * blend                                                                   # the cobbles sink under the mud
    H = (hs - sink) * (1 - blend) + np.maximum(hs - sink, mudh - 0.02) * blend * 0.5 + mudh * blend
    ID = cid * (1 - blend); GAP = (1 - joint) * (1 - blend)
    WET = np.clip(blend * (0.4 + 0.5 * sstep(0.0, -0.03, mudh - mudh.mean())) + (1 - blend) * sstep(0.55, 0.3, 0.5 + 0.5 * (pfbm(u * 2, v * 2, 15, 2, 3) - 0.5) * 2) * 0.3, 0, 1)
    VEG = np.clip((1 - blend) * (pfbm(u * 4, v * 4, 16, 4, 3) - 0.4) * 2.0, 0, 1) * (1 - joint)

# the mesh: high = displaced grid with attributes; low = one quad (UV 0..1 exactly, no packing)
if HIGH:
    X, Y = (U - 0.5) * TILE, (V - 0.5) * TILE
    Vt = np.stack([X, Y, H], -1).reshape(-1, 3); Q = grid_quads(U.shape[0], U.shape[1], False)
    hn = (H - H.min()) / max(H.max() - H.min(), 1e-6)
    mesh('Ground', Vt, [Q], 'Ground', uv=np.stack([U, V], -1).reshape(-1, 2),
         attrs={'ht': hn.ravel(), 'sid': ID.ravel(), 'gap': GAP.ravel(), 'wet': WET.ravel(), 'veg': VEG.ravel(), 'glow': GLOW.ravel()})   # ('id' is reserved in Blender)
else:
    z0 = float(H.mean()) if HIGH else 0.0
    Vt = np.array([[-TILE / 2, -TILE / 2, 0.0], [TILE / 2, -TILE / 2, 0.0], [TILE / 2, TILE / 2, 0.0], [-TILE / 2, TILE / 2, 0.0]])
    mesh('Ground', Vt, [np.array([[0, 1, 2, 3]])], 'Ground', uv=np.array([[0, 0], [1, 0], [1, 1], [0, 1]], float))
json.dump({'grip': [0, 0, 0], 'tile_m': TILE, 'height_range_m': [float(H.min()), float(H.max())]}, open(os.path.join(D, 'ground%s_meta.json' % VAR.lower()), 'w'))
tris = sum(len(p.vertices) - 2 for o in bpy.data.objects if o.type == 'MESH' for p in o.data.polygons)
print('TRIS', tris)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'Ground%s_%s.blend' % (VAR, 'high' if HIGH else 'low')))
print('BUILD OK')
