# #390 spindrift spots: wind-exposed ridge crests where a NW (315 deg) gale lifts snow plumes off the lee edge.
#   "<blender python>" -I gen_drift.py   ->  out/drift.json  (world cm; yaw 45 = plume blows toward SE; read by winterkeep_ue.py --step drift)
import json, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, 'out')
H = np.load(os.path.join(OUT, 'height_m.npy')); N = H.shape[0]; HALF = (N - 1) / 2
L = json.load(open(os.path.join(OUT, 'layout.json')))

def box(a, r):                       # box blur, radius r px (1 px = 1 m), edge-clamped
    p = np.pad(a, r, mode='edge'); c = p.cumsum(0).cumsum(1); c = np.pad(c, ((1, 0), (1, 0)))
    k = 2 * r + 1
    return (c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]) / (k * k)
crest = H - box(H, 40)                                   # convex: higher than the 81 m neighbourhood
gy, gx = np.gradient(H)                                   # rows = +Y (south), cols = +X (east)
wind_to = np.array([0.7071, 0.7071])                      # toward SE in (x, y)
lee_drop = -(gx * wind_to[0] + gy * wind_to[1])           # >0 where the ground falls away downwind (cornice edge)
score = np.clip(crest, 0, None) * np.clip(lee_drop + 0.15, 0, None) * np.clip((H - 120.0) / 120.0, 0, 1)
cx, cy = L['castle_centre'][0] / 100 + HALF, L['castle_centre'][1] / 100 + HALF
yy, xx = np.mgrid[0:N, 0:N]
score[np.hypot(xx - cx, yy - cy) < 250] = 0               # not over the castle
score[:60] = score[-60:] = 0; score[:, :60] = score[:, -60:] = 0
spots = []
order = np.argsort(score, axis=None)[::-1]
for idx in order[:200000]:
    y, x = divmod(int(idx), N)
    if score[y, x] <= 0 or len(spots) >= 24: break
    if any(np.hypot(x - sx, y - sy) < 150 for sx, sy, _ in spots): continue
    spots.append((x, y, float(H[y, x])))
res = [{'loc': [round((x - HALF) * 100, 1), round((y - HALF) * 100, 1), round(z * 100 + 50, 1)], 'yaw': 45.0, 'score': round(float(score[y, x]), 3)}
       for x, y, z in spots]
json.dump({'card': 390, 'wind_from_deg': 315, 'spots': res}, open(os.path.join(OUT, 'drift.json'), 'w'), indent=1)
print('wrote out/drift.json:', len(res), 'spindrift spots; heights m', sorted(round(s[2]) for s in spots))
