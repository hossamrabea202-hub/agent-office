# #401 stables: tiling PBR texture sets (2048 px = 2 x 2 m, 1024 px/m). checkking (Claude), 2026-11-01.
#   blender -b --factory-startup -P tex_stable.py -- <outdir> [res]
# Every value follows the knowledge base: non-metal 30-240 sRGB (natural >= 50), metallic 0/1 only, roughness varied at
# 3 scales, no light or AO baked into BaseColor (AO goes to ORM.R as small-scale cavity only). The large-scale wear
# (wet band, muck splash, sun bleach, mesh AO) is NOT in these tiles: it's in the mesh vertex colours, so one tile
# serves every board and every wall without the same stain repeating.
#   T_StableOak      weathered oak, grain along U (posts, beams, boards)
#   T_StableDaub     limewash over wattle-and-daub (INDUSTRY_SECRETS rule 4: castles were whitewashed)
#   T_StableShingle  riven oak shingles, 20 cm rows, grain down the slope
#   T_StableStraw    straw bedding (rasterised strands)
#   T_StableCobble   cobbled walkway with muck and straw in the joints
#   T_StableIron     forged iron rings, hinges, nails: oxide over bare metal on the edges
import sys, os, math, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cavlib import *
from cavlib import _hash
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = argv[0] if argv else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tex')
RES = int(argv[1]) if len(argv) > 1 else 2048
PPM = RES / 2.0                                                    # px per metre (2 m tile)
U, V = grid(RES)
rng = np.random.default_rng(401)
ONLY = os.environ.get('ONLY', '')
def want(n): return not ONLY or n in ONLY.split(',')

# ---------------------------------------------------------------- weathered oak
if want('Oak'):
    # grain: long along U (2 periods over 2 m), tight across V (growth rings ~ 3 mm apart)
    ring = pfbm(U, V, 2, 64, 3, 1)                                  # wavy late-wood lines
    lines = 0.5 + 0.5 * np.sin(2 * np.pi * (V * 330 + 6.0 * pfbm(U, V, 3, 6, 3, 2)))
    lines = ss(0.55, 0.95, lines)
    fib = pnoise(U, V, 40, 900, 3)                                   # fibre streaks
    broad = pfbm(U, V, 2, 6, 3, 4)                                   # board-to-board tone
    # checks: drying cracks along the grain, a few cm to 40 cm long
    ck = pnoise(U, V, 5, 220, 5); ckl = ss(0.86, 0.93, ck) * ss(0.35, 0.6, pnoise(U, V, 6, 30, 6))
    crack = ckl
    # knots: a few, with rings bending round them
    d1, d2, cid = cells(U, V, 3, 14, 7, 0.9); knot = ss(0.10, 0.03, d1) * (cid > 0.82)        # ovals along the grain
    base = lin(118, 106, 92)                                         # sun-greyed oak, ~0.14 linear (KB weathered 0.12-0.16)
    col = np.tile(base, (RES, RES, 1)) * (0.86 + 0.28 * broad)[..., None] * (0.92 + 0.12 * fib)[..., None]
    col = mix(col, lin(96, 84, 70), 0.55 * lines)                   # late-wood darker
    col = mix(col, lin(132, 124, 114), 0.35 * ss(0.55, 0.8, pfbm(U, V, 4, 16, 3, 8)))   # silvery greyed patches
    col = mix(col, lin(78, 64, 52), 0.8 * knot)
    col = mix(col, lin(56, 48, 42), 0.85 * crack)                   # crack interiors: shadowed wood, not black
    rough = 0.80 + 0.06 * (fib - 0.5) + 0.08 * (broad - 0.5) - 0.05 * lines + 0.06 * crack + 0.04 * (pnoise(U, V, 300, 300, 9) - 0.5)
    h = 0.0006 * lines + 0.0004 * fib - 0.004 * crack + 0.0015 * (broad - 0.5) - 0.0015 * knot * (1 - ss(0.02, 0.06, d1))
    ao = 1 - 0.5 * crack - 0.15 * lines * 0.5
    rough = rough + 0.16 * (pfbm(U, V, 3, 3, 3, 90) - 0.5) + 0.06 * ss(0.6, 0.8, pfbm(U, V, 10, 10, 2, 91))   # macro: weathered vs sheltered patches
    write_set(OUT, 'T_StableOak', col, rough, ao, h, PPM, nstrength=1.0)

