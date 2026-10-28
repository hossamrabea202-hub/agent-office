# numpy port of M_HintCard, 5 moments of the animation stacked: blender -b --factory-startup -P preview_hint.py -- out.png
import sys, numpy as np, bpy
OUT = sys.argv[sys.argv.index('--') + 1]
CW, CH, A = 520, 190, 520 / 190
def sat(v): return np.clip(v, 0, 1)
yy, xx = np.mgrid[0:CH, 0:CW].astype(np.float32)
U, V = (xx + 0.5) / CW, (yy + 0.5) / CH
x, y = U * A, V
d = np.minimum(np.minimum(x, A - x), np.minimum(y, 1 - y))
t = np.where(d == y, x, np.where(d == A - x, A + y, np.where(d == 1 - y, A + 1 + (A - x), 2 * A + 1 + (1 - y))))
P = 2 * A + 2; s = np.abs(t - A * 0.5); s = np.minimum(s, P - s) / (P * 0.5)
aa = 0.006
outer = sat(1 - np.abs(d - 0.022) / aa); inner = sat(1 - np.abs(d - 0.060) / (aa * 0.8))
vign = 1 - 0.5 * sat(np.hypot((x / A - 0.5) * 1.6, y - 0.5) * 1.3) ** 2
bg = np.array([0.05, 0.06, 0.05])
rows = []
for age in (0.7, 1.05, 1.4, 1.9, 3.5):
    prog = sat((age - 0.8) / 0.8); drawn = (s <= prog).astype(np.float32)
    head = sat(1 - np.abs(s - prog) / 0.025) * (prog < 1) * sat(1 - np.abs(d - 0.041) / 0.035)
    corner = np.zeros_like(x)
    for cx, cy in ((0.06, 0.06), (A - 0.06, 0.06), (A - 0.06, 0.94), (0.06, 0.94)):
        dm = np.abs(x - cx) + np.abs(y - cy); lit = 1.0 if prog > 0.97 else 0.0
        corner = np.maximum(corner, sat(1 - np.abs(dm - 0.035) / aa) * lit + sat(1 - dm / 0.016) * lit)
    frame = np.maximum((outer + inner) * drawn, corner)
    sweep = sat((age - 1.2) / 1.2)
    band = sat(1 - np.abs((x / A + (1 - y) * 0.25) - (sweep * 1.5 - 0.25)) / 0.08) * (0 < sweep < 1)
    fill = sat((age - 0.5) / 0.4)
    panel = np.array([0.018, 0.016, 0.020]) * vign[..., None] + np.array([0.010, 0.007, 0.003]) * (1 - y)[..., None]
    c = panel + np.array([0.92, 0.66, 0.28]) * (frame * 1.4)[..., None] + np.array([1.0, 0.92, 0.70]) * (head * 3.0)[..., None]
    c = c + np.array([0.55, 0.42, 0.20]) * (band * 0.16)[..., None]
    a = sat(np.maximum(fill * 0.86, np.maximum(frame, head)))[..., None]
    img = bg * (1 - a) + np.minimum(c, 4) * a
    pad = np.tile(bg, (CH, 20, 1)); rows.append(np.concatenate([pad, img, pad], 1)); rows.append(np.tile(bg, (14, CW + 40, 1)))
img = np.concatenate(rows, 0); img = img / (1 + img) * 1.6
img = np.where(img <= 0.0031308, 12.92 * img, 1.055 * np.power(np.clip(img, 0, 1), 1 / 2.4) - 0.055)
h, w = img.shape[:2]
o = bpy.data.images.new('p', w, h); o.pixels = np.concatenate([img[::-1], np.ones((h, w, 1))], -1).astype(np.float32).ravel()
o.filepath_raw = OUT; o.file_format = 'PNG'; o.save(); print('PREVIEW', OUT, w, h)
