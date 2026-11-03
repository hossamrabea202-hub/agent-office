# #440 phase B meadow edge (i5, 2026-11-03), computed OFFLINE: new short grass 45-75 m from the castle box, so the dense ring fades out
# instead of stopping (kept grass today: 0.94 / m2 at 30-40 m, 0.34 at 40-50, 0.08 from 50 m).
#   python feather440.py [seed=441]  -> feather_plan.csv (x,y,var,scale_z,scale_xy,yaw) + density table on stdout
# Only XY + size are planned here. feather440_ue.py traces the ground and adds the instances on the Master.
# Rules (as relayout.py): roads + 3 m verge bare, worn apron skipped, 12 m clumping noise, height tapers from 30-40 cm to 12-20 cm.
import csv, math, os, random, sys
H = os.path.dirname(os.path.abspath(__file__))
SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 441
rng = random.Random(SEED)
BOX = (-400.0, -400.0, 5000.0, 3850.0)
R0, R1 = 4500.0, 7500.0
CELL = 100.0                                                                     # candidate grid, cm
PEAK = 0.60                                                                      # added density / m2 at R0, 0 at R1
cells = lambda f: set(tuple(int(v) for v in l.split(',')) for l in open(os.path.join(H, f)) if l.strip())
ROAD, WORN = cells('road_cells.csv'), cells('worn_cells.csv')
VARS = 'ABCDEFGH'
mh = {l.split(',')[0]: float(l.split(',')[1]) for l in open(os.path.join(H, 'mesh_heights.csv')) if l.strip()}

def dbox(x, y): return math.hypot(max(BOX[0] - x, 0, x - BOX[2]), max(BOX[1] - y, 0, y - BOX[3]))
def vnoise(x, y, scale, seed):
    gx, gy = x / scale, y / scale; x0, y0 = math.floor(gx), math.floor(gy); fx, fy = gx - x0, gy - y0
    h = lambda i, j: (math.sin(i * 127.1 + j * 311.7 + seed * 74.7) * 43758.5453) % 1.0
    sx, sy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b, c, d = h(x0, y0), h(x0 + 1, y0), h(x0, y0 + 1), h(x0 + 1, y0 + 1)
    return (a * (1 - sx) + b * sx) * (1 - sy) + (c * (1 - sx) + d * sx) * sy
def near_road(ix, iy): return any((ix + dx, iy + dy) in ROAD for dx in range(-3, 4) for dy in range(-3, 4))

out, tot = [], {}
for iy in range(int((BOX[1] - R1) // CELL), int((BOX[3] + R1) // CELL) + 1):
    for ix in range(int((BOX[0] - R1) // CELL), int((BOX[2] + R1) // CELL) + 1):
        x, y = (ix + rng.random()) * CELL, (iy + rng.random()) * CELL
        d = dbox(x, y)
        if not (R0 <= d < R1): continue
        i2, j2 = int(math.floor(x / 100)), int(math.floor(y / 100))
        if (i2, j2) in WORN or near_road(i2, j2): continue
        t = (d - R0) / (R1 - R0); fade = 1 - t * t * (3 - 2 * t)                 # smooth 1 -> 0
        clump = 0.45 + 0.55 * vnoise(x, y, 1200.0, 440)                          # same 12 m patches as phase A
        if rng.random() > PEAK * fade * clump * 1.45: continue                   # 1.45: clump averages ~0.7
        v = rng.choice(VARS); m = 'SM_vczndjqja_Var' + v
        lo, hi = 30 + (12 - 30) * t, 40 + (20 - 40) * t
        s = max(0.15, min(1.5, (lo + (hi - lo) * rng.random()) / max(mh.get(m, 40.0), 1.0)))
        out.append('%.0f,%.0f,%s,%.3f,%.3f,%.0f' % (x, y, v, s, max(s, 0.8 + 0.2 * rng.random()), rng.random() * 360))
        b = int(d // 500) * 5; tot[b] = tot.get(b, 0) + 1
open(os.path.join(H, 'feather_plan.csv'), 'w').write('x,y,var,sz,sxy,yaw\n' + '\n'.join(out))
P = 2 * (BOX[2] - BOX[0] + BOX[3] - BOX[1]) / 100
for b in sorted(tot):
    a = P * 5 + math.pi * ((b + 5) ** 2 - b ** 2)
    print('%2d-%2d m  +%4d  +%.2f / m2' % (b, b + 5, tot[b], tot[b] / a))
print('new instances', len(out), '(phase A removed 24,552)')
