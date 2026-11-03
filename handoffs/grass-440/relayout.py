# #440 grass re-layout plan (i5, 2026-11-03), computed OFFLINE from grass_dump.csv: one action per instance.
#   python relayout.py [seed=440]   -> plan.csv (actor,comp,idx,action,sz,sxy,why)  action: keep | remove | scale
#   Height is set by Z; the clump keeps 80-100 % of its width (a uniform shrink would open bare gaps).
#                                      + map_after.npy + stats on stdout
# Rules (RESEARCH.md: AAA mountain grass = data-driven bands, clumping noise, roads bare, terrain carries distance):
#   road (GateMudPath, YW paths, PortalRoad, gate band)   nothing; verge 0-1.5 m short trampled grass, 1.5-3 m shortened
#   courtyard (castle box)                                packed earth: 10 % short weeds survive, no flowers / bushes
#   worn apron (Env_WornGround_Decal)                     grazed: 70 % kept, 12-25 cm, flowers 10 %
#   meadow heights by noise patches                       lush 45-60 cm / normal 28-42 cm / thin 15-25 cm (never a carpet)
#   altitude bands (z above the valley floor)             < 15 m meadow, 15-50 m tussock 20-35 cm (65 %), > 50 m dwarf 6-14 cm (35 %)
#   clumping                                              12 m noise density mask (0.55-1.0); the ring edge is feathered outward in phase B
#   flowers                                               only inside their species patches, ~25 % of the old count
# Rocks and bushes: only the road / courtyard rules (no height change).
import csv, math, os, random, sys
import numpy as np
H = os.path.dirname(os.path.abspath(__file__))
SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 440
rng = random.Random(SEED)
rows = list(csv.DictReader(open(os.path.join(H, 'grass_dump.csv'))))
mh = {l.split(',')[0]: float(l.split(',')[1]) for l in open(os.path.join(H, 'mesh_heights.csv')) if l.strip()}
cells = lambda f: set(tuple(int(v) for v in l.split(',')) for l in open(os.path.join(H, f)) if l.strip())
ROAD, WORN = cells('road_cells.csv'), cells('worn_cells.csv')
CASTLE = (-400.0, -400.0, 5000.0, 3850.0)
CX, CY, FLOOR_Z = 2300.0, 1725.0, 0.0
kind = lambda m: 'rock' if 'Rock' in m else 'flower' if ('Flower' in m or 'Flora' in m) else 'bush' if ('Bush' in m or 'Fern' in m or 'vdknafgha' in m) else 'grass'

def vnoise(x, y, scale, seed):
    gx, gy = x / scale, y / scale; x0, y0 = math.floor(gx), math.floor(gy); fx, fy = gx - x0, gy - y0
    h = lambda i, j: (math.sin(i * 127.1 + j * 311.7 + seed * 74.7) * 43758.5453) % 1.0
    sx, sy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b, c, d = h(x0, y0), h(x0 + 1, y0), h(x0, y0 + 1), h(x0 + 1, y0 + 1)
    return (a * (1 - sx) + b * sx) * (1 - sy) + (c * (1 - sx) + d * sx) * sy

# distance to the nearest road cell (in cells, capped at 4) via a small dilation
def road_dist(ix, iy):
    for r in range(0, 4):
        if any((ix + dx, iy + dy) in ROAD for dx in range(-r, r + 1) for dy in range(-r, r + 1) if max(abs(dx), abs(dy)) == r): return r
    return 9

out, stats = [], {}
def act(r, a, s=None, why='', sxy=None):
    out.append('%s,%s,%s,%s,%s,%s,%s' % (r['actor'], r['comp'], r['idx'], a, '' if s is None else '%.3f' % s, '' if sxy is None else '%.3f' % sxy, why))
    k = (kind(r['mesh']), a, why); stats[k] = stats.get(k, 0) + 1

for r in rows:
    x, y, z, sz, m = float(r['x']), float(r['y']), float(r['z']), float(r['sz']), r['mesh']
    k = kind(m); ix, iy = int(math.floor(x / 100)), int(math.floor(y / 100))
    u = rng.random()
    rd = road_dist(ix, iy)
    in_castle = CASTLE[0] < x < CASTLE[2] and CASTLE[1] < y < CASTLE[3]
    if rd == 0 and k != 'rock': act(r, 'remove', why='road'); continue            # the road itself is bare
    if in_castle and k != 'rock':
        if k == 'grass' and u < 0.10: act(r, 'scale', min(sz, 12.0 / max(mh.get(m, 30), 1)), 'courtyard', min(sz, 0.6)); continue
        act(r, 'remove', why='courtyard'); continue
    if k in ('rock', 'bush'):
        act(r, 'remove' if (rd <= 1 and k == 'bush') else 'keep', why='verge' if (rd <= 1 and k == 'bush') else ''); continue
    worn = (ix, iy) in WORN
    dz = z - FLOOR_Z
    n_clump = vnoise(x, y, 1200.0, SEED)                                          # 12 m patches
    n_lush = vnoise(x + 7777, y - 3333, 2500.0, SEED + 1)                        # 25 m wet / dry
    d_c = math.hypot(x - CX, y - CY)
    if k == 'flower':
        keep = n_clump > 0.55 and u < 0.45                                        # only in the species patches
        if worn or rd <= 2: keep = keep and u < 0.10
        if dz > 5000: keep = keep and u < 0.15
        act(r, 'keep' if keep else 'remove', why='' if keep else 'flower-ratio'); continue
    # ---- grass ----
    dens = 0.55 + 0.45 * n_clump                                                  # clumping
    if dz > 5000: dens *= 0.35; lo, hi = 6, 14                                    # dwarf tufts high up
    elif dz > 1500: dens *= 0.65; lo, hi = 20, 35                                 # tussock band
    elif n_lush > 0.62: lo, hi = 45, 60                                           # lush hollows
    elif n_lush < 0.35: lo, hi = 15, 25                                           # thin, dry patches
    else: lo, hi = 28, 42
    # (no ring thinning: phase B feathers the edge OUTWARD with new tapered grass, 55-75 m)
    if worn: dens *= 0.70; lo, hi = 12, 25
    if rd == 1: lo, hi = lo * 0.35, hi * 0.55                                     # trampled verge
    elif rd == 2: lo, hi = lo * 0.7, hi * 0.8
    if u > dens: act(r, 'remove', why='worn' if worn else 'clump/ring/band'); continue
    target = lo + (hi - lo) * rng.random()
    base = max(mh.get(m, 40.0), 1.0)
    s_z = max(0.15, min(1.5, target / base))
    act(r, 'scale', s_z, 'height', max(s_z, min(sz, 1.0) * (0.8 + 0.2 * rng.random())))

open(os.path.join(H, 'plan.csv'), 'w').write('actor,comp,idx,action,sz,sxy,why\n' + '\n'.join(out))
tot = {}
for (k, a, w), n in stats.items(): tot.setdefault(k, {})[a + (':' + w if w else '')] = n
for k, d in sorted(tot.items()): print('%-7s %s' % (k, '  '.join('%s %d' % kv for kv in sorted(d.items()))))
kept = sum(n for (k, a, w), n in stats.items() if a != 'remove'); print('instances %d -> %d kept (%.0f%%)' % (len(rows), kept, 100.0 * kept / len(rows)))
