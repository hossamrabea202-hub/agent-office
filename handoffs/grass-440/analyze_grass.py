# #440 (i5): offline audit of grass_dump.csv (no editor). Blender's python (numpy) or any python with numpy.
#   python analyze_grass.py            -> report on stdout + map_before.png (top-down: roads, grass by actor, castle box)
import csv, math, os, sys
import numpy as np
H = os.path.dirname(os.path.abspath(__file__))
rows = list(csv.DictReader(open(os.path.join(H, 'grass_dump.csv'))))
mh = {l.split(',')[0]: float(l.split(',')[1]) for l in open(os.path.join(H, 'mesh_heights.csv')) if l.strip()}
road = set(tuple(int(v) for v in l.split(',')) for l in open(os.path.join(H, 'road_cells.csv')) if l.strip())
kind = lambda m: 'rock' if 'Rock' in m else 'flower' if ('Flower' in m or 'Flora' in m) else 'bush' if ('Bush' in m or 'Fern' in m or 'vdknafgha' in m) else 'grass'
X = np.array([float(r['x']) for r in rows]); Y = np.array([float(r['y']) for r in rows]); Z = np.array([float(r['z']) for r in rows])
S = np.array([float(r['sz']) for r in rows]); M = [r['mesh'] for r in rows]; ACT = [r['actor'] for r in rows]
K = np.array([kind(m) for m in M]); HT = np.array([mh.get(m, 0) * s for m, s in zip(M, S)])
ix, iy = np.floor(X / 100).astype(int), np.floor(Y / 100).astype(int)
def near_road(pad_cells):
    out = np.zeros(len(rows), bool)
    for k, (a, b) in enumerate(zip(ix, iy)):
        out[k] = any((a + dx, b + dy) in road for dx in range(-pad_cells, pad_cells + 1) for dy in range(-pad_cells, pad_cells + 1))
    return out
on = near_road(0); verge = near_road(2) & ~on
print('instances %d, road cells %d (%.0f m2)' % (len(rows), len(road), len(road)))
for a in sorted(set(ACT)):
    sel = np.array([x == a for x in ACT])
    for k in ('grass', 'flower', 'bush', 'rock'):
        s = sel & (K == k)
        if not s.any(): continue
        h = HT[s]
        print('%-15s %-6s %6d  on road %5d (%4.1f%%)  verge<2m %5d  height cm p10/p50/p90 %3.0f/%3.0f/%3.0f  z %6.0f..%6.0f' % (
            a, k, s.sum(), (s & on).sum(), 100.0 * (s & on).sum() / s.sum(), (s & verge).sum(), *np.percentile(h, [10, 50, 90]), Z[s].min(), Z[s].max()))
# grass heights against the 25-45 cm meadow target
g = K == 'grass'
print('grass taller than 60 cm: %d (%.0f%%), shorter than 15 cm: %d' % ((HT[g] > 60).sum(), 100.0 * (HT[g] > 60).mean(), (HT[g] < 15).sum()))
# density by distance ring from the castle centre
cx, cy = 2300.0, 1725.0
d = np.hypot(X - cx, Y - cy)
for r0, r1 in ((0, 5000), (5000, 10000), (10000, 15000), (15000, 22000), (22000, 1e9)):
    s = g & (d >= r0) & (d < r1)
    area = math.pi * (min(r1, 22000) ** 2 - r0 ** 2) / 1e4 if r1 < 1e8 else float('nan')
    print('ring %5.0f-%5.0f m: grass %6d  (%.2f /m2)' % (r0 / 100, min(r1, 1e5) / 100, s.sum(), s.sum() / area if area == area and area > 0 else 0))
# top-down map, 1 px = 1 m, around the castle
R = 230
img = np.full((2 * R, 2 * R, 3), 0.12, np.float32)
for (a, b) in road:
    u, v = a - int(cx / 100) + R, b - int(cy / 100) + R
    if 0 <= u < 2 * R and 0 <= v < 2 * R: img[v, u] = (0.55, 0.45, 0.32)
cols = {'Env_GrassTall': (0.2, 0.8, 0.25), 'Env_BaseRubble': (0.9, 0.85, 0.2), 'Meadow351': (0.3, 0.55, 1.0)}
for k in range(len(rows)):
    if K[k] != 'grass': continue
    u, v = int(X[k] / 100) - int(cx / 100) + R, int(Y[k] / 100) - int(cy / 100) + R
    if 0 <= u < 2 * R and 0 <= v < 2 * R:
        img[v, u] = (1, 0.1, 0.1) if on[k] else cols.get(ACT[k], (1, 1, 1))
for u in range(int(-400 / 100), int(5000 / 100)):
    for v in (int(-400 / 100), int(3850 / 100)):
        img[v - int(cy / 100) + R, u - int(cx / 100) + R] = (1, 1, 1)
np.save(os.path.join(H, 'map_before.npy'), img)
print('map saved (npy); red = grass on a road')