# ---------------------------------------------------------------- limewash over daub
if want('Daub'):
    big = pfbm(U, V, 3, 3, 4, 20); mid = pfbm(U, V, 12, 12, 3, 21); fine = pnoise(U, V, 500, 500, 22)
    brush = pfbm(U, V, 30, 4, 2, 23)                                 # horizontal brush strokes of the limewash
    fl = pfbm(U, V, 10, 10, 5, 24) + 0.10 * (mid - 0.5)
    flake = ss(0.70, 0.74, fl) * 0.7                                       # newest limewash coat fallen off: older coat shows
    deep = ss(0.80, 0.83, fl)                                       # down to the daub, straw temper shows
    lime = lin(178, 174, 164)                                        # ~0.43 linear (KB plaster/limewash 0.40-0.45)
    col = np.tile(lime, (RES, RES, 1)) * (0.93 + 0.10 * big)[..., None] * (0.97 + 0.05 * brush)[..., None]
    col = mix(col, lin(160, 156, 146), 0.4 * ss(0.5, 0.8, mid))     # thinner coats: daub greys through
    col = mix(col, lin(166, 160, 146), flake)                       # older, slightly yellowed limewash coat
    col = mix(col, lin(136, 112, 84), deep)                         # clay daub
    col = mix(col, lin(150, 128, 88), deep * ss(0.6, 0.8, pnoise(U, V, 120, 400, 25)))   # straw temper in the clay
    col = mix(col, lin(104, 88, 68), deep * 0.5)
    rough = 0.90 + 0.04 * (fine - 0.5) + 0.03 * (mid - 0.5) - 0.04 * flake
    h = 0.0012 * (big - 0.5) + 0.0003 * brush + 0.0002 * fine - 0.0015 * flake - 0.0025 * deep
    ao = 1 - 0.25 * deep - 0.1 * flake * (1 - deep)
    rough = rough - 0.10 * ss(0.55, 0.8, pfbm(U, V, 3, 3, 3, 92)) + 0.08 * (mid - 0.5) - 0.05 * brush * 0 + 0.06 * (pfbm(U, V, 40, 8, 2, 93) - 0.5)   # dense fresh coats are smoother
    write_set(OUT, 'T_StableDaub', col, rough, ao, h, PPM)

# ---------------------------------------------------------------- riven oak shingles (V = down the slope)
if want('Shingle'):
    ROWS = 10                                                        # 20 cm exposure
    rowf = V * ROWS; row = np.floor(rowf).astype(np.int64); t = rowf - row       # t: 0 top of the exposed part .. 1 butt end
    off = _hash(row % ROWS, row * 0 + 3, 31)
    # shingle widths vary 10-25 cm: integer-periodic stagger, widths from a hashed sequence per row
    NW = 7; edges_u = (U * NW + off * NW)
    sid = np.floor(edges_u).astype(np.int64); su = edges_u - sid
    w = 0.25 + 0.5 * _hash(sid % NW, row % ROWS, 32)                # split position inside the cell = a second joint
    sub = su > w; sid2 = sid * 2 + sub; sl = np.where(sub, (su - w) / (1 - w), su / w)
    tone = _hash(sid2 % (2 * NW), row % ROWS, 33)
    grain = pnoise(U * 0 + sl * 0.3 + tone, V, 30, 260, 34)          # grain down the slope
    lines = ss(0.6, 0.9, 0.5 + 0.5 * np.sin(2 * np.pi * (U * 380 + 4 * pfbm(U, V, 4, 8, 2, 35))))
    gap = ss(0.035, 0.0, np.minimum(sl, 1 - sl) * np.where(sub, 1 - w, w) / NW * 2) # joint between shingles
    butt = ss(0.88, 1.0, t)                                          # thick butt end casts onto the row below
    under = ss(0.12, 0.0, t)                                         # top of the row is under the butt above: shaded & damp
    lich = ss(0.70, 0.78, pfbm(U, V, 8, 8, 4, 36)) * (0.4 + 0.6 * butt)
    base = lin(116, 108, 98)
    col = np.tile(base, (RES, RES, 1)) * (0.80 + 0.40 * tone)[..., None] * (0.94 + 0.12 * grain)[..., None]
    col = mix(col, lin(100, 92, 82), 0.18 * lines * ss(0.3, 0.7, pnoise(U, V, 60, 40, 37)))
    col = mix(col, lin(86, 74, 62), 0.6 * under)                     # damp, darker wood under the overlap
    col = mix(col, lin(62, 54, 46), 0.85 * gap)
    col = mix(col, lin(150, 152, 132), 0.55 * lich)                  # pale grey-green lichen (not saturated)
    rough = 0.82 + 0.06 * (grain - 0.5) + 0.06 * (tone - 0.5) - 0.06 * under + 0.05 * lich
    h = 0.012 * t + 0.0008 * grain + 0.0005 * lines - 0.006 * gap
    ao = 1 - 0.55 * under - 0.6 * gap
    rough = rough + 0.14 * (pfbm(U, V, 3, 3, 3, 94) - 0.5) + 0.08 * (tone - 0.5)
    write_set(OUT, 'T_StableShingle', col, rough, ao, h, PPM, nstrength=1.0)

