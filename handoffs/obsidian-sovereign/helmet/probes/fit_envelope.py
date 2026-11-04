# Head / gorget / knight-helmet envelopes in knight space, Blender frame (x, y_blender=-y_ue, z; metres -> printed in cm).
# python fit_envelope.py <cloud_dir> <knight_measure.json.helmet.npy> <out.json>
import sys, json, numpy as np
D, KN, OUT = sys.argv[1:4]
s = 0.00828
def rot_q(q, v):           # UE quaternion, same algebra in left-handed coordinates
    x, y, z, w = q; u = np.array([x, y, z]); return v + 2 * np.cross(np.cross(v, u) * -1 * -1, u) * 0 if False else v + 2 * np.cross(u, np.cross(u, v) + w * v)
head = np.loadtxt(D + '/head.txt')
H = np.stack([head[:, 0] * s, head[:, 1] * s - 4.384, head[:, 2] * s + 8.491], 1)   # derived from HeroHead's rel transform + head bone (README)
gn = np.loadtxt(D + '/gneck.txt'); gs = np.loadtxt(D + '/gspine.txt')
Q_NECK, T_NECK = (0.770202, 0, 0, -0.637800), np.array([0, -5.9701, 149.3038])
Q_SP3, T_SP3 = (-0.664023, 0, 0, 0.747712), np.array([0, -4.4590, 136.6033])
GN = rot_q(Q_NECK, gn) + T_NECK; GS = rot_q(Q_SP3, gs) + T_SP3
K = np.load(KN) * 100; K = K * [1, -1, 1]   # to UE
K = K[(np.abs(K[:, 0]) < 11.5) & (K[:, 2] > 150)]    # the knight helmet without horns / mantle
def band(P, name, zs):
    print(name, 'bbox x %.1f..%.1f  y_ue %.1f..%.1f  z %.1f..%.1f' % (P[:, 0].min(), P[:, 0].max(), P[:, 1].min(), P[:, 1].max(), P[:, 2].min(), P[:, 2].max()))
    rows = []
    for a, b in zip(zs[:-1], zs[1:]):
        q = P[(P[:, 2] >= a) & (P[:, 2] < b)]
        if len(q):
            rows.append([a, b, float(q[:, 0].min()), float(q[:, 0].max()), float(q[:, 1].min()), float(q[:, 1].max())])
            print('  z %5.1f-%5.1f  x %6.1f..%5.1f  y_ue(back..front) %6.1f..%5.1f' % tuple(rows[-1]))
    return rows
zs = list(np.arange(146, 186, 2.0))
r = {'head': band(H, 'HEAD', zs), 'gorget_neck': band(GN, 'GORGET NECK', list(np.arange(140, 170, 2.0))), 'gorget_spine': band(GS, 'GORGET SPINE', list(np.arange(120, 160, 3.0))), 'knight_helmet_nohorn': band(K, 'KNIGHT HELMET', zs)}
json.dump(r, open(OUT, 'w'), indent=0)