# ---------------------------------------------------------------- straw bedding (rasterised strands)
def straw_layer(n, length_m, width_px, seed, dirt=0.0):
    r = np.random.default_rng(seed)
    hbuf = np.zeros(RES * RES, np.float64); key = np.full(RES * RES, -1.0)
    K = int(length_m * PPM / 1.5)
    x0 = r.uniform(0, RES, n); y0 = r.uniform(0, RES, n); a = r.uniform(0, np.pi, n)
    a = a + 0.35 * np.sin(2 * np.pi * y0 / RES)                      # slight combing, like forked bedding
    L = length_m * PPM * r.uniform(0.4, 1.0, n); bend = r.normal(0, 0.25, n)
    lay = r.uniform(0, 1, n)                                         # stacking order (higher = on top)
    ids = np.arange(n)
    for k in range(K):
        s = k / (K - 1) - 0.5
        ang = a + bend * s
        px = x0 + np.cos(ang) * L * s; py = y0 + np.sin(ang) * L * s
        prof = 1 - (2 * s) ** 8                                      # tapers at the ends
        for o in range(-(width_px // 2), width_px // 2 + 1):
            qx = (np.round(px - np.sin(ang) * o).astype(np.int64)) % RES; qy = (np.round(py + np.cos(ang) * o).astype(np.int64)) % RES
            cross = np.sqrt(max(0.0, 1 - (2 * o / (width_px + 1)) ** 2))
            hv = lay + 0.002 * cross * prof
            idx = qy * RES + qx; kv = np.floor(hv * 1e5) * 1e6 + ids * 10 + min(9, int(cross * 9))
            np.maximum.at(key, idx, kv)
    return key, lay
if want('Straw'):
    key, lay = straw_layer(52000, 0.22, 4, 410)
    hit = key >= 0; sid = np.where(hit, (key % 1e6) // 10, 0).astype(np.int64); cr = np.where(hit, (key % 10) / 9.0, 0)
    top = np.where(hit, np.floor(key / 1e6) / 1e5, 0)
    r = np.random.default_rng(411); stone = r.uniform(0, 1, 52000); age = r.uniform(0, 1, 52000)
    s_col = np.stack([lin(184, 156, 96), lin(160, 132, 80), lin(142, 122, 86), lin(118, 100, 72)])   # fresh gold .. old grey-brown
    pick = np.clip((age * 3.99).astype(np.int64), 0, 3)
    c = s_col[pick[sid]] * (0.85 + 0.3 * stone[sid])[:, None]
    c = c * (0.75 + 0.25 * cr)[:, None]                              # strand edges are thinner, shadowed by the strand below
    col = np.where(hit[:, None], c, lin(70, 58, 44)[None]).reshape(RES, RES, 3)   # earth floor between strands
    depth = top.reshape(RES, RES)
    col = col * (0.62 + 0.38 * ss(0.0, 1.0, depth))[..., None]       # deeper layers darker (packed, dusty)
    col = np.maximum(col, lin(52, 44, 36))
    # urine/ muck stains: yellow-brown, glossier (moved to the vertex 'muck' mask on the mesh; here only light patches)
    stain = ss(0.62, 0.75, pfbm(U, V, 4, 4, 4, 412))
    col = mix(col, col * lin(150, 120, 80) / lin(150, 150, 150), 0.5 * stain)
    rough = np.where(hit, 0.62 + 0.10 * (1 - cr) , 0.9).reshape(RES, RES) + 0.05 * (pnoise(U, V, 200, 200, 413) - 0.5) - 0.12 * stain
    h = (0.025 * depth + 0.0015 * cr.reshape(RES, RES)) * hit.reshape(RES, RES)
    ao = 0.45 + 0.55 * ss(0.0, 1.0, depth)
    rough = rough + 0.12 * (pfbm(U, V, 4, 4, 3, 95) - 0.5) + 0.08 * (np.where(hit, stone[sid], 0.5).reshape(RES, RES) - 0.5)   # waxy fresh stalks vs dull old ones
    write_set(OUT, 'T_StableStraw', col, rough, ao, h, PPM, nstrength=0.5)

# ---------------------------------------------------------------- cobbles with muck joints
if want('Cobble'):
    d1, d2, cid = cells(U, V, 14, 14, 420, 0.7)
    edge = d2 - d1                                                   # 0 at the joint
    dome = ss(0.06, 0.5, edge)                                       # rounded cobble tops
    joint = ss(0.17, 0.06, edge)                                     # earth/muck between the stones
    tone = cid; spk = pnoise(U, V, 600, 600, 421); mid = pfbm(U, V, 24, 24, 3, 422)
    stones = [lin(120, 116, 108), lin(140, 132, 118), lin(104, 98, 92), lin(126, 112, 96)]
    sc_ = np.stack(stones); pick = np.clip((tone * 3.99).astype(np.int64), 0, 3)
    col = sc_[pick] * (0.88 + 0.2 * mid)[..., None] * (0.95 + 0.1 * spk)[..., None]
    col = mix(col, col * 0.86, ss(0.5, 0.2, dome) * (1 - joint))     # worn flank: darker damp
    muck = np.clip(joint + 0.6 * ss(0.62, 0.75, pfbm(U, V, 6, 6, 4, 423)) * (1 - dome), 0, 1)
    col = mix(col, lin(64, 52, 40), muck)
    strawbits = ss(0.82, 0.9, pnoise(U, V, 30, 300, 424)) * ss(0.55, 0.7, pfbm(U, V, 5, 5, 3, 425)) * (1 - dome * 0.6)
    col = mix(col, lin(150, 124, 78), 0.7 * strawbits)
    rough = 0.68 + 0.12 * (mid - 0.5) + 0.06 * (spk - 0.5) - 0.12 * dome * 0.5 - 0.30 * muck * ss(0.5, 0.8, pnoise(U, V, 40, 40, 426)) + 0.1 * strawbits
    h = 0.016 * dome - 0.006 * joint + 0.0008 * spk
    ao = 1 - 0.55 * joint
    write_set(OUT, 'T_StableCobble', col, rough, ao, h, PPM, nstrength=0.6)

# ---------------------------------------------------------------- forged iron (512, 0.5 m tile)
if want('Iron'):
    R = 512; u, v = grid(R)
    ham = pfbm(u, v, 16, 16, 3, 430); scale = ss(0.45, 0.6, pfbm(u, v, 8, 8, 4, 431))
    bare = ss(0.80, 0.86, pnoise(u, v, 6, 160, 432)) * ss(0.5, 0.7, pfbm(u, v, 4, 4, 3, 434))   # scratches rubbed bare (tie ropes); big wear is on the mesh edges
    rust = ss(0.68, 0.76, pfbm(u, v, 6, 6, 4, 433)) * (1 - bare)
    col = np.tile(lin(72, 68, 64), (R, R, 1)) * (0.9 + 0.2 * ham)[..., None]   # black forge scale (oxide, non-metal)
    col = mix(col, lin(118, 72, 40), rust * 0.8)                     # KB rust 118,68,35
    col = mix(col, lin(196, 192, 186), ss(0.3, 0.5, bare))           # bare iron >= 180 sRGB, metallic 1 (full colour wherever metallic = 1)
    metal = (bare > 0.5).astype(np.float32)
    rough = np.where(metal > 0.5, 0.35 + 0.1 * ham, 0.78 + 0.1 * scale + 0.12 * rust)
    h = 0.0006 * ham - 0.0004 * rust
    ao = np.ones((R, R), np.float32)
    PPM_I = R / 0.5
    os.makedirs(OUT, exist_ok=True)
    save_png(os.path.join(OUT, 'T_StableIron_BC.png'), to_srgb(col))
    save_png(os.path.join(OUT, 'T_StableIron_ORM.png'), np.stack([ao, np.clip(rough, 0.05, 0.98), metal], -1))
    dx, gl = normal_from_height(h, PPM_I); save_png(os.path.join(OUT, 'T_StableIron_N.png'), dx); save_png(os.path.join(OUT, 'T_StableIron_N_GL.png'), gl)
print('TEX STABLE OK', flush=True)
